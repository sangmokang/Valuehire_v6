"""Hard-exclusion gate and candidate scoring for the ``<company>search`` pipeline.

Inherits the v6 founding spec (``docs/engineering/humansearch-v6-founding-spec-2026-08-07.md``):

* **코드가 총점을 계산한다.** An LLM may supply per-axis evidence, never the total —
  otherwise the score tracks writing quality instead of fit.
* **하드제외**: 프리랜서 / 12개월 미만 단기이직 2회+ / 전문대 (사람인·잡코리아만 학교 컷).
* **이직 횟수는 회사 단위 groupby 후 ``unique_companies - 1``** — a promotion inside one
  company is not a job change. v5 cut its best candidate by counting titles.
* **인서울 가중치**는 계약 데이터(``contracts/humansearch/in-seoul-universities.json``)에서
  읽는다. 코드에 학교명을 하드코딩하지 않는다.
* aisearch 등록 문턱은 **60** (humansearch 70과 다르다 — 섞지 말 것).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = (
    "AISEARCH_REGISTER_MIN",
    "Candidate",
    "Verdict",
    "SchoolTier",
    "company_tenures",
    "job_changes",
    "load_school_contract",
    "school_tier",
    "score",
    "short_stint_count",
)

AISEARCH_REGISTER_MIN = 60
STRONG_MIN = 85

_CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "contracts"
    / "humansearch"
    / "in-seoul-universities.json"
)


@dataclass(frozen=True, slots=True)
class Candidate:
    """One portal profile, already parsed from the listing/detail page."""

    name: str
    profile_url: str
    school: str | None = None
    degree: str | None = None
    #: (company, months) in reverse-chronological order, one entry per *role*.
    roles: tuple[tuple[str, int], ...] = ()
    is_freelancer: bool = False
    open_to_work: bool = False
    keyword_hits: tuple[str, ...] = ()
    channel: str = "saramin"
    raw: dict[str, Any] = field(default_factory=dict, compare=False)


@dataclass(frozen=True, slots=True)
class Verdict:
    eligible: bool
    total: int
    grade: str
    hard_exclude_reason: str | None
    triage_tier: int
    breakdown: dict[str, int]
    notes: tuple[str, ...]


class SchoolTier:
    IN_SEOUL = "in_seoul"
    WORLD_TOP = "world_top"
    NATIONAL = "national"
    OTHER = "other"
    TWO_YEAR = "two_year"


def load_school_contract(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or _CONTRACT_PATH).read_text(encoding="utf-8"))


def _normalize(text: str, contract: dict[str, Any]) -> str:
    """Reduce a school name to a comparable stem.

    Entries are written as ``연세대`` while profiles say ``연세대학교``; stripping the
    long suffixes first and then a trailing ``대`` lands both on ``연세``.
    """
    rules = contract["normalize"]
    out = text
    for token in rules["strip"]:
        out = out.replace(token, "")
    for token in rules.get("trailing_strip", ()):
        if out.endswith(token):
            out = out[: -len(token)]
    return out.casefold() if rules.get("casefold") else out


def _raw(text: str) -> str:
    """Casefolded name with whitespace removed, but suffixes intact.

    Branch-campus markers must be matched here rather than against ``_normalize``:
    normalization strips ``캠퍼스``, which would turn the marker ``세종캠퍼스`` into
    ``세종`` and collide with 세종대 (an in-Seoul university).
    """
    return "".join(text.split()).casefold()


def _is_two_year_name(raw: str, contract: dict[str, Any]) -> bool:
    """Two-year-college markers, with professional graduate schools carved out first.

    ``전문대학원`` (경영/법학/의학) contains ``전문대`` but is a graduate school at a
    four-year university — matching it hard-excluded 서울대 경영전문대학원 MBA holders.
    """
    cut = contract["hard_exclude"]
    residue = raw
    for negative in cut.get("negative_markers", ()):
        residue = residue.replace(_raw(negative), "")
    return any(_raw(marker) in residue for marker in cut["two_year_college_markers"])


def school_tier(school: str | None, contract: dict[str, Any]) -> str:
    """Classify a school string against the contract. Unknown/missing -> OTHER."""
    if not school:
        return SchoolTier.OTHER
    raw = _raw(school)
    normalized = _normalize(school, contract)
    tokens = {token.casefold() for token in re.findall(r"[A-Za-z0-9]+", school)}
    max_len = contract.get("ascii_token_match_max_len", 5)

    def hit(name: str) -> bool:
        if name.isascii():
            folded = "".join(name.split()).casefold()
            return folded in tokens if len(name) <= max_len else folded in raw
        return _normalize(name, contract) in normalized

    # 전문대 표지는 원문 기준으로 본다. 정규화는 '산업대학'을 '산업'으로 줄여
    # '한국산업기술대학교'(4년제)를 전문대로 하드제외했다 (실측 2026-09-28).
    if _is_two_year_name(raw, contract):
        return SchoolTier.TWO_YEAR
    for marker in contract.get("downgrade_markers", {}).get("markers", ()):
        if _normalize(marker, contract) in normalized:
            return SchoolTier.OTHER
    # 분교·이원화 캠퍼스는 본교 어간을 그대로 달고 있어 in_seoul 판정 전에 걸러야 한다.
    for marker in contract.get("branch_campus", {}).get("markers", ()):
        if _raw(marker) in raw:
            return SchoolTier.OTHER
    for name in contract["special_tier"]["world_top"]:
        if hit(name):
            return SchoolTier.WORLD_TOP
    for name in contract["national_tier"]["members"]:
        if hit(name):
            return SchoolTier.NATIONAL
    for name in contract["in_seoul"]:
        if hit(name):
            return SchoolTier.IN_SEOUL
    return SchoolTier.OTHER


def company_tenures(roles: tuple[tuple[str, int], ...]) -> list[tuple[str, int]]:
    """Collapse consecutive roles at the same company into one tenure.

    A promotion (two roles, one employer) must not read as a job change.
    """
    collapsed: list[list[Any]] = []
    for company, months in roles:
        if collapsed and collapsed[-1][0] == company:
            collapsed[-1][1] += months
        else:
            collapsed.append([company, months])
    return [(company, months) for company, months in collapsed]


def job_changes(roles: tuple[tuple[str, int], ...]) -> int:
    """창립 스펙 그대로 ``unique_companies - 1``.

    Counting tenure spans instead would charge a boomerang (A -> B -> A) two job
    changes for two employers.
    """
    companies = {company for company, _ in roles}
    return max(len(companies) - 1, 0)


def short_stint_count(roles: tuple[tuple[str, int], ...], *, threshold_months: int = 12) -> int:
    """Company-level tenures shorter than the threshold, excluding the current role.

    The current role is excluded because someone three months into a new job has not
    yet job-hopped — counting it punishes every recent mover.
    """
    tenures = company_tenures(roles)
    return sum(1 for _, months in tenures[1:] if months < threshold_months)


def _degree_is_two_year(degree: str | None, contract: dict[str, Any]) -> bool:
    """전문학사는 학교명이 4년제로 보여도 전문대 학력이다. degree 필드를 실제로 읽는다."""
    if not degree:
        return False
    return _is_two_year_name(_raw(degree), contract)


def _hard_exclude(candidate: Candidate, tier: str, contract: dict[str, Any]) -> str | None:
    if candidate.is_freelancer:
        return "freelancer"
    if short_stint_count(candidate.roles) >= 2:
        return "short_stint_2plus"
    school_cut = tier == SchoolTier.TWO_YEAR or _degree_is_two_year(candidate.degree, contract)
    if school_cut and candidate.channel in contract["hard_exclude"]["channels"]:
        return "two_year_college"
    if not candidate.profile_url.startswith(("http://", "https://")):
        return "invalid_profile_url"
    return None


def _triage_tier(tier: str, candidate: Candidate) -> int:
    """열람 순서 — 인서울+OTW → 인서울+Non-OTW(2년+) → 그 외+OTW → 그 외+Non-OTW(2년+)."""
    privileged = tier in (SchoolTier.IN_SEOUL, SchoolTier.WORLD_TOP, SchoolTier.NATIONAL)
    tenures = company_tenures(candidate.roles)
    current_months = tenures[0][1] if tenures else 0
    if privileged and candidate.open_to_work:
        return 1
    if privileged and current_months >= 24:
        return 2
    if candidate.open_to_work:
        return 3
    if current_months >= 24:
        return 4
    return 5  # triage_deferred — 버리지 않고 뒤로 민다


_SCHOOL_POINTS = {
    SchoolTier.WORLD_TOP: 25,
    SchoolTier.IN_SEOUL: 22,
    SchoolTier.NATIONAL: 22,
    SchoolTier.OTHER: 10,
    SchoolTier.TWO_YEAR: 0,
}


def score(
    candidate: Candidate,
    *,
    required_terms: list[str],
    preferred_terms: list[str],
    contract: dict[str, Any] | None = None,
) -> Verdict:
    """Compute the whole verdict. Callers never assemble a total themselves."""
    contract = contract or load_school_contract()
    tier = school_tier(candidate.school, contract)
    reason = _hard_exclude(candidate, tier, contract)
    notes: list[str] = []

    hits = {term.casefold() for term in candidate.keyword_hits}
    required_hit = sum(1 for term in required_terms if term.casefold() in hits)
    preferred_hit = sum(1 for term in preferred_terms if term.casefold() in hits)

    # 40 — 직무 적합(핵심 키워드 커버리지)
    keyword_points = (
        round(40 * required_hit / len(required_terms)) if required_terms else 0
    )
    # 25 — 학벌(인서울 가중치, 계약 데이터 기준)
    school_points = _SCHOOL_POINTS[tier]
    # 20 — 재직 안정성: 이직이 잦을수록 감점
    changes = job_changes(candidate.roles)
    stability_points = max(0, 20 - 5 * max(0, changes - 1))
    if changes >= 3:
        notes.append(f"이직 {changes}회 — 재직안정성 감점 {5 * (changes - 1)}점")
    # 15 — 우대 요건
    preferred_points = (
        round(15 * preferred_hit / len(preferred_terms)) if preferred_terms else 0
    )

    breakdown = {
        "keyword_fit_40": keyword_points,
        "school_25": school_points,
        "stability_20": stability_points,
        "preferred_15": preferred_points,
    }
    total = sum(breakdown.values())

    if reason:
        # 게이트 캡을 breakdown 에도 반영한다. total 만 깎으면 메일에 찍히는 점수 내역의
        # 합과 총점이 어긋난다 (실측 82 vs 49, 2026-09-28).
        capped = min(total, 49)
        if capped != total:
            breakdown["hard_exclude_cap"] = capped - total
        total = capped
        notes.append(f"하드제외: {reason}")

    grade = "strong" if total >= STRONG_MIN else "fit" if total >= AISEARCH_REGISTER_MIN else "below"
    eligible = reason is None and total >= AISEARCH_REGISTER_MIN

    return Verdict(
        eligible=eligible,
        total=total,
        grade=grade,
        hard_exclude_reason=reason,
        triage_tier=_triage_tier(tier, candidate),
        breakdown=breakdown,
        notes=tuple(notes),
    )
