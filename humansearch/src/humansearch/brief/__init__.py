"""HS-13 포지션 브리프·서치 패킷 패키지의 공개 경계."""

from .boolean_query import BooleanQuerySet, build_boolean_queries, check_balanced
from .inmail import InMailDraft, build_inmail, build_inmails
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
from .linkedin_limit import (
    KOREAN_ENDINGS,
    LINKEDIN_FRAME_LINES,
    LinkedInReport,
    check_linkedin,
    core_tokens,
    verify_linkedin_fidelity,
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
    "KOREAN_ENDINGS",
    "LINKEDIN_FRAME_LINES",
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
    "InMailDraft",
    "JdPacket",
    "JdSource",
    "LinkedInReport",
    "PositionSpec",
    "ScoreBreakdown",
    "SearchPacket",
    "Section",
    "SourceRef",
    "TeamMail",
    "TwoField",
    "build_boolean_queries",
    "build_inmail",
    "build_inmails",
    "check_balanced",
    "check_linkedin",
    "content_lines",
    "core_tokens",
    "extract_block",
    "normalize_line",
    "split_sections",
    "split_two_field",
    "verify_fidelity",
    "verify_linkedin_fidelity",
]
