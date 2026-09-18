from django.urls import path
from authentication.views import session, login, logout
from .views import state, command, debrief_state
from vehicles.ai import callback
from mission.debrief import callback as debrief_callback

urlpatterns = [path("ai/callback/", callback), path("debrief/callback/", debrief_callback), path("session/", session),
               path("login/", login), path("logout/", logout), path("state/", state), path("control/", command),
               path("debrief/", debrief_state)]
