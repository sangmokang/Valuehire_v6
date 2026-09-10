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
from .policy import (
    BriefPolicy,
    load_brief_policy,
    override_policy_for_tests,
    policy,
)
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
from .types_packet import JdPacket, SearchFilters, SearchPacket, TeamMail

__all__ = [
    "EXTRA_CONDITION_PATTERNS",
    "BooleanQuerySet",
    "BriefInputError",
    "BriefPolicy",
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
    "SearchFilters",
    "SearchPacket",
    "Section",
    "SourceRef",
    "TeamMail",
    "build_boolean_queries",
    "check_balanced",
    "content_lines",
    "extract_block",
    "load_brief_policy",
    "normalize_line",
    "override_policy_for_tests",
    "policy",
    "split_sections",
    "verify_fidelity",
]
