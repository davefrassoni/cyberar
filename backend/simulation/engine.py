"""Motor puro: sin reloj de pared, red, ORM ni dependencias de interfaz."""
import copy
import math
from enum import StrEnum
from communications.channels import metrics
from events.log import emit
from .scenario import DemoScenario, ROUTE


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
    def initial(self, duration=150):
        state = {"elapsed": 0, "duration": duration, "phase": Phase.PREPARING, "automatic": True,
                 "interference": 0, "active_channel": "RF-PRIMARY", "channels": metrics(),
                 "checkpoint_index": 0, "route": copy.deepcopy(ROUTE), "events": [], "event_sequence": 0}
        self._telemetry(state)
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
            t = DemoScenario(state["duration"]).time(state["elapsed"])
            for threshold, phase in [(1, Phase.TAKEOFF), (8, Phase.TRANSIT), (65, Phase.RECON), (100, Phase.RETURN), (145, Phase.LANDED), (150, Phase.MISSION_COMPLETE)]:
                if t >= threshold and phase in TRANSITIONS[state["phase"]]: self.transition(state, phase)
            index = max(i for i, cp in enumerate(ROUTE) if t >= cp["at"])
            if index != state["checkpoint_index"]:
                for i in range(state["checkpoint_index"] + 1, index + 1):
                    emit(state, "MISSION", f"{ROUTE[i]['id']} alcanzado")
                state["checkpoint_index"] = index
            if state["automatic"]:
                self.set_interference(state, DemoScenario(state["duration"]).interference(state["elapsed"]))
            self._telemetry(state)
        return state

    def set_interference(self, state, level):
        if type(level) not in (int, float) or not math.isfinite(level) or not 0 <= level <= 100:
            raise ValueError("Interferencia fuera de rango")
        if state["interference"] != level:
            state["interference"] = level
            emit(state, "WARNING" if level else "COMMUNICATION", f"Interferencia simulada: {level}%" if level else "Enlace recuperado · métricas nominales")
        state["channels"] = metrics(level)

    def _telemetry(self, state):
        t = DemoScenario(state["duration"]).time(state["elapsed"])
        index = min(state["checkpoint_index"], len(ROUTE) - 2)
        a, b = ROUTE[index:index+2]
        fraction = max(0, min(1, (t - a["at"]) / (b["at"] - a["at"])))
        x, y = a["x"] + (b["x"] - a["x"]) * fraction, a["y"] + (b["y"] - a["y"]) * fraction
        altitude = round(1420 * min(1, t / 8, max(0, (145 - t) / 8)))
        state["telemetry"] = {"x": round(x, 2), "y": round(y, 2), "latitude": round(-47 - y / 100, 5), "longitude": round(-69 + x / 100, 5),
                              "altitude": altitude, "heading": round(math.degrees(math.atan2(b["x"]-a["x"], a["y"]-b["y"])) % 360),
                              "speed": 82 if altitude else 0, "battery": round(100 - min(t, 150) * .21, 1), "gps_status": "ONLINE",
                              "distance_to_base": round(math.hypot(x-195, y-230) * .55, 1), "current_checkpoint": ROUTE[state["checkpoint_index"]]["id"],
                              "next_checkpoint": b["id"], "onboard_storage": 0, "timestamp": state["elapsed"]}
