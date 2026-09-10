"""HS-13.02 — JD 원문의 내용 줄이 렌더링 결과에 그대로 남았는지 판정한다.

§7 D5: "100% 정확"의 판정 단위는 **내용 줄**(공백·글머리표·마크다운 기호 정규화 후)이다.
순서 보존은 요구하지 않으며, 외부 공고의 연차·학력·연봉 조건이 렌더링에만 끼어들면 FAIL 이다.
시계·파일·네트워크 접근 0, 전부 순수 함수다. 정규식은 모듈 상수(문자열)로 두고 호출 시점에 컴파일한다.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .types import BriefInputError, JdSource

__all__ = [
    "EXTRA_CONDITION_PATTERNS",
    "FidelityReport",
    "Section",
    "content_lines",
    "extract_block",
    "normalize_line",
    "split_sections",
    "verify_fidelity",
]

# 선행 글머리표로만 취급하는 문자. 번호(`1)`)·기호(`※`)는 내용이므로 여기 없다.
_BULLET_CHARS = frozenset("•-*·–—▪■○●◦>|")
_MARKDOWN_MARKS = re.compile(r"\*\*|__|`")
_WHITESPACE_RUN = re.compile(r"\s+")
_SENTENCE_END = (".", "!", "?", "。")
_HEADING_MAX_LEN = 12

# 렌더링에만 있으면 FAIL 로 볼 "연차·학력·연봉" 조건. 컴파일은 _matches_condition 에서 한다.
EXTRA_CONDITION_PATTERNS: tuple[str, ...] = (
    r"\d+\s*~?\s*\d*\s*년\s*(이상|이하|차|이내)",
    r"경력\s*\d+",
    r"신입",
    r"(학사|석사|박사)\s*(이상|학위)",
    r"연봉",
    r"\d[\d,]*\s*만\s*원",
    r"\d[\d,]*\s*억",
)


def _strip_bullets(text: str) -> str:
    """양끝 공백과 선행 글머리표 문자를 더 지울 것이 없을 때까지 번갈아 지운다."""
    stripped = text.strip()
    while stripped and stripped[0] in _BULLET_CHARS:
        stripped = stripped[1:].strip()
    return stripped


def _drop_markdown(text: str) -> str:
    """`**`·`__`·백틱을 고정점까지 지운다(한 번만 지우면 잔여 기호가 새 쌍을 만든다)."""
    current = text
    while True:
        shorter = _MARKDOWN_MARKS.sub("", current)
        if shorter == current:
            return current
        current = shorter


def normalize_line(line: str) -> str:
    """한 줄을 비교 가능한 내용 줄로 정규화한다. 내용이 남지 않으면 빈 문자열."""
    text = unicodedata.normalize("NFKC", line)
    text = text.replace("　", " ").replace("\t", " ")
    text = _strip_bullets(text)
    text = _drop_markdown(text)
    text = _strip_bullets(text)
    text = unicodedata.normalize("NFKC", text)
    return _WHITESPACE_RUN.sub(" ", text).strip()


def content_lines(text: str) -> tuple[str, ...]:
    """정규화 후 남는 내용 줄만 순서·중복 그대로 돌려준다."""
    normalized = (normalize_line(raw) for raw in text.splitlines())
    return tuple(line for line in normalized if line)


@dataclass(frozen=True)
class Section:
    """JD 한 절 — 제목 한 줄(`heading`)과 그 아래 내용 줄들(`lines`)."""

    heading: str
    lines: tuple[str, ...]


def _raw_body(raw: str) -> str:
    return unicodedata.normalize("NFKC", raw).replace("　", " ").replace("\t", " ").strip()


def _is_bullet_raw(raw: str) -> bool:
    body = _raw_body(raw)
    return bool(body) and body[0] in _BULLET_CHARS


def _is_heading(raw: str, normalized: str) -> bool:
    """제목 판정 — ① 원문이 `|` 로 시작 ② `[`…`]` 로 감싸짐 ③ 짧고 문장 종결이 아닌 비글머리표 줄."""
    if not normalized:
        return False
    if _raw_body(raw).startswith("|"):
        return True
    if normalized.startswith("[") and normalized.endswith("]"):
        return True
    if _is_bullet_raw(raw):
        return False
    return len(normalized) <= _HEADING_MAX_LEN and not normalized.endswith(_SENTENCE_END)


def _heading_text(normalized: str) -> str:
    return normalized.replace("|", "").replace("[", "").replace("]", "").strip()


def split_sections(text: str) -> tuple[Section, ...]:
    """JD 를 제목 단위 절로 나눈다. 첫 제목 앞의 줄들은 heading 이 빈 Section 이다."""
    sections: list[Section] = []
    heading = ""
    lines: list[str] = []
    opened = False
    for raw in text.splitlines():
        normalized = normalize_line(raw)
        if not normalized:
            continue
        if _is_heading(raw, normalized):
            if opened or lines:
                sections.append(Section(heading=heading, lines=tuple(lines)))
            heading = _heading_text(normalized)
            lines = []
            opened = True
            continue
        lines.append(normalized)
    if opened or lines:
        sections.append(Section(heading=heading, lines=tuple(lines)))
    return tuple(sections)


@dataclass(frozen=True)
class FidelityReport:
    """충실도 판정 결과. `missing` 은 JD 순서, `extra_condition` 은 렌더링 순서."""

    missing: tuple[str, ...]
    extra_condition: tuple[str, ...]
    jd_line_count: int
    rendered_line_count: int
    extra_lines: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        raise NotImplementedError("HS-13.02b 미구현")


def _matches_condition(line: str) -> bool:
    return any(re.compile(pattern).search(line) for pattern in EXTRA_CONDITION_PATTERNS)


def _normalized_allowlist(allowed_extra: tuple[str, ...]) -> frozenset[str]:
    allowed: set[str] = set()
    for item in allowed_extra:
        normalized = normalize_line(item)
        if not normalized:
            raise BriefInputError("allowed_extra 에 내용 없는 줄이 있다(공백·글머리표뿐)")
        allowed.add(normalized)
    return frozenset(allowed)


def verify_fidelity(
    jd: JdSource,
    rendered: str,
    *,
    allowed_extra: tuple[str, ...] = (),
) -> FidelityReport:
    """JD 내용 줄이 렌더링에 빠짐없이 있는지, 렌더링에만 조건이 끼었는지 판정한다."""
    if not rendered.strip():
        raise BriefInputError("verify_fidelity 의 rendered 는 공백만일 수 없다")
    allowed = _normalized_allowlist(allowed_extra)
    jd_lines = content_lines(jd.text)
    rendered_lines = content_lines(rendered)
    jd_seen = frozenset(jd_lines)
    rendered_seen = frozenset(rendered_lines)
    missing = tuple(line for line in jd_lines if line not in rendered_seen)
    extra_condition = tuple(
        line
        for line in rendered_lines
        if line not in jd_seen and line not in allowed and _matches_condition(line)
    )
    return FidelityReport(
        missing=missing,
        extra_condition=extra_condition,
        jd_line_count=len(jd_lines),
        rendered_line_count=len(rendered_lines),
    )


def extract_block(text: str, start_marker: str, end_marker: str) -> str:
    raise NotImplementedError("HS-13.02b 미구현")
