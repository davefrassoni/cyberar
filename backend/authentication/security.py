import hashlib
import time
from functools import wraps
from django.db import transaction
from django.http import JsonResponse
from mission.models import RateLimit


def rate_allowed(scope, identity, limit, seconds):
    key = scope + ":" + hashlib.sha256(identity.encode()).hexdigest()
    window = int(time.time()) // seconds
    with transaction.atomic():
        RateLimit.objects.get_or_create(key=key)
        row = RateLimit.objects.select_for_update().get(key=key)
        row.count = row.count + 1 if row.window == window else 1
        row.window = window
        row.save()
        return row.count <= limit


def authenticated(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.session.get("cyberar_authenticated"):
            return JsonResponse({"detail": "Iniciá sesión para continuar"}, status=401)
        return view(request, *args, **kwargs)
    return wrapped
