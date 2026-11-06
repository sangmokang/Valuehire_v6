import copy
import unittest

import review
import web_archive


class WebArchiveAcceptance(unittest.TestCase):
    def setUp(self):
        self.policy = {'excluded_consultant_aliases': ['ExampleColleague']}
        self.capture = {'messages': [{'role': 'user', 'text': '전문 출력'},
                                     {'role': 'model', 'text': '채용 합의. 사적 내용. 다음 요건.'}],
            'verification': 'all_DOM_text_nodes_accounted_and_top_bottom_snapshots_identical',
            'url': 'https://gemini.google.com/app/1234abcd', 'query_count': 1, 'response_count': 1,
            'attachment_names': ['recording_261106_140350.m4a'], 'capture_verified_at': '2026-11-06'}
        self.decision = {'source_sha256': review.digest(self.capture['messages']),
            'policy_sha256': review.digest(self.policy), 'reviewer': 'Codex', 'call_kind': 'BUSINESS',
            'title': '업무 대화', 'excluded': [{'message_index': 1, 'start': 7, 'end': 13,
                'reason': 'PERSONAL', 'text_sha256': review.digest('사적 내용.')} ]}

    def test_exact_private_span_removed_without_rewriting_business(self):
        text, verdict = web_archive.stage(self.capture, self.decision, self.policy)
        self.assertIn('채용 합의.  다음 요건.', text)
        self.assertNotIn('사적 내용.', text)
        count = verdict['completeness']
        self.assertEqual(count['source_characters'], count['retained_characters'] + count['excluded_characters'])
        self.assertFalse(count['audio_reverified'])

    def test_changed_capture_and_wrong_exclusion_hash_fail(self):
        changed = copy.deepcopy(self.capture)
        changed['messages'][1]['text'] += '다른 내용'
        with self.assertRaisesRegex(ValueError, 'NOT_BOUND'):
            web_archive.stage(changed, self.decision, self.policy)
        self.decision['excluded'][0]['text_sha256'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'EXACT_SOURCE_RANGE'):
            web_archive.stage(self.capture, self.decision, self.policy)

    def test_partial_or_non_audio_conversation_is_not_published(self):
        for field, value in [('busy', True), ('response_count', 2), ('attachment_names', [])]:
            changed = {**self.capture, field: value}
            with self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
                web_archive.stage(changed, self.decision, self.policy)

    def test_overlapping_exclusions_fail_and_missed_consultant_is_not_published(self):
        self.decision['excluded'] *= 2
        with self.assertRaisesRegex(ValueError, 'OVERLAP'):
            web_archive.stage(self.capture, self.decision, self.policy)

    def test_summary_only_capture_is_not_presented_as_an_audio_transcript(self):
        self.decision['source_content_kind'] = 'SUMMARY_ONLY'
        text, verdict = web_archive.stage(self.capture, self.decision, self.policy)
        self.assertIn('발화별 통화 전문이 없습니다', text)
        self.assertEqual(verdict['source_content_kind'], 'SUMMARY_ONLY')

    def test_excluded_wrong_number_attachment_cannot_remain_in_business_header(self):
        self.capture['attachment_names'].append('wrong-number.m4a')
        self.decision['excluded_attachment_names'] = ['wrong-number.m4a']
        text, verdict = web_archive.stage(self.capture, self.decision, self.policy)
        self.assertNotIn('wrong-number.m4a', text)
        self.assertEqual(verdict['source_recording_filenames'], ['recording_261106_140350.m4a'])
        self.decision['excluded_attachment_names'] = ['unknown.m4a']
        with self.assertRaisesRegex(ValueError, 'ATTACHMENT'):
            web_archive.stage(self.capture, self.decision, self.policy)
        self.capture['messages'][1]['text'] = '고객사. ExampleColleague 논의. 다음 고객사.'
        self.decision['source_sha256'] = review.digest(self.capture['messages'])
        self.decision['excluded'] = []
        with self.assertRaisesRegex(ValueError, 'PRECISE_REVIEW'):
            web_archive.stage(self.capture, self.decision, self.policy)


if __name__ == '__main__':
    unittest.main()
