"""PR #83 F83-3 — 회사 리서치 절의 금액 줄을 채용 조건으로 오인해 거부하지 않는다.

Codex 13차 반례: 렌더러가 CompanyBrief 에서 만든 정상 줄 `- 매출: 300억 원 [I1]` 이
`\\d[\\d,]*\\s*억` 패턴에 걸려 "JD 블록 밖에 채용 조건이 끼었다" 로 거부됐다.
정상 draft → compose_brief_mail → SearchPacket 경로가 통째로 막힌다.

계약(v7 §2 I-c): 회사 리서치 절이 CompanyBrief 의 검증된 렌더링 결과와 일치하면
채용 조건으로 오인해 거부하지 않는다. 패턴을 통째로 빼는 방식은 음성 대조군에서 막힌다.

회사·후보 자료는 전부 합성이다(test_hs_1305 의 합성 fixture 재사용).
"""

from __future__ import annotations

import hashlib

import pytest
from test_hs_1305 import TODAY, _draft, _recipients

from humansearch.brief import (
    BriefInputError,
    SearchPacket,
    TeamMail,
    from_json,
    packet_id,
    to_json,
)
from humansearch.brief.mail import compose_brief_mail

RENDERED_AMOUNT_LINE = "- 매출: 300억 원 [I1]"
SUBSECTION_HEAD = "2. 매출·영업이익·투자"
HIRING_CONDITION = "- 경력 5년 이상"
UNRENDERED_AMOUNT_LINE = "- 매출: 999억 원 [I1]"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _mail_body() -> str:
    draft = _draft()
    return compose_brief_mail(draft, _recipients(), TODAY, first_live=False).body


def _packet(body: str | None = None) -> SearchPacket:
    draft = _draft()
    mail = compose_brief_mail(draft, _recipients(), TODAY, first_live=False)
    text = mail.body if body is None else body
    return SearchPacket(
        packet_id=packet_id(draft.position, draft.jd),
        created_on=TODAY,
        position=draft.position,
        jd=draft.jd,
        company=draft.company,
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


# ---------------------------------------------------------------- 양성: 정상 경로


def test_the_rendered_company_amount_line_is_in_the_mail_body() -> None:
    assert RENDERED_AMOUNT_LINE in _mail_body().splitlines()


def test_a_normal_draft_becomes_a_packet_and_survives_json_roundtrip() -> None:
    """정상 draft → compose_brief_mail → SearchPacket → to_json/from_json 왕복."""
    packet = _packet()
    restored = from_json(to_json(packet))
    assert RENDERED_AMOUNT_LINE in restored.mail.body.splitlines()
    assert restored.mail.body_sha256 == packet.mail.body_sha256


# ---------------------------------------------------------------- 음성 대조군


def test_a_hiring_condition_inserted_into_the_company_section_is_still_rejected() -> None:
    """회사 절이라도 렌더링 결과가 아닌 채용 조건 줄은 여전히 거부한다."""
    body = _mail_body().replace(
        SUBSECTION_HEAD, f"{SUBSECTION_HEAD}\n{HIRING_CONDITION}", 1
    )
    assert HIRING_CONDITION in body.splitlines()
    with pytest.raises(BriefInputError):
        _packet(body)


def test_an_amount_line_the_company_brief_did_not_render_is_rejected() -> None:
    """금액 패턴을 통째로 빼면 통과해 버릴 줄 — CompanyBrief 와 대조하므로 막힌다."""
    body = _mail_body().replace(RENDERED_AMOUNT_LINE, UNRENDERED_AMOUNT_LINE, 1)
    assert UNRENDERED_AMOUNT_LINE in body.splitlines()
    with pytest.raises(BriefInputError):
        _packet(body)
