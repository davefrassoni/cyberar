import json
import mimetypes
from django.conf import settings
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from authentication.security import authenticated, rate_allowed
from mission.service import ensure_mission, serialize, control
from mission.models import MissionState
from mission import debrief


@require_GET
def index(request):
    file = settings.FRONTEND_DIST / "index.html"
    if not file.is_file(): return JsonResponse({"detail": "Ejecutá npm run build en frontend/"}, status=503)
    response = HttpResponse(file.read_bytes(), content_type="text/html")
    response["Cache-Control"] = "no-store"
    response["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    return response


@require_GET
def asset(request, name):
    file = settings.FRONTEND_DIST / "assets" / name
    if not file.is_file() or file.parent != settings.FRONTEND_DIST / "assets": raise Http404
    return HttpResponse(file.read_bytes(), content_type=mimetypes.guess_type(file)[0] or "application/octet-stream")


@require_GET
@authenticated
def state(request):
    mission = ensure_mission(request.session.session_key, request.session.get("cyberar_ai_disabled", False))
    response = JsonResponse(serialize(mission.live))
    response["Cache-Control"] = "no-store"
    return response


@require_GET
@authenticated
def debrief_state(request):
    mission = ensure_mission(request.session.session_key, request.session.get("cyberar_ai_disabled", False))
    response = JsonResponse(debrief.serialize(mission))
    response["Cache-Control"] = "no-store"
    return response


@require_POST
@authenticated
def command(request):
    if not rate_allowed("control", request.session.session_key, 90, 60):
        return JsonResponse({"detail": "Demasiadas acciones. Esperá un minuto."}, status=429)
    try:
        body = json.loads(request.body)
        if not isinstance(body, dict): raise ValueError("Solicitud inválida")
        mission = ensure_mission(request.session.session_key, request.session.get("cyberar_ai_disabled", False))
        return JsonResponse(control(mission.id, request.session.session_key, body))
    except (ValueError, TypeError) as error:
        return JsonResponse({"detail": str(error)}, status=400)
