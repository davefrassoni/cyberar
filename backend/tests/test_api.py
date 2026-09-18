import json
from datetime import timedelta
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from django.contrib.sessions.models import Session
from mission.models import Mission, MissionState, MissionEvent, TelemetrySnapshot
from mission.service import tick, engine


@override_settings(CYBERAR_USER="demo", CYBERAR_PASSWORD="test-only-password", SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class APITests(TestCase):
    def setUp(self): self.client = Client(enforce_csrf_checks=True)

    def post(self, path, body, client=None):
        client = client or self.client
        csrf = client.get("/cyberar/api/session/").json()["csrf"]
        return client.post(f"/cyberar/api/{path}/", json.dumps(body), content_type="application/json", HTTP_X_CSRFTOKEN=csrf)

    def login(self, client=None):
        response = self.post("login", {"username":"demo", "password":"test-only-password"}, client)
        self.assertEqual(response.status_code, 200)

    def test_permissions_and_csrf(self):
        self.assertEqual(self.client.get("/cyberar/api/state/").status_code, 401)
        self.assertEqual(self.post("control", {"action":"start"}).status_code, 401)
        self.assertEqual(self.client.post("/cyberar/api/login/", {}).status_code, 403)
        self.assertEqual(Mission.objects.count(), 0)
        self.login()
        self.assertEqual(self.client.post("/cyberar/api/control/", json.dumps({"action":"start"}), content_type="application/json").status_code, 403)

    def test_login_rate_limit(self):
        for _ in range(8): self.assertEqual(self.post("login", {"username":"bad", "password":"bad"}).status_code, 401)
        self.assertEqual(self.post("login", {"username":"demo", "password":"test-only-password"}).status_code, 429)

    def test_mission_isolation(self):
        self.login()
        first = self.client.get("/cyberar/api/state/").json()
        other = Client(enforce_csrf_checks=True)
        self.login(other)
        second = other.get("/cyberar/api/state/").json()
        self.assertNotEqual(first["mission_id"], second["mission_id"])
        self.post("control", {"action":"interference", "value":77})
        self.assertEqual(other.get("/cyberar/api/state/").json()["interference"], 0)

    def test_clock_pause_reset_and_snapshot_frequency(self):
        self.login()
        original = self.client.get("/cyberar/api/state/").json()
        mission_id = original["mission_id"]
        self.post("control", {"action":"automatic_demo"})
        self.post("control", {"action":"speed", "value":4})
        for _ in range(20): tick(mission_id)
        advanced = self.client.get("/cyberar/api/state/").json()
        self.assertEqual(advanced["elapsed"], 80)
        self.assertGreater(MissionEvent.objects.count(), 5)
        self.assertLess(TelemetrySnapshot.objects.count(), 20)
        self.post("control", {"action":"pause"})
        tick(mission_id)
        self.assertEqual(self.client.get("/cyberar/api/state/").json()["elapsed"], 80)
        reset = self.post("control", {"action":"reset"}).json()
        for key in ["revision"]: original.pop(key); reset.pop(key)
        self.assertEqual(original, reset)
        self.assertEqual(MissionEvent.objects.count(), 1)
        self.assertEqual(TelemetrySnapshot.objects.count(), 1)

    def test_logout_and_expiry_stop_clock(self):
        self.login()
        state = self.post("control", {"action":"start"}).json()
        self.post("logout", {})
        self.assertFalse(MissionState.objects.get(mission_id=state["mission_id"]).running)
        self.assertEqual(self.client.get("/cyberar/api/state/").status_code, 401)
        self.login()
        state = self.post("control", {"action":"start"}).json()
        Session.objects.update(expire_date=timezone.now()-timedelta(seconds=1))
        tick(state["mission_id"])
        self.assertFalse(MissionState.objects.get(mission_id=state["mission_id"]).running)
        self.assertEqual(self.client.get("/cyberar/api/state/").status_code, 401)

    def test_unknown_actions_invalid_json_and_speed(self):
        self.login()
        for payload in [[], {"action":"shell"}, {"action":"speed", "value":True}, {"action":"speed", "value":99}, {"action":"interference", "value":-20}, {"action":"automatic", "value":"false"}]:
            self.assertEqual(self.post("control", payload).status_code, 400)
        self.assertEqual(self.client.get("/cyberar/api/control/").status_code, 405)

    def test_cookie_path(self):
        self.login()
        cookie = self.client.cookies["cyberar_session"]
        self.assertEqual(cookie["path"], "/cyberar/")
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Strict")

    def test_legacy_pre_fleet_state_self_heals_on_next_load(self):
        self.login()
        original = self.client.get("/cyberar/api/state/").json()
        live = MissionState.objects.get(mission_id=original["mission_id"])
        legacy_state = dict(live.state)
        del legacy_state["drones"]
        del legacy_state["drones_launch"]
        legacy_state["telemetry"] = {"altitude": 0, "x": 195, "y": 230}
        live.state = legacy_state
        live.save()
        response = self.client.get("/cyberar/api/state/")
        self.assertEqual(response.status_code, 200)
        healed = response.json()
        self.assertIsInstance(healed["drones"], list)
        self.assertGreaterEqual(len(healed["drones"]), 1)
        self.assertIsInstance(healed["route"], list)

    def test_can_controls_are_session_scoped_and_independent_from_rf(self):
        self.login()
        self.post("control", {"action": "interference", "value": 55})
        started = self.post("control", {"action": "can_start"}).json()
        self.assertEqual(started["ugv"]["level"], 15)
        increased = self.post("control", {"action": "can_increase"}).json()
        self.assertEqual(increased["ugv"]["level"], 45)
        restored = self.post("control", {"action": "can_restore"}).json()
        self.assertEqual(restored["ugv"]["level"], 0)
        self.assertEqual(restored["interference"], 55)
