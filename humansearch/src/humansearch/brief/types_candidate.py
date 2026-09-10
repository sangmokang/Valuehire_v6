"""HS-13 브리프 패킷의 후보자 값 타입 — 연락처·근거·점수·후보."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "CandidateEvidence",
    "CandidateLead",
    "ConnectionDegree",
    "EmailContact",
    "ScoreBreakdown",
]


@dataclass(frozen=True)
class EmailContact:
    """공개 출처에서 확인된 이메일. 출처 없는 주소는 존재할 수 없다."""

    address: str
    source_url: str
    provenance: str


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


@dataclass(frozen=True)
class ScoreBreakdown:
    """D6 4축 점수. 상한 40/20/20/20."""

    role: int
    education: int
    stability: int
    profile: int

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
