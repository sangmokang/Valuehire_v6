"""익명(anon) 키 노출 감사 계약 시험 — SOT §4-b 의 객체는 anon 키로 건수가 0 이어야 한다.

실제 네트워크를 쓰지 않는다. 건수 조회 함수는 주입한다.
계약(EARS):
  - SOT 표 `| 객체 | anon 허용 건수 |` 의 허용 건수는 0 만 허용한다(다른 숫자는 정본 오류).
  - anon 건수 > 0 인 객체가 하나라도 있으면 FAIL. 조회 오류는 NOT_RUN. 검사 객체 0개는 FAIL.
  - 401/403 은 '차단됨' 이므로 0 으로 센다. 그 밖의 HTTP 오류는 조회 오류다.
  - anon 키가 없으면 rc 2(NOT_RUN). 값(개인정보)은 읽지 않는다.
"""
from __future__ import annotations

import tempfile
import unittest
import urllib.error
from pathlib import Path

from scripts.llm_wiki import anon_exposure_audit as ax

SOT = """
## 4. 최소 채움률
| 객체.필드 | 최소 채움률 | 실측 |
|---|---|---|
| profile_archives.structured_json | 2 | 2.4% |

### 4-b. 익명(anon) 키 허용 건수
| 객체 | anon 허용 건수 |
|---|---|
| profile_archives | 0 |
| gmail_messages | 0 |
| pipeline_candidates_active | 0 |
"""


class ParseTests(unittest.TestCase):
    def test_parses_object_names_in_order(self):
        self.assertEqual(ax.parse_anon_zero_objects(SOT), ["profile_archives", "gmail_messages", "pipeline_candidates_active"])

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


class CollectTests(unittest.TestCase):
    def _counter(self, mapping):
        def counter(base, key, table, filt):
            r = mapping[table]
            if isinstance(r, int) and r >= 400:
                raise urllib.error.HTTPError(f"{base}/{table}", r, "x", {}, None)
            return r
        return counter

    def test_401_and_403_count_as_blocked_zero(self):
        stats = ax.collect("https://x", "k", ["a", "b", "c"], counter=self._counter({"a": 401, "b": 403, "c": 7}))
        self.assertEqual([(s.name, s.count, s.error) for s in stats], [("a", 0, None), ("b", 0, None), ("c", 7, None)])

    def test_other_http_error_is_error(self):
        stats = ax.collect("https://x", "k", ["a"], counter=self._counter({"a": 500}))
        self.assertEqual(stats[0].count, None)
        self.assertIn("500", stats[0].error)


class CredsTests(unittest.TestCase):
    def test_missing_anon_key_is_exit_2(self):
        with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
            f.write("NEXT_PUBLIC_SUPABASE_URL=https://x.supabase.co\n")
        with self.assertRaises(SystemExit) as cm:
            ax.load_anon_creds(Path(f.name))
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
