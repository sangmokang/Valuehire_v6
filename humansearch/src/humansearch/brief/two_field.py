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


def _raw_sections(text: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """`split_sections` 의 절 경계(개수)를 그대로 써서 원문(비정규화) 줄을 절 단위로 되짚는다.

    `split_sections` 는 정규화된 내용 줄만 돌려준다. 여기서는 그 절마다의 줄 개수를
    빌려, 원문에서 내용 있는 줄(정규화 결과가 빈 문자열이 아닌 줄)만 같은 순서로 다시
    훑어 절 경계에 맞게 슬라이스한다 — heading 판정 로직 자체는 재구현하지 않는다.
    """
    sections = split_sections(text)
    raw_lines = [line for line in text.splitlines() if normalize_line(line)]
    pointer = 0
    result: list[tuple[str, tuple[str, ...]]] = []
    for section in sections:
        block: list[str] = []
        if section.heading:
            block.append(raw_lines[pointer])
            pointer += 1
        body_count = len(section.lines)
        block.extend(raw_lines[pointer : pointer + body_count])
        pointer += body_count
        result.append((section.heading, tuple(block)))
    return tuple(result)


def split_two_field(
    jd: JdSource,
    company_intro: str,
    *,
    section_markers: tuple[str, ...],
) -> TwoField:
    """JD 를 회사 소개(company_intro)·JD 본문(section_markers 로 고른 절) 2필드로 나눈다."""
    if not company_intro.strip():
        raise BriefInputError("company_intro 는 공백만일 수 없다")
    if _HTML_TAG_RE.search(company_intro):
        raise BriefInputError("company_intro 에 HTML 태그가 남아 있다")
    if not section_markers:
        raise BriefInputError("section_markers 는 비어 있을 수 없다")

    raw_sections = _raw_sections(jd.text)
    heading_set = frozenset(heading for heading, _ in raw_sections if heading)

    normalized_markers: list[str] = []
    for marker in section_markers:
        normalized = normalize_line(marker)
        if not normalized:
            raise BriefInputError(f"section_markers 에 내용 없는 마커가 있다: {marker!r}")
        if normalized not in heading_set:
            raise BriefInputError(f"section_markers 에 없는 절 이름이다: {marker!r}")
        normalized_markers.append(normalized)
    marker_set = frozenset(normalized_markers)

    for line in company_intro.splitlines():
        normalized_line = normalize_line(line)
        if normalized_line and normalized_line in heading_set:
            raise BriefInputError(
                f"company_intro 에 JD 절 제목 줄이 그대로 들어 있다: {normalized_line!r}"
            )

    selected = [(heading, lines) for heading, lines in raw_sections if heading in marker_set]
    content_line_total = sum(len(lines) - 1 for _, lines in selected)
    if content_line_total <= 0:
        raise BriefInputError("section_markers 로 고른 절이 모두 빈 절이다(본문 줄이 없다)")

    flat_lines = [line for _, lines in selected for line in lines]
    jd_body = "\n".join(flat_lines)
    if not jd_body.strip():
        raise BriefInputError("jd_body 가 공백뿐이다")

    selected_source = JdSource(text=jd_body, raw_sha256=jd.raw_sha256, provided_by=jd.provided_by)
    report = verify_fidelity(selected_source, jd_body)
    if not report.ok:
        raise BriefInputError("jd_body 가 선택된 절의 원문과도 자기 충실도를 만족하지 못한다")

    return TwoField(company_intro=company_intro, jd_body=jd_body, report=report)
