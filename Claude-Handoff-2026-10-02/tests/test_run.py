import json
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from src import qa_run


class RunTests(unittest.TestCase):
    def test_server_assigned_session_updates_dependants(self):
        state = {'patient': 'patients/p', 'session': 'patients/p/sessions/requested', 'actions': [
            {'body': {'parent': 'patients/p/sessions/requested'}},
            {'body': {'alarm': {'session': 'patients/p/sessions/requested'}}}]}
        qa_run.bind_session(state, {'name': 'patients/p/sessions/actual'})
        self.assertEqual(state['session'], 'patients/p/sessions/actual')
        self.assertEqual(state['actions'][0]['body']['parent'], state['session'])
        self.assertEqual(state['actions'][1]['body']['alarm']['session'], state['session'])
        with self.assertRaises(RuntimeError):
            qa_run.bind_session(state, {'name': 'patients/other/sessions/no'})

    def test_refuses_account_switch(self):
        path = Mock()
        path.read_text.return_value = json.dumps({'email': 'qa@example.com', 'user': 'users/one', 'patient': 'patients/one'})
        with patch.object(qa_run, 'RUN', path), patch.object(qa_run, 'identity', return_value={
            'name': 'users/two', 'selfPatient': 'patients/two'}):
            with self.assertRaises(RuntimeError):
                qa_run.load_bound()

    def test_pagination_follows_all_pages_and_rejects_repeated_cursor(self):
        with patch.object(qa_run, 'access_token', return_value='test'), patch.object(qa_run, 'rpc', side_effect=[
            {'events': [1], 'nextPageToken': 'next'}, {'events': [2]}]) as call:
            self.assertEqual(qa_run.paged('ListEvents', {}, 'events'), [1, 2])
            self.assertEqual(call.call_args.args[1]['page_token'], 'next')
        with patch.object(qa_run, 'access_token', return_value='test'), patch.object(qa_run, 'rpc', return_value={
            'events': [], 'nextPageToken': 'same'}):
            with self.assertRaises(RuntimeError):
                qa_run.paged('ListEvents', {}, 'events')

    def test_rejected_batch_is_not_checkpointed(self):
        state = {'actions': [{'key': 'session', 'status': 'done'}], 'data': {'readings': [
            {'index': 1}]}, 'session': 'patients/p/sessions/s', 'batches': []}
        with patch.object(qa_run, 'load_bound', return_value=state), patch.object(qa_run, 'access_token', return_value='test'), \
             patch.object(qa_run, 'rpc', return_value={'failedReadings': {'0': {'code': 3}}}), \
             patch.object(qa_run, 'save') as save:
            with self.assertRaises(RuntimeError):
                qa_run.write_readings(smoke=True)
            self.assertEqual(state['batches'], [])
            save.assert_not_called()

    def test_readback_compares_fields_not_just_counts(self):
        self.assertTrue(qa_run.matches_payload({'event_time': 'time', 'insulin': {'units': 2}},
                                               {'eventTime': 'time', 'insulin': {'units': 2.0}, 'name': 'events/1'}))
        self.assertFalse(qa_run.matches_payload({'insulin': {'units': 2}}, {'insulin': {'units': 20}}))
        self.assertFalse(qa_run.matches_payload({'index': 1}, None))


if __name__ == '__main__':
    unittest.main()
