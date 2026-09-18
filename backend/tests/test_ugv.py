import copy
from unittest import TestCase
from simulation.engine import SimulationEngine
from vehicles.can import CANAnomalyDetector, CANSimulationEngine
from vehicles.ugv import control, SafetyValidator


class UGVTests(TestCase):
    def setUp(self): self.engine = SimulationEngine()

    def test_progressive_detection_and_safe_continuation(self):
        state = self.engine.initial()
        scores = []
        for t in range(1, 106):
            state = self.engine.advance(state)
            if t in (60, 75, 80, 85, 90): scores.append(state['ugv']['detector']['score'])
            if t == 70: self.assertIsNone(state['ugv']['alert_at'])
        self.assertEqual(scores, sorted(scores))
        self.assertLess(scores[1], 80)
        self.assertGreaterEqual(scores[-1], 80)
        self.assertTrue(state['ugv']['untrusted'])
        self.assertEqual(state['ugv']['speed'], 9)
        self.assertEqual(state['ugv']['analysis']['source'], 'LOCAL')
        self.assertGreater(state['ugv']['progress'], 3)
        self.assertIn('ANOMALÍA CAN', state['ugv']['milestones'])

    def test_manual_restore_does_not_change_uav(self):
        state = self.engine.advance(self.engine.initial(), 80)
        interference = state['interference']
        control(state, 'can_increase')
        state = self.engine.advance(state, 20)
        control(state, 'can_restore')
        self.assertFalse(state['ugv']['untrusted'])
        self.assertEqual(state['ugv']['analysis']['status'], 'IDLE')
        state = self.engine.advance(state, 10)
        self.assertEqual(state['ugv']['level'], 0)
        self.assertEqual(state['ugv']['detector']['score'], 12)
        # CAN controls never touch RF interference — no jammer was ever activated.
        self.assertEqual(interference, state['interference'])

    def test_detector_uses_evidence_not_scenario(self):
        detector = CANAnomalyDetector()
        normal = CANSimulationEngine().sample(1, 33, 0)
        self.assertEqual(detector.analyze(normal, 33, 32, [])['score'], 12)
        samples = copy.deepcopy(normal)
        samples[0]['value'] = 99999
        samples[1]['frequency'] = 99
        samples.append(dict(samples[0], can_id='0x999'))
        evidence = detector.analyze(samples, 33, 32, [])['evidence']
        for part in ('rango', 'frecuencia', 'inesperado'):
            self.assertTrue(any(part in e for e in evidence))
        samples[2]['value'] = 4
        evidence = detector.analyze(samples, 33, 32, [{'can':33,'gps':33,'residual':0}])['evidence']
        self.assertTrue(any('abrupto' in e for e in evidence))
        self.assertTrue(any('ambas fuentes' in e for e in evidence))

    def test_safety_validator_rejects_unsupported_and_unjustified_actions(self):
        ugv = self.engine.initial()['ugv']
        for action in ('ISOLATE_SIGNAL', 'EXECUTE_COMMAND', 'SAFE_STOP'):
            with self.assertRaises(ValueError):
                SafetyValidator.validate({'recommended_action': action, 'suspected_source': 'CAN_SPEED', 'confidence': .94}, ugv)

    def test_old_state_upgrades_on_tick(self):
        state = self.engine.initial()
        del state['ugv']
        self.assertIn('ugv', self.engine.advance(state))
