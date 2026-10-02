"""jd_channels 회귀 테스트.

fixture 로 표시한 가상 JD 는 후보자용 실제 공고가 아니다. 실제 공고는
outputs/_units/ 의 정의만이며, 여기서는 읽기만 한다.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jd_channels.checks import (  # noqa: E402
    inmail_structure, inmail_tone, scan, scan_inmail,
)
from jd_channels.measure import (  # noqa: E402
    PORTAL_SAFE_SUBSTITUTE, measure, normalize_for_compare, scan_portal_risk,
)
from jd_channels.pipeline import run, verify  # noqa: E402
from jd_channels.render import render  # noqa: E402
from jd_channels.units import UnitError, load  # noqa: E402

REAL_UNITS = ROOT / "outputs/_units/bunjang__core-product-pm.json"


def unit(uid, section, kind, full, compact=None, **kw):
    return {"id": uid, "section": section, "kind": kind,
            "meaning": f"fixture {uid}", "full": full,
            "compact": compact if compact is not None else full,
            "source": "FIXTURE", **kw}


def doc(units, **kw):
    base = {"company": "픽스처컴퍼니", "position": "Fixture Engineer",
            "source_url": "fixture://none", "captured_at": "2026-01-01T00:00:00+00:00",
            "source_status": "FIXTURE", "jd_id": "FIXTURE",
            "company_slug": "fixture", "position_slug": "engineer", "units": units}
    base.update(kw)
    return base


def write(tmp, payload):
    p = Path(tmp) / "units.json"
    p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return p


class GoldenShapeTest(unittest.TestCase):
    """번개장터형 — 팀·도메인·업무·평가 기준 구조가 긴 JD."""

    @classmethod
    def setUpClass(cls):
        cls.src = load(REAL_UNITS)

    def test_all_channels_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports = run(REAL_UNITS, tmp)
        self.assertEqual([r.channel for r in reports],
                         ["gmail", "linkedin_rps", "saramin", "jobkorea"])
        for r in reports:
            with self.subTest(channel=r.channel):
                self.assertEqual(r.status, "READY_DRAFT")
                self.assertEqual(r.missing_core, ())
                self.assertEqual(r.banned, ())
                self.assertEqual(r.notes, ())

    def test_three_work_axes_survive_compression(self):
        body = render(self.src, "linkedin_rps").body
        for axis in ("기능 기획·출시", "시스템 구조", "비즈니스 로직"):
            self.assertIn(axis, body, f"압축본에서 업무 축 누락: {axis}")

    def test_three_qualification_axes_survive(self):
        body = render(self.src, "linkedin_rps").body
        for axis in ("Outcome", "MVP", "정합성·일관성·재현성"):
            self.assertIn(axis, body, f"압축본에서 자격 축 누락: {axis}")

    def test_evaluation_priority_notes_survive(self):
        """원문 Note 의 평가 우선순위는 축약본에서도 남는다."""
        body = normalize_for_compare(render(self.src, "linkedin_rps").body)
        self.assertIn(normalize_for_compare("중고거래 경력 자체보다"), body)
        self.assertIn(normalize_for_compare("요청 실행보다"), body)

    def test_no_direct_apply_path(self):
        """회사 직접 지원 경로는 어느 채널에도 남지 않는다."""
        for channel in ("gmail", "linkedin_rps", "saramin", "jobkorea"):
            text = render(self.src, channel).full_text
            self.assertNotIn("join@bunjang.co.kr", text)
            self.assertNotIn("@", text.replace("valuehire.cc", ""))

    def test_rps_within_limit_and_keeps_company(self):
        draft = render(self.src, "linkedin_rps")
        self.assertLessEqual(draft.measured.codepoints, 1900)
        self.assertIn("Series E", draft.body, "한도에 여유가 있는데 회사 정보를 버렸다")

    def test_gmail_is_longer_than_rps(self):
        """Gmail 을 RPS 수준으로 줄이지 않는다."""
        self.assertGreater(render(self.src, "gmail").measured.codepoints,
                           render(self.src, "linkedin_rps").measured.codepoints * 1.3)


class TechJDTest(unittest.TestCase):
    """기술직형 — 예시 기술과 필수 기술이 구분된 JD."""

    def test_example_stack_not_promoted_to_required(self):
        units = [
            unit("Q1", "requirements", "core", "- Python 3년 이상"),
            unit("P1", "preferred", "core", "- 예: Airflow, dbt 사용 경험"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            src = load(write(tmp, doc(units)))
            draft = render(src, "gmail")
        req_at = draft.body.index("[자격요건]")
        pref_at = draft.body.index("[우대사항]")
        self.assertLess(req_at, pref_at)
        self.assertIn("예: Airflow", draft.body[pref_at:])
        self.assertNotIn("Airflow", draft.body[req_at:pref_at])


class ConditionJDTest(unittest.TestCase):
    """조건형 — '또는 이에 준하는 경험', 고용형태 예외."""

    def test_alternative_clause_preserved_in_compact(self):
        full = "- FP&A 5년 이상 수행하신 분(또는 이에 준하는 경험)"
        units = [unit("Q1", "requirements", "core", full,
                      "- FP&A 5년 이상(또는 이에 준하는 경험)")]
        with tempfile.TemporaryDirectory() as tmp:
            src = load(write(tmp, doc(units)))
            for channel in ("gmail", "linkedin_rps"):
                body = render(src, channel).body
                self.assertIn("또는 이에 준하는 경험", body,
                              f"{channel}: 대체 인정 조건이 사라졌다")

    def test_employment_exception_preserved(self):
        units = [unit("N1", "conditions", "core",
                      "- 정규직(상호 합의 시 계약직 전환 가능)",
                      "- 정규직(상호 합의 시 계약직 가능)")]
        with tempfile.TemporaryDirectory() as tmp:
            src = load(write(tmp, doc(units)))
            self.assertIn("상호 합의", render(src, "linkedin_rps").body)


class ErrorPathTest(unittest.TestCase):
    """오류형 — 정의 위반, 글자 수 초과, 금지 문구."""

    def test_compact_longer_than_full_is_rejected(self):
        units = [unit("Q1", "requirements", "core", "- 짧음", "- 이것은 훨씬 더 긴 압축본이다")]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(UnitError):
                load(write(tmp, doc(units)))

    def test_core_cannot_be_dropped(self):
        units = [unit("Q1", "requirements", "core", "- 필수", drop_rank=2)]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(UnitError):
                load(write(tmp, doc(units)))

    def test_zero_units_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(UnitError):
                load(write(tmp, doc([])))

    def test_over_limit_becomes_needs_length_decision(self):
        """core 만으로 한도를 넘으면 누락을 숨기지 않고 상태로 드러낸다."""
        units = [unit(f"Q{i}", "requirements", "core", "- " + "가" * 200)
                 for i in range(20)]
        with tempfile.TemporaryDirectory() as tmp:
            src = load(write(tmp, doc(units)))
            draft = render(src, "linkedin_rps")
        self.assertEqual(draft.status, "NEEDS_LENGTH_DECISION")
        self.assertGreater(draft.measured.codepoints, 1900)
        self.assertEqual(draft.dropped_units, (), "core 를 버려서 한도를 맞추면 안 된다")

    def test_banned_internal_sentence_is_caught(self):
        units = [unit("C1", "company", "company",
                      "- 인원: 192명(국민연금 기반으로 현재와 동일하다고 단정하지 않습니다)")]
        with tempfile.TemporaryDirectory() as tmp:
            src = load(write(tmp, doc(units + [unit("Q1", "requirements", "core", "- 경력 2년")])))
            report = verify(src, render(src, "gmail"))
        self.assertIn("PENSION_SOURCE", report.banned)
        self.assertIn("SELF_HEDGE_ASSERT", report.banned)
        self.assertFalse(report.ok)

    def test_invisible_character_is_flagged(self):
        m = measure("한도​우회")
        self.assertFalse(m.clean)

    def test_portal_transform_is_detected(self):
        """포털이 저장하면서 바꾸는 문자를 쓰기 전에 잡는다(2026-09-21·22 실측)."""
        jk = "크랙(일본 '캬라푸') 정의\u2013수집"
        hits = scan_portal_risk(jk, "jobkorea")
        self.assertIn("'", hits, "잡코리아: 작은따옴표→백틱 치환을 못 잡았다")
        self.assertIn("\u2013", hits, "잡코리아: en dash→물음표를 못 잡았다")

        sr = "서류 전형 \u2192 실무 인터뷰 \u2192 컬처핏"
        hits = scan_portal_risk(sr, "saramin")
        self.assertIn("\u2192", hits, "사람인: 화살표 삭제를 못 잡았다")
        self.assertEqual(hits["\u2192"][0], 2)

    def test_portal_risk_is_per_portal(self):
        """포털마다 바꾸는 문자가 다르다 — 한쪽 규칙을 다른 쪽에 적용하지 않는다."""
        self.assertEqual(scan_portal_risk("서류 \u2192 면접", "jobkorea"), {})
        self.assertEqual(scan_portal_risk("'캬라푸'", "saramin"), {})

    def test_safe_substitutes_clear_the_scan(self):
        """권장 대체 표기로 바꾸면 경고가 사라지고 단어는 남는다."""
        for portal, text in (("jobkorea", "'캬라푸' 정의\u2013수집"),
                             ("saramin", "서류 \u2192 면접")):
            fixed = text
            for bad, good in PORTAL_SAFE_SUBSTITUTE.items():
                fixed = fixed.replace(bad, good)
            self.assertEqual(scan_portal_risk(fixed, portal), {}, portal)
            self.assertIn("캬라푸" if portal == "jobkorea" else "면접", fixed)

    def test_real_drafts_are_portal_safe(self):
        """실제 산출 원고가 각 포털에서 안전한지 확인한다."""
        src = load(REAL_UNITS)
        for portal, channel in (("jobkorea", "jobkorea"), ("saramin", "saramin")):
            body = render(src, channel).body
            hits = scan_portal_risk(body, portal)
            self.assertEqual(hits, {}, f"{portal} 원고에 변환 위험 문자: {hits}")

    def test_inmail_rejects_ai_tells(self):
        """사람이 쓰지 않는 문구는 계속 잡는다. 서식(볼드·■·•)은 금지 대상이 아니다."""
        bad = ("안녕하세요 전혜인 매니저님\n\n귀하의 경력을 주목하여 연락드립니다 \U0001F642\n"
               "{{first_name}}님께 좋은 기회가 될 것입니다")
        rules = {h.rule for h in scan_inmail(bad)}
        for want in ("INMAIL_NAME_HARDCODED", "INMAIL_STOCK_PHRASE",
                     "INMAIL_EMOJI", "INMAIL_RAW_VAR"):
            self.assertIn(want, rules, f"{want} 를 못 잡았다")

    def test_inmail_formatting_is_not_banned(self):
        """2026-09-22 오전 회귀 방지 — 골든의 서식을 금지 규칙으로 잡으면 안 된다."""
        for name in ("rps_wrtn_golden.txt", "rps_bunjang_golden.txt"):
            text = (ROOT / "outputs/_golden" / name).read_text(encoding="utf-8").strip()
            with self.subTest(golden=name):
                self.assertEqual(scan_inmail(text), [], "골든 샘플이 금지 규칙에 걸렸다")
                self.assertEqual(inmail_structure(text), [], "골든 샘플이 구조 검사에 걸렸다")
                self.assertGreater(inmail_tone(text)["bullet_ratio"], 0.3,
                                   "골든은 불릿 비율이 0.44~0.46 이다")

    def test_inmail_structure_catches_prose_only_draft(self):
        """음성 대조군 — 불릿·섹션 없는 산문 원고는 구조 검사에서 걸린다."""
        prose = (ROOT / "outputs/run-20260921/wrtn__finance-data-analyst__199492"
                        "/linkedin_rps_inmail.txt")
        if not prose.exists():
            self.skipTest("산문판 없음")
        rules = {h.rule for h in inmail_structure(prose.read_text(encoding="utf-8"))}
        self.assertIn("INMAIL_NO_SECTION", rules)
        self.assertIn("INMAIL_NO_BULLET", rules)

    def test_inmail_structure_mutation_is_detected(self):
        """R2 — 골든에서 한 요소씩 고장 내면 그 규칙만 뜬다(검사기가 살아 있는지)."""
        golden = (ROOT / "outputs/_golden/rps_wrtn_golden.txt").read_text(
            encoding="utf-8").strip()
        cases = (
            ("INMAIL_NO_SECTION", golden.replace("■ ", "")),
            ("INMAIL_NO_POSITION_HEADER", golden.replace("■ Position | ", "Position | ")),
            ("INMAIL_NO_BULLET", golden.replace("• ", "")),
            ("INMAIL_NO_BOLD", golden.replace("**", "")),
            ("INMAIL_SIGNATURE", golden.replace("테크 전문 서치펌", "서치펌")),
            ("INMAIL_NEGATIVE_METRIC", golden + "\n영업손실 588억원"),
            ("INMAIL_TERM_TRANSLATED", golden.replace("Reference Check", "평판 조회")),
            ("INMAIL_CLOSING", golden.replace("LinkedIn 수락 또는 간단한 회신만 주셔도",
                                              "이력서를 보내주시면")),
            ("INMAIL_TOO_LONG", golden + "가" * 1900),
        )
        for rule, mutated in cases:
            with self.subTest(rule=rule):
                self.assertIn(rule, {h.rule for h in inmail_structure(mutated)},
                              f"{rule} 변이가 살아남았다")

    def test_inmail_good_body_passes(self):
        """생성 원고는 금지 0건·구조 0건이고 골든과 같은 불릿 밀도를 갖는다."""
        for name in ("wrtn__finance-data-analyst", "bunjang__core-product-pm"):
            with self.subTest(jd=name):
                body = render(load(ROOT / f"outputs/_units/{name}.json"),
                              "linkedin_rps").body
                self.assertEqual(scan_inmail(body), [], "생성 원고에 금지 항목이 있다")
                self.assertEqual(inmail_structure(body), [], "생성 원고가 골든 구조를 벗어났다")
                tone = inmail_tone(body)
                self.assertEqual(tone["bullet_verdict"], "ok",
                                 f"불릿 비율 {tone['bullet_ratio']} — 조건이 산문에 묻혔다")

    def test_inmail_length_within_hard_cap(self):
        """제목+빈 줄+본문 합계가 1,899자를 넘지 않는다(SOT L1)."""
        for name in ("wrtn__finance-data-analyst", "bunjang__core-product-pm"):
            with self.subTest(jd=name):
                draft = render(load(ROOT / f"outputs/_units/{name}.json"), "linkedin_rps")
                self.assertLessEqual(draft.measured.codepoints, 1899)
                self.assertEqual(draft.status, "READY_DRAFT")

    def test_inmail_keeps_core_conditions(self):
        """축약해도 핵심 조건은 남는다(SOT L2·L3). 골든 기준 영문 용어도 보존한다."""
        must = {
            "wrtn__finance-data-analyst": (
                "5년", "또는 이에 준하는 경험", "정규직", "수습 3개월",
                "Reference Check", "Culture Fit", "Offer"),
            "bunjang__core-product-pm": (
                "2년", "정규직", "수습 3개월", "Outcome", "MVP", "Cross-functional"),
        }
        for name, needles in must.items():
            body = render(load(ROOT / f"outputs/_units/{name}.json"), "linkedin_rps").body
            for needle in needles:
                with self.subTest(jd=name, needle=needle):
                    self.assertIn(needle, body, f"핵심 조건 누락: {needle}")

    def test_inmail_drops_negative_metrics_but_keeps_growth(self):
        """G7 — 영업손실·인원은 빼고 매출·투자·사용자 규모는 남긴다."""
        wrtn = render(load(ROOT / "outputs/_units/wrtn__finance-data-analyst.json"),
                      "linkedin_rps").body
        self.assertNotIn("영업손실", wrtn)
        self.assertIn("471억원", wrtn, "매출까지 같이 버렸다")
        bunjang = render(load(ROOT / "outputs/_units/bunjang__core-product-pm.json"),
                         "linkedin_rps").body
        self.assertNotIn("영업손실", bunjang)
        self.assertNotIn("192명", bunjang)
        self.assertIn("Series E", bunjang, "투자 정보까지 같이 버렸다")

    def test_inmail_core_units_are_never_dropped(self):
        """rps_drop 은 core 에 쓸 수 없다 — 채널이 달라도 core 삭제 금지는 같다."""
        units = [unit("Q1", "requirements", "core", "- 필수", rps_drop=True)]
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(UnitError):
                load(write(tmp, doc(units)))
        for name in ("wrtn__finance-data-analyst", "bunjang__core-product-pm"):
            src = load(ROOT / f"outputs/_units/{name}.json")
            dropped = set(render(src, "linkedin_rps").dropped_units)
            core = {u.id for u in src.units if u.kind == "core"}
            self.assertEqual(dropped & core, set(), f"{name}: core 단위가 생략됐다")

    def test_legit_conditions_are_not_flagged(self):
        legit = ("- 전형 절차는 일정 및 상황에 따라 일부 추가/생략될 수 있습니다.\n"
                 "- 입사지원서 기재사항이 사실과 다를 경우 합격이 취소될 수 있습니다.\n"
                 "- 국가유공자 및 장애인 등 취업보호대상자는 관계법령에 따라 우대합니다.")
        self.assertEqual(scan(legit), [], "원문 조건 문구를 금지 문구로 오탐했다")


if __name__ == "__main__":
    unittest.main(verbosity=2)
