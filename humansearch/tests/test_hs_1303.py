"""HS-13.03 — LinkedIn 1,899자 한도와 절 생략·어미 축약 정책을 강제한다.

JD 는 실제 고객사 문장이 아니라 구조만 흉내 낸 **합성** 예시다(회사명·실 JD 문장 0).
§7 D4(길이 = `len()` 코드포인트·개행 포함·`[복사 시작]`/`[복사 끝]` 제외)와
§2 ⓑ(어미 축약 두 방식)·§5(`omittable_sections` 로 지정한 절만 생략 허용)를 함께 묶는다.
§11 변이 정조준 ②(경계 `>` ↔ `>=`)와 이 WU 의 ⓑ(접미 제거 생략)·ⓒ(절 이름 검증 생략)가
아래 시험 중 하나 이상을 FAIL 시켜야 한다.
"""

from __future__ import annotations

import hashlib

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from humansearch.brief import (
    KOREAN_ENDINGS,
    LINKEDIN_FRAME_LINES,
    BriefInputError,
    JdSource,
    check_linkedin,
    core_tokens,
    verify_linkedin_fidelity,
)

# ---------------------------------------------------------------- 합성 JD

JD_HEAD = """\
| 팀 소개
• 합성 예시 조직의 인재 플랫폼 팀은 채용 데이터 품질을 책임집니다
• 팀은 여덟 명이며 절반이 데이터 직무입니다

[자격요건]
• 고객 문제를 관찰하고 가설을 세워 본 경험이 있습니다
• 구조적 사고를 중요하게 생각합니다
• 파이썬으로 데이터 파이프라인을 작성할 수 있습니다

[우대사항]
• 검색 품질 지표를 직접 정의해 본 분을 찾습니다
• 연간 2천만 건의 로그를 다뤄 본 이력이 있습니다
"""

JD_TAIL = """\

혜택 및 복지
• 도서 구입비와 학회 참가비를 지원합니다
• 사내 점심과 저녁 식대를 제공합니다

채용 전형
• 서류 검토 후 직무 인터뷰를 한 차례 진행합니다
• 최종 인터뷰는 팀 리드와 함께 진행합니다
"""

SAMPLE_JD = JD_HEAD + JD_TAIL

FRAME_HEAD = "제목: 합성 예시 조직 인재 플랫폼 엔지니어 포지션 제안\n[복사 시작]\n"
FRAME_TAIL = "[복사 끝]\n[회사 정보 보완]\n문의: 회신으로 알려주세요\n"

THINKING_LINE = "• 구조적 사고를 중요하게 생각합니다\n"
THINKING_SHORT = "• 구조적 사고를 중요하게 생각\n"
PYTHON_LINE = "• 파이썬으로 데이터 파이프라인을 작성할 수 있습니다\n"
CUSTOMER_LINE = "• 고객 문제를 관찰하고 가설을 세워 본 경험이 있습니다\n"
CUSTOMER_NO_NOUN = "• 문제를 관찰하고 가설을 세워 본 경험이 있습니다\n"
SEEK_LINE = "• 검색 품질 지표를 직접 정의해 본 분을 찾습니다\n"
SEEK_NOUNISED = "• 검색 품질 지표를 직접 정의해 본 분을 찾음\n"
FREE_LINE = "• 재택근무 가능\n"
CONDITION_LINE = "• 경력 3년 이상\n"

_ALPHABET = "가나다라마바사아자차카타파하 \nabcXYZ0123·"


def _jd(text: str = SAMPLE_JD) -> JdSource:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return JdSource(text=text, raw_sha256=digest, provided_by="U1")


def _body(block: str = SAMPLE_JD) -> str:
    return f"{FRAME_HEAD}{block}{FRAME_TAIL}"


# ---------------------------------------------------------------- check_linkedin 경계


def test_exactly_1899_codepoints_is_ok() -> None:
    report = check_linkedin("가" * 1899)
    assert report.length == 1899
    assert report.limit == 1899
    assert report.over_by == 0
    assert report.ok is True


def test_1900_codepoints_is_over_by_one() -> None:
    report = check_linkedin("가" * 1900)
    assert report.length == 1900
    assert report.over_by == 1
    assert report.ok is False


def test_newlines_are_counted() -> None:
    report = check_linkedin("가" * 1898 + "\n")
    assert report.length == 1899
    assert report.ok is True
    assert check_linkedin("가" * 1899 + "\n").ok is False


def test_copy_markers_are_not_counted() -> None:
    inner = "가" * 1898
    body = f"[복사 시작]\n{inner}\n[복사 끝]\n"
    report = check_linkedin(body)
    assert len(body) > 1899
    assert report.length == 1899
    assert report.ok is True


@pytest.mark.parametrize("limit", [0, -1, -1899])
def test_non_positive_limit_is_rejected(limit: int) -> None:
    with pytest.raises(BriefInputError):
        check_linkedin("가", limit=limit)


def test_caller_supplied_limit_is_used() -> None:
    report = check_linkedin("가" * 11, limit=10)
    assert report.limit == 10
    assert report.over_by == 1
    assert report.ok is False


@settings(max_examples=250, deadline=None)
@given(
    seed=st.text(alphabet=_ALPHABET, max_size=2500),
    padding=st.integers(min_value=0, max_value=2500),
)
def test_length_property_holds_for_arbitrary_bodies(seed: str, padding: int) -> None:
    text = (seed + "가" * padding)[:2500]
    report = check_linkedin(text)
    assert report.length == len(text)
    assert report.ok == (len(text) <= 1899)
    assert report.over_by == max(0, len(text) - 1899)


# ---------------------------------------------------------------- core_tokens


def test_ending_contraction_keeps_the_same_tokens() -> None:
    assert core_tokens("구조적 사고를 중요하게 생각합니다") == core_tokens("구조적 사고 중요하게 생각")


def test_dropping_a_noun_changes_tokens() -> None:
    assert core_tokens("고객 문제를 관찰하고") != core_tokens("문제를 관찰하고")


def test_dropping_a_number_changes_tokens() -> None:
    assert core_tokens("연간 2천만 건의 로그를 다뤘습니다") != core_tokens("연간 건의 로그를 다뤘습니다")


def test_sentence_punctuation_is_stripped_around_endings() -> None:
    assert core_tokens("생각합니다.") == core_tokens("생각")
    assert core_tokens("[자격요건]") == core_tokens("자격요건")


def test_empty_line_has_no_tokens() -> None:
    assert core_tokens("   •  ") == ()
    assert core_tokens("") == ()


def test_language_constants_are_populated() -> None:
    assert "합니다" in KOREAN_ENDINGS
    assert "습니다" in KOREAN_ENDINGS
    assert "[복사 시작]" in LINKEDIN_FRAME_LINES
    assert "문의:" in LINKEDIN_FRAME_LINES


# ---------------------------------------------------------------- 충실도 양성


def test_verbatim_body_passes() -> None:
    report = verify_linkedin_fidelity(_jd(), _body())
    assert report.missing == ()
    assert report.extra_lines == ()
    assert report.ok is True
    assert report.jd_line_count > 0


def test_ending_contraction_in_body_passes() -> None:
    body = _body().replace(THINKING_LINE, THINKING_SHORT)
    assert THINKING_SHORT in body
    report = verify_linkedin_fidelity(_jd(), body)
    assert report.missing == ()
    assert report.extra_lines == ()
    assert report.ok is True


def test_declared_sections_may_be_omitted() -> None:
    report = verify_linkedin_fidelity(
        _jd(),
        _body(JD_HEAD),
        omittable_sections=("혜택 및 복지", "채용 전형"),
    )
    assert report.missing == ()
    assert report.extra_lines == ()
    assert report.ok is True


# ---------------------------------------------------------------- 충실도 음성


def test_undeclared_section_line_removal_is_missing() -> None:
    body = _body().replace(PYTHON_LINE, "")
    report = verify_linkedin_fidelity(_jd(), body)
    assert "파이썬으로 데이터 파이프라인을 작성할 수 있습니다" in report.missing
    assert report.ok is False


def test_omitting_a_section_does_not_excuse_other_sections() -> None:
    body = _body(JD_HEAD.replace(PYTHON_LINE, ""))
    report = verify_linkedin_fidelity(
        _jd(),
        body,
        omittable_sections=("혜택 및 복지", "채용 전형"),
    )
    assert "파이썬으로 데이터 파이프라인을 작성할 수 있습니다" in report.missing
    assert report.ok is False


def test_dropping_one_noun_is_missing() -> None:
    body = _body().replace(CUSTOMER_LINE, CUSTOMER_NO_NOUN)
    report = verify_linkedin_fidelity(_jd(), body)
    assert "고객 문제를 관찰하고 가설을 세워 본 경험이 있습니다" in report.missing
    assert report.ok is False


def test_unlisted_ending_form_is_not_a_contraction() -> None:
    body = _body().replace(SEEK_LINE, SEEK_NOUNISED)
    report = verify_linkedin_fidelity(_jd(), body)
    assert "검색 품질 지표를 직접 정의해 본 분을 찾습니다" in report.missing
    assert report.ok is False


@pytest.mark.parametrize("name", ["복리후생", "전형 절차", "", "  "])
def test_unknown_omittable_section_name_is_rejected(name: str) -> None:
    with pytest.raises(BriefInputError):
        verify_linkedin_fidelity(_jd(), _body(), omittable_sections=(name,))


def test_free_line_inside_block_is_extra() -> None:
    body = _body(SAMPLE_JD + FREE_LINE)
    report = verify_linkedin_fidelity(_jd(), body)
    assert report.missing == ()
    assert "재택근무 가능" in report.extra_lines
    assert report.ok is False


def test_extra_condition_line_is_reported_on_its_own_axis() -> None:
    body = _body(SAMPLE_JD + CONDITION_LINE)
    report = verify_linkedin_fidelity(_jd(), body)
    assert "경력 3년 이상" in report.extra_condition
    assert "경력 3년 이상" in report.extra_lines
    assert report.ok is False


def test_frame_lines_are_not_counted_as_extra() -> None:
    report = verify_linkedin_fidelity(_jd(), _body())
    assert report.extra_lines == ()
    assert report.rendered_line_count > report.jd_line_count


def test_allowed_extra_removes_a_declared_line() -> None:
    body = _body(SAMPLE_JD + FREE_LINE)
    report = verify_linkedin_fidelity(_jd(), body, allowed_extra=("• 재택근무 가능",))
    assert report.extra_lines == ()
    assert report.ok is True


def test_blank_body_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        verify_linkedin_fidelity(_jd(), "   \n\n")
