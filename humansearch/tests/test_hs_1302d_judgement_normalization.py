"""PR #83 3차 — 판정 직전 정규화·이메일 형식·금액 형식을 조인다(값싼 방어 3건).

Codex V2 2차 반증(5576b02):
- `EMAIL_DOUBLE_DOT_RENDERED=PASS:문의: 홍길동 (holder@b..com)` · `EMAIL_LEADING_HYPHEN_DOMAIN=PASS:holder@-b.com`
- `COMPANY_ZWSP_VISIBLE_KNOWN=PASS:- 매출: 경(ZWSP)력 5년 이(ZWSP)상 [I1]`
- `COMPANY_MARKDOWN_VISIBLE_KNOWN=PASS:- 매출: 경**력** 5년 이**상** [I1]`
- `CONTACT_ZWSP_VISIBLE_KNOWN=PASS:문의: 경(ZWSP)력 5년 이(ZWSP)상 (x@example.com)`
- `MALFORMED_AMOUNT_SHAPE=PASS:- 매출: 1,,,원 [I1]`

계약:
- 이메일은 로컬@도메인이고, 도메인은 `[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?` 라벨을 점으로
  이은 2개 이상이며 마지막 라벨은 알파벳 2자 이상이어야 한다.
- 조건 정규식과 JD 충실도 대조는 **같은 판정용 사본**에서 수행한다 — 영폭·유니코드 format
  문자를 지우고 마크다운 강조를 벗기고 NFKC 로 내린 문자열. 원문은 그대로 보존한다.
- 회사 금액 면제는 `\\d{1,3}(,\\d{3})*(\\.\\d+)?\\s*(억|만|조)?\\s*(원|달러|USD|KRW)` 전체
  일치일 때만. 금액 필드인데 그 모양이 아니면 거부한다. 천 단위 구분이 **필수**이므로
  `1000원`(쉼표 없는 네 자리)은 의도적으로 거부한다 — 자릿수 오타와 정상 금액을 눈으로
  구분할 수 없기 때문이다. 세 자리 이하(`300억 원`)와 구분된 값(`1,234억 원`)만 받는다.
- 이메일 로컬파트는 허용 문자로 이루어진 점 구분 조각이어야 한다 — 빈 조각·선행 점·
  후행 점은 거부한다. **따옴표 로컬파트와 국제화 도메인(비ASCII)은 지원하지 않는다**
  (부분 정규식으로는 그 계약을 끝까지 검증할 수 없어, 통과시키느니 거부한다).

이 정규화는 **의미 검증이 아니다** — 목록 밖 표현은 여전히 통과한다(§7-5 결정 카드).
모든 자료는 합성이다.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any

import pytest
from test_hs_1304b import _jd, _jd_packet, _packet
from test_hs_1305 import COMPANY, TODAY, _draft, _recipients

from humansearch.brief import (
    BriefInputError,
    Claim,
    CompanyBrief,
    Contact,
    SearchPacket,
    TeamMail,
    from_json,
    packet_id,
    to_json,
)
from humansearch.brief.mail import compose_brief_mail

ZWSP = chr(0x200B)  # 영폭 공백. 화면에서는 붙어 보이지만 글자 사이를 갈라 정규식을 피한다.
ZWNJ = chr(0x200C)
BOM = chr(0xFEFF)

# 사람 눈에는 전부 "경력 5년 이상" 으로 읽히는 변형들.
INVISIBLE = "경" + ZWSP + "력 5년 이" + ZWSP + "상"
MARKDOWN = "경**력** 5년 이**상**"
UNDERSCORE = "경__력__ 5년 이__상__"
FULLWIDTH = "경력 ５년 이상"
BOM_MIX = BOM + "경력 5년" + ZWNJ + " 이상"
VISIBLE_SAME: tuple[str, ...] = (INVISIBLE, MARKDOWN, UNDERSCORE, FULLWIDTH, BOM_MIX)

# PII 게이트(scripts/acceptance-hs-1305-pii.sh)가 허용하는 형태만 쓴다 — 로컬파트가 정확히
# `holder` 이거나 주소가 `@example.com` 으로 끝나는 합성 주소다. 그래서 형식 위반 음성
# 주소는 로컬파트를 `holder` 로 두고 도메인 쪽만 망가뜨렸다(게이트는 도메인을 보지 않는다).
BAD_EMAILS: tuple[str, ...] = (
    "holder@b..com",  # 빈 라벨
    "holder@-b.com",  # 라벨이 하이픈으로 시작
    "holder@b-.com",  # 라벨이 하이픈으로 끝
    "holder@b",  # 점이 없다(라벨 1개)
    "holder@@b.com",  # @ 가 둘
    "holder b@example.com",  # 로컬파트에 공백
    "holder..b@example.com",  # 로컬파트에 연속 점
    ".holder@example.com",  # 로컬파트가 점으로 시작
    "holder.@example.com",  # 로컬파트가 점으로 끝
    '"hol der"@example.com',  # 따옴표 로컬파트 — 지원하지 않는다
    "holder@도메인.example.com",  # 국제화 도메인 — 지원하지 않는다
)
# 점·플러스(로컬파트)와 하이픈 라벨·다단 도메인을 나눠서 덮는다 — 한 주소로는 게이트
# 허용 형태를 만족시키면서 둘 다 담을 수 없다.
GOOD_EMAILS: tuple[str, ...] = (
    "a.b+c@example.com",  # 로컬파트의 점과 플러스
    "holder@d-e.example.com",  # 하이픈이 든 라벨 + 3단 도메인
    "holder@a.io",  # 한 글자 라벨 + 두 글자 최상위
    "hong@example.com",
)

BAD_AMOUNTS: tuple[str, ...] = ("1,,,원", "1,00원", ",100원", "1,2345원", "억 원")
GOOD_AMOUNTS: tuple[str, ...] = ("300억 원", "1,234억 원", "12.5억 원", "3,000만 원", "500달러")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _company_packet(company: CompanyBrief) -> SearchPacket:
    draft = _draft(company=company)
    mail = compose_brief_mail(draft, _recipients(), TODAY, first_live=False)
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
            body=mail.body,
            body_sha256=_sha256(mail.body),
        ),
        boolean_queries=draft.boolean_queries,
        inmails=draft.inmails,
        search_filters=draft.search_filters,
    )


def _with_revenue(value: str) -> CompanyBrief:
    return replace(COMPANY, revenue=Claim(value, ("I1",)))


# ---------------------------------------------------------------- ① 이메일 형식


@pytest.mark.parametrize("email", BAD_EMAILS)
def test_a_malformed_email_is_rejected(email: str) -> None:
    with pytest.raises(BriefInputError):
        Contact(name="홍길동", email=email)


@pytest.mark.parametrize("email", GOOD_EMAILS)
def test_a_well_formed_email_is_accepted(email: str) -> None:
    assert Contact(name="홍길동", email=email).email == email


def test_a_malformed_email_cannot_reach_the_packet() -> None:
    """잘못된 주소가 렌더 줄을 타고 패킷 경계를 넘지 못한다."""
    jd = _jd()
    with pytest.raises(BriefInputError):
        contact = Contact(name="홍길동", email="holder@b..com")
        _packet(
            jd_packet=_jd_packet(
                jd,
                linkedin_body=f"{jd.text}\n{contact.rendered_line()}",
                linkedin_contact=contact,
            )
        )


# ---------------------------------------------------------------- ② 판정 전 정규화


@pytest.mark.parametrize("variant", VISIBLE_SAME)
def test_an_invisible_or_marked_up_condition_cannot_be_a_contact_name(variant: str) -> None:
    """눈에 같은 조건 문구는 글자 사이를 갈라도 담당자 이름이 될 수 없다."""
    with pytest.raises(BriefInputError):
        Contact(name=variant, email="x@example.com")


@pytest.mark.parametrize("variant", VISIBLE_SAME)
def test_an_invisible_or_marked_up_condition_in_a_company_field_is_rejected(variant: str) -> None:
    """금액 필드가 아닌 자리에 넣는다 — 금액 형식 검사가 대신 막아 주면 정규화를 안 보게 된다.

    `products` 는 자유 서술이라 조건 정규식만이 유일한 방어선이고, 그래서 이 시험이
    판정용 정규화를 정조준한다.
    """
    company = replace(COMPANY, products=(Claim(variant, ("C1",)),))
    with pytest.raises(BriefInputError):
        _company_packet(company)


@pytest.mark.parametrize("variant", VISIBLE_SAME)
def test_an_invisible_or_marked_up_condition_in_an_amount_field_is_rejected(variant: str) -> None:
    """금액 자리에 넣으면 금액 형식 검사와 조건 검사 둘 다 막는다(이중 방어)."""
    with pytest.raises(BriefInputError):
        _company_packet(_with_revenue(variant))


@pytest.mark.parametrize("variant", VISIBLE_SAME)
def test_an_invisible_or_marked_up_condition_in_the_linkedin_body_is_rejected(
    variant: str,
) -> None:
    jd = _jd()
    with pytest.raises(BriefInputError):
        _packet(jd_packet=_jd_packet(jd, linkedin_body=f"{jd.text}\n문의: {variant}"))


def test_normal_lines_still_pass_after_normalization() -> None:
    """정규화가 정상 경로를 막지 않는다 — 양성 대조군."""
    assert "- 매출: 300억 원 [I1]" in _company_packet(COMPANY).mail.body.splitlines()
    jd = _jd()
    contact = Contact(name="홍길동", email="hong@example.com")
    ok = _packet(
        jd_packet=_jd_packet(
            jd,
            linkedin_body=f"{jd.text}\n{contact.rendered_line()}",
            linkedin_contact=contact,
        )
    )
    assert contact.rendered_line() in ok.jd_packet.linkedin_body


def test_the_stored_text_keeps_the_original_bytes() -> None:
    """정규화는 판정용 사본에만 건다 — 저장된 원문 바이트는 그대로 남는다."""
    company = _with_revenue("1,234억 원")
    packet = _company_packet(company)
    stored = from_json(to_json(packet))
    assert stored.mail.body == packet.mail.body
    assert stored.company.revenue is not None
    assert stored.company.revenue.value == "1,234억 원"


# ---------------------------------------------------------------- ③ 금액 형식


@pytest.mark.parametrize("value", BAD_AMOUNTS)
def test_a_malformed_amount_in_an_amount_field_is_rejected(value: str) -> None:
    with pytest.raises(BriefInputError):
        _company_packet(_with_revenue(value))


@pytest.mark.parametrize("value", GOOD_AMOUNTS)
def test_a_well_formed_amount_in_an_amount_field_passes(value: str) -> None:
    lines = _company_packet(_with_revenue(value)).mail.body.splitlines()
    assert f"- 매출: {value} [I1]" in lines


def test_every_amount_field_is_checked() -> None:
    """매출뿐 아니라 영업이익·누적 투자금도 같은 모양 검사를 받는다."""
    for field in ("revenue", "operating_profit", "funding_total"):
        change: dict[str, Any] = {field: Claim("1,,,원", ("I1",))}
        with pytest.raises(BriefInputError):
            _company_packet(replace(COMPANY, **change))


def test_json_roundtrip_keeps_the_amount_verdict() -> None:
    packet = _company_packet(_with_revenue("1,234억 원"))
    assert "- 매출: 1,234억 원 [I1]" in from_json(to_json(packet)).mail.body.splitlines()
