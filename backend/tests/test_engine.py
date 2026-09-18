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
        degraded = self.engine.advance(initial, 80)
        self.assertLess(degraded["channels"][0]["snr"], 5)
        self.assertGreater(degraded["channels"][0]["packet_loss"], 50)
        recovered = self.engine.advance(degraded, 25)
        self.assertEqual(initial["channels"], recovered["channels"])

    def test_duration_scaling(self):
        result = self.engine.advance(self.engine.initial(30), 30)
        self.assertEqual(result["phase"], Phase.MISSION_COMPLETE)
        self.assertEqual(result["checkpoint_index"], 7)

    def test_manual_control_is_not_overwritten(self):
        state = self.engine.initial()
        state["automatic"] = False
        self.engine.set_interference(state, 55)
        self.assertEqual(self.engine.advance(state, 120)["interference"], 55)

    def test_invalid_interference(self):
        for value in [-1, 101, True, None, "20", float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.engine.set_interference(self.engine.initial(), value)

    def test_invalid_fleet_size_rejected(self):
        for value in [0, 4, "3", True, None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.engine.initial(fleet_size=value)

    def test_fleet_drones_are_staggered_and_trailing_drone_gates_completion(self):
        state = self.engine.initial(fleet_size=3)
        self.assertEqual(len(state["drones"]), 3)
        state = self.engine.advance(state, 9)
        lead, second, third = state["drones"]
        self.assertGreater(lead["altitude"], second["altitude"])
        self.assertGreater(second["altitude"], third["altitude"])
        # Lead drone has finished its route by elapsed=150, but the trailing drone's offset isn't done yet.
        state = self.engine.advance(state, 141)
        self.assertEqual(state["elapsed"], 150)
        self.assertNotEqual(state["phase"], Phase.MISSION_COMPLETE)
        state = self.engine.advance(state, 16)
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
