from io import StringIO
from unittest import skipUnless
from unittest.mock import patch
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TransactionTestCase


@skipUnless(connection.vendor == "postgresql", "Liderazgo de producción requiere PostgreSQL")
class RunnerLeadershipTests(TransactionTestCase):
    def open_connection(self):
        leader = connection.get_new_connection(connection.get_connection_params())
        leader.autocommit = True
        self.addCleanup(leader.close)
        return leader

    def test_second_runner_cannot_acquire_leadership(self):
        leader = self.open_connection()
        self.assertTrue(leader.execute("SELECT pg_try_advisory_lock(2026091601)").fetchone()[0])
        with self.assertRaisesMessage(CommandError, "Ya existe un reloj"):
            call_command("run_simulator", stdout=StringIO())

    def test_clock_releases_leadership_when_it_stops(self):
        with patch("simulation.management.commands.run_simulator.time.sleep", side_effect=RuntimeError("test stop")):
            with self.assertRaisesMessage(RuntimeError, "test stop"):
                call_command("run_simulator", stdout=StringIO())
        replacement = self.open_connection()
        self.assertTrue(replacement.execute("SELECT pg_try_advisory_lock(2026091601)").fetchone()[0])
