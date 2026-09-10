"""HS-13.08 — 후보별 InMail 초안을 1,899자 한도 안에서 만든다.

§7 D4(길이 판정은 `linkedin_limit.check_linkedin` 재사용)와 §9 HS-13.08 을 구현한다.
구조는 고정 순서다: ① 인사(`greeting`, 호출자가 후보 이름을 넣어 만든다) ② 매칭 이유
최대 2개(`lead.match_reasons[:2]`, 각 줄 앞 "• ") ③ `linkedin_body`(JD 의 LinkedIn 판,
그대로) ④ `sender_line`. 빈 줄 1개로 구분한다.

자동 축약은 하지 않는다 — 한도를 넘으면 거부만 하고, 호출자가 `linkedin_body` 를
줄여 다시 부른다. 발송 함수는 없다(D0 §4 — 발송은 항상 금지. 이 모듈에
`send`/`smtplib`/`requests` 는 0건이다).

시계·파일·네트워크 접근 0, 전부 순수 함수다.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .types_candidate import CandidateLead

__all__ = ["InMailDraft", "build_inmail", "build_inmails"]


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
    limit: int = 1899,
) -> InMailDraft:
    """고정 순서(인사·매칭 이유·JD 본문·발신자 줄)로 InMail 초안 하나를 만든다."""
    raise NotImplementedError


def build_inmails(
    leads: tuple[CandidateLead, ...],
    linkedin_body: str,
    *,
    greeting_for: Callable[[CandidateLead], str],
    sender_line: str,
    limit: int = 1899,
) -> tuple[tuple[str, str], ...]:
    """`SearchPacket.inmails` 형식 `(linkedin_url, body)` 튜플들을 만든다."""
    raise NotImplementedError
