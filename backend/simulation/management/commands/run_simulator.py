import fcntl
import os
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import close_old_connections
from mission.models import MissionState
from mission.service import tick


class Command(BaseCommand):
    help = "Único reloj de simulación; no depende de las conexiones del navegador."

    def handle(self, *args, **options):
        # The application is deployed on one host. flock also excludes manual
        # duplicate runners, including when no PostgreSQL is used in development.
        default_lock = "/tmp/cyberar-runner.lock" if settings.DEBUG else "/run/cyberar/simulator.lock"
        with open(os.getenv("CYBERAR_RUNNER_LOCK", default_lock), "w") as lock:
            try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: raise CommandError("Ya existe un reloj de simulación activo")
            self.stdout.write("Reloj CYBER.AR activo")
            while True:
                started = time.monotonic()
                close_old_connections()
                for mission_id in MissionState.objects.filter(running=True).values_list("mission_id", flat=True):
                    tick(mission_id)
                time.sleep(max(0, 1 - (time.monotonic() - started)))
