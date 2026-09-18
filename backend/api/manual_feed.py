"""Proxy same-origin para el video de referencia de la cabina de control
manual. El share público de DF Drive sirve el archivo como adjunto genérico
(application/octet-stream, Content-Disposition: attachment) resuelto detrás
de un job de descarga asincrónico — <video> no reproduce eso inline, y
consultarlo directo desde el navegador choca con CORS/CSP cuando esta app no
comparte origen con davefrassoni.com (desarrollo local). Este endpoint
resuelve el job del lado del servidor (sin esas restricciones), reenvía el
header Range del cliente para permitir seek real, y transmite los bytes en
streaming con Content-Type video/mp4."""
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from django.conf import settings
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_GET
from authentication.security import authenticated

_JOB_POLL_ATTEMPTS = 6
_JOB_POLL_DELAY_SECONDS = 1
_CONTENT_URL_TTL_SECONDS = 1800
_CHUNK_BYTES = 65536
# davefrassoni.com está detrás de protección anti-bot que rechaza clientes
# sin User-Agent de navegador (ver docs/verification.md).
_USER_AGENT = "Mozilla/5.0 CYBER.AR manual-feed proxy"
# El content_url resuelto (job de descarga ya completado en el origen) se
# reusa entre requests — cada seek del reproductor dispara un nuevo Range
# request y no debería repetir el round-trip de creación/polling del job.
_cache = {"content_url": "", "expires_at": 0.0}


def _fetch_json(url, timeout=10):
    with urlopen(Request(url, headers={"User-Agent": _USER_AGENT}), timeout=timeout) as response:
        return json.loads(response.read(65536))


def _resolve_content_url():
    now = time.monotonic()
    if _cache["content_url"] and _cache["expires_at"] > now:
        return _cache["content_url"]
    data = _fetch_json(f"{settings.CYBERAR_MANUAL_FEED_URL}/download/")
    if data.get("status") != "completed" or not data.get("content_url"):
        job_id = data["job_id"]
        for _ in range(_JOB_POLL_ATTEMPTS):
            time.sleep(_JOB_POLL_DELAY_SECONDS)
            data = _fetch_json(f"{settings.CYBERAR_MANUAL_FEED_URL}/jobs/{job_id}/")
            if data.get("status") == "completed" and data.get("content_url"):
                break
            if data.get("status") == "failed":
                raise ValueError(data.get("error") or "Falló la carga del video en el origen.")
        else:
            raise TimeoutError("Tiempo de espera agotado cargando el video en el origen.")
    content_url = "https://davefrassoni.com" + data["content_url"]
    _cache.update(content_url=content_url, expires_at=now + _CONTENT_URL_TTL_SECONDS)
    return content_url


def _stream(upstream):
    with upstream:
        while True:
            chunk = upstream.read(_CHUNK_BYTES)
            if not chunk:
                return
            yield chunk


@require_GET
@authenticated
def manual_feed(request):
    try:
        content_url = _resolve_content_url()
    except (HTTPError, URLError, ValueError, TimeoutError, KeyError, json.JSONDecodeError):
        _cache.update(content_url="", expires_at=0.0)
        return JsonResponse({"detail": "No se pudo cargar el video de referencia."}, status=502)

    headers = {"User-Agent": _USER_AGENT}
    range_header = request.headers.get("Range")
    if range_header:
        headers["Range"] = range_header
    try:
        upstream = urlopen(Request(content_url, headers=headers), timeout=30)
    except HTTPError as error:
        if error.code == 416:
            response = HttpResponse(status=416)
            response["Content-Range"] = error.headers.get("Content-Range", "")
            return response
        _cache.update(content_url="", expires_at=0.0)
        return JsonResponse({"detail": "No se pudo descargar el video de referencia."}, status=502)
    except URLError:
        _cache.update(content_url="", expires_at=0.0)
        return JsonResponse({"detail": "No se pudo descargar el video de referencia."}, status=502)

    response = StreamingHttpResponse(_stream(upstream), status=upstream.status, content_type="video/mp4")
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "private, max-age=3600"
    for header in ("Content-Range", "Content-Length"):
        value = upstream.headers.get(header)
        if value:
            response[header] = value
    return response
