from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_DIR = REPO_ROOT / "tools" / "invoice"
sys.path.insert(0, str(MODULE_DIR))
import generate_deduction as deduction  # noqa: E402


CONTRACT_PATH = REPO_ROOT / "contracts" / "invoice" / "deduction-v1.json"


class DeductionGeneratorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = deduction.load_contract(CONTRACT_PATH)

    @staticmethod
    def payload(**overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "settlement_number": "DRAFT-SET-20260901-001",
            "invoice_number": "DRAFT-20260901-001",
            "fee_agreement_ref": "TEST-CLIENT-POSITION-2026",
            "issue_date": "2026-09-01",
            "company_name": "가상회사",
            "candidate_name": "홍길동",
            "start_date": "2026-09-01",
            "position": "테스트 엔지니어",
            "annual_salary_manwon": 6000,
            "guarantee_months": 3,
            "fee_percent": "20",
            "account_manager_name": None,
            "account_manager_percent": "45",
            "coworker_name": None,
            "coworker_percent": "30",
            "rps_status": "pending",
            "rps_advance_krw": None,
            "rps_bearer": None,
            "draft": True,
        }
        base.update(overrides)
        return base

    def calculate(self, **overrides: object):
        source = deduction.validate_input(self.payload(**overrides), self.contract)
        return deduction.calculate_settlement(source, self.contract)

    def test_reference_example_locks_25_percent_split_and_withholding(self) -> None:
        result = self.calculate(
            annual_salary_manwon=8000,
            fee_percent="15",
            account_manager_percent="40",
            coworker_percent="35",
        )
        self.assertEqual(result.invoice_amount_krw, 12_000_000)
        self.assertEqual(result.company_share_krw, 3_000_000)
        self.assertEqual(result.account_manager_gross_krw, 4_800_000)
        self.assertEqual(result.coworker_gross_krw, 4_200_000)
        self.assertEqual(result.account_manager_withholding_krw, 158_400)
        self.assertEqual(result.coworker_withholding_krw, 138_600)
        self.assertEqual(result.account_manager_net_krw, 4_641_600)
        self.assertEqual(result.coworker_net_krw, 4_061_400)

    def test_current_45_30_split_is_calculated_from_invoice_amount(self) -> None:
        result = self.calculate()
        self.assertEqual(result.invoice_amount_krw, 12_000_000)
        self.assertEqual(result.company_share_krw, 3_000_000)
        self.assertEqual(result.account_manager_gross_krw, 5_400_000)
        self.assertEqual(result.coworker_gross_krw, 3_600_000)
        self.assertEqual(result.account_manager_withholding_krw, 178_200)
        self.assertEqual(result.coworker_withholding_krw, 118_800)
        self.assertEqual(result.account_manager_net_krw, 5_221_800)
        self.assertEqual(result.coworker_net_krw, 3_481_200)

    def test_rps_deduction_requires_amount_and_bearer_and_cannot_overdraw(self) -> None:
        with self.assertRaisesRegex(deduction.InputError, "requires rps_bearer"):
            deduction.validate_input(
                self.payload(rps_status="deducted", rps_advance_krw=100_000),
                self.contract,
            )
        with self.assertRaisesRegex(deduction.InputError, "requires a positive"):
            deduction.validate_input(
                self.payload(rps_status="deducted", rps_bearer="coworker"),
                self.contract,
            )
        result = self.calculate(
            rps_status="deducted",
            rps_advance_krw=100_000,
            rps_bearer="account_manager",
        )
        self.assertEqual(result.account_manager_rps_krw, 100_000)
        self.assertEqual(result.account_manager_net_krw, 5_121_800)
        with self.assertRaisesRegex(deduction.InputError, "exceeds"):
            self.calculate(
                rps_status="deducted",
                rps_advance_krw=4_000_000,
                rps_bearer="coworker",
            )

    def test_final_requires_names_and_explicit_zero_rps(self) -> None:
        with self.assertRaisesRegex(deduction.InputError, "explicit RPS"):
            deduction.validate_input(self.payload(draft=False), self.contract)
        with self.assertRaisesRegex(deduction.InputError, "account_manager_name"):
            deduction.validate_input(
                self.payload(draft=False, rps_status="none", rps_advance_krw=0),
                self.contract,
            )
        source = deduction.validate_input(
            self.payload(
                draft=False,
                rps_status="deferred",
                rps_advance_krw=0,
                account_manager_name="담당자",
                coworker_name="코웍자",
            ),
            self.contract,
        )
        self.assertFalse(source.draft)
        html = deduction.render_html(deduction.calculate_settlement(source, self.contract), self.contract)
        self.assertIn("배분·원천징수 확인 완료 · RPS 이번 Term 미공제", html)
        self.assertIn("이번 Term에서 미공제, 추후 공제 예정", html)
        self.assertIn("이번 Term 세후 지급액", html)
        self.assertNotIn("미입력 항목 확정 전", html)
        self.assertNotIn("내부 정산 검수용", html)

    def test_rejects_invalid_totals_types_unknown_fields_and_dates(self) -> None:
        cases = (
            {"coworker_percent": "29"},
            {"fee_percent": 20},
            {"fee_percent": "NaN"},
            {"fee_percent": "Infinity"},
            {"annual_salary_manwon": True},
            {"guarantee_months": 61},
            {"start_date": "2026-02-30"},
            {"rps_status": "unknown"},
            {"mystery": 1},
        )
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(deduction.InputError):
                deduction.validate_input(self.payload(**changes), self.contract)

    def test_html_contains_required_fields_and_escapes_names(self) -> None:
        source = deduction.validate_input(
            self.payload(company_name="가상 <회사>", account_manager_name="{담당자}"),
            self.contract,
        )
        html = deduction.render_html(deduction.calculate_settlement(source, self.contract), self.contract)
        for required in (
            "계산서 발행 정산 내역",
            "INVOICE DRAFT-20260901-001",
            "RPS STATUS PENDING",
            "가상 &lt;회사&gt;",
            "&#123;담당자&#125;",
            "12,000,000원",
            "20%",
            "45%",
            "30%",
            "3,000,000원",
            "5,400,000원",
            "3,600,000원",
            "5,221,800원",
            "3,481,200원",
            "RPS 회사 선결제 상태",
            "미입력 · 금액/부담 주체 확정 필요",
            "DRAFT · 검수용",
            "세금계산서가 아닙니다",
        ):
            with self.subTest(required=required):
                self.assertIn(required, html)
        self.assertNotIn("<h1>DEDUCTION</h1>", html)
        self.assertNotIn(">DEDUCTIONS<", html)
        self.assertNotIn("가상 <회사>", html)
        self.assertNotIn("E+", html)

    def test_generates_three_outputs_and_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path, output_path = root / "input.json", root / "settlement.pdf"
            input_path.write_text(json.dumps(self.payload(), ensure_ascii=False), encoding="utf-8")

            def fake_render(_chrome: str, _html: Path, pdf: Path, _profile: Path) -> None:
                pdf.write_bytes(b"%PDF-1.7\n" + b"x" * 1100 + b"\n/Type /Page\n%%EOF\n")

            with mock.patch.object(deduction.invoice_core, "ARTIFACT_ROOT", root), mock.patch.object(
                deduction.invoice_core, "find_chrome", return_value="chrome"
            ), mock.patch.object(deduction.invoice_core, "_render_pdf", side_effect=fake_render):
                result, pdf, html, metadata, digest = deduction.generate_files(
                    input_path, output_path, CONTRACT_PATH, None, False
                )
                self.assertEqual(result.invoice_amount_krw, 12_000_000)
                self.assertTrue(all(path.stat().st_size > 0 for path in (pdf, html, metadata)))
                stored = json.loads(metadata.read_text())
                self.assertEqual(stored["pdf_sha256"], digest)
                self.assertEqual(stored["fee_authority"], "UNVERIFIED_DRAFT")
                self.assertEqual(stored["invoice_number"], "DRAFT-20260901-001")
                self.assertEqual(
                    stored["fee_agreement_ref"], "TEST-CLIENT-POSITION-2026"
                )
                with self.assertRaisesRegex(deduction.InputError, "already exists"):
                    deduction.generate_files(input_path, output_path, CONTRACT_PATH, None, False)

    def test_final_file_generation_fails_closed_without_remote_fee_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path, output_path = root / "input.json", root / "settlement.pdf"
            input_path.write_text(
                json.dumps(self.payload(
                    draft=False,
                    account_manager_name="담당자",
                    coworker_name="코웍자",
                    rps_status="deferred",
                    rps_advance_krw=0,
                ), ensure_ascii=False),
                encoding="utf-8",
            )
            with mock.patch.object(deduction.invoice_core, "ARTIFACT_ROOT", root), mock.patch.object(
                deduction.invoice_core.storage_remote,
                "verify_fee_authority",
                side_effect=deduction.invoice_core.storage_remote.RemoteError("network unavailable"),
            ), self.assertRaisesRegex(deduction.ContractError, "was not proven"):
                deduction.generate_files(input_path, output_path, CONTRACT_PATH, None, False)
            self.assertFalse(output_path.exists())

    def test_contract_constants_are_locked(self) -> None:
        self.assertEqual(self.contract["issuer_name"], "밸류커넥트 주식회사")
        self.assertEqual(self.contract["company_share_percent"], "25")
        self.assertEqual(self.contract["withholding_percent"], "3.3")
        self.assertEqual(self.contract["allocation_total_percent"], "100")
        self.assertEqual(set(self.contract["rps_bearers"]), set(deduction.RPS_BEARER_LABELS))
        self.assertEqual(
            set(self.contract["rps_statuses"]),
            {"pending", "none", "deferred", "deducted"},
        )
        self.assertEqual(self.contract["document"]["title_ko"], "계산서 발행 정산 내역")
        self.assertEqual(
            self.contract["document"]["status_en"]["deferred"],
            "RPS NOT DEDUCTED THIS TERM",
        )
        self.assertEqual(
            self.contract["document"]["zero_rps_status"],
            "이번 Term에서 미공제, 추후 공제 예정",
        )


if __name__ == "__main__":
    unittest.main()
