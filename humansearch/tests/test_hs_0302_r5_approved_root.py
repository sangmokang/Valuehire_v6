"""Approved DB root and connect-time swap-back regression tests."""

from __future__ import annotations

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
