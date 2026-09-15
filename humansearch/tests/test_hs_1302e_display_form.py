"""PR #83 5차 — 판정 사본을 **사람이 화면에서 읽는 글자**로 되돌리고, 섞인 문자 체계를 거부한다.

Codex V1 3차 반증(c57dde1) — 실제 메일 조립 경로에서 통과한 네 줄:
- `CONTACT 경(U+FE0F)력 5년 이(U+FE0F)상 = ACCEPTED`
- `COMPANY • 경(U+FE0F)력 5년 이(U+FE0F)상 [C1] = ACCEPTED`
- `CONTACT 문의: 경[력]() 5년 이[상]() (…) = ACCEPTED`
- `COMPANY • 경[력]() 5년 이[상]() [C1] = ACCEPTED`
그리고 키릴 `а` 를 끼운 `경а력 5년 이а상` 도 통과했습니다.

원인은 셋입니다. ① 마크다운 링크의 대괄호·괄호가 글자를 끊는다. ② U+FE0F 같은 변이
선택자는 Cf 가 아니라 Mn 이라 Cf 제거에 걸리지 않는다. ③ NFKC 는 서로 다른 문자 체계의
닮은 글자를 같은 글자로 바꾸지 않는다.

계약:
- ① 마크다운 링크·이미지 `[표시](url)`·`![표시](url)`·`[표시]()` 는 표시 문자열로 환원한다.
- ② Cf 에 더해 변이 선택자와 결합 격리(U+FE00-FE0F, U+180B-180D, U+E0100-E01EF, U+034F)를
  제거한다.
- ③ 한 어절 안에 한글과 비-라틴 외국 문자 체계(키릴·그리스·아르메니아)가 섞이면 **거부**한다.
  ③ 은 정규화가 아니라 입력 거부다 — 정상 한국어·영문·숫자 혼용(`Python 개발자`)은 허용한다.

시험은 타입 생성만이 아니라 **실제 전체 메일 조립 경로**(Contact 렌더 줄 · CompanyBrief
자유 서술 → compose_brief_mail → SearchPacket)에서 확인한다. 자료는 전부 합성이다.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

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

VS16 = chr(0xFE0F)  # 변이 선택자. Mn 범주라 Cf 제거에 걸리지 않고 화면에는 보이지 않는다.
VS1 = chr(0xFE00)
CGJ = chr(0x034F)  # 결합 격리 — 글자 사이를 갈라 놓는다.
MONGOLIAN_FVS = chr(0x180B)
CYRILLIC_A = "\N{CYRILLIC SMALL LETTER A}"
GREEK_O = "\N{GREEK SMALL LETTER OMICRON}"

# 화면에서는 전부 "경력 5년 이상" 으로 읽히지만 판정 사본은 서로 다른 변형들.
VS_SPLIT = "경" + VS16 + "력 5년 이" + VS16 + "상"
VS1_SPLIT = "경" + VS1 + "력 5년 이" + VS1 + "상"
CGJ_SPLIT = "경" + CGJ + "력 5년 이" + CGJ + "상"
FVS_SPLIT = "경" + MONGOLIAN_FVS + "력 5년 이" + MONGOLIAN_FVS + "상"
LINK_SPLIT = "경[력]() 5년 이[상]()"
LINK_URL_SPLIT = "경[력](https://example.com) 5년 이[상](https://example.com)"
IMAGE_SPLIT = "경![력]() 5년 이![상]()"

INVISIBLE_SPLIT: tuple[str, ...] = (VS_SPLIT, VS1_SPLIT, CGJ_SPLIT, FVS_SPLIT)
LINK_FORMS: tuple[str, ...] = (LINK_SPLIT, LINK_URL_SPLIT, IMAGE_SPLIT)

# 문자 체계를 섞어 같은 글자처럼 보이게 만든 것들.
MIXED_SCRIPT: tuple[str, ...] = (
    "경" + CYRILLIC_A + "력 5년 이" + CYRILLIC_A + "상",
    "경" + GREEK_O + "력 5년 이상",
    CYRILLIC_A + "경력 5년 이상",
)

# 섞이지 않은 정상 문구 — 거부하면 안 된다.
NOT_MIXED: tuple[str, ...] = (
    "Python 개발자",
    "합성 검색 엔진",
    "AI 기반 B2B SaaS 2026",
    "Series-B 투자 유치",
)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _company_packet(company: CompanyBrief) -> SearchPacket:
    """CompanyBrief → compose_brief_mail → SearchPacket. 실제 조립 경로 그대로다."""
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


def _contact_packet(name: str) -> SearchPacket:
    """Contact → 렌더 줄 → linkedin_body → SearchPacket. 실제 조립 경로 그대로다."""
    contact = Contact(name=name, email="holder@example.com")
    jd = _jd()
    return _packet(
        jd_packet=_jd_packet(
            jd,
            linkedin_body=f"{jd.text}\n{contact.rendered_line()}",
            linkedin_contact=contact,
        )
    )


def _with_products(value: str) -> CompanyBrief:
    """자유 서술 필드 — 조건 정규식이 유일한 방어선인 자리다."""
    return replace(COMPANY, products=(Claim(value, ("C1",)),))


# ---------------------------------------------------------------- ① 마크다운 링크


@pytest.mark.parametrize("variant", LINK_FORMS)
def test_a_link_split_condition_cannot_become_a_contact(variant: str) -> None:
    with pytest.raises(BriefInputError):
        _contact_packet(variant)


@pytest.mark.parametrize("variant", LINK_FORMS)
def test_a_link_split_condition_cannot_reach_the_company_section(variant: str) -> None:
    with pytest.raises(BriefInputError):
        _company_packet(_with_products(variant))


def test_a_link_keeps_its_display_text_for_judgement() -> None:
    """환원은 표시 문자열만 남긴다 — 주소는 판정에서 사라진다."""
    from humansearch.brief.jd_fidelity import judgement_form

    assert judgement_form("경[력](https://example.com) 5년") == "경력 5년"
    assert judgement_form("![그림](x.png) 뒤") == "그림 뒤"


# ---------------------------------------------------------------- ② 보이지 않는 문자


@pytest.mark.parametrize("variant", INVISIBLE_SPLIT)
def test_an_invisible_split_condition_cannot_become_a_contact(variant: str) -> None:
    with pytest.raises(BriefInputError):
        _contact_packet(variant)


@pytest.mark.parametrize("variant", INVISIBLE_SPLIT)
def test_an_invisible_split_condition_cannot_reach_the_company_section(variant: str) -> None:
    with pytest.raises(BriefInputError):
        _company_packet(_with_products(variant))


# ---------------------------------------------------------------- ③ 섞인 문자 체계


@pytest.mark.parametrize("variant", MIXED_SCRIPT)
def test_a_mixed_script_word_cannot_become_a_contact(variant: str) -> None:
    with pytest.raises(BriefInputError):
        _contact_packet(variant)


@pytest.mark.parametrize("variant", MIXED_SCRIPT)
def test_a_mixed_script_word_cannot_reach_the_company_section(variant: str) -> None:
    with pytest.raises(BriefInputError):
        _company_packet(_with_products(variant))


@pytest.mark.parametrize("text", NOT_MIXED)
def test_ordinary_korean_english_and_digits_are_not_mixed_script(text: str) -> None:
    """한글·영문·숫자 혼용은 정상이다 — 거부하면 정상 브리프가 막힌다."""
    assert _company_packet(_with_products(text)).company.products[0].value == text


# ---------------------------------------------------------------- 양성 대조군


def test_the_normal_paths_still_pass() -> None:
    assert "- 매출: 300억 원 [I1]" in _company_packet(COMPANY).mail.body.splitlines()
    packet = _contact_packet("홍길동")
    assert "문의: 홍길동 (holder@example.com)" in packet.jd_packet.linkedin_body


def test_json_roundtrip_keeps_the_original_bytes() -> None:
    """정규화·거부는 판정용 사본의 일이고, 저장 원문은 그대로다."""
    packet = _contact_packet("홍길동")
    assert from_json(to_json(packet)).jd_packet.linkedin_body == packet.jd_packet.linkedin_body
