import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jd_channels.conditions import missing, required  # noqa: E402
from jd_channels.render import render  # noqa: E402
from jd_channels.units import load  # noqa: E402


def unit(uid, section, kind, full, compact=None, **kw):
    return {
        "id": uid,
        "section": section,
        "kind": kind,
        "meaning": f"fixture {uid}",
        "full": full,
        "compact": compact if compact is not None else full,
        "source": "FIXTURE",
        **kw,
    }


def doc(units):
    return {
        "company": "픽스처컴퍼니",
        "position": "Fixture Engineer",
        "source_url": "fixture://none",
        "captured_at": "2026-01-01T00:00:00+00:00",
        "source_status": "FIXTURE",
        "jd_id": "FIXTURE",
        "company_slug": "fixture",
        "position_slug": "engineer",
        "units": units,
    }


def source(units):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "units.json"
        path.write_text(json.dumps(doc(units), ensure_ascii=False), encoding="utf-8")
        return load(path)


class ConditionValuePreservationTest(unittest.TestCase):
    def setUp(self):
        self.src = source([
            unit("Q1", "requirements", "core",
                 "- FP&A 경력 5년 이상(또는 이에 준하는 경험)",
                 "- FP&A **5년+**(또는 이에 준하는 경험)"),
            unit("N1", "conditions", "core",
                 "- 정규직 / 수습 3개월", "- 정규직 / 수습 3개월"),
            unit("S1", "process", "core",
                 "- 서류 → Culture Fit → Reference Check → Offer",
                 "- 서류 → Culture Fit → Reference Check → Offer"),
        ])
        self.body = render(self.src, "linkedin_rps").body

    def test_existing_fixture_passes(self):
        self.assertEqual(missing(self.src, self.body), [])

    def test_output_only_required_condition_deletion_fails(self):
        body = self.body.replace("**5년+**", "경험").replace("정규직 / ", "")
        notes = missing(self.src, body)
        self.assertIn("연차", notes)
        self.assertIn("고용형태", notes)

    def test_output_only_unsourced_condition_addition_fails(self):
        notes = missing(self.src, self.body + "\n• 계약직 전환 가능")
        self.assertIn("원문에 없는 고용형태: 계약직", notes)

    def test_output_only_year_value_change_fails(self):
        notes = missing(self.src, self.body.replace("**5년+**", "**3년+**"))
        self.assertIn("연차 값 누락: 5년 이상", notes)
        self.assertIn("원문에 없는 연차 값: 3년 이상", notes)

    def test_output_only_year_direction_change_fails(self):
        notes = missing(self.src, self.body.replace("**5년+**", "5년 이하"))
        self.assertIn("연차 값 누락: 5년 이상", notes)
        self.assertIn("원문에 없는 연차 값: 5년 이하", notes)

    def test_output_only_probation_value_change_fails(self):
        notes = missing(self.src, self.body.replace("수습 3개월", "수습 6개월"))
        self.assertIn("수습 기간 누락: 3개월", notes)
        self.assertIn("원문에 없는 수습 기간: 6개월", notes)

    def test_output_only_employment_value_change_fails(self):
        notes = missing(self.src, self.body.replace("정규직", "계약직"))
        self.assertIn("고용형태 값 누락: 정규직", notes)
        self.assertIn("원문에 없는 고용형태: 계약직", notes)

    def test_equivalent_year_expression_is_allowed(self):
        self.assertEqual(missing(self.src, self.body.replace("**5년+**", "5년 이상")), [])

    def test_empty_optional_and_no_source_conditions(self):
        empty = source([unit("Q0", "requirements", "core", "- ", "- ")])
        optional = source([
            unit("R1", "role", "core", "- 데이터를 해석합니다", "- 데이터를 해석합니다"),
            unit("P1", "preferred", "extra", "- 경력 7년 이상이면 우대",
                 "- 경력 7년 이상이면 우대"),
        ])
        no_condition = source([unit("R1", "role", "core", "- 데이터를 해석합니다",
                                    "- 데이터를 해석합니다")])

        self.assertEqual(required(empty), [])
        self.assertEqual(missing(empty, render(empty, "linkedin_rps").body), [])
        self.assertEqual(required(optional), [])
        self.assertEqual(missing(optional, render(optional, "linkedin_rps").body), [])
        self.assertEqual(missing(optional, render(optional, "linkedin_rps").body.replace(
            "경력 7년 이상이면 우대", "우대 조건은 별도 협의")), [])
        self.assertEqual(required(no_condition), [])
        self.assertEqual(missing(no_condition, render(no_condition, "linkedin_rps").body), [])
        self.assertIn("원문에 없는 고용형태: 계약직",
                      missing(no_condition, render(no_condition, "linkedin_rps").body
                              + "\n• 계약직 가능"))
        self.assertIn("원문에 없는 조건: 평판 조회 단계",
                      missing(no_condition, render(no_condition, "linkedin_rps").body
                              + "\n• Reference Check 진행"))
        self.assertIn("원문에 없는 조건: 수습",
                      missing(no_condition, render(no_condition, "linkedin_rps").body
                              + "\n• 수습 기간 적용"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
