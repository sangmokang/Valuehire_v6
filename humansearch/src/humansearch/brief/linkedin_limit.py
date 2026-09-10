"""HS-13.03 — LinkedIn InMail 1,899자 한도와 절 생략·어미 축약 정책을 판정한다(골격).

RED 단계 골격이다. 공개 이름은 전부 존재하지만 판정은 아직 없다(NotImplementedError).
"""

from __future__ import annotations

from dataclasses import dataclass

from .jd_fidelity import FidelityReport
from .types import JdSource

__all__ = [
    "KOREAN_ENDINGS",
    "LINKEDIN_FRAME_LINES",
    "LinkedInReport",
    "check_linkedin",
    "core_tokens",
    "verify_linkedin_fidelity",
]

# GREEN 에서 채운다. 지금 비어 있는 것은 "아직 판정하지 않는다"는 뜻이다.
KOREAN_ENDINGS: tuple[str, ...] = ()
LINKEDIN_FRAME_LINES: tuple[str, ...] = ()


@dataclass(frozen=True)
class LinkedInReport:
    """LinkedIn 본문 길이 판정 결과."""

    length: int
    limit: int
    ok: bool
    over_by: int


def check_linkedin(body: str, *, limit: int = 1899) -> LinkedInReport:
    """본문 길이가 한도 이내인지 판정한다."""
    raise NotImplementedError("HS-13.03 GREEN 에서 구현한다")


def core_tokens(line: str) -> tuple[str, ...]:
    """어미·조사를 뗀 핵심 토큰 열을 돌려준다."""
    raise NotImplementedError("HS-13.03 GREEN 에서 구현한다")


def verify_linkedin_fidelity(
    jd: JdSource,
    body: str,
    *,
    omittable_sections: tuple[str, ...] = (),
    allowed_extra: tuple[str, ...] = (),
) -> FidelityReport:
    """지정 절 생략과 어미 축약만 허용하고 그 밖의 누락·추가를 잡아낸다."""
    raise NotImplementedError("HS-13.03 GREEN 에서 구현한다")
