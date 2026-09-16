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
        self.assertEqual(first["telemetry"]["altitude"], 0)
        self.assertEqual(first["telemetry"]["x"], ROUTE[0]["x"])
        self.assertEqual(first["telemetry"]["y"], ROUTE[0]["y"])
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
