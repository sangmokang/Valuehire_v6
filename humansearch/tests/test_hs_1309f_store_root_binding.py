"""PR #83 2차 F83-2 — 잠금·패킷 파일을 **정규화한 저장 루트 하나**에 묶는다.

Codex V1 반증: 잠금 경로가 호출자가 준 디렉터리에 종속되고, `verify_and_mark` 는 `dir` 을
잠근 뒤 **별도** `packet_path` 를 읽는다. 그래서 장부는 A 디렉터리, 검증 대상 패킷은 B
디렉터리인 조합이 VERIFIED 로 통과한다.

계약:
- 모든 공개 진입점은 받은 디렉터리를 `resolve()` 한 값으로 잠금·파일 경로를 만든다
  (심볼릭 링크로 같은 디렉터리를 두 이름으로 불러도 잠금이 하나로 합쳐진다).
- `verify_and_mark` 는 `packet_path.resolve()` 가 `(dir/<packet_id>.packet.json).resolve()` 와
  다르면 거부한다.
- 실제 **별도 프로세스** 둘이 경합해도 "청구 True ∧ 저장 digest ≠ 청구 digest" 는 0.

1차 시험은 스레드·같은 디렉터리만 썼다. 이 파일이 그 공백을 닫는다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
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

import humansearch
from humansearch.brief import (
    BriefInputError,
    PacketStore,
    SearchPacket,
    SendState,
    mark,
    record_intent,
)
from humansearch.brief.cli import verify_and_mark

_WAIT = 60.0
_POLL = 0.002
_PROCESS_ROUNDS = 10

_CHILD = '''
import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[2])
import test_hs_1309e as t
from humansearch.brief import BriefInputError, record_intent
from humansearch.brief import claim_send as raw_claim

directory = Path(sys.argv[1])
gate = directory / "go"
(directory / "child.ready").write_text("1", encoding="utf-8")
while not gate.exists():
    time.sleep(0.001)
packet = t._current_packet()
try:
    record_intent(directory, t._intent())
    _, won = raw_claim(
        directory, t._PACKET_ID, "gmail", 1, at=t._CLAIM_AT, evidence="child",
        recipients_sha256=t.recipients_digest(packet.mail.to, packet.mail.cc),
        body_sha256=packet.mail.body_sha256,
    )
except BriefInputError:
    won = False
print("CLAIM:" + ("True" if won else "False"))
'''


def _other_packet() -> SearchPacket:
    current = _current_packet()
    body = current.mail.body + "추가 줄\n"
    return replace(current, mail=replace(current.mail, body=body, body_sha256=_sha256(body)))


def _take_claim(directory: Path) -> bool:
    try:
        record_intent(directory, _intent())
        _, won = claim_send(
            directory, _PACKET_ID, "gmail", 1, at=_CLAIM_AT, evidence="발송 직전 청구"
        )
    except BriefInputError:
        return False
    return won


# ---------------------------------------------------------------- 정규 저장 루트


def _aliased(tmp_path: Path) -> tuple[Path, Path]:
    """(실체 디렉터리, 심볼릭 링크를 지나는 같은 디렉터리)."""
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    ledger = real / "ledger"
    ledger.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    return ledger, link / "ledger"


def test_store_root_is_canonical(tmp_path: Path) -> None:
    """같은 디렉터리를 두 이름으로 불러도 저장 루트는 하나로 합쳐져야 한다."""
    ledger, alias = _aliased(tmp_path)
    assert not alias.is_symlink()  # 링크는 부모 쪽에 있다
    assert PacketStore(alias).dir == PacketStore(ledger).dir
    assert PacketStore(alias).path_for(_PACKET_ID) == PacketStore(ledger).path_for(_PACKET_ID)


def test_an_aliased_directory_cannot_take_a_second_claim(tmp_path: Path) -> None:
    """별칭 경로로 다시 청구해도 발송 권한은 한 번만 나간다(회귀 방지)."""
    ledger, alias = _aliased(tmp_path)
    PacketStore(ledger).save(_current_packet())
    assert _take_claim(ledger) is True
    assert _take_claim(alias) is False


# ---------------------------------------------------------------- packet_path 동일성


def _prepare_verified_input(directory: Path, root: Path) -> Path:
    """claim → SENT_UNVERIFIED 까지 진행하고 readback 영수증 경로를 돌려준다."""
    packet = _current_packet()
    PacketStore(directory).save(packet)
    record_intent(directory, _intent())
    claim_send(directory, _PACKET_ID, "gmail", 1, at=_CLAIM_AT, evidence="청구")
    mark(
        directory,
        _PACKET_ID,
        "gmail",
        1,
        state=SendState.SENT_UNVERIFIED,
        at=_CLAIM_AT,
        evidence="보냈다",
        message_id="<m1@example.com>",
    )
    body = packet.mail.body + f"packet-id: {_PACKET_ID}\n"
    receipt = {
        "packet_id": _PACKET_ID,
        "channel": "gmail",
        "attempt": 1,
        "message_id": "<m1@example.com>",
        "to": list(packet.mail.to),
        "cc": list(packet.mail.cc),
        "body": body,
    }
    sent = root / "receipt.sent.json"
    sent.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
    return sent


def test_verify_and_mark_accepts_the_canonical_packet_path(tmp_path: Path) -> None:
    directory = _ledger(tmp_path)
    sent = _prepare_verified_input(directory, tmp_path)
    canonical = PacketStore(directory).path_for(_PACKET_ID)
    result = verify_and_mark(directory, canonical, sent, "<m1@example.com>", _CLAIM_AT)
    assert result.state is SendState.VERIFIED


def test_verify_and_mark_rejects_a_packet_path_outside_the_ledger(tmp_path: Path) -> None:
    """장부는 이쪽, 검증 대상 패킷 파일은 저쪽인 조합은 거부한다."""
    directory = _ledger(tmp_path)
    other = tmp_path / "other"
    other.mkdir(mode=0o700)
    PacketStore(other).save(_current_packet())
    foreign = PacketStore(other).path_for(_PACKET_ID)
    sent = _prepare_verified_input(directory, tmp_path)
    assert foreign.is_file() and foreign.parent != directory
    with pytest.raises(BriefInputError):
        verify_and_mark(directory, foreign, sent, "<m1@example.com>", _CLAIM_AT)


def test_verify_and_mark_accepts_an_aliased_but_identical_packet_path(tmp_path: Path) -> None:
    """같은 파일을 심볼릭 링크를 지나는 경로로 줘도 같은 파일이면 통과한다."""
    ledger, alias = _aliased(tmp_path)
    sent = _prepare_verified_input(ledger, tmp_path)
    aliased_packet = alias / f"{_PACKET_ID}.packet.json"
    result = verify_and_mark(ledger, aliased_packet, sent, "<m1@example.com>", _CLAIM_AT)
    assert result.state is SendState.VERIFIED


# ---------------------------------------------------------------- 별도 프로세스 경합


def _tests_dir() -> str:
    return str(Path(__file__).resolve().parent)


def _src_dir() -> str:
    return str(Path(humansearch.__file__).resolve().parents[1])


def _process_round(directory: Path, driver: Path) -> tuple[bool, bool]:
    """자식 프로세스가 청구, 부모가 save(B). (청구를 땄는가, 저장이 승인 본문 그대로인가)."""
    directory.mkdir(mode=0o700, parents=True)
    approved = _current_packet()
    store = PacketStore(directory)
    store.save(approved)
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join([_src_dir(), _tests_dir()])
    child = subprocess.Popen(
        [sys.executable, str(driver), str(directory), _tests_dir()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    ready = directory / "child.ready"
    deadline = time.monotonic() + _WAIT
    while not ready.exists() and time.monotonic() < deadline:
        if child.poll() is not None:
            break
        time.sleep(_POLL)
    (directory / "go").write_text("1", encoding="utf-8")
    try:
        store.save(_other_packet())
    except BriefInputError:
        pass
    out, err = child.communicate(timeout=_WAIT)
    assert child.returncode == 0, f"자식 프로세스 실패: {err}"
    won = "CLAIM:True" in out
    stored = store.load(_PACKET_ID)
    return won, stored.mail.body_sha256 == approved.mail.body_sha256


def test_two_separate_processes_never_split_the_approved_digest(tmp_path: Path) -> None:
    """실제 별도 프로세스 경합에서도 승인 digest 와 저장 패킷이 갈라지면 안 된다."""
    driver = tmp_path / "child_driver.py"
    driver.write_text(_CHILD, encoding="utf-8")
    violations: list[int] = []
    for index in range(_PROCESS_ROUNDS):
        won, intact = _process_round(tmp_path / f"p{index:02d}", driver)
        if won and not intact:
            violations.append(index)
    assert violations == []


def test_the_child_driver_can_actually_take_a_claim(tmp_path: Path) -> None:
    """경합 시험이 '자식이 아무것도 못 해서' 조용히 초록이 되는 것을 막는 양성 대조군."""
    driver = tmp_path / "child_driver.py"
    driver.write_text(_CHILD, encoding="utf-8")
    directory = tmp_path / "solo"
    directory.mkdir(mode=0o700)
    PacketStore(directory).save(_current_packet())
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join([_src_dir(), _tests_dir()])
    child = subprocess.Popen(
        [sys.executable, str(driver), str(directory), _tests_dir()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    ready = directory / "child.ready"
    deadline = time.monotonic() + _WAIT
    while not ready.exists() and time.monotonic() < deadline:
        time.sleep(_POLL)
    (directory / "go").write_text("1", encoding="utf-8")
    out, err = child.communicate(timeout=_WAIT)
    assert child.returncode == 0, err
    assert "CLAIM:True" in out


def test_a_held_lock_blocks_another_process(tmp_path: Path) -> None:
    """이 스레드가 잠금을 쥔 동안 **다른 프로세스**는 청구에 들어오지 못한다(flock 프로세스 간 배타)."""
    from humansearch.brief import packet as packet_module

    driver = tmp_path / "child_driver.py"
    driver.write_text(_CHILD, encoding="utf-8")
    directory = tmp_path / "held"
    directory.mkdir(mode=0o700)
    PacketStore(directory).save(_current_packet())
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join([_src_dir(), _tests_dir()])
    entered = threading.Event()
    with packet_module._channel_lock(PacketStore(directory).dir, _PACKET_ID, "gmail"):
        child = subprocess.Popen(
            [sys.executable, str(driver), str(directory), _tests_dir()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        ready = directory / "child.ready"
        deadline = time.monotonic() + _WAIT
        while not ready.exists() and time.monotonic() < deadline:
            time.sleep(_POLL)
        (directory / "go").write_text("1", encoding="utf-8")
        time.sleep(0.5)
        assert child.poll() is None, "잠금을 쥔 동안 다른 프로세스가 청구를 끝냈다"
        entered.set()
    out, err = child.communicate(timeout=_WAIT)
    assert entered.is_set()
    assert child.returncode == 0, err
    assert "CLAIM:True" in out
