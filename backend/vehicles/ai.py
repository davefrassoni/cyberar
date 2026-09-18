"""Broker DF AI: un único vuelo persistido, callback autenticado y respaldo local."""
import json
import secrets
import uuid
import logging
from datetime import timedelta
from urllib.request import Request, urlopen
from django.conf import settings
from django.db import transaction, close_old_connections
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from events.log import emit
from mission.models import AIFlight, MissionState
from .ugv import ACTIONS, apply_recommendation

SCHEMA = {"type": "object", "additionalProperties": False, "required": ["severity", "assessment", "suspected_source", "confidence", "recommended_action"], "properties": {
    "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
    "assessment": {"type": "string", "maxLength": 500},
    "suspected_source": {"type": "string", "enum": ["CAN_SPEED"]},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "recommended_action": {"type": "string", "enum": sorted(ACTIONS)}}}


class DFAIClient:
    def submit(self, flight):
        payload = {"job_type": "prompt_json", "priority": 1, "idempotency_key": flight.key,
                   "payload": {"kind": "cyberar_can_anomaly", "messages": [{"role": "system", "content": "Analizá evidencia de una simulación software de UGV. Respondé únicamente un objeto JSON con exactamente las propiedades del siguiente JSON Schema. assessment debe estar en español argentino; los enums deben conservar sus valores exactos. No agregues timestamp ni campos adicionales. No ejecutás acciones. Una señal válida no necesariamente contiene información confiable. JSON Schema: " + json.dumps(SCHEMA)},
                                             {"role": "user", "content": json.dumps(flight.snapshot)}],
                               "response_schema": SCHEMA, "temperature": 0, "num_predict": 500}}
        request = Request(settings.DF_AI_URL + "/api/ai/jobs/", data=json.dumps(payload).encode(), headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + settings.DF_AI_TOKEN,
            "X-AI-Project": "cyberar", "Host": settings.DF_AI_HOST})
        with urlopen(request, timeout=settings.CYBERAR_AI_TIMEOUT) as response:
            body = json.loads(response.read(65536))
        return str(uuid.UUID(body["id"]))


@transaction.atomic
def reserve():
    flight = AIFlight.objects.select_for_update().filter(pk=1).first()
    if flight and flight.status != "DONE":
        if flight.status == "PENDING" and flight.attempts < 3 and flight.next_attempt <= timezone.now():
            return flight
        if flight.status == "PENDING" and flight.attempts >= 3:
            # Delivery failed 3 times in a row: this mission's own local fallback
            # already covers it (the 8s timeout doesn't wait on AIFlight state).
            # Abandoning the slot here matters for every *other* mission — this
            # is the single shared flight, and leaving it permanently non-DONE
            # would otherwise block CAN analysis app-wide forever.
            AIFlight.objects.filter(pk=1, key=flight.key, status="PENDING").update(status="DONE")
        return None
    for live in MissionState.objects.filter(running=True, mission__ai_disabled=False).order_by("mission_id"):
        ugv = live.state.get("ugv", {})
        analysis = ugv.get("analysis", {})
        if analysis.get("status") != "PENDING": continue
        # Lock the mission only after the flight slot, matching the callback lock order.
        live = MissionState.objects.select_for_update().get(pk=live.pk)
        ugv = live.state.get("ugv", {})
        if ugv.get("analysis", {}).get("status") != "PENDING": continue
        sample = ugv["detector"]["sample"]
        snapshot = {"asset": "UGV-01", "type": "CAN_ANOMALY", "mission_phase": "PATROL",
                    "can": {"speed": sample["can"], "expected_speed": sample["gps"], "message_frequency": 10},
                    "gps": {"speed": sample["gps"]}, "imu": {"estimated_speed": sample["imu"]},
                    "anomaly_score": ugv["detector"]["score"] / 100, "evidence": ugv["detector"]["evidence"]}
        flight, _ = AIFlight.objects.update_or_create(pk=1, defaults={"mission": live.mission,
            "generation": live.generation, "incident": ugv["incident"], "key": "cyberar-"+str(uuid.uuid4()),
            "snapshot": snapshot, "status": "PENDING", "attempts": 0, "job_id": "", "next_attempt": timezone.now()})
        ugv["analysis"].update(status="SUBMITTING", source="DF AI")
        emit(live.state, "DF AI", "Análisis CAN solicitado P1 · único vuelo")
        live.revision += 1
        live.save()
        from mission.service import persist_events
        persist_events(live)
        return flight
    return None


def process():
    if not settings.CYBERAR_AI_ENABLED or not settings.DF_AI_TOKEN or not settings.DF_AI_CALLBACK_TOKEN:
        return
    close_old_connections()
    try:
        flight = reserve()
        if not flight: return
        # Persist retry budget before network I/O; timeouts reuse the same idempotency key.
        AIFlight.objects.filter(pk=1, key=flight.key).update(attempts=flight.attempts+1, next_attempt=timezone.now()+timedelta(seconds=10 * 2**flight.attempts))
        try:
            job_id = DFAIClient().submit(flight)
        except (OSError, ValueError, KeyError, TypeError):
            # Ambiguous delivery must not release the single-flight slot. The local
            # detector still isolates the signal while this circuit remains open.
            return
        AIFlight.objects.filter(pk=1, key=flight.key, status="PENDING").update(job_id=job_id, status="WAITING")
    except Exception:
        logging.getLogger(__name__).exception("No se pudo procesar el análisis DF AI")
    finally:
        close_old_connections()


def parse_result(raw):
    if isinstance(raw, dict) and "content" in raw: raw = raw["content"]
    if isinstance(raw, str): raw = json.loads(raw)
    if not isinstance(raw, dict) or set(raw) != set(SCHEMA["required"]): raise ValueError("Esquema inválido")
    if raw["severity"] not in {"LOW", "MEDIUM", "HIGH"}: raise ValueError("Severidad inválida")
    if not isinstance(raw["assessment"], str) or not 1 <= len(raw["assessment"]) <= 500: raise ValueError("Texto inválido")
    if raw["suspected_source"] != "CAN_SPEED" or raw["recommended_action"] not in ACTIONS: raise ValueError("Acción inválida")
    if type(raw["confidence"]) not in (int, float) or not 0 <= raw["confidence"] <= 1: raise ValueError("Confianza inválida")
    return raw


@csrf_exempt
@require_POST
def callback(request):
    token = settings.DF_AI_CALLBACK_TOKEN
    if not token or not secrets.compare_digest(request.headers.get("Authorization", "").encode(), ("Bearer "+token).encode()):
        return JsonResponse({"detail": "Credenciales inválidas"}, status=403)
    try:
        if len(request.body) > 16384: raise ValueError("Respuesta demasiado grande")
        body = json.loads(request.body)
        if not isinstance(body, dict) or body.get("job_type") != "prompt_json": raise ValueError("Tipo inválido")
    except (ValueError, TypeError):
        return JsonResponse({"detail": "Respuesta inválida"}, status=400)
    try:
        result = parse_result(body.get("result"))
    except (ValueError, TypeError):
        result = None
    with transaction.atomic():
        flight = AIFlight.objects.select_for_update().filter(pk=1).first()
        if not flight or not flight.job_id or flight.job_id != body.get("job_id"):
            return JsonResponse({"detail": "Job no reconocido"}, status=409)
        if flight.status == "DONE": return JsonResponse({"accepted": True})
        live = MissionState.objects.select_for_update().get(mission=flight.mission)
        ugv = live.state.get("ugv", {})
        if live.generation == flight.generation and ugv.get("incident") == flight.incident:
            try:
                if result is None:
                    # Terminal regardless of `untrusted`: this must always resolve, or a
                    # periodic re-verification response with a bad schema would leave
                    # analysis.status stuck forever, freezing every future re-check.
                    ugv["analysis"].update(status="REJECTED", source="LOCAL", result=None)
                    emit(live.state, "DF AI", "Respuesta descartada: esquema inválido · respaldo local activo")
                elif ugv.get("untrusted"):
                    ugv["analysis"].update(status="COMPLETED", source="DF AI", result=result)
                    emit(live.state, "DF AI", "Análisis recibido · aislamiento local ya aplicado; sin nueva acción")
                else:
                    apply_recommendation(live.state, result, "DF AI")
                live.revision += 1
                live.save()
                from mission.service import persist_events
                persist_events(live)
            except ValueError:
                emit(live.state, "SYSTEM", "SafetyValidator rechazó recomendación DF AI · respaldo local activo")
                live.revision += 1
                live.save()
                from mission.service import persist_events
                persist_events(live)
        flight.status = "DONE"
        flight.save(update_fields=["status"])
    return JsonResponse({"accepted": result is not None})
