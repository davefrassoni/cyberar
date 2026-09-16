import fcntl
import os
import time
from contextlib import ExitStack
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections, connection
from mission.models import MissionState
from mission.service import tick


class Command(BaseCommand):
    help = "Único reloj de simulación; no depende de las conexiones del navegador."

    def handle(self, *args, **options):
        with ExitStack() as resources:
            leader = None
            if connection.vendor == "postgresql":
                # Dedicated connection: ORM connection recycling must not release
                # leadership. PostgreSQL also excludes runners on other hosts.
                leader = connection.get_new_connection(connection.get_connection_params())
                leader.autocommit = True
                resources.callback(leader.close)
                acquired = leader.execute("SELECT pg_try_advisory_lock(2026091601)").fetchone()[0]
                if not acquired:
                    raise CommandError("Ya existe un reloj de simulación activo")
            else:
                lock = resources.enter_context(open(os.getenv("CYBERAR_RUNNER_LOCK", "/tmp/cyberar-runner.lock"), "w"))
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise CommandError("Ya existe un reloj de simulación activo")
            self.stdout.write("Reloj CYBER.AR activo")
            while True:
                started = time.monotonic()
                if leader is not None:
                    # Fail closed if the leadership connection has been lost.
                    leader.execute("SELECT 1")
                close_old_connections()
                for mission_id in MissionState.objects.filter(running=True).values_list("mission_id", flat=True):
                    tick(mission_id)
                time.sleep(max(0, 1 - (time.monotonic() - started)))
