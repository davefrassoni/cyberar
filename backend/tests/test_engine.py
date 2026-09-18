from unittest import TestCase
from simulation.engine import SimulationEngine, Phase
from simulation.scenario import ROUTE


class EngineTests(TestCase):
    def setUp(self): self.engine = SimulationEngine()

    def test_complete_scenario_is_repeatable_and_returns_to_base(self):
        first = self.engine.advance(self.engine.initial(), 150)
        second = self.engine.advance(self.engine.initial(), 150)
        self.assertEqual(first, second)
        self.assertEqual(first["phase"], Phase.MISSION_COMPLETE)
        self.assertEqual(first["drones"][0]["altitude"], 0)
        self.assertEqual(first["drones"][0]["x"], ROUTE[0]["x"])
        self.assertEqual(first["drones"][0]["y"], ROUTE[0]["y"])
        self.assertEqual(first["checkpoint_index"], 7)
        self.assertEqual(first["interference"], 0)

    def test_step_size_does_not_skip_events(self):
        state = self.engine.initial()
        for _ in range(150): state = self.engine.advance(state)
        self.assertEqual(state, self.engine.advance(self.engine.initial(), 150))

    def test_original_is_not_mutated(self):
        original = self.engine.initial()
        self.engine.advance(original, 90)
        self.assertEqual(original, self.engine.initial())

    def test_invalid_transition_rejected(self):
        with self.assertRaises(ValueError): self.engine.transition(self.engine.initial(), Phase.RECON)

    def test_degradation_and_restoration(self):
        initial = self.engine.initial()
        jammer_id = initial["jammers"][0]["id"]
        degraded = self.engine.set_jammer(initial, jammer_id, True)
        self.assertLess(degraded["channels"][0]["snr"], 5)
        self.assertGreater(degraded["channels"][0]["packet_loss"], 50)
        recovered = self.engine.restore_jammers(degraded)
        self.assertEqual(initial["channels"], recovered["channels"])

    def test_duration_scaling(self):
        result = self.engine.advance(self.engine.initial(30), 30)
        self.assertEqual(result["phase"], Phase.MISSION_COMPLETE)
        self.assertEqual(result["checkpoint_index"], 7)

    def test_jammer_interference_persists_while_active(self):
        state = self.engine.initial()
        jammer_id = state["jammers"][0]["id"]
        state = self.engine.set_jammer(state, jammer_id, True)
        self.assertGreater(state["interference"], 0)
        advanced = self.engine.advance(state, 5)
        self.assertGreater(advanced["interference"], 0)
        self.assertTrue(advanced["jammers"][0]["active"])

    def test_invalid_interference(self):
        for value in [-1, 101, True, None, "20", float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.engine.set_interference(self.engine.initial(), value)

    def test_add_drone_rejects_when_fleet_full_or_mission_complete(self):
        state = self.engine.initial()
        state = self.engine.add_drone(state)
        state = self.engine.add_drone(state)
        self.assertEqual(len(state["drones"]), 3)
        with self.assertRaises(ValueError):
            self.engine.add_drone(state)
        complete = self.engine.advance(self.engine.initial(), 150)
        with self.assertRaises(ValueError):
            self.engine.add_drone(complete)

    def test_added_drone_launches_from_base_at_the_current_time(self):
        state = self.engine.advance(self.engine.initial(), 20)
        state = self.engine.add_drone(state)
        self.assertEqual(len(state["drones"]), 2)
        lead, second = state["drones"]
        self.assertGreater(lead["altitude"], 0)
        self.assertEqual(second["altitude"], 0)
        self.assertEqual(second["x"], state["route"][0]["x"])
        self.assertEqual(second["y"], state["route"][0]["y"])

    def test_trailing_drone_gates_mission_completion(self):
        state = self.engine.advance(self.engine.initial(), 140)
        state = self.engine.add_drone(state)
        state = self.engine.advance(state, 10)
        self.assertEqual(state["elapsed"], 150)
        self.assertNotEqual(state["phase"], Phase.MISSION_COMPLETE)
        state = self.engine.advance(state, 140)
        self.assertEqual(state["phase"], Phase.MISSION_COMPLETE)

    def test_retelemeter_does_not_advance_clock(self):
        state = self.engine.advance(self.engine.initial(), 40)
        state["drone_faults"] = {"0": 50}
        refreshed = self.engine.retelemeter(state)
        self.assertEqual(refreshed["elapsed"], state["elapsed"])
        self.assertEqual(refreshed["phase"], state["phase"])
        self.assertLess(refreshed["drones"][0]["altitude"], state["drones"][0]["altitude"])

    def test_all_scenario_presets_have_valid_routes(self):
        from simulation.scenario import SCENARIOS
        for key, entry in SCENARIOS.items():
            with self.subTest(scenario=key):
                route = entry["route"]
                self.assertGreaterEqual(len(route), 3)
                at_values = [cp["at"] for cp in route]
                self.assertEqual(at_values, sorted(at_values))
                self.assertEqual(at_values[0], 0)
                for cp in route:
                    self.assertTrue(0 <= cp["x"] <= 1100)
                    self.assertTrue(0 <= cp["y"] <= 650)
                ugv_route = entry["ugv"]["route"]
                self.assertGreaterEqual(len(ugv_route), 3)
                self.assertEqual(len(entry["jammers"]), 2)
                for jammer in entry["jammers"]:
                    self.assertTrue(0 <= jammer["cx"] <= 1100)
                    self.assertTrue(0 <= jammer["cy"] <= 650)
