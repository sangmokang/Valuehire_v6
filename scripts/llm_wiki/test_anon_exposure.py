"""익명(anon) 키 노출 감사 계약 시험 — SOT §4-b 의 객체는 anon 키로 건수가 0 이어야 한다.

실제 네트워크를 쓰지 않는다. 건수 조회 함수는 주입한다.
계약(EARS):
  - SOT 표 `| 객체 | anon 허용 건수 |` 의 허용 건수는 0 만 허용한다(다른 숫자는 정본 오류).
  - anon 건수 > 0 인 객체가 하나라도 있으면 FAIL. 조회 오류는 NOT_RUN. 검사 객체 0개는 FAIL.
  - 401/403 은 '차단됨' 이므로 0 으로 센다. 그 밖의 HTTP 오류는 조회 오류다.
  - anon 키가 없으면 rc 2(NOT_RUN). 값(개인정보)은 읽지 않는다.
"""
from __future__ import annotations

import io
import tempfile
import unittest
import urllib.error
from pathlib import Path

from scripts.llm_wiki import anon_exposure_audit as ax

OBJECTS = ["profile_archives", "gmail_messages", "gmail_sync_state", "candidates",
           "pipeline_candidates_active", "pipeline_candidates_archive", "unified_candidate_history_view"]
SOT = """
## 4. 최소 채움률
| 객체.필드 | 최소 채움률 | 실측 |
|---|---|---|
| profile_archives.structured_json | 2 | 2.4% |

### 4-b. 익명(anon) 키 허용 건수
| 객체 | anon 허용 건수 |
|---|---|
""" + "".join(f"| {o} | 0 |\n" for o in OBJECTS) + """
## 5. 다음 절
| ⓪ | 다른 표 | x |
"""


class ParseTests(unittest.TestCase):
    def test_parses_object_names_in_order(self):
        self.assertEqual(ax.parse_anon_zero_objects(SOT), OBJECTS)

    def test_malformed_row_inside_table_is_rejected(self):
        # Codex 2026-10-14 결함 4: 백틱·오타 행이 조용히 빠져 검사 대상이 줄어든다
        with self.assertRaises(ValueError):
            ax.parse_anon_zero_objects(SOT.replace("| profile_archives | 0 |", "| `profile_archives` | 0 |"))

    def test_required_object_removed_is_rejected(self):
        with self.assertRaises(ValueError):
            ax.parse_anon_zero_objects(SOT.replace("| gmail_messages | 0 |\n", ""))

    def test_rows_outside_the_anon_table_are_ignored(self):
        self.assertNotIn("x", ax.parse_anon_zero_objects(SOT))

    def test_field_rows_with_dot_are_not_objects(self):
        self.assertNotIn("profile_archives.structured_json", ax.parse_anon_zero_objects(SOT))

    def test_non_zero_allowance_is_rejected(self):
        with self.assertRaises(ValueError):
            ax.parse_anon_zero_objects(SOT.replace("| gmail_messages | 0 |", "| gmail_messages | 5 |"))

    def test_missing_table_is_rejected(self):
        with self.assertRaises(ValueError):
            ax.parse_anon_zero_objects("## 4-b\n없음\n")


class JudgeTests(unittest.TestCase):
    def test_exposed_count_is_fail(self):
        v = ax.judge([ax.ObjectStat("a", 0), ax.ObjectStat("b", 21651)], ["a", "b"])
        self.assertEqual(v.status, "FAIL")
        self.assertEqual(v.failures, ["b: anon 노출 21651건"])

    def test_all_zero_is_pass(self):
        self.assertEqual(ax.judge([ax.ObjectStat("a", 0), ax.ObjectStat("b", 0)], ["a", "b"]).status, "PASS")

    def test_error_is_not_run(self):
        v = ax.judge([ax.ObjectStat("a", None, error="timeout")], ["a"])
        self.assertEqual(v.status, "NOT_RUN")

    def test_missing_object_and_empty_list_are_fail(self):
        self.assertEqual(ax.judge([ax.ObjectStat("a", 0)], ["a", "b"]).status, "FAIL")
        self.assertEqual(ax.judge([], []).status, "FAIL")


DENIED = (401, b'{"code":"42501","message":"permission denied for materialized view x"}')
BAD_KEY = (401, b'{"message":"Invalid API key"}')


class CollectTests(unittest.TestCase):
    def _counter(self, mapping):
        def counter(base, key, table, filt):
            r = mapping[table]
            if isinstance(r, tuple):
                raise urllib.error.HTTPError(f"{base}/{table}", r[0], "x", {}, io.BytesIO(r[1]))
            return r
        return counter

    def test_permission_denied_counts_as_blocked_zero(self):
        stats = ax.collect("https://x", "k", ["a", "b", "c"], counter=self._counter({"a": DENIED, "b": (403, DENIED[1]), "c": 7}))
        self.assertEqual([(s.name, s.count, s.error) for s in stats], [("a", 0, None), ("b", 0, None), ("c", 7, None)])

    def test_head_without_body_is_classified_by_get_lookup(self):
        # 운영 실측(2026-10-14 14:09): HEAD 의 401 은 본문이 없다. GET 재조회로 42501 이면 차단, 아니면 오류.
        stats = ax.collect("https://x", "k", ["a", "b"], counter=self._counter({"a": (401, b""), "b": (401, b"")}),
                           denial_lookup=lambda base, key, name: {"code": "42501"} if name == "a" else {"message": "Invalid API key"})
        self.assertEqual([(s.name, s.count) for s in stats], [("a", 0), ("b", None)])

    def test_invalid_api_key_401_is_error_not_blocked(self):
        # Codex 2026-10-14 결함 1: 무효 키의 401 을 차단 성공으로 세면 안 된다
        stats = ax.collect("https://x", "k", ["a"], counter=self._counter({"a": BAD_KEY}))
        self.assertEqual(stats[0].count, None)
        self.assertIn("Invalid API key", stats[0].error)

    def test_other_http_error_is_error(self):
        stats = ax.collect("https://x", "k", ["a"], counter=self._counter({"a": (500, b"boom")}))
        self.assertEqual(stats[0].count, None)
        self.assertIn("500", stats[0].error)


class KeyProbeTests(unittest.TestCase):
    """anon 키가 살아 있는지 양성 대조군: 탐침 객체에 2xx 또는 권한 거부(42501)면 인증됨, "Invalid API key" 401 이면 죽은 키."""

    def test_valid_key_probe_true_and_invalid_false(self):
        class OK:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *a): return False
        self.assertTrue(ax.key_is_valid("https://x", "k", opener=lambda req, timeout: OK()))

        def denied(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 401, "x", {}, io.BytesIO(DENIED[1]))
        self.assertTrue(ax.key_is_valid("https://x", "k", opener=denied))

        def bad(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 401, "x", {}, io.BytesIO(BAD_KEY[1]))
        self.assertFalse(ax.key_is_valid("https://x", "k", opener=bad))


class CredsTests(unittest.TestCase):
    def test_missing_anon_key_is_exit_2(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("NEXT_PUBLIC_SUPABASE_URL=https://x.supabase.co\n")
        with self.assertRaises(SystemExit) as cm:
            ax.load_anon_creds(Path(f.name))
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
