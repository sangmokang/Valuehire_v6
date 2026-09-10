"""HS-13.04 — JD 를 회사 소개(필드1)·JD 본문(필드2) 2개 필드로 명시적으로 나눈다.

사람인·잡코리아 등록 화면은 회사 소개와 JD 내용을 별도 입력칸으로 받는다. §5(two_field.py)·
§6 3절·§9 HS-13.04 계약: 필드2 는 호출자가 `section_markers` 로 지정한 절들만(순서는 JD
순서, 마커 나열 순서 아님) 골라 원문 그대로(정규화하지 않은 원문 줄) 이어 붙인 것이고,
자기 자신에 대한 `verify_fidelity` 가 항상 통과해야 한다. 마커에 없는 절(예: "혜택 및
복지"·"채용 전형")은 생략이 명시적이도록 필드2에 들어가지 않는다.

순수 함수. 시계·파일·네트워크 접근 0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .jd_fidelity import FidelityReport, normalize_line, split_sections, verify_fidelity
from .types import BriefInputError, JdSource

__all__ = ["TwoField", "split_two_field"]

# §4 입력 영역 표: HTML 태그 잔존은 어디서든 거부한다.
_HTML_TAG_RE = re.compile(r"<[A-Za-z/!]")


@dataclass(frozen=True)
class TwoField:
    """사람인·잡코리아 2필드 — 필드1(회사 소개)·필드2(JD 본문)와 필드2 자기 충실도 보고."""

    company_intro: str
    jd_body: str
    report: FidelityReport


def split_two_field(
    jd: JdSource,
    company_intro: str,
    *,
    section_markers: tuple[str, ...],
) -> TwoField:
    """JD 를 회사 소개(company_intro)·JD 본문(section_markers 로 고른 절) 2필드로 나눈다."""
    raise NotImplementedError
