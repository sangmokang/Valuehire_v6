"""HS-13 포지션 브리프·서치 패킷 패키지의 공개 경계."""

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

# boolean_query 는 위 BriefInputError 가 이미 이 모듈 네임스페이스에 바인딩된 뒤에 임포트한다
# (boolean_query.py 는 `from . import BriefInputError` 로 이 패키지에서 되돌려 가져온다).
from .boolean_query import BooleanQuerySet, build_boolean_queries, check_balanced

__all__ = [
    "BooleanQuerySet",
    "BriefInputError",
    "CandidateEvidence",
    "CandidateLead",
    "Claim",
    "CompanyBrief",
    "ConnectionDegree",
    "EmailContact",
    "ExecProfile",
    "JdPacket",
    "JdSource",
    "PositionSpec",
    "ScoreBreakdown",
    "SearchPacket",
    "SourceRef",
    "TeamMail",
    "build_boolean_queries",
    "check_balanced",
]
