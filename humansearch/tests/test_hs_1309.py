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
    PacketStore,
    PositionSpec,
    ScoreBreakdown,
    SearchPacket,
    SendIntent,
    SendState,
    SourceRef,
    TeamMail,
    Transition,
    from_json,
    load_attempt,
    load_intent,
    mark,
    may_send,
    packet_id,
    recipients_digest,
    record_intent,
    split_sections,
    split_two_field,
    to_json,
)
from humansearch.brief import claim_send as _raw_claim_send
from humansearch.brief import open_new_attempt as _raw_open_new_attempt
from humansearch.brief import packet as packet_module
from humansearch.brief import send_ledger as send_ledger_module

# --- 합성 패킷 ---------------------------------------------------------------

_JD_TEXT = "주요업무\n• 실험을 설계한다.\n자격요건\n• 실험 설계 경험이 있다.\n"
_RAW_SHA = hashlib.sha256(_JD_TEXT.encode("utf-8")).hexdigest()
_CLICKUP = "86e1abcd"
_TODAY = date(2026, 9, 10)
_PACKET_ID = f"{_CLICKUP}-{_RAW_SHA[:8]}"
_LEAD_URL = "https://www.linkedin.com/in/example-lead"
_AT = datetime(2026, 9, 10, 3, 20, 0, tzinfo=UTC)
_LATER = datetime(2026, 9, 10, 4, 0, 0, tzinfo=UTC)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()




def claim_send(
    dir: Path,
    packet_id: str,
    channel: str,
    attempt: int,
    *,
    at: datetime,
    evidence: str,
    recipients_sha256: str | None = None,
    body_sha256: str | None = None,
) -> tuple[SendIntent, bool]:
    return _raw_claim_send(
        dir,
        packet_id,
        channel,
        attempt,
        at=at,
        evidence=evidence,
        recipients_sha256=recipients_sha256 or _sha256("sangmokang@valueconnect.kr"),
        body_sha256=body_sha256 or _sha256("본문"),
    )


def open_new_attempt(
    dir: Path,
    packet_id: str,
    channel: str,
    *,
    approval: Approval,
    at: datetime,
    recipients_sha256: str | None = None,
    body_sha256: str | None = None,
) -> tuple[SendIntent, bool]:
    retry_seed = f"재시도 본문 {approval.from_attempt + 1}"
    return _raw_open_new_attempt(
        dir,
        packet_id,
        channel,
        approval=approval,
        at=at,
        recipients_sha256=recipients_sha256 or _sha256("sangmokang@valueconnect.kr"),
        body_sha256=body_sha256 or _sha256(retry_seed),
    )


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


def _packet(text: str = "예시 문구") -> SearchPacket:
    jp = _faithful_jd_packet(JdSource(_JD_TEXT, _RAW_SHA, "U1"))
    body = _mail_body(jp, "예시 문구\n내부 공유 본문")  # 자유 텍스트는 제목·법인명에만 — 본문 마커 충돌 방지
    return SearchPacket(
        packet_id=_PACKET_ID,
        created_on=_TODAY,
        position=PositionSpec(_CLICKUP, "예시 고객사", text, None, "정규직", "서울", None),
        jd=JdSource(_JD_TEXT, _RAW_SHA, "U1"),
        company=CompanyBrief(
            legal_name=Claim(text, ("C1",)),
            sources=(SourceRef("C1", "https://example.com/about", "회사 소개", _TODAY),),
        ),
        jd_packet=jp,
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


def _intent(
    channel: str = "gmail",
    recorded_at: datetime = _AT,
    attempt: int = 1,
    approval: Approval | None = None,
) -> SendIntent:
    return SendIntent(
        packet_id=_PACKET_ID,
        channel=channel,
        attempt=attempt,
        recipients_sha256=_sha256("sangmokang@valueconnect.kr"),
        body_sha256=_sha256("본문"),
        recorded_at=recorded_at,
        state=SendState.INTENT,
        approval=approval,
    )


def _approval(
    approved_by: str = "sangmokang@valueconnect.kr",
    search_query: str = 'in:sent subject:"[포지션]"',
    search_checked_at: str = "2026-09-10T04:00:00+00:00",
    reason: str = "발송함에서 찾지 못해 재시도를 승인한다",
    packet_id: str = _PACKET_ID,
    from_attempt: int = 1,
) -> Approval:
    return Approval(
        approved_by=approved_by,
        search_query=search_query,
        search_checked_at=search_checked_at,
        reason=reason,
        packet_id=packet_id,
        from_attempt=from_attempt,
    )


def _mode(target: Path) -> int:
    return stat.S_IMODE(target.stat().st_mode)


def _claim(directory: Path) -> None:
    """러너 규율 ②: 발송 직전 청구 1회(HS-13.09d). 청구 없는 SENT_UNVERIFIED 는 거부된다."""
    claim_send(directory, _PACKET_ID, "gmail", 1, at=_LATER, evidence="발송 직전 청구")


def _ledger(tmp_path: Path) -> Path:
    directory = tmp_path / "ledger"
    directory.mkdir(mode=0o700)
    os.chmod(directory, 0o700)
    return directory


# --- 1. packet_id ------------------------------------------------------------


def test_packet_id_is_clickup_and_sha8() -> None:
    sample = _packet()
    assert packet_id(sample.position, sample.jd) == f"{_CLICKUP}-{_RAW_SHA[:8]}"


def test_packet_id_rejects_clickup_id_outside_contract_shape() -> None:
    position = PositionSpec("86e1/../etc", "예시 고객사", "PM", None, None, None, None)
    with pytest.raises(BriefInputError):
        packet_id(position, _packet().jd)


# --- 2. JSON 왕복 ------------------------------------------------------------


def test_to_json_and_from_json_round_trip_is_identical() -> None:
    original = _packet()
    assert from_json(to_json(original)) == original


def test_to_json_encodes_date_enum_and_tuple_in_contract_shape() -> None:
    decoded = json.loads(to_json(_packet()))
    assert decoded["schema_version"] == 1
    assert decoded["company"]["sources"][0]["checked_on"] == "2026-09-10"
    assert decoded["candidates"][0]["degree"] == "second"
    assert isinstance(decoded["boolean_queries"], list)


@settings(deadline=None, max_examples=50)
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


def test_from_json_rejects_legacy_packet_without_schema_version() -> None:
    payload = json.loads(to_json(_packet()))
    del payload["schema_version"]
    with pytest.raises(BriefInputError):
        from_json(json.dumps(payload, ensure_ascii=False))


def test_from_json_rejects_packet_with_unknown_schema_version() -> None:
    payload = json.loads(to_json(_packet()))
    payload["schema_version"] = 2
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
    assert len(list(directory.glob("*.packet.json"))) == 1


def test_resaving_changed_packet_overwrites_in_place(tmp_path: Path) -> None:
    directory = tmp_path / "packets"
    store = PacketStore(directory)
    store.save(_packet("첫 문구"))
    target = store.save(_packet("두 번째 문구"))
    assert len(list(directory.glob("*.packet.json"))) == 1
    assert store.load(_PACKET_ID) == _packet("두 번째 문구")
    assert _mode(target) == 0o600


def test_save_rejects_changed_packet_after_send_intent_exists(tmp_path: Path) -> None:
    directory = tmp_path / "packets"
    store = PacketStore(directory)
    original = _packet("첫 문구")
    store.save(original)
    record_intent(directory, _intent())

    with pytest.raises(BriefInputError):
        store.save(_packet("두 번째 문구"))

    assert store.load(_PACKET_ID) == original


def test_recipients_digest_is_sorted_and_distinguishes_to_from_cc() -> None:
    assert recipients_digest(
        ("z@example.org", "a@example.org"), ("c@example.org",)
    ) == recipients_digest(("a@example.org", "z@example.org"), ("c@example.org",))
    assert recipients_digest(("a@example.org",), ("c@example.org",)) != recipients_digest(
        ("a@example.org", "c@example.org"), ()
    )


def test_recipients_digest_rejects_duplicate_across_to_and_cc() -> None:
    with pytest.raises(BriefInputError):
        recipients_digest(("a@example.org",), ("a@example.org",))


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


# --- 4. 발송 장부 — 영구 묘비 + attempt (D9) --------------------------------


def test_record_intent_reports_creation_and_writes_0600_attempt_file(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    stored, created = record_intent(directory, _intent())
    assert created is True
    assert stored == _intent()
    target = directory / f"{_PACKET_ID}.gmail.a1.sent.json"
    assert _mode(target) == 0o600
    assert _mode(directory) == 0o700


def test_record_intent_twice_returns_the_existing_attempt_and_one_file(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    first, created_first = record_intent(directory, _intent())
    second, created_second = record_intent(directory, _intent(recorded_at=_LATER))
    assert created_first is True
    assert created_second is False
    assert second == first
    assert len(list(directory.glob("*.sent.json"))) == 1


def test_record_intent_creates_exactly_once_under_concurrent_callers(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    barrier = threading.Barrier(2)

    def attempt() -> bool:
        barrier.wait(timeout=60)
        _, created = record_intent(directory, _intent())
        return created

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result() for future in [pool.submit(attempt), pool.submit(attempt)]]
    assert sorted(results) == [False, True]
    assert len(list(directory.glob("*.sent.json"))) == 1


def test_record_intent_rejects_attempt_other_than_one(tmp_path: Path) -> None:
    with pytest.raises(BriefInputError):
        record_intent(tmp_path / "ledger", _intent(attempt=2, approval=_approval()))


def test_may_send_is_true_only_while_no_attempt_file_exists(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    assert may_send(directory, _PACKET_ID, "gmail") is True
    record_intent(directory, _intent())
    assert may_send(directory, _PACKET_ID, "gmail") is False


@pytest.mark.parametrize(
    "crash_point",
    ["after_intent", "after_send", "after_mark", "after_readback"],
)
def test_rerun_after_any_crash_point_grants_no_send(tmp_path: Path, crash_point: str) -> None:
    """중간에 끊긴 뒤 재실행해도 발송 허가는 나오지 않는다 — 허가는 청구 1회(claim_send) 뿐이다."""
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    if crash_point != "after_intent":
        _claim(directory)
    if crash_point in {"after_mark", "after_readback"}:
        mark(
            directory,
            _PACKET_ID,
            "gmail",
            1,
            SendState.SENT_UNVERIFIED,
            "msg-1",
            _LATER,
            "발송함 id",
        )
    if crash_point == "after_readback":
        assert load_intent(directory, _PACKET_ID, "gmail") is not None
    replayed, created = record_intent(directory, _intent())
    assert created is False
    assert may_send(directory, _PACKET_ID, "gmail") is False
    assert replayed.attempt == 1


def test_mark_walks_claimed_to_sent_and_appends_transitions(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    _claim(directory)
    sent = mark(
        directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _LATER, "발송함 id"
    )
    assert sent.state is SendState.SENT_UNVERIFIED
    assert tuple(step.state for step in sent.transitions) == (
        SendState.SEND_CLAIMED,
        SendState.SENT_UNVERIFIED,
    )
    assert sent.transitions[1].evidence == "발송함 id"
    assert load_intent(directory, _PACKET_ID, "gmail") == sent


def test_mark_rejects_skipping_straight_to_verified(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", 1, SendState.VERIFIED, "msg-1", _LATER, "건너뛰기")


def test_mark_rejects_backward_transition(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    _claim(directory)
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _LATER, "발송함 id")
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", 1, SendState.INTENT, "msg-1", _LATER, "되돌리기")


def test_mark_rejects_abandoned_as_a_manual_transition(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", 1, SendState.ABANDONED, None, _LATER, "임의 포기")


def test_mark_rejects_sent_without_message_id(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, None, _LATER, "id 없음")


def test_mark_rejects_channel_without_recorded_attempt(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    with pytest.raises(BriefInputError):
        mark(
            directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _AT, "없는 시도"
        )


def test_mark_rejects_an_attempt_that_is_not_the_latest(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    open_new_attempt(directory, _PACKET_ID, "gmail", approval=_approval(), at=_LATER)
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _LATER, "과거")


# --- 5. open_new_attempt — 승인 없이는 두 번째 시도가 열리지 않는다 ----------


def test_open_new_attempt_abandons_the_uncertain_attempt_and_keeps_its_file(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    fresh, created = open_new_attempt(
        directory, _PACKET_ID, "gmail", approval=_approval(), at=_LATER
    )
    assert created is True
    assert fresh.attempt == 2
    assert fresh.state is SendState.INTENT
    assert fresh.approval == _approval()
    first_file = directory / f"{_PACKET_ID}.gmail.a1.sent.json"
    assert first_file.exists(), "묘비는 지우거나 이름을 바꾸지 않는다"
    assert (directory / f"{_PACKET_ID}.gmail.a2.sent.json").exists()
    abandoned = load_attempt(directory, _PACKET_ID, "gmail", 1)
    assert abandoned is not None
    assert abandoned.state is SendState.ABANDONED
    assert abandoned.transitions[-1].state is SendState.ABANDONED
    assert abandoned.attempt == 1


def test_open_new_attempt_can_be_repeated_for_a_second_uncertain_attempt(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    open_new_attempt(directory, _PACKET_ID, "gmail", approval=_approval(), at=_LATER)
    third, created = open_new_attempt(
        directory, _PACKET_ID, "gmail", approval=_approval(from_attempt=2), at=_LATER
    )
    assert created is True
    assert third.attempt == 3
    assert len(list(directory.glob("*.sent.json"))) == 3


@pytest.mark.parametrize("field", ["approved_by", "search_query", "search_checked_at", "reason"])
def test_open_new_attempt_rejects_blank_approval_field(tmp_path: Path, field: str) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        open_new_attempt(
            directory,
            _PACKET_ID,
            "gmail",
            approval=_approval(**{field: "   "}),  # type: ignore[arg-type]
            at=_LATER,
        )


def test_open_new_attempt_is_refused_once_the_send_is_known(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    record_intent(directory, _intent())
    _claim(directory)
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _LATER, "발송함 id")
    with pytest.raises(BriefInputError):
        open_new_attempt(directory, _PACKET_ID, "gmail", approval=_approval(), at=_LATER)


def test_open_new_attempt_is_refused_without_any_recorded_attempt(tmp_path: Path) -> None:
    directory = tmp_path / "ledger"
    with pytest.raises(BriefInputError):
        open_new_attempt(directory, _PACKET_ID, "gmail", approval=_approval(), at=_LATER)


def test_open_new_attempt_opens_exactly_once_under_concurrent_callers(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    barrier = threading.Barrier(2)

    def attempt() -> str:
        barrier.wait(timeout=60)
        try:
            _, created = open_new_attempt(
                directory, _PACKET_ID, "gmail", approval=_approval(), at=_LATER
            )
        except BriefInputError:
            return "stale-approval"  # 잠금 뒤에 들어온 쪽은 최신 attempt 가 2 라 승인(from_attempt=1)이 낡았다
        return "opened" if created else "not-opened"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result() for future in [pool.submit(attempt), pool.submit(attempt)]]
    assert sorted(results) == ["opened", "stale-approval"]
    assert len(list(directory.glob("*.sent.json"))) == 2


# --- 6. 타입 불변식 ----------------------------------------------------------


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
            attempt=1,
            recipients_sha256=_sha256("수신자"),
            body_sha256=_sha256("본문"),
            recorded_at=datetime(2026, 9, 10, 3, 20),  # noqa: DTZ001
            state=SendState.INTENT,
        )


def test_retry_attempt_without_approval_is_rejected_by_the_type() -> None:
    with pytest.raises(BriefInputError):
        _intent(attempt=2)


def test_first_attempt_with_approval_is_rejected_by_the_type() -> None:
    with pytest.raises(BriefInputError):
        _intent(approval=_approval())


def test_abandoned_state_cannot_carry_a_message_id() -> None:
    with pytest.raises(BriefInputError):
        SendIntent(
            packet_id=_PACKET_ID,
            channel="gmail",
            attempt=1,
            recipients_sha256=_sha256("수신자"),
            body_sha256=_sha256("본문"),
            recorded_at=_AT,
            state=SendState.ABANDONED,
            message_id="msg-1",
            transitions=(Transition(_LATER, SendState.ABANDONED, "포기"),),
        )


# --- 7. 정적 경계 ------------------------------------------------------------


def test_modules_hold_no_clock_network_or_process_access() -> None:
    forbidden = ("datetime.now", "socket", "requests", "smtplib", "subprocess")
    for module in (packet_module, send_ledger_module):
        source_file = module.__file__
        assert source_file is not None
        source = Path(source_file).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{source_file} 에 {token} 이 있다"
