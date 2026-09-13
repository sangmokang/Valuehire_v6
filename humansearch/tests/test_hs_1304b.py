"""HS-13.04b — 2필드 절 범위와 패킷 경계 충실도.

① 라이브 실측(2026-09-10 번개장터): `[다루는 문제의 범위]` 같은 괄호 소제목이 별도 절로 잘려
   `주요업무`·`혜택 및 복지` 의 본문이 필드 2 에서 통째로 빠졌다. 처방: 마커 절은 **다음 마커 절이
   뒤에 이어지는 괄호 소제목 절을 흡수**한다(다음 일반 제목에서 끝). 순서는 결과를 바꾸지 않는다.
② Codex V1 10차: 충실도에 실패한 JD 3종을 담은 패킷도 저장·복원·VERIFIED 가 됐다. 처방:
   `JdPacket` 이 절 선택(`two_field_sections`)·LinkedIn 생략 절(`linkedin_omitted_sections`)을 들고,
   `SearchPacket` 이 조립·역직렬화 때 Gmail·LinkedIn·2필드 셋 다 원문과 재검증한다.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from humansearch.brief import (
    BriefInputError,
    CandidateEvidence,
    CandidateLead,
    Claim,
    CompanyBrief,
    ConnectionDegree,
    EmailContact,
    JdPacket,
    JdSource,
    PacketStore,
    PositionSpec,
    ScoreBreakdown,
    SearchPacket,
    SourceRef,
    TeamMail,
    from_json,
    packet_id,
    split_two_field,
    to_json,
)

_JD_LINES: tuple[str, ...] = (
    "| 합류하게 될 팀을 소개해요",
    "[Core Product 팀]",
    "• 전 고객 여정을 설계하는 조직입니다.",
    "주요업무",
    "[다루는 문제의 범위]",
    "• 탐색과 거래 흐름을 다룹니다.",
    "[맡게 될 주요 업무]",
    "• 기능을 기획하고 실험으로 검증합니다.",
    "자격요건",
    "• 실험 설계 경험이 있는 분",
    "혜택 및 복지",
    "[몰입 환경]",
    "• 고사양 장비 지원",
    "[활력]",
    "• 식대 지원",
    "채용 전형",
    "서류 ＞ 인터뷰 ＞ 최종 합격",
)
_JD_TEXT = "\n".join(_JD_LINES)
_RAW_SHA = hashlib.sha256(_JD_TEXT.encode("utf-8")).hexdigest()
_CLICKUP = "86e1f00d"
_DAY = date(2026, 9, 10)
_LEAD_URL = "https://www.linkedin.com/in/example-lead"
_MARKERS = ("주요업무", "자격요건", "혜택 및 복지", "채용 전형")
_INTRO = "예시 고객사는 중고거래 플랫폼입니다."


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _jd(text: str = _JD_TEXT) -> JdSource:
    return JdSource(text, _sha256(text), "U1")


def _position() -> PositionSpec:
    return PositionSpec(_CLICKUP, "예시 고객사", "프로덕트 매니저", None, "정규직", "서울", None)


def _jd_packet(source: JdSource, **overrides: Any) -> JdPacket:
    two = split_two_field(source, _INTRO, section_markers=_MARKERS)
    fields: dict[str, Any] = {
        "gmail_body": source.text,
        "linkedin_body": source.text,
        "two_field_company": two.company_intro,
        "two_field_jd": two.jd_body,
        "two_field_sections": _MARKERS,
        "linkedin_omitted_sections": (),
    }
    fields.update(overrides)
    return JdPacket(**fields)


def _mail_body(jp: JdPacket, tail: str = "") -> str:
    """§6 3절 블록을 렌더러와 같은 마커로 담은 최소 본문(HS-13.04b 메일 결합). tail 은 뒤에 덧붙인다."""
    lines = [
        "[JD 원문 시작]",
        *jp.gmail_body.splitlines(),
        "[JD 원문 끝]",
        "[복사 시작]",
        *jp.linkedin_body.splitlines(),
        "[복사 끝]",
        "[필드 1: 회사 소개]",
        *jp.two_field_company.splitlines(),
        "",
        "[필드 2: JD 내용]",
        *jp.two_field_jd.splitlines(),
    ]
    if tail:
        lines.append(tail)
    return "\n".join(lines) + "\n"


def _packet(jd_packet: JdPacket | None = None, source: JdSource | None = None) -> SearchPacket:
    jd = _jd() if source is None else source
    jp = _jd_packet(jd) if jd_packet is None else jd_packet
    body = _mail_body(jp)
    return SearchPacket(
        packet_id=packet_id(_position(), jd),
        created_on=_DAY,
        position=_position(),
        jd=jd,
        company=CompanyBrief(
            legal_name=Claim("예시 주식회사", ("C1",)),
            sources=(SourceRef("C1", "https://example.com/about", "회사 소개", _DAY),),
        ),
        jd_packet=jp,
        candidates=(
            CandidateLead(
                display_name="예시 후보",
                headline="프로덕트 매니저",
                linkedin_url=_LEAD_URL,
                education="예시대학원 석사",
                career="예시사 3년",
                match_reasons=("실험 설계 경험",),
                check_points=("도메인 적합성",),
                evidence=CandidateEvidence(("실험",), 1, 2, "석사", 2, (24, 18), 2, 8, 10),
                score=ScoreBreakdown(30, 15, 15, 15),
                email=EmailContact("lead@example.org", "https://example.org/lab", "연구실"),
                degree=ConnectionDegree.SECOND,
                source_note="공개 프로필 URL 일치",
            ),
        ),
        mail=TeamMail(
            subject="[포지션]예시 고객사, 프로덕트 매니저",
            to=("sangmokang@valueconnect.kr",),
            cc=(),
            body=body,
            body_sha256=_sha256(body),
        ),
        boolean_queries=('("Product Manager" OR PM) AND 실험',),
        inmails=((_LEAD_URL, "안녕하세요, 포지션을 제안드립니다."),),
    )


# --- ① 2필드 절 범위 -------------------------------------------------------------


def test_marker_section_absorbs_bracketed_subsections_until_the_next_marker() -> None:
    two = split_two_field(_jd(), _INTRO, section_markers=_MARKERS)
    body = two.jd_body
    assert "• 탐색과 거래 흐름을 다룹니다." in body
    assert "• 기능을 기획하고 실험으로 검증합니다." in body
    assert "• 고사양 장비 지원" in body and "• 식대 지원" in body
    assert "서류 ＞ 인터뷰 ＞ 최종 합격" in body
    assert "합류하게 될 팀" not in body and "Core Product 팀" not in body
    assert body.index("주요업무") < body.index("자격요건") < body.index("혜택 및 복지")


def test_marker_order_does_not_change_the_selection() -> None:
    forward = split_two_field(_jd(), _INTRO, section_markers=_MARKERS)
    backward = split_two_field(_jd(), _INTRO, section_markers=tuple(reversed(_MARKERS)))
    assert forward.jd_body == backward.jd_body


def test_skipping_a_top_level_section_keeps_its_body_out() -> None:
    two = split_two_field(_jd(), _INTRO, section_markers=("주요업무", "채용 전형"))
    assert "• 실험 설계 경험이 있는 분" not in two.jd_body
    assert "• 고사양 장비 지원" not in two.jd_body
    assert "• 기능을 기획하고 실험으로 검증합니다." in two.jd_body


def test_marker_naming_a_bracketed_subsection_still_works_as_its_own_range() -> None:
    two = split_two_field(_jd(), _INTRO, section_markers=("맡게 될 주요 업무", "자격요건"))
    assert "• 기능을 기획하고 실험으로 검증합니다." in two.jd_body
    assert "• 탐색과 거래 흐름을 다룹니다." not in two.jd_body


# --- ② 패킷 경계 충실도 -------------------------------------------------------------


def test_packet_with_faithful_bodies_is_accepted_and_round_trips() -> None:
    packet = _packet()
    assert from_json(to_json(packet)) == packet


def test_packet_rejects_gmail_body_missing_a_jd_line() -> None:
    jd = _jd()
    broken = _jd_packet(jd, gmail_body=jd.text.replace("• 식대 지원\n", ""))
    with pytest.raises(BriefInputError):
        _packet(jd_packet=broken)


def test_packet_rejects_gmail_body_with_an_added_condition() -> None:
    jd = _jd()
    broken = _jd_packet(jd, gmail_body=jd.text + "\n• 석사 이상 필수")
    with pytest.raises(BriefInputError):
        _packet(jd_packet=broken)


def test_packet_rejects_two_field_jd_that_lost_a_marker_section_body() -> None:
    jd = _jd()
    good = _jd_packet(jd)
    lossy = replace(good, two_field_jd=good.two_field_jd.replace("• 고사양 장비 지원\n", ""))
    with pytest.raises(BriefInputError):
        _packet(jd_packet=lossy)


def test_packet_rejects_linkedin_body_missing_a_non_omitted_section() -> None:
    jd = _jd()
    without_benefits = jd.text.replace("[몰입 환경]\n• 고사양 장비 지원\n[활력]\n• 식대 지원\n", "")
    broken = _jd_packet(jd, linkedin_body=without_benefits)
    with pytest.raises(BriefInputError):
        _packet(jd_packet=broken)


def test_packet_accepts_linkedin_body_that_omits_only_declared_sections() -> None:
    jd = _jd()
    without_benefits = jd.text.replace(
        "혜택 및 복지\n[몰입 환경]\n• 고사양 장비 지원\n[활력]\n• 식대 지원\n", ""
    )
    ok = _jd_packet(
        jd,
        linkedin_body=without_benefits,
        linkedin_omitted_sections=("혜택 및 복지", "몰입 환경", "활력"),
    )
    assert _packet(jd_packet=ok).jd_packet.linkedin_omitted_sections == (
        "혜택 및 복지",
        "몰입 환경",
        "활력",
    )


def test_jd_packet_requires_at_least_one_two_field_section() -> None:
    jd = _jd()
    with pytest.raises(BriefInputError):
        _jd_packet(jd, two_field_sections=())


def test_store_refuses_to_load_a_tampered_unfaithful_packet(tmp_path: Path) -> None:
    store = PacketStore(tmp_path / "packets")
    packet = _packet()
    target = store.save(packet)
    text = target.read_text(encoding="utf-8")
    tampered = text.replace("• 식대 지원", "• 식대 지원(석사 이상)", 1)
    assert tampered != text
    target.write_text(tampered, encoding="utf-8")
    with pytest.raises(BriefInputError):
        store.load(packet.packet_id)


# --- ③ Codex 11차: 메일 본문 결합·빈 LinkedIn 판·비조건 추가 줄·소제목 마커 ---------------------


def _packet_with_mail(jp: JdPacket, body: str) -> SearchPacket:
    base = _packet(jd_packet=jp)
    return replace(base, mail=replace(base.mail, body=body, body_sha256=_sha256(body)))


def test_mail_body_must_embed_all_three_jd_blocks_verbatim() -> None:
    jp = _jd_packet(_jd())
    assert _packet_with_mail(jp, _mail_body(jp)).mail.body.startswith("[JD 원문 시작]")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: "예시 문구\n내부 공유 본문",
        lambda b: b.replace("\n[JD 원문 끝]", "\n• 석사 이상 필수\n[JD 원문 끝]", 1),
        lambda b: b.replace("서류 ＞ 인터뷰 ＞ 최종 합격\n[JD 원문 끝]", "[JD 원문 끝]", 1),
        lambda b: b.replace("[복사 시작]\n", "[복사 시작]\n제목: 임의 추가\n", 1).replace(
            "제목: 임의 추가", "석사 우대", 1
        ),
        lambda b: b.replace("[필드 2: JD 내용]\n주요업무", "[필드 2: JD 내용]\n주요 업무(임의)", 1),
        lambda b: b + "\n[JD 원문 시작]",
    ],
)
def test_mail_body_that_does_not_reproduce_the_packet_blocks_is_rejected(mutate: object) -> None:
    jp = _jd_packet(_jd())
    body = mutate(_mail_body(jp))  # type: ignore[operator]
    assert body != _mail_body(jp)
    with pytest.raises(BriefInputError):
        _packet_with_mail(jp, body)


@pytest.mark.parametrize(
    "condition",
    [
        "경력 10년 이상 필수",
        "연봉 1억 이상 협의",
        "석사 이상 지원 가능",
    ],
)
def test_mail_body_rejects_recruiting_conditions_outside_jd_blocks(condition: str) -> None:
    jp = _jd_packet(_jd())
    with pytest.raises(BriefInputError):
        _packet_with_mail(jp, _mail_body(jp) + f"\n{condition}")


def test_omitting_every_section_cannot_yield_an_empty_linkedin_body() -> None:
    jd = _jd()
    headings = tuple(
        h
        for h in (
            "합류하게 될 팀을 소개해요",
            "Core Product 팀",
            "주요업무",
            "다루는 문제의 범위",
            "맡게 될 주요 업무",
            "자격요건",
            "혜택 및 복지",
            "몰입 환경",
            "활력",
            "채용 전형",
        )
    )
    with pytest.raises(BriefInputError):
        _packet(
            jd_packet=_jd_packet(
                jd, linkedin_body="[복사 시작]\n[복사 끝]", linkedin_omitted_sections=headings
            )
        )
    with pytest.raises(BriefInputError):
        _packet(jd_packet=replace(_jd_packet(jd), linkedin_omitted_sections=("주요업무",)))


def test_core_sections_from_the_contract_cannot_be_omitted() -> None:
    jd = _jd()
    for core in ("주요업무", "자격요건"):
        stripped = jd.text
        with pytest.raises(BriefInputError):
            _packet(
                jd_packet=_jd_packet(jd, linkedin_body=stripped, linkedin_omitted_sections=(core,))
            )


@pytest.mark.parametrize("label", ["gmail_body", "linkedin_body"])
def test_packet_rejects_non_condition_extra_lines_in_jd_channels(label: str) -> None:
    jd = _jd()
    extra = jd.text + "\n재택근무 가능\n"
    with pytest.raises(BriefInputError):
        _packet(jd_packet=_jd_packet(jd, **{label: extra}))


def test_a_subheading_marker_does_not_absorb_its_sibling_subheadings() -> None:
    two = split_two_field(_jd(), _INTRO, section_markers=("다루는 문제의 범위",))
    assert "• 탐색과 거래 흐름을 다룹니다." in two.jd_body
    assert "• 기능을 기획하고 실험으로 검증합니다." not in two.jd_body


def test_an_empty_subheading_marker_is_rejected_as_an_empty_selection() -> None:
    text = _JD_TEXT.replace(
        "[다루는 문제의 범위]\n• 탐색과 거래 흐름을 다룹니다.\n", "[빈 소제목]\n"
    )
    with pytest.raises(BriefInputError):
        split_two_field(_jd(text), _INTRO, section_markers=("빈 소제목",))


# --- ④ Codex 12차: 프레임 줄 조건 은닉·핵심 절 제목 변형·끝 마커 중복/CRLF·빈 소제목 혼합 ----------


def test_frame_line_cannot_hide_a_recruiting_condition() -> None:
    jd = _jd()
    with pytest.raises(BriefInputError):
        _packet(
            jd_packet=_jd_packet(
                jd, linkedin_body=jd.text + "\n문의: 경력 10년 이상만 지원 가능합니다"
            )
        )
    with pytest.raises(BriefInputError):
        _packet(jd_packet=_jd_packet(jd, linkedin_body="제목: 예시 | 경력 2~6년\n" + jd.text))
    ok = _packet(
        jd_packet=_jd_packet(
            jd, linkedin_body="제목: 예시 고객사 프로덕트 매니저\n" + jd.text + "\n문의: 밸류커넥트"
        )
    )
    assert ok.jd_packet.linkedin_body.startswith("제목:")


def test_core_section_heading_with_trailing_punctuation_is_still_core() -> None:
    text = _JD_TEXT.replace("주요업무\n", "주요업무:\n").replace("자격요건\n", "자격요건：\n")
    jd = _jd(text)
    markers = ("주요업무:", "자격요건：", "혜택 및 복지", "채용 전형")
    two = split_two_field(jd, _INTRO, section_markers=markers)
    packet = JdPacket(
        gmail_body=text,
        linkedin_body=text,
        two_field_company=two.company_intro,
        two_field_jd=two.jd_body,
        two_field_sections=markers,
        linkedin_omitted_sections=("주요업무:", "자격요건："),
    )
    with pytest.raises(BriefInputError):
        _packet(source=jd, jd_packet=packet)


def test_omission_is_refused_when_no_core_section_is_recognised() -> None:
    text = "Duties\n• ship features\nPerks\n• snacks"
    jd = _jd(text)
    two = split_two_field(jd, _INTRO, section_markers=("Duties",))
    packet = JdPacket(
        gmail_body=text,
        linkedin_body="Duties\n• ship features",
        two_field_company=two.company_intro,
        two_field_jd=two.jd_body,
        two_field_sections=("Duties",),
        linkedin_omitted_sections=("Perks",),
    )
    with pytest.raises(BriefInputError):
        _packet(source=jd, jd_packet=packet)


def test_duplicate_end_marker_and_crlf_body_are_rejected() -> None:
    jp = _jd_packet(_jd())
    body = _mail_body(jp)
    with pytest.raises(BriefInputError):
        _packet_with_mail(jp, body + "\n[JD 원문 끝]")
    with pytest.raises(BriefInputError):
        _packet_with_mail(jp, body + "\n[복사 끝]")
    with pytest.raises(BriefInputError):
        _packet_with_mail(jp, body.replace("\n", "\r\n"))


def test_an_empty_subheading_mixed_with_a_real_section_is_rejected() -> None:
    text = _JD_TEXT.replace(
        "[다루는 문제의 범위]\n• 탐색과 거래 흐름을 다룹니다.\n", "[빈 소제목]\n"
    )
    with pytest.raises(BriefInputError):
        split_two_field(_jd(text), _INTRO, section_markers=("빈 소제목", "자격요건"))
