"""LLM 위키 필드 감사기 판정 계약 시험 (네트워크 없음)."""
from __future__ import annotations

import unittest

from scripts.llm_wiki import field_audit as fa


class JudgeTests(unittest.TestCase):
    def test_fill_rate_below_floor_is_fail(self):
        rows = [fa.FieldStat("profile_archives", "structured_json", total=100, nulls=98)]
        verdict = fa.judge(rows, {("profile_archives", "structured_json"): 50.0})
        self.assertEqual(verdict.status, "FAIL")
        self.assertIn("profile_archives.structured_json", verdict.failures[0])

    def test_fill_rate_at_floor_is_pass(self):
        rows = [fa.FieldStat("t", "c", total=200, nulls=100)]
        self.assertEqual(fa.judge(rows, {("t", "c"): 50.0}).status, "PASS")

    def test_zero_total_is_fail_not_pass(self):
        # 검사 대상 0개는 합격이 아니다 (P20)
        rows = [fa.FieldStat("t", "c", total=0, nulls=0)]
        self.assertEqual(fa.judge(rows, {("t", "c"): 0.0}).status, "FAIL")

    def test_missing_threshold_field_is_fail(self):
        # 문턱이 정의된 필드가 집계에 없으면 조용히 통과하지 않는다
        verdict = fa.judge([], {("t", "c"): 10.0})
        self.assertEqual(verdict.status, "FAIL")

    def test_error_stat_is_not_run(self):
        rows = [fa.FieldStat("t", "c", total=None, nulls=None, error="HTTP 401")]
        self.assertEqual(fa.judge(rows, {("t", "c"): 10.0}).status, "NOT_RUN")

    def test_thresholds_parse_from_sot_table(self):
        md = (
            "| 객체.필드 | 최소 채움률 |\n|---|---|\n"
            "| profile_archives.structured_json | 60 |\n"
            "| gmail_derived_events.candidate_id | 0 |\n"
        )
        got = fa.parse_thresholds(md)
        self.assertEqual(got[("profile_archives", "structured_json")], 60.0)
        self.assertEqual(got[("gmail_derived_events", "candidate_id")], 0.0)

    def test_duplicate_field_row_is_rejected(self):
        # V1 결함 3: 같은 필드를 두 번 적으면 낮은 값으로 덮이지 않고 거부한다
        md = "| 객체.필드 | 최소 채움률 |\n|---|---|\n| t.c | 75 |\n| t.c | 0 |\n"
        with self.assertRaises(ValueError):
            fa.parse_thresholds(md)

    def test_unparseable_number_row_is_rejected_not_dropped(self):
        md = "| 객체.필드 | 최소 채움률 |\n|---|---|\n| t.c | 50% |\n| t.d | 10 |\n"
        with self.assertRaises(ValueError):
            fa.parse_thresholds(md)

    def test_decimal_threshold_is_not_truncated(self):
        md = "| 객체.필드 | 최소 채움률 |\n|---|---|\n| t.c | 2.4 |\n"
        self.assertEqual(fa.parse_thresholds(md)[("t", "c")], 2.4)
        rows = [fa.FieldStat("t", "c", total=1000, nulls=977)]  # 2.3% < 2.4
        self.assertEqual(fa.judge(rows, {("t", "c"): 2.4}).status, "FAIL")

    def test_empty_threshold_table_is_rejected(self):
        with self.assertRaises(ValueError):
            fa.parse_thresholds("# 아무 표 없음\n")


if __name__ == "__main__":
    unittest.main()
