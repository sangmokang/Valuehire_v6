#!/usr/bin/env python3
"""Archive one observed resume, then verify the same snapshot in both stores."""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


class ArchiveError(Exception):
    pass


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def instant(value):
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            raise ValueError('timezone required')
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError):
        raise ArchiveError('Timestamp must be timezone-aware ISO 8601') from None


def persist(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as out:
        json.dump(value, out, ensure_ascii=False, indent=2)
        out.flush()
        os.fsync(out.fileno())
    os.replace(tmp, path)


def request(url, method='GET', data=None, headers=None):
    req = urllib.request.Request(url, method=method, headers=headers or {},
                                 data=None if data is None else json.dumps(data).encode())
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        # Never expose remote error bodies, which may contain resumes or credentials.
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
        raise ArchiveError('HTTP operation failed: ' + type(exc).__name__) from None


def credentials(config):
    env = {}
    for filename in config.get('env_files', []):
        for line in Path(filename).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.removeprefix('export ').split('=', 1)
            value = value.strip()
            if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            env.setdefault(key.strip(), value)
    env.update(os.environ)
    url = env.get('NEXT_PUBLIC_SUPABASE_URL') or env.get('SUPABASE_URL')
    key = env.get('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        raise ArchiveError('Supabase configuration missing')
    return url.rstrip('/'), {'apikey': key, 'Authorization': 'Bearer ' + key}


def connection(config):
    path = Path(config['sqlite_path']).resolve()
    if not path.is_file():
        raise ArchiveError('SQLite database missing')
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def local_snapshot(config, capture, archive_id=None):
    with closing(connection(config)) as db:
        if archive_id:
            rows = db.execute('SELECT * FROM archives WHERE id=?', (archive_id,)).fetchall()
        else:
            rows = db.execute('SELECT * FROM archives WHERE url=? AND run_id=? AND captured_at=?',
                              (capture['url'], capture['run_id'], capture['capturedAt'])).fetchall()
        if len(rows) > 1:
            raise ArchiveError('Ambiguous local snapshot; multiple matching rows')
        if not rows:
            return None
        row = dict(rows[0])
        for field, expected in [('url', capture['url']), ('text_content', capture['text']),
                                ('page_title', capture.get('title', '')),
                                ('run_id', capture['run_id']), ('captured_at', capture['capturedAt'])]:
            if row.get(field) != expected:
                raise ArchiveError('Local snapshot mismatch: ' + field)
        row['screenshot_paths'] = [r[0] for r in db.execute(
            'SELECT file_path FROM screenshots WHERE archive_id=? ORDER BY sequence', (row['id'],))]
        return row


def run(config, capture, ledger_path):
    for field in ('url', 'text', 'run_id'):
        if not isinstance(capture.get(field), str) or not capture[field].strip():
            raise ArchiveError('Capture requires nonempty ' + field)
    ledger_path = Path(ledger_path)
    if 'artifacts' not in ledger_path.resolve().parts:
        raise ArchiveError('Resume ledger must be stored under an artifacts directory')
    # This lock is released by the OS even after interruption.
    import fcntl
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(ledger_path) + '.lock', 'a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ArchiveError('Ledger already in use') from None
        return _run_locked(config, dict(capture), ledger_path)


def _run_locked(config, capture, ledger_path):
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
        saved = ledger['capture']
        for field in ('url', 'text', 'run_id', 'title', 'archive_id'):
            if capture.get(field, '') != saved.get(field, ''):
                raise ArchiveError('Ledger capture mismatch: ' + field)
        if capture.get('capturedAt') and capture['capturedAt'] != saved['capturedAt']:
            raise ArchiveError('Ledger timestamp mismatch')
        capture = saved
        if ledger.get('sqlite_path') != str(Path(config['sqlite_path']).resolve()):
            raise ArchiveError('Ledger SQLite target mismatch')
    else:
        if capture.get('archive_id') and not capture.get('capturedAt'):
            raise ArchiveError('Existing archive reuse requires original capturedAt')
        capture.setdefault('capturedAt', datetime.now(timezone.utc).isoformat())
        instant(capture['capturedAt'])
        ledger = {'capture': capture, 'state': 'intent', 'id': capture.get('archive_id'),
                  'sqlite_path': str(Path(config['sqlite_path']).resolve())}
        persist(ledger_path, ledger)
    try:
        row = local_snapshot(config, capture, ledger.get('id'))
        if row is None:
            if ledger.get('id') or ledger['state'] == 'local_request_uncertain':
                raise ArchiveError('Local write outcome unresolved; automatic duplicate write blocked')
            ledger['state'] = 'local_request_uncertain'
            persist(ledger_path, ledger)
            try:
                reply = request(config['archiver_url'].rstrip('/') + '/api/archive', 'POST', {
                    'url': capture['url'], 'pageTitle': capture.get('title', ''),
                    'textContent': capture['text'], 'capturedAt': capture['capturedAt'],
                    'run_id': capture['run_id'], 'force': True, 'screenshots': []})
                if not isinstance(reply, dict) or not reply.get('id') or not reply.get('ok'):
                    raise ArchiveError('Archive response lacks successful snapshot ID')
                ledger['id'] = reply['id']
                persist(ledger_path, ledger)
            except ArchiveError:
                row = local_snapshot(config, capture)
                if row is None:
                    raise
            if row is None:
                row = local_snapshot(config, capture, ledger['id'])
            if row is None:
                raise ArchiveError('Archive response not present in SQLite')
        ledger.update(id=row['id'], state='local_verified')
        persist(ledger_path, ledger)
        base, headers = credentials(config)
        if ledger.get('supabase_target') not in (None, base):
            raise ArchiveError('Ledger Supabase target mismatch')
        ledger['supabase_target'] = base
        payload = {k: row.get(k) for k in ('url', 'site', 'page_title', 'captured_at',
                   'text_content', 'text_length', 'screenshot_count', 'doc_height', 'viewport_height', 'run_id')}
        payload.update(local_id=row['id'], ocr_text=row.get('ocr_text'), screenshot_paths=row['screenshot_paths'])
        ledger['state'] = 'remote_write_pending'
        persist(ledger_path, ledger)
        endpoint = base + '/rest/v1/profile_archives'
        try:
            request(endpoint + '?on_conflict=local_id', 'POST', payload,
                    {**headers, 'Prefer': 'resolution=merge-duplicates,return=minimal'})
        except ArchiveError:
            # Lost response may still mean a committed upsert; read it back.
            pass
        query = urllib.parse.urlencode({'local_id': 'eq.' + row['id'],
                    'select': 'local_id,url,text_content,run_id,captured_at,page_title,text_length,screenshot_paths'})
        remote = request(endpoint + '?' + query, headers=headers)
        if not isinstance(remote, list) or len(remote) != 1:
            raise ArchiveError('Remote readback requires exactly one row')
        for field in ('local_id', 'url', 'text_content', 'run_id', 'page_title', 'text_length', 'screenshot_paths'):
            if remote[0].get(field) != payload[field]:
                raise ArchiveError('Remote snapshot mismatch: ' + field)
        if instant(remote[0].get('captured_at')) != instant(payload['captured_at']):
            raise ArchiveError('Remote snapshot mismatch: captured_at')
        # Detect concurrent local changes during the remote operation.
        if local_snapshot(config, capture, row['id']) is None:
            raise ArchiveError('Local snapshot disappeared during verification')
        result = {'ok': True, 'id': row['id'], 'sha256': digest(capture['text']),
                  'sqlite_verified': True, 'supabase_verified': True}
        ledger.update(state='verified', result=result)
        ledger.pop('error', None)
        persist(ledger_path, ledger)
        return result
    except Exception as exc:
        ledger.pop('result', None)
        if ledger['state'] == 'verified':
            ledger['state'] = 'verification_failed'
        ledger['error'] = str(exc) if isinstance(exc, ArchiveError) else type(exc).__name__
        persist(ledger_path, ledger)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('config', 'capture', 'ledger'):
        parser.add_argument('--' + flag, required=True)
    args = parser.parse_args()
    try:
        result = run(json.loads(Path(args.config).read_text()),
                     json.loads(Path(args.capture).read_text()), args.ledger)
        print(json.dumps(result))
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary redacts secrets and exits nonzero
        print(json.dumps({'ok': False, 'error': str(exc) if isinstance(exc, ArchiveError)
                          else type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
