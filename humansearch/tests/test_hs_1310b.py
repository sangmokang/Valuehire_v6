"""HS-13.10b — verify 의 readback 정규화 계약을 고정한다(Gmail 리다이렉트 언랩).

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 __main__.py · §10.

라이브 초안 readback 실측: Gmail 은 본문의 링크를
`https://www.google.com/url?q=<URL>&source=gmail&ust=<digits>&sa=<alnum>` 로 감싼다.
감싼 채로 해시를 뜨면 보낸 본문과 절대 같아지지 않아 발송이 영원히 SENT_UNVERIFIED 로 남는다.

두 가지를 못 박는다.
① **꼬리를 정확히 고정한다** — `sa=` 뒤를 `[^\\s]*` 같은 느슨한 꼬리로 두면 뒤따르는 `)` 까지
   삼켜 `(URL)` 이 `(URL` 로 복원된다(실측 반례, 아래 시험 4).
② **양쪽에 같은 정규화를 건다** — 패킷 본문의 URL 도 같은 unquote 를 거쳐야 퍼센트 인코딩
   URL(`.../in/%EC%9D%80…`)이 감싸였다 풀린 쪽과 대칭으로 만난다.

발송·네트워크·시계 접근 0. 합성 `SearchPacket` 은 test_hs_1310.py 의 빌더 구조를 복제한다
(다른 시험 파일을 import 해 결합을 만들지 않는다).
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

import pytest

from humansearch.brief import (
    Approval,
    BriefInputError,
    CandidateEvidence,
    CandidateLead,
    Claim,
    CompanyBrief,
    ConnectionDegree,
    EmailContact,
    JdPacket,
    JdSource,
    PositionSpec,
    ScoreBreakdown,
    SearchPacket,
    SendIntent,
    SendState,
    SourceRef,
    TeamMail,
    claim_send,
    load_intent,
    mark,
    open_new_attempt,
    recipients_digest,
    record_intent,
    split_sections,
    split_two_field,
    to_json,
)
from humansearch.brief import cli as cli_module
from humansearch.brief.cli import normalize_readback, verify

# --- 실측 형태 ---------------------------------------------------------------

_UST = "1757500000000000"
_U_SA = "U"


def _wrap(url: str, *, sa: str = "D") -> str:
    """Gmail 이 본문 링크를 감싸는 실측 형태."""
    return f"https://www.google.com/url?q={url}&source=gmail&ust={_UST}&sa={sa}"


_PLAIN_URL = "https://example.com/a"
_SECOND_URL = "https://example.org/b"
# 실측 원문 — 퍼센트 인코딩된 한글 프로필 슬러그.
_ENCODED_URL = "https://www.linkedin.com/in/example-%EC%98%88%EC%8B%9C-000001/"

# --- 합성 패킷 (test_hs_1310.py 의 빌더 구조를 복제) --------------------------

_JD_TEXT = "주요업무\n• 실험을 설계한다.\n자격요건\n• 실험 설계 경험이 있다.\n"
_RAW_SHA = hashlib.sha256(_JD_TEXT.encode("utf-8")).hexdigest()
_CLICKUP = "77a2bcde"
_TODAY = date(2026, 9, 10)
_PACKET_ID = f"{_CLICKUP}-{_RAW_SHA[:8]}"
_LEAD_URL = "https://www.linkedin.com/in/example-lead"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _moment(hour: int) -> datetime:
    from datetime import UTC, datetime

    return datetime(2026, 9, 10, hour, 0, 0, tzinfo=UTC)


def _faithful_jd_packet(source: JdSource, company_intro: str = "회사 소개 필드") -> JdPacket:
    """JD 3종을 원문과 일치하게 만든다 — SearchPacket 이 조립 시 충실도를 재검증한다(HS-13.04b)."""
    markers = tuple(s.heading for s in split_sections(source.text) if s.heading and s.lines)
    two = split_two_field(source, company_intro, section_markers=markers)
    return JdPacket(
        gmail_body=source.text,
        linkedin_body=source.text,
        two_field_company=two.company_intro,
        two_field_jd=two.jd_body,
        two_field_sections=markers,
        linkedin_omitted_sections=(),
    )


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
    return "\n".join(lines)


def _packet(body: str) -> SearchPacket:
    return SearchPacket(
        packet_id=_PACKET_ID,
        created_on=_TODAY,
        position=PositionSpec(
            _CLICKUP, "예시 고객사", "백엔드 엔지니어", None, "정규직", "서울", None
        ),
        jd=JdSource(_JD_TEXT, _RAW_SHA, "U1"),
        company=CompanyBrief(
            legal_name=Claim("예시 주식회사", ("C1",)),
            sources=(SourceRef("C1", "https://example.com/about", "회사 소개", _TODAY),),
        ),
        jd_packet=_JP,
        candidates=(
            CandidateLead(
                display_name="예시 후보",
                headline="백엔드 엔지니어",
                linkedin_url=_LEAD_URL,
                education="예시대학원 석사",
                career="예시사 3년",
                match_reasons=("분산 시스템 경험",),
                check_points=("도메인 적합성",),
                evidence=CandidateEvidence(("분산시스템",), 1, 2, "석사", 2, (24, 18), 2, 8, 10),
                score=ScoreBreakdown(30, 15, 15, 15),
                email=EmailContact("lead@example.org", "https://example.org/lab", "연구실 페이지"),
                degree=ConnectionDegree.SECOND,
                source_note="공개 프로필 URL 일치",
            ),
        ),
        mail=TeamMail(
            subject="[포지션]예시 고객사, 백엔드 엔지니어",
            to=("sangmokang@valueconnect.kr",),
            cc=(),
            body=body,
            body_sha256=_sha256(body),
        ),
        boolean_queries=('("Backend Engineer" OR 백엔드) AND 분산시스템',),
        inmails=((_LEAD_URL, "안녕하세요, 포지션을 제안드립니다."),),
    )


_JP = _faithful_jd_packet(JdSource(_JD_TEXT, _RAW_SHA, "U1"))


def _round_trip(tmp_path: Path, sent_body: str, packet_body: str) -> tuple[int, str]:
    """패킷·readback 둘 다 §6 블록 앞머리를 같이 붙인다(메일 결합 경계) — URL 정규화 대상은 tail 뿐."""
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(to_json(_packet(_mail_body(_JP, packet_body))), encoding="utf-8")
    sent_path = tmp_path / "sent.txt"
    sent_path.write_bytes(_mail_body(_JP, sent_body).encode("utf-8"))
    return verify(packet_path, sent_path)


def _write_packet_and_sent(tmp_path: Path, packet_body: str, sent_body: str) -> tuple[Path, Path]:
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(to_json(_packet(_mail_body(_JP, packet_body))), encoding="utf-8")
    sent_path = tmp_path / "sent.txt"
    sent_path.write_text(_mail_body(_JP, sent_body), encoding="utf-8")
    return packet_path, sent_path


def _ledger(tmp_path: Path) -> Path:
    directory = tmp_path / "ledger"
    directory.mkdir(mode=0o700)
    return directory


def _intent(body: str = _mail_body(_JP, "정상 본문")) -> SendIntent:
    return SendIntent(
        packet_id=_PACKET_ID,
        channel="gmail",
        attempt=1,
        recipients_sha256=recipients_digest(("sangmokang@valueconnect.kr",), ()),
        body_sha256=_sha256(body),
        recorded_at=_moment(3),
        state=SendState.INTENT,
    )


def _claim(directory: Path, body: str = _mail_body(_JP, "정상 본문")) -> None:
    claim_send(
        directory,
        _PACKET_ID,
        "gmail",
        1,
        at=_moment(4),
        evidence="러너가 발송 직전 청구",
        recipients_sha256=recipients_digest(("sangmokang@valueconnect.kr",), ()),
        body_sha256=_sha256(body),
    )


def _approval(from_attempt: int = 1) -> Approval:
    return Approval(
        approved_by="sangmokang@valueconnect.kr",
        search_query='in:sent subject:"[포지션]"',
        search_checked_at="2026-09-10T05:00:00+00:00",
        reason="정정 없음 — 발송함에서 찾지 못해 재시도를 승인한다",
        packet_id=_PACKET_ID,
        from_attempt=from_attempt,
    )


# --- 1. 감싼 URL 1개 -----------------------------------------------------------


def test_normalize_readback_unwraps_one_google_redirect() -> None:
    text = f"본문 첫 줄\n프로필: {_wrap(_PLAIN_URL)}\n본문 끝 줄"
    assert normalize_readback(text) == f"본문 첫 줄\n프로필: {_PLAIN_URL}\n본문 끝 줄"


# --- 2. 감싼 URL 여러 개 -------------------------------------------------------


def test_normalize_readback_unwraps_several_google_redirects() -> None:
    text = f"첫 링크 {_wrap(_PLAIN_URL)} 그리고\n둘째 링크 {_wrap(_SECOND_URL, sa=_U_SA)} 끝"
    assert normalize_readback(text) == f"첫 링크 {_PLAIN_URL} 그리고\n둘째 링크 {_SECOND_URL} 끝"


# --- 3. 괄호 안 URL 이 정확히 복원된다 -----------------------------------------


def test_normalize_readback_restores_url_inside_parentheses() -> None:
    text = f"프로필({_wrap(_PLAIN_URL + '/')})을 참고하세요."
    assert normalize_readback(text) == f"프로필({_PLAIN_URL}/)을 참고하세요."


# --- 4. 반례 고정 — 느슨한 꼬리는 `)` 를 삼킨다 --------------------------------


def test_loose_tail_pattern_swallows_the_closing_paren_but_ours_does_not() -> None:
    """`sa=[^\\s]*` 로 두면 닫는 괄호까지 매치가 먹는다 — 이 반례를 계약에 못 박는다."""
    loose = re.compile(r"https://www\.google\.com/url\?q=([^&\s]+)&source=gmail&ust=\d+&sa=[^\s]*")
    text = f"프로필({_wrap(_PLAIN_URL)})을 참고하세요."
    expected = f"프로필({_PLAIN_URL})을 참고하세요."

    # 느슨한 꼬리는 `sa=D)을` 까지 한 매치로 먹어 닫는 괄호와 조사를 함께 지운다.
    swallowed = loose.sub(lambda m: unquote(m.group(1)), text)
    assert swallowed == f"프로필({_PLAIN_URL} 참고하세요."
    assert ")" not in swallowed
    assert swallowed != expected
    # 계약 꼬리(`sa=[A-Za-z0-9]+`)는 `)` 에서 멈춘다.
    assert normalize_readback(text) == expected


# --- 5. 퍼센트 인코딩 URL — 실측 원문과 대칭으로 만난다 ------------------------


def test_percent_encoded_url_verifies_against_the_packet_body(tmp_path: Path) -> None:
    """Gmail 이 `%` 를 그대로 둔 채 감싸면 unquote 가 한글로 바꾼다.

    패킷 본문 쪽도 같은 URL 정규화를 거치므로 두 쪽이 같은 값에서 만난다.
    """
    packet_body = f"안녕하세요.\n후보 프로필: {_ENCODED_URL}\n확인 부탁드립니다."
    sent_body = f"안녕하세요.\n후보 프로필: {_wrap(_ENCODED_URL)}\n확인 부탁드립니다."
    code, message = _round_trip(tmp_path, f"{sent_body}\npacket-id: {_PACKET_ID}", packet_body)
    assert code == 0, message


def test_percent_encoded_url_verifies_when_gmail_double_encodes(tmp_path: Path) -> None:
    """Gmail 이 `%` 를 `%25` 로 다시 감싸는 변형에서도 같은 값에서 만난다."""
    packet_body = f"안녕하세요.\n후보 프로필: {_ENCODED_URL}\n확인 부탁드립니다."
    doubled = _ENCODED_URL.replace("%", "%25")
    sent_body = f"안녕하세요.\n후보 프로필: {_wrap(doubled)}\n확인 부탁드립니다."
    code, message = _round_trip(tmp_path, f"{sent_body}\npacket-id: {_PACKET_ID}", packet_body)
    assert code == 0, message


# --- 6. 음성 — 다른 URL 이 감싸여 오면 여전히 불일치 ---------------------------


def test_a_different_wrapped_url_still_fails_verification(tmp_path: Path) -> None:
    packet_body = f"프로필: {_PLAIN_URL}"
    sent_body = f"프로필: {_wrap(_SECOND_URL)}"
    code, _ = _round_trip(tmp_path, sent_body, packet_body)
    assert code == 1


# --- 7. 순서 고정 — CRLF → 언랩 → 줄끝 공백 → packet-id 꼬리 → 끝 빈 줄 --------


def test_normalize_readback_applies_the_fixed_step_order() -> None:
    text = f"첫 줄   \r\n프로필: {_wrap(_PLAIN_URL)}\t\r\n\r\npacket-id: {_PACKET_ID}\r\n\r\n\r\n"
    assert normalize_readback(text) == f"첫 줄\n프로필: {_PLAIN_URL}"


def test_normalize_readback_is_idempotent() -> None:
    text = f"프로필({_wrap(_ENCODED_URL)})\npacket-id: {_PACKET_ID}\n"
    once = normalize_readback(text)
    assert normalize_readback(once) == once


# --- Codex 12차: readback 꼬리 packet-id 는 정확히 1줄이고 패킷 id 와 같아야 VERIFIED ---------------


def test_verify_requires_exactly_one_matching_packet_id_tail(tmp_path: Path) -> None:
    body = "본문 첫 줄\n본문 끝 줄"
    good = f"{body}\npacket-id: {_PACKET_ID}"
    assert _round_trip(tmp_path, good, body)[0] == 0
    code, message = _round_trip(tmp_path, body, body)
    assert code == 1 and "reason=tail_missing" in message
    code, message = _round_trip(tmp_path, f"{body}\npacket-id: 86e1abcd-deadbeef", body)
    assert code == 1 and "reason=tail_mismatch" in message
    code, message = _round_trip(tmp_path, f"{good}\npacket-id: {_PACKET_ID}", body)
    assert code == 1 and "reason=tail_duplicate" in message


def test_public_mark_cannot_create_verified_state(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    _claim(directory)
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _moment(5), "발송함 id")
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", 1, SendState.VERIFIED, "msg-1", _moment(6), "해시 일치")


def test_verify_and_mark_rejects_failed_readback_and_keeps_unverified(tmp_path: Path) -> None:
    body = "정상 본문"
    directory = _ledger(tmp_path)
    record_intent(directory, _intent(_mail_body(_JP, body)))
    _claim(directory, _mail_body(_JP, body))
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _moment(5), "발송함 id")
    packet_path, sent_path = _write_packet_and_sent(tmp_path, body, body)
    sent_path.write_text(_mail_body(_JP, body), encoding="utf-8")
    with pytest.raises(BriefInputError):
        cli_module.verify_and_mark(directory, packet_path, sent_path, "msg-1", _moment(6))
    current = load_intent(directory, _PACKET_ID, "gmail")
    assert current is not None
    assert current.state is SendState.SENT_UNVERIFIED


def test_verify_and_mark_rejects_packet_changed_after_send_claim(tmp_path: Path) -> None:
    original = "정상 본문"
    changed = "바뀐 본문"
    directory = _ledger(tmp_path)
    record_intent(directory, _intent(_mail_body(_JP, original)))
    _claim(directory, _mail_body(_JP, original))
    packet_path, sent_path = _write_packet_and_sent(
        tmp_path, changed, f"{changed}\npacket-id: {_PACKET_ID}"
    )
    with pytest.raises(BriefInputError):
        cli_module.verify_and_mark(directory, packet_path, sent_path, "msg-1", _moment(6))


def test_verify_and_mark_rejects_message_id_from_another_attempt(tmp_path: Path) -> None:
    body = "정상 본문"
    directory = _ledger(tmp_path)
    first = _intent(_mail_body(_JP, body))
    record_intent(directory, first)
    _claim(directory, _mail_body(_JP, body))
    open_new_attempt(
        directory,
        _PACKET_ID,
        "gmail",
        approval=_approval(),
        at=_moment(5),
        body_sha256=first.body_sha256,
        recipients_sha256=first.recipients_sha256,
    )
    claim_send(
        directory,
        _PACKET_ID,
        "gmail",
        2,
        at=_moment(6),
        evidence="러너가 발송 직전 청구",
        recipients_sha256=first.recipients_sha256,
        body_sha256=first.body_sha256,
    )
    mark(directory, _PACKET_ID, "gmail", 2, SendState.SENT_UNVERIFIED, "msg-2", _moment(7), "발송함 id")
    packet_path, sent_path = _write_packet_and_sent(
        tmp_path, body, f"{body}\npacket-id: {_PACKET_ID}"
    )
    with pytest.raises(BriefInputError):
        cli_module.verify_and_mark(directory, packet_path, sent_path, "msg-1", _moment(8))


def test_verify_and_mark_rejects_packet_recipients_changed_after_send_claim(tmp_path: Path) -> None:
    body = "정상 본문"
    directory = _ledger(tmp_path)
    original = _intent(_mail_body(_JP, body))
    record_intent(directory, original)
    _claim(directory, _mail_body(_JP, body))
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _moment(5), "발송함 id")

    packet_path, sent_path = _write_packet_and_sent(
        tmp_path, body, f"{body}\npacket-id: {_PACKET_ID}"
    )
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    payload["mail"]["to"] = ["other@example.org"]
    packet_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(BriefInputError):
        cli_module.verify_and_mark(directory, packet_path, sent_path, "msg-1", _moment(6))


def test_main_verify_mark_writes_verified_transition(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    body = "정상 본문"
    directory = _ledger(tmp_path)
    record_intent(directory, _intent(_mail_body(_JP, body)))
    _claim(directory, _mail_body(_JP, body))
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _moment(5), "발송함 id")
    packet_path, sent_path = _write_packet_and_sent(
        tmp_path, body, f"{body}\npacket-id: {_PACKET_ID}"
    )

    from humansearch.brief.__main__ import main

    code = main([
        "verify",
        "--packet",
        str(packet_path),
        "--sent",
        str(sent_path),
        "--mark-dir",
        str(directory),
        "--message-id",
        "msg-1",
        "--at",
        _moment(6).isoformat(),
    ])

    assert code == 0
    assert "VERIFIED" in capsys.readouterr().out
    verified = load_intent(directory, _PACKET_ID, "gmail")
    assert verified is not None
    assert verified.state is SendState.VERIFIED
