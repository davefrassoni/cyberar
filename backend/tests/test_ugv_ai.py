import json
import uuid
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.utils import timezone
from mission.models import AIFlight, Mission, MissionState, DemoScenario
from simulation.engine import SimulationEngine
from vehicles.ai import process, parse_result

RESULT = {'severity':'HIGH', 'assessment':'CAN contradice GPS e IMU.', 'suspected_source':'CAN_SPEED', 'confidence':.94, 'recommended_action':'ISOLATE_SIGNAL'}


@override_settings(CYBERAR_AI_ENABLED=True, DF_AI_TOKEN='producer-test', DF_AI_CALLBACK_TOKEN='callback-test')
class AITests(TestCase):
    def setUp(self):
        scenario = DemoScenario.objects.create()
        mission = Mission.objects.create(owner_session='session-test', scenario=scenario)
        self.live = MissionState.objects.create(mission=mission, state=SimulationEngine().advance(SimulationEngine().initial(), 92), running=True)

    def callback(self, job_id, result=RESULT, token='callback-test'):
        return self.client.post('/cyberar/api/ai/callback/', json.dumps({'job_id':job_id, 'job_type':'prompt_json', 'result':result}), content_type='application/json', HTTP_AUTHORIZATION='Bearer '+token)

    @patch('vehicles.ai.close_old_connections')
    @patch('vehicles.ai.DFAIClient.submit')
    def test_single_flight_and_callback(self, submit, close):
        submit.return_value = str(uuid.uuid4())
        process(); process()
        self.assertEqual(submit.call_count, 1)
        self.assertEqual(self.callback(submit.return_value, token='wrong').status_code, 403)
        self.assertEqual(self.callback(submit.return_value).status_code, 200)
        self.live.refresh_from_db()
        self.assertTrue(self.live.state['ugv']['untrusted'])
        revision = self.live.revision
        self.callback(submit.return_value)
        self.live.refresh_from_db()
        self.assertEqual(self.live.revision, revision)

    @patch('vehicles.ai.close_old_connections')
    @patch('vehicles.ai.DFAIClient.submit')
    def test_reset_rejects_late_result(self, submit, close):
        submit.return_value = str(uuid.uuid4()); process()
        self.live.refresh_from_db()
        self.live.generation += 1
        self.live.state = SimulationEngine().initial()
        self.live.save()
        self.assertEqual(self.callback(submit.return_value).status_code, 200)
        self.live.refresh_from_db()
        self.assertFalse(self.live.state['ugv']['untrusted'])
        self.assertEqual(self.live.state['ugv']['analysis']['status'], 'IDLE')

    @patch('vehicles.ai.close_old_connections')
    @patch('vehicles.ai.DFAIClient.submit', side_effect=TimeoutError)
    def test_timeouts_keep_same_key_and_block_new_jobs(self, submit, close):
        process(); key = AIFlight.objects.get().key
        for _ in range(5):
            AIFlight.objects.update(next_attempt=timezone.now())
            process()
        self.assertEqual(submit.call_count, 3)
        self.assertEqual(AIFlight.objects.get().key, key)
        self.assertEqual(AIFlight.objects.get().status, 'PENDING')
        self.assertTrue(all(call.args[0].key == key for call in submit.call_args_list))

    def test_schema_rejects_non_json_actions_and_nan(self):
        for result in [dict(RESULT, recommended_action='RUN_SHELL'), dict(RESULT, confidence=float('nan')), dict(RESULT, assessment=12)]:
            with self.assertRaises(ValueError): parse_result(result)
