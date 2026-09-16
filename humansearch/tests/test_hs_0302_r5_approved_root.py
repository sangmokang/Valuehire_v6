"""Approved DB root and connect-time swap-back regression tests."""

from __future__ import annotations

import os
import shutil
import sqlite3
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
_KEY = bytes(range(32))


def _key_file(root: Path) -> Path:
    root.mkdir(mode=0o700)
    key_path = root / "candidate.key"
    key_path.write_bytes(_KEY)
    key_path.chmod(0o600)
    return key_path


def _rows(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        return int(connection.execute("select count(*) from hs_candidates").fetchone()[0])


def test_unapproved_private_compatible_db_is_refused(tmp_path: Path) -> None:
    """Git 밖의 0700/0600 호환 DB라도 승인 설정의 root가 다르면 기록하지 않는다."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    other_root = tmp_path / "unapproved"
    other_root.mkdir(mode=0o700)
    other_db = other_root / approved.db_path.name
    shutil.copyfile(approved.db_path, other_db)
    other_db.chmod(0o600)
    key_path = _key_file(tmp_path / "keys")

    with pytest.raises(CandidateIdentityError, match="approved"):
        record_candidate_identity(
            other_db, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
        )

    assert _rows(other_db) == 0
    assert _rows(approved.db_path) == 0


def test_connect_swap_back_to_other_compatible_db_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """경계 검사 뒤 symlink로 다른 DB를 열고 즉시 원상복구해도 열린 연결을 거부한다."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    alternate = initialize_humansearch_storage(tmp_path / "alternate")
    key_path = _key_file(tmp_path / "keys")
    real_connect = sqlite3.connect
    parked = approved.db_path.with_name("parked.sqlite3")
    opened_alternate = False

    def swap_connect(
        path: Path, *, isolation_level: None, timeout: float
    ) -> sqlite3.Connection:
        nonlocal opened_alternate
        approved.db_path.rename(parked)
        approved.db_path.symlink_to(alternate.db_path)
        try:
            connection = real_connect(path, isolation_level=isolation_level, timeout=timeout)
            opened_alternate = True
        finally:
            approved.db_path.unlink()
            parked.rename(approved.db_path)
        return connection

    monkeypatch.setattr(
        "humansearch.candidate_identity.sqlite3",
        SimpleNamespace(connect=swap_connect, IntegrityError=sqlite3.IntegrityError,
                        OperationalError=sqlite3.OperationalError),
    )

    with pytest.raises(CandidateIdentityError, match="opened"):
        record_candidate_identity(
            approved.db_path,
            _RECORD,
            hmac_key_path=key_path,
            approved_root=approved.protected_root,
        )

    assert opened_alternate
    assert _rows(approved.db_path) == 0
    assert _rows(alternate.db_path) == 0


def _compatible_copy(source: Path, target_root: Path, name: str) -> Path:
    """정상 초기화 DB를 다른 자리로 옮긴 0600 호환 사본 — 모양은 같지만 승인은 없다."""

    target_root.mkdir(mode=0o700, exist_ok=True)
    copy = target_root / name
    shutil.copyfile(source, copy)
    copy.chmod(0o600)
    return copy


def test_self_approved_private_compatible_db_is_refused(tmp_path: Path) -> None:
    """승인 root 인자를 DB 부모로 스스로 채워도 초기화가 승인한 root가 아니면 기록하지 않는다."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    other_db = _compatible_copy(approved.db_path, tmp_path / "unapproved", approved.db_path.name)
    key_path = _key_file(tmp_path / "keys")

    with pytest.raises(CandidateIdentityError, match="approved"):
        record_candidate_identity(
            other_db, _RECORD, hmac_key_path=key_path, approved_root=other_db.parent
        )

    assert _rows(other_db) == 0


def test_other_db_filename_inside_approved_root_is_refused(tmp_path: Path) -> None:
    """승인 root 안이라도 초기화가 돌려준 DB 파일이 아니면 기록하지 않는다."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    other_db = _compatible_copy(approved.db_path, approved.protected_root, "parked.sqlite3")
    key_path = _key_file(tmp_path / "keys")

    with pytest.raises(CandidateIdentityError, match="approved"):
        record_candidate_identity(
            other_db, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
        )

    assert _rows(other_db) == 0
    assert _rows(approved.db_path) == 0


def test_initialized_storage_result_still_records(tmp_path: Path) -> None:
    """양성 대조군 — 초기화 결과의 db_path·protected_root 쌍은 그대로 기록된다."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")

    outcome = record_candidate_identity(
        approved.db_path, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
    )

    assert outcome == "inserted"
    assert _rows(approved.db_path) == 1


@pytest.mark.parametrize("direction", ["link-out", "link-in"])
def test_hardlinked_db_is_refused(tmp_path: Path, direction: str) -> None:
    """symlink 처럼 hard link 도 경로 표면만 승인 root 안이다 — 같은 inode 가 밖에서도 열린다."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    alternate = initialize_humansearch_storage(tmp_path / "alternate")
    key_path = _key_file(tmp_path / "keys")
    if direction == "link-out":
        os.link(approved.db_path, alternate.protected_root / "leak.sqlite3")
    else:
        approved.db_path.unlink()
        os.link(alternate.db_path, approved.db_path)

    with pytest.raises(CandidateIdentityError, match="link"):
        record_candidate_identity(
            approved.db_path, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
        )

    assert _rows(approved.db_path) == 0
    assert _rows(alternate.db_path) == 0


def test_renamed_in_compatible_db_at_approved_path_is_refused(tmp_path: Path) -> None:
    """경로 이름만 같고 파일 정체성(st_dev·st_ino)이 다르면 초기화가 돌려준 그 파일이 아니다(V1 결함 1)."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    alternate = initialize_humansearch_storage(tmp_path / "alternate")
    key_path = _key_file(tmp_path / "keys")
    parked = approved.protected_root / "parked-original.sqlite3"
    approved.db_path.rename(parked)
    alternate.db_path.rename(approved.db_path)

    with pytest.raises(CandidateIdentityError, match="approved"):
        record_candidate_identity(
            approved.db_path, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
        )

    assert _rows(approved.db_path) == 0
    assert _rows(parked) == 0


def test_regular_inode_swap_during_connect_and_commit_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from humansearch import candidate_identity as identity_module

    approved = initialize_humansearch_storage(tmp_path / "approved")
    alternate = initialize_humansearch_storage(tmp_path / "alternate")
    key_path = _key_file(tmp_path / "keys")
    parked = approved.protected_root / "parked-original.sqlite3"
    real_verify = identity_module
    check = real_verify._verify_db_boundary
    calls = 0

    def raced_verify(path: Path, root: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            approved.db_path.rename(alternate.db_path)
            parked.rename(approved.db_path)
            try:
                check(path, root)
            finally:
                approved.db_path.rename(parked)
                alternate.db_path.rename(approved.db_path)
            return
        check(path, root)
        if calls == 2:
            approved.db_path.rename(parked)
            alternate.db_path.rename(approved.db_path)

    monkeypatch.setattr(real_verify, "_verify_db_boundary", raced_verify)
    with pytest.raises(CandidateIdentityError):
        record_candidate_identity(
            approved.db_path, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
        )
    assert calls >= 2
    assert _rows(approved.db_path) == 0
    assert _rows(parked) == 0


def test_regular_inode_swap_back_after_connect_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    approved = initialize_humansearch_storage(tmp_path / "approved")
    alternate = initialize_humansearch_storage(tmp_path / "alternate")
    key_path = _key_file(tmp_path / "keys")
    with sqlite3.connect(alternate.db_path) as connection:
        assert connection.execute("pragma journal_mode=wal").fetchone()[0] == "wal"
    real_connect = sqlite3.connect
    parked = approved.protected_root / "parked-original.sqlite3"
    opened = False

    def swap_connect(path: Path, *, isolation_level: None, timeout: float) -> sqlite3.Connection:
        nonlocal opened
        approved.db_path.rename(parked)
        alternate.db_path.rename(approved.db_path)
        try:
            connection = real_connect(path, isolation_level=isolation_level, timeout=timeout)
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


def test_unrelated_open_files_in_other_threads_do_not_refuse_writes(tmp_path: Path) -> None:
    """다른 스레드가 무관한 파일을 여닫는 동안에도 정상 쓰기는 거부되면 안 된다(오거부 = 순회 중단)."""
    import threading

    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    scratch = tmp_path / "scratch.txt"
    scratch.write_text("x")
    stop = threading.Event()

    def churn() -> None:
        while not stop.is_set():
            with scratch.open() as handle:
                handle.read()

    worker = threading.Thread(target=churn)
    worker.start()
    try:
        outcomes = [
            record_candidate_identity(
                approved.db_path,
                CandidateIdentityInput(f"POS-{index}", "saramin", "cand", "2026-09-15T10:00:00Z"),
                hmac_key_path=key_path,
                approved_root=approved.protected_root,
            )
            for index in range(60)
        ]
    finally:
        stop.set()
        worker.join()
    assert outcomes == ["inserted"] * 60
    assert _rows(approved.db_path) == 60


def test_opened_db_reported_outside_approved_path_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """열린 연결이 승인 경로가 아닌 파일을 main 으로 보고하면 INSERT 전에 거부한다(AC-8, V2 결함 1)."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    real_connect = sqlite3.connect
    elsewhere = str(approved.protected_root / "elsewhere.sqlite3")

    class _Misreporting:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._connection = connection

        def execute(self, sql: str, params: tuple[str, ...] = ()) -> object:
            if sql.strip().startswith("pragma database_list"):
                return [(0, "main", elsewhere)]
            return self._connection.execute(sql, params)

        def close(self) -> None:
            self._connection.close()

    def connect(path: Path, *, isolation_level: None, timeout: float) -> _Misreporting:
        return _Misreporting(real_connect(path, isolation_level=isolation_level, timeout=timeout))

    monkeypatch.setattr(
        "humansearch.candidate_identity.sqlite3",
        SimpleNamespace(connect=connect, IntegrityError=sqlite3.IntegrityError,
                        OperationalError=sqlite3.OperationalError),
    )
    with pytest.raises(CandidateIdentityError, match="opened db is outside"):
        record_candidate_identity(
            approved.db_path, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
        )
    assert _rows(approved.db_path) == 0


@pytest.mark.parametrize("suffix", ["-journal", "-wal", "-shm"])
def test_hardlinked_sqlite_sidecar_is_refused(tmp_path: Path, suffix: str) -> None:
    """보조 파일도 hard link 로 다른 이름을 가지면 보호 범위 밖에서 읽힌다(AC-11 sidecar 절반, V2 결함 2)."""

    approved = initialize_humansearch_storage(tmp_path / "approved")
    key_path = _key_file(tmp_path / "keys")
    sidecar = approved.db_path.with_name(approved.db_path.name + suffix)
    sidecar.write_bytes(b"")
    sidecar.chmod(0o600)
    outside = tmp_path / "outside"
    outside.mkdir(mode=0o700)
    os.link(sidecar, outside / "leak")

    with pytest.raises(CandidateIdentityError, match="link"):
        record_candidate_identity(
            approved.db_path, _RECORD, hmac_key_path=key_path, approved_root=approved.protected_root
        )
    assert _rows(approved.db_path) == 0
