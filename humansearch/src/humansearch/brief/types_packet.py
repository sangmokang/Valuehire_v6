"""HS-13 브리프 패킷의 산출물 값 타입 — 채널별 JD·팀 메일·서치 패킷."""

from __future__ import annotations

from dataclasses import dataclass

from .types import CompanyBrief, JdSource, PositionSpec
from .types_candidate import CandidateLead

__all__ = ["JdPacket", "SearchPacket", "TeamMail"]


@dataclass(frozen=True)
class JdPacket:
    """채널별 JD 3종(Gmail·LinkedIn·2필드)."""

    gmail_body: str
    linkedin_body: str
    two_field_company: str
    two_field_jd: str


@dataclass(frozen=True)
class TeamMail:
    """팀 내부 공유 메일 한 통. 본문 해시로 발송 readback 과 대조한다."""

    subject: str
    to: tuple[str, ...]
    cc: tuple[str, ...]
    body: str
    body_sha256: str


@dataclass(frozen=True)
class SearchPacket:
    """한 포지션의 브리프를 만들기 위해 모은 구조화 자료 묶음."""

    packet_id: str
    position: PositionSpec
    jd: JdSource
    company: CompanyBrief
    jd_packet: JdPacket
    candidates: tuple[CandidateLead, ...]
    mail: TeamMail
    boolean_queries: tuple[str, ...]
    inmails: tuple[tuple[str, str], ...]
