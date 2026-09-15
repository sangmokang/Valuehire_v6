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
    "judgement_form",
    "mixed_script_word",
    "multi_position_hint",
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

# §4 "JD 합본" 행 — 한 문서에 포지션이 둘 이상 섞였을 수 있다는 **경고**용 머리 줄.
# 거부 근거는 러너가 적는 `JdSource.position_count` 다(HS-13.01b). 이 휴리스틱은
# 단일 JD 의 `포지션:`+`직무:` 를 오탐하므로 `ok` 에는 절대 넣지 않는다(Codex 2차 반례).
_POSITION_HEAD_PREFIXES = ("포지션:", "Position:", "직무:")
_MARKDOWN_HEADING = "## "
_MULTI_POSITION_MIN = 2

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


# 판정용 사본에서 지우는 것: 화면에 나타나지 않는 문자와 마크다운 표시 문법.
# 사람 눈에는 `경력 5년 이상` 인데 글자 사이가 갈려 조건 정규식을 빠져나가는 변형을 막는다.
#   Codex V2 2차: `경\u200b력 5년 이\u200b상` · `경**력** 5년 이**상**`
#   Codex V1 3차: `경\ufe0f력 5년 이\ufe0f상`(U+FE0F 는 Cf 가 아니라 Mn 이다) · `경[력]() 5년 이[상]()`
_EMPHASIS = re.compile(r"\*\*|__|~~|[*_`]")

# `[표시](주소)` · `![표시](주소)` · `[표시]()` 를 표시 문자열로 되돌린다. 주소는 판정에서 뺀다 —
# 사람이 화면에서 읽는 것은 표시 문자열뿐이기 때문이다.
_MARKDOWN_LINK = re.compile(r"!?\[([^\]\[]*)\]\([^()]*\)")

# 기본적으로 보이지 않는데 Cf 가 아닌 것들: 변이 선택자와 결합 격리(전부 Mn 범주).
_INVISIBLE_MARKS = frozenset(
    chr(cp)
    for cp in (*range(0xFE00, 0xFE10), *range(0x180B, 0x180E), *range(0xE0100, 0xE01F0), 0x034F)
)


def _is_invisible(char: str) -> bool:
    return unicodedata.category(char) == "Cf" or char in _INVISIBLE_MARKS


def judgement_form(text: str) -> str:
    """조건 판정·충실도 대조에 쓰는 **사본**. 원문은 호출자가 그대로 보관한다.

    ① NFKC 정규화(전각 `５` → `5`) ② 마크다운 링크·이미지를 표시 문자열로 환원
    ③ 보이지 않는 문자 제거(Cf + 변이 선택자 + 결합 격리) ④ 마크다운 강조 기호 제거.
    ②③④ 는 고정점까지 반복한다 — 한 번만 지우면 남은 기호가 새 쌍·새 링크를 만든다.

    이것은 **의미 검증이 아니다**. 화면에 같아 보이게 만드는 문자 장난을 걷어 낼 뿐이고,
    목록 밖 표현은 그대로 통과한다(§7-5 결정 카드 ⑤).
    서로 다른 문자 체계를 섞은 글자는 여기서 고치지 않는다 — `mixed_script_word` 가 거부한다.
    """
    current = unicodedata.normalize("NFKC", text)
    while True:
        without_links = _MARKDOWN_LINK.sub(r"\1", current)
        visible = "".join(ch for ch in without_links if not _is_invisible(ch))
        shorter = _EMPHASIS.sub("", visible)
        if shorter == current:
            return current
        current = shorter


# 한글과 섞이면 거부할 문자 체계. NFKC 는 키릴 `а` 를 한글로 바꾸지 않으므로 정규화로는
# 못 막는다 — 닮은 글자를 끼워 조건 문구를 끊는 입력은 아예 받지 않는다(Codex V1 3차).
_FOREIGN_SCRIPTS = ("CYRILLIC", "GREEK", "ARMENIAN")
_HANGUL = ("HANGUL",)


def _script_of(char: str) -> str | None:
    try:
        name = unicodedata.name(char)
    except ValueError:
        return None
    return name.split(" ", 1)[0]


def mixed_script_word(text: str) -> str | None:
    """한글과 비-라틴 외국 문자 체계가 **한 어절 안에** 섞인 첫 어절. 없으면 None.

    라틴 문자·숫자·부호는 정상 혼용이라 보지 않는다(`Python 개발자`·`Series-B` 는 통과).
    """
    for word in judgement_form(text).split():
        scripts = {script for script in (_script_of(ch) for ch in word) if script is not None}
        if scripts & set(_HANGUL) and scripts & set(_FOREIGN_SCRIPTS):
            return word
    return None


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
    # 경고 전용(§4). `ok` 는 이 값을 보지 않는다 — 오탐으로 발송을 막으면 안 된다.
    multi_position_hint: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.missing and not self.extra_condition and not self.extra_lines


def multi_position_hint(text: str) -> tuple[str, ...]:
    """합본 의심 머리 줄들. 2개 미만이면 빈 튜플 — 한 줄짜리는 경고할 것이 없다."""
    heads = [
        normalized
        for raw in text.splitlines()
        if (normalized := normalize_line(raw))
        and (
            normalized.startswith(_POSITION_HEAD_PREFIXES)
            or _raw_body(raw).startswith(_MARKDOWN_HEADING)
        )
    ]
    return tuple(heads) if len(heads) >= _MULTI_POSITION_MIN else ()


def _matches_condition(line: str) -> bool:
    """조건 문구인가. 반드시 판정용 사본에서 본다 — 원문에는 보이지 않는 갈라짐이 있다."""
    probe = judgement_form(line)
    return any(re.compile(pattern).search(probe) for pattern in EXTRA_CONDITION_PATTERNS)


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
    extra_lines = tuple(
        line for line in rendered_lines if line not in jd_seen and line not in allowed
    )
    extra_condition = tuple(line for line in extra_lines if _matches_condition(line))
    return FidelityReport(
        missing=missing,
        extra_condition=extra_condition,
        jd_line_count=len(jd_lines),
        rendered_line_count=len(rendered_lines),
        extra_lines=extra_lines,
        multi_position_hint=multi_position_hint(jd.text),
    )


def _marker_index(lines: tuple[str, ...], marker: str, label: str) -> int:
    target = normalize_line(marker)
    if not target:
        raise BriefInputError(f"extract_block 의 {label} 는 내용 없는 줄일 수 없다")
    hits = [index for index, line in enumerate(lines) if normalize_line(line) == target]
    if not hits:
        raise BriefInputError(f"extract_block 이 {label} 줄을 찾지 못했다: {target!r}")
    if len(hits) > 1:
        raise BriefInputError(f"extract_block 의 {label} 줄이 {len(hits)}회 나타난다(1회여야 한다)")
    return hits[0]


def extract_block(text: str, start_marker: str, end_marker: str) -> str:
    """두 마커 줄(정규화 비교) 사이의 텍스트만 잘라 낸다.

    Gmail 본문 전체가 아니라 이 블록만 충실도 판정 대상이다(블록 밖 인사·회사 소개는 제외).
    마커가 없거나 2회 이상이거나 끝 마커가 시작 마커보다 앞이면 BriefInputError.
    """
    lines = tuple(text.splitlines())
    start = _marker_index(lines, start_marker, "start_marker")
    end = _marker_index(lines, end_marker, "end_marker")
    if end <= start:
        raise BriefInputError("extract_block 의 end_marker 줄이 start_marker 줄보다 앞에 있다")
    return "".join(f"{line}\n" for line in lines[start + 1 : end])
