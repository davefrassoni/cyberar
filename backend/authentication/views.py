import json
import secrets
from django.conf import settings
from django.http import JsonResponse
from django.middleware.csrf import get_token, rotate_token
from django.views.decorators.http import require_GET, require_POST
from .security import rate_allowed


@require_GET
def session(request):
    response = JsonResponse({"authenticated": bool(request.session.get("cyberar_authenticated")), "csrf": get_token(request)})
    response["Cache-Control"] = "no-store"
    return response


@require_POST
def login(request):
    # Nginx replaces X-Real-IP; the ASGI listener is bound to loopback only.
    ip = request.META.get("HTTP_X_REAL_IP", request.META.get("REMOTE_ADDR", "unknown"))
    if not rate_allowed("login", ip, 8, 300):
        response = JsonResponse({"detail": "Demasiados intentos. Esperá cinco minutos."}, status=429)
        response["Retry-After"] = "300"
        return response
    try:
        body = json.loads(request.body)
        user, password = body["username"], body["password"]
        if not isinstance(user, str) or not isinstance(password, str): raise ValueError
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"detail": "Solicitud inválida"}, status=400)
    valid_user = secrets.compare_digest(user.encode(), settings.CYBERAR_USER.encode())
    valid_password = secrets.compare_digest(password.encode(), settings.CYBERAR_PASSWORD.encode())
    is_real = bool(settings.CYBERAR_USER and settings.CYBERAR_PASSWORD and valid_user and valid_password)
    is_demo = bool(
        settings.CYBERAR_DEMO_ENABLED
        and secrets.compare_digest(user.encode(), settings.CYBERAR_DEMO_USER.encode())
        and secrets.compare_digest(password.encode(), settings.CYBERAR_DEMO_PASSWORD.encode())
    )
    if not (is_real or is_demo):
        return JsonResponse({"detail": "Credenciales incorrectas"}, status=401)
    if not request.session.get("cyberar_authenticated"):
        request.session.flush()
    request.session["cyberar_authenticated"] = True
    # Real credentials always win if they happen to coincide with the demo
    # pair (e.g. local dev, where both default to admin/admin).
    request.session["cyberar_ai_disabled"] = not is_real
    request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    request.session.save()
    rotate_token(request)
    return JsonResponse({"authenticated": True, "csrf": get_token(request)})


@require_POST
def logout(request):
    from mission.models import MissionState
    MissionState.objects.filter(mission__owner_session=request.session.session_key).update(running=False)
    request.session.flush()
    return JsonResponse({"authenticated": False})
