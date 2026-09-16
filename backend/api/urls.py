from django.urls import path
from authentication.views import session, login, logout
from .views import state, command

urlpatterns = [path("session/", session), path("login/", login), path("logout/", logout), path("state/", state), path("control/", command)]
