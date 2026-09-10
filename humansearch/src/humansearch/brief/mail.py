"""HS-13.05 — 팀 브리프 메일의 제목·수신자·평문 본문을 조립한다 (골격 · RED).

아직 구현이 없다. `humansearch/tests/test_hs_1305.py` 가 먼저 실패해야 하고,
그 실패가 이 파일의 유일한 존재 이유다(게이트 2 — RED 먼저).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .types import Claim, CompanyBrief, JdSource, PositionSpec
from .types_candidate import CandidateLead
from .types_packet import JdPacket, SearchFilters, TeamMail

__all__ = [
    "BriefDraft",
    "Recipients",
    "compose_brief_mail",
    "load_recipients",
    "render_brief_body",
]


@dataclass(frozen=True)
class Recipients:
    """팀 수신자 계약 파일의 내용(D2)."""

    to: tuple[str, ...]
    cc: tuple[str, ...]
    first_live_to_only: tuple[str, ...]


@dataclass(frozen=True)
class BriefDraft:
    """브리프 메일 한 통을 조립하기 위한 입력 묶음."""

    position: PositionSpec
    jd: JdSource
    company: CompanyBrief
    jd_packet: JdPacket
    candidates: tuple[CandidateLead, ...]
    boolean_queries: tuple[str, ...]
    inmails: tuple[tuple[str, str], ...]
    search_filters: SearchFilters
    intro_paragraphs: tuple[str, str]
    key_line: str
    reflection_notes: tuple[str, ...]
    attraction_points: tuple[Claim, ...]
    keywords: tuple[str, ...]
    interview_questions: tuple[str, ...]
    open_items: tuple[str, ...]
    linkedin_char_count: int
    sender_name: str
    sender_email: str

    def __post_init__(self) -> None:
        raise NotImplementedError("HS-13.05 BriefDraft 검증 미구현")


def load_recipients(path: Path | None = None) -> Recipients:
    """팀 수신자 계약 파일을 읽어 검증한다."""

    raise NotImplementedError("HS-13.05 load_recipients 미구현")


def render_brief_body(draft: BriefDraft, today: date) -> str:
    """§6 출력 계약 순서 그대로 평문 본문을 만든다."""

    raise NotImplementedError("HS-13.05 render_brief_body 미구현")


def compose_brief_mail(
    draft: BriefDraft,
    recipients: Recipients,
    today: date,
    *,
    first_live: bool,
    search_mode: bool = False,
) -> TeamMail:
    """제목(D3)·수신자(D2)·평문 본문을 묶어 TeamMail 을 만든다."""

    raise NotImplementedError("HS-13.05 compose_brief_mail 미구현")
