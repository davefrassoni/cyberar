"""Patrulla y respuesta segura, gobernadas por el reloj del servidor."""
import copy
from events.log import emit
from .can import CANSimulationEngine, CANAnomalyDetector
from simulation.scenario import DemoScenario

ROUTE = [dict(id=name, x=x, y=y) for name, x, y in [
    ("BASE-UGV", 666, 252), ("T-01", 680, 238), ("T-02", 706, 242),
    ("T-03", 711, 264), ("OBSERVATION", 689, 294), ("RETURN", 666, 252)]]
DEFAULT_ASSET = "UGV-01"
DEFAULT_LABEL = "Vehículo terrestre costero"
ACTIONS = {"CONTINUE_MONITORING", "MARK_SIGNAL_UNTRUSTED", "ISOLATE_SIGNAL", "REDUCE_SPEED", "SAFE_STOP", "RETURN_TO_BASE"}
# Segundos simulados (misma escala normalizada que `t`) entre reverificaciones
# de integridad una vez aislada la señal: el monitoreo no termina en el primer
# análisis, se sigue confirmando periódicamente durante el resto de la misión.
REANALYSIS_INTERVAL = 15


class SafetyValidator:
    @staticmethod
    def validate(recommendation, ugv):
        action = recommendation.get("recommended_action")
        if action not in ACTIONS or recommendation.get("suspected_source") != "CAN_SPEED":
            raise ValueError("Recomendación no permitida")
        confidence = recommendation.get("confidence")
        if type(confidence) not in (int, float) or not 0 <= confidence <= 1:
            raise ValueError("Confianza inválida")
        if action != "CONTINUE_MONITORING" and (ugv["detector"]["score"] < ugv["threshold"] or confidence < .7):
            raise ValueError("Evidencia insuficiente para ejecutar la recomendación")
        return action


def initial(threshold=80, route=None, asset=None, label=None):
    route = copy.deepcopy(route) if route else copy.deepcopy(ROUTE)
    asset = asset or DEFAULT_ASSET
    label = label or DEFAULT_LABEL
    messages = CANSimulationEngine().sample(0, 0, 0)
    return {"asset": asset, "label": label, "route": route, "position": copy.deepcopy(route[0]),
            "progress": 0, "checkpoint": route[0]["id"], "speed": 0, "status": "OPERATIVO",
            "stage": "PATRULLA NORMAL", "level": 0, "manual": False, "incident": 0,
            "history": [], "messages": messages, "threshold": threshold, "untrusted": False,
            "safe_stop": False, "returning": False, "reduced": False,
            "detector": CANAnomalyDetector().analyze(messages, 0, 0, []),
            "analysis": {"status": "IDLE", "source": "LOCAL", "requested_at": None, "result": None},
            "milestones": [], "alert_at": None, "analysis_runs": 0,
            "next_reanalysis_at": None, "reanalysis_requested_at": None}


def control(state, action):
    ugv = state.setdefault("ugv", initial())
    ugv["manual"] = True
    if action == "can_restore":
        threshold, position, progress = ugv["threshold"], ugv["position"], ugv["progress"]
        route, asset, label = ugv["route"], ugv["asset"], ugv["label"]
        incident = ugv["incident"] + 1
        ugv.update(initial(threshold, route, asset, label))
        ugv.update(manual=True, incident=incident, position=position, progress=progress)
        emit(state, "CAN", "CAN restaurado · historial y evidencia reiniciados")
    else:
        ugv["level"] = min(100, ugv["level"] + (30 if action == "can_increase" else 15))
        emit(state, "CAN", "Escenario SILENT_CAN_MANIPULATION ajustado · tráfico ficticio")


def apply_recommendation(state, recommendation, source):
    ugv = state["ugv"]
    action = SafetyValidator.validate(recommendation, ugv)
    if action in {"MARK_SIGNAL_UNTRUSTED", "ISOLATE_SIGNAL"}:
        ugv["untrusted"] = True
        ugv["reduced"] = True
        emit(state, "SYSTEM", "CAN SPEED no confiable · señal aislada por SafetyValidator")
        emit(state, "UGV", "Modo degradado · GPS + IMU · continuando hacia punto seguro")
    elif action == "REDUCE_SPEED": ugv["reduced"] = True
    elif action == "SAFE_STOP": ugv["safe_stop"] = True
    elif action == "RETURN_TO_BASE":
        ugv["returning"] = True
        ugv["reduced"] = True
    ugv["analysis"].update(status="COMPLETED", source=source, result=recommendation)


def update(state, t):
    ugv = state.setdefault("ugv", initial())
    route = ugv["route"]
    last = len(route) - 1
    if not ugv["manual"]:
        ugv["level"] = DemoScenario(state["duration"]).can_manipulation(state["elapsed"])
    speed = 0 if t == 0 or ugv["safe_stop"] or ugv["progress"] >= last else (9 if ugv["reduced"] else 33)
    ugv["speed"] = speed
    dt = 150 / state["duration"]
    ugv["progress"] = min(last, ugv["progress"] + dt / 29 * speed / 33)
    index = min(last - 1, int(ugv["progress"]))
    a, b = route[index:index+2]
    f = ugv["progress"] - index
    if ugv["returning"]:
        import math
        b = route[-1]
        position = ugv["position"]
        distance = math.hypot(b["x"]-position["x"], b["y"]-position["y"])
        fraction = min(1, dt * speed / 33 / max(distance, .001))
        ugv["position"] = {axis: round(position[axis]+(b[axis]-position[axis])*fraction, 2) for axis in ("x", "y")}
        if fraction == 1: ugv["safe_stop"] = True
    elif not ugv["safe_stop"]:
        ugv["position"] = {"x": round(a["x"]+(b["x"]-a["x"])*f, 2), "y": round(a["y"]+(b["y"]-a["y"])*f, 2)}
    ugv["checkpoint"] = b["id"]
    # The bad signal remains inconsistent even after the independent estimator slows the vehicle.
    reported_speed = 33 if ugv["untrusted"] else speed
    ugv["messages"] = CANSimulationEngine().sample(state["elapsed"], reported_speed, ugv["level"])
    gps, imu = speed, max(0, speed-1)
    result = CANAnomalyDetector().analyze(ugv["messages"], gps, imu, ugv["history"])
    ugv["detector"] = result
    ugv["history"] = (ugv["history"] + [dict(timestamp=state["elapsed"], **result["sample"], score=result["score"])])[-40:]
    score = result["score"]
    stage = "ANOMALÍA CAN" if score >= ugv["threshold"] else "CORRELACIONANDO SENSORES…" if score >= 60 else "INCONSISTENCIA DETECTADA" if score >= 40 else "ANALIZANDO COMPORTAMIENTO…" if score >= 20 else "PATRULLA NORMAL"
    if ugv["untrusted"]: stage = "ANOMALÍA AISLADA"
    ugv["status"] = "MODO DEGRADADO" if ugv["untrusted"] or ugv["reduced"] else "ANOMALÍA" if score >= ugv["threshold"] else "INVESTIGANDO" if score >= 20 else "OPERATIVO"
    if ugv["safe_stop"]: ugv["status"] = "DETENIDO EN ZONA SEGURA"
    if stage not in ugv["milestones"]:
        ugv["milestones"].append(stage)
        emit(state, "WARNING" if stage == "ANOMALÍA CAN" else "CAN", f"{ugv['asset']} · {stage}")
    ugv["stage"] = stage
    if score >= ugv["threshold"] and ugv["alert_at"] is None:
        ugv["alert_at"] = t
        ugv["analysis"].update(status="PENDING", requested_at=state["elapsed"])
        ugv["analysis_runs"] += 1
        ugv["next_reanalysis_at"] = t + REANALYSIS_INTERVAL
        emit(state, "SYSTEM", "Evidencia CAN suficiente · análisis P1 pendiente")
    # Local fallback is explicit, and never waits on the availability of a model.
    if ugv["alert_at"] is not None and t-ugv["alert_at"] >= 8 and not ugv["untrusted"] and score >= ugv["threshold"]:
        apply_recommendation(state, {"severity": "HIGH", "assessment": "CAN SPEED contradice GPS e IMU de forma persistente. Se descarta la señal y se reduce la velocidad.",
            "suspected_source": "CAN_SPEED", "confidence": .94, "recommended_action": "ISOLATE_SIGNAL"}, "LOCAL")
    # Monitoreo continuo: aislar la señal una vez no cierra el caso. Se sigue
    # reverificando la integridad cada REANALYSIS_INTERVAL, con el mismo
    # respaldo local explícito de 8s si el broker no contesta a tiempo —
    # nunca se queda esperando indefinidamente a un modelo externo. Se
    # reverifica en base al estado aislado, no al score del momento: una vez
    # aislada la señal, la fuente confiable (GPS/IMU) baja el score por
    # diseño, y eso no significa que ya no haga falta seguir confirmando.
    if ugv["untrusted"]:
        status = ugv["analysis"]["status"]
        if status in ("COMPLETED", "REJECTED") and t >= ugv["next_reanalysis_at"]:
            ugv["analysis"].update(status="PENDING", requested_at=state["elapsed"])
            ugv["analysis_runs"] += 1
            ugv["reanalysis_requested_at"] = t
            emit(state, "SYSTEM", "Reverificación periódica de integridad CAN · análisis pendiente")
        # Times out on PENDING/SUBMITTING/WAITING alike — not just PENDING. If the
        # broker claims this reanalysis (flips it to SUBMITTING/WAITING) and then
        # stalls (a delivery failure, a slow callback, the shared flight going to
        # someone else's mission), this must still resolve on its own; otherwise
        # the panel is left showing "queued" forever with nothing actually queued.
        elif status in ("PENDING", "SUBMITTING", "WAITING") and ugv["reanalysis_requested_at"] is not None \
                and t - ugv["reanalysis_requested_at"] >= 8:
            apply_recommendation(state, {"severity": "LOW", "assessment": "Reverificación local: CAN SPEED continúa aislado, GPS e IMU siguen consistentes entre sí.",
                "suspected_source": "CAN_SPEED", "confidence": .9, "recommended_action": "CONTINUE_MONITORING"}, "LOCAL")
            ugv["next_reanalysis_at"] = t + REANALYSIS_INTERVAL
            emit(state, "CAN", "Reverificación local confirmada · señal continúa aislada")
