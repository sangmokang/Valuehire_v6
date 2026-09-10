"""HS-13.06 — 후보 채점 순수 함수와 학교 계층 계약 로더 (골격, RED)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .types_candidate import CandidateEvidence, ScoreBreakdown

__all__ = [
    "SchoolTiers",
    "load_school_tiers",
    "resolve_school_tier",
    "score_candidate",
]


@dataclass(frozen=True)
class SchoolTiers:
    """계약 파일에서 읽은 학교 서열. 정식명→tier 와 별칭→정식명."""

    by_name: Mapping[str, int]
    aliases: Mapping[str, str]


def load_school_tiers(path: Path) -> SchoolTiers:
    """학교 계층 계약 파일을 읽어 검증한다."""

    raise NotImplementedError("HS-13.06 GREEN 에서 구현한다")


def resolve_school_tier(name: str | None, tiers: SchoolTiers) -> int | None:
    """학교 이름을 정확 일치로 tier 에 대응시킨다. 없으면 None."""

    raise NotImplementedError("HS-13.06 GREEN 에서 구현한다")


def score_candidate(ev: CandidateEvidence) -> ScoreBreakdown:
    """§7 D6 4축(40/20/20/20)으로 후보를 채점한다."""

    raise NotImplementedError("HS-13.06 GREEN 에서 구현한다")
