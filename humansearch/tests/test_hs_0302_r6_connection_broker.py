"""R6 — connection-identity boundary hardening.

Codex 적대검증(2026-09-16)이 지적한 5개 결함 중 코드 경계 안에서 검증 가능한 세 가지:
(a) decoy 승인 FD 가 `/dev/fd` 집합 차분을 무력화한다, (b) 다른 HMAC 키로 같은 triplet 을
기록할 수 있다, (c) 스키마 connect 시 외부 DB swap-back 뒤에도 두 DB 모두 무변경이어야 한다.
계약: docs/engineering/humansearch-hs-0302-connection-broker-goal-2026-09-17.md
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from humansearch.candidate_identity import (
    CandidateIdentityError,
    CandidateIdentityInput,
    record_candidate_identity,
)
from humansearch.storage_schema import initialize_humansearch_storage

_RECORD = CandidateIdentityInput("POS-1", "saramin", "cand-1", "2026-09-15T10:00:00Z")
_KEY_A = bytes(range(32))
_KEY_B = bytes(range(1, 33))


def _key_file(root: Path, key: bytes = _KEY_A) -> Path:
    root.mkdir(mode=0o700)
    key_path = root / "candidate.key"
    key_path.write_bytes(key)
    key_path.chmod(0o600)
    return key_path


def _rows(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        return int(connection.execute("select count(*) from hs_candidates").fetchone()[0])


def test_decoy_approved_fd_still_bypasses_the_identity_check_blocked_ac8(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(a) BLOCKED — 결정 카드 AC-8 잔여 위험의 재현. 승인 inode 를 가리키는 decoy fd(원본을
    rename 만 한 parked 경로를 여는 무관한 스레드)가 정확히 그 창에서 열려 있으면, `/dev/fd`
    집합 차분은 실제 커넥션이 rename 스왑으로 다른 파일(alternate)을 열었어도 그 사실을
    가려낼 수 없다 — decoy 의 identity 가 "새로 나타난 fd 중 하나"라는 사실만으로 판정을
    속인다. stdlib `sqlite3` 는 어떤 fd 가 **이 커넥션**의 것인지 노출하지 않으므로, 이
    모호성은 코드로 없앨 수 없다(native VFS 없이는 AC-8 완전 증명 불가 — goal 결정 카드 3).

    symlink 스왑이 아니라 **rename** 스왑을 쓰는 이유: symlink 는 SQLite 가
    ``pragma database_list`` 에 realpath 를 보고해 별개 검사(`_insert_once` 의 경로 대조)가
    이미 잡는다. rename 스왑은 경로 문자열이 그대로라 그 검사를 통과하고, 오직 `/dev/fd`
    집합 차분만이 최종 방어선이다.

    이 재현에서 결과적으로 예외가 나는 것은 이 커넥션이 실제로 alternate 파일을 가리키게 된
    뒤 SQLite 가 우연히 "readonly" 오류를 내기 때문이지, 우리 코드가 laundering 을 탐지해서가
    아니다(`_insert_once` 가 그 raw 오류를 닫힌 `CandidateIdentityError` 로 감쌀 뿐이다). 다른
    타이밍이나 파일시스템에서는 이 우연한 실패 없이 조용히 alternate 에 기록될 수 있다 —
    그래서 이 시험은 "고쳤다"가 아니라 "잔여 위험이 존재하고, 지금은 우연히 닫힌 오류로
    끝난다"는 사실만 고정한다. 단일 writer 브로커는 이 위험한 재연결을 프로세스당 딱 한
    번(첫 쓰기)으로 줄여 노출을 줄이지만 없애지는 못한다.
    """
    approved = initialize_humansearch_storage(tmp_path / "approved")
    alternate = initialize_humansearch_storage(tmp_path / "alternate")
    key_path = _key_file(tmp_path / "keys")
    real_connect = sqlite3.connect
    parked = approved.protected_root / "parked-original.sqlite3"
    parked_ready = threading.Event()
    decoy_holding = threading.Event()
    stop_holding = threading.Event()
    decoy_handle: list[object] = []

    def decoy_open() -> None:
        assert parked_ready.wait(timeout=2.0), "swap never renamed the original to parked"
        handle = open(parked, "rb")  # noqa: SIM115 -- decoy fd 를 "after" 스냅샷까지 열어둬야 한다
        decoy_handle.append(handle)
        decoy_holding.set()
        stop_holding.wait(timeout=2.0)
        handle.close()

    def swap_connect(path: Path, **kwargs: object) -> sqlite3.Connection:
        approved.db_path.rename(parked)
        alternate.db_path.rename(approved.db_path)
        parked_ready.set()
        try:
            connection: sqlite3.Connection = real_connect(path, **kwargs)  # type: ignore[call-overload]
        finally:
            # decoy 가 승인 identity fd 를 실제로 쥔 뒤에야 원상복구한다 — 그래야 "after"
            # 스냅샷이 찍히는 순간에도 decoy fd 가 여전히 열려 있다.
            assert decoy_holding.wait(timeout=2.0), "decoy never opened its fd"
            approved.db_path.rename(alternate.db_path)
            parked.rename(approved.db_path)
        return connection

    monkeypatch.setattr(
        "humansearch.candidate_identity.sqlite3",
        SimpleNamespace(connect=swap_connect, IntegrityError=sqlite3.IntegrityError,
                        OperationalError=sqlite3.OperationalError),
    )
    worker = threading.Thread(target=decoy_open)
    worker.start()
    try:
        # 판정("opened db is not the approved file")은 decoy 때문에 통과한다 — 여기서 나는
        # CandidateIdentityError 는 그 판정이 아니라 laundered 커넥션에 대한 SQLite 자체의
        # 뒤늦은 실패(우연)를 감싼 것이다. BLOCKED 잔여 위험 — 위 docstring 참고.
        with pytest.raises(CandidateIdentityError):
            record_candidate_identity(
                approved.db_path,
                _RECORD,
                hmac_key_path=key_path,
                approved_root=approved.protected_root,
            )
    finally:
        stop_holding.set()
        worker.join(timeout=2.0)
    assert not worker.is_alive()
    assert decoy_handle, "decoy fd setup never ran"
    assert _rows(approved.db_path) == 0
    assert _rows(alternate.db_path) == 0


def test_different_key_for_the_same_triplet_is_refused(tmp_path: Path) -> None:
    """(b) 같은 (position, channel, candidate_ref) 라도 DB 가 이미 결합된 키와 다른 키로는
    기록을 거부한다 — 다른 키는 다른 candidate_key_hmac 을 만들어 PK 제약을 우회하기 때문이다."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_a = _key_file(tmp_path / "keys-a", _KEY_A)
    key_b = _key_file(tmp_path / "keys-b", _KEY_B)

    outcome = record_candidate_identity(
        approved.db_path, _RECORD, hmac_key_path=key_a, approved_root=approved.protected_root
    )
    assert outcome == "inserted"

    with pytest.raises(CandidateIdentityError, match="key"):
        record_candidate_identity(
            approved.db_path, _RECORD, hmac_key_path=key_b, approved_root=approved.protected_root
        )

    assert _rows(approved.db_path) == 1  # 다른 키 시도가 두 번째 행을 만들지 않았다


def test_schema_connect_swap_back_leaves_both_dbs_unmodified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(c) 브로커의 최초(스키마) connect 시점에 외부에서 DB를 바꿔치기했다가 되돌려도,
    거부된 시도는 승인된 DB와 바꿔치기된 DB 양쪽 모두를 변경하지 않는다."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    alternate = initialize_humansearch_storage(tmp_path / "alternate")
    key_path = _key_file(tmp_path / "keys")
    real_connect = sqlite3.connect
    parked = approved.protected_root / "parked-original.sqlite3"
    opened = False

    def swap_connect(path: Path, **kwargs: object) -> sqlite3.Connection:
        nonlocal opened
        approved.db_path.rename(parked)
        alternate.db_path.rename(approved.db_path)
        try:
            connection: sqlite3.Connection = real_connect(path, **kwargs)  # type: ignore[call-overload]
            opened = True
        finally:
            approved.db_path.rename(alternate.db_path)
            parked.rename(approved.db_path)
        return connection

    monkeypatch.setattr(
        "humansearch.candidate_identity.sqlite3",
        SimpleNamespace(connect=swap_connect, IntegrityError=sqlite3.IntegrityError,
                        OperationalError=sqlite3.OperationalError),
    )

    with pytest.raises(CandidateIdentityError):
        record_candidate_identity(
            approved.db_path, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
        )
    assert opened
    assert _rows(approved.db_path) == 0
    assert _rows(alternate.db_path) == 0

    # 브로커가 실패한 연결을 캐시하지 않았는지 확인 — 스왑 없는 재시도는 정상 기록된다.
    monkeypatch.undo()
    outcome = record_candidate_identity(
        approved.db_path, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
    )
    assert outcome == "inserted"


def test_broker_reuses_one_connection_across_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """단일 writer 브로커: 같은 승인 root 에 대한 두 번째 쓰기는 새 sqlite3.connect 를
    부르지 않고 캐시된 커넥션을 재사용한다 — 그래야 재연결 경합 창이 반복되지 않는다."""
    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    connect_calls = 0
    real_connect = sqlite3.connect

    def counting_connect(path: Path, **kwargs: object) -> sqlite3.Connection:
        nonlocal connect_calls
        connect_calls += 1
        return real_connect(path, **kwargs)  # type: ignore[call-overload,no-any-return]

    monkeypatch.setattr(
        "humansearch.candidate_identity.sqlite3",
        SimpleNamespace(connect=counting_connect, IntegrityError=sqlite3.IntegrityError,
                        OperationalError=sqlite3.OperationalError),
    )
    for index in range(3):
        outcome = record_candidate_identity(
            approved.db_path,
            CandidateIdentityInput(f"POS-{index}", "saramin", "cand", "2026-09-15T10:00:00Z"),
            hmac_key_path=key_path,
            approved_root=approved.protected_root,
        )
        assert outcome == "inserted"
    monkeypatch.undo()

    assert connect_calls == 1, f"expected exactly one connect for the broker, got {connect_calls}"
    assert _rows(approved.db_path) == 3
