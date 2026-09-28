"""Segment a company's career postings and expand each segment into bilingual keywords.

Pure functions only. No network, no clock, no filesystem — the callers own those so
that segmentation stays testable and identical on Windows and macOS.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from keywords import TIERS, terms, tier  # noqa: E402

__all__ = (
    "ExperienceRange",
    "UNSEGMENTED",
    "expand_keywords",
    "is_searchable",
    "parse_experience",
    "segment_of",
    "segment_positions",
)

UNSEGMENTED = "unsegmented"

# Employment types whose *candidates* we never source from a job portal talent pool.
# 사장님 규칙 3 — 프리랜서 제외. Instructor/mentor and talent-pool postings are the
# freelance surface of codeit's careers page, so they are collected and segmented but
# never turned into a candidate search.
_NON_SOURCEABLE_JOBS = ("강사", "멘토")
_NON_SOURCEABLE_TITLE_MARKERS = ("인재풀 등록", "콘텐츠 파트너")
_SOURCEABLE_ETYPES = ("정규직",)
_OPEN_STATUS = "상시 채용"

_JOB_SEGMENTS = {
    "소프트웨어 엔지니어링": "software_engineering",
    "PM": "product_management",
    "프로덕트 디자인": "product_design",
    "영상": "content_video",
    "보안": "security",
    "HR": "hr_ga",
    "마케팅": "marketing",
    "세일즈": "sales",
    "교육 운영": "education_operations",
    "교육 행정": "education_admin",
    "CX": "customer_experience",
    "강사·멘토": "instructor_mentor",
}


class ExperienceRange(tuple):
    """(annual_from, annual_to) with ``None`` meaning open-ended."""

    __slots__ = ()

    def __new__(cls, annual_from: int | None, annual_to: int | None):
        return super().__new__(cls, (annual_from, annual_to))

    @property
    def annual_from(self) -> int | None:
        return self[0]

    @property
    def annual_to(self) -> int | None:
        return self[1]


_RANGE = re.compile(r"(\d+)\s*~\s*(\d+)\s*년")
_AT_LEAST = re.compile(r"(\d+)\s*년\s*이상")
_AT_MOST = re.compile(r"(\d+)\s*년\s*이하")


def parse_experience(exp: str | None) -> ExperienceRange:
    """Turn codeit's Korean experience label into a numeric year range.

    ``경력 (3~10년)`` -> (3, 10); ``경력 (1년 이상)`` -> (1, None);
    ``경력 (5년 이하)`` -> (0, 5); ``경력 무관``/``신입``/missing -> (None, None).
    """
    if not exp:
        return ExperienceRange(None, None)
    text = exp.strip()
    if (match := _RANGE.search(text)) is not None:
        return ExperienceRange(int(match.group(1)), int(match.group(2)))
    if (match := _AT_LEAST.search(text)) is not None:
        return ExperienceRange(int(match.group(1)), None)
    if (match := _AT_MOST.search(text)) is not None:
        return ExperienceRange(0, int(match.group(1)))
    return ExperienceRange(None, None)


def segment_of(position: dict[str, Any]) -> str:
    """Map one posting to a stable snake_case segment key.

    Title markers win over the job label because codeit files talent-pool and
    content-partner postings under a normal job family (or under none at all).
    """
    title = position.get("title") or ""
    if any(marker in title for marker in _NON_SOURCEABLE_TITLE_MARKERS):
        return "talent_pool" if "인재풀 등록" in title else "content_partner"
    job = position.get("job")
    if job in _JOB_SEGMENTS:
        return _JOB_SEGMENTS[job]
    return UNSEGMENTED


def is_searchable(position: dict[str, Any]) -> bool:
    """True when this posting should drive a live candidate search on a job portal.

    Full-time, still open, and not one of the freelance instructor / talent-pool /
    content-partner surfaces. Interns and 계약직 are collected but not sourced.
    """
    if position.get("status") != _OPEN_STATUS:
        return False
    if position.get("etype") not in _SOURCEABLE_ETYPES:
        return False
    title = position.get("title") or ""
    if any(marker in title for marker in _NON_SOURCEABLE_TITLE_MARKERS):
        return False
    job = position.get("job") or ""
    return not any(marker in job for marker in _NON_SOURCEABLE_JOBS)


def expand_keywords(segment: str) -> dict[str, list[str]]:
    """Return the bilingual keyword tiers for a segment (see ``keywords.py``)."""
    return {name: tier(segment, name) for name in TIERS}


def segment_positions(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate every posting with segment, experience range, keywords and sourceability."""
    annotated = []
    for position in positions:
        segment = segment_of(position)
        years = parse_experience(position.get("exp"))
        annotated.append(
            {
                **position,
                "segment": segment,
                "annual_from": years.annual_from,
                "annual_to": years.annual_to,
                "searchable": is_searchable(position),
                "keywords": expand_keywords(segment),
                "query_terms": terms(segment),
            }
        )
    return annotated
