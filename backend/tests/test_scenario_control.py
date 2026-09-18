import json
from django.test import TestCase, Client, override_settings
from mission.service import tick


@override_settings(CYBERAR_USER="demo", CYBERAR_PASSWORD="test-only-password", SESSION_COOKIE_SECURE=False, CSRF_COOKIE_SECURE=False)
class ScenarioControlTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        csrf = self.client.get("/cyberar/api/session/").json()["csrf"]
        self.client.post("/cyberar/api/login/", json.dumps({"username": "demo", "password": "test-only-password"}),
                          content_type="application/json", HTTP_X_CSRFTOKEN=csrf)

    def post(self, body):
        csrf = self.client.get("/cyberar/api/session/").json()["csrf"]
        return self.client.post("/cyberar/api/control/", json.dumps(body), content_type="application/json", HTTP_X_CSRFTOKEN=csrf)

    def test_select_scenario_swaps_route_and_meta(self):
        response = self.post({"action": "select_scenario", "value": "vaca-muerta"})
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertEqual(state["scenario_meta"]["key"], "vaca-muerta")
        self.assertEqual(state["scenario_meta"]["vehicle_type"], "QUADCOPTER")
        self.assertEqual(state["scenario_meta"]["ugv"]["asset"], "ROV-01")
        self.assertEqual(state["route"][1]["id"], "POZO-01")

    def test_select_scenario_rejects_unknown_key(self):
        self.assertEqual(self.post({"action": "select_scenario", "value": "moon-base"}).status_code, 400)

    def test_add_drone_grows_fleet_and_caps_at_three(self):
        response = self.post({"action": "add_drone"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["drones"]), 2)
        self.post({"action": "add_drone"})
        response = self.post({"action": "add_drone"})
        self.assertEqual(response.status_code, 400)

    def test_set_checkpoint_persists_and_reverts_on_scenario_switch(self):
        response = self.post({"action": "set_checkpoint", "value": {"index": 1, "x": 400, "y": 300}})
        self.assertEqual(response.status_code, 200)
        state = response.json()
        self.assertEqual(state["route"][1]["x"], 400)
        self.assertEqual(state["route"][1]["y"], 300)
        reset = self.post({"action": "reset", "value": None}).json()
        self.assertEqual(reset["route"][1]["x"], 400)
        switched = self.post({"action": "select_scenario", "value": "atlantic"}).json()
        self.assertNotEqual(switched["route"][1]["x"], 400)

    def test_set_checkpoint_rejects_fixed_and_out_of_range(self):
        for value in [{"index": 0, "x": 400, "y": 300}, {"index": 7, "x": 400, "y": 300},
                      {"index": 1, "x": 5000, "y": 300}, {"index": 1, "x": float("nan"), "y": 300}]:
            with self.subTest(value=value):
                self.assertEqual(self.post({"action": "set_checkpoint", "value": value}).status_code, 400)

    def test_set_checkpoint_rejected_once_running(self):
        self.post({"action": "start"})
        response = self.post({"action": "set_checkpoint", "value": {"index": 1, "x": 400, "y": 300}})
        self.assertEqual(response.status_code, 400)

    def test_set_channel_switches_and_rejects_invalid(self):
        self.assertEqual(self.post({"action": "set_channel", "value": "UNKNOWN"}).status_code, 400)
        response = self.post({"action": "set_channel", "value": "SATELLITE-FALLBACK"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["active_channel"], "SATELLITE-FALLBACK")

    def test_set_channel_rejects_unavailable(self):
        original = self.client.get("/cyberar/api/state/").json()
        jammer_id = original["jammers"][0]["id"]
        self.post({"action": "set_jammer", "value": {"id": jammer_id, "active": True}})
        state = self.client.get("/cyberar/api/state/").json()
        target = next(c for c in state["channels"] if c["id"] == "RF-PRIMARY")
        self.assertFalse(target["available"])
        self.assertEqual(self.post({"action": "set_channel", "value": "RF-PRIMARY"}).status_code, 400)

    def test_set_drone_fault_biases_altitude_and_validates(self):
        self.post({"action": "add_drone"})
        state = self.post({"action": "start"}).json()
        mission_id = state["mission_id"]
        for _ in range(10): tick(mission_id)
        baseline = self.client.get("/cyberar/api/state/").json()["drones"][1]["altitude"]
        self.assertGreater(baseline, 0)
        for value in [{"drone": 5, "level": 30}, {"drone": 0, "level": 130}, {"drone": "0", "level": 30}]:
            with self.subTest(value=value):
                self.assertEqual(self.post({"action": "set_drone_fault", "value": value}).status_code, 400)
        response = self.post({"action": "set_drone_fault", "value": {"drone": 1, "level": 80}})
        self.assertEqual(response.status_code, 200)
        self.assertLess(response.json()["drones"][1]["altitude"], baseline)
        clean = self.post({"action": "clear_drone_faults"}).json()
        self.assertEqual(clean["drones"][1]["altitude"], baseline)

    def test_set_jammer_toggles_interference_and_validates(self):
        state = self.client.get("/cyberar/api/state/").json()
        jammer_id = state["jammers"][0]["id"]
        for value in [{"id": jammer_id}, {"id": jammer_id, "active": "yes"}, {"id": "unknown", "active": True}]:
            with self.subTest(value=value):
                self.assertEqual(self.post({"action": "set_jammer", "value": value}).status_code, 400)
        activated = self.post({"action": "set_jammer", "value": {"id": jammer_id, "active": True}}).json()
        self.assertTrue(activated["jammers"][0]["active"])
        self.assertGreater(activated["interference"], 0)
        restored = self.post({"action": "restore"}).json()
        self.assertFalse(restored["jammers"][0]["active"])
        self.assertEqual(restored["interference"], 0)

    def test_set_control_mode_switches_and_rejects_invalid(self):
        self.assertEqual(self.post({"action": "set_control_mode", "value": "TELEPATHIC"}).status_code, 400)
        response = self.post({"action": "set_control_mode", "value": "MANUAL_REMOTE"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["control_mode"], "MANUAL_REMOTE")
