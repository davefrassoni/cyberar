"""Debriefing posterior a la misión: comparación de sensores de flota + insight DF AI."""
import json
import logging
import math
import secrets
import statistics
import uuid
from datetime import timedelta
from urllib.request import Request, urlopen
from django.conf import settings
from django.db import transaction, close_old_connections
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from events.log import emit
from .models import DebriefFlight, MissionState, TelemetrySnapshot

DRONE_IDS = ["UAV-01", "UAV-02", "UAV-03", "NONE"]
COMPONENTS = ["ALTITUDE_SENSOR", "GPS", "BATTERY", "SPEED_SENSOR", "NONE"]
FIELDS = ("altitude", "speed", "battery")
DEVIATION_THRESHOLDS = {"altitude": 40, "speed": 8, "battery": 5}

SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["overall_assessment", "suspect_drone", "suspect_component", "confidence", "findings"],
          "properties": {
              "overall_assessment": {"type": "string", "maxLength": 600},
              "suspect_drone": {"type": "string", "enum": DRONE_IDS},
              "suspect_component": {"type": "string", "enum": COMPONENTS},
              "confidence": {"type": "number", "minimum": 0, "maximum": 1},
              "findings": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 200}}}}


def telemetry_series(mission):
    rows = TelemetrySnapshot.objects.filter(mission=mission).order_by("elapsed")
    series = []
    for row in rows:
        if not isinstance(row.data, list): continue
        series.append({"elapsed": row.elapsed, "drones": row.data})
    return series[-200:]


def snapshot_for(mission):
    series = telemetry_series(mission)
    by_id = {}
    for point in series:
        for drone in point["drones"]:
            by_id.setdefault(drone["id"], []).append(drone)
    drones = []
    for drone_id in sorted(by_id):
        samples = by_id[drone_id]
        stats = {}
        for field in FIELDS:
            values = [s[field] for s in samples]
            stats[field] = {"mean": round(statistics.fmean(values), 2) if values else 0,
                             "stdev": round(statistics.pstdev(values), 2) if len(values) > 1 else 0}
        drones.append({"id": drone_id, "samples": len(samples), **stats})
    return {"drones": drones, "points": len(series)}


def local_insight(snapshot):
    drones = snapshot["drones"]
    if len(drones) < 2:
        return {"overall_assessment": "Se necesitan al menos dos drones en la misma ruta para comparar sensores entre sí.",
                "suspect_drone": "NONE", "suspect_component": "NONE", "confidence": 0.4, "findings": []}
    component_by_field = {"altitude": "ALTITUDE_SENSOR", "speed": "SPEED_SENSOR", "battery": "BATTERY"}
    label_by_field = {"altitude": "altitud", "speed": "velocidad", "battery": "batería"}
    findings, best = [], None
    for field, component in component_by_field.items():
        means = [d[field]["mean"] for d in drones]
        median = statistics.median(means)
        for drone in drones:
            deviation = abs(drone[field]["mean"] - median)
            if deviation > DEVIATION_THRESHOLDS[field]:
                findings.append(f"{drone['id']}: {field} promedio {drone[field]['mean']} vs. mediana de flota {round(median, 1)} (Δ{round(deviation, 1)})")
                if best is None or deviation > best["deviation"]:
                    best = {"drone": drone["id"], "component": component, "field": field, "deviation": deviation}
    if best is None:
        return {"overall_assessment": "Los sensores de altitud, velocidad y batería son consistentes entre los drones de la flota; no se detecta un componente sospechoso.",
                "suspect_drone": "NONE", "suspect_component": "NONE", "confidence": 0.85, "findings": findings[:5]}
    confidence = round(min(0.95, 0.5 + best["deviation"] / 200), 2)
    assessment = (f"{best['drone']} reporta una desviación sostenida en su sensor de {label_by_field[best['field']]} "
                  f"respecto al resto de la flota, que voló la misma ruta. Se recomienda inspeccionar ese componente.")
    return {"overall_assessment": assessment, "suspect_drone": best["drone"], "suspect_component": best["component"],
            "confidence": confidence, "findings": findings[:5]}


def request(live):
    snapshot = snapshot_for(live.mission)
    result = local_insight(snapshot)
    now = timezone.now()
    DebriefFlight.objects.update_or_create(pk=1, defaults={
        "mission": live.mission, "generation": live.generation, "key": "cyberar-debrief-" + str(uuid.uuid4()),
        "job_id": "", "status": "PENDING", "snapshot": snapshot, "result": result, "source": "LOCAL",
        "attempts": 0, "next_attempt": now, "requested_at": now})
    emit(live.state, "DF AI", "Debriefing solicitado · insight local instantáneo, análisis DF AI en curso")


class DebriefAIClient:
    def submit(self, flight):
        payload = {"job_type": "prompt_json", "priority": 2, "idempotency_key": flight.key,
                   "payload": {"kind": "cyberar_fleet_debrief", "messages": [
                       {"role": "system", "content": "Analizá telemetría comparada de una flota de drones en una simulación software que voló la misma ruta. Respondé únicamente un objeto JSON con exactamente las propiedades del siguiente JSON Schema. overall_assessment y findings deben estar en español argentino; los enums deben conservar sus valores exactos. No agregues campos adicionales. No ejecutás acciones. JSON Schema: " + json.dumps(SCHEMA)},
                       {"role": "user", "content": json.dumps(flight.snapshot)}],
                       "response_schema": SCHEMA, "temperature": 0, "num_predict": 600}}
        request_obj = Request(settings.DF_AI_URL + "/api/ai/jobs/", data=json.dumps(payload).encode(), headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + settings.DF_AI_TOKEN,
            "X-AI-Project": "cyberar", "Host": settings.DF_AI_HOST})
        with urlopen(request_obj, timeout=settings.CYBERAR_AI_TIMEOUT) as response:
            body = json.loads(response.read(65536))
        return str(uuid.UUID(body["id"]))


@transaction.atomic
def _reserve():
    flight = DebriefFlight.objects.select_for_update().filter(pk=1).first()
    if flight and flight.status == "PENDING" and flight.attempts < 3 and flight.next_attempt <= timezone.now():
        return flight
    return None


def process():
    if not settings.CYBERAR_AI_ENABLED or not settings.DF_AI_TOKEN or not settings.DF_AI_CALLBACK_TOKEN:
        return
    close_old_connections()
    try:
        flight = _reserve()
        if not flight: return
        DebriefFlight.objects.filter(pk=1, key=flight.key).update(
            attempts=flight.attempts + 1, next_attempt=timezone.now() + timedelta(seconds=10 * 2 ** flight.attempts))
        try:
            job_id = DebriefAIClient().submit(flight)
        except (OSError, ValueError, KeyError, TypeError):
            # Ambiguous delivery must not release the single-flight slot; the LOCAL insight already stands.
            return
        DebriefFlight.objects.filter(pk=1, key=flight.key, status="PENDING").update(job_id=job_id, status="WAITING")
    except Exception:
        logging.getLogger(__name__).exception("No se pudo procesar el debriefing DF AI")
    finally:
        close_old_connections()


def parse_result(raw):
    if isinstance(raw, dict) and "content" in raw: raw = raw["content"]
    if isinstance(raw, str): raw = json.loads(raw)
    if not isinstance(raw, dict) or set(raw) != set(SCHEMA["required"]): raise ValueError("Esquema inválido")
    if raw["suspect_drone"] not in DRONE_IDS: raise ValueError("Dron sospechoso inválido")
    if raw["suspect_component"] not in COMPONENTS: raise ValueError("Componente sospechoso inválido")
    if not isinstance(raw["overall_assessment"], str) or not 1 <= len(raw["overall_assessment"]) <= 600:
        raise ValueError("Texto inválido")
    if type(raw["confidence"]) not in (int, float) or not math.isfinite(raw["confidence"]) or not 0 <= raw["confidence"] <= 1:
        raise ValueError("Confianza inválida")
    findings = raw["findings"]
    if not isinstance(findings, list) or len(findings) > 5 or not all(isinstance(f, str) and len(f) <= 200 for f in findings):
        raise ValueError("Hallazgos inválidos")
    return raw


@csrf_exempt
@require_POST
def callback(request):
    token = settings.DF_AI_CALLBACK_TOKEN
    if not token or not secrets.compare_digest(request.headers.get("Authorization", "").encode(), ("Bearer " + token).encode()):
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
        flight = DebriefFlight.objects.select_for_update().filter(pk=1).first()
        if not flight or not flight.job_id or flight.job_id != body.get("job_id"):
            return JsonResponse({"detail": "Job no reconocido"}, status=409)
        if flight.status == "DONE": return JsonResponse({"accepted": True})
        live = MissionState.objects.select_for_update().filter(mission=flight.mission).first()
        if result is not None and live is not None and live.generation == flight.generation:
            flight.result = result
            flight.source = "DF AI"
        flight.status = "DONE"
        flight.save(update_fields=["status", "result", "source"])
    return JsonResponse({"accepted": result is not None})


def serialize(mission):
    flight = DebriefFlight.objects.filter(pk=1, mission=mission).first()
    if not flight:
        return {"status": "NONE", "source": None, "result": None, "requested_at": None, "series": telemetry_series(mission)}
    return {"status": flight.status, "source": flight.source, "result": flight.result,
            "requested_at": flight.requested_at.isoformat() if flight.requested_at else None,
            "series": telemetry_series(mission)}
