"""HS-13.08 — 후보별 InMail 초안을 1,899자 한도 안에서 만든다.

§7 D4(길이 판정은 `linkedin_limit.check_linkedin` 재사용)와 §9 HS-13.08 을 구현한다.
구조는 고정 순서다: ① 인사(`greeting`, 호출자가 후보 이름을 넣어 만든다) ② 매칭 이유
최대 2개(`lead.match_reasons[:2]`, 각 줄 앞 "• ") ③ `linkedin_body`(JD 의 LinkedIn 판,
그대로) ④ `sender_line`. 빈 줄 1개로 구분한다.

자동 축약은 하지 않는다 — 한도를 넘으면 거부만 하고, 호출자가 `linkedin_body` 를
줄여 다시 부른다. 발송 함수는 없다(D0 §4 — 발송은 항상 금지. 이 모듈은 초안 문자열만
만들 뿐, 메일 전송 계열 표준 라이브러리·HTTP 클라이언트를 전혀 참조하지 않는다).

시계·파일·네트워크 접근 0, 전부 순수 함수다.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from .linkedin_limit import check_linkedin
from .types import _reject
from .types_candidate import CandidateLead

__all__ = ["InMailDraft", "build_inmail", "build_inmails"]

# HTML 태그 흔적. types.py 의 JdSource 검사와 같은 패턴이다.
_HTML_TAG = re.compile(r"<[A-Za-z/!]")
# 매칭 이유는 최대 이 개수까지만 싣는다(§9 HS-13.08).
_MAX_REASONS = 2


def _require_no_html(value: str, field: str) -> None:
    if _HTML_TAG.search(value):
        _reject(f"{field} 에 HTML 태그가 있다")


@dataclass(frozen=True)
class InMailDraft:
    """한 후보에게 보낼 InMail 초안. 발송 함수는 없다 — 초안만 만든다."""

    linkedin_url: str
    body: str
    length: int


def build_inmail(
    lead: CandidateLead,
    linkedin_body: str,
    *,
    greeting: str,
    sender_line: str,
    limit: int | None = None,
) -> InMailDraft:
    """고정 순서(인사·매칭 이유·JD 본문·발신자 줄)로 InMail 초안 하나를 만든다.

    한도 초과는 거부만 한다 — `linkedin_body` 를 줄이지 않는다(자동 축약 금지).
    거부하면 호출자가 `linkedin_body` 를 줄여 다시 호출해야 한다.
    """
    _require_no_html(greeting, "build_inmail 의 greeting")
    _require_no_html(linkedin_body, "build_inmail 의 linkedin_body")
    if lead.display_name not in greeting:
        _reject("build_inmail 의 greeting 에 후보 이름(display_name)이 없다")
    if not lead.match_reasons:
        _reject("build_inmail 의 lead.match_reasons 가 비어 있다")
    if not sender_line.strip():
        _reject("build_inmail 의 sender_line 은 공백일 수 없다")

    reasons_block = "\n".join(f"• {reason}" for reason in lead.match_reasons[:_MAX_REASONS])
    body = f"{greeting}\n\n{reasons_block}\n\n{linkedin_body}\n\n{sender_line}"

    report = check_linkedin(body, limit=limit)
    if not report.ok:
        _reject(
            f"build_inmail 의 초안이 {report.limit}자를 넘는다"
            f"({report.length}자, {report.over_by}자 초과) —"
            " linkedin_body 를 줄여 다시 호출하라(자동 축약 없음)"
        )
    return InMailDraft(linkedin_url=lead.linkedin_url, body=body, length=report.length)


def build_inmails(
    leads: tuple[CandidateLead, ...],
    linkedin_body: str,
    *,
    greeting_for: Callable[[CandidateLead], str],
    sender_line: str,
    limit: int | None = None,
) -> tuple[tuple[str, str], ...]:
    """`SearchPacket.inmails` 형식 `(linkedin_url, body)` 튜플들을 만든다.

    같은 LinkedIn URL 이 `leads` 에 중복되면 거부한다.
    """
    seen: set[str] = set()
    drafts: list[tuple[str, str]] = []
    for lead in leads:
        if lead.linkedin_url in seen:
            _reject(f"build_inmails 의 leads 에 중복 LinkedIn URL 이 있다: {lead.linkedin_url}")
        seen.add(lead.linkedin_url)
        draft = build_inmail(
            lead,
            linkedin_body,
            greeting=greeting_for(lead),
            sender_line=sender_line,
            limit=limit,
        )
        drafts.append((draft.linkedin_url, draft.body))
    return tuple(drafts)
