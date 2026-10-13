"""Exercise the Aside output boundary without operating a live browser."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'recruiting_browser', Path(__file__).parents[1] / 'scripts/recruiting_browser.py'
)
browser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(browser)


class AsideBoundaryTest(unittest.TestCase):
    def invoke(self, stdout, stderr='', returncode=0):
        with patch.object(browser.subprocess, 'run', return_value=CompletedProcess(
            args=[], returncode=returncode, stdout=stdout, stderr=stderr
        )):
            return browser.aside('unused')

    def test_console_error_with_zero_exit_is_failure(self):
        for stdout, stderr in [('CAPTURE:{}\n[error | failed', ''),
                               ('CAPTURE:{}', '[error | failed')]:
            with self.subTest(stdout=stdout, stderr=stderr), self.assertRaises(RuntimeError):
                self.invoke(stdout, stderr)

    def test_missing_duplicate_or_failed_capture_is_failure(self):
        for stdout, code in [('no capture', 0), ('CAPTURE:{}\nCAPTURE:{}', 0),
                             ('CAPTURE:{}', 1)]:
            with self.subTest(stdout=stdout, code=code), self.assertRaises(RuntimeError):
                self.invoke(stdout, returncode=code)

    def test_invalid_json_is_failure(self):
        with self.assertRaises(ValueError):
            self.invoke('CAPTURE:{broken')

    def test_only_marker_payload_is_returned(self):
        self.assertEqual(self.invoke('log\nCAPTURE:{"text":"profile"}\nlog'),
                         {'text': 'profile'})


class BrowserCliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.contract = self.root / "contract.json"
        self.contract.write_text(json.dumps({
            "jobkorea": {
                "origin": "https://www.jobkorea.co.kr",
                "search_path": "/Search/Resume",
                "reset": "#reset",
                "keyword": "#keyword",
                "submit": "#submit",
                "conditions": "#conditions",
                "rows": ".row",
                "profile_link": "a",
                "loading_text": "loading"
            }
        }))
        self.snapshot = self.root / "snapshot.json"
        self.write_snapshot()

    def tearDown(self):
        self.tmp.cleanup()

    def write_snapshot(self, **overrides):
        payload = {
            "schema_version": "company-intelligence-v1",
            "status": "ready",
            "snapshot_hash": "hash",
            "jd": {"source_url": "https://example.com/jd"},
            "search_hypothesis": {"hard_requirements": ["qa"], "priority": ["mobile testing"]},
            "channel_search_plan": {"jobkorea": ["QA Engineer mobile testing"]},
        }
        payload.update(overrides)
        if payload.get("snapshot_hash") == "hash":
            body = {key: value for key, value in payload.items() if key != "snapshot_hash"}
            payload["snapshot_hash"] = browser.hash_payload(body)
        self.snapshot.write_text(json.dumps(payload, ensure_ascii=False))
        return payload

    def fake_aside(self, seen):
        def _fake(code):
            seen.append(code)
            return {
                "url": "https://www.jobkorea.co.kr/Search/Resume",
                "title": "검색",
                "text": "검색 결과",
                "conditions": ["통합검색 : QA Engineer mobile testing"],
                "rows": [{"id": "1", "url": "https://www.jobkorea.co.kr/User/Profile/1", "text": "row"}],
            }
        return _fake

    def run_cli(self, *args):
        return browser.main([
            *args,
            "--contract", str(self.contract),
            "--output", str(self.root / "out.json"),
        ])

    def test_company_snapshot_query_index_records_trace(self):
        seen = []
        with patch.object(browser, "aside", self.fake_aside(seen)):
            rc = self.run_cli("search", "--url", "https://www.jobkorea.co.kr/Search/Resume",
                              "--company-snapshot", str(self.snapshot), "--query-index", "0")
        self.assertEqual(rc, 0)
        out = json.loads((self.root / "out.json").read_text())
        self.assertEqual(out["requested_keyword"], "QA Engineer mobile testing")
        self.assertEqual(out["company_snapshot"]["source_jd"], "https://example.com/jd")
        self.assertIn("snapshot_hash", out["company_snapshot"])
        self.assertIn("openTab", seen[0])
        self.assertIn("Wrong search tab", seen[0])
        self.assertIn("waitSearchControls", seen[0])
        self.assertIn("Reset missing with active conditions", seen[0])
        self.assertEqual(out["effective_result_validation"]["condition_readback"], "exact")
        self.assertTrue(out["effective_result_validation"]["keyword_tag_only"])
        self.assertFalse(out["effective_result_validation"]["quality_success"])

    def test_reset_wait_allows_clean_state_only_when_keyword_visible_and_conditions_empty(self):
        code = browser.search_reset_code("초기화")
        self.assertIn("keywordVisible", code)
        self.assertIn("conditions.length===0", code)
        self.assertIn("clean_without_visible_reset", code)
        self.assertIn("Reset missing with active conditions", code)

    def test_explicit_keyword_must_be_in_snapshot_plan(self):
        seen = []
        with patch.object(browser, "aside", self.fake_aside(seen)), self.assertRaisesRegex(
            browser.BrowserInputError, "not present in company snapshot"
        ):
            self.run_cli("search", "--tab", "tab-id", "--keyword", "outside",
                         "--company-snapshot", str(self.snapshot))
        self.assertEqual(seen, [])

    def test_malformed_tampered_blocked_or_empty_snapshot_blocks_before_browser(self):
        cases = [
            {"snapshot_hash": "wrong"},
            {"status": "blocked_company_identity"},
            {"channel_search_plan": {"jobkorea": []}},
        ]
        for override in cases:
            with self.subTest(override=override):
                self.write_snapshot(**override)
                seen = []
                with patch.object(browser, "aside", self.fake_aside(seen)), self.assertRaises(browser.BrowserInputError):
                    self.run_cli("search", "--tab", "tab-id", "--company-snapshot", str(self.snapshot))
                self.assertEqual(seen, [])

    def test_profile_local_only_saves_without_archive_remote_write(self):
        seen = []
        def fake_profile(code):
            seen.append(code)
            return {"url": "https://www.jobkorea.co.kr/User/Profile/1", "title": "p", "text": "profile"}
        with patch.object(browser, "aside", fake_profile):
            rc = self.run_cli("profile", "--url", "https://www.jobkorea.co.kr/User/Profile/1",
                              "--archive-config", str(self.root / "archive.json"),
                              "--run-id", "run-1", "--local-only")
        self.assertEqual(rc, 0)
        out = json.loads((self.root / "out.json").read_text())
        self.assertEqual(out["persistence_receipt"]["state"], "NOT_RUN_PERMISSION")
        self.assertEqual(out["run_id"], "run-1")


if __name__ == '__main__':
    unittest.main()
