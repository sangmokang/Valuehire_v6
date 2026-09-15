"""PR #83 2차 F83-3 — 회사 절 면제를 "렌더러가 만들었다" 에서 **금액 필드 + 금액 형식**으로 좁힌다.

Codex V1 반증: 1차 수정은 회사 리서치 절의 줄이 `render_company_research` 결과와 같으면
조건 검사를 통째로 건너뛰었다. `CompanyBrief.revenue=Claim('경력 5년 이상', ('I1',))` 처럼
조건을 구조화 필드에 먼저 넣으면 `- 매출: 경력 5년 이상 [I1]` 이 허용 집합에 들어가
패킷과 JSON 왕복을 통과했다("F83-3-BYPASS True True").

계약(v7 §2 I-c 개정): 회사 절 줄에도 채용 조건 검사를 계속 적용한다. 면제는 **금액 필드
(매출·영업이익·누적 투자금)에서 렌더한 줄 중 값이 금액 형식에 맞는 줄**로만 좁힌다.

회사 자료는 전부 합성이다(test_hs_1305 fixture 재사용).
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest
from test_hs_1305 import COMPANY, TODAY, _draft, _recipients

from humansearch.brief import (
    BriefInputError,
    Claim,
    CompanyBrief,
    ExecProfile,
    SearchPacket,
    TeamMail,
    from_json,
    packet_id,
    to_json,
)
from humansearch.brief.mail import compose_brief_mail

# 조건 정규식이 실제로 보는 문구만 쓴다. `대졸 필수`·`재택근무 가능` 은 이 정규식이 모르는
# 문구라 회사 절에서도 잡히지 않는다 — 보고서의 잔여 위험 항목으로 따로 적었다.
CONDITIONS: tuple[str, ...] = ("경력 5년 이상", "연봉 5천 이상")

SINGLE_FIELDS: tuple[str, ...] = (
    "legal_name",
    "founded",
    "ceo",
    "headquarters",
    "headcount",
    "revenue",
    "operating_profit",
    "funding_stage",
    "funding_total",
)
LIST_FIELDS: tuple[str, ...] = ("products", "history", "news", "youtube")

RENDERED_AMOUNT_LINE = "- 매출: 300억 원 [I1]"
UNRENDERED_AMOUNT_LINE = "- 매출: 999억 원 [I1]"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _packet(company: CompanyBrief = COMPANY, body: str | None = None) -> SearchPacket:
    draft = _draft(company=company)
    mail = compose_brief_mail(draft, _recipients(), TODAY, first_live=False)
    text = mail.body if body is None else body
    return SearchPacket(
        packet_id=packet_id(draft.position, draft.jd),
        created_on=TODAY,
        position=draft.position,
        jd=draft.jd,
        company=company,
        jd_packet=draft.jd_packet,
        candidates=draft.candidates,
        mail=TeamMail(
            subject=mail.subject,
            to=tuple(mail.to),
            cc=tuple(mail.cc),
            body=text,
            body_sha256=_sha256(text),
        ),
        boolean_queries=draft.boolean_queries,
        inmails=draft.inmails,
        search_filters=draft.search_filters,
    )


# ---------------------------------------------------------------- 양성: 정상 금액


def test_a_normal_company_brief_still_becomes_a_packet() -> None:
    packet = _packet()
    restored = from_json(to_json(packet))
    assert RENDERED_AMOUNT_LINE in restored.mail.body.splitlines()


def test_every_amount_field_with_an_amount_shaped_value_passes() -> None:
    company = replace(
        COMPANY,
        revenue=Claim("1,250억 원", ("I1",)),
        operating_profit=Claim("50억 원", ("I1",)),
        funding_total=Claim("3,000만 원", ("I1",)),
    )
    lines = _packet(company).mail.body.splitlines()
    assert "- 매출: 1,250억 원 [I1]" in lines
    assert "- 영업이익: 50억 원 [I1]" in lines
    assert "- 누적 투자금: 3,000만 원 [I1]" in lines


# ---------------------------------------------------------------- 음성: 조건 주입


@pytest.mark.parametrize("field", SINGLE_FIELDS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_a_condition_in_any_single_company_field_is_rejected(field: str, condition: str) -> None:
    company = replace(COMPANY, **{field: Claim(condition, ("I1",))})
    with pytest.raises(BriefInputError):
        _packet(company)


@pytest.mark.parametrize("field", LIST_FIELDS)
@pytest.mark.parametrize("condition", CONDITIONS)
def test_a_condition_in_any_company_list_field_is_rejected(field: str, condition: str) -> None:
    company = replace(COMPANY, **{field: (Claim(condition, ("C1",)),)})
    with pytest.raises(BriefInputError):
        _packet(company)


@pytest.mark.parametrize("condition", CONDITIONS)
def test_a_condition_in_a_c_level_summary_is_rejected(condition: str) -> None:
    company = replace(
        COMPANY,
        c_level=(
            ExecProfile(
                name_role="합성 CTO",
                linkedin_url="https://www.linkedin.com/in/example-cto",
                summary=Claim(condition, ("C1",)),
            ),
        ),
    )
    with pytest.raises(BriefInputError):
        _packet(company)


def test_json_roundtrip_also_rejects_an_injected_condition() -> None:
    """조립이 막히므로 왕복도 막힌다 — 저장본으로 우회할 길이 없다."""
    company = replace(COMPANY, revenue=Claim("경력 5년 이상", ("I1",)))
    with pytest.raises(BriefInputError):
        from_json(to_json(_packet(company)))


# ---------------------------------------------------------------- 금액 형식 경계


def test_an_amount_shaped_value_in_a_non_amount_field_is_not_exempt() -> None:
    """금액처럼 보여도 금액 필드가 아니면 면제하지 않는다."""
    company = replace(COMPANY, headcount=Claim("300억 원", ("C1",)))
    with pytest.raises(BriefInputError):
        _packet(company)


def test_an_amount_line_the_company_brief_did_not_render_is_rejected() -> None:
    body = _packet().mail.body.replace(RENDERED_AMOUNT_LINE, UNRENDERED_AMOUNT_LINE, 1)
    assert UNRENDERED_AMOUNT_LINE in body.splitlines()
    with pytest.raises(BriefInputError):
        _packet(body=body)


def test_a_hiring_condition_inserted_into_the_company_section_is_still_rejected() -> None:
    body = _packet().mail.body.replace(
        "2. 매출·영업이익·투자", "2. 매출·영업이익·투자\n- 경력 5년 이상", 1
    )
    with pytest.raises(BriefInputError):
        _packet(body=body)
