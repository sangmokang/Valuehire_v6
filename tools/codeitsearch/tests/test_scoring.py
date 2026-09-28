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

    def test_non_http_profile_url_rejected(self):
        verdict = score(candidate(profile_url="javascript:void(0)"), required_terms=REQUIRED,
                        preferred_terms=PREFERRED, contract=CONTRACT)
        assert verdict.hard_exclude_reason == "invalid_profile_url"


class TestScore:
    def test_total_is_the_sum_of_the_breakdown(self):
        verdict = score(candidate(), required_terms=REQUIRED, preferred_terms=PREFERRED,
                        contract=CONTRACT)
        assert verdict.total == sum(verdict.breakdown.values())

    def test_register_threshold_is_60_not_70(self):
        # aisearch 등록 문턱 60 — humansearch 70과 섞지 않는다 (창립 스펙).
        assert AISEARCH_REGISTER_MIN == 60

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
