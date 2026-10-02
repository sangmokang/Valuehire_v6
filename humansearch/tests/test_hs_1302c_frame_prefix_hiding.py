"""PR #83 F83-1 — 프레임 접두(`문의:`·`제목:`)가 채용 조건을 숨기던 면제를 없앤다.

Codex 13차 반례: `문의: 대졸 필수`·`문의: 재택근무 가능` 는 조건 정규식(EXTRA_CONDITION_PATTERNS)에
걸리지 않아 프레임 줄 면제로 충실도 검사에서 통째로 빠졌다. 정규식에 단어를 더 넣는 처방은
`문의: 야간 근무 가능` 같은 제3의 반례에서 다시 뚫리므로 여기서는 **면제 자체**를 없앤다.

계약(v7 §2 I-a):
- 본문 줄이 JD 원문에 없는 채용 조건을 담으면 프레임 접두로 시작하더라도 패킷 생성을 거부한다.
- JD 원문의 조건 줄이 프레임 위치에 있어도 충실도 검사 대상에서 빠지지 않는다.

허용 프레임 줄은 `JdPacket.linkedin_frame_lines` 로 **선언한 정확 문자열**과 일치할 때만 통과한다.
JD 는 합성 문장이며 실 고객사 문장·실명은 0 이다.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json

import pytest
from test_hs_1304b import _jd, _jd_packet, _packet

from humansearch.brief import (
    BriefInputError,
    Contact,
    JdPacket,
    JdSource,
    from_json,
    to_json,
    verify_linkedin_fidelity,
)

# 조건 정규식이 잡지 못하는 채용 조건들 — 셋 다 같은 이유로 막혀야 한다(땜질 검출).
HIDDEN_CONDITIONS: tuple[str, ...] = (
    "문의: 대졸 필수",
    "문의: 재택근무 가능",
    "문의: 야간 근무 가능",
    "제목: 대졸 필수",
)

# 조건이 아닌 안내 문구 — 타입 출처(Contact)가 있으면 통과해야 한다.
CONTACT = Contact(name="담당 컨설턴트", email="consultant@example.com")
CONTACT_LINE = CONTACT.rendered_line()

_COND_JD_TEXT = "주요업무\n• 검색 랭킹을 설계한다.\n자격요건\n• 경력 3년 이상\n"


def _cond_jd() -> JdSource:
    digest = hashlib.sha256(_COND_JD_TEXT.encode("utf-8")).hexdigest()
    return JdSource(text=_COND_JD_TEXT, raw_sha256=digest, provided_by="U1")


# ---------------------------------------------------------------- 음성: 숨은 조건


@pytest.mark.parametrize("hidden", HIDDEN_CONDITIONS)
def test_frame_prefix_cannot_hide_a_condition_the_regex_misses(hidden: str) -> None:
    """프레임 접두를 붙였다고 원문에 없는 조건 줄이 검사에서 빠지면 안 된다."""
    jd = _jd()
    with pytest.raises(BriefInputError):
        _packet(jd_packet=_jd_packet(jd, linkedin_body=jd.text + "\n" + hidden))


def test_an_undeclared_plain_frame_line_is_also_rejected() -> None:
    """선언하지 않은 프레임 줄은 조건이 아니어도 원문에 없는 줄이다(면제 폐지)."""
    jd = _jd()
    with pytest.raises(BriefInputError):
        _packet(jd_packet=_jd_packet(jd, linkedin_body=jd.text + "\n" + CONTACT_LINE))


# ---------------------------------------------------------------- 선언 필드


def test_jd_packet_declares_its_linkedin_contact() -> None:
    """허용 프레임 줄의 출처는 패킷의 **타입 필드**다 — 접두 기반 면제를 대체한다.

    1차에서는 자유 문자열 목록(`linkedin_frame_lines`)이었으나, 조건 문구를 그 목록에
    적는 것만으로 뚫려(Codex V1) 타입 필드로 옮겼다.
    """
    names = {field.name for field in dataclasses.fields(JdPacket)}
    assert "linkedin_contact" in names
    assert "linkedin_frame_lines" not in names


def test_a_declared_frame_line_passes_and_survives_json_roundtrip() -> None:
    jd = _jd()
    packet = _packet(
        jd_packet=_jd_packet(
            jd,
            linkedin_body=jd.text + "\n" + CONTACT_LINE,
            linkedin_contact=CONTACT,
        )
    )
    restored = from_json(to_json(packet))
    assert CONTACT_LINE in restored.jd_packet.linkedin_body
    assert restored.jd_packet.linkedin_contact == CONTACT


def test_json_roundtrip_rejects_a_frame_line_that_was_not_declared() -> None:
    """왕복 뒤에도 같은 판정 — 저장 파일을 고쳐 프레임 줄을 끼워 넣어도 복원이 막는다."""
    jd = _jd()
    packet = _packet(
        jd_packet=_jd_packet(
            jd,
            linkedin_body=jd.text + "\n" + CONTACT_LINE,
            linkedin_contact=CONTACT,
        )
    )
    raw = json.loads(to_json(packet))
    raw["jd_packet"]["linkedin_contact"] = None
    with pytest.raises(BriefInputError):
        from_json(json.dumps(raw, ensure_ascii=False))


def test_a_contact_still_cannot_carry_a_known_condition() -> None:
    """타입 필드도 면제권이 아니다 — 조건 문구는 담당자 이름이 될 수 없다."""
    with pytest.raises(BriefInputError):
        Contact(name="경력 10년 이상", email="x@example.com")
    jd = _jd()
    hidden = "문의: 경력 10년 이상만 지원 가능합니다"
    with pytest.raises(BriefInputError):
        _packet(
            jd_packet=_jd_packet(
                jd, linkedin_body=jd.text + "\n" + hidden, linkedin_contact=CONTACT
            )
        )


# ---------------------------------------------------------------- 프레임 위치의 JD 조건 줄


def test_a_jd_condition_line_at_a_frame_position_is_still_checked() -> None:
    """JD 원문의 조건 줄을 프레임 접두 뒤로 옮겨도 검사 대상이다 — 누락 0 이어야 한다."""
    body = "[복사 시작]\n주요업무\n• 검색 랭킹을 설계한다.\n자격요건\n문의: 경력 3년 이상\n[복사 끝]\n"
    report = verify_linkedin_fidelity(_cond_jd(), body)
    assert report.missing == ()
    assert report.extra_lines == ()
    assert report.ok is True
