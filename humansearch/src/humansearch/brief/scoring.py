"""HS-13.06 — 후보 채점 순수 함수와 학교 계층 계약 로더.

§7 D6: 4축(직무 40 · 학력 20 · 재직 안정성 20 · 프로필 충실도 20). 학교 서열은
`contracts/humansearch/schools-tier.json` 계약에만 있고 코드에는 없다(P22).
목록에 없는 학교는 tier 4 가 아니라 **미확인**이며 학력 0점이다(추정 금지).

순수성 계약: 시계·네트워크 접근 0. 파일은 `load_school_tiers` 하나만 읽는다.
반올림은 `Decimal` + `ROUND_HALF_UP` 로 고정한다 — 내장 `round()` 의 짝수 반올림은
같은 입력에 대해 사람이 계산한 값과 어긋나므로 쓰지 않는다.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import cast

from .types import _reject
from .types_candidate import CandidateEvidence, ScoreBreakdown

__all__ = [
    "SchoolTiers",
    "load_school_tiers",
    "resolve_school_tier",
    "score_candidate",
]

_TIER_KEYS = ("1", "2", "3", "4")
_ROLE_CAP = 40
_PROFILE_CAP = 20
_EDUCATION_POINTS: Mapping[int | None, int] = {None: 0, 1: 20, 2: 15, 3: 10, 4: 5}
_STABILITY_THRESHOLDS = ((36, 20), (24, 15), (12, 10))
_STABILITY_FLOOR = 5
_JOB_HOP_LIMIT = 3
_JOB_HOP_PENALTY = 5
_PARENTHESIS = re.compile(r"[(\[]([^()\[\]]*)[)\]]")


@dataclass(frozen=True)
class SchoolTiers:
    """계약 파일에서 읽은 학교 서열. 정식명→tier 와 별칭→정식명."""

    by_name: Mapping[str, int]
    aliases: Mapping[str, str]


def _normalize(value: str) -> str:
    """NFKC 정규화 + 앞뒤·중복 공백 정리. 표기 차이만 흡수하고 이름은 바꾸지 않는다."""

    return " ".join(unicodedata.normalize("NFKC", value).split())


def _name_candidates(normalized: str) -> tuple[str, ...]:
    """괄호 병기를 분해한다: "연세대학교(Yonsei University)" → 원문·앞부분·괄호 안."""

    candidates = [normalized]
    inner = [match.group(1).strip() for match in _PARENTHESIS.finditer(normalized)]
    outer = " ".join(_PARENTHESIS.sub(" ", normalized).split())
    candidates.append(outer)
    candidates.extend(inner)
    seen: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.append(candidate)
    return tuple(seen)


def _read_contract(path: Path) -> dict[str, object]:
    """계약 파일을 읽어 최상위 객체를 돌려준다. 읽기·파싱 실패는 전부 거부다."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        _reject(f"학교 계층 계약 파일을 읽지 못했다: {path.name} ({type(error).__name__})")
    try:
        raw: object = json.loads(text)
    except json.JSONDecodeError as error:
        _reject(f"학교 계층 계약 파일이 JSON 이 아니다: {path.name} ({error.msg})")
    if not isinstance(raw, dict):
        _reject("학교 계층 계약의 최상위는 객체여야 한다")
    return cast(dict[str, object], raw)


def _require_version(root: dict[str, object]) -> None:
    version = root.get("version")
    if isinstance(version, bool) or version != 1:
        _reject(f"학교 계층 계약의 version 은 1 이어야 한다: {version!r}")
    note = root.get("source_note")
    if not isinstance(note, str) or not note.strip():
        _reject("학교 계층 계약에 source_note 가 없다(출처·갱신 근거 없는 계약은 거부)")


def _tier_table(root: dict[str, object]) -> dict[str, int]:
    """tiers 절을 정식명→tier 표로 편다. 키는 "1"~"4", 학교 중복은 거부."""

    tiers_raw = root.get("tiers")
    if not isinstance(tiers_raw, dict):
        _reject("학교 계층 계약의 tiers 는 객체여야 한다")
    by_name: dict[str, int] = {}
    for key, value in cast(dict[str, object], tiers_raw).items():
        if key not in _TIER_KEYS:
            _reject(f'학교 계층 계약의 tiers 키는 "1"~"4" 여야 한다: {key!r}')
        if not isinstance(value, list):
            _reject(f"학교 계층 계약의 tiers[{key!r}] 는 배열이어야 한다")
        for item in cast(list[object], value):
            if not isinstance(item, str) or not item.strip():
                _reject(f"학교 계층 계약의 tiers[{key!r}] 에 빈 학교 이름이 있다")
            name = _normalize(item)
            if name in by_name:
                _reject(f"같은 학교가 두 tier 에 있다: {name}")
            by_name[name] = int(key)
    if not by_name:
        _reject("학교 계층 계약에 학교가 한 곳도 없다(빈 계약은 검사 무효)")
    return by_name


def _alias_table(root: dict[str, object], by_name: Mapping[str, int]) -> dict[str, str]:
    """aliases 절을 별칭→정식명 표로 편다. 목록 밖 대상·중복 별칭은 거부."""

    aliases_raw = root.get("aliases", {})
    if not isinstance(aliases_raw, dict):
        _reject("학교 계층 계약의 aliases 는 객체여야 한다")
    aliases: dict[str, str] = {}
    for alias, target in cast(dict[str, object], aliases_raw).items():
        if not alias.strip():
            _reject("학교 계층 계약의 aliases 에 빈 별칭이 있다")
        if not isinstance(target, str) or not target.strip():
            _reject(f"학교 계층 계약의 aliases[{alias!r}] 대상이 문자열이 아니다")
        key = _normalize(alias)
        official = _normalize(target)
        if official not in by_name:
            _reject(f"alias 대상이 학교 목록에 없다: {alias} → {target}")
        if key in aliases or key in by_name:
            _reject(f"alias 가 정식명이나 다른 별칭과 겹친다: {alias}")
        aliases[key] = official
    return aliases


def load_school_tiers(path: Path) -> SchoolTiers:
    """학교 계층 계약 파일을 읽어 검증한다. 어떤 위반이든 `BriefInputError`."""

    root = _read_contract(path)
    _require_version(root)
    by_name = _tier_table(root)
    return SchoolTiers(by_name=by_name, aliases=_alias_table(root, by_name))


def resolve_school_tier(name: str | None, tiers: SchoolTiers) -> int | None:
    """학교 이름을 **정확 일치**로 tier 에 대응시킨다. 부분 일치·유사도는 쓰지 않는다.

    괄호 병기는 앞부분과 괄호 안을 각각 시도한다. 확인되지 않으면 None(=미확인).
    """

    if name is None:
        return None
    normalized = _normalize(name)
    if not normalized:
        return None
    for candidate in _name_candidates(normalized):
        tier = tiers.by_name.get(candidate)
        if tier is not None:
            return tier
        official = tiers.aliases.get(candidate)
        if official is not None:
            return tiers.by_name.get(official)
    return None


def _round_half_up(numerator: int, denominator: int) -> int:
    """HALF_UP 반올림. 파이썬 내장 `round()` 의 짝수 반올림을 쓰지 않는다."""

    quotient = Decimal(numerator) / Decimal(denominator)
    return int(quotient.quantize(Decimal(0), rounding=ROUND_HALF_UP))


def _stability_points(ev: CandidateEvidence) -> int:
    """재직 기간 평균과 5년 내 이직 횟수로 안정성 점수를 낸다."""

    months = ev.tenure_months_per_job
    if not months:
        points = 0  # 미확인은 0점 — 추정하지 않는다.
    else:
        total = sum(months)
        count = len(months)
        points = _STABILITY_FLOOR
        for threshold, value in _STABILITY_THRESHOLDS:
            if total >= threshold * count:  # 평균 비교를 정수로 — 부동소수 오차 0.
                points = value
                break
    if ev.jobs_last_5y >= _JOB_HOP_LIMIT:
        points -= _JOB_HOP_PENALTY
    return max(points, 0)


def score_candidate(ev: CandidateEvidence) -> ScoreBreakdown:
    """§7 D6 4축(40/20/20/20)으로 후보를 채점한다. 순수·결정적이다.

    tier 는 `ev.school_tier` 를 그대로 쓴다(해석은 `resolve_school_tier` 의 몫).
    분모가 0 인 축은 계산이 성립하지 않으므로 0점이 아니라 거부한다.
    """

    if ev.jd_required_terms_total == 0:
        _reject("CandidateEvidence.jd_required_terms_total 이 0 이다(직무 축을 낼 수 없다)")
    if ev.profile_fields_total == 0:
        _reject("CandidateEvidence.profile_fields_total 이 0 이다(프로필 축을 낼 수 없다)")
    return ScoreBreakdown(
        role=_round_half_up(_ROLE_CAP * ev.jd_required_terms_hit, ev.jd_required_terms_total),
        education=_EDUCATION_POINTS[ev.school_tier],
        stability=_stability_points(ev),
        profile=_round_half_up(_PROFILE_CAP * ev.profile_fields_filled, ev.profile_fields_total),
    )
