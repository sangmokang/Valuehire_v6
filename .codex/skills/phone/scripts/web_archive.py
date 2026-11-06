#!/usr/bin/env python3
"""Stage a complete Gemini UI conversation with source-bound, exact exclusions.

Capture is a separate browser UI operation. This module never fetches private
Gemini endpoints, executes source text, or invents audio word timestamps.
"""
import argparse
import json
import os
from pathlib import Path
import re

import phone
import review


def stage(capture, decision, policy):
    messages = capture['messages']
    source_sha = review.digest(messages)
    if (decision.get('source_sha256') != source_sha
            or decision.get('policy_sha256') != review.digest(policy)
            or decision.get('reviewer') != 'Codex'
            or decision.get('call_kind') != 'BUSINESS'):
        raise ValueError('WEB_REVIEW_NOT_BOUND_TO_BUSINESS_SOURCE_AND_POLICY')
    if (capture.get('verification') != 'all_DOM_text_nodes_accounted_and_top_bottom_snapshots_identical'
            or capture.get('busy') or capture.get('stop')
            or not re.fullmatch(r'https://gemini\.google\.com/app/[0-9a-f]+', capture['url'])
            or capture['query_count'] != sum(m['role'] == 'user' for m in messages)
            or capture['response_count'] != sum(m['role'] == 'model' for m in messages)
            or not capture.get('attachment_names')):
        raise ValueError('WEB_CAPTURE_INCOMPLETE_OR_AUDIO_ORIGIN_UNCONFIRMED')
    excluded = decision.get('excluded', [])
    attachments = capture['attachment_names']
    excluded_attachments = decision.get('excluded_attachment_names', [])
    if (not isinstance(excluded_attachments, list) or len(set(excluded_attachments)) != len(excluded_attachments)
            or any(name not in attachments for name in excluded_attachments)):
        raise ValueError('WEB_EXCLUDED_ATTACHMENT_NOT_IN_SOURCE')
    retained_attachments = [name for name in attachments if name not in excluded_attachments]
    if not retained_attachments:
        raise ValueError('WEB_NO_BUSINESS_AUDIO_ATTACHMENT_REMAINS')
    content_kind = decision.get('source_content_kind', 'TRANSCRIPT_PRESENT')
    if content_kind not in ['TRANSCRIPT_PRESENT', 'SUMMARY_ONLY']:
        raise ValueError('WEB_UNKNOWN_SOURCE_CONTENT_KIND')
    grouped = {i: [] for i in range(len(messages))}
    for item in excluded:
        index = item['message_index']
        if type(index) is not int or index not in grouped:
            raise ValueError('INVALID_WEB_MESSAGE_INDEX')
        text = messages[index]['text']
        start, end = item['start'], item['end']
        if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
                or item['reason'] not in ['PERSONAL', 'CONSULTANT', 'MODEL_EXECUTION_ARTIFACT', 'NONBUSINESS_CALL']
                or review.digest(text[start:end]) != item['text_sha256']):
            raise ValueError('WEB_EXCLUSION_NOT_BOUND_TO_EXACT_SOURCE_RANGE')
        grouped[index].append(item)
    source_note = ('Gemini에 저장된 통화 요약과 후속 업무 대화를 보존한 검수본입니다. '
                   '이 대화에는 발화별 통화 전문이 없습니다. ' if content_kind == 'SUMMARY_ONLY'
                   else 'Gemini에 저장된 통화 전문과 후속 업무 대화를 보존한 검수본입니다. ')
    header = (decision['title'] + '\n\n출처: ' + capture['url'] + '\n'
              '첨부 녹음: ' + ', '.join(retained_attachments) + '\n' + source_note +
              '원음과의 재대조는 수행하지 않았습니다. Gemini의 요약·분석은 당시 생성된 답변으로 보존합니다.\n'
              '사용자가 제외하도록 지정한 사담·타 컨설턴트 논의 및 모델 실행 흔적은 구간별로 제외했습니다.\n\n')
    parts = [header]
    source_chars = retained_chars = 0
    for index, message in enumerate(messages):
        original = message['text']
        source_chars += len(original)
        cursor = 0
        kept = []
        for item in sorted(grouped[index], key=lambda s: s['start']):
            if item['start'] < cursor:
                raise ValueError('WEB_EXCLUSION_OVERLAP')
            kept.append(original[cursor:item['start']])
            cursor = item['end']
        kept.append(original[cursor:])
        content = ''.join(kept)
        retained_chars += len(content)
        role = '사용자' if message['role'] == 'user' else 'Gemini'
        parts.append(f'대화 {index + 1} · {role}\n{content}\n\n')
    text = ''.join(parts)
    if review.alias_hits(text, policy['excluded_consultant_aliases'], policy, source_sha):
        raise ValueError('WEB_FORBIDDEN_PERSON_REQUIRES_PRECISE_REVIEW')
    if any(name in text for name in excluded_attachments):
        raise ValueError('WEB_EXCLUDED_ATTACHMENT_STILL_IN_BUSINESS_TEXT')
    omitted = sum(s['end'] - s['start'] for s in excluded)
    if source_chars != retained_chars + omitted:
        raise ValueError('WEB_SOURCE_CHARACTER_ACCOUNTING_FAILED')
    verdict = {'status': 'BUSINESS_REVIEWED', 'source_kind': 'gemini_web_conversation',
        'source_sha256': source_sha, 'source_path': capture['url'], 'source_url': capture['url'],
        'source_recording_filename': retained_attachments[0],
        'policy_sha256': review.digest(policy), 'excluded': excluded,
        'review_strategy': 'codex_full_conversation_review_with_exact_character_accounting',
        'capture_verification': {'method': capture['verification'], 'messages': len(messages),
                                 'captured_at': capture['capture_verified_at']},
        'completeness': {'unit': 'unicode_codepoint', 'source_characters': source_chars,
                         'retained_characters': retained_chars, 'excluded_characters': omitted,
                         'all_source_turns_accounted': True, 'audio_reverified': False},
        'text_sha256': review.digest(text)}
    # Preserve old staged verdicts byte for byte; new decisions opt into richer provenance.
    if 'source_content_kind' in decision or 'excluded_attachment_names' in decision:
        verdict.update(source_content_kind=content_kind, source_recording_filenames=retained_attachments)
    return text, verdict


def verify_staged(out, policy):
    capture = json.loads((out / 'capture.json').read_text())
    decision = json.loads((out / 'business-review.json').read_text())
    text, verdict = stage(capture, decision, policy)
    if (text != (out / 'transcript.txt').read_text()
            or verdict != json.loads((out / 'review-verdict.json').read_text())):
        raise ValueError('WEB_STAGED_CONTENT_CHANGED_SINCE_REVIEW')
    return verdict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--policy', type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    out = args.out
    text, verdict = stage(json.loads((out / 'capture.json').read_text()),
                          json.loads((out / 'business-review.json').read_text()),
                          json.loads(args.policy.read_text()))
    if (out / 'document-receipt.json').exists():
        receipt = json.loads((out / 'document-receipt.json').read_text())
        if receipt.get('text_sha256') != review.digest(text):
            raise ValueError('EXISTING_DOCUMENT_REQUIRES_EXPLICIT_REVISION')
    (out / 'transcript.txt').write_text(text)
    phone.save_json(out / 'review-verdict.json', verdict)
    phone.save_json(out / 'docs-requests.json', [{'insertText': {'location': {'index': 1}, 'text': text}}])
    print('BUSINESS_REVIEWED', verdict['completeness'])


if __name__ == '__main__':
    main()
