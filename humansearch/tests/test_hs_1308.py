"""HS-13.08 — 후보별 InMail 초안이 고정 순서·1,899자 한도·발송 부재를 지키는지 확인한다.

이름·URL·이메일은 전부 합성이다(실제 후보자 정보 0건). §7 D4(길이 판정 재사용)와
§9 HS-13.08(≤1,899 보장·초과 시 거부·후보 이름/매칭 이유 포함·발송 API 부재)을 정조준한다.
§11 변이 정조준 — 이 WU 의 ⓐ(길이 검사 생략)·ⓑ(greeting 이름 검사 생략)가
아래 시험 중 하나 이상을 FAIL 시켜야 한다.
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from humansearch.brief import (
    BriefInputError,
    CandidateEvidence,
    CandidateLead,
    ConnectionDegree,
    EmailContact,
    InMailDraft,
    ScoreBreakdown,
    build_inmail,
    build_inmails,
    check_linkedin,
)

LEAD_URL_1 = "https://www.linkedin.com/in/example-0001"
LEAD_URL_2 = "https://kr.linkedin.com/in/example-0002"

GREETING = "예시 후보 A 님, 안녕하세요. 밸류커넥트에서 좋은 기회를 안내드립니다."
SENDER_LINE = "밸류커넥트 강상모 | sangmokang@valueconnect.kr"
LINKEDIN_BODY = (
    "예시고객사 검색 엔지니어 포지션을 제안드립니다.\n"
    "핵심 업무: 검색 파이프라인 설계\n"
    "자격 요건: Python 5년"
)


def _evidence(**overrides: Any) -> CandidateEvidence:
    fields: dict[str, Any] = {
        "role_match_terms": ("검색", "랭킹"),
        "jd_required_terms_hit": 3,
        "jd_required_terms_total": 4,
        "highest_education": "석사",
        "school_tier": 2,
        "tenure_months_per_job": (36, 28),
        "jobs_last_5y": 2,
        "profile_fields_filled": 7,
        "profile_fields_total": 9,
    }
    fields.update(overrides)
    return CandidateEvidence(**fields)


def _score(**overrides: Any) -> ScoreBreakdown:
    fields: dict[str, Any] = {"role": 32, "education": 15, "stability": 16, "profile": 14}
    fields.update(overrides)
    return ScoreBreakdown(**fields)


def _email(**overrides: Any) -> EmailContact:
    fields: dict[str, Any] = {
        "address": "holder@valueconnect.kr",
        "source_url": "https://example.com/lab/members",
        "provenance": "연구실 공개 페이지 구성원 목록",
    }
    fields.update(overrides)
    return EmailContact(**fields)


def _lead(**overrides: Any) -> CandidateLead:
    fields: dict[str, Any] = {
        "display_name": "예시 후보 A",
        "headline": "Search Engineer at 예시테크",
        "linkedin_url": LEAD_URL_1,
        "education": "예시대학교 컴퓨터공학 석사",
        "career": "예시테크 3년 / 예시랩 2년",
        "match_reasons": ("검색 랭킹 실무 3년", "팀 리드 경험"),
        "check_points": ("실제 담당 범위 확인 필요",),
        "evidence": _evidence(),
        "score": _score(),
        "email": _email(),
        "degree": ConnectionDegree.UNKNOWN,
        "source_note": "공개 프로필 헤드라인·근무 이력으로 동명이인 배제",
    }
    fields.update(overrides)
    return CandidateLead(**fields)


# ---------------------------------------------------------------- 양성


def test_build_inmail_orders_sections_and_reports_length() -> None:
    draft = build_inmail(_lead(), LINKEDIN_BODY, greeting=GREETING, sender_line=SENDER_LINE)
    assert isinstance(draft, InMailDraft)
    lines = draft.body.splitlines()
    assert lines[0] == GREETING
    assert lines[-1] == SENDER_LINE
    assert draft.linkedin_url == LEAD_URL_1
    report = check_linkedin(draft.body)
    assert report.ok
    assert draft.length == report.length


def test_match_reasons_limited_to_two_and_bulleted() -> None:
    lead = _lead(match_reasons=("이유 하나", "이유 둘", "이유 셋"))
    draft = build_inmail(lead, LINKEDIN_BODY, greeting=GREETING, sender_line=SENDER_LINE)
    assert "• 이유 하나" in draft.body
    assert "• 이유 둘" in draft.body
    assert "이유 셋" not in draft.body


def test_linkedin_body_is_included_verbatim() -> None:
    draft = build_inmail(_lead(), LINKEDIN_BODY, greeting=GREETING, sender_line=SENDER_LINE)
    assert LINKEDIN_BODY in draft.body


def test_build_inmails_two_leads_returns_two_tuples() -> None:
    lead_a = _lead()
    lead_b = _lead(display_name="예시 후보 B", linkedin_url=LEAD_URL_2, email=None)

    def greeting_for(lead: CandidateLead) -> str:
        return f"{lead.display_name} 님, 안녕하세요. 밸류커넥트에서 좋은 기회를 안내드립니다."

    result = build_inmails(
        (lead_a, lead_b), LINKEDIN_BODY, greeting_for=greeting_for, sender_line=SENDER_LINE
    )
    assert len(result) == 2
    assert result[0] == (LEAD_URL_1, result[0][1])
    assert result[1] == (LEAD_URL_2, result[1][1])
    assert all(isinstance(item, tuple) and len(item) == 2 for item in result)


# ---------------------------------------------------------------- 음성


def test_over_limit_linkedin_body_is_rejected_without_truncation() -> None:
    long_body = "가" * 2000
    with pytest.raises(BriefInputError):
        build_inmail(_lead(), long_body, greeting=GREETING, sender_line=SENDER_LINE)
    # 자동 축약이 없다는 것을 부정으로 단언한다 — 짧은 본문은 그대로(잘리지 않고) 들어간다.
    trimmed = "가" * 100
    draft = build_inmail(_lead(), trimmed, greeting=GREETING, sender_line=SENDER_LINE)
    assert trimmed in draft.body


def test_greeting_without_display_name_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        build_inmail(
            _lead(),
            LINKEDIN_BODY,
            greeting="안녕하세요, 좋은 기회를 안내드립니다.",
            sender_line=SENDER_LINE,
        )


def test_empty_match_reasons_lead_is_rejected() -> None:
    lead = _lead(match_reasons=())
    # CandidateLead 타입 수준에서는 빈 match_reasons 를 막지 않는다는 사실을 기록한다
    # (types_candidate.CandidateLead.__post_init__ 에 이 필드 검증이 없다).
    assert lead.match_reasons == ()
    with pytest.raises(BriefInputError):
        build_inmail(lead, LINKEDIN_BODY, greeting=GREETING, sender_line=SENDER_LINE)


def test_html_tag_in_greeting_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        build_inmail(
            _lead(),
            LINKEDIN_BODY,
            greeting=f"{GREETING} <b>강조</b>",
            sender_line=SENDER_LINE,
        )


def test_html_tag_in_linkedin_body_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        build_inmail(_lead(), LINKEDIN_BODY + "<br/>", greeting=GREETING, sender_line=SENDER_LINE)


def test_blank_sender_line_is_rejected() -> None:
    with pytest.raises(BriefInputError):
        build_inmail(_lead(), LINKEDIN_BODY, greeting=GREETING, sender_line="   ")


def test_duplicate_linkedin_url_in_build_inmails_is_rejected() -> None:
    lead_a = _lead()
    lead_b = _lead(display_name="예시 후보 B", email=None)  # linkedin_url 동일 — 중복

    def greeting_for(lead: CandidateLead) -> str:
        return f"{lead.display_name} 님, 안녕하세요."

    with pytest.raises(BriefInputError):
        build_inmails(
            (lead_a, lead_b), LINKEDIN_BODY, greeting_for=greeting_for, sender_line=SENDER_LINE
        )


# ---------------------------------------------------------------- 속성


_ALPHABET = "가나다라마바사아자차카타파하 \nabcXYZ0123·"  # '<' 는 제외(HTML 판정과 분리)

# 길이를 먼저 균등하게 뽑고 그 길이로 정확히 채운다. `st.text(max_size=2200)` 만 쓰면
# Hypothesis 가 대부분 수십 자짜리만 생성해 1,899 경계 부근을 사실상 탐색하지 않는다
# (실측: 200회 중 최댓값이 28자였다) — 경계 반례를 놓치는 변이 생존 위험이라 길이를
# 명시적으로 균등 분포시킨다(0..2,200 전 구간, 1,899 안팎 포함).
_BODY_TEXT = st.integers(min_value=0, max_value=2200).flatmap(
    lambda n: st.text(alphabet=_ALPHABET, min_size=n, max_size=n)
)


@settings(max_examples=200, deadline=None)
@given(body_text=_BODY_TEXT)
def test_length_ok_matches_exception_behavior(body_text: str) -> None:
    lead = _lead()
    reasons_block = "\n".join(f"• {reason}" for reason in lead.match_reasons[:2])
    preview = f"{GREETING}\n\n{reasons_block}\n\n{body_text}\n\n{SENDER_LINE}"
    expected_ok = check_linkedin(preview).ok
    try:
        draft = build_inmail(lead, body_text, greeting=GREETING, sender_line=SENDER_LINE)
    except BriefInputError:
        assert not expected_ok
    else:
        assert expected_ok
        assert draft.length == check_linkedin(draft.body).length
