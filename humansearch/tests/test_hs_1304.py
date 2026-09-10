"""HS-13.04 — JD 를 사람인·잡코리아용 회사 소개(필드1)·JD 본문(필드2) 2필드로 나눈다.

§5 two_field.py·§6 3절·§9 HS-13.04. 합성 JD 는 `test_hs_1302.GOLDEN_JD` 를 그대로 쓴다
(실제 고객사 JD 문장 0). 필드2 = `section_markers` 로 지정한 절들만(순서는 JD 순서) 원문
그대로 이어 붙인 것이며, 마커 밖 절(예: "혜택 및 복지"·"채용 전형")은 생략이 명시적이다.
"""

from __future__ import annotations

import hashlib

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from test_hs_1302 import GOLDEN_JD

from humansearch.brief import BriefInputError, JdSource
from humansearch.brief.two_field import TwoField, split_two_field

# --------------------------------------------------------------------------- 고정값

MARKERS = ("주요업무", "자격요건", "우대사항")
COMPANY_INTRO = "합성 예시 조직은 검색 품질을 다루는 팀이다. 이직 제안을 위해 포지션을 소개한다."

# 헤딩만 있고 본문 줄이 하나도 없는 절 하나짜리 합성 JD ("빈 절" 시험 전용).
EMPTY_SECTION_JD = "팀 소개\n합성 팀을 소개하는 문장이다.\n빈 절\n"


def _jd(text: str = GOLDEN_JD) -> JdSource:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return JdSource(text=text, raw_sha256=digest, provided_by="U1")


# --------------------------------------------------------------------------- 양성


def test_split_two_field_keeps_only_marker_sections_in_jd_order() -> None:
    result = split_two_field(_jd(), COMPANY_INTRO, section_markers=MARKERS)
    assert isinstance(result, TwoField)
    assert result.company_intro == COMPANY_INTRO
    assert result.report.ok is True

    lines = result.jd_body.splitlines()
    # 지정한 세 절의 제목 줄이 JD 순서(주요업무 → 자격요건 → 우대사항)대로 들어 있다.
    assert lines.index("주요업무") < lines.index("자격요건") < lines.index("우대사항")
    # 지정한 절의 본문 줄은 원문 그대로 들어 있다.
    assert "• 질의 이해 모듈을 개선해 재현율을 끌어올린다." in lines
    assert "• 검색 또는 추천 시스템을 직접 운영해 본 경험이 있다." in lines
    assert "• 벡터 검색 엔진을 운영해 본 경험이 있다." in lines


def test_split_two_field_excludes_non_marker_sections() -> None:
    result = split_two_field(_jd(), COMPANY_INTRO, section_markers=MARKERS)
    lines = result.jd_body.splitlines()
    # 마커에 없는 절("역할"·"혜택 및 복지"·"채용 전형")은 제목·본문 모두 생략된다.
    assert "역할" not in lines
    assert "혜택 및 복지" not in lines
    assert "채용 전형" not in lines
    assert "• 검색 랭킹 모델을 설계하고 오프라인 지표로 검증한다." not in lines
    assert "• 재택과 사무실 근무를 자유롭게 선택할 수 있다." not in lines
    assert "• 서류 검토 후 직무 인터뷰를 한 차례 진행한다." not in lines


def test_split_two_field_marker_order_does_not_change_output() -> None:
    forward = split_two_field(_jd(), COMPANY_INTRO, section_markers=MARKERS)
    reversed_markers = tuple(reversed(MARKERS))
    backward = split_two_field(_jd(), COMPANY_INTRO, section_markers=reversed_markers)
    assert forward.jd_body == backward.jd_body


def test_split_two_field_single_marker() -> None:
    result = split_two_field(_jd(), COMPANY_INTRO, section_markers=("주요업무",))
    lines = result.jd_body.splitlines()
    assert lines[0] == "주요업무"
    assert "자격요건" not in lines
    assert result.report.ok is True


# --------------------------------------------------------------------------- 음성


def test_empty_section_markers_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        split_two_field(_jd(), COMPANY_INTRO, section_markers=())


def test_unknown_section_marker_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        split_two_field(_jd(), COMPANY_INTRO, section_markers=("존재하지 않는 절",))


def test_unknown_section_marker_is_rejected_even_mixed_with_a_valid_one() -> None:
    # 실존 검사가 생략되면(변이 ①) "주요업무" 하나만으로도 필드2 가 채워져 조용히 통과한다.
    # 마커 하나하나가 실존 검사를 통과해야 한다 — 나머지가 유효해도 예외여선 안 된다.
    with pytest.raises(BriefInputError):
        split_two_field(_jd(), COMPANY_INTRO, section_markers=("주요업무", "존재하지 않는 절"))


def test_blank_company_intro_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        split_two_field(_jd(), "   ", section_markers=MARKERS)


def test_html_company_intro_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        split_two_field(_jd(), "<b>합성 예시 조직</b>", section_markers=MARKERS)


def test_company_intro_containing_section_heading_is_rejected() -> None:
    intro = "회사를 소개한다.\n주요업무\n계속 이어지는 소개문이다."
    with pytest.raises(BriefInputError):
        split_two_field(_jd(), intro, section_markers=MARKERS)


def test_all_marker_sections_empty_rejects_blank_jd_body() -> None:
    with pytest.raises(BriefInputError):
        split_two_field(_jd(EMPTY_SECTION_JD), COMPANY_INTRO, section_markers=("빈 절",))


# --------------------------------------------------------------------------- 속성(Hypothesis)


@settings(deadline=None, max_examples=100)
@given(
    st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters=" ",
        ),
        min_size=1,
        max_size=100,
    ).filter(lambda t: bool(t.strip()))
)
def test_company_intro_round_trips_for_arbitrary_tag_free_text(intro: str) -> None:
    result = split_two_field(_jd(), intro, section_markers=MARKERS)
    assert result.company_intro == intro
