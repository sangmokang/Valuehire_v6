import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError


class PhoneAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).with_name('phone.py')
        spec = importlib.util.spec_from_file_location('phone', path)
        cls.phone = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.phone)

    def response(self, status='completed', text='네. 네.', words=None):
        if words is None:
            words = [
                {'type': 'word_info', 'text': '네.', 'speaker': 'spk:0',
                 'start_offset': '0.1s', 'end_offset': '0.4s'},
                {'type': 'word_info', 'text': '네.', 'speaker': 'spk:1',
                 'start_offset': '1s', 'end_offset': '1.4s'},
            ]
        return {'status': status, 'steps': [{'type': 'model_output', 'content': [
            {'type': 'text', 'text': text, 'annotations': words}]}]}

    def test_full_text_and_repetitions_survive(self):
        text, words = self.phone.parse_response(self.response(), 2)
        self.assertEqual(text, '네. 네.')
        self.assertEqual([w['text'] for w in words], ['네.', '네.'])
        self.assertNotEqual(words[0]['speaker'], words[1]['speaker'])

    def test_partial_or_missing_words_cannot_pass(self):
        for response in [self.response(status='in_progress'),
                         self.response(text='네. 네. 누락된 발언'),
                         self.response(words=[])]:
            with self.subTest(response=response), self.assertRaises(ValueError):
                self.phone.parse_response(response, 2)

    def test_invalid_times_fail_but_overlapping_speakers_survive(self):
        response = self.response()
        response['steps'][0]['content'][0]['annotations'][1]['end_offset'] = '100s'
        with self.assertRaises(ValueError):
            self.phone.parse_response(response, 2)
        response = self.response()
        response['steps'][0]['content'][0]['annotations'].reverse()
        response['steps'][0]['content'][0]['text'] = '네. 네.'
        self.assertEqual(len(self.phone.parse_response(response, 2)[1]), 2)

    def test_chunk_plan_covers_the_entire_recording(self):
        spans = self.phone.chunk_plan(1201.25, 600)
        self.assertEqual(spans[0][0], 0)
        self.assertEqual(spans[-1][1], 1201.25)
        self.assertTrue(all(a[1] == b[0] for a, b in zip(spans, spans[1:])))
        with self.assertRaises(ValueError):
            self.phone.chunk_plan(1, 0)

    def test_reverse_word_end_is_visible_uncertainty_not_lost_speech(self):
        response = self.response()
        response['steps'][0]['content'][0]['annotations'][1]['end_offset'] = '0.5s'
        text, words = self.phone.parse_response(response, 2)
        self.assertEqual(text, '네. 네.')
        self.assertEqual(words[1]['text'], '네.')
        self.assertIn('1s–0.5s', words[1]['timing_note'])

    def test_unicode_filename_resolves_without_shell_interpretation(self):
        import unicodedata
        with tempfile.TemporaryDirectory() as root:
            name = '통화 이름 $(untrusted)_261001_110513.m4a'
            actual = Path(root) / unicodedata.normalize('NFD', name)
            actual.write_bytes(b'audio')
            resolved = self.phone.resolve_audio(str(Path(root) / name))
            self.assertTrue(resolved.samefile(actual))
            self.assertEqual(resolved.read_bytes(), b'audio')

    def test_resume_identity_changes_with_audio_or_model(self):
        first = self.phone.cache_identity('hash1', 'model', 0, 10)
        self.assertNotEqual(first, self.phone.cache_identity('hash2', 'model', 0, 10))
        self.assertNotEqual(first, self.phone.cache_identity('hash1', 'other', 0, 10))

    def test_missing_middle_speech_is_reported(self):
        words = [{'start': 0, 'end': 1}, {'start': 20, 'end': 21}]
        self.assertTrue(self.phone.coverage_gaps([(0, 21)], words))
        self.assertFalse(self.phone.coverage_gaps([(0, 1), (20, 21)], words))

    def test_rate_limit_has_a_bounded_backoff(self):
        errors = [HTTPError('https://example.invalid', 429, 'rate limited', {}, None) for _ in range(3)]
        with patch.object(self.phone.os, 'getenv', return_value='test'), \
             patch.object(self.phone.urllib.request, 'urlopen', side_effect=errors) as request, \
             patch.object(self.phone.time, 'sleep') as sleep:
            with self.assertRaisesRegex(ValueError, 'GEMINI_HTTP_429'):
                self.phone.request_transcript(b'audio', 'model')
        self.assertEqual(request.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [30, 60])

    def test_document_requires_all_recordings_and_preserves_repetitions(self):
        record = {'number': 1, 'filename': '통화.m4a', 'duration_seconds': 2, 'sha256': 'hash',
                  'status': 'FAILED', 'chunks': [{}], 'words': [
                      {'chunk': 1, 'start': 0, 'end': 1, 'speaker': 'spk:0', 'text': '네.'},
                      {'chunk': 1, 'start': 1, 'end': 2, 'speaker': 'spk:0', 'text': '네.'}]}
        manifest = {'title': '전화 ☎️', 'model': 'model', 'files': [record]}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with self.assertRaisesRegex(ValueError, 'DOCUMENT_NOT_READY'):
                self.phone.render_document(manifest, output)
            self.assertFalse((output / 'transcript.txt').exists())
            record['status'] = 'TRANSCRIBED'
            self.phone.render_document(manifest, output)
            self.assertIn('네. 네.', (output / 'transcript.txt').read_text())
            import json
            requests = json.loads((output / 'docs-requests.json').read_text())
            self.assertEqual(requests[0]['insertText']['text'], (output / 'transcript.txt').read_text())
            self.assertEqual(manifest['document_status'], 'NOT_CREATED')


if __name__ == '__main__':
    unittest.main()
