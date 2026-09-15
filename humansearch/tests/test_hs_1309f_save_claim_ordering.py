"""PR #83 F83-2 — `PacketStore.save` 의 확인·교체를 발송 장부와 같은 잠금 안에 넣는다.

Codex 13차 반례(순서 뒤집기): save(B) 가 "발송 intent 없음"을 확인한 **뒤**에
record_intent(A)+claim_send(A) 가 끼어들면, 청구는 A 본문으로 발송 권한을 얻었는데
저장 파일은 B 로 바뀐다. 승인 digest 와 저장 패킷이 갈라진 채 발송이 열린다.

계약(v7 §2 I-b): `claim_send` 가 True 를 돌려준 뒤에는 새 attempt 가 열리기 전까지
같은 packet_id 의 저장 패킷 본문·수신자 digest 를 바꾸는 `save` 를 거부해야 한다.
순서가 뒤집혀도(save 확인 → 청구 → save 교체) 같다.

사후 digest 재검사만으로는 못 막는다 — 승인 본문이 이미 사라진 뒤이기 때문이다.
그래서 여기서는 **잠금 자체**를 시험한다.
"""

from __future__ import annotations

import contextlib
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest
from test_hs_1309e import (
    _CLAIM_AT,
    _PACKET_ID,
    _current_packet,
    _intent,
    _ledger,
    _sha256,
    claim_send,
)

from humansearch.brief import BriefInputError, PacketStore, SearchPacket, record_intent
from humansearch.brief import packet as packet_module

_JOIN_TIMEOUT = 60.0
_BLOCKED_WAIT = 2.0
_ROUNDS = 100


def _other_packet() -> SearchPacket:
    """A 와 본문만 다른 패킷 B — 저장이 교체되면 digest 로 바로 드러난다."""
    current = _current_packet()
    body = current.mail.body + "추가 줄\n"
    return replace(current, mail=replace(current.mail, body=body, body_sha256=_sha256(body)))


def _take_claim(directory: Path) -> bool:
    """record_intent(A) + claim_send(A). 발송 권한을 실제로 땄으면 True."""
    try:
        record_intent(directory, _intent())
        _, won = claim_send(directory, _PACKET_ID, "gmail", 1, at=_CLAIM_AT, evidence="발송 직전 청구")
    except BriefInputError:
        return False
    return won


# ---------------------------------------------------------------- ① 결정적: 순서 뒤집기


def test_save_cannot_replace_a_packet_while_a_claim_is_being_taken(
    tmp_path: Path, monkeypatch: object
) -> None:
    """save(B) 의 intent 확인 직후에 청구가 끼어들어도 승인 본문이 사라지면 안 된다."""
    directory = _ledger(tmp_path)
    approved = _current_packet()
    store = PacketStore(directory)
    store.save(approved)

    claimed: list[bool] = []
    workers: list[threading.Thread] = []
    original = PacketStore._has_send_intent

    def wedge(self: PacketStore, packet_id: str) -> bool:
        seen = original(self, packet_id)
        if not workers:
            worker = threading.Thread(
                target=lambda: claimed.append(_take_claim(directory)), daemon=True
            )
            workers.append(worker)
            worker.start()
            worker.join(timeout=_BLOCKED_WAIT)
        return seen

    PacketStore._has_send_intent = wedge  # type: ignore[method-assign]
    try:
        try:
            store.save(_other_packet())
            saved = "accepted"
        except BriefInputError:
            saved = "rejected"
    finally:
        PacketStore._has_send_intent = original  # type: ignore[method-assign]
    workers[0].join(timeout=_JOIN_TIMEOUT)

    stored = store.load(_PACKET_ID)
    won = bool(claimed and claimed[0])
    assert not (won and stored.mail.body_sha256 != approved.mail.body_sha256)
    assert saved == "rejected" or won is False


def test_a_claim_wedged_into_the_same_thread_check_cannot_survive(tmp_path: Path) -> None:
    """같은 스레드가 확인 도중 청구를 끼워 넣어도(재진입) 승인 본문은 교체되지 않는다.

    flock 은 같은 스레드의 재진입을 막지 않는다 — 잠금만으로는 이 경로가 열린 채로 남는다.
    """
    directory = _ledger(tmp_path)
    approved = _current_packet()
    store = PacketStore(directory)
    store.save(approved)
    fired: list[bool] = []
    original = PacketStore._has_send_intent

    def wedge(self: PacketStore, packet_id: str) -> bool:
        seen = original(self, packet_id)
        if not fired:
            fired.append(_take_claim(directory))
        return seen

    PacketStore._has_send_intent = wedge  # type: ignore[method-assign]
    try:
        with pytest.raises(BriefInputError):
            store.save(_other_packet())
    finally:
        PacketStore._has_send_intent = original  # type: ignore[method-assign]
    assert fired == [True]
    assert store.load(_PACKET_ID).mail.body_sha256 == approved.mail.body_sha256


# ---------------------------------------------------------------- ② 동시 경합


def _contention_round(directory: Path) -> tuple[bool, bool]:
    """(청구를 땄는가, 저장 패킷이 승인 본문 그대로인가)."""
    directory.mkdir(mode=0o700)
    approved = _current_packet()
    store = PacketStore(directory)
    store.save(approved)
    barrier = threading.Barrier(2)

    def save_side() -> None:
        barrier.wait(timeout=_JOIN_TIMEOUT)
        with contextlib.suppress(BriefInputError):
            store.save(_other_packet())

    def claim_side() -> bool:
        barrier.wait(timeout=_JOIN_TIMEOUT)
        return _take_claim(directory)

    with ThreadPoolExecutor(max_workers=2) as pool:
        saving = pool.submit(save_side)
        claiming = pool.submit(claim_side)
        saving.result()
        won = claiming.result()
    stored = store.load(_PACKET_ID)
    return won, stored.mail.body_sha256 == approved.mail.body_sha256


def test_concurrent_save_and_claim_never_split_the_approved_digest(tmp_path: Path) -> None:
    """어느 회차에서도 '청구 True + 저장 digest ≠ 승인 digest' 가 나오면 안 된다."""
    violations: list[int] = []
    for index in range(_ROUNDS):
        won, intact = _contention_round(tmp_path / f"round{index:03d}")
        if won and not intact:
            violations.append(index)
    assert violations == []


# ---------------------------------------------------------------- ③ 같은 잠금인가


def test_a_held_channel_lock_blocks_packet_save(tmp_path: Path) -> None:
    """장부 잠금을 쥔 스레드가 있으면 save 는 들어오지 못한다 — 둘이 같은 잠금이라는 뜻이다."""
    directory = _ledger(tmp_path)
    store = PacketStore(directory)
    store.save(_current_packet())
    holder_ready = threading.Event()
    release = threading.Event()
    finished: list[int] = []

    def holder() -> None:
        with packet_module._channel_lock(directory, _PACKET_ID, "gmail"):
            holder_ready.set()
            release.wait(timeout=_JOIN_TIMEOUT)

    def saver() -> None:
        holder_ready.wait(timeout=_JOIN_TIMEOUT)
        with contextlib.suppress(BriefInputError):
            store.save(_other_packet())
        finished.append(1)

    threads = [
        threading.Thread(target=holder, daemon=True),
        threading.Thread(target=saver, daemon=True),
    ]
    for thread in threads:
        thread.start()
    holder_ready.wait(timeout=_JOIN_TIMEOUT)
    threads[1].join(timeout=_BLOCKED_WAIT)
    assert finished == []  # 장부 잠금 보유 중에는 저장이 시작되지 못한다
    release.set()
    for thread in threads:
        thread.join(timeout=_JOIN_TIMEOUT)
    assert finished == [1]
