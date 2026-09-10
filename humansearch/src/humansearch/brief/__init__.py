"""HS-13 포지션 브리프·서치 패킷 패키지의 공개 경계."""

from .boolean_query import BooleanQuerySet, build_boolean_queries, check_balanced
from .jd_fidelity import (
    EXTRA_CONDITION_PATTERNS,
    FidelityReport,
    Section,
    content_lines,
    extract_block,
    normalize_line,
    split_sections,
    verify_fidelity,
)
from .two_field import TwoField, split_two_field
from .types import (
    BriefInputError,
    Claim,
    CompanyBrief,
    ExecProfile,
    JdSource,
    PositionSpec,
    SourceRef,
)
from .types_candidate import (
    CandidateEvidence,
    CandidateLead,
    ConnectionDegree,
    EmailContact,
    ScoreBreakdown,
)
from .types_packet import JdPacket, SearchPacket, TeamMail

__all__ = [
    "EXTRA_CONDITION_PATTERNS",
    "BooleanQuerySet",
    "BriefInputError",
    "CandidateEvidence",
    "CandidateLead",
    "Claim",
    "CompanyBrief",
    "ConnectionDegree",
    "EmailContact",
    "ExecProfile",
    "FidelityReport",
    "JdPacket",
    "JdSource",
    "PositionSpec",
    "ScoreBreakdown",
    "SearchPacket",
    "Section",
    "SourceRef",
    "TeamMail",
    "TwoField",
    "build_boolean_queries",
    "check_balanced",
    "content_lines",
    "extract_block",
    "normalize_line",
    "split_sections",
    "split_two_field",
    "verify_fidelity",
]
