import json
import uuid
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from mission.models import DemoScenario, Mission, MissionState
from simulation.engine import SimulationEngine
from vehicles.ai import process


@override_settings(CYBERAR_USER="demo", CYBERAR_PASSWORD="test-only-password",
                    CYBERAR_DEMO_ENABLED=True, CYBERAR_DEMO_USER="admin", CYBERAR_DEMO_PASSWORD="admin",
                    SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class DemoLoginTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def post(self, path, body):
        csrf = self.client.get("/cyberar/api/session/").json()["csrf"]
        return self.client.post(f"/cyberar/api/{path}/", json.dumps(body), content_type="application/json", HTTP_X_CSRFTOKEN=csrf)

    def test_real_credentials_do_not_disable_ai(self):
        self.post("login", {"username": "demo", "password": "test-only-password"})
        self.post("control", {"action": "start"})
        mission = Mission.objects.get()
        self.assertFalse(mission.ai_disabled)

    def test_demo_credentials_login_but_disable_ai(self):
        response = self.post("login", {"username": "admin", "password": "admin"})
        self.assertEqual(response.status_code, 200)
        self.post("control", {"action": "start"})
        mission = Mission.objects.get()
        self.assertTrue(mission.ai_disabled)

    def test_demo_credentials_rejected_when_disabled(self):
        with override_settings(CYBERAR_DEMO_ENABLED=False):
            self.assertEqual(self.post("login", {"username": "admin", "password": "admin"}).status_code, 401)

    def test_wrong_credentials_still_rejected(self):
        self.assertEqual(self.post("login", {"username": "admin", "password": "wrong"}).status_code, 401)


@override_settings(CYBERAR_AI_ENABLED=True, DF_AI_TOKEN="producer-test", DF_AI_CALLBACK_TOKEN="callback-test")
class AIDisabledMissionSkippedTests(TestCase):
    def _mission(self, ai_disabled):
        scenario = DemoScenario.objects.create()
        mission = Mission.objects.create(owner_session=f"session-{uuid.uuid4()}", scenario=scenario, ai_disabled=ai_disabled)
        return MissionState.objects.create(
            mission=mission, state=SimulationEngine().advance(SimulationEngine().initial(), 92), running=True,
        )

    @patch("vehicles.ai.close_old_connections")
    @patch("vehicles.ai.DFAIClient.submit")
    def test_ai_disabled_mission_never_reserves_the_shared_flight(self, submit, close):
        self._mission(ai_disabled=True)
        process()
        submit.assert_not_called()

    @patch("vehicles.ai.close_old_connections")
    @patch("vehicles.ai.DFAIClient.submit")
    def test_ai_enabled_mission_still_reserves_the_shared_flight(self, submit, close):
        submit.return_value = str(uuid.uuid4())
        self._mission(ai_disabled=False)
        process()
        submit.assert_called_once()
