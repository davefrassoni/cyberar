"""Motor puro: sin reloj de pared, red, ORM ni dependencias de interfaz."""
import copy
import math
from enum import StrEnum
from communications.channels import metrics
from events.log import emit
from .scenario import DemoScenario, ROUTE, SCENARIOS
from vehicles import ugv

OFFSET_SECONDS = 8


class Phase(StrEnum):
    PREPARING = "PREPARING"
    TAKEOFF = "TAKEOFF"
    TRANSIT = "TRANSIT"
    RECON = "RECON"
    RETURN = "RETURN"
    LANDED = "LANDED"
    MISSION_COMPLETE = "MISSION_COMPLETE"


TRANSITIONS = {
    Phase.PREPARING: {Phase.TAKEOFF}, Phase.TAKEOFF: {Phase.TRANSIT},
    Phase.TRANSIT: {Phase.RECON}, Phase.RECON: {Phase.RETURN},
    Phase.RETURN: {Phase.LANDED}, Phase.LANDED: {Phase.MISSION_COMPLETE},
    Phase.MISSION_COMPLETE: set(),
}
LABELS = {Phase.TAKEOFF: "Despegue confirmado", Phase.TRANSIT: "Tránsito hacia zona marítima", Phase.RECON: "Reconocimiento de zona marítima", Phase.RETURN: "Regreso a base", Phase.LANDED: "Aterrizaje confirmado", Phase.MISSION_COMPLETE: "Misión completada"}


class SimulationEngine:
    def initial(self, duration=150, can_threshold=80, route=None, fleet_size=1,
                ugv_route=None, ugv_asset=None, ugv_label=None):
        if type(fleet_size) is not int or not 1 <= fleet_size <= 3:
            raise ValueError("El tamaño de flota debe ser 1, 2 o 3")
        atlantic = SCENARIOS["atlantic"]
        state = {"elapsed": 0, "duration": duration, "phase": Phase.PREPARING, "automatic": True,
                 "interference": 0, "active_channel": "RF-PRIMARY", "channels": metrics(),
                 "checkpoint_index": 0, "route": copy.deepcopy(route) if route else copy.deepcopy(ROUTE),
                 "fleet_size": fleet_size, "drone_faults": {}, "events": [], "event_sequence": 0,
                 "ugv": ugv.initial(can_threshold,
                                     copy.deepcopy(ugv_route) if ugv_route else None,
                                     ugv_asset or atlantic["ugv"]["asset"],
                                     ugv_label or atlantic["ugv"]["label"])}
        self._fleet_telemetry(state)
        emit(state, "SYSTEM", "Simulador listo · escenario determinístico v1")
        return state

    def transition(self, state, target):
        if target not in TRANSITIONS[state["phase"]]:
            raise ValueError(f"Transición no permitida: {state['phase']} → {target}")
        state["phase"] = target
        emit(state, "MISSION", LABELS[target])

    def advance(self, original, seconds=1):
        if isinstance(seconds, bool) or not isinstance(seconds, int) or seconds < 0:
            raise ValueError("El paso debe ser un entero no negativo")
        state = copy.deepcopy(original)
        for _ in range(seconds):
            if state["phase"] == Phase.MISSION_COMPLETE: break
            state["elapsed"] += 1
            route = state["route"]
            t_lead = DemoScenario(state["duration"]).time(state["elapsed"])
            trailing_elapsed = max(0, state["elapsed"] - (state["fleet_size"] - 1) * OFFSET_SECONDS)
            t_trail = DemoScenario(state["duration"]).time(trailing_elapsed)
            for threshold, phase, t in [(1, Phase.TAKEOFF, t_lead), (8, Phase.TRANSIT, t_lead),
                                         (65, Phase.RECON, t_lead), (100, Phase.RETURN, t_lead),
                                         (145, Phase.LANDED, t_trail), (150, Phase.MISSION_COMPLETE, t_trail)]:
                if t >= threshold and phase in TRANSITIONS[state["phase"]]: self.transition(state, phase)
            index = max(i for i, cp in enumerate(route) if t_lead >= cp["at"])
            if index != state["checkpoint_index"]:
                for i in range(state["checkpoint_index"] + 1, index + 1):
                    emit(state, "MISSION", f"{route[i]['id']} alcanzado")
                state["checkpoint_index"] = index
            if state["automatic"]:
                self.set_interference(state, DemoScenario(state["duration"]).interference(state["elapsed"]))
            self._fleet_telemetry(state)
            ugv.update(state, t_lead)
        return state

    def retelemeter(self, original):
        """Recalcula la telemetría de la flota sin avanzar el reloj (edición de checkpoints/fallas)."""
        state = copy.deepcopy(original)
        self._fleet_telemetry(state)
        return state

    def set_interference(self, state, level):
        if type(level) not in (int, float) or not math.isfinite(level) or not 0 <= level <= 100:
            raise ValueError("Interferencia fuera de rango")
        if state["interference"] != level:
            state["interference"] = level
            emit(state, "WARNING" if level else "COMMUNICATION", f"Interferencia simulada: {level}%" if level else "Enlace recuperado · métricas nominales")
        state["channels"] = metrics(level)

    def _drone_telemetry(self, route, duration, elapsed, asset_id):
        t = DemoScenario(duration).time(elapsed)
        raw_index = max(i for i, cp in enumerate(route) if t >= cp["at"])
        index = min(raw_index, len(route) - 2)
        a, b = route[index:index + 2]
        fraction = max(0, min(1, (t - a["at"]) / (b["at"] - a["at"])))
        x, y = a["x"] + (b["x"] - a["x"]) * fraction, a["y"] + (b["y"] - a["y"]) * fraction
        altitude = round(1420 * min(1, t / 8, max(0, (145 - t) / 8)))
        return {"id": asset_id, "x": round(x, 2), "y": round(y, 2), "latitude": round(-47 - y / 100, 5),
                "longitude": round(-69 + x / 100, 5), "altitude": altitude,
                "heading": round(math.degrees(math.atan2(b["x"] - a["x"], a["y"] - b["y"])) % 360),
                "speed": 82 if altitude else 0, "battery": round(100 - min(t, 150) * .21, 1), "gps_status": "ONLINE",
                "distance_to_base": round(math.hypot(x - route[0]["x"], y - route[0]["y"]) * .55, 1),
                "current_checkpoint": route[raw_index]["id"], "next_checkpoint": b["id"],
                "checkpoint_index": raw_index, "onboard_storage": 0, "timestamp": elapsed}

    def _fleet_telemetry(self, state):
        route, duration, fleet_size = state["route"], state["duration"], state["fleet_size"]
        faults = state.get("drone_faults") or {}
        drones = []
        for i in range(fleet_size):
            elapsed_i = max(0, state["elapsed"] - i * OFFSET_SECONDS)
            drone = self._drone_telemetry(route, duration, elapsed_i, f"UAV-{i + 1:02d}")
            fault = faults.get(str(i), 0)
            if fault:
                drone["altitude"] = max(0, round(drone["altitude"] - fault * 6))
            drones.append(drone)
        state["drones"] = drones
