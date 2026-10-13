"""HS-13.06 — 후보 채점이 순수·결정적이고, 학교 계층이 계약 파일에서만 오는지 확인한다.

§7 D6(4축 40/20/20/20 · 학교 서열은 계약 파일 · 추정 금지)과 §11 변이 ③을 정조준한다.
fixture 의 사람 이름·학교 이름은 전부 합성이며, 실제 후보자 정보는 0건이다.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from humansearch.brief import BriefInputError, CandidateEvidence, ScoreBreakdown
from humansearch.brief import scoring as scoring_module
from humansearch.brief.scoring import (
    SchoolTiers,
    load_school_tiers,
    resolve_school_tier,
    score_candidate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "contracts" / "humansearch" / "schools-tier.json"


def _ev(**overrides: Any) -> CandidateEvidence:
    """합성 근거 하나. 기본값은 모든 축이 중간값인 후보다."""

    fields: dict[str, Any] = {
        "role_match_terms": ("검색", "랭킹"),
        "jd_required_terms_hit": 5,
        "jd_required_terms_total": 10,
        "highest_education": "학사",
        "school_tier": None,
        "tenure_months_per_job": (40, 44),
        "jobs_last_5y": 1,
        "profile_fields_filled": 5,
        "profile_fields_total": 10,
    }
    fields.update(overrides)
    return CandidateEvidence(**fields)


@st.composite
def _evidence(draw: st.DrawFn) -> CandidateEvidence:
    """타입 제약(hit ≤ total, filled ≤ total)을 지키는 임의 근거."""

    role_total = draw(st.integers(min_value=1, max_value=60))
    profile_total = draw(st.integers(min_value=1, max_value=60))
    return CandidateEvidence(
        role_match_terms=(),
        jd_required_terms_hit=draw(st.integers(min_value=0, max_value=role_total)),
        jd_required_terms_total=role_total,
        highest_education=None,
        school_tier=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=4))),
        tenure_months_per_job=draw(
            st.lists(st.integers(min_value=0, max_value=600), max_size=8).map(tuple)
        ),
        jobs_last_5y=draw(st.integers(min_value=0, max_value=12)),
        profile_fields_filled=draw(st.integers(min_value=0, max_value=profile_total)),
        profile_fields_total=profile_total,
    )


def _payload(**overrides: Any) -> dict[str, Any]:
    """합성 학교 계층 계약. 실제 계약 파일과 같은 형식이다."""

    payload: dict[str, Any] = {
        "version": 1,
        "source_note": "시험용 합성 목록 — 실제 학교가 아니다",
        "tiers": {"1": ["가나대학교"], "2": ["다라대학교"], "3": [], "4": []},
        "aliases": {"Ganada University": "가나대학교"},
    }
    payload.update(overrides)
    return payload


def _write(tmp_path: Path, payload: object) -> Path:
    target = tmp_path / "schools-tier.json"
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return target


@pytest.fixture(scope="module")
def tiers() -> SchoolTiers:
    return load_school_tiers(CONTRACT_PATH)


# ── 결정성 ────────────────────────────────────────────────────────────────────


def test_same_input_scores_identically_across_100_runs() -> None:
    digests = {
        hashlib.sha256(repr(score_candidate(_ev())).encode("utf-8")).hexdigest() for _ in range(100)
    }
    assert len(digests) == 1


def test_scoring_module_touches_no_clock_network_and_reads_one_file() -> None:
    module_file = scoring_module.__file__
    assert module_file is not None
    source = Path(module_file).read_text(encoding="utf-8")
    for banned in ("import socket", "import urllib", "import requests", "datetime", "time("):
        assert banned not in source, f"{banned} 이 채점 모듈에 있다(시계·네트워크 0 위반)"
    assert source.count("read_text") == 1, "파일 읽기는 load_school_tiers 한 곳뿐이어야 한다"


# ── 축 상한·합계 ──────────────────────────────────────────────────────────────


@given(_evidence())
def test_every_axis_stays_within_its_cap(ev: CandidateEvidence) -> None:
    score = score_candidate(ev)
    assert 0 <= score.role <= 40
    assert 0 <= score.education <= 20
    assert 0 <= score.stability <= 20
    assert 0 <= score.profile <= 20
    assert score.total == score.role + score.education + score.stability + score.profile
    assert 0 <= score.total <= 100
    assert isinstance(score, ScoreBreakdown)


def test_total_boundaries_reach_zero_and_one_hundred() -> None:
    floor = score_candidate(
        _ev(
            jd_required_terms_hit=0,
            school_tier=None,
            tenure_months_per_job=(),
            jobs_last_5y=4,
            profile_fields_filled=0,
        )
    )
    assert floor.total == 0
    ceiling = score_candidate(
        _ev(
            jd_required_terms_hit=10,
            school_tier=1,
            tenure_months_per_job=(48, 60),
            jobs_last_5y=1,
            profile_fields_filled=10,
        )
    )
    assert ceiling.total == 100


# ── 학력 ──────────────────────────────────────────────────────────────────────


def test_unknown_school_tier_scores_zero_education() -> None:
    assert score_candidate(_ev(school_tier=None)).education == 0


@pytest.mark.parametrize(("tier", "expected"), [(1, 20), (2, 15), (3, 10), (4, 5)])
def test_school_tier_maps_to_fixed_education_points(tier: int, expected: int) -> None:
    assert score_candidate(_ev(school_tier=tier)).education == expected


# ── 재직 안정성 ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("tenures", "expected"),
    [
        ((36, 36), 20),
        ((36,), 20),
        ((35, 36), 15),
        ((24, 24), 15),
        ((23,), 10),
        ((12, 12), 10),
        ((11,), 5),
        ((0,), 5),
    ],
)
def test_stability_thresholds(tenures: tuple[int, ...], expected: int) -> None:
    assert score_candidate(_ev(tenure_months_per_job=tenures, jobs_last_5y=1)).stability == expected


def test_empty_tenure_list_scores_zero_stability() -> None:
    assert score_candidate(_ev(tenure_months_per_job=(), jobs_last_5y=0)).stability == 0


def test_three_jobs_in_five_years_costs_five_points() -> None:
    assert score_candidate(_ev(tenure_months_per_job=(40,), jobs_last_5y=2)).stability == 20
    assert score_candidate(_ev(tenure_months_per_job=(40,), jobs_last_5y=3)).stability == 15


def test_stability_penalty_never_goes_below_zero() -> None:
    assert score_candidate(_ev(tenure_months_per_job=(), jobs_last_5y=9)).stability == 0


# ── 반올림·거부 ───────────────────────────────────────────────────────────────


def test_role_axis_rejects_zero_required_terms() -> None:
    with pytest.raises(BriefInputError):
        score_candidate(_ev(jd_required_terms_hit=0, jd_required_terms_total=0))


def test_profile_axis_rejects_zero_field_total() -> None:
    with pytest.raises(BriefInputError):
        score_candidate(_ev(profile_fields_filled=0, profile_fields_total=0))


def test_role_rounding_is_half_up_not_bankers() -> None:
    assert score_candidate(_ev(jd_required_terms_hit=1, jd_required_terms_total=8)).role == 5
    # 40 * 9 / 80 = 4.5 — 내장 round() 는 4(짝수 쪽), HALF_UP 은 5.
    assert score_candidate(_ev(jd_required_terms_hit=9, jd_required_terms_total=80)).role == 5
    # 40 * 1 / 16 = 2.5 — 내장 round() 는 2, HALF_UP 은 3.
    assert score_candidate(_ev(jd_required_terms_hit=1, jd_required_terms_total=16)).role == 3


def test_profile_rounding_is_half_up_not_bankers() -> None:
    # 20 * 1 / 8 = 2.5 — 내장 round() 는 2, HALF_UP 은 3.
    assert score_candidate(_ev(profile_fields_filled=1, profile_fields_total=8)).profile == 3
    # 20 * 3 / 8 = 7.5 — 내장 round() 는 8 과 같지만, 20 * 5 / 8 = 12.5 는 12 로 갈린다.
    assert score_candidate(_ev(profile_fields_filled=5, profile_fields_total=8)).profile == 13


# ── 계약 파일 로드 ────────────────────────────────────────────────────────────


def test_real_contract_file_loads(tiers: SchoolTiers) -> None:
    assert tiers.by_name["서울대학교"] == 1
    assert tiers.by_name["성균관대학교"] == 2
    assert tiers.by_name["건국대학교"] == 3
    assert 4 not in set(tiers.by_name.values()), "tier 4 는 비어 있어야 한다(목록 밖 = 미확인)"
    assert tiers.aliases["Yonsei University"] == "연세대학교"


def test_missing_contract_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_school_tiers(tmp_path / "없는파일.json")


def test_non_json_contract_file_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "schools-tier.json"
    target.write_text("이건 JSON 이 아니다", encoding="utf-8")
    with pytest.raises(BriefInputError):
        load_school_tiers(target)


def test_wrong_version_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        load_school_tiers(_write(tmp_path, _payload(version=2)))


def test_same_school_in_two_tiers_is_rejected(tmp_path: Path) -> None:
    payload = _payload(tiers={"1": ["가나대학교"], "2": ["가나대학교"], "3": [], "4": []})
    with pytest.raises(BriefInputError):
        load_school_tiers(_write(tmp_path, payload))


def test_alias_pointing_outside_the_list_is_rejected(tmp_path: Path) -> None:
    payload = _payload(aliases={"Mabar University": "마바대학교"})
    with pytest.raises(BriefInputError):
        load_school_tiers(_write(tmp_path, payload))


def test_tier_key_outside_one_to_four_is_rejected(tmp_path: Path) -> None:
    payload = _payload(tiers={"1": ["가나대학교"], "5": ["다라대학교"]})
    with pytest.raises(BriefInputError):
        load_school_tiers(_write(tmp_path, payload))


def test_missing_source_note_is_rejected(tmp_path: Path) -> None:
    payload = _payload()
    del payload["source_note"]
    with pytest.raises(BriefInputError):
        load_school_tiers(_write(tmp_path, payload))


# ── 학교명 해석 ───────────────────────────────────────────────────────────────


def test_resolve_matches_official_name_exactly(tiers: SchoolTiers) -> None:
    assert resolve_school_tier("서울대학교", tiers) == 1
    assert resolve_school_tier("  연세대학교  ", tiers) == 1


def test_resolve_matches_alias(tiers: SchoolTiers) -> None:
    assert resolve_school_tier("Yonsei University", tiers) == 1
    assert resolve_school_tier("카이스트", tiers) == 1
    assert resolve_school_tier("Sungkyunkwan University", tiers) == 2


def test_resolve_handles_parenthetical_pairing(tiers: SchoolTiers) -> None:
    assert resolve_school_tier("연세대학교(Yonsei University)", tiers) == 1
    assert resolve_school_tier("Seoul National University (서울대학교)", tiers) == 1


def test_resolve_refuses_substring_and_similar_names(tiers: SchoolTiers) -> None:
    assert resolve_school_tier("연세대학교 미래캠퍼스 경영대학원", tiers) is None
    assert resolve_school_tier("서울대학교병원", tiers) is None
    assert resolve_school_tier("성신여자대학교", tiers) is None
    assert resolve_school_tier("가나대학교", tiers) is None


def test_resolve_returns_none_for_missing_name(tiers: SchoolTiers) -> None:
    assert resolve_school_tier(None, tiers) is None
    assert resolve_school_tier("   ", tiers) is None


@given(st.text(max_size=40))
def test_resolve_never_raises_on_arbitrary_text(name: str) -> None:
    synthetic = SchoolTiers(by_name={"가나대학교": 1}, aliases={"Ganada University": "가나대학교"})
    result = resolve_school_tier(name, synthetic)
    assert result is None or result == 1
