import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.core.asgi import get_asgi_application
http_application = get_asgi_application()
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from channels.sessions import SessionMiddlewareStack
from django.conf import settings
from django.urls import path
from api.consumers import MissionConsumer

origins = settings.CSRF_TRUSTED_ORIGINS or ["https://davefrassoni.com"]
application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": OriginValidator(SessionMiddlewareStack(URLRouter([
        path("cyberar/ws/mission/", MissionConsumer.as_asgi()),
    ])), origins),
})
