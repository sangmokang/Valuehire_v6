"""HS-03.02 6차 — V2(2026-09-16) 새 맥락 재검증에서 생존한 방어 지점 7곳을 시험으로 고정한다.

각 시험은 인수 스크립트의 약화 변이 한 종과 1:1 로 대응한다. 변이 사본에서 빨개지지 않으면
그 방어는 저장소 안에서 보호되지 않는 것이다(변이는 목록이 아니라 생성으로 잡는다).
"""

from __future__ import annotations

import os
import sqlite3
import threading
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from humansearch.candidate_identity import (
    CandidateIdentityError,
    CandidateIdentityInput,
    Channel,
    record_candidate_identity,
)
from humansearch.storage_schema import initialize_humansearch_storage

_RECORD = CandidateIdentityInput("POS-1", "saramin", "cand-1", "2026-09-15T10:00:00Z")
_KEY = bytes(range(32))
_MAX_FIELD_CHARS = 512
_BLOCK_TIMEOUT_SECONDS = 5.0


def _key_file(root: Path) -> Path:
    root.mkdir(mode=0o700)
    key_path = root / "candidate.key"
    key_path.write_bytes(_KEY)
    key_path.chmod(0o600)
    return key_path


def _rows(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        return int(connection.execute("select count(*) from hs_candidates").fetchone()[0])


def _record(db_path: Path, key_path: Path, root: Path, record: CandidateIdentityInput = _RECORD) -> str:
    return str(record_candidate_identity(db_path, record, hmac_key_path=key_path, approved_root=root))


def _record_with_deadline(db_path: Path, key_path: Path, root: Path) -> BaseException | str:
    """FIFO 같은 입력에서 구현이 멈추면 시험도 같이 멈추므로 스레드 마감으로 잰다."""
    outcome: dict[str, BaseException | str] = {}

    def run() -> None:
        try:
            outcome["result"] = _record(db_path, key_path, root)
        except BaseException as exc:  # noqa: BLE001 — 시험은 무엇이 나오든 기록한다
            outcome["result"] = exc

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(_BLOCK_TIMEOUT_SECONDS)
    if worker.is_alive():
        return "BLOCKED"
    return outcome["result"]


def _unblock_fifo(path: Path) -> None:
    """읽는 쪽이 FIFO 에 걸려 있으면 쓰기 쪽을 열어 풀어 준다(뒤 시험의 잠금 교착 방지)."""
    try:
        fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
    except OSError:
        return
    try:
        os.write(fd, b"\0" * 64)
    finally:
        os.close(fd)


def _swap_on_insert(approved_db: Path, moved: Path, replacement: Path) -> SimpleNamespace:
    """INSERT 직후·commit 전에 승인 DB 를 root 밖으로 옮기고 호환 DB 를 그 자리에 둔다."""
    real_connect = sqlite3.connect

    class _Swapping:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._connection = connection

        def execute(self, sql: str, params: tuple[str, ...] = ()) -> object:
            cursor = self._connection.execute(sql, params)
            if "insert into hs_candidates" in sql:
                approved_db.rename(moved)
                replacement.rename(approved_db)
            return cursor

        def close(self) -> None:
            self._connection.close()

    def connect(path: Path, *, isolation_level: None, timeout: float) -> _Swapping:
        return _Swapping(real_connect(path, isolation_level=isolation_level, timeout=timeout))

    return SimpleNamespace(
        connect=connect, IntegrityError=sqlite3.IntegrityError, OperationalError=sqlite3.OperationalError
    )


def test_db_swapped_out_of_root_between_insert_and_commit_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """commit 직전 재검사는 경로가 아니라 승인 inode 를 봐야 한다(V2 M19 — 단독 결손 시 전부 초록)."""
    approved = initialize_humansearch_storage(tmp_path / "approved")
    alternate = initialize_humansearch_storage(tmp_path / "alternate")
    key_path = _key_file(tmp_path / "keys")
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    moved = outside / "moved.sqlite3"
    monkeypatch.setattr(
        "humansearch.candidate_identity.sqlite3", _swap_on_insert(approved.db_path, moved, alternate.db_path)
    )
    with pytest.raises(CandidateIdentityError, match="not the approved file"):
        _record(approved.db_path, key_path, approved.protected_root)
    assert _rows(moved) == 0, "root 밖으로 옮겨진 승인 inode 에 행이 확정됐다"
    assert _rows(approved.db_path) == 0


def test_db_unlinked_after_first_boundary_check_is_a_closed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """첫 경계 검사 뒤 DB 가 사라지면 키 경로 검사의 resolve 도 경로 없는 닫힌 오류여야 한다(V2 M12)."""
    from humansearch import candidate_identity as identity_module

    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    real_verify = identity_module._verify_db_boundary
    calls = 0

    def vanish_after_first(path: Path, root: Path) -> None:
        nonlocal calls
        calls += 1
        real_verify(path, root)
        if calls == 1:
            path.unlink()

    monkeypatch.setattr(identity_module, "_verify_db_boundary", vanish_after_first)
    with pytest.raises(CandidateIdentityError, match="db file is missing") as caught:
        _record(approved.db_path, key_path, approved.protected_root)
    rendered = "".join(traceback.format_exception(caught.value))
    assert str(tmp_path) not in rendered, "원인 사슬에 보호 경로가 실렸다"


@pytest.mark.parametrize("field", ["position_ref", "channel", "candidate_ref"])
def test_over_length_field_is_refused(tmp_path: Path, field: str) -> None:
    """상한(512자)을 한 글자 넘긴 필드는 행을 만들지 않고 닫힌 오류여야 한다(V2 M3)."""
    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    values = {"position_ref": "POS-1", "channel": "saramin", "candidate_ref": "cand-1"}
    values[field] = "c" * (_MAX_FIELD_CHARS + 1)
    record = CandidateIdentityInput(
        values["position_ref"], cast(Channel, values["channel"]), values["candidate_ref"], "2026-09-15T10:00:00Z"
    )
    with pytest.raises(CandidateIdentityError, match="too long"):
        _record(approved.db_path, key_path, approved.protected_root, record)
    assert _rows(approved.db_path) == 0


def test_max_length_field_still_records(tmp_path: Path) -> None:
    """상한과 같은 길이는 정상이다 — 경계 한 점의 양성 대조군."""
    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    record = CandidateIdentityInput("POS-1", "saramin", "c" * _MAX_FIELD_CHARS, "2026-09-15T10:00:00Z")
    assert _record(approved.db_path, key_path, approved.protected_root, record) == "inserted"
    assert _rows(approved.db_path) == 1


def test_non_busy_begin_error_is_not_folded_into_duplicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """읽기 전용 같은 BUSY 아닌 쓰기 실패는 잠금 대기 경로로 접혀 `duplicate` 가 되면 안 된다(V2 M30)."""
    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    assert _record(approved.db_path, key_path, approved.protected_root) == "inserted"
    real_connect = sqlite3.connect

    class _ReadOnlyBegin:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._connection = connection

        def execute(self, sql: str, params: tuple[str, ...] = ()) -> object:
            if sql.strip().startswith("begin immediate"):
                failure = sqlite3.OperationalError("attempt to write a readonly database")
                failure.sqlite_errorname = "SQLITE_READONLY"
                raise failure
            return self._connection.execute(sql, params)

        def close(self) -> None:
            self._connection.close()

    def connect(path: Path, *, isolation_level: None, timeout: float) -> _ReadOnlyBegin:
        return _ReadOnlyBegin(real_connect(path, isolation_level=isolation_level, timeout=timeout))

    monkeypatch.setattr(
        "humansearch.candidate_identity.sqlite3",
        SimpleNamespace(connect=connect, IntegrityError=sqlite3.IntegrityError,
                        OperationalError=sqlite3.OperationalError),
    )
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        _record(approved.db_path, key_path, approved.protected_root)
    assert _rows(approved.db_path) == 1


def test_exclusive_lock_wait_exceeded_is_a_closed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """EXCLUSIVE 잠금은 승자 조회조차 막는다 — 그 경로도 원문이 아니라 닫힌 오류여야 한다(V2 M36)."""
    from humansearch import candidate_identity as identity_module

    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    monkeypatch.setattr(identity_module, "_LOCK_WAIT_SECONDS", 0.2, raising=False)
    holder = sqlite3.connect(approved.db_path, isolation_level=None)
    holder.execute("begin exclusive")
    try:
        with pytest.raises(CandidateIdentityError, match="lock wait exceeded") as caught:
            _record(approved.db_path, key_path, approved.protected_root)
    finally:
        holder.execute("rollback")
        holder.close()
    rendered = "".join(traceback.format_exception(caught.value))
    assert str(tmp_path) not in rendered
    assert _rows(approved.db_path) == 0


def test_fifo_at_key_path_is_refused_without_blocking(tmp_path: Path) -> None:
    """키 자리의 FIFO 는 읽으면 영원히 멈춘다 — regular 검사가 먼저 거부해야 한다(V2 M13)."""
    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_dir = tmp_path / "keys"
    key_dir.mkdir(mode=0o700)
    fifo = key_dir / "candidate.key"
    os.mkfifo(fifo, 0o600)
    try:
        outcome = _record_with_deadline(approved.db_path, fifo, approved.protected_root)
    finally:
        _unblock_fifo(fifo)
    assert isinstance(outcome, CandidateIdentityError), f"FIFO 키에서 멈추거나 통과했다: {outcome!r}"
    assert "regular file" in str(outcome)
    assert _rows(approved.db_path) == 0


def test_fifo_sqlite_sidecar_is_refused_without_blocking(tmp_path: Path) -> None:
    """journal 자리의 FIFO 는 SQLite 가 읽다 멈춘다 — sidecar regular 검사가 먼저 거부해야 한다(V2 M27)."""
    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    sidecar = approved.db_path.with_name(approved.db_path.name + "-journal")
    os.mkfifo(sidecar, 0o600)
    try:
        outcome = _record_with_deadline(approved.db_path, key_path, approved.protected_root)
    finally:
        _unblock_fifo(sidecar)
        sidecar.unlink()
    assert isinstance(outcome, CandidateIdentityError), f"FIFO sidecar 에서 멈추거나 통과했다: {outcome!r}"
    assert "regular file" in str(outcome)
    assert _rows(approved.db_path) == 0
