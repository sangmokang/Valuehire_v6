"""2026-09-03 Codex 적대 검증 값-우회 반례의 영구 회귀 (R9).

find_sensitive_values가 놓쳤던 값 계열: 프로필 URL, 전각 ＠ 이메일, 전각 숫자 전화,
주민등록번호, 비한국 전화, 문자열화 JSON 내 금지 키. 정당 값 오탐 0건도 함께 고정한다.
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from fixtures import load_gate, mark_all_targets_verified, valid_bundle


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

    def test_unicode_dash_and_dot_separator_variants_are_blocked(self):
        # 2026-09-04 codeaudit B-트랙 발견 반례 (R9): NFKC가 정규화하지 않는 대시 변형
        for value in (
            "010–1234–5678",   # en dash
            "010—1234—5678",   # em dash
            "010−1234−5678",   # minus sign
            "900101–1234567",       # en dash 주민번호
            "900101.1234567",            # 점 구분 주민번호
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

    def test_codex_v2_false_negative_formats_are_blocked(self):
        # 2026-09-04 fresh Codex V2 FAIL 반례의 영구 회귀 (R9)
        for value in (
            '"synthetic.person"@example.com',
            "010/1234/5678",
            "+1 (415) 555-2671",
            "900101/1234567",
            "https://github.com:443/synthetic-person",
            '비고: {"candidateName":"synthetic-person"}',
            '비고: {"이름":"synthetic-name"}',
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_codex_v2_round2_false_negative_formats_are_blocked(self):
        # 2026-09-04 fresh Codex V2 2차 FAIL 반례의 영구 회귀 (R9)
        for value in (
            '"John Doe"@example.com',
            "홍길동@예시.한국",
            "(02) 123-4567",
            "900101-5234567",
            "900101 - 1234567",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_codex_v2_round3_false_negative_formats_are_blocked(self):
        # 2026-09-04 fresh Codex V2 3차 FAIL 반례의 영구 회귀 (R9)
        for value in (
            '"홍 길동"@예시.한국',
            "user@example.xn--3e0b707e",
            "(02) 123 - 4567",
            "010-1234-5678x123",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_codex_v2_round4_false_negative_formats_are_blocked(self):
        # 2026-09-04 fresh Codex V2 4차 FAIL 반례의 영구 회귀 (R9)
        for value in (
            "user@[192.0.2.1]",
            "(02)   123 - 4567",
            "https://www.linkedin.com./in/synthetic-person",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_email_publication_target_enforces_recipient_allowlist(self):
        # V2 4차 반례: publication_state가 수신자 allowlist를 구조적으로 강제하지 않았다
        for target_id in ("user@[192.0.2.1]", "ops-mailing-list"):
            with self.subTest(target_id=target_id):
                bundle = valid_bundle()
                email_target = next(
                    target for target in bundle["publication_targets"]
                    if target["name"] == "email"
                )
                email_target["target_id"] = target_id
                result = self.gate.evaluate(bundle)
                self.assertEqual(result["verdict"], "BLOCKED")
                self.assertIn("EMAIL_TARGET_NOT_ALLOWLISTED", result["errors"])

    def test_codex_v2_round5_false_negative_formats_are_blocked(self):
        # 2026-09-04 fresh Codex V2 5차 FAIL 반례의 영구 회귀 (R9)
        for value in (
            "user@[IPv6:2001:db8::1]",
            "user!@example.com",
            "+33 1 42 68 53 00",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_codex_v2_round6_false_negative_formats_are_blocked(self):
        # 2026-09-04 fresh Codex V2 6차 FAIL 반례의 영구 회귀 (R9)
        for value in (
            '"john@doe"@example.com',
            "+82 2 1234 5678",
            "+81 3 1234 5678",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_codex_v2_round7_false_negative_formats_are_blocked(self):
        # 2026-09-04 fresh Codex V2 7차 FAIL 반례의 영구 회귀 (R9)
        # + URL 정책을 승인 호스트 allowlist(fail-closed)로 반전
        for value in (
            '후보 데이터: {"firstName":"John","lastName":"Doe"}',
            "https://www.behance.net/synthetic-designer",
            "https://gitlab.com/synthetic-person",
            "https://unknown-portfolio.example/synthetic-person",
        ):
            with self.subTest(value=value):
                self.assert_action_value_blocked(value)

    def test_business_delta_notation_is_not_an_intl_phone(self):
        bundle = valid_bundle()
        bundle["positions"][0]["action"] = "전주 대비 +1 234 567건 증가"
        result = self.gate.evaluate(bundle)
        self.assertNotIn("FORBIDDEN_SENSITIVE_VALUE", result["errors"])
        self.assertEqual(result["data_verdict"], "PASS")

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


class WeeklyGateMainEndToEndTest(unittest.TestCase):
    """Codex V2 지적: evaluate만 검증하고 main 종단 경로는 무검증이던 공백을 닫는다."""

    def run_main(self, bundle, fmt):
        gate = load_gate()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.json"
            path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = gate.main([str(path), "--format", fmt])
        return code, buffer.getvalue()

    def test_allowlisted_email_target_publishes_in_every_format(self):
        gate = load_gate()
        bundle = valid_bundle()
        email_target = next(
            target for target in bundle["publication_targets"] if target["name"] == "email"
        )
        email_target["target_id"] = "sangmokang@valueconnect.kr"
        first = gate.evaluate(bundle)
        mark_all_targets_verified(bundle, first)
        for fmt in ("json", "markdown", "html"):
            with self.subTest(fmt=fmt):
                code, output = self.run_main(bundle, fmt)
                self.assertEqual(code, 0)
                self.assertNotIn("FORBIDDEN_SENSITIVE_OUTPUT", output)

    def run_main_with_html_injection(self, injected):
        gate = load_gate()
        original = gate.render_html
        gate.render_html = lambda *args, **kwargs: original(*args, **kwargs) + injected
        bundle = valid_bundle()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bundle.json"
            path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = gate.main([str(path), "--format", "html"])
        return code, buffer.getvalue()

    def test_post_render_injection_is_blocked_by_main_rescan(self):
        # main의 최종 문자열 검사만 무력화해도 죽는 격리 반례 (V2 2차: 공허 테스트 지적)
        code, output = self.run_main_with_html_injection(
            "<p>synthetic.person@example.com</p>"
        )
        self.assertEqual(code, 1)
        self.assertNotIn("synthetic.person@example.com", output)

    def test_allowlist_prefix_injection_cannot_slip_past_masking(self):
        # V2 2차 반례: substring 마스킹이 sangmokang@valueconnect.kr.evil.com 을 통과시킴
        code, output = self.run_main_with_html_injection(
            "<p>sangmokang@valueconnect.kr.evil.com</p>"
        )
        self.assertEqual(code, 1)
        self.assertNotIn("evil.com", output)

    def test_allowlist_email_injected_into_html_is_still_blocked(self):
        # V2 3차 반례: allowlist 이메일의 정당한 자리는 JSON target_id뿐 —
        # 렌더링된 HTML에 등장하면 마스킹 없이 차단돼야 한다
        code, output = self.run_main_with_html_injection(
            "<p>sangmokang@valueconnect.kr</p>"
        )
        self.assertEqual(code, 1)
        self.assertNotIn("sangmokang@valueconnect.kr", output)

    def test_pii_action_never_reaches_stdout_in_any_format(self):
        bundle = valid_bundle()
        bundle["positions"][0]["action"] = "연락 010/1234/5678 부탁"
        for fmt in ("json", "markdown", "html"):
            with self.subTest(fmt=fmt):
                code, output = self.run_main(bundle, fmt)
                self.assertEqual(code, 1)
                self.assertNotIn("010/1234/5678", output)


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
