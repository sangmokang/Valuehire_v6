import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".agents/skills/weekly-ops/scripts/sot_gate.py"
spec = importlib.util.spec_from_file_location("weekly_sot_gate", MODULE_PATH)
sot_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sot_gate)


HEADINGS = (
    "## 권한과 정본 우선순위",
    "## 현재 구현 상태",
    "## 보고 주차와 4주 데이터",
    "## 실제 고객 포지션과 Scraped 경계",
    "## Task identity와 중복 제거",
    "## Pipeline 정의",
    "## 후보자 소싱",
    "## LinkedIn 시장 접근성",
    "## 소싱 커버리지 위험지수",
    "## Notion Golden Sample 형식",
    "## 외부 발행과 개인정보",
    "## 검증과 완료 조건",
    "## 롤백과 영향 반경",
)


def valid_files():
    sot = "\n".join(("# Weekly Ops", *HEADINGS)) + """
valuehire-report-calendar-v1
SCRAPED_STAGING CLIENT_REQUESTED CLIENT_SHARED
(candidate_key_hmac, position_id, hiring_cycle_id)
RECOMMENDATION_PENDING CLIENT_REVIEW ASSIGNMENT INTERVIEW_1 INTERVIEW_2
FINAL_INTERVIEW OFFER FINAL_ACCEPTED JOINED REJECTED WITHDRAWN CLOSED
Saramin JobKorea LinkedIn Recruiter
market_accessibility = (pool_points * precision_points * 100) // 2500
0/20 HARD 0 UNRANKED
A=70..100 B=40..69 C=0..39
P0/P1 즉시 실행 해야 한다
MODE_FORBIDS_PUBLICATION CONTRACT_ONLY_NOT_EXECUTABLE
"""
    legacy = {
        "runtime_status": {
            "state": "CONTRACT_ONLY_NOT_EXECUTABLE",
            "publication_allowed": False,
            "replacement_required": "notion-weekly-golden-v2",
        }
    }
    return {
        "sot": sot,
        "index": "[weekly-ops-contract.md](weekly-ops-contract.md)",
        "skill": "Read `docs/sot/weekly-ops-contract.md` before acting.",
        "prompt_contract": "Authority: `docs/sot/weekly-ops-contract.md`; Golden v1 is NOT_RUN.",
        "golden_reference": "Authority: `docs/sot/weekly-ops-contract.md`; publication is NOT_RUN.",
        "verification": "단위 테스트 0건 거부·mutation 생존 0건·CHECKED 양수",
        "legacy_contract": json.dumps(legacy),
    }


class WeeklySotContractTest(unittest.TestCase):
    def assert_error(self, files, code):
        self.assertIn(code, sot_gate.audit_bundle(files))

    def test_valid_contract_bundle_passes(self):
        self.assertEqual(sot_gate.audit_bundle(valid_files()), [])

    def test_missing_heading_fails(self):
        files = valid_files()
        files["sot"] = files["sot"].replace(HEADINGS[4], "")
        self.assert_error(files, "SOT_HEADING_MISSING:## Task identity와 중복 제거")

    def test_additive_market_formula_fails(self):
        files = valid_files()
        files["sot"] = files["sot"].replace(
            "(pool_points * precision_points * 100) // 2500",
            "pool_points + precision_points",
        )
        self.assert_error(files, "SOT_MARKET_FORMULA_MISSING")

    def test_pre_interview_stage_contract_fails_when_removed(self):
        files = valid_files()
        files["sot"] = files["sot"].replace("RECOMMENDATION_PENDING CLIENT_REVIEW", "")
        self.assert_error(files, "SOT_PIPELINE_STAGE_MISSING:CLIENT_REVIEW")

    def test_index_and_execution_surfaces_must_link_sot(self):
        for key in ("index", "skill", "prompt_contract", "golden_reference"):
            with self.subTest(key=key):
                files = valid_files()
                files[key] = "unrelated"
                self.assert_error(files, f"SOT_LINK_MISSING:{key}")

    def test_legacy_contract_cannot_claim_publication(self):
        files = valid_files()
        legacy = json.loads(files["legacy_contract"])
        legacy["runtime_status"]["publication_allowed"] = True
        files["legacy_contract"] = json.dumps(legacy)
        self.assert_error(files, "LEGACY_PUBLICATION_NOT_BLOCKED")

    def test_fixed_mutation_count_is_rejected(self):
        files = valid_files()
        files["verification"] = "62개 단위 계약·mutation 25종"
        self.assert_error(files, "VERIFICATION_COUNT_DRIFT_RISK")

    def test_repository_bundle_is_complete(self):
        self.assertEqual(sot_gate.audit_paths(ROOT), [])

    def test_missing_repository_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = sot_gate.audit_paths(Path(directory))
        self.assertTrue(errors)
        self.assertIn("FILE_MISSING:docs/sot/weekly-ops-contract.md", errors)


if __name__ == "__main__":
    unittest.main()
