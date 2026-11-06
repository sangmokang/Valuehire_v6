#!/usr/bin/env python3
"""Gemini verbatim call transcription; Google Docs writes belong to the agent's connector."""
import argparse
import base64
import datetime as dt
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.request

API = 'https://generativelanguage.googleapis.com/v1beta/interactions'
CONFIG = {'language_codes': ['ko-KR'], 'mode': {
    'type': 'verbatim', 'diarization_mode': 'speaker', 'timestamp_granularities': ['word']}}


def save_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)


def resolve_audio(value):
    path = Path(value).expanduser().absolute()
    if path.is_file():
        return path
    if path.parent.is_dir():
        matches = [p for p in path.parent.iterdir() if p.is_file() and
                   unicodedata.normalize('NFC', p.name) == unicodedata.normalize('NFC', path.name)]
        if len(matches) == 1:
            return matches[0]
    raise ValueError(f'INPUT_NOT_FOUND: {path}')


def run_media(args):
    result = subprocess.run(args, capture_output=True)
    if result.returncode:
        raise ValueError(f'MEDIA_ERROR: {args[0]} exit {result.returncode}')
    return result


def duration(path):
    result = run_media(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'default=nw=1:nk=1', str(path)])
    value = float(result.stdout)
    if not math.isfinite(value) or value <= 0:
        raise ValueError('INVALID_AUDIO_DURATION')
    return value


def chunk_plan(seconds, size):
    if not math.isfinite(seconds) or seconds <= 0 or not 0 < size <= 600:
        raise ValueError('INVALID_CHUNK_PLAN: use 1..600 seconds')
    return [(start, min(start + size, seconds)) for start in range(0, math.ceil(seconds), size)]


def cache_identity(audio_hash, model, start, end):
    data = [2, audio_hash, model, start, end, CONFIG]
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def seconds(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+(?:\.\d+)?s', value):
        raise ValueError('INVALID_WORD_TIMESTAMP')
    return float(value[:-1])


def parse_response(response, clip_duration):
    if response.get('status') != 'completed':
        raise ValueError('INCOMPLETE_GEMINI_RESPONSE')
    texts, words = [], []
    for step in response.get('steps', []):
        if step.get('type') != 'model_output':
            continue
        for content in step.get('content', []):
            if content.get('type') != 'text':
                continue
            text = content.get('text', '')
            annotations = [a for a in content.get('annotations', []) if a.get('type') == 'word_info']
            normalize = lambda s: re.sub(r'\s+', '', s)
            if not text.strip() or normalize(text) != normalize(''.join(a.get('text', '') for a in annotations)):
                raise ValueError('MISSING_WORD_ANNOTATIONS: full text must match annotated words')
            texts.append(text)
            for item in annotations:
                start, end = seconds(item['start_offset']), seconds(item['end_offset'])
                if not (0 <= start <= clip_duration + 1 and 0 <= end <= clip_duration + 1):
                    raise ValueError('WORD_OUTSIDE_AUDIO')
                if not item.get('text', '').strip() or not item.get('speaker'):
                    raise ValueError('MISSING_WORD_OR_SPEAKER')
                word = {'start': start, 'end': end, 'text': item['text'], 'speaker': item['speaker']}
                if end < start:
                    # Preserve the utterance and original faulty annotation; expose uncertainty in the document.
                    word['timing_note'] = f'{item["text"]} ({item["start_offset"]}–{item["end_offset"]})'
                    word['end'] = start
                words.append(word)
    if not texts or not words:
        raise ValueError('EMPTY_TRANSCRIPT: inspect silence or unintelligible audio manually')
    return '\n'.join(texts), words


def active_ranges(path, length):
    result = run_media(['ffmpeg', '-nostdin', '-hide_banner', '-i', str(path), '-af',
                        'silencedetect=noise=-35dB:d=1', '-f', 'null', '-'])
    events = re.findall(r'silence_(start|end): ([0-9.]+)', result.stderr.decode(errors='replace'))
    active, cursor = [], 0.0
    for event, value in events:
        value = min(float(value), length)
        if event == 'start' and value > cursor:
            active.append((cursor, value))
        elif event == 'end':
            cursor = value
    if events and events[-1][0] == 'start':
        cursor = length
    if cursor < length:
        active.append((cursor, length))
    return active


def coverage_gaps(active, words):
    """Flag >=6 s of sound without a nearby recognized word; this is not proof of accuracy."""
    covered = sorted((max(0, w['start'] - 2.5), w['end'] + 2.5) for w in words)
    gaps = []
    for start, end in active:
        cursor = start
        for left, right in covered:
            if right <= cursor:
                continue
            if left >= end:
                break
            if left - cursor >= 6:
                gaps.append([round(cursor, 3), round(min(left, end), 3)])
            cursor = max(cursor, right)
        if end - cursor >= 6:
            gaps.append([round(cursor, 3), round(end, 3)])
    return gaps


def request_transcript(audio, model):
    key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not key:
        raise ValueError('GEMINI_KEY_MISSING: set GEMINI_API_KEY in the execution environment')
    body = {'model': model, 'store': False, 'input': [{'type': 'audio', 'mime_type': 'audio/flac',
            'data': base64.b64encode(audio).decode()}], 'generation_config': {'transcription_config': CONFIG}}
    payload = json.dumps(body).encode()
    if len(payload) > 19_000_000:
        raise ValueError('INLINE_AUDIO_TOO_LARGE: retry with a smaller --chunk-seconds')
    for attempt in range(3):
        request = urllib.request.Request(API, data=payload,
            headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < 2:
                retry_after = error.headers.get('Retry-After', '')
                delay = min(60, max(1, int(retry_after))) if retry_after.isdigit() else 30 * (attempt + 1)
                print(f'GEMINI_RETRY http={error.code} after={delay}s', flush=True)
                time.sleep(delay)
                continue
            # Provider bodies may contain request data; never log them or the credential.
            raise ValueError(f'GEMINI_HTTP_{error.code}: transcription was not completed') from None
        except (urllib.error.URLError, TimeoutError):
            raise ValueError('GEMINI_NETWORK_ERROR: rerun the same output directory to resume') from None


def transcribe_one(record, output, model, size):
    path, length = Path(record['path']), record['duration_seconds']
    words, clips = [], []
    plan = chunk_plan(length, size)
    for index, (start, end) in enumerate(plan):
        # One second of context on both sides; retain only words whose midpoint belongs to the core.
        clip_start, clip_end = max(0, start - 1), min(length, end + 1)
        identity = cache_identity(record['sha256'], model, start, end)
        cache = output / f'{identity}.json'
        if cache.exists():
            stored = json.loads(cache.read_text())
            if stored.get('identity') != identity:
                raise ValueError('CACHE_IDENTITY_MISMATCH')
            response = stored['response']
        else:
            audio = run_media(['ffmpeg', '-nostdin', '-v', 'error', '-ss', str(clip_start),
                '-i', str(path), '-t', str(clip_end - clip_start), '-ac', '1', '-ar', '16000',
                '-f', 'flac', 'pipe:1']).stdout
            try:
                response = request_transcript(audio, model)
            except ValueError as error:
                if str(error).startswith('INLINE_AUDIO_TOO_LARGE') and size > 30:
                    print(f'SPLIT_AUDIO file={record["number"]} chunk_seconds={size // 2}', flush=True)
                    return transcribe_one(record, output, model, size // 2)
                raise
            save_json(cache, {'identity': identity, 'response': response})
        raw_text, clip_words = parse_response(response, clip_end - clip_start)
        kept = []
        for word in clip_words:
            word = dict(word)
            word['start'] = round(word['start'] + clip_start, 3)
            word['end'] = round(word['end'] + clip_start, 3)
            middle = (word['start'] + word['end']) / 2
            if start <= middle < end or (index == len(plan) - 1 and middle == end):
                word['chunk'] = index + 1
                kept.append(word)
        if not kept:
            raise ValueError('EMPTY_CORE_TRANSCRIPT: inspect the chunk boundary')
        words.extend(kept)
        clips.append({'start': start, 'end': end, 'cache': cache.name, 'raw_text': raw_text})
        print(f'CHUNK_TRANSCRIBED {record["number"]} {index + 1}/{len(plan)}', flush=True)
    gaps = coverage_gaps(active_ranges(path, length), words)
    record.update(words=words, chunks=clips, coverage_gaps=gaps,
                  uncertain_timestamps=sum(bool(w.get('timing_note')) for w in words),
                  status='REVIEW_REQUIRED' if gaps else 'TRANSCRIBED')
    return record


def timestamp(value):
    milliseconds = round(value * 1000)
    hours, rest = divmod(milliseconds, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f'{hours:02}:{minutes:02}:{secs:02}.{millis:03}'


def paragraphs(record):
    groups = []
    for word in record['words']:
        key = (word['chunk'], word['speaker'])
        if (not groups or groups[-1]['key'] != key or len(groups[-1]['texts']) >= 45
                or word['start'] - groups[-1]['end'] > 3):
            groups.append({'key': key, 'start': word['start'], 'end': word['end'], 'texts': [], 'timing_notes': []})
        group = groups[-1]
        group['end'] = max(group['end'], word['end'])
        group['texts'].append(word['text'])
        if word.get('timing_note'):
            group['timing_notes'].append(word['timing_note'])
    for group in groups:
        chunk, speaker = group['key']
        label = f'화자 {speaker}'
        if len(record['chunks']) > 1:
            label = f'구간 {chunk} · {label}'
        yield f'[{timestamp(group["start"])}–{timestamp(group["end"])}] {label}: ' + ' '.join(group['texts'])
        if group['timing_notes']:
            yield '[Gemini 원 응답의 단어 종료 시간 오류 · 해당 단어 시간 확인 필요: ' + '; '.join(group['timing_notes']) + ']'


def render_document(manifest, output):
    if any(r['status'] != 'TRANSCRIBED' for r in manifest['files']):
        raise ValueError('DOCUMENT_NOT_READY: resolve every failed or flagged recording first')
    parts = [manifest['title'], '',
        f'통화 {len(manifest["files"])}건 · 총 {timestamp(sum(r["duration_seconds"] for r in manifest["files"]))}',
        f'전사: Gemini {manifest["model"]} / verbatim (반복·추임새 유지)',
        '화자 번호는 각 파일·분할 구간에서만 유효합니다. 실명과 대응시키지 않았습니다.',
        '자동 전사본입니다. 청취가 어려운 부분과 고유명사는 원음 확인이 필요할 수 있습니다.', '']
    headings = []
    for record in manifest['files']:
        heading = f'{record["number"]:02}. {record["filename"]}'
        headings.append(heading)
        parts.extend([heading, f'길이: {timestamp(record["duration_seconds"])}',
                      f'원본 SHA-256: {record["sha256"]}', ''])
        parts.extend(paragraphs(record))
        parts.append('')
    text = '\n'.join(parts) + '\n'
    (output / 'transcript.txt').write_text(text, encoding='utf-8')
    requests = [{'insertText': {'location': {'index': 1}, 'text': text}}]
    cursor = 1
    for line in text.splitlines(keepends=True):
        size = len(line.encode('utf-16-le')) // 2
        if line.rstrip('\n') == manifest['title'] or line.rstrip('\n') in headings:
            style = 'TITLE' if cursor == 1 else 'HEADING_1'
            requests.append({'updateParagraphStyle': {'range': {'startIndex': cursor,
                'endIndex': cursor + size}, 'paragraphStyle': {'namedStyleType': style},
                'fields': 'namedStyleType'}})
        cursor += size
    save_json(output / 'docs-requests.json', requests)
    manifest.update(status='TRANSCRIBED', text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    document_status='NOT_CREATED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='*', help='Audio file paths as separate shell arguments')
    parser.add_argument('--input-json', type=Path, help='JSON array of exact audio file paths')
    parser.add_argument('--out', type=Path, required=True, help='Private output directory; reuse to resume')
    parser.add_argument('--title', default='통화 내용 전문')
    parser.add_argument('--model', default='gemini-3.5-transcribe')
    parser.add_argument('--chunk-seconds', type=int, default=600)
    parser.add_argument('--preflight', action='store_true', help='Inspect inputs without sending audio')
    args = parser.parse_args()
    os.umask(0o077)
    args.out.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = (args.out / '.lock').open('w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise ValueError('RUN_ALREADY_ACTIVE: another process owns this output directory') from None
    inputs = list(args.files)
    if args.input_json:
        supplied = json.loads(args.input_json.read_text())
        if not isinstance(supplied, list) or any(not isinstance(x, str) for x in supplied):
            raise ValueError('INPUT_JSON_MUST_BE_A_PATH_ARRAY')
        inputs.extend(supplied)
    if not inputs:
        raise ValueError('NO_AUDIO_INPUTS')
    chunk_plan(1, args.chunk_seconds)
    records = []
    for value in inputs:
        path = resolve_audio(value)
        with path.open('rb') as source:
            audio_hash = hashlib.file_digest(source, 'sha256').hexdigest()
        records.append({'number': len(records) + 1, 'path': str(path),
            'filename': unicodedata.normalize('NFC', path.name), 'duration_seconds': duration(path),
            'sha256': audio_hash, 'status': 'PENDING'})
    manifest = {'version': 1, 'title': args.title, 'model': args.model,
                'created_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'files': records,
                'status': 'PREFLIGHT', 'document_status': 'NOT_CREATED'}
    manifest_path = args.out / 'manifest.json'
    receipt_path = args.out / 'document-receipt.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if not receipt.get('document_id'):
            raise ValueError('INVALID_DOCUMENT_RECEIPT: inspect before creating any document')
        print('DOCUMENT_ALREADY_CREATED: read back the saved document before resuming publication')
        return
    # Never overwrite a document receipt or silently repurpose a previous run directory.
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text())
        identity = lambda m: [(r['path'], r['sha256']) for r in m['files']]
        if identity(old) != identity(manifest) or old['model'] != manifest['model'] or old['title'] != manifest['title']:
            raise ValueError('OUTPUT_DIRECTORY_CONFLICT: use a fresh output directory for changed inputs')
        if old.get('document_status') in ('CREATED', 'VERIFIED'):
            print('DOCUMENT_ALREADY_CREATED: use its saved receipt; do not create a duplicate')
            return
    save_json(manifest_path, manifest)
    print(f'PREFLIGHT_OK files={len(records)} seconds={sum(r["duration_seconds"] for r in records):.3f}', flush=True)
    if args.preflight:
        return
    failures = 0
    for record in records:
        try:
            transcribe_one(record, args.out, args.model, args.chunk_seconds)
            if record['status'] != 'TRANSCRIBED':
                failures += 1
        except (ValueError, KeyError, OSError) as error:
            record.update(status='FAILED', error=str(error))
            failures += 1
            print(f'FILE_FAILED {record["number"]}: {error}', file=sys.stderr, flush=True)
            if 'GEMINI_HTTP_429' in str(error):
                save_json(manifest_path, manifest)
                break
        save_json(manifest_path, manifest)
    if failures:
        manifest['status'] = 'REVIEW_REQUIRED'
        save_json(manifest_path, manifest)
        raise ValueError(f'BATCH_INCOMPLETE: {failures}/{len(records)} files need attention; no Google Doc is ready')
    render_document(manifest, args.out)
    save_json(manifest_path, manifest)
    print(f'TRANSCRIBED files={len(records)}; Google Docs publication and readback still required', flush=True)
    print(str(args.out / 'docs-requests.json'))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
