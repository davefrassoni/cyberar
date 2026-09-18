import os
from pathlib import Path
import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatorio")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CSRF_TRUSTED_ORIGINS = list(filter(None, os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")))
INSTALLED_APPS = ["django.contrib.contenttypes", "django.contrib.sessions", "mission", "simulation"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware"]
DATABASES = {"default": dj_database_url.config(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=0)}
ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "es-ar"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "cyberar_session"
SESSION_COOKIE_PATH = "/cyberar/"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = int(os.getenv("CYBERAR_SESSION_SECONDS", "7200"))
CSRF_COOKIE_NAME = "cyberar_csrf"
CSRF_COOKIE_PATH = "/cyberar/"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Strict"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CYBERAR_USER = os.getenv("CYBERAR_USER", "")
CYBERAR_PASSWORD = os.getenv("CYBERAR_PASSWORD", "")
CYBERAR_DEMO_DURATION = int(os.getenv("CYBERAR_DEMO_DURATION", "150"))
if CYBERAR_DEMO_DURATION < 30:
    raise ImproperlyConfigured("CYBERAR_DEMO_DURATION debe ser >= 30")
if not DEBUG and (len(CYBERAR_PASSWORD) < 16 or CYBERAR_PASSWORD == "admin"):
    raise ImproperlyConfigured("Configurá una contraseña de producción de al menos 16 caracteres")
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

# Public demo login (default admin/admin) — deliberately weak, always allowed
# even in production, separate from CYBERAR_USER/PASSWORD above. Missions it
# creates are flagged ai_disabled so a visitor never consumes the single
# shared DF AI flight slot meant for the presenter's own live demo.
CYBERAR_DEMO_ENABLED = os.getenv("CYBERAR_DEMO_ENABLED", "true").lower() == "true"
CYBERAR_DEMO_USER = os.getenv("CYBERAR_DEMO_USER", "admin")
CYBERAR_DEMO_PASSWORD = os.getenv("CYBERAR_DEMO_PASSWORD", "admin")

# Video de referencia mostrado en la cabina de "control manual": un archivo
# compartido públicamente desde DF Drive, proxeado por el backend (en vez de
# fetch directo del navegador) porque el share sirve octet-stream/attachment
# y el navegador necesita Content-Type video/* + soporte de Range para
# reproducirlo — y para evitar CORS/CSP cuando esta app no comparte origen
# con davefrassoni.com (desarrollo local).
CYBERAR_MANUAL_FEED_URL = os.getenv(
    "CYBERAR_MANUAL_FEED_URL", "https://davefrassoni.com/drive/s/Bz05g6mSo_zJqeky0zeJzg"
).rstrip("/")

CYBERAR_CAN_THRESHOLD = int(os.getenv("CYBERAR_CAN_THRESHOLD", "80"))
if not 40 <= CYBERAR_CAN_THRESHOLD <= 99:
    raise ImproperlyConfigured("CYBERAR_CAN_THRESHOLD debe estar entre 40 y 99")
CYBERAR_AI_ENABLED = os.getenv("CYBERAR_AI_ENABLED", "false").lower() == "true"
DF_AI_URL = os.getenv("DF_AI_URL", "http://127.0.0.1:8050").rstrip("/")
DF_AI_TOKEN = os.getenv("DF_AI_TOKEN", "")
DF_AI_CALLBACK_TOKEN = os.getenv("DF_AI_CALLBACK_TOKEN", "")
DF_AI_HOST = os.getenv("DF_AI_HOST", "davefrassoni.com")
CYBERAR_AI_TIMEOUT = min(30, max(1, int(os.getenv("CYBERAR_AI_TIMEOUT", "5"))))
