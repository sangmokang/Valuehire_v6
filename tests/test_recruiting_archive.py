import importlib.util
import json
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('archive', Path(__file__).parents[1] / 'scripts/recruiting_archive.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'artifacts'
        self.root.mkdir()
        self.db = self.root / 'archive.db'
        with closing(sqlite3.connect(self.db)) as db, db:
            db.executescript('''CREATE TABLE archives(id TEXT PRIMARY KEY,url TEXT,site TEXT,
                page_title TEXT,captured_at TEXT,text_content TEXT,text_length INTEGER,
                screenshot_count INTEGER,doc_height INTEGER,viewport_height INTEGER,run_id TEXT);
                CREATE TABLE screenshots(archive_id TEXT,file_path TEXT,sequence INTEGER);''')
        self.posts = 0
        self.remote = {}
        self.lose_local = False
        self.lose_remote = False
        self.remote_fail = False
        self.remote_corrupt = False
        self.remote_timestamp = None
        self.remote_override = {}
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def send(self, data, code=200):
                raw = json.dumps(data).encode()
                self.send_response(code)
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if self.path.startswith('/api/archive'):
                    owner.posts += 1
                    aid = str(owner.posts)
                    with closing(sqlite3.connect(owner.db)) as db, db:
                        db.execute('INSERT INTO archives VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                            (aid, data['url'], 'jobkorea', data['pageTitle'], data['capturedAt'],
                             data['textContent'], len(data['textContent']), 0, None, None, data['run_id']))
                    if owner.lose_local:
                        self.connection.close()
                        return
                    self.send({'ok': True, 'id': aid})
                else:
                    if owner.remote_fail:
                        self.send({'error': 'rejected'}, 503)
                        return
                    owner.remote[data['local_id']] = data
                    if owner.lose_remote:
                        self.connection.close()
                        return
                    self.send(None)

            def do_GET(self):
                rows = list(owner.remote.values())
                if owner.remote_corrupt and rows:
                    rows = [{**rows[0], 'text_content': 'wrong'}]
                if owner.remote_timestamp and rows:
                    rows = [{**rows[0], 'captured_at': owner.remote_timestamp}]
                if owner.remote_override and rows:
                    rows = [{**rows[0], **owner.remote_override}]
                self.send(rows)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        base = 'http://127.0.0.1:' + str(self.server.server_port)
        self.env = patch.dict('os.environ', {'NEXT_PUBLIC_SUPABASE_URL': base,
                                              'SUPABASE_SERVICE_ROLE_KEY': 'test'}, clear=True)
        self.env.start()
        self.config = {'archiver_url': base, 'sqlite_path': str(self.db)}
        self.capture = {'url': 'https://www.jobkorea.co.kr/resume/123', 'title': 'candidate',
                        'text': '경력 원문', 'run_id': 'test-run'}
        self.ledger = self.root / 'ledger.json'

    def tearDown(self):
        self.env.stop()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def execute(self):
        return archive.run(self.config, self.capture, self.ledger)

    def test_both_stores_and_idempotent_resume(self):
        first = self.execute()
        self.assertTrue(first['supabase_verified'])
        self.assertEqual(first['sha256'], archive.digest(self.capture['text']))
        self.assertEqual(first, self.execute())
        self.assertEqual(self.posts, 1)

    def test_local_response_loss_recovers_without_duplicate(self):
        self.lose_local = True
        self.assertTrue(self.execute()['ok'])
        self.assertEqual(self.posts, 1)

    def test_remote_response_loss_verified_by_get(self):
        self.lose_remote = True
        self.assertTrue(self.execute()['ok'])
        self.assertEqual(len(self.remote), 1)

    def test_remote_failure_is_failure_then_resumable(self):
        self.remote_fail = True
        with self.assertRaises(archive.ArchiveError):
            self.execute()
        self.assertNotEqual(json.loads(self.ledger.read_text())['state'], 'verified')
        self.remote_fail = False
        self.assertTrue(self.execute()['ok'])
        self.assertEqual(self.posts, 1)

    def test_remote_wrong_body_rejected(self):
        self.remote_corrupt = True
        with self.assertRaisesRegex(archive.ArchiveError, 'Remote snapshot mismatch'):
            self.execute()

    def test_changed_local_body_rejected_on_resume(self):
        self.execute()
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE archives SET text_content='short'")
        with self.assertRaisesRegex(archive.ArchiveError, 'Local snapshot mismatch'):
            self.execute()
        self.assertEqual(self.posts, 1)

    def test_changed_local_title_rejected_before_remote_overwrite(self):
        result = self.execute()
        original_remote_title = self.remote[result['id']]['page_title']
        with closing(sqlite3.connect(self.db)) as db, db:
            db.execute("UPDATE archives SET page_title='WRONG PERSON'")
        with self.assertRaisesRegex(archive.ArchiveError, 'Local snapshot mismatch: page_title'):
            self.execute()
        self.assertEqual(self.remote[result['id']]['page_title'], original_remote_title)
        self.assertEqual(self.posts, 1)
        failed = json.loads(self.ledger.read_text())
        self.assertEqual(failed['state'], 'verification_failed')
        self.assertNotIn('result', failed)

    def test_changed_input_cannot_reuse_ledger(self):
        self.execute()
        self.capture['text'] = 'different candidate'
        with self.assertRaisesRegex(archive.ArchiveError, 'Ledger capture mismatch'):
            self.execute()

    def test_unresolved_local_write_blocks_duplicate(self):
        capture = {**self.capture, 'capturedAt': '2026-09-20T00:00:00Z'}
        archive.persist(self.ledger, {'state': 'local_request_uncertain', 'id': None,
                        'capture': capture, 'sqlite_path': str(self.db.resolve())})
        with self.assertRaisesRegex(archive.ArchiveError, 'duplicate write blocked'):
            self.execute()
        self.assertEqual(self.posts, 0)

    def test_remote_timestamp_mismatch_rejected(self):
        self.remote_timestamp = '2001-01-01T00:00:00Z'
        with self.assertRaisesRegex(archive.ArchiveError, 'mismatch: captured_at'):
            self.execute()

    def test_remote_timestamp_equivalent_timezone_accepted(self):
        self.capture['capturedAt'] = '2026-09-20T09:00:00.000+09:00'
        self.remote_timestamp = '2026-09-20T00:00:00+00:00'
        self.assertTrue(self.execute()['ok'])

    def test_existing_archive_id_reused_without_post(self):
        result = self.execute()
        self.capture = json.loads(self.ledger.read_text())['capture']
        self.capture['archive_id'] = result['id']
        self.ledger = self.root / 'second-ledger.json'
        self.assertEqual(self.execute()['id'], result['id'])
        self.assertEqual(self.posts, 1)

    def test_remote_metadata_corruption_rejected(self):
        for field, bad in [('page_title', 'WRONG'), ('text_length', -1),
                           ('screenshot_paths', ['wrong/path.png'])]:
            with self.subTest(field=field):
                self.remote_override = {field: bad}
                with self.assertRaisesRegex(archive.ArchiveError, 'mismatch: ' + field):
                    self.execute()


if __name__ == '__main__':
    unittest.main()
