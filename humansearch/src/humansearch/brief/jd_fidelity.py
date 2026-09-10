"""HS-13.02 — JD 충실도 판정(골격). 아직 아무것도 판정하지 않는다.

RED 단계 골격이다. 성공을 하드코딩하지 않고 모든 판정 경로가 NotImplementedError 로 멈춘다.
"""

from __future__ import annotations

from dataclasses import dataclass

from .types import JdSource

__all__ = [
    "EXTRA_CONDITION_PATTERNS",
    "FidelityReport",
    "Section",
    "content_lines",
    "normalize_line",
    "split_sections",
    "verify_fidelity",
]

EXTRA_CONDITION_PATTERNS: tuple[str, ...] = ()


@dataclass(frozen=True)
class Section:
    """JD 한 절 — 제목 한 줄과 그 아래 내용 줄들."""

    heading: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class FidelityReport:
    """JD 충실도 판정 결과."""

    missing: tuple[str, ...]
    extra_condition: tuple[str, ...]
    jd_line_count: int
    rendered_line_count: int

    @property
    def ok(self) -> bool:
        raise NotImplementedError("HS-13.02 미구현")


def normalize_line(line: str) -> str:
    raise NotImplementedError("HS-13.02 미구현")


def content_lines(text: str) -> tuple[str, ...]:
    raise NotImplementedError("HS-13.02 미구현")


def split_sections(text: str) -> tuple[Section, ...]:
    raise NotImplementedError("HS-13.02 미구현")


def verify_fidelity(
    jd: JdSource,
    rendered: str,
    *,
    allowed_extra: tuple[str, ...] = (),
) -> FidelityReport:
    raise NotImplementedError("HS-13.02 미구현")
