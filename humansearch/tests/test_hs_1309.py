"""HS-13.09 — 패킷을 git 밖에 0600 으로 저장·readback 하고 발송 장부가 재발송을 막는가.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5(packet.py·send_ledger.py)
      §7 D7(git 밖 0700/0600) · D9(at-most-once 발송 장부) · §9 HS-13.09 카드
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

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
    SendIntent,
    SendState,
    SourceRef,
    TeamMail,
    from_json,
    load_intent,
    mark,
    may_send,
    packet_id,
    reconcile,
    record_intent,
    to_json,
)
from humansearch.brief import packet as packet_module
from humansearch.brief import send_ledger as send_ledger_module

# --- 합성 패킷 ---------------------------------------------------------------

_JD_TEXT = "직무: 프로덕트 매니저\n요구: 실험 설계 경험 3년"
_RAW_SHA = hashlib.sha256(_JD_TEXT.encode("utf-8")).hexdigest()
_CLICKUP = "86e1abcd"
_TODAY = date(2026, 9, 10)
_PACKET_ID = f"20260910-{_CLICKUP}-{_RAW_SHA[:8]}"
_LEAD_URL = "https://www.linkedin.com/in/example-lead"
_AT = datetime(2026, 9, 10, 3, 20, 0, tzinfo=UTC)
_LATER = datetime(2026, 9, 10, 4, 0, 0, tzinfo=UTC)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _packet(text: str = "예시 문구") -> SearchPacket:
    body = f"{text}\n내부 공유 본문"
    return SearchPacket(
        packet_id=_PACKET_ID,
        position=PositionSpec(_CLICKUP, "예시 고객사", text, None, "정규직", "서울", None),
        jd=JdSource(_JD_TEXT, _RAW_SHA, "U1"),
        company=CompanyBrief(
            legal_name=Claim(text, ("C1",)),
            sources=(SourceRef("C1", "https://example.com/about", "회사 소개", _TODAY),),
        ),
        jd_packet=JdPacket(text, "링크드인 본문", "회사 소개 필드", "JD 본문 필드"),
        candidates=(
            CandidateLead(
                display_name=text,
                headline="프로덕트 매니저",
                linkedin_url=_LEAD_URL,
                education="예시대학원 석사",
                career="예시사 3년",
                match_reasons=("실험 설계 경험",),
                check_points=("도메인 적합성",),
                evidence=CandidateEvidence(("실험",), 1, 2, "석사", 2, (24, 18), 2, 8, 10),
                score=ScoreBreakdown(30, 15, 15, 15),
                email=EmailContact("lead@example.org", "https://example.org/lab", "연구실 페이지"),
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


def _intent(channel: str = "gmail", recorded_at: datetime = _AT) -> SendIntent:
    return SendIntent(
        packet_id=_PACKET_ID,
        channel=channel,
        recipients_sha256=_sha256("sangmokang@valueconnect.kr"),
        body_sha256=_sha256("본문"),
        recorded_at=recorded_at,
        state=SendState.INTENT,
    )


def _mode(target: Path) -> int:
    return stat.S_IMODE(target.stat().st_mode)


def _ledger(tmp_path: Path) -> Path:
    directory = tmp_path / "ledger"
    directory.mkdir(mode=0o700)
    os.chmod(directory, 0o700)
    return directory


# --- 1. packet_id ------------------------------------------------------------


def test_packet_id_is_date_clickup_and_sha8() -> None:
    sample = _packet()
    assert packet_id(sample.position, sample.jd, _TODAY) == f"20260910-{_CLICKUP}-{_RAW_SHA[:8]}"


def test_packet_id_rejects_clickup_id_outside_contract_shape() -> None:
    position = PositionSpec("86e1/../etc", "예시 고객사", "PM", None, None, None, None)
    with pytest.raises(BriefInputError):
        packet_id(position, _packet().jd, _TODAY)


# --- 2. JSON 왕복 ------------------------------------------------------------


def test_to_json_and_from_json_round_trip_is_identical() -> None:
    original = _packet()
    assert from_json(to_json(original)) == original


def test_to_json_encodes_date_enum_and_tuple_in_contract_shape() -> None:
    decoded = json.loads(to_json(_packet()))
    assert decoded["company"]["sources"][0]["checked_on"] == "2026-09-10"
    assert decoded["candidates"][0]["degree"] == "second"
    assert isinstance(decoded["boolean_queries"], list)


@settings(max_examples=50)
@given(st.text(min_size=1, max_size=60).filter(lambda value: value.strip() != ""))
def test_round_trip_holds_for_arbitrary_unicode_text_fields(text: str) -> None:
    original = _packet(text)
    assert from_json(to_json(original)) == original


def test_from_json_rejects_unknown_key() -> None:
    payload = json.loads(to_json(_packet()))
    payload["unexpected"] = 1
    with pytest.raises(BriefInputError):
        from_json(json.dumps(payload, ensure_ascii=False))


def test_from_json_rejects_missing_field() -> None:
    payload = json.loads(to_json(_packet()))
    del payload["mail"]
    with pytest.raises(BriefInputError):
        from_json(json.dumps(payload, ensure_ascii=False))


def test_from_json_rejects_type_mismatch() -> None:
    payload = json.loads(to_json(_packet()))
    payload["candidates"][0]["score"]["role"] = "30"
    with pytest.raises(BriefInputError):
        from_json(json.dumps(payload, ensure_ascii=False))


def test_from_json_rejects_broken_json() -> None:
    with pytest.raises(BriefInputError):
        from_json('{"packet_id": ')


# --- 3. PacketStore 권한·원자성 ----------------------------------------------


def test_store_creates_directory_with_0700(tmp_path: Path) -> None:
    directory = tmp_path / "packets"
    PacketStore(directory)
    assert _mode(directory) == 0o700


def test_store_rejects_directory_with_loose_permission(tmp_path: Path) -> None:
    directory = tmp_path / "loose"
    directory.mkdir()
    os.chmod(directory, 0o755)
    with pytest.raises(BriefInputError):
        PacketStore(directory)


def test_store_rejects_symlinked_directory(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    os.chmod(real, 0o700)
    link = tmp_path / "link"
    link.symlink_to(real)
    with pytest.raises(BriefInputError):
        PacketStore(link)


def test_save_writes_0600_file_named_by_packet_id(tmp_path: Path) -> None:
    store = PacketStore(tmp_path / "packets")
    target = store.save(_packet())
    assert target.name == f"{_PACKET_ID}.packet.json"
    assert _mode(target) == 0o600


def test_saving_same_packet_twice_leaves_one_file(tmp_path: Path) -> None:
    directory = tmp_path / "packets"
    store = PacketStore(directory)
    store.save(_packet())
    store.save(_packet())
    assert len(list(directory.iterdir())) == 1


def test_resaving_changed_packet_overwrites_in_place(tmp_path: Path) -> None:
    directory = tmp_path / "packets"
    store = PacketStore(directory)
    store.save(_packet("첫 문구"))
    target = store.save(_packet("두 번째 문구"))
    assert len(list(directory.iterdir())) == 1
    assert store.load(_PACKET_ID) == _packet("두 번째 문구")
    assert _mode(target) == 0o600


def test_load_returns_the_saved_packet(tmp_path: Path) -> None:
    store = PacketStore(tmp_path / "packets")
    store.save(_packet())
    assert store.load(_PACKET_ID) == _packet()


def test_load_rejects_missing_packet(tmp_path: Path) -> None:
    store = PacketStore(tmp_path / "packets")
    with pytest.raises(BriefInputError):
        store.load(_PACKET_ID)


def test_load_rejects_corrupted_file(tmp_path: Path) -> None:
    store = PacketStore(tmp_path / "packets")
    target = store.save(_packet())
    target.write_text("{broken", encoding="utf-8")
    with pytest.raises(BriefInputError):
        store.load(_PACKET_ID)


def test_readback_is_true_for_untouched_file(tmp_path: Path) -> None:
    store = PacketStore(tmp_path / "packets")
    packet = _packet()
    store.save(packet)
    assert store.readback(packet) is True


def test_readback_is_false_after_file_tampering(tmp_path: Path) -> None:
    store = PacketStore(tmp_path / "packets")
    packet = _packet()
    target = store.save(packet)
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["boolean_queries"] = []
    target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert store.readback(packet) is False


# --- 4. 발송 장부 (D9 · at-most-once) ----------------------------------------


def test_record_intent_reports_creation_and_writes_0600_file(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    stored, created = record_intent(directory, _intent())
    assert created is True
    assert stored == _intent()
    target = directory / f"{_PACKET_ID}.gmail.sent.json"
    assert _mode(target) == 0o600
    assert _mode(directory) == 0o700


def test_record_intent_twice_returns_the_first_intent_and_one_file(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    first, created_first = record_intent(directory, _intent())
    second, created_second = record_intent(directory, _intent(recorded_at=_LATER))
    assert created_first is True
    assert created_second is False
    assert second == first
    assert len(list(directory.iterdir())) == 1


def test_record_intent_creates_exactly_once_under_concurrent_callers(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    barrier = threading.Barrier(2)

    def attempt() -> bool:
        barrier.wait(timeout=5)
        _, created = record_intent(directory, _intent())
        return created

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result() for future in [pool.submit(attempt), pool.submit(attempt)]]
    assert sorted(results) == [False, True]
    assert len(list(directory.iterdir())) == 1


def test_may_send_is_true_only_while_no_intent_file_exists(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    assert may_send(directory, _PACKET_ID, "gmail") is True
    record_intent(directory, _intent())
    assert may_send(directory, _PACKET_ID, "gmail") is False


def test_may_send_stays_false_after_the_send_is_marked(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    mark(directory, _PACKET_ID, "gmail", SendState.SENT_UNVERIFIED, "msg-1", _AT)
    assert may_send(directory, _PACKET_ID, "gmail") is False
    mark(directory, _PACKET_ID, "gmail", SendState.VERIFIED, "msg-1", _LATER)
    assert may_send(directory, _PACKET_ID, "gmail") is False


def test_mark_walks_intent_to_sent_to_verified(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    sent = mark(directory, _PACKET_ID, "gmail", SendState.SENT_UNVERIFIED, "msg-1", _AT)
    assert sent.state is SendState.SENT_UNVERIFIED
    verified = mark(directory, _PACKET_ID, "gmail", SendState.VERIFIED, "msg-1", _LATER)
    assert verified.state is SendState.VERIFIED
    assert load_intent(directory, _PACKET_ID, "gmail") == verified


def test_mark_rejects_skipping_straight_to_verified(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", SendState.VERIFIED, "msg-1", _AT)


def test_mark_rejects_backward_transition(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    mark(directory, _PACKET_ID, "gmail", SendState.SENT_UNVERIFIED, "msg-1", _AT)
    mark(directory, _PACKET_ID, "gmail", SendState.VERIFIED, "msg-1", _LATER)
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", SendState.INTENT, "msg-1", _LATER)


def test_mark_rejects_sent_without_message_id(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", SendState.SENT_UNVERIFIED, None, _AT)


def test_mark_rejects_channel_without_recorded_intent(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", SendState.SENT_UNVERIFIED, "msg-1", _AT)


def test_channel_outside_lowercase_alphabet_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        record_intent(tmp_path / "ledger", _intent(channel="Gmail-1"))


def test_load_intent_returns_none_before_any_record(tmp_path: Path) -> None:
    assert load_intent(tmp_path / "ledger", _PACKET_ID, "gmail") is None


def test_send_intent_rejects_naive_datetime() -> None:
    with pytest.raises(BriefInputError):
        SendIntent(
            packet_id=_PACKET_ID,
            channel="gmail",
            recipients_sha256=_sha256("수신자"),
            body_sha256=_sha256("본문"),
            recorded_at=datetime(2026, 9, 10, 3, 20),  # noqa: DTZ001
            state=SendState.INTENT,
        )


# --- 5. reconcile — 끊긴 패킷을 사람이 확인한 뒤 정리한다 --------------------


def test_reconcile_promotes_to_sent_unverified_when_the_mail_was_found(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    settled = reconcile(
        directory, _PACKET_ID, "gmail", sent_found=True, message_id="msg-9", at=_LATER
    )
    assert settled.state is SendState.SENT_UNVERIFIED
    assert settled.message_id == "msg-9"
    assert may_send(directory, _PACKET_ID, "gmail") is False


def test_reconcile_requires_message_id_when_the_mail_was_found(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        reconcile(directory, _PACKET_ID, "gmail", sent_found=True, message_id=None, at=_LATER)


def test_reconcile_releases_the_intent_when_no_mail_was_found(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    released = reconcile(
        directory, _PACKET_ID, "gmail", sent_found=False, message_id=None, at=_LATER
    )
    assert released.state is SendState.INTENT
    assert not (directory / f"{_PACKET_ID}.gmail.sent.json").exists()
    release_file = directory / f"{_PACKET_ID}.gmail.released.json"
    assert _mode(release_file) == 0o600
    payload = json.loads(release_file.read_text(encoding="utf-8"))
    assert payload["reason"] == "reconcile-not-found"
    assert payload["released_at"] == _LATER.isoformat()
    assert payload["body_sha256"] == _sha256("본문")
    assert may_send(directory, _PACKET_ID, "gmail") is True


def test_reconcile_rejects_states_other_than_intent(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    mark(directory, _PACKET_ID, "gmail", SendState.SENT_UNVERIFIED, "msg-1", _AT)
    with pytest.raises(BriefInputError):
        reconcile(directory, _PACKET_ID, "gmail", sent_found=False, message_id=None, at=_LATER)


def test_reconcile_rejects_channel_without_recorded_intent(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    with pytest.raises(BriefInputError):
        reconcile(directory, _PACKET_ID, "gmail", sent_found=False, message_id=None, at=_LATER)


# --- 6. 정적 경계 ------------------------------------------------------------


def test_modules_hold_no_clock_network_or_process_access() -> None:
    forbidden = ("datetime.now", "socket", "requests", "smtplib", "subprocess")
    for module in (packet_module, send_ledger_module):
        source_file = module.__file__
        assert source_file is not None
        source = Path(source_file).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{source_file} 에 {token} 이 있다"
