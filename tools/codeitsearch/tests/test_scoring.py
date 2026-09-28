import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scoring import (  # noqa: E402
    AISEARCH_REGISTER_MIN,
    Candidate,
    SchoolTier,
    company_tenures,
    job_changes,
    load_school_contract,
    school_tier,
    score,
    short_stint_count,
)

CONTRACT = load_school_contract()
REQUIRED = ["백엔드 개발자", "Spring", "Kotlin", "MSA"]
PREFERRED = ["에듀테크", "SaaS"]


def candidate(**overrides):
    base = dict(
        name="테스터",
        profile_url="https://www.saramin.co.kr/zf_user/profile/1",
        school="연세대학교",
        roles=(("A사", 40), ("B사", 30)),
        keyword_hits=("백엔드 개발자", "Spring", "Kotlin", "MSA", "에듀테크", "SaaS"),
    )
    base.update(overrides)
    return Candidate(**base)


class TestSchoolTier:
    @pytest.mark.parametrize(
        "school,expected",
        [
            ("연세대학교", SchoolTier.IN_SEOUL),
            ("서울시립대학교", SchoolTier.IN_SEOUL),
            ("KAIST", SchoolTier.NATIONAL),
            ("Stanford University", SchoolTier.WORLD_TOP),
            ("부산대학교", SchoolTier.OTHER),
            ("영진전문대학", SchoolTier.TWO_YEAR),
            (None, SchoolTier.OTHER),
        ],
    )
    def test_classifies_from_contract(self, school, expected):
        assert school_tier(school, CONTRACT) == expected

    @pytest.mark.parametrize(
        "school",
        [
            "한양대학교 ERICA", "고려대학교 세종캠퍼스", "연세대학교 미래캠퍼스",
            "동국대학교 WISE", "건국대학교 글로컬", "중앙대학교 다빈치",
            "한국외국어대학교 글로벌캠퍼스", "홍익대학교 세종캠퍼스",
        ],
    )
    def test_branch_campuses_are_not_in_seoul(self, school):
        # 본교 어간이 이름에 남아 있어 전부 in_seoul 로 잡히던 실측 결함 (2026-09-28).
        assert school_tier(school, CONTRACT) == SchoolTier.OTHER

    @pytest.mark.parametrize("school", ["세종대학교", "한양대학교", "고려대학교", "연세대학교"])
    def test_main_campuses_stay_in_seoul(self, school):
        # 분교 필터가 본교까지 깎으면 안 된다 — 특히 세종대 vs 세종캠퍼스.
        assert school_tier(school, CONTRACT) == SchoolTier.IN_SEOUL

    @pytest.mark.parametrize(
        "school",
        ["연세대학교 국제캠퍼스", "성균관대학교 자연과학캠퍼스", "고려대학교 세종캠퍼스"],
    )
    def test_any_non_seoul_campus_is_excluded_not_just_listed_ones(self, school):
        # 표지 나열 방식이 국제·자연과학캠퍼스를 놓치던 실측 결함 (codex 2차).
        assert school_tier(school, CONTRACT) == SchoolTier.OTHER

    @pytest.mark.parametrize(
        "school",
        ["연세대학교 신촌캠퍼스", "성균관대학교 인문사회과학캠퍼스", "고려대학교 안암캠퍼스"],
    )
    def test_seoul_campuses_stay_in_seoul(self, school):
        assert school_tier(school, CONTRACT) == SchoolTier.IN_SEOUL

    @pytest.mark.parametrize(
        "school",
        ["Michigan State University", "Toronto Metropolitan University",
         "Columbia College Chicago", "Oxford Brookes University"],
    )
    def test_lookalike_english_names_are_not_world_top(self, school):
        # 'Michigan'·'Toronto'·'Columbia'·'Oxford' 어간 부분일치 실측 결함 (codex 2차).
        assert school_tier(school, CONTRACT) == SchoolTier.OTHER

    @pytest.mark.parametrize(
        "school",
        ["University of Michigan", "University of Toronto", "Columbia University",
         "University of Oxford", "MIT Sloan"],
    )
    def test_the_real_world_top_schools_still_match(self, school):
        assert school_tier(school, CONTRACT) == SchoolTier.WORLD_TOP

    @pytest.mark.parametrize(
        "school,expected",
        [("동서울대학교", SchoolTier.OTHER), ("서울신학대학교", SchoolTier.OTHER),
         ("서울대학교", SchoolTier.IN_SEOUL), ("서울시립대학교", SchoolTier.IN_SEOUL),
         ("서울과학기술대학교", SchoolTier.IN_SEOUL), ("이화여자대학교", SchoolTier.IN_SEOUL)],
    )
    def test_korean_stems_match_only_at_the_start(self, school, expected):
        # 부분일치였을 때 '동서울대' 가 '서울대' 로 잡혔다 (codex 3차).
        assert school_tier(school, CONTRACT) == expected

    def test_a_major_after_the_school_name_does_not_break_matching(self):
        assert school_tier("연세대학교 컴퓨터과학과", CONTRACT) == SchoolTier.IN_SEOUL

    @pytest.mark.parametrize(
        "school",
        ["University of Michigan-Flint", "University of Michigan-Dearborn"],
    )
    def test_satellite_campuses_of_world_top_schools_are_excluded(self, school):
        # 정식 명칭의 연속 부분수열이어도 뒤에 다른 지명이 남으면 다른 학교다 (codex 3차).
        assert school_tier(school, CONTRACT) == SchoolTier.OTHER

    @pytest.mark.parametrize(
        "school", ["MIT Sloan", "Harvard Business School", "The University of Oxford"]
    )
    def test_generic_trailing_words_still_match(self, school):
        assert school_tier(school, CONTRACT) == SchoolTier.WORLD_TOP

    @pytest.mark.parametrize("school", ["Smith College", "Methodist University"])
    def test_short_ascii_acronyms_do_not_substring_match(self, school):
        # MIT -> "Smith", ETH -> "Methodist" 로 world_top 승격되던 실측 결함 (2026-09-28).
        assert school_tier(school, CONTRACT) == SchoolTier.OTHER

    @pytest.mark.parametrize(
        "school,expected",
        [("MIT", SchoolTier.WORLD_TOP), ("ETH Zurich", SchoolTier.WORLD_TOP),
         ("KAIST", SchoolTier.NATIONAL), ("Stanford University", SchoolTier.WORLD_TOP)],
    )
    def test_real_acronyms_still_match(self, school, expected):
        assert school_tier(school, CONTRACT) == expected

    def test_in_seoul_scores_above_other(self):
        in_seoul = score(candidate(school="고려대학교"), required_terms=REQUIRED,
                         preferred_terms=PREFERRED, contract=CONTRACT)
        other = score(candidate(school="부산대학교"), required_terms=REQUIRED,
                      preferred_terms=PREFERRED, contract=CONTRACT)
        assert in_seoul.total > other.total


class TestTenure:
    def test_promotion_within_one_company_is_not_a_job_change(self):
        roles = (("코드잇", 14), ("코드잇", 22), ("이전사", 36))
        assert company_tenures(roles) == [("코드잇", 36), ("이전사", 36)]
        assert job_changes(roles) == 1

    def test_boomerang_counts_unique_employers_not_spans(self):
        # 창립 스펙: job_changes = unique_companies - 1. A -> B -> A 는 2회가 아니라 1회.
        assert job_changes((("A", 20), ("B", 30), ("A", 40))) == 1

    def test_short_stints_exclude_the_current_role(self):
        # 현재 3개월차 — 아직 이직한 것이 아니다.
        assert short_stint_count((("현재사", 3), ("이전사", 40))) == 0
        assert short_stint_count((("현재사", 3), ("A", 8), ("B", 7))) == 2


class TestHardExclude:
    def test_freelancer_is_excluded_and_capped(self):
        verdict = score(candidate(is_freelancer=True), required_terms=REQUIRED,
                        preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason == "freelancer"
        assert verdict.eligible is False
        assert verdict.total <= 49

    def test_two_short_stints_excluded(self):
        verdict = score(candidate(roles=(("현재", 5), ("A", 8), ("B", 6))),
                        required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason == "short_stint_2plus"

    def test_two_year_college_cut_applies_to_saramin_only(self):
        saramin = score(candidate(school="영진전문대학", channel="saramin"),
                        required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        linkedin = score(candidate(school="영진전문대학", channel="linkedin"),
                         required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert saramin.hard_exclude_reason == "two_year_college"
        assert linkedin.hard_exclude_reason is None

    @pytest.mark.parametrize(
        "school,expected",
        [("한국산업기술대학교", SchoolTier.OTHER), ("한국산업대학교", SchoolTier.TWO_YEAR),
         ("영진전문대학", SchoolTier.TWO_YEAR)],
    )
    def test_two_year_markers_do_not_over_match(self, school, expected):
        # '산업대학' 이 정규화로 '산업' 이 되어 한국산업기술대(4년제)를 전문대로 자르던 실측 결함.
        assert school_tier(school, CONTRACT) == expected

    @pytest.mark.parametrize(
        "school,expected",
        [("서울대학교 경영전문대학원", SchoolTier.IN_SEOUL),
         ("연세대학교 법학전문대학원", SchoolTier.IN_SEOUL),
         ("KAIST 경영전문대학원", SchoolTier.NATIONAL)],
    )
    def test_professional_graduate_schools_are_not_two_year(self, school, expected):
        # '전문대학원' 안의 '전문대' 에 걸려 서울대 MBA 가 하드제외되던 실측 결함 (2026-09-28).
        assert school_tier(school, CONTRACT) == expected

    @pytest.mark.parametrize("degree", ["산업대학원 석사", "경영전문대학원 석사", "일반대학원 박사"])
    def test_graduate_degrees_are_never_two_year(self, degree):
        # '산업대학원' 이 '산업대학' 표지에 걸려 하드제외되던 실측 결함 (codex 2차).
        verdict = score(candidate(school="부산대학교", degree=degree), required_terms=REQUIRED,
                        preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason is None

    @pytest.mark.parametrize("degree", ["전문학사", "2년제 학사", "Associate Degree"])
    def test_every_two_year_degree_spelling_is_cut(self, degree):
        verdict = score(candidate(school="부산대학교", degree=degree, channel="saramin"),
                        required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason == "two_year_college"

    def test_mba_degree_string_is_not_a_two_year_degree(self):
        verdict = score(candidate(school="서울대학교", degree="경영전문대학원 석사"),
                        required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason is None

    def test_associate_degree_is_cut_even_when_the_school_looks_four_year(self):
        # degree 필드를 아예 안 읽어 전문학사가 통과하던 실측 결함 (2026-09-28).
        verdict = score(candidate(school="부산대학교", degree="전문학사", channel="saramin"),
                        required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason == "two_year_college"

    def test_associate_degree_cut_does_not_apply_to_linkedin(self):
        verdict = score(candidate(school="부산대학교", degree="전문학사", channel="linkedin"),
                        required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason is None

    def test_non_http_profile_url_rejected(self):
        verdict = score(candidate(profile_url="javascript:void(0)"), required_terms=REQUIRED,
                        preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason == "invalid_profile_url"


class TestScore:
    def test_total_is_the_sum_of_the_breakdown(self):
        verdict = score(candidate(), required_terms=REQUIRED, preferred_terms=PREFERRED,
                        contract=CONTRACT)
        assert verdict.total == sum(verdict.breakdown.values())

    def test_total_still_equals_the_breakdown_when_hard_excluded(self):
        # 캡을 total 에만 걸어 내역 합 82 vs 총점 49 로 어긋나던 실측 결함 (2026-09-28).
        verdict = score(candidate(is_freelancer=True), required_terms=REQUIRED,
                        preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.total == sum(verdict.breakdown.values())
        assert verdict.total <= 49

    def test_register_threshold_is_60_not_70(self):
        # aisearch 등록 문턱 60 — humansearch 70과 섞지 않는다 (창립 스펙).
        assert AISEARCH_REGISTER_MIN == 60

    @pytest.mark.parametrize("hits,eligible", [(4, True), (1, False)])
    def test_gate_is_enforced_by_behaviour_not_just_the_constant(self, hits, eligible):
        # 상수만 단언하면 러너가 70으로 바꿔도 테스트가 통과한다. 실제 판정을 본다.
        verdict = score(candidate(school="부산대학교", keyword_hits=tuple(REQUIRED[:hits])),
                        required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.eligible is eligible
        assert (verdict.total >= AISEARCH_REGISTER_MIN) is eligible

    def test_frequent_mover_scores_below_a_stable_peer(self):
        stable = score(candidate(roles=(("A", 40), ("B", 40))), required_terms=REQUIRED,
                       preferred_terms=PREFERRED, contract=CONTRACT)
        mover = score(candidate(roles=(("A", 20), ("B", 25), ("C", 26), ("D", 30))),
                      required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert mover.total < stable.total

    def test_triage_puts_in_seoul_otw_first(self):
        first = score(candidate(school="서울대학교", open_to_work=True), required_terms=REQUIRED,
                      preferred_terms=PREFERRED, contract=CONTRACT)
        later = score(candidate(school="부산대학교", open_to_work=False,
                                roles=(("A", 30), ("B", 30))),
                      required_terms=REQUIRED, preferred_terms=PREFERRED, contract=CONTRACT)
        assert first.triage_tier < later.triage_tier

    def test_no_keyword_hits_falls_below_the_gate(self):
        verdict = score(candidate(keyword_hits=()), required_terms=REQUIRED,
                        preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.eligible is False
        assert verdict.grade == "below"
