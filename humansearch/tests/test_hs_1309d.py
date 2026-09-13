"""HS-13.09d — 발송 허가는 소비되는 청구(claim)다. 같은 attempt 로 Gmail 을 두 번 부를 수 없다.

Codex V1 7차 반례: `record_intent` 의 `created=True` 는 불리언이라 같은 프로세스가 그 값을
들고 `send_message` 를 두 번 불러도 장부는 attempt 하나·message_id 하나만 남긴다.
처방: INTENT → SEND_CLAIMED 전이를 **배타 생성 마커 파일**로 딱 한 번만 허용하고,
SENT_UNVERIFIED 는 SEND_CLAIMED 에서만 갈 수 있게 한다. 러너는 청구 1건당 발송 1회다.

계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §5 send_claim.py · §7 D9 · §10 ②.
"""

from __future__ import annotations

import hashlib
import stat
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from humansearch.brief import (
    Approval,
    BriefInputError,
    SendIntent,
    SendState,
    claim_send,
    load_intent,
    mark,
    open_new_attempt,
    record_intent,
)

_PACKET_ID = "86e1abcd-0123abcd"
_AT = datetime(2026, 9, 10, 3, 20, 0, tzinfo=UTC)
_CLAIM_AT = datetime(2026, 9, 10, 3, 30, 0, tzinfo=UTC)
_LATER = datetime(2026, 9, 10, 4, 0, 0, tzinfo=UTC)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_raw_claim_send = claim_send
_raw_open_new_attempt = open_new_attempt


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
    body_seed = "본문" if attempt == 1 else f"재시도 본문 {attempt}"
    return _raw_claim_send(
        dir,
        packet_id,
        channel,
        attempt,
        at=at,
        evidence=evidence,
        recipients_sha256=recipients_sha256 or _sha256("sangmokang@valueconnect.kr"),
        body_sha256=body_sha256 or _sha256(body_seed),
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
    """테스트 기본 재시도 digest 를 붙인다. 발송 권한은 claim_send 의 True 만이다."""
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


def _intent() -> SendIntent:
    return SendIntent(
        packet_id=_PACKET_ID,
        channel="gmail",
        attempt=1,
        recipients_sha256=_sha256("sangmokang@valueconnect.kr"),
        body_sha256=_sha256("본문"),
        recorded_at=_AT,
        state=SendState.INTENT,
    )


def _approval(from_attempt: int) -> Approval:
    return Approval(
        approved_by="sangmokang@valueconnect.kr",
        search_query='in:sent subject:"[포지션]"',
        search_checked_at="2026-09-10T04:00:00+00:00",
        reason="발송함에서 찾지 못해 재시도를 승인한다",
        packet_id=_PACKET_ID,
        from_attempt=from_attempt,
    )


def _ledger(tmp_path: Path) -> Path:
    directory = tmp_path / "ledger"
    directory.mkdir(mode=0o700)
    return directory


def _claim(directory: Path, attempt: int = 1, at: datetime = _CLAIM_AT) -> tuple[SendIntent, bool]:
    return claim_send(
        directory, _PACKET_ID, "gmail", attempt, at=at, evidence="러너가 발송 직전 청구"
    )


def _claim_with_digest(
    directory: Path,
    *,
    recipients_sha256: str | None = None,
    body_sha256: str | None = None,
) -> tuple[SendIntent, bool]:
    return claim_send(
        directory,
        _PACKET_ID,
        "gmail",
        1,
        at=_CLAIM_AT,
        evidence="러너가 발송 직전 청구",
        recipients_sha256=recipients_sha256 or _sha256("sangmokang@valueconnect.kr"),
        body_sha256=body_sha256 or _sha256("본문"),
    )


def _marker(directory: Path, attempt: int = 1) -> Path:
    return directory / f"{_PACKET_ID}.gmail.a{attempt}.claim.json"


# --- 1. 청구는 한 번만 --------------------------------------------------------


def test_claim_moves_intent_to_send_claimed_and_leaves_a_marker(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    claimed, won = _claim(directory)
    assert won is True
    assert claimed.state is SendState.SEND_CLAIMED
    assert claimed.message_id is None
    assert [step.state for step in claimed.transitions] == [SendState.SEND_CLAIMED]
    marker = _marker(directory)
    assert marker.is_file()
    assert stat.S_IMODE(marker.stat().st_mode) == 0o600
    stored = load_intent(directory, _PACKET_ID, "gmail")
    assert stored is not None
    assert stored.state is SendState.SEND_CLAIMED


def test_second_claim_on_the_same_attempt_is_refused(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    first, won_first = _claim(directory)
    second, won_second = _claim(directory, at=_LATER)
    assert won_first is True
    assert won_second is False
    assert second == first
    assert len(second.transitions) == 1


def test_claim_is_granted_exactly_once_under_concurrent_callers(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    workers = 6
    barrier = threading.Barrier(workers)

    def attempt() -> bool:
        barrier.wait(timeout=60)
        _, won = _claim(directory)
        return won

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = [future.result() for future in [pool.submit(attempt) for _ in range(workers)]]
    assert results.count(True) == 1
    stored = load_intent(directory, _PACKET_ID, "gmail")
    assert stored is not None
    assert len(stored.transitions) == 1


# --- 2. 청구 없는 발송 표시는 거부 ------------------------------------------------


def test_mark_sent_without_claim_is_rejected(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        mark(
            directory,
            _PACKET_ID,
            "gmail",
            1,
            SendState.SENT_UNVERIFIED,
            "msg-1",
            _LATER,
            "청구 없음",
        )


def test_mark_cannot_produce_send_claimed_by_itself(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        mark(directory, _PACKET_ID, "gmail", 1, SendState.SEND_CLAIMED, None, _LATER, "손 청구")
    assert not _marker(directory).exists()


def test_claimed_attempt_walks_to_sent_and_verified(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    _claim(directory)
    sent = mark(
        directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _LATER, "발송함 id"
    )
    assert sent.state is SendState.SENT_UNVERIFIED
    assert [step.state for step in sent.transitions] == [
        SendState.SEND_CLAIMED,
        SendState.SENT_UNVERIFIED,
    ]


# --- 3. 마커만 남고 죽은 경우 = 보냈는지 모름 → 재청구 불가, 승인 재시도만 ----------------


def test_orphan_marker_means_unknown_send_and_blocks_reclaim(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    _marker(directory).write_text("{}", encoding="utf-8")
    current, won = _claim(directory)
    assert won is False
    assert current.state is SendState.INTENT
    reopened, opened = open_new_attempt(
        directory, _PACKET_ID, "gmail", approval=_approval(from_attempt=1), at=_LATER
    )
    assert opened is True
    assert reopened.attempt == 2
    _, won_again = _claim(directory, attempt=2, at=_LATER)
    assert won_again is True
    assert _marker(directory, 2).is_file()


def test_open_new_attempt_accepts_a_claimed_but_unsent_attempt(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    _claim(directory)
    reopened, opened = open_new_attempt(
        directory, _PACKET_ID, "gmail", approval=_approval(from_attempt=1), at=_LATER
    )
    assert opened is True
    assert reopened.state is SendState.INTENT
    first = directory / f"{_PACKET_ID}.gmail.a1.sent.json"
    assert '"abandoned"' in first.read_text(encoding="utf-8")


# --- 4. 형식·순서 위반 -----------------------------------------------------------


def test_claim_rejects_attempt_that_is_not_the_latest(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        _claim(directory, attempt=2)


def test_claim_rejects_channel_without_recorded_intent(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    with pytest.raises(BriefInputError):
        _claim(directory)


def test_claim_rejects_an_attempt_whose_send_is_already_known(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    _claim(directory)
    mark(directory, _PACKET_ID, "gmail", 1, SendState.SENT_UNVERIFIED, "msg-1", _LATER, "발송함 id")
    with pytest.raises(BriefInputError):
        _claim(directory, at=_LATER)


def test_send_claimed_intent_cannot_carry_a_message_id() -> None:
    with pytest.raises(BriefInputError):
        SendIntent(
            packet_id=_PACKET_ID,
            channel="gmail",
            attempt=1,
            recipients_sha256=_sha256("sangmokang@valueconnect.kr"),
            body_sha256=_sha256("본문"),
            recorded_at=_AT,
            state=SendState.SEND_CLAIMED,
            message_id="msg-1",
            transitions=(),
        )


def test_claim_rejects_blank_evidence(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        claim_send(directory, _PACKET_ID, "gmail", 1, at=_CLAIM_AT, evidence="   ")


def test_claim_rejects_body_digest_changed_after_intent(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        _claim_with_digest(directory, body_sha256=_sha256("바뀐 본문"))


def test_claim_rejects_recipients_digest_changed_after_intent(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        _claim_with_digest(directory, recipients_sha256=_sha256("a,b,c,d"))


def test_claim_rejects_both_body_and_recipients_changed_after_intent(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    record_intent(directory, _intent())
    with pytest.raises(BriefInputError):
        _claim_with_digest(
            directory,
            recipients_sha256=_sha256("a,b,c,d"),
            body_sha256=_sha256("바뀐 본문"),
        )
