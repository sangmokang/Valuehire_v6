"""HS-13 브리프 패킷의 후보자 값 타입 — 연락처·근거·점수·후보.

§4 후보·이메일 행과 §7 D6(4축 상한 40/20/20/20)을 생성 시점에 강제한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .types import (
    _reject,
    _require_count,
    _require_email,
    _require_http_url,
    _require_profile_url,
    _require_range,
    _require_text,
)

__all__ = [
    "CandidateEvidence",
    "CandidateLead",
    "ConnectionDegree",
    "EmailContact",
    "ScoreBreakdown",
]

_SCORE_LIMITS = (("role", 40), ("education", 20), ("stability", 20), ("profile", 20))


@dataclass(frozen=True)
class EmailContact:
    """공개 출처에서 확인된 이메일. 출처 없는 주소는 존재할 수 없다."""

    address: str
    source_url: str
    provenance: str

    def __post_init__(self) -> None:
        _require_email(self.address, "EmailContact.address")
        _require_http_url(self.source_url, "EmailContact.source_url")
        _require_text(self.provenance, "EmailContact.provenance")


class ConnectionDegree(Enum):
    """LinkedIn 연결 촌수. 로그인 화면 밖에서는 UNKNOWN."""

    UNKNOWN = "unknown"
    FIRST = "first"
    SECOND = "second"
    THIRD_PLUS = "third_plus"


@dataclass(frozen=True)
class CandidateEvidence:
    """러너가 추출한 구조화 사실. 점수 함수의 유일한 입력."""

    role_match_terms: tuple[str, ...]
    jd_required_terms_hit: int
    jd_required_terms_total: int
    highest_education: str | None
    school_tier: int | None
    tenure_months_per_job: tuple[int, ...]
    jobs_last_5y: int
    profile_fields_filled: int
    profile_fields_total: int

    def __post_init__(self) -> None:
        prefix = "CandidateEvidence"
        hit = _require_count(self.jd_required_terms_hit, f"{prefix}.jd_required_terms_hit")
        total = _require_count(self.jd_required_terms_total, f"{prefix}.jd_required_terms_total")
        if hit > total:
            _reject(f"{prefix}.jd_required_terms_hit 이 total 보다 크다")
        filled = _require_count(self.profile_fields_filled, f"{prefix}.profile_fields_filled")
        fields = _require_count(self.profile_fields_total, f"{prefix}.profile_fields_total")
        if filled > fields:
            _reject(f"{prefix}.profile_fields_filled 이 total 보다 크다")
        _require_count(self.jobs_last_5y, f"{prefix}.jobs_last_5y")
        for index, months in enumerate(self.tenure_months_per_job):
            _require_count(months, f"{prefix}.tenure_months_per_job[{index}]")
        if self.school_tier is not None:
            _require_range(self.school_tier, f"{prefix}.school_tier", 1, 4)


@dataclass(frozen=True)
class ScoreBreakdown:
    """D6 4축 점수. 상한 40/20/20/20."""

    role: int
    education: int
    stability: int
    profile: int

    def __post_init__(self) -> None:
        for axis, upper in _SCORE_LIMITS:
            _require_range(getattr(self, axis), f"ScoreBreakdown.{axis}", 0, upper)

    @property
    def total(self) -> int:
        """4축 합계(0..100)."""
        return self.role + self.education + self.stability + self.profile


@dataclass(frozen=True)
class CandidateLead:
    """초도 후보 한 명. LinkedIn 공개 프로필 URL 이 식별자다."""

    display_name: str
    headline: str
    linkedin_url: str
    education: str
    career: str
    match_reasons: tuple[str, ...]
    check_points: tuple[str, ...]
    evidence: CandidateEvidence
    score: ScoreBreakdown
    email: EmailContact | None
    degree: ConnectionDegree
    source_note: str

    def __post_init__(self) -> None:
        _require_text(self.display_name, "CandidateLead.display_name")
        _require_profile_url(self.linkedin_url, "CandidateLead.linkedin_url")
        _require_text(self.source_note, "CandidateLead.source_note")
        if not isinstance(self.degree, ConnectionDegree):
            _reject("CandidateLead.degree 는 ConnectionDegree 여야 한다")
