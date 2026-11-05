import unittest
from unittest.mock import Mock, patch

from src import qa_run
from src.api_helpers import collect_pages, matches_payload


class ApiHelperTests(unittest.TestCase):
    def test_pagination_preserves_input_and_refreshes_auth_per_page(self):
        body = {'parent': 'patients/test'}
        with patch.object(qa_run, 'access_token', side_effect=['first', 'second']), \
             patch.object(qa_run, 'rpc', side_effect=[
                 {'events': [1], 'nextPageToken': 'next'}, {'events': [2]}]) as rpc:
            self.assertEqual([1, 2], qa_run.paged('ListEvents', body, 'events'))
        self.assertEqual({'parent': 'patients/test'}, body)
        self.assertEqual(['first', 'second'], [call.args[2] for call in rpc.call_args_list])

    def test_empty_page_with_cursor_does_not_end_collection(self):
        request = Mock(side_effect=[{'nextPageToken': 'next'}, {'events': [1]}])
        self.assertEqual([1], collect_pages(request, 'ListEvents', {}, 'events'))

    def test_page_failure_propagates_without_retry(self):
        request = Mock(side_effect=RuntimeError('transport failed'))
        with self.assertRaisesRegex(RuntimeError, 'transport failed'):
            collect_pages(request, 'ListEvents', {}, 'events')
        self.assertEqual(1, request.call_count)

    def test_nested_fields_and_additional_server_fields(self):
        expected = {'firmware_version': {'image_sha256': 'hash', 'major': 3}}
        self.assertTrue(matches_payload(expected, {
            'firmwareVersion': {'imageSha256': 'hash', 'major': 3, 'minor': 1},
            'name': 'sessions/test'}))
        self.assertFalse(matches_payload(expected, {'firmwareVersion': {'major': 3}}))


if __name__ == '__main__':
    unittest.main()
