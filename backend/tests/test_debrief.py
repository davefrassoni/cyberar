import json
import uuid
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from mission.models import DebriefFlight
from mission.service import tick
from mission import debrief

RESULT = {"overall_assessment": "UAV-02 muestra una desviación sostenida en altitud.",
          "suspect_drone": "UAV-02", "suspect_component": "ALTITUDE_SENSOR", "confidence": 0.9, "findings": ["UAV-02: altitud fuera de rango"]}


@override_settings(CYBERAR_USER="demo", CYBERAR_PASSWORD="test-only-password", SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class DebriefTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        csrf = self.client.get("/cyberar/api/session/").json()["csrf"]
        self.client.post("/cyberar/api/login/", json.dumps({"username": "demo", "password": "test-only-password"}),
                          content_type="application/json", HTTP_X_CSRFTOKEN=csrf)

    def post(self, body):
        csrf = self.client.get("/cyberar/api/session/").json()["csrf"]
        return self.client.post("/cyberar/api/control/", json.dumps(body), content_type="application/json", HTTP_X_CSRFTOKEN=csrf)

    def complete_mission_with_fleet(self, fleet_size=3):
        self.post({"action": "set_fleet_size", "value": fleet_size})
        self.post({"action": "speed", "value": 4})
        state = self.post({"action": "start"}).json()
        mission_id = state["mission_id"]
        for _ in range(60): tick(mission_id)
        return mission_id

    def test_request_debrief_rejected_before_mission_complete(self):
        self.post({"action": "set_fleet_size", "value": 2})
        self.post({"action": "start"})
        self.assertEqual(self.post({"action": "request_debrief"}).status_code, 400)

    def test_local_insight_names_the_faulty_drone(self):
        self.post({"action": "set_fleet_size", "value": 3})
        state = self.post({"action": "start"}).json()
        mission_id = state["mission_id"]
        for _ in range(5): tick(mission_id)
        self.post({"action": "set_drone_fault", "value": {"drone": 1, "level": 90}})
        for _ in range(200): tick(mission_id)
        response = self.post({"action": "request_debrief"})
        self.assertEqual(response.status_code, 200)
        debrief_state = self.client.get("/cyberar/api/debrief/").json()
        self.assertEqual(debrief_state["source"], "LOCAL")
        self.assertEqual(debrief_state["result"]["suspect_drone"], "UAV-02")
        self.assertEqual(debrief_state["result"]["suspect_component"], "ALTITUDE_SENSOR")
        self.assertGreater(len(debrief_state["series"]), 0)

    @override_settings(CYBERAR_AI_ENABLED=True, DF_AI_TOKEN="producer-test", DF_AI_CALLBACK_TOKEN="callback-test")
    @patch("mission.debrief.close_old_connections")
    @patch("mission.debrief.DebriefAIClient.submit")
    def test_df_ai_callback_upgrades_source(self, submit, close):
        submit.return_value = str(uuid.uuid4())
        mission_id = self.complete_mission_with_fleet()
        self.post({"action": "request_debrief"})
        debrief.process()
        self.assertEqual(submit.call_count, 1)
        job_id = DebriefFlight.objects.get().job_id
        response = self.client.post("/cyberar/api/debrief/callback/", json.dumps({"job_id": job_id, "job_type": "prompt_json", "result": RESULT}),
                                     content_type="application/json", HTTP_AUTHORIZATION="Bearer callback-test")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["accepted"])
        state = self.client.get("/cyberar/api/debrief/").json()
        self.assertEqual(state["source"], "DF AI")
        self.assertEqual(state["result"]["suspect_drone"], "UAV-02")

    @override_settings(CYBERAR_AI_ENABLED=True, DF_AI_TOKEN="producer-test", DF_AI_CALLBACK_TOKEN="callback-test")
    @patch("mission.debrief.close_old_connections")
    @patch("mission.debrief.DebriefAIClient.submit")
    def test_stale_generation_callback_is_ignored(self, submit, close):
        submit.return_value = str(uuid.uuid4())
        mission_id = self.complete_mission_with_fleet()
        self.post({"action": "request_debrief"})
        debrief.process()
        job_id = DebriefFlight.objects.get().job_id
        self.post({"action": "reset"})
        response = self.client.post("/cyberar/api/debrief/callback/", json.dumps({"job_id": job_id, "job_type": "prompt_json", "result": RESULT}),
                                     content_type="application/json", HTTP_AUTHORIZATION="Bearer callback-test")
        self.assertEqual(response.status_code, 200)
        flight = DebriefFlight.objects.get()
        self.assertEqual(flight.status, "DONE")
        self.assertEqual(flight.source, "LOCAL")

    def test_debrief_endpoint_tolerates_legacy_snapshot_rows(self):
        from mission.models import TelemetrySnapshot, Mission
        mission_id = self.complete_mission_with_fleet(fleet_size=1)
        mission = Mission.objects.get(pk=mission_id)
        TelemetrySnapshot.objects.create(mission=mission, elapsed=9999, data={"legacy": "single-vehicle shape"})
        response = self.client.get("/cyberar/api/debrief/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn({"legacy": "single-vehicle shape"}, [p.get("drones") for p in response.json()["series"]])
