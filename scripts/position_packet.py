"""Validate candidate-facing position text offline; never publishes or sends."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

CONTRACT = Path(__file__).resolve().parents[1] / 'contracts/saramin-position-registration.json'
SELECTION_KEYS = ['category', 'experience_min', 'experience_max', 'salary_min', 'salary_max']
URL_RE = re.compile(r'(?i)\b(?:https?://|www\.)\S+')
EMAIL_RE = re.compile(r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b')


def normalize(text):
    return ' '.join(re.sub('[\u200b\u200c\u200d\ufeff]', '', text).split())


def lengths(text):
    return {'code_points': len(text), 'utf16_units': len(text.encode('utf-16-le')) // 2}


def string_list(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def candidate_text_policy():
    try:
        contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        contract = {}
    policy = contract.get('candidate_text_policy', {})
    return {
        'allow_urls': policy.get('allow_urls') is True,
        'allow_emails': policy.get('allow_emails') is True,
    }


def selection_errors(value, label):
    if not isinstance(value, dict):
        return [f'{label} selections required']
    errors = []
    for key in SELECTION_KEYS:
        if not isinstance(value.get(key), str):
            errors.append(f'{label} selection {key} must be a string')
    if type(value.get('ai')) is not bool:
        errors.append(f'{label} selection ai must be a boolean')
    return errors


def schema_errors(packet):
    if not isinstance(packet, dict):
        return ['packet must be an object']
    errors = []
    for key in ['title', 'source_text', 'source_sha256']:
        if not isinstance(packet.get(key), str) or not packet[key].strip():
            errors.append(f'{key} must be a nonempty string')
    for key in ['fields', 'source_lines', 'allowed_additions', 'forbidden_literals']:
        if not string_list(packet.get(key)):
            errors.append(f'{key} must be a string array')
    if string_list(packet.get('fields')) and (len(packet['fields']) != 2 or
                                               any(not normalize(x) for x in packet['fields'])):
        errors.append('exactly two nonempty fields required')
    for key in ['limit', 'title_limit']:
        if type(packet.get(key)) is not int or packet[key] < 1:
            errors.append(f'{key} must be a positive integer')
    errors.extend(selection_errors(packet.get('selections'), 'packet'))
    if packet.get('forbidden_literals') == []:
        errors.append('forbidden_literals cannot be empty')
    excluded = packet.get('excluded_lines')
    if not isinstance(excluded, list) or any(
        not isinstance(item, dict) or any(not isinstance(item.get(key), str) or
                                         not normalize(item[key]) for key in ['text', 'reason'])
        for item in excluded
    ):
        errors.append('excluded_lines require nonempty text and reason')
    return errors


def content_errors(packet):
    errors = []
    source = [normalize(line) for line in packet['source_text'].splitlines() if normalize(line)]
    ledger = [normalize(line) for line in packet['source_lines'] if normalize(line)]
    if source != ledger:
        errors.append('source_lines differ from source_text')
    digest = hashlib.sha256(packet['source_text'].encode('utf-8')).hexdigest()
    if digest != packet['source_sha256']:
        errors.append('source_sha256 mismatch')
    excluded = Counter(normalize(item['text']) for item in packet['excluded_lines'])
    available = Counter(source)
    if any(count > available[line] for line, count in excluded.items()):
        errors.append('exclusion missing from source or repeated too often')
    retained = []
    for line in source:
        if excluded[line]:
            excluded[line] -= 1
        else:
            retained.append(line)
    output = normalize('\n'.join(packet['fields']))
    cursor = 0
    gaps = []
    for line in retained:
        location = output.find(line, cursor)
        if location < 0:
            errors.append(f'source line absent or out of order: {line}')
        else:
            gaps.append(output[cursor:location])
            cursor = location + len(line)
    additions = [normalize(line) for item in packet['allowed_additions']
                 for line in item.splitlines() if normalize(line)]
    gaps.append(output[cursor:])
    addition_output = normalize(' '.join(gaps))
    if addition_output != normalize(' '.join(additions)):
        errors.append('approved additions missing, reordered, repeated, or changed')
    if '밸류커넥트' not in output:
        errors.append('ValueConnect application wording missing')
    policy = candidate_text_policy()
    candidate_text = normalize(packet['title'] + '\n' + output)
    if not policy['allow_urls'] and URL_RE.search(candidate_text):
        errors.append('candidate text contains URL')
    if not policy['allow_emails'] and EMAIL_RE.search(candidate_text):
        errors.append('candidate text contains email')
    for literal in packet['forbidden_literals']:
        if not normalize(literal):
            errors.append('forbidden literals cannot be empty')
        elif normalize(literal) in candidate_text:
            errors.append(f'forbidden application literal present: {literal}')
    return errors


def validate(packet):
    errors = schema_errors(packet)
    if errors:
        return {'status': 'FAIL', 'errors': errors}
    try:
        counts = [lengths(field) for field in packet['fields']]
        title_counts = lengths(packet['title'])
        for index, count in enumerate(counts):
            if max(count.values()) > min(2000, packet['limit']):
                errors.append(f'field {index + 1} exceeds limit')
        if max(title_counts.values()) > min(35, packet['title_limit']):
            errors.append('title exceeds limit')
        errors.extend(content_errors(packet))
    except UnicodeEncodeError:
        return {'status': 'FAIL', 'errors': ['invalid Unicode surrogate']}
    return {'status': 'FAIL' if errors else 'PASS', 'errors': errors,
            'field_lengths': counts, 'title_lengths': title_counts}


def line_endings(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')


def readback(packet, observed):
    result = validate(packet)
    if not isinstance(packet, dict):
        return result
    if not isinstance(observed, dict) or not isinstance(observed.get('title'), str) or \
            not string_list(observed.get('fields')) or len(observed['fields']) != 2:
        result['errors'].append('observed title and two fields required')
    else:
        for key in ['title', 'fields']:
            expected = packet.get(key)
            actual = observed[key]
            if key == 'fields' and string_list(expected):
                expected = [line_endings(item) for item in expected]
                actual = [line_endings(item) for item in actual]
            elif isinstance(expected, str):
                expected, actual = line_endings(expected), line_endings(actual)
            if expected != actual:
                result['errors'].append(f'readback {key} mismatch')
        observed_lengths = [lengths(field) for field in observed['fields']]
        for index, count in enumerate(observed_lengths):
            if max(count.values()) > min(2000, packet.get('limit', 0)):
                result['errors'].append(f'observed field {index + 1} exceeds limit')
    selection_result = selection_errors(observed.get('selections') if isinstance(observed, dict) else None,
                                       'observed')
    result['errors'].extend(selection_result)
    if not selection_result and isinstance(packet.get('selections'), dict) and \
            observed.get('selections') != packet['selections']:
        result['errors'].append('readback selections mismatch')
    result['status'] = 'FAIL' if result['errors'] else 'PASS'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['validate', 'readback'])
    parser.add_argument('--packet', required=True, type=Path)
    parser.add_argument('--observed', type=Path)
    args = parser.parse_args()
    try:
        packet = json.loads(args.packet.read_text(encoding='utf-8'))
        if args.action == 'readback':
            if args.observed is None:
                parser.error('--observed is required for readback')
            observed = json.loads(args.observed.read_text(encoding='utf-8'))
            result = readback(packet, observed)
        else:
            result = validate(packet)
    except (OSError, ValueError) as error:
        result = {'status': 'FAIL', 'errors': [str(error)]}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
