from django.conf import settings
from django.db import transaction
from django.contrib.sessions.models import Session
from django.utils import timezone
from events.log import emit
from simulation.engine import SimulationEngine, Phase
from vehicles import ugv
from .models import Mission, MissionState, DemoScenario, MissionEvent, TelemetrySnapshot, CommunicationSnapshot

engine = SimulationEngine()


def persist_events(live):
    last = MissionEvent.objects.filter(mission=live.mission).order_by("-sequence").values_list("sequence", flat=True).first() or 0
    MissionEvent.objects.bulk_create([MissionEvent(mission=live.mission, **event) for event in live.state["events"] if event["sequence"] > last])


def snapshot(live):
    TelemetrySnapshot.objects.create(mission=live.mission, elapsed=live.state["elapsed"], data=live.state["telemetry"])
    CommunicationSnapshot.objects.create(mission=live.mission, elapsed=live.state["elapsed"], data=live.state["channels"])


@transaction.atomic
def ensure_mission(session_key):
    # A session row serializes simultaneous first requests from multiple tabs.
    Session.objects.select_for_update().get(session_key=session_key)
    mission = Mission.objects.filter(owner_session=session_key).first()
    if mission is None:
        scenario = DemoScenario.objects.create(duration=settings.CYBERAR_DEMO_DURATION, configuration={"engine": "atlantic-v1"})
        mission = Mission.objects.create(owner_session=session_key, scenario=scenario)
        live = MissionState.objects.create(mission=mission, state=engine.initial(scenario.duration, settings.CYBERAR_CAN_THRESHOLD))
        persist_events(live)
        snapshot(live)
    return mission


def serialize(live):
    state = dict(live.state)
    state.setdefault("ugv", ugv.initial(settings.CYBERAR_CAN_THRESHOLD))
    return {"mission_id": str(live.mission_id), "revision": live.revision, "running": live.running, "speed": live.speed, **state}


@transaction.atomic
def control(mission_id, owner, body):
    live = MissionState.objects.select_for_update().select_related("mission__scenario").get(mission_id=mission_id, mission__owner_session=owner)
    action = body.get("action")
    if action in {"reset", "automatic_demo"}:
        live.state = engine.initial(live.mission.scenario.duration, settings.CYBERAR_CAN_THRESHOLD)
        live.generation += 1
        live.running = action == "automatic_demo"
        live.speed = 1
        MissionEvent.objects.filter(mission=live.mission).delete()
        TelemetrySnapshot.objects.filter(mission=live.mission).delete()
        CommunicationSnapshot.objects.filter(mission=live.mission).delete()
        snapshot(live)
    elif action in {"can_start", "can_increase", "can_restore"}:
        ugv.control(live.state, action)
    elif action == "start":
        if live.state["phase"] == Phase.MISSION_COMPLETE: raise ValueError("Reiniciá la demo para comenzar otra misión")
        live.running = True
    elif action == "pause": live.running = False
    elif action == "speed":
        if type(body.get("value")) is not int or body["value"] not in (1, 2, 4): raise ValueError("Velocidad inválida")
        live.speed = body["value"]
    elif action == "automatic":
        if type(body.get("value")) is not bool: raise ValueError("Modo inválido")
        live.state["automatic"] = body["value"]
        emit(live.state, "SYSTEM", "Eventos automáticos" if body["value"] else "Control manual de interferencia")
    elif action in {"interference", "restore"}:
        live.state["automatic"] = False
        engine.set_interference(live.state, 0 if action == "restore" else body.get("value"))
    else: raise ValueError("Acción no permitida")
    live.revision += 1
    live.save()
    persist_events(live)
    return serialize(live)


@transaction.atomic
def tick(mission_id):
    live = MissionState.objects.select_for_update().select_related("mission").get(mission_id=mission_id)
    if not live.running: return
    if not Session.objects.filter(session_key=live.mission.owner_session, expire_date__gt=timezone.now()).exists():
        live.running = False
        live.save()
        return
    previous = live.state["phase"]
    previous_bucket = live.state["elapsed"] // 10
    live.state = engine.advance(live.state, live.speed)
    live.running = live.state["phase"] != Phase.MISSION_COMPLETE
    live.revision += 1
    live.save()
    persist_events(live)
    if live.state["elapsed"] // 10 != previous_bucket or live.state["phase"] != previous:
        snapshot(live)
