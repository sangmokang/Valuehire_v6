"""LLM 위키 필드 채움률 감사기 (RED 뼈대)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FieldStat:
    table: str
    column: str
    total: int | None
    nulls: int | None
    error: str | None = None


@dataclass
class Verdict:
    status: str = "PASS"
    failures: list[str] = field(default_factory=list)


def parse_thresholds(markdown: str) -> dict[tuple[str, str], float]:
    return {}


def judge(stats: list[FieldStat], thresholds: dict[tuple[str, str], float]) -> Verdict:
    return Verdict()
