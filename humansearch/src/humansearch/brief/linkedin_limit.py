"""HS-13.03 — LinkedIn InMail 1,899자 한도와 절 생략·어미 축약 정책을 판정한다.

§7 D4: 길이는 Python `len()`(코드포인트) 기준이고 개행을 포함하며, 프레임 줄인
`[복사 시작]`/`[복사 끝]` 은 세지 않는다. 한도 값 자체는 이 모듈이 소유하지 않는다 —
호출자가 `limit` 로 주입한다(정책 파일이 붙으면 그쪽이 정본이 된다).

§2 ⓑ: 본문을 줄이는 방식은 ① 호출자가 이름으로 지정한 절 통째 생략
② 어미·조사만 떼는 축약 두 가지뿐이다. 명사·숫자·영문 토큰이 하나라도 빠지면 누락이다.

시계·파일·네트워크 접근 0, 전부 순수 함수다. 판정 단위·정규화는 `jd_fidelity` 를 그대로 쓴다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .jd_fidelity import (
    EXTRA_CONDITION_PATTERNS,
    FidelityReport,
    Section,
    content_lines,
    normalize_line,
    split_sections,
)
from .policy import policy
from .types import BriefInputError, JdSource

__all__ = [
    "KOREAN_ENDINGS",
    "LINKEDIN_FRAME_LINES",
    "LinkedInReport",
    "check_linkedin",
    "core_tokens",
    "verify_linkedin_fidelity",
]

# 길이 계산에서 빼는 복사 마커. 러너가 붙였다 떼는 프레임이지 본문이 아니다(§7 D4).
_COPY_MARKERS: tuple[str, ...] = ("[복사 시작]", "[복사 끝]")

# 본문 밖 프레임 줄 목록. 제목·문의는 실제 내용이 뒤따르므로 접두로 허용하되,
# 복사/회사정보 마커는 정확히 같은 줄만 JD 내용 줄에서 제외한다.
#   "제목:"          — InMail 제목 줄
#   "[복사 시작]"    — 복사 구간 시작
#   "[복사 끝]"      — 복사 구간 끝
#   "[회사 정보 보완]" — 러너가 덧붙이는 회사 사실 절의 머리
#   "문의:"          — 회신 안내 줄
LINKEDIN_FRAME_LINES: tuple[str, ...] = (
    "제목:",
    "[복사 시작]",
    "[복사 끝]",
    "[회사 정보 보완]",
    "문의:",
)

# 축약으로 인정할 어미·조사·존칭 접미. 명사·숫자·영문은 여기 없다(빠지면 누락이다).
KOREAN_ENDINGS: tuple[str, ...] = (
    # 종결 어미(하십시오체·해요체)
    "기다립니다",
    "있습니다",
    "없습니다",
    "찾습니다",
    "했습니다",
    "습니다",
    "입니다",
    "합니다",
    "됩니다",
    "이에요",
    "있어요",
    "없어요",
    "예요",
    "해요",
    "어요",
    "여요",
    # 연결 어미
    "하는",
    "하신",
    "하실",
    "하고",
    "하며",
    "하여",
    "되어",
    "이며",
    "이고",
    # 조사·존칭 접미
    "으로",
    "에서",
    "에게",
    "께서",
    "로",
    "을",
    "를",
    "이",
    "가",
    "은",
    "는",
    "의",
    "와",
    "과",
    "도",
    "만",
    "분",
    "님",
)
_ENDINGS_LONGEST_FIRST: tuple[str, ...] = tuple(sorted(KOREAN_ENDINGS, key=len, reverse=True))

# 토큰 양끝에서 지우는 문장부호.
_PUNCTUATION = ".,:;!?~·…()[]\"'"


@dataclass(frozen=True)
class LinkedInReport:
    """LinkedIn 본문 길이 판정. `length` 는 복사 마커 줄을 뺀 코드포인트 수다."""

    length: int
    limit: int
    ok: bool
    over_by: int


def _is_copy_marker(line: str) -> bool:
    normalized = normalize_line(line)
    return any(normalized == normalize_line(marker) for marker in _COPY_MARKERS)


def check_linkedin(body: str, *, limit: int | None = None) -> LinkedInReport:
    """본문 길이가 한도 이내인지 판정한다(1,899 = 합격, 1,900 = 불합격).

    개행을 포함한 코드포인트 수이며 `[복사 시작]`/`[복사 끝]` 줄만 빼고 센다.
    한도가 0 이하면 판정 자체가 성립하지 않으므로 거부한다.
    """
    if limit is None:
        limit = policy().linkedin_inmail_max_chars
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise BriefInputError("check_linkedin 의 limit 는 정수여야 한다")
    if limit <= 0:
        raise BriefInputError(f"check_linkedin 의 limit 는 1 이상이어야 한다: {limit}")
    counted = "".join(
        piece for piece in body.splitlines(keepends=True) if not _is_copy_marker(piece)
    )
    length = len(counted)
    return LinkedInReport(
        length=length,
        limit=limit,
        ok=length <= limit,
        over_by=max(0, length - limit),
    )


def _strip_ending(token: str) -> str:
    """목록의 접미를 가장 긴 것부터 **한 번만** 뗀다."""
    for ending in _ENDINGS_LONGEST_FIRST:
        if token.endswith(ending):
            return token[: len(token) - len(ending)]
    return token


def core_tokens(line: str) -> tuple[str, ...]:
    """어미·조사를 뗀 핵심 토큰 열. 명사·숫자·영문이 빠지면 결과가 달라진다.

    문장부호는 접미를 떼기 **전후 모두** 양끝에서 지운다. 스펙 §2 ⓑ 의 순서(접미 → 부호)만
    적용하면 "생각합니다." 처럼 마침표가 붙은 실제 JD 줄에서 접미가 남아 축약을 놓친다.
    """
    normalized = normalize_line(line)
    if not normalized:
        return ()
    tokens: list[str] = []
    for raw in normalized.split():
        stem = _strip_ending(raw.strip(_PUNCTUATION)).strip(_PUNCTUATION)
        if stem:
            tokens.append(stem)
    return tuple(tokens)


_HEADING_TAIL = re.compile(r"[\s:：\.\-–—]+$")


def _canonical_heading(text: str) -> str:
    """절 제목 비교용 — 끝의 콜론·마침표·대시·공백을 지우고 안쪽 공백을 없앤다(`주요업무:`·`주요 업무` = `주요업무`)."""
    return _HEADING_TAIL.sub("", normalize_line(text)).replace(" ", "")


def _is_frame_line(line: str) -> bool:
    normalized = normalize_line(line)
    prefix_allowed = tuple(
        normalize_line(prefix) for prefix in LINKEDIN_FRAME_LINES if prefix in {"제목:", "문의:"}
    )
    exact_allowed = {
        normalize_line(prefix)
        for prefix in LINKEDIN_FRAME_LINES
        if prefix not in {"제목:", "문의:"}
    }
    return normalized.startswith(prefix_allowed) or normalized in exact_allowed


def _matches_condition(line: str) -> bool:
    return any(re.compile(pattern).search(line) for pattern in EXTRA_CONDITION_PATTERNS)


def _normalized_names(names: tuple[str, ...], field: str) -> tuple[str, ...]:
    normalized: list[str] = []
    for name in names:
        text = normalize_line(name)
        if not text:
            raise BriefInputError(f"{field} 에 내용 없는 값이 있다(공백·글머리표뿐)")
        normalized.append(text)
    return tuple(normalized)


def _omitted_headings(sections: tuple[Section, ...], names: tuple[str, ...]) -> frozenset[str]:
    """생략 지정 절 이름이 JD 절 heading 과 정규화 후 정확 일치하는지 확인한다."""
    headings = frozenset(section.heading for section in sections if section.heading)
    chosen: set[str] = set()
    for name in _normalized_names(names, "omittable_sections"):
        if name not in headings:
            raise BriefInputError(f"omittable_sections 의 절 이름이 JD 에 없다: {name!r}")
        chosen.add(name)
    return frozenset(chosen)


def _token_sets(lines: tuple[str, ...]) -> frozenset[tuple[str, ...]]:
    return frozenset(tokens for tokens in (core_tokens(line) for line in lines) if tokens)


def _covered(
    line: str,
    exact: frozenset[str],
    tokens: frozenset[tuple[str, ...]],
) -> bool:
    """(a) 정규화 동일 또는 (b) 핵심 토큰 열 동일이면 덮인 것으로 본다."""
    if line in exact:
        return True
    line_tokens = core_tokens(line)
    return bool(line_tokens) and line_tokens in tokens


def verify_linkedin_fidelity(
    jd: JdSource,
    body: str,
    *,
    omittable_sections: tuple[str, ...] = (),
    allowed_extra: tuple[str, ...] = (),
) -> FidelityReport:
    """지정 절 생략과 어미 축약만 허용하고 그 밖의 누락·추가를 잡아낸다.

    `omittable_sections` 는 JD 절 heading 과 정규화 후 정확 일치해야 한다(오타는 거부).
    `allowed_extra` 는 호출자가 명시적으로 승인한 추가 줄이다. 프레임 줄
    (`LINKEDIN_FRAME_LINES` 접두)은 애초에 판정 대상이 아니다.
    `jd_line_count` 는 **검사 대상으로 남은** JD 줄 수, `rendered_line_count` 는 본문의
    전체 내용 줄 수(프레임 포함)다.
    """
    if not body.strip():
        raise BriefInputError("verify_linkedin_fidelity 의 body 는 공백만일 수 없다")
    sections = split_sections(jd.text)
    omitted = _omitted_headings(sections, omittable_sections)
    core = frozenset(_canonical_heading(name) for name in policy().linkedin_core_sections)
    blocked = sorted(name for name in omitted if _canonical_heading(name) in core)
    if blocked:
        raise BriefInputError(
            f"핵심 절은 LinkedIn 판에서 생략할 수 없다(계약 linkedin_core_sections): {blocked[0]!r}"
        )
    if omitted and not any(
        section.heading and _canonical_heading(section.heading) in core for section in sections
    ):
        # 인식된 핵심 절이 0 인 JD 에서 생략을 허용하면 무엇이 핵심인지 모른 채 본문이 빠진다 — fail-closed(Codex 12차)
        raise BriefInputError(
            "JD 에서 계약 핵심 절(linkedin_core_sections)을 하나도 인식하지 못했다 — 절 생략을 허용하지 않는다"
        )
    checked: list[str] = []
    for section in sections:
        if section.heading and section.heading in omitted:
            continue
        if section.heading:
            checked.append(section.heading)
        checked.extend(section.lines)

    jd_all = content_lines(jd.text) + tuple(s.heading for s in sections if s.heading)
    jd_exact = frozenset(jd_all)
    jd_tokens = _token_sets(jd_all)

    if not checked:
        raise BriefInputError(
            "생략 뒤 검사 대상 JD 줄이 0 이다 — 모든 절을 생략한 LinkedIn 판은 산출물이 아니다"
        )
    body_all = content_lines(body)
    # 프레임 줄이라도 채용 조건 문구를 품으면 면제하지 않는다(Codex 12차: `문의: 경력 10년 이상만`)
    body_lines = tuple(
        line for line in body_all if not (_is_frame_line(line) and not _matches_condition(line))
    )
    if not body_lines:
        raise BriefInputError("LinkedIn 본문에 프레임 줄 외 내용 줄이 0 이다")
    body_exact = frozenset(body_lines)
    body_tokens = _token_sets(body_lines)

    allowed = frozenset(_normalized_names(allowed_extra, "allowed_extra"))
    missing = tuple(line for line in checked if not _covered(line, body_exact, body_tokens))
    extra_lines = tuple(
        line
        for line in body_lines
        if line not in allowed and not _covered(line, jd_exact, jd_tokens)
    )
    return FidelityReport(
        missing=missing,
        extra_condition=tuple(line for line in extra_lines if _matches_condition(line)),
        jd_line_count=len(checked),
        rendered_line_count=len(body_all),
        extra_lines=extra_lines,
    )
