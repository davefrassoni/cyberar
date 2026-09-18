"""Motor puro: sin reloj de pared, red, ORM ni dependencias de interfaz."""
import copy
import math
from enum import StrEnum
from communications.channels import metrics
from events.log import emit
from .scenario import DemoScenario, ROUTE, SCENARIOS, jammers_for
from vehicles import ugv

MAX_FLEET = 3
JAMMER_RANGE = 500
JAMMER_POWER = 100
JAMMER_ORBIT_PERIOD = 60  # segundos simulados para una vuelta completa del avión jammer
CONTROL_MODES = {"AUTONOMOUS_ROUTE", "MANUAL_REMOTE", "AUTONOMOUS_AI_VISION"}


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
    def initial(self, duration=150, can_threshold=80, route=None,
                ugv_route=None, ugv_asset=None, ugv_label=None, jammers=None):
        atlantic = SCENARIOS["atlantic"]
        state = {"elapsed": 0, "duration": duration, "phase": Phase.PREPARING, "control_mode": "AUTONOMOUS_ROUTE",
                 "interference": 0, "active_channel": "RF-PRIMARY", "channels": metrics(),
                 "checkpoint_index": 0, "route": copy.deepcopy(route) if route else copy.deepcopy(ROUTE),
                 "jammers": copy.deepcopy(jammers) if jammers is not None else jammers_for("atlantic"),
                 "drones_launch": [0], "drone_faults": {}, "events": [], "event_sequence": 0,
                 "ugv": ugv.initial(can_threshold,
                                     copy.deepcopy(ugv_route) if ugv_route else None,
                                     ugv_asset or atlantic["ugv"]["asset"],
                                     ugv_label or atlantic["ugv"]["label"])}
        self._fleet_telemetry(state)
        self._apply_jammers(state)
        emit(state, "SYSTEM", "Simulador listo · escenario determinístico v1")
        return state

    def add_drone(self, original):
        state = copy.deepcopy(original)
        launches = state.setdefault("drones_launch", [0])
        if len(launches) >= MAX_FLEET:
            raise ValueError("La flota ya alcanzó el máximo de 3 UAV")
        if state["phase"] == Phase.MISSION_COMPLETE:
            raise ValueError("La misión ya finalizó · reiniciá la demo para agregar más UAV")
        launches.append(state["elapsed"])
        self._fleet_telemetry(state)
        emit(state, "MISSION", f"UAV-{len(launches):02d} despegó desde base")
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
            launches = state.get("drones_launch") or [0]
            t_lead = DemoScenario(state["duration"]).time(state["elapsed"])
            trailing_elapsed = max(0, state["elapsed"] - max(launches))
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
            self._fleet_telemetry(state)
            self._apply_jammers(state)
            ugv.update(state, t_lead)
        return state

    def retelemeter(self, original):
        """Recalcula la telemetría de la flota sin avanzar el reloj (edición de checkpoints/fallas)."""
        state = copy.deepcopy(original)
        self._fleet_telemetry(state)
        self._apply_jammers(state)
        return state

    def set_interference(self, state, level):
        if type(level) not in (int, float) or not math.isfinite(level) or not 0 <= level <= 100:
            raise ValueError("Interferencia fuera de rango")
        if state["interference"] != level:
            state["interference"] = level
            emit(state, "WARNING" if level else "COMMUNICATION", f"Interferencia simulada: {level}%" if level else "Enlace recuperado · métricas nominales")
        state["channels"] = metrics(level)

    def _apply_jammers(self, state):
        """Recalcula posición (patrulla circular para el avión jammer) e interferencia
        activa de cada jammer del teatro, en función de su distancia al UAV más cercano —
        reemplaza la vieja curva de interferencia automática basada en tiempo."""
        jammers = state.setdefault("jammers", [])
        drones = state.get("drones") or []
        total = 0
        for jammer in jammers:
            if jammer["kind"] == "AIRCRAFT" and jammer.get("radius"):
                angle = state["elapsed"] * (2 * math.pi / JAMMER_ORBIT_PERIOD)
                jammer["x"] = round(jammer["cx"] + jammer["radius"] * math.cos(angle), 2)
                jammer["y"] = round(jammer["cy"] + jammer["radius"] * math.sin(angle), 2)
            else:
                jammer["x"], jammer["y"] = jammer["cx"], jammer["cy"]
            if not jammer["active"] or not drones:
                continue
            distance = min(math.hypot(jammer["x"] - d["x"], jammer["y"] - d["y"]) for d in drones)
            total += JAMMER_POWER * max(0, 1 - distance / JAMMER_RANGE)
        self.set_interference(state, round(min(100, total), 1))

    def set_jammer(self, original, jammer_id, active):
        state = copy.deepcopy(original)
        jammer = next((j for j in state.get("jammers") or [] if j["id"] == jammer_id), None)
        if jammer is None:
            raise ValueError("Jammer desconocido")
        if jammer["active"] != active:
            jammer["active"] = active
            emit(state, "WARNING" if active else "COMMUNICATION",
                 f"{jammer['label']} {'activado' if active else 'desactivado'}")
        self._apply_jammers(state)
        return state

    def restore_jammers(self, original):
        state = copy.deepcopy(original)
        changed = any(j["active"] for j in state.get("jammers") or [])
        for jammer in state.get("jammers") or []:
            jammer["active"] = False
        if changed:
            emit(state, "COMMUNICATION", "Todos los jammers desactivados · enlaces en recuperación")
        self._apply_jammers(state)
        return state

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
        route, duration = state["route"], state["duration"]
        launches = state.get("drones_launch") or [0]
        faults = state.get("drone_faults") or {}
        drones = []
        for i, launch in enumerate(launches):
            elapsed_i = max(0, state["elapsed"] - launch)
            drone = self._drone_telemetry(route, duration, elapsed_i, f"UAV-{i + 1:02d}")
            fault = faults.get(str(i), 0)
            if fault:
                drone["altitude"] = max(0, round(drone["altitude"] - fault * 6))
            drones.append(drone)
        state["drones"] = drones
