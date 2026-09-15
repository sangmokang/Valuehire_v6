"""PR #83 2차 F83-1 — 프레임 줄 면제를 자유 문자열 선언에서 **타입 필드 렌더링**으로 옮긴다.

Codex V1 반증: 1차 수정은 `JdPacket.linkedin_frame_lines` 라는 자유 문자열 목록을 면제권으로
썼다. 조건 문구 자체를 그 목록에 적으면 `문의: 대졸 필수`·`재택근무 가능`·`야간 근무 가능`·
`제목: 대졸 필수` 네 개가 전부 패킷 생성과 JSON 왕복을 통과했다("F83-1-BYPASS ... PASS").

신뢰 경계 전제: 본문도 선언도 같은 생성 파이프라인(LLM·러너)에서 온다. 호출자가 준 자유
문자열은 면제권이 될 수 없다.

계약:
- `제목:` 줄은 `제목: {position.title}` 과 정규화 후 정확 일치할 때만 통과.
- `문의:` 줄은 `JdPacket.linkedin_contact`(타입 필드)에서 `문의: {name} ({email})` 로 렌더한
  문자열과 정확 일치할 때만 통과. name 은 공백 포함 2~20자·조건 정규식 불일치·제어문자 없음,
  email 은 형식 검증.
- 그 밖의 `제목:`·`문의:` 줄은 접두를 떼고 내용을 판정한다.

모든 자료는 합성이다(실명·실 주소 0).
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import replace

import pytest
import test_hs_1304b as test_module
from test_hs_1304b import _jd, _jd_packet, _packet, _position

import humansearch.brief as brief_pkg
from humansearch.brief import BriefInputError, JdPacket, from_json, to_json

# 조건 정규식이 잡지 못하는 채용 조건 네 개(1차와 같은 정조준 문구).
HIDDEN_CONDITIONS: tuple[str, ...] = (
    "문의: 대졸 필수",
    "문의: 재택근무 가능",
    "문의: 야간 근무 가능",
    "제목: 대졸 필수",
)

# 같은 문구의 정규화 변형 — NFKC 전각 콜론·글머리표·공백 반복.
NORMALIZATION_VARIANTS: tuple[str, ...] = (
    "문의：대졸 필수",
    "- 문의: 대졸 필수",
    "문의:  대졸  필수",
)

CONTACT_NAME = "홍길동"
CONTACT_EMAIL = "hong@example.kr"
CONTACT_LINE = f"문의: {CONTACT_NAME} ({CONTACT_EMAIL})"


def _contact(name: str = CONTACT_NAME, email: str = CONTACT_EMAIL) -> object:
    """계약 타입을 실행 시점에 찾는다 — 없으면 import 오류가 아니라 판정 실패로 떨어뜨린다."""
    factory = getattr(brief_pkg, "Contact", None)
    assert factory is not None, "humansearch.brief 에 담당자 타입 Contact 가 없다"
    return factory(name=name, email=email)


def _title_line() -> str:
    return f"제목: {_position().title}"


# ---------------------------------------------------------------- 선언 목록 폐지


def test_jd_packet_no_longer_declares_free_string_frame_lines() -> None:
    """자유 문자열 선언 목록은 사라지고 타입 필드가 그 자리를 대신한다."""
    names = {field.name for field in dataclasses.fields(JdPacket)}
    assert "linkedin_frame_lines" not in names
    assert "linkedin_contact" in names


# ---------------------------------------------------------------- 제목 줄


def test_the_title_frame_line_must_equal_the_position_title() -> None:
    jd = _jd()
    ok = _packet(jd_packet=_jd_packet(jd, linkedin_body=f"{_title_line()}\n{jd.text}"))
    assert ok.jd_packet.linkedin_body.startswith("제목:")
    with pytest.raises(BriefInputError):
        _packet(jd_packet=_jd_packet(jd, linkedin_body=f"제목: 다른 제목\n{jd.text}"))


# ---------------------------------------------------------------- 문의 줄


def test_the_contact_frame_line_must_equal_the_rendered_contact() -> None:
    jd = _jd()
    ok = _packet(
        jd_packet=_jd_packet(
            jd, linkedin_body=f"{jd.text}\n{CONTACT_LINE}", linkedin_contact=_contact()
        )
    )
    assert ok.jd_packet.linkedin_contact == _contact()
    # 이름만 적고 주소를 뺀 줄은 렌더 결과와 다르다.
    with pytest.raises(BriefInputError):
        _packet(
            jd_packet=_jd_packet(
                jd, linkedin_body=f"{jd.text}\n문의: 홍길동", linkedin_contact=_contact()
            )
        )


def test_a_contact_frame_line_without_a_declared_contact_is_rejected() -> None:
    jd = _jd()
    with pytest.raises(BriefInputError):
        _packet(jd_packet=_jd_packet(jd, linkedin_body=f"{jd.text}\n{CONTACT_LINE}"))


# ---------------------------------------------------------------- 숨은 조건


@pytest.mark.parametrize("hidden", HIDDEN_CONDITIONS)
def test_a_condition_line_without_a_matching_rendered_source_is_rejected(hidden: str) -> None:
    """타입 출처가 만든 줄과 다르면 거부된다 — 거부 근거는 **문자열 불일치**다.

    Codex V2 지적: 이 시험만 보면 "조건이라서 막혔다" 로 읽히지만, 실제로는 담당자 렌더
    결과(`문의: 이름 (주소)`)에 이메일이 붙어 있어 본문 줄과 다르기 때문이다.
    조건 판정 자체를 보는 시험은 바로 아래 xfail 두 건이 따로 고정한다.
    """
    jd = _jd()
    with pytest.raises(BriefInputError):
        _packet(
            jd_packet=_jd_packet(
                jd,
                linkedin_body=f"{jd.text}\n{hidden}",
                linkedin_contact=_contact(hidden.split(": ", 1)[1], "x@example.kr"),
            )
        )


@pytest.mark.xfail(strict=True, reason="구조 변경 결정 대기 — §7-5 카드(담당자를 운영자 설정에서 조회)")
def test_an_unknown_condition_as_contact_name_passes_with_the_real_rendered_line() -> None:
    """**현재 계약에서는 통과하는 잔여 구멍.** 실제 렌더 줄을 그대로 쓴 반례다.

    `대졸 필수` 는 조건 정규식이 모르는 문구라 담당자 이름 검증을 빠져나가고,
    본문에 `문의: 대졸 필수 (x@example.kr)` 를 그대로 적으면 렌더 결과와 일치해 면제된다.
    닫으려면 담당자를 패킷 자유 입력이 아니라 운영자 소유 설정에서 조회해야 한다.
    구멍이 닫히면 strict xfail 이 **실패로** 알려 준다.
    """
    jd = _jd()
    contact = _contact("대졸 필수", "x@example.kr")
    with pytest.raises(BriefInputError):
        _packet(
            jd_packet=_jd_packet(
                jd,
                linkedin_body=f"{jd.text}\n{contact.rendered_line()}",  # type: ignore[attr-defined]
                linkedin_contact=contact,
            )
        )


@pytest.mark.xfail(strict=True, reason="구조 변경 결정 대기 — §7-5 카드(position.title 면제 폐지)")
def test_an_unknown_condition_as_position_title_passes() -> None:
    """**현재 계약에서는 통과하는 잔여 구멍.** 포지션 제목이 곧 면제권이다.

    `제목:` 줄은 `제목: {position.title}` 과 같으면 통과하므로, 포지션 제목 자체가
    조건 문구이면 그 줄이 그대로 나간다. 닫으려면 포지션 제목의 신뢰 출처를 코드로
    증명하거나 제목 줄 면제를 폐지해야 한다.
    """
    jd = _jd()
    title = "대졸 필수"
    original = test_module._position
    test_module._position = lambda: replace(original(), title=title)
    try:
        with pytest.raises(BriefInputError):
            _packet(jd_packet=_jd_packet(jd, linkedin_body=f"제목: {title}\n{jd.text}"))
    finally:
        test_module._position = original


@pytest.mark.parametrize("variant", NORMALIZATION_VARIANTS)
def test_normalization_variants_of_a_hidden_condition_are_rejected(variant: str) -> None:
    """전각 콜론·글머리표·공백 반복으로 모양을 바꿔도 같은 판정이어야 한다."""
    jd = _jd()
    with pytest.raises(BriefInputError):
        _packet(
            jd_packet=_jd_packet(
                jd,
                linkedin_body=f"{jd.text}\n{variant}",
                linkedin_contact=_contact("대졸 필수", "x@example.kr"),
            )
        )


# ---------------------------------------------------------------- Contact 모양 검증


@pytest.mark.parametrize(
    "name",
    ["", " ", "가", "가" * 21, "홍길" + chr(0) + "동", "홍길\n동", "경력 5년 이상", "연봉 5천만 원"],
)
def test_contact_name_shape_is_enforced(name: str) -> None:
    with pytest.raises(BriefInputError):
        _contact(name, "x@example.kr")


@pytest.mark.parametrize("email", ["", "hong", "hong@", "@example.kr", "hong example.kr"])
def test_contact_email_format_is_enforced(email: str) -> None:
    with pytest.raises(BriefInputError):
        _contact("홍길동", email)


def test_a_two_character_name_is_the_lower_bound() -> None:
    assert _contact("홍길", "x@example.kr").name == "홍길"  # type: ignore[attr-defined]


# ---------------------------------------------------------------- JSON 왕복


def test_json_roundtrip_keeps_the_typed_contact() -> None:
    jd = _jd()
    packet = _packet(
        jd_packet=_jd_packet(
            jd, linkedin_body=f"{jd.text}\n{CONTACT_LINE}", linkedin_contact=_contact()
        )
    )
    restored = from_json(to_json(packet))
    assert restored.jd_packet.linkedin_contact == _contact()
    assert CONTACT_LINE in restored.jd_packet.linkedin_body


def test_json_roundtrip_rejects_a_condition_injected_into_the_contact_name() -> None:
    """저장 파일을 고쳐 담당자 이름에 조건을 넣어도 복원이 막는다."""
    jd = _jd()
    packet = _packet(
        jd_packet=_jd_packet(
            jd, linkedin_body=f"{jd.text}\n{CONTACT_LINE}", linkedin_contact=_contact()
        )
    )
    raw = json.loads(to_json(packet))
    raw["jd_packet"]["linkedin_contact"]["name"] = "경력 5년 이상"
    with pytest.raises(BriefInputError):
        from_json(json.dumps(raw, ensure_ascii=False))


def test_json_roundtrip_rejects_a_contact_that_no_longer_matches_the_body() -> None:
    jd = _jd()
    packet = _packet(
        jd_packet=_jd_packet(
            jd, linkedin_body=f"{jd.text}\n{CONTACT_LINE}", linkedin_contact=_contact()
        )
    )
    raw = json.loads(to_json(packet))
    raw["jd_packet"]["linkedin_contact"] = None
    with pytest.raises(BriefInputError):
        from_json(json.dumps(raw, ensure_ascii=False))
