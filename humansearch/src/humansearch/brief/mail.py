"""HS-13.05 — 팀 브리프 메일의 제목·수신자·평문 본문을 조립한다.

§6 출력 계약(절 순서)·§7 D2(수신자)·D3(제목)·D10(회사 매력 포인트)이 여기서 강제된다.
순수 함수이며 시계는 호출자가 `today` 로 주입한다. 파일을 여는 함수는 계약 로더
`load_recipients`(`recipients.py` 소유, 여기서 그대로 재수출) 하나뿐이고,
발송 API 는 이 패키지 어디에도 없다(D8).

절의 **순서**는 이 파일이 코드로 소유한다. 순서를 상수 목록으로 빼면 시험이 그 상수를
같이 읽게 되고, 순서를 바꾼 변이가 시험과 함께 움직여 통과해 버린다(자기 대조 tautology).
그래서 `render_brief_body` 는 절을 문장 순서 그대로 붙이고, 기대 순서는 시험 파일이
따로 적는다.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date

from .linkedin_limit import check_linkedin
from .mail_sections import (
    SEPARATOR,
    render_candidates,
    render_company_research,
    render_gmail_channel,
    render_header,
    render_inmails,
    render_linkedin_channel,
    render_search_criteria,
    render_sources,
    render_two_field_channel,
)
from .policy import policy
from .recipients import Recipients, load_recipients
from .types import (
    Claim,
    CompanyBrief,
    JdSource,
    PositionSpec,
    _reject,
    _require_email,
    _require_text,
)
from .types_candidate import CandidateLead
from .types_packet import JdPacket, SearchFilters, TeamMail

__all__ = [
    "BriefDraft",
    "Recipients",
    "compose_brief_mail",
    "load_recipients",
    "render_brief_body",
]

_HTML_TAG = re.compile(r"<[A-Za-z/!]")
_ATTRACTION_RANGE = (3, 5)
_REFLECTION_RANGE = (1, 4)
_QUESTION_RANGE = (3, 5)


@dataclass(frozen=True)
class BriefDraft:
    """브리프 메일 한 통을 조립하기 위한 입력 묶음. 위반은 생성 시점에 거부한다."""

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
        self._check_intro()
        self._check_attraction()
        self._check_counts()
        self._check_sender()
        self._check_linkedin_count()
        self._check_inmails()

    def _check_intro(self) -> None:
        if len(self.intro_paragraphs) != 2:
            _reject("BriefDraft.intro_paragraphs 는 후보자 관점 소개 2문단이어야 한다(D10)")
        for index, paragraph in enumerate(self.intro_paragraphs):
            _require_text(paragraph, f"BriefDraft.intro_paragraphs[{index}]")
        _require_text(self.key_line, "BriefDraft.key_line")

    def _check_attraction(self) -> None:
        low, high = _ATTRACTION_RANGE
        if not low <= len(self.attraction_points) <= high:
            _reject(
                f"BriefDraft.attraction_points 는 {low}~{high}개여야 한다(D10): "
                f"{len(self.attraction_points)}개"
            )
        known = {ref.id for ref in self.company.sources}
        for index, point in enumerate(self.attraction_points):
            unknown = tuple(sorted(set(point.source_ids) - known))
            if unknown:
                _reject(
                    f"BriefDraft.attraction_points[{index}] 의 출처 id 가 "
                    f"company.sources 에 없다: {unknown}"
                )

    def _check_counts(self) -> None:
        for label, values, bounds in (
            ("reflection_notes", self.reflection_notes, _REFLECTION_RANGE),
            ("interview_questions", self.interview_questions, _QUESTION_RANGE),
        ):
            low, high = bounds
            if not low <= len(values) <= high:
                _reject(f"BriefDraft.{label} 는 {low}~{high}개여야 한다: {len(values)}개")
            for index, value in enumerate(values):
                _require_text(value, f"BriefDraft.{label}[{index}]")

    def _check_sender(self) -> None:
        _require_text(self.sender_name, "BriefDraft.sender_name")
        _require_email(self.sender_email, "BriefDraft.sender_email")
        if not self.sender_email.endswith(f"@{policy().team_mail_domain}"):
            _reject("BriefDraft.sender_email 이 계약 팀 도메인 밖이다")

    def _check_linkedin_count(self) -> None:
        measured = check_linkedin(self.jd_packet.linkedin_body).length
        if self.linkedin_char_count != measured:
            _reject(
                "BriefDraft.linkedin_char_count 가 실제 본문 길이와 다르다: "
                f"{self.linkedin_char_count} ≠ {measured}"
            )

    def _check_inmails(self) -> None:
        urls = {lead.linkedin_url for lead in self.candidates}
        for index, (url, body) in enumerate(self.inmails):
            if url not in urls:
                _reject(f"BriefDraft.inmails[{index}] 의 후보가 candidates 에 없다")
            _require_text(body, f"BriefDraft.inmails[{index}] 본문")


def render_brief_body(draft: BriefDraft, today: date) -> str:
    """§6 출력 계약 순서 그대로 평문 본문을 만든다(HTML 0)."""

    if not isinstance(today, date):
        _reject("render_brief_body 의 today 는 date 여야 한다")
    packet = draft.jd_packet
    lines: list[str] = list(
        render_header(
            draft.position,
            today,
            draft.intro_paragraphs[0],
            draft.key_line,
            draft.reflection_notes,
        )
    )

    lines.append(SEPARATOR)
    lines.extend(
        render_gmail_channel(
            draft.intro_paragraphs[1],
            draft.attraction_points,
            packet.gmail_body,
            draft.sender_name,
            draft.sender_email,
        )
    )

    lines.append(SEPARATOR)
    lines.extend(render_linkedin_channel(packet.linkedin_body, draft.linkedin_char_count))

    lines.append(SEPARATOR)
    lines.extend(render_two_field_channel(packet.two_field_company, packet.two_field_jd))

    lines.append(SEPARATOR)
    lines.extend(render_company_research(draft.company, draft.open_items, today))
    lines.append("")
    lines.extend(
        render_search_criteria(
            draft.search_filters,
            draft.keywords,
            draft.boolean_queries,
            draft.interview_questions,
        )
    )

    lines.append(SEPARATOR)
    lines.extend(render_sources(draft.company))

    lines.append(SEPARATOR)
    lines.extend(render_candidates(draft.candidates))
    lines.extend(render_inmails(draft.inmails, draft.candidates))
    return "\n".join(lines) + "\n"


def compose_brief_mail(
    draft: BriefDraft,
    recipients: Recipients,
    today: date,
    *,
    first_live: bool,
    search_mode: bool = False,
) -> TeamMail:
    """제목(D3)·수신자(D2)·평문 본문을 묶어 TeamMail 을 만든다.

    본문 끝에 `packet-id` 를 붙이지 않는다 — 패킷 id 는 §10 절차에서 러너가 붙이며,
    여기서 미리 붙이면 본문 해시가 패킷 id 를 알기 전에 굳어 버린다.
    """

    prefixes = policy().subject_prefixes
    if len(prefixes) < 2:
        _reject("브리프 정책의 subject_prefixes 가 브리프·서치 2형을 담고 있지 않다(D3)")
    prefix = prefixes[1] if search_mode else prefixes[0]
    subject = f"{prefix}{draft.position.client_name}, {draft.position.title}"
    if draft.candidates:
        subject += policy().subject_search_suffix

    body = render_brief_body(draft, today)
    if _HTML_TAG.search(body):
        _reject("팀 메일 본문에 HTML 태그가 있다 — 브리프는 평문으로만 나간다")

    to = recipients.first_live_to_only if first_live else recipients.to
    cc: tuple[str, ...] = () if first_live else recipients.cc
    return TeamMail(
        subject=subject,
        to=to,
        cc=cc,
        body=body,
        body_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
    )
