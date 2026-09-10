"""HS-13.02 — JD 원문의 내용 줄이 렌더링 결과에 그대로 남아 있는지 판정한다.

황금 표본은 실제 고객사 JD 가 아니라 구조만 흉내 낸 **합성** JD 다(회사명·실 문장 0).
§7 D5(판정 단위 = 내용 줄)와 §11 변이 정조준 ①(missing 을 항상 () 로 만드는 변이)이
이 파일의 음성 시험에 걸리도록 구성한다.
"""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from humansearch.brief import (
    EXTRA_CONDITION_PATTERNS,
    BriefInputError,
    FidelityReport,
    JdSource,
    Section,
    content_lines,
    normalize_line,
    split_sections,
    verify_fidelity,
)

GOLDEN_JD = """\
| 팀 소개
합성 예시 조직의 검색 플랫폼 팀은 사내 데이터 검색 품질을 책임진다.
• 팀 규모는 열두 명이며 백엔드와 머신러닝 인력이 섞여 있다.
• 분기마다 검색 품질 지표를 공개하고 개선 과제를 정한다.

[역할]
• 검색 랭킹 모델을 설계하고 오프라인 지표로 검증한다.
• 색인 파이프라인의 지연 구간을 찾아 개선한다.
• 실험 설계와 결과 해석을 직접 주도한다.

주요업무
• 질의 이해 모듈을 개선해 재현율을 끌어올린다.
• 색인 스키마를 정리하고 마이그레이션 계획을 세운다.
• 검색 로그를 분석해 실패 질의를 분류한다.
• 온라인 실험 지표를 정의하고 대시보드를 만든다.

자격요건
• 검색 또는 추천 시스템을 직접 운영해 본 경험이 있다.
• 파이썬으로 데이터 파이프라인을 작성할 수 있다.
• 분산 색인 시스템의 동작 원리를 설명할 수 있다.
• 지표를 근거로 의사결정을 설득한 사례가 있다.

우대사항
• 벡터 검색 엔진을 운영해 본 경험이 있다.
• 오픈 소스 검색 엔진에 기여한 이력이 있다.
• 대규모 로그 처리 도구를 다뤄 본 경험이 있다.

혜택 및 복지
• 재택과 사무실 근무를 자유롭게 선택할 수 있다.
• 도서 구입비와 학회 참가비를 지원한다.
• 사내 점심과 저녁 식대를 제공한다.

채용 전형
• 서류 검토 후 직무 인터뷰를 한 차례 진행한다.
• 최종 인터뷰는 팀 리드와 함께 진행한다.
"""

GOLDEN_HEADINGS = (
    "팀 소개",
    "역할",
    "주요업무",
    "자격요건",
    "우대사항",
    "혜택 및 복지",
    "채용 전형",
)
GOLDEN_CONTENT_COUNT = 29
GOLDEN_SECTION_LINE_COUNT = 22
DROPPED_LINE = "• 검색 로그를 분석해 실패 질의를 분류한다."
DROPPED_CONTENT = "검색 로그를 분석해 실패 질의를 분류한다."
EXTRA_CONDITION_LINE = "• 경력 2년 이상"
EXTRA_CONDITION_CONTENT = "경력 2년 이상"


def _jd(text: str = GOLDEN_JD) -> JdSource:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return JdSource(text=text, raw_sha256=digest, provided_by="U1")


def _emphasize(text: str) -> str:
    return "\n".join(f"**{line}**" if line.strip() else line for line in text.splitlines())


# ---------------------------------------------------------------- 양성(정규화 동치)


def test_golden_jd_verbatim_passes() -> None:
    report = verify_fidelity(_jd(), GOLDEN_JD)
    assert report.missing == ()
    assert report.extra_condition == ()
    assert report.ok is True
    assert report.jd_line_count == GOLDEN_CONTENT_COUNT
    assert report.rendered_line_count == GOLDEN_CONTENT_COUNT


def test_bullet_style_substitution_passes() -> None:
    report = verify_fidelity(_jd(), GOLDEN_JD.replace("•", "-"))
    assert report.ok is True
    assert report.rendered_line_count == GOLDEN_CONTENT_COUNT


def test_indentation_and_blank_lines_pass() -> None:
    rendered = "\n\n".join(f"      {line}" for line in GOLDEN_JD.splitlines())
    report = verify_fidelity(_jd(), rendered)
    assert report.ok is True
    assert report.rendered_line_count == GOLDEN_CONTENT_COUNT


def test_markdown_emphasis_passes() -> None:
    report = verify_fidelity(_jd(), _emphasize(GOLDEN_JD))
    assert report.ok is True


def test_fullwidth_space_and_tab_pass() -> None:
    fullwidth = verify_fidelity(_jd(), GOLDEN_JD.replace(" ", "　"))
    tabbed = verify_fidelity(_jd(), GOLDEN_JD.replace(" ", "\t"))
    assert fullwidth.ok is True
    assert tabbed.ok is True


# ---------------------------------------------------------------- 음성(변이 정조준)


def test_dropped_content_line_is_reported_as_missing() -> None:
    rendered = GOLDEN_JD.replace(DROPPED_LINE + "\n", "")
    report = verify_fidelity(_jd(), rendered)
    assert report.missing == (DROPPED_CONTENT,)
    assert report.ok is False
    assert report.rendered_line_count == GOLDEN_CONTENT_COUNT - 1


def test_reordered_words_line_is_reported_as_missing() -> None:
    shuffled = "• 실패 질의를 분류한다 검색 로그를 분석해."
    rendered = GOLDEN_JD.replace(DROPPED_LINE, shuffled)
    report = verify_fidelity(_jd(), rendered)
    assert report.missing == (DROPPED_CONTENT,)
    assert report.ok is False
    assert report.rendered_line_count == GOLDEN_CONTENT_COUNT


def test_added_experience_condition_is_reported() -> None:
    report = verify_fidelity(_jd(), GOLDEN_JD + EXTRA_CONDITION_LINE + "\n")
    assert report.missing == ()
    assert report.extra_condition == (EXTRA_CONDITION_CONTENT,)
    assert report.ok is False


def test_allowed_extra_permits_the_same_condition_line() -> None:
    report = verify_fidelity(
        _jd(),
        GOLDEN_JD + EXTRA_CONDITION_LINE + "\n",
        allowed_extra=(EXTRA_CONDITION_LINE,),
    )
    assert report.extra_condition == ()
    assert report.ok is True


def test_non_condition_extra_line_is_not_reported() -> None:
    rendered = GOLDEN_JD + "• 지원 절차는 담당자가 개별 안내한다.\n"
    report = verify_fidelity(_jd(), rendered)
    assert report.extra_condition == ()
    assert report.ok is True


@pytest.mark.parametrize(
    "condition",
    [
        "경력 5년 이상 보유한 분을 찾는다",
        "3~5년 차 엔지니어를 우대한다",
        "신입 지원도 가능하다",
        "석사 학위 이상 보유자를 우대한다",
        "연봉은 면접 후 협의한다",
        "성과급 1,200만 원을 별도로 지급한다",
        "누적 투자 300억 규모를 유치했다",
    ],
)
def test_extra_condition_patterns_catch_condition_lines(condition: str) -> None:
    report = verify_fidelity(_jd(), GOLDEN_JD + "• " + condition + "\n")
    assert report.extra_condition == (condition,)
    assert report.ok is False


@pytest.mark.parametrize("rendered", ["", "   ", "\n\t\n", "　"])
def test_blank_rendered_is_rejected(rendered: str) -> None:
    with pytest.raises(BriefInputError):
        verify_fidelity(_jd(), rendered)


@pytest.mark.parametrize("blank", ["", "  ", "　", "•", "- "])
def test_blank_allowed_extra_is_rejected(blank: str) -> None:
    with pytest.raises(BriefInputError):
        verify_fidelity(_jd(), GOLDEN_JD, allowed_extra=(blank,))


# ---------------------------------------------------------------- 정규화·절 분해


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("• 항목 하나", "항목 하나"),
        ("- 항목 하나", "항목 하나"),
        ("  ▪  항목 하나  ", "항목 하나"),
        ("> | • 항목 하나", "항목 하나"),
        ("**강조된 항목**", "강조된 항목"),
        ("`코드` 항목", "코드 항목"),
        ("__밑줄__ 항목", "밑줄 항목"),
        ("항목　하나\t둘", "항목 하나 둘"),
        ("항목    하나", "항목 하나"),
        ("1) 번호 항목", "1) 번호 항목"),
        ("A. 번호 항목", "A. 번호 항목"),
        ("※ 주의 항목", "※ 주의 항목"),
        ("", ""),
        ("   ", ""),
        ("• - * ·", ""),
    ],
)
def test_normalize_line_table(raw: str, expected: str) -> None:
    assert normalize_line(raw) == expected


def test_content_lines_keeps_order_and_duplicates() -> None:
    text = "• 같은 줄입니다\n\n• 다른 줄입니다\n- 같은 줄입니다\n   \n"
    assert content_lines(text) == ("같은 줄입니다", "다른 줄입니다", "같은 줄입니다")


def test_split_sections_finds_seven_headings_in_order() -> None:
    sections = split_sections(GOLDEN_JD)
    assert tuple(section.heading for section in sections) == GOLDEN_HEADINGS
    benefits = next(section for section in sections if section.heading == "혜택 및 복지")
    assert benefits.lines == (
        "재택과 사무실 근무를 자유롭게 선택할 수 있다.",
        "도서 구입비와 학회 참가비를 지원한다.",
        "사내 점심과 저녁 식대를 제공한다.",
    )
    assert len(benefits.lines) == 3
    assert sum(len(section.lines) for section in sections) == GOLDEN_SECTION_LINE_COUNT


def test_split_sections_puts_preamble_under_empty_heading() -> None:
    text = "머리말 한 줄이 제목보다 먼저 나온다.\n• 머리말 글머리표 줄이다.\n주요업무\n• 첫 번째 업무를 수행한다.\n"
    sections = split_sections(text)
    assert sections[0].heading == ""
    assert sections[0].lines == ("머리말 한 줄이 제목보다 먼저 나온다.", "머리말 글머리표 줄이다.")
    assert sections[1] == Section(heading="주요업무", lines=("첫 번째 업무를 수행한다.",))


def test_split_sections_is_deterministic() -> None:
    assert split_sections(GOLDEN_JD) == split_sections(GOLDEN_JD)


def test_section_and_report_are_frozen() -> None:
    section = Section(heading="주요업무", lines=("한 줄",))
    report = FidelityReport(missing=(), extra_condition=(), jd_line_count=1, rendered_line_count=1)
    with pytest.raises(FrozenInstanceError):
        section.heading = "다른 제목"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.jd_line_count = 2  # type: ignore[misc]


def test_report_ok_requires_both_axes_empty() -> None:
    base = FidelityReport(missing=(), extra_condition=(), jd_line_count=2, rendered_line_count=2)
    assert base.ok is True
    assert FidelityReport(("빠진 줄",), (), 2, 2).ok is False
    assert FidelityReport((), ("경력 3년 이상",), 2, 2).ok is False


def test_extra_condition_patterns_are_non_empty_strings() -> None:
    assert len(EXTRA_CONDITION_PATTERNS) >= 7
    assert all(isinstance(pattern, str) and pattern.strip() for pattern in EXTRA_CONDITION_PATTERNS)


# ---------------------------------------------------------------- 속성(Hypothesis)


@settings(deadline=None, max_examples=200)
@given(st.text(max_size=200))
def test_content_lines_is_idempotent(text: str) -> None:
    lines = content_lines(text)
    assert content_lines("\n".join(lines)) == lines


_JD_ALPHABET = "가나다라마바사아자차 \t　•-*·–—▪■○●◦>|[]`_.!?。0123456789년이상경력신입※1)A\n"


@settings(deadline=None, max_examples=200)
@given(st.text(alphabet=_JD_ALPHABET, min_size=1, max_size=200).filter(lambda t: bool(t.strip())))
def test_jd_always_matches_itself(text: str) -> None:
    jd = _jd(text)
    report = verify_fidelity(jd, text)
    assert report.missing == ()
    assert report.jd_line_count == report.rendered_line_count
