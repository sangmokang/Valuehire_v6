"""2026-09-03 Codex 적대 검증 값-우회 반례의 영구 회귀 (R9).

find_sensitive_values가 놓쳤던 값 계열: 프로필 URL, 전각 ＠ 이메일, 전각 숫자 전화,
주민등록번호, 비한국 전화, 문자열화 JSON 내 금지 키. 정당 값 오탐 0건도 함께 고정한다.
"""

import unittest

from fixtures import load_gate, valid_bundle


class WeeklyGatePiiValueTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()

    def assert_action_value_blocked(self, value):
        bundle = valid_bundle()
        bundle["positions"][0]["action"] = value
        result = self.gate.evaluate(bundle)
        self.assertEqual(result["data_verdict"], "BLOCKED")
        self.assertIn("FORBIDDEN_SENSITIVE_VALUE", result["errors"])
        self.assertEqual(result["brief_markdown"], "")

    def test_profile_url_values_are_blocked(self):
        for value in (
            "https://www.linkedin.com/in/synthetic-person",
            "https://kr.linkedin.com/in/synthetic-person",
            "https://lnkd.in/xyz-synthetic",
            "https://github.com/synthetic-person",
            "후보 프로필은 www.linkedin.com/in/synthetic-person 참조",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_fullwidth_unicode_variants_are_blocked_after_nfkc(self):
        for value in (
            "연락은 synthetic＠example.com 으로",
            "０１０-１２３４-５６７８",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_resident_registration_numbers_are_blocked(self):
        for value in (
            "900101-1234567",
            "900101 1234567",
            "9001011234567",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_international_phone_numbers_are_blocked(self):
        for value in (
            "+1 415 555 2671",
            "+44 20 7946 0958",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_stringified_json_with_forbidden_key_tokens_is_blocked(self):
        for value in (
            '{"name": "synthetic-name"}',
            '{"candidate_name": "synthetic-name"}',
            "비고: 'candidate_name': 'synthetic-name' 형태 유입",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_candidate_alias_style_keys_stay_blocked_by_allowlist(self):
        for field in ("candidate_alias", "candidateDisplayNameV2"):
            with self.subTest(field=field):
                bundle = valid_bundle()
                bundle["positions"][0][field] = "synthetic-name"
                result = self.gate.evaluate(bundle)
                self.assertEqual(result["data_verdict"], "BLOCKED")
                self.assertIn("FORBIDDEN_UNKNOWN_FIELD", result["errors"])

    def test_legitimate_values_have_zero_false_positives(self):
        for value in (
            "https://careers.codeit.com/recruit",
            "https://www.jobkorea.co.kr/corp/person/position",
            "https://app.notion.com/p/valueconnect/1975f52f80964fb1996eed3b0226e633",
            "[week_start, week_end) exact SQL counts; current snapshots are explicitly separate",
            "후보군 확장과 1차 추천 일정 확정",
            "26W35 신규 포지션 14개, 2026-08-31T05:35:00+09:00 기준",
        ):
            with self.subTest(value=value):
                bundle = valid_bundle()
                bundle["positions"][0]["action"] = value
                result = self.gate.evaluate(bundle)
                self.assertNotIn("FORBIDDEN_SENSITIVE_VALUE", result["errors"])
                self.assertEqual(result["data_verdict"], "PASS")

    def test_allowlisted_email_target_is_not_a_false_positive(self):
        bundle = valid_bundle()
        email_target = next(
            target for target in bundle["publication_targets"] if target["name"] == "email"
        )
        email_target["target_id"] = "sangmokang@valueconnect.kr"
        result = self.gate.evaluate(bundle)
        self.assertNotIn("FORBIDDEN_SENSITIVE_VALUE", result["errors"])
        self.assertEqual(result["data_verdict"], "PASS")


class WeeklyGateFinalOutputRescanTest(unittest.TestCase):
    """WU-3: renderer 이후 최종 산출물 독립 재검사 — 마지막 방어선."""

    def evaluate_with_injected_brief(self, injected_line):
        gate = load_gate()
        original = gate.render_brief
        gate.render_brief = (
            lambda *args, **kwargs: original(*args, **kwargs) + "\n" + injected_line
        )
        result = gate.evaluate(valid_bundle())
        return gate, result

    def test_renderer_injected_email_is_blocked_and_payload_is_stripped(self):
        gate, result = self.evaluate_with_injected_brief(
            "- 문의: synthetic.person@example.com"
        )
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("FORBIDDEN_SENSITIVE_OUTPUT", result["errors"])
        self.assertEqual(result["brief_markdown"], "")
        self.assertEqual(result["positions"], [])
        self.assertNotIn("synthetic.person@example.com", gate.canonical_json(result))

    def test_renderer_injected_phone_is_blocked(self):
        gate, result = self.evaluate_with_injected_brief("- 연락처: 010-1234-5678")
        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("FORBIDDEN_SENSITIVE_OUTPUT", result["errors"])
        self.assertNotIn("010-1234-5678", gate.canonical_json(result))

    def test_injected_forbidden_or_unknown_output_keys_are_violations(self):
        gate = load_gate()
        clean = gate.evaluate(valid_bundle())
        self.assertEqual(gate.final_output_violations(clean), [])
        with_forbidden = dict(clean, candidate_name="synthetic-name")
        self.assertTrue(gate.final_output_violations(with_forbidden))
        with_unknown = dict(clean, kakao_id="synthetic-value")
        self.assertTrue(gate.final_output_violations(with_unknown))

    def test_clean_bundle_keeps_full_payload_after_rescan(self):
        gate = load_gate()
        result = gate.evaluate(valid_bundle())
        self.assertEqual(result["data_verdict"], "PASS")
        self.assertNotEqual(result["brief_markdown"], "")
        self.assertNotIn("FORBIDDEN_SENSITIVE_OUTPUT", result["errors"])


if __name__ == "__main__":
    unittest.main()
