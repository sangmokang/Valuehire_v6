"""HS-13 브리프 패킷의 산출물 값 타입 — 채널별 JD·팀 메일·서치 패킷.

§7 D3(제목)·D4(1,899자)와 §4 수신자·본문 길이 행을 생성 시점에 강제한다.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .types import (
    CompanyBrief,
    JdSource,
    PositionSpec,
    _reject,
    _require_email,
    _require_sha256,
    _require_text,
)
from .types_candidate import CandidateLead

__all__ = ["JdPacket", "SearchPacket", "TeamMail"]

# D4: 본문은 1,899 코드포인트까지. 1,900 이상이면 거부한다(개행 포함).
_BODY_REJECT_AT = 1900
_TEAM_DOMAIN = "@valueconnect.kr"
_SUBJECT_PREFIXES = ("[포지션]", "[ValuehireSearch][포지션]")
_PACKET_ID = re.compile(r"[0-9]{8}-[A-Za-z0-9]+-[0-9a-f]{8}")


def _require_within_limit(body: str, field: str) -> None:
    if len(body) >= _BODY_REJECT_AT:
        _reject(f"{field} 가 {_BODY_REJECT_AT - 1}자를 넘는다: {len(body)}자")


def _require_balanced_query(query: str, index: int) -> None:
    if query.count('"') % 2 != 0:
        _reject(f"boolean_queries[{index}] 의 큰따옴표 짝이 맞지 않는다")
    depth = 0
    for char in query:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                _reject(f"boolean_queries[{index}] 의 괄호가 열리기 전에 닫힌다")
    if depth != 0:
        _reject(f"boolean_queries[{index}] 의 괄호가 닫히지 않았다")


@dataclass(frozen=True)
class JdPacket:
    """채널별 JD 3종(Gmail·LinkedIn·2필드)."""

    gmail_body: str
    linkedin_body: str
    two_field_company: str
    two_field_jd: str

    def __post_init__(self) -> None:
        bodies = (
            ("gmail_body", self.gmail_body),
            ("linkedin_body", self.linkedin_body),
            ("two_field_company", self.two_field_company),
            ("two_field_jd", self.two_field_jd),
        )
        for label, body in bodies:
            _require_text(body, f"JdPacket.{label}")
        _require_within_limit(self.linkedin_body, "JdPacket.linkedin_body")


@dataclass(frozen=True)
class TeamMail:
    """팀 내부 공유 메일 한 통. 본문 해시로 발송 readback 과 대조한다."""

    subject: str
    to: tuple[str, ...]
    cc: tuple[str, ...]
    body: str
    body_sha256: str

    def __post_init__(self) -> None:
        if not self.subject.startswith(_SUBJECT_PREFIXES):
            _reject("TeamMail.subject 는 D3 제목 형식으로 시작해야 한다")
        if not self.to:
            _reject("TeamMail.to 는 1명 이상이어야 한다")
        seen: set[str] = set()
        for label, addresses in (("to", self.to), ("cc", self.cc)):
            for address in addresses:
                _require_email(address, f"TeamMail.{label}")
                if not address.endswith(_TEAM_DOMAIN):
                    _reject(f"TeamMail.{label} 에 계약 도메인 밖 주소가 있다")
                if address in seen:
                    _reject(f"TeamMail.{label} 에 중복 주소가 있다")
                seen.add(address)
        _require_text(self.body, "TeamMail.body")
        _require_sha256(self.body_sha256, "TeamMail.body_sha256")
        if self.body_sha256 != hashlib.sha256(self.body.encode("utf-8")).hexdigest():
            _reject("TeamMail.body_sha256 이 본문 해시와 다르다")


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

    def __post_init__(self) -> None:
        if not _PACKET_ID.fullmatch(self.packet_id):
            _reject("SearchPacket.packet_id 는 {yyyymmdd}-{clickup_id}-{sha8} 형태여야 한다")
        known: set[str] = set()
        for lead in self.candidates:
            if lead.linkedin_url in known:
                _reject("SearchPacket.candidates 에 중복 LinkedIn URL 이 있다")
            known.add(lead.linkedin_url)
        for index, (url, body) in enumerate(self.inmails):
            if url not in known:
                _reject(f"SearchPacket.inmails[{index}] 의 후보가 candidates 에 없다")
            _require_within_limit(body, f"SearchPacket.inmails[{index}]")
        for index, query in enumerate(self.boolean_queries):
            _require_balanced_query(query, index)
