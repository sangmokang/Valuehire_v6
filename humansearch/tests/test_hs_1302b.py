"""HS-13.02b — JD 블록 안에 러너가 끼워 넣은 **모든** 추가 줄을 잡는다.

Codeaudit D-8: 추가 금지가 숫자 조건(연차·학력·연봉)에만 걸려 있어 "재택근무 가능" 같은
비숫자 문장을 끼워 넣어도 PASS 했다. `extra_lines` 는 JD 에 없고 `allowed_extra` 로도
선언되지 않은 줄 전부를 담고, `ok` 는 그 축까지 비어야 참이 된다.
충실도 판정 대상은 Gmail 본문 전체가 아니라 `extract_block` 이 잘라 낸 JD 블록이다.
"""

from __future__ import annotations

import hashlib

import pytest

from humansearch.brief import (
    BriefInputError,
    FidelityReport,
    JdSource,
    extract_block,
    verify_fidelity,
)
from test_hs_1302 import GOLDEN_JD

START_MARKER = "[JD 원문 시작]"
END_MARKER = "[JD 원문 끝]"
FREE_LINE = "• 재택근무 가능"
FREE_CONTENT = "재택근무 가능"
CONDITION_LINE = "• 경력 2년 이상"
CONDITION_CONTENT = "경력 2년 이상"
GREETING = "안녕하세요, 아래 포지션 원문을 공유드립니다.\n\n"
TRAILER = "\n회사 소개와 서치 기준은 아래 절에 이어집니다.\n"


def _jd(text: str = GOLDEN_JD) -> JdSource:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return JdSource(text=text, raw_sha256=digest, provided_by="U1")


def _gmail_body(block: str = GOLDEN_JD) -> str:
    return f"{GREETING}{START_MARKER}\n{block}{END_MARKER}\n{TRAILER}"


# ---------------------------------------------------------------- extra_lines 양성


def test_verbatim_block_has_no_extra_lines() -> None:
    report = verify_fidelity(_jd(), GOLDEN_JD)
    assert report.extra_lines == ()
    assert report.ok is True


def test_allowed_extra_removes_line_from_extra_lines() -> None:
    rendered = GOLDEN_JD + FREE_LINE + "\n"
    report = verify_fidelity(_jd(), rendered, allowed_extra=(FREE_LINE,))
    assert report.extra_lines == ()
    assert report.extra_condition == ()
    assert report.ok is True


# ---------------------------------------------------------------- extra_lines 음성


def test_non_condition_extra_line_is_reported() -> None:
    report = verify_fidelity(_jd(), GOLDEN_JD + FREE_LINE + "\n")
    assert report.extra_lines == (FREE_CONTENT,)
    assert report.extra_condition == ()
    assert report.ok is False


def test_extra_condition_is_a_subset_of_extra_lines() -> None:
    rendered = GOLDEN_JD + FREE_LINE + "\n" + CONDITION_LINE + "\n"
    report = verify_fidelity(_jd(), rendered)
    assert report.extra_lines == (FREE_CONTENT, CONDITION_CONTENT)
    assert report.extra_condition == (CONDITION_CONTENT,)
    assert set(report.extra_condition) <= set(report.extra_lines)
    assert report.ok is False


def test_extra_lines_keep_render_order_and_duplicates() -> None:
    rendered = GOLDEN_JD + FREE_LINE + "\n- 재택근무 가능\n"
    report = verify_fidelity(_jd(), rendered)
    assert report.extra_lines == (FREE_CONTENT, FREE_CONTENT)
    assert report.ok is False


def test_missing_and_extra_lines_are_reported_together() -> None:
    dropped = "• 사내 점심과 저녁 식대를 제공한다."
    rendered = GOLDEN_JD.replace(dropped + "\n", "") + FREE_LINE + "\n"
    report = verify_fidelity(_jd(), rendered)
    assert report.missing == ("사내 점심과 저녁 식대를 제공한다.",)
    assert report.extra_lines == (FREE_CONTENT,)
    assert report.ok is False


def test_report_ok_requires_extra_lines_empty() -> None:
    clean = FidelityReport(
        missing=(),
        extra_condition=(),
        jd_line_count=2,
        rendered_line_count=3,
        extra_lines=(),
    )
    dirty = FidelityReport(
        missing=(),
        extra_condition=(),
        jd_line_count=2,
        rendered_line_count=3,
        extra_lines=(FREE_CONTENT,),
    )
    assert clean.ok is True
    assert dirty.ok is False


# ---------------------------------------------------------------- extract_block


def test_extract_block_returns_only_inner_text() -> None:
    assert extract_block(_gmail_body(), START_MARKER, END_MARKER) == GOLDEN_JD


def test_extract_block_compares_markers_after_normalization() -> None:
    body = f"{GREETING}**[JD 원문 시작]**\n{GOLDEN_JD}•　[JD　원문　끝]\n{TRAILER}"
    assert extract_block(body, START_MARKER, END_MARKER) == GOLDEN_JD


def test_extract_block_output_passes_fidelity() -> None:
    block = extract_block(_gmail_body(), START_MARKER, END_MARKER)
    report = verify_fidelity(_jd(), block)
    assert report.ok is True
    assert report.missing == ()
    assert report.extra_lines == ()


def test_extract_block_catches_line_added_inside_the_block() -> None:
    body = _gmail_body(GOLDEN_JD + FREE_LINE + "\n")
    report = verify_fidelity(_jd(), extract_block(body, START_MARKER, END_MARKER))
    assert report.extra_lines == (FREE_CONTENT,)
    assert report.ok is False


def test_extract_block_ignores_text_outside_the_block() -> None:
    outside = "회사 소개 문장이 블록 밖에 있다."
    tail = "채용 담당 연락처는 블록 밖에 둔다."
    body = f"{GREETING}{outside}\n{START_MARKER}\n{GOLDEN_JD}{END_MARKER}\n{tail}\n"
    report = verify_fidelity(_jd(), extract_block(body, START_MARKER, END_MARKER))
    assert report.ok is True


@pytest.mark.parametrize(
    "body",
    [
        f"{GREETING}{GOLDEN_JD}{END_MARKER}\n",
        f"{GREETING}{START_MARKER}\n{GOLDEN_JD}",
        GREETING + GOLDEN_JD,
    ],
)
def test_extract_block_rejects_missing_marker(body: str) -> None:
    with pytest.raises(BriefInputError):
        extract_block(body, START_MARKER, END_MARKER)


@pytest.mark.parametrize(
    "body",
    [
        f"{START_MARKER}\n{GOLDEN_JD}{START_MARKER}\n{END_MARKER}\n",
        f"{START_MARKER}\n{GOLDEN_JD}{END_MARKER}\n{END_MARKER}\n",
    ],
)
def test_extract_block_rejects_duplicate_marker(body: str) -> None:
    with pytest.raises(BriefInputError):
        extract_block(body, START_MARKER, END_MARKER)


def test_extract_block_rejects_reversed_markers() -> None:
    body = f"{GREETING}{END_MARKER}\n{GOLDEN_JD}{START_MARKER}\n"
    with pytest.raises(BriefInputError):
        extract_block(body, START_MARKER, END_MARKER)


def test_extract_block_rejects_identical_markers() -> None:
    body = f"{START_MARKER}\n{GOLDEN_JD}"
    with pytest.raises(BriefInputError):
        extract_block(body, START_MARKER, START_MARKER)


@pytest.mark.parametrize("marker", ["", "   ", "　", "•"])
def test_extract_block_rejects_blank_marker(marker: str) -> None:
    with pytest.raises(BriefInputError):
        extract_block(_gmail_body(), marker, END_MARKER)
    with pytest.raises(BriefInputError):
        extract_block(_gmail_body(), START_MARKER, marker)


def test_extract_block_rejects_empty_block() -> None:
    body = f"{GREETING}{START_MARKER}\n{END_MARKER}\n{TRAILER}"
    assert extract_block(body, START_MARKER, END_MARKER) == ""
    with pytest.raises(BriefInputError):
        verify_fidelity(_jd(), extract_block(body, START_MARKER, END_MARKER))
