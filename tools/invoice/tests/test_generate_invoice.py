from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO_ROOT / "tools" / "invoice" / "generate_invoice.py"
CONTRACT_PATH = REPO_ROOT / "contracts" / "invoice" / "invoice-v1.json"
SPEC = importlib.util.spec_from_file_location("invoice_generator", MODULE_PATH)
assert SPEC and SPEC.loader
invoice_generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(invoice_generator)


class InvoiceGeneratorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = invoice_generator.load_contract(CONTRACT_PATH)

    @staticmethod
    def payload(**overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "invoice_number": "DRAFT-20260901-001",
            "issue_date": "2026-09-01",
            "company_name": "가상회사",
            "candidate_name": "홍길동",
            "start_date": "2026-09-01",
            "position": "테스트 엔지니어",
            "annual_salary_krw": 60_000_000,
            "draft": True,
        }
        base.update(overrides)
        return base

    def calculate(self, **overrides: object):
        validated = invoice_generator.validate_input(self.payload(**overrides), self.contract)
        return invoice_generator.calculate_invoice(validated, self.contract)

    def test_calculates_fee_and_calendar_due_date(self) -> None:
        self.assertEqual(invoice_generator._won(invoice_generator.Decimal("1.5")), 2)
        result = self.calculate()
        self.assertEqual(result.requested_fee_krw, 12_000_000)
        self.assertEqual(result.total_amount_krw, 12_000_000)
        self.assertEqual(result.due_date, date(2026, 9, 15))

        second = self.calculate(annual_salary_krw=40_000_000)
        self.assertEqual(second.requested_fee_krw, 8_000_000)

        rounded = self.calculate(annual_salary_krw=12_345_678)
        self.assertEqual(rounded.requested_fee_krw, 2_469_136)

        manwon_payload = self.payload(annual_salary_manwon=6_000)
        manwon_payload.pop("annual_salary_krw")
        validated = invoice_generator.validate_input(manwon_payload, self.contract)
        manwon_result = invoice_generator.calculate_invoice(validated, self.contract)
        self.assertEqual(manwon_result.source.annual_salary_krw, 60_000_000)
        self.assertEqual(manwon_result.requested_fee_krw, 12_000_000)

    def test_due_date_crosses_month_and_leap_day(self) -> None:
        month_end = self.calculate(start_date="2026-01-25")
        leap_day = self.calculate(start_date="2028-02-20")
        year_end = self.calculate(start_date="2026-12-25")
        self.assertEqual(month_end.due_date, date(2026, 2, 8))
        self.assertEqual(leap_day.due_date, date(2028, 3, 5))
        self.assertEqual(year_end.due_date, date(2027, 1, 8))

    def test_rejects_calculated_and_unknown_input_fields(self) -> None:
        for key in ("fee_amount", "requested_fee", "total_amount", "due_date", "mystery"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(invoice_generator.InputError, "unknown field"):
                    invoice_generator.validate_input(self.payload(**{key: 1}), self.contract)

    def test_rejects_invalid_salary_values(self) -> None:
        for value in (True, 0, -1, 10_000_000_001, 60_000_000.0, "60000000"):
            with self.subTest(value=value):
                with self.assertRaises(invoice_generator.InputError):
                    invoice_generator.validate_input(
                        self.payload(annual_salary_krw=value), self.contract
                    )
        both = self.payload(annual_salary_manwon=6_000)
        with self.assertRaisesRegex(invoice_generator.InputError, "exactly one"):
            invoice_generator.validate_input(both, self.contract)

        missing = self.payload()
        missing.pop("annual_salary_krw")
        with self.assertRaisesRegex(invoice_generator.InputError, "exactly one"):
            invoice_generator.validate_input(missing, self.contract)

    def test_rejects_blank_long_and_invalid_date_values(self) -> None:
        cases = (
            {"company_name": "   "},
            {"position": "x" * 121},
            {"start_date": "2026-02-30"},
            {"start_date": "2029-02-29"},
            {"issue_date": "09/01/2026"},
        )
        for payload in cases:
            with self.subTest(payload=payload):
                with self.assertRaises(invoice_generator.InputError):
                    invoice_generator.validate_input(self.payload(**payload), self.contract)

    def test_rejects_final_document_while_tax_is_unconfirmed(self) -> None:
        with self.assertRaisesRegex(invoice_generator.ContractError, "tax policy"):
            invoice_generator.validate_input(self.payload(draft=False), self.contract)

    def test_html_contains_required_business_fields_and_escapes_input(self) -> None:
        validated = invoice_generator.validate_input(
            self.payload(
                invoice_number="{_format_krw(invoice.total_amount_krw)}",
                company_name="가상 <회사> {검수}",
            ),
            self.contract,
        )
        result = invoice_generator.calculate_invoice(validated, self.contract)
        html = invoice_generator.render_html(result, self.contract)

        for required in (
            "INVOICE",
            "채용 수수료 청구서",
            "밸류커넥트 주식회사",
            "가상 &lt;회사&gt; &#123;검수&#125;",
            "&#123;_format_krw(invoice.total_amount_krw)&#125;",
            "입사자명",
            "입사일",
            "직책",
            "결정 연봉",
            "60,000,000원",
            "요청 수수료",
            "12,000,000원",
            "총 청구 금액",
            "2026.09.15",
            "하나은행",
            "588-910030-71604",
            "DRAFT · 검수용",
            "메일 발송 안 됨",
        ):
            with self.subTest(required=required):
                self.assertIn(required, html)
        self.assertNotIn("가상 <회사>", html)
        self.assertNotIn("수수료율", html)

        changed_contract = json.loads(json.dumps(self.contract, ensure_ascii=False))
        changed_contract["issuer"]["company_name"] = "{draft_notice}"
        protected = invoice_generator.render_html(result, changed_contract)
        self.assertIn("&#123;draft_notice&#125;", protected)

    def test_generates_three_outputs_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "input.json"
            output_path = root / "invoice.pdf"
            input_path.write_text(
                json.dumps(self.payload(), ensure_ascii=False), encoding="utf-8"
            )

            def fake_render(_chrome: str, _html: Path, pdf: Path, _profile: Path) -> None:
                pdf.write_bytes(b"%PDF-1.7\n" + b"x" * 1100 + b"\n/Type /Page\n%%EOF\n")

            with mock.patch.object(invoice_generator, "ARTIFACT_ROOT", root), mock.patch.object(
                invoice_generator, "find_chrome", return_value="chrome"
            ), mock.patch.object(invoice_generator, "_render_pdf", side_effect=fake_render):
                result, pdf, html_path, metadata_path, digest = invoice_generator.generate_files(
                    input_path,
                    output_path,
                    CONTRACT_PATH,
                    None,
                    False,
                )
                self.assertEqual(result.requested_fee_krw, 12_000_000)
                self.assertTrue(all(path.stat().st_size > 0 for path in (pdf, html_path, metadata_path)))
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                self.assertEqual(metadata["pdf_sha256"], digest)
                with self.assertRaisesRegex(invoice_generator.InputError, "already exists"):
                    invoice_generator.generate_files(
                        input_path, output_path, CONTRACT_PATH, None, False
                    )

    def test_rejects_artifact_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "allowed"
            with mock.patch.object(invoice_generator, "ARTIFACT_ROOT", root):
                with self.assertRaisesRegex(invoice_generator.InputError, "must be inside"):
                    invoice_generator._ensure_artifact_path(Path(temp_dir) / "outside.pdf", "output")

    def test_contract_business_constants_are_locked(self) -> None:
        self.assertEqual(self.contract["issuer"]["company_name"], "밸류커넥트 주식회사")
        self.assertEqual(self.contract["billing"]["default_fee_rate"], "0.20")
        self.assertEqual(
            self.contract["billing"]["final_total_policy"], "BLOCK_UNTIL_CONFIRMED"
        )
        self.assertEqual(self.contract["payment"]["due_offset_days"], 14)
        self.assertEqual(self.contract["payment"]["bank_name"], "하나은행")
        self.assertEqual(self.contract["payment"]["account_number_display"], "588-910030-71604")
        self.assertEqual(
            self.contract["delivery"],
            {
                "default_recipient": "sangmokang@valueconnect.kr",
                "send_enabled": False,
                "require_final_confirmation": True,
                "require_attachment_sha256": True,
                "automatic_retry": False,
            },
        )

    def test_contract_loader_rejects_invalid_fields(self) -> None:
        source = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        mutations = (
            ("billing", "default_fee_rate", "not-a-decimal"),
            ("billing", "final_total_policy", "ALLOW"),
            ("payment", "due_offset_days", True),
            ("payment", "bank_name", ""),
            ("delivery", "default_recipient", "not-an-email"),
            ("delivery", "send_enabled", "false"),
        )
        for section, key, value in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temp_dir:
                mutated = json.loads(json.dumps(source, ensure_ascii=False))
                mutated[section][key] = value
                path = Path(temp_dir) / "contract.json"
                path.write_text(json.dumps(mutated, ensure_ascii=False), encoding="utf-8")
                with mock.patch.object(invoice_generator, "DEFAULT_CONTRACT", path):
                    with self.assertRaises(invoice_generator.ContractError):
                        invoice_generator.load_contract(path)

    def test_chrome_discovery_rejects_missing_explicit_binary(self) -> None:
        with self.assertRaises(invoice_generator.RenderError):
            invoice_generator.find_chrome("/definitely/missing/chrome")


if __name__ == "__main__":
    unittest.main()
