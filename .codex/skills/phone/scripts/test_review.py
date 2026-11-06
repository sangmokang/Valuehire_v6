import copy
import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import review


def record(texts):
    return {'status': 'TRANSCRIBED', 'number': 1, 'sha256': 'a' * 64, 'filename': 'source.m4a',
            'path': '/authorized/source.m4a', 'duration_seconds': 30,
            'chunks': [{'raw_text': 'private source', 'start': 0, 'end': 30}], 'words': [
                {'text': text, 'start': i * 2, 'end': i * 2 + 1, 'speaker': 'spk:' + str(i % 2), 'chunk': 1}
                for i, text in enumerate(texts)]}


def result(labels, kind='BUSINESS'):
    return {'call_kind': kind, 'spans': [
        {'start': i + 1, 'end': i + 1, 'label': value} for i, value in enumerate(labels)]}


class ReviewAcceptance(unittest.TestCase):
    def setUp(self):
        self.policy = {'excluded_consultant_aliases': ['ExampleColleague'], 'scope_root': '/authorized',
                       'delete_suspected_nonbusiness_to_trash': True, 'supabase_domain': 'business_call_transcripts'}

    def test_omitted_or_duplicated_turns_fail_closed(self):
        for value in [result(['BUSINESS']), {'call_kind': 'BUSINESS', 'spans': [
                {'start': 1, 'end': 2, 'label': 'BUSINESS'}, {'start': 2, 'end': 2, 'label': 'BUSINESS'}]}]:
            with self.assertRaises(ValueError):
                review.validate_review(value, 2)

    def test_discussion_is_removed_including_indirect_continuation(self):
        source = record(['고객사 채용 요건', 'ExampleColleague 평가', '그 사람 이야기는 이어서', '다음 고객사 요건'])
        labels = ['BUSINESS', 'CONSULTANT', 'CONSULTANT', 'BUSINESS']
        value = review.filter_record(source, self.policy, [result(labels), result(labels)])
        self.assertEqual([w['text'] for w in value['record']['words']], ['고객사 채용 요건', '다음 고객사 요건'])
        self.assertEqual(value['kept_word_indices'], [0, 3])
        self.assertEqual(len(value['excluded']), 2)
        self.assertNotEqual(value['record']['words'][0]['speaker'], value['record']['words'][1]['speaker'])
        self.assertNotIn('raw_text', value['record']['chunks'][0])
        self.assertEqual(source['chunks'][0]['raw_text'], 'private source')

    def test_literal_guard_blocks_a_missed_name(self):
        source = record(['채용 기준', 'ExampleColleague 근황'])
        value = review.filter_record(source, self.policy, [result(['BUSINESS'] * 2), result(['BUSINESS'] * 2)])
        self.assertEqual([w['text'] for w in value['record']['words']], ['채용 기준'])

    def test_uncertain_and_disagreeing_content_is_not_published(self):
        source = record(['고객사 채용 요건', '사적 대화'])
        value = review.filter_record(source, self.policy, [
            result(['BUSINESS', 'BUSINESS']), result(['BUSINESS', 'UNCERTAIN'])])
        self.assertEqual(value['kept_word_indices'], [0])

    def test_nonbusiness_ledger_accounts_for_every_original_word(self):
        source = record(['안녕하세요', '가족 행사'])
        value = review.filter_record(source, self.policy, [
            result(['NEUTRAL', 'PERSONAL'], 'PERSONAL'), result(['NEUTRAL', 'PERSONAL'], 'PERSONAL')])
        self.assertEqual(value['status'], 'SUSPECTED_NONBUSINESS')
        self.assertEqual(sorted(i for span in value['excluded'] for i in span['word_indices']), [0, 1])

    def test_failed_source_and_repeated_model_cannot_pass(self):
        source = record(['업무'])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'DIFFERENT'):
                review.review_record(source, self.policy, Path(directory), ['same', 'same'])
            source['status'] = 'FAILED'
            with self.assertRaisesRegex(ValueError, 'NOT_COMPLETE'):
                review.review_record(source, self.policy, Path(directory), ['a', 'b'])

    def test_supabase_requires_actual_docs_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            (out / 'review-verdict.json').write_text(json.dumps({'status': 'BUSINESS_REVIEWED'}))
            (out / 'document-receipt.json').write_text(json.dumps({'status': 'CREATED'}))
            with patch.object(review.urllib.request, 'urlopen') as network:
                with self.assertRaisesRegex(ValueError, 'READBACK'):
                    review.sync_ontology(out, self.policy, '/unused')
                network.assert_not_called()

    def test_trash_cannot_delete_outside_the_authorized_folder(self):
        value = {'status': 'SUSPECTED_NONBUSINESS', 'source_path': '/other/file.m4a'}
        with tempfile.TemporaryDirectory() as directory, patch.object(review.subprocess, 'run') as trash:
            with self.assertRaisesRegex(ValueError, 'OUTSIDE'):
                review.trash_nonbusiness(value, self.policy, Path(directory))
            trash.assert_not_called()

    def test_alias_matching_does_not_match_inside_other_english_words(self):
        self.assertEqual(review.alias_hits('sleeve', ['Lee']), [])
        self.assertEqual(review.alias_hits('LEE 관련 내용', ['Lee']), ['Lee'])

    def test_korean_alias_inside_unrelated_word_is_not_a_person(self):
        self.assertEqual(review.alias_hits('국민수당 안내', ['민수']), [])
        self.assertEqual(review.alias_hits('민수님의 내용', ['민수']), ['민수'])

    def test_same_name_external_person_exception_is_source_and_quote_bound(self):
        policy = copy.deepcopy(self.policy)
        policy['nonconsultant_identity_exceptions'] = [{'source_sha256': 'source-one', 'alias': 'ExampleColleague',
            'exact_context_quotes': ['ExampleColleague 외부 회사 의장']}]
        phrase = 'ExampleColleague 외부 회사 의장'
        self.assertEqual(review.alias_hits(phrase, ['ExampleColleague'], policy, 'source-one'), [])
        self.assertEqual(review.alias_hits(phrase, ['ExampleColleague'], policy, 'other-source'), ['ExampleColleague'])
        self.assertEqual(review.alias_hits(phrase + ' ExampleColleague 정산', ['ExampleColleague'], policy, 'source-one'), ['ExampleColleague'])

    def test_direct_review_requires_exact_source_and_policy_hashes(self):
        source = record(['업무 내용'])
        envelope = {'reviewer': 'Codex', 'source_sha256': source['sha256'],
                    'source_words_sha256': 'wrong', 'policy_sha256': review.digest(self.policy),
                    'review': result(['BUSINESS'])}
        with tempfile.TemporaryDirectory() as directory, patch.object(review, 'model_review') as model:
            with self.assertRaisesRegex(ValueError, 'NOT_BOUND'):
                review.review_record(source, self.policy, Path(directory), [], envelope)
            model.assert_not_called()

    def test_each_source_has_a_stable_distinct_unique_domain(self):
        first = review.ontology_identity('a' * 64, 'business_call_transcripts')
        self.assertEqual(first, review.ontology_identity('a' * 64, 'business_call_transcripts'))
        other = review.ontology_identity('b' * 64, 'business_call_transcripts')
        self.assertNotEqual(first[0], other[0])
        self.assertNotEqual(first[1], other[1])
        with self.assertRaises(ValueError):
            review.ontology_identity('not-a-source-hash', 'business_call_transcripts')

    def test_anonymous_access_must_be_denied_before_private_upload(self):
        with patch.object(review.urllib.request, 'urlopen'):
            with self.assertRaisesRegex(ValueError, 'ANONYMOUSLY_READABLE'):
                review.assert_anonymous_denied('https://example.invalid/object', {})

    def test_public_ontology_index_cannot_contain_body_or_docs_links(self):
        safe = {'schema_version': 1, 'status': 'PRIVATE_BUSINESS_EVIDENCE_VERIFIED',
                'storage_bucket': 'phone-business-evidence', 'storage_path': 'a' * 64 + '.json',
                'evidence_sha256': 'b' * 64, 'redaction_policy_sha256': 'c' * 64}
        review.assert_safe_pointer(safe)
        for field in ['body_text', 'google_docs_url', 'candidate_name']:
            unsafe = {**safe, field: 'private value'}
            with self.assertRaisesRegex(ValueError, 'UNAPPROVED'):
                review.assert_safe_pointer(unsafe)
        unsafe = {**safe, 'storage_path': '../other-private-object'}
        with self.assertRaisesRegex(ValueError, 'OPAQUE'):
            review.assert_safe_pointer(unsafe)

    def test_recording_time_comes_from_source_filename_without_inventing_timezone(self):
        self.assertEqual(review.source_local_time('/recordings/example_241206_172538.m4a'), '2024-12-06T17:25:38')
        self.assertIsNone(review.source_local_time('/recordings/no-date.m4a'))
        self.assertIsNone(review.source_local_time('/recordings/example_241332_999999.m4a'))
        self.assertEqual(review.source_local_time('/recordings/example_261106_140350 (1).m4a'), '2026-11-06T14:03:50')

    def test_multi_recording_web_source_does_not_invent_one_recording_time(self):
        value = review.web_recording_metadata({'source_recording_filenames': [
            'example_261106_140350 (1).m4a', 'example_261107_090000.m4a']})
        self.assertIsNone(value['recorded_local_time'])
        self.assertEqual(value['recording_time_source'], 'multiple_source_filenames')
        self.assertEqual([r['recorded_local_time'] for r in value['recordings']],
                         ['2026-11-06T14:03:50', '2026-11-07T09:00:00'])

    def test_private_object_keys_change_with_content_but_not_json_key_order(self):
        first = review.private_evidence_path('a' * 64, {'text': 'original', 'date': None})
        self.assertEqual(first, review.private_evidence_path('a' * 64, {'date': None, 'text': 'original'}))
        self.assertNotEqual(first, review.private_evidence_path('a' * 64, {'text': 'revised', 'date': None}))
        self.assertTrue(first.startswith('a' * 64 + '/'))

    def test_only_excluded_words_are_removed_when_one_turn_has_two_topics(self):
        source = record(['고객사', '채용', 'ExampleColleague', '정산', '그분', '사생활', '다음', '포지션'])
        for word in source['words']:
            word['speaker'] = 'spk:0'
        self.assertEqual(len(review.turns(source)), 1)
        decision = result(['BUSINESS', 'BUSINESS', 'CONSULTANT', 'CONSULTANT',
                           'CONSULTANT', 'CONSULTANT', 'BUSINESS', 'BUSINESS'], 'MIXED')
        decision['unit'] = 'WORD'
        value = review.filter_record(source, self.policy, [decision, decision])
        self.assertEqual(value['kept_word_indices'], [0, 1, 6, 7])
        self.assertEqual([w['text'] for w in value['record']['words']], ['고객사', '채용', '다음', '포지션'])

    def test_missed_consultant_topic_requires_review_instead_of_dropping_whole_turn(self):
        source = record(['채용', 'ExampleColleague', '다음업무'])
        for word in source['words']:
            word['speaker'] = 'spk:0'
        decision = result(['BUSINESS'] * 3)
        decision['unit'] = 'WORD'
        with self.assertRaisesRegex(ValueError, 'PRECISE_REVIEW'):
            review.filter_record(source, self.policy, [decision, decision])

    def test_review_input_preserves_annotations_that_contain_spaces(self):
        source = record(['두 단어', '다음 발언'])
        for word in source['words']:
            word['speaker'] = 'spk:0'
        decision = result(['BUSINESS', 'BUSINESS'])
        decision['unit'] = 'WORD'
        response = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': json.dumps(decision)}]}}]}
        with patch.object(review.os, 'getenv', return_value='test'), patch.object(
                review.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(response).encode())) as network:
            review.model_review(review.turns(source), self.policy, 'test-model')
        sent = json.loads(network.call_args.args[0].data)['contents'][0]['parts'][0]['text']
        dialogue = json.loads(sent.split('\nDIALOGUE:\n')[1])
        self.assertEqual(dialogue[0]['words'], [{'id': 1, 'text': '두 단어'}, {'id': 2, 'text': '다음 발언'}])
        with patch.object(review.urllib.request, 'urlopen', side_effect=HTTPError(
                'https://example.invalid', 403, 'denied', {}, None)):
            review.assert_anonymous_denied('https://example.invalid/object', {})
        with patch.object(review.urllib.request, 'urlopen', side_effect=HTTPError(
                'https://example.invalid', 500, 'unavailable', {}, None)):
            with self.assertRaisesRegex(ValueError, 'INCONCLUSIVE'):
                review.assert_anonymous_denied('https://example.invalid/object', {})


if __name__ == '__main__':
    unittest.main()
