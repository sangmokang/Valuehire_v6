from __future__ import annotations

import os
import sqlite3
import stat
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from humansearch import storage_schema
from humansearch.storage_schema import (
    CURRENT_SCHEMA_VERSION,
    SUPPORTED_MIGRATION_RANGE,
    StorageSchemaError,
    initialize_humansearch_storage,
)


def _root(tmp_path: Path) -> Path:
    return tmp_path / "protected-root"


def _table_columns(db_path: Path, table: str) -> set[str]:
    with sqlite3.connect(db_path) as connection:
        return {row[1] for row in connection.execute(f"pragma table_info({table})")}


def _tables(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as connection:
        return {
            row[0]
            for row in connection.execute(
                "select name from sqlite_master where type = 'table' and name not like 'sqlite_%'"
            )
        }


def _schema_version(db_path: Path) -> int:
    with sqlite3.connect(db_path) as connection:
        row = connection.execute("select max(version) from hs_schema_migrations").fetchone()
    assert row is not None
    assert isinstance(row[0], int)
    return row[0]


def test_installs_empty_hs_sqlite_schema_with_restricted_modes(tmp_path: Path) -> None:
    root = _root(tmp_path)

    result = initialize_humansearch_storage(root)

    assert result.schema_version == CURRENT_SCHEMA_VERSION
    assert result.applied_migrations == (1,)
    assert result.db_path == root / "humansearch.sqlite3"
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE(result.db_path.stat().st_mode) == 0o600
    assert root.stat().st_uid == os.getuid()
    assert result.db_path.stat().st_uid == os.getuid()
    assert _tables(result.db_path) == {
        "hs_schema_migrations",
        "hs_candidates",
        "hs_evidence_manifests",
    }
    assert _schema_version(result.db_path) == CURRENT_SCHEMA_VERSION


def test_schema_contains_only_non_sensitive_candidate_and_evidence_columns(tmp_path: Path) -> None:
    result = initialize_humansearch_storage(_root(tmp_path))

    candidate_columns = _table_columns(result.db_path, "hs_candidates")
    evidence_columns = _table_columns(result.db_path, "hs_evidence_manifests")
    joined = "\n".join(sorted(candidate_columns | evidence_columns))

    assert candidate_columns == {
        "candidate_key_hmac",
        "position_ref",
        "channel",
        "candidate_ref_state",
        "candidate_ref_hash",
        "storage_status",
        "created_at",
    }
    assert evidence_columns == {
        "evidence_id",
        "candidate_key_hmac",
        "run_id",
        "position_ref",
        "channel",
        "source_url_hash",
        "observed_at",
        "evidence_manifest_ref",
        "evidence_manifest_sha256",
        "encrypted_payload_refs_ref",
        "coverage_status",
        "readback_status",
        "storage_status",
        "created_at",
    }
    for forbidden in ("raw", "contact", "email", "phone", "source_url\n", "plaintext", "token"):
        assert forbidden not in joined


def test_schema_constraints_reject_plain_shapes_and_bad_hmac(tmp_path: Path) -> None:
    db_path = initialize_humansearch_storage(_root(tmp_path)).db_path

    with sqlite3.connect(db_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                insert into hs_candidates
                  (candidate_key_hmac, position_ref, channel, candidate_ref_state)
                values (?, 'POS', 'linkedin_rps', 'observed')
                """,
                ("not-a-hmac",),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                insert into hs_evidence_manifests
                  (evidence_id, run_id, position_ref, channel, source_url_hash,
                   observed_at, evidence_manifest_ref, evidence_manifest_sha256,
                   encrypted_payload_refs_ref, coverage_status, readback_status)
                values
                  ('ev1', 'run1', 'POS', 'linkedin_rps', ?, '2026-09-14T00:00:00+09:00',
                   'protected://manifest/ev1', ?, 'protected://cipher/ev1', 'partial', 'not_run')
                """,
                ("bad-url-hash", "a" * 64),
            )


def test_candidate_and_evidence_primary_refs_reject_null_keys(tmp_path: Path) -> None:
    db_path = initialize_humansearch_storage(_root(tmp_path)).db_path

    with sqlite3.connect(db_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                insert into hs_candidates
                  (candidate_key_hmac, position_ref, channel, candidate_ref_state)
                values (null, 'POS', 'jobkorea', 'observed')
                """
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                insert into hs_evidence_manifests
                  (evidence_id, candidate_key_hmac, run_id, position_ref, channel, source_url_hash,
                   observed_at, evidence_manifest_ref, evidence_manifest_sha256,
                   encrypted_payload_refs_ref, coverage_status, readback_status)
                values
                  (null, null, 'run1', 'POS', 'jobkorea', ?, '2026-09-14T00:00:00+09:00',
                   'protected://manifest/ev-null', ?, 'protected://cipher/ev-null', 'partial', 'not_run')
                """,
                ("a" * 64, "b" * 64),
            )


def test_migration_is_idempotent_and_uses_n_minus_one_range(tmp_path: Path) -> None:
    root = _root(tmp_path)

    first = initialize_humansearch_storage(root)
    second = initialize_humansearch_storage(root)

    assert SUPPORTED_MIGRATION_RANGE == (0, CURRENT_SCHEMA_VERSION)
    assert second.applied_migrations == ()
    assert _tables(first.db_path) == _tables(second.db_path)
    with sqlite3.connect(second.db_path) as connection:
        row = connection.execute("select count(*) from hs_schema_migrations").fetchone()
    assert row == (1,)


def test_rejects_future_or_corrupt_migration_ledger(tmp_path: Path) -> None:
    root = _root(tmp_path)
    db_path = initialize_humansearch_storage(root).db_path
    with sqlite3.connect(db_path) as connection:
        connection.execute("update hs_schema_migrations set version = 99")

    with pytest.raises(StorageSchemaError, match="unsupported schema version"):
        initialize_humansearch_storage(root)


def test_rejects_root_inside_git_worktree(tmp_path: Path) -> None:
    del tmp_path
    repo_inside = Path.cwd().parent / "data" / "hs-db"

    with pytest.raises(StorageSchemaError, match="outside the git worktree"):
        initialize_humansearch_storage(repo_inside)


def test_rejects_root_inside_any_git_repository(tmp_path: Path) -> None:
    other_repo = tmp_path / "otherrepo"
    (other_repo / ".git").mkdir(parents=True)

    with pytest.raises(StorageSchemaError, match="outside the git worktree"):
        initialize_humansearch_storage(other_repo / "secrets")


def test_rejects_symlink_root_and_db_target(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    real_root.mkdir(mode=0o700)
    symlink_root = tmp_path / "link-root"
    symlink_root.symlink_to(real_root, target_is_directory=True)

    with pytest.raises(StorageSchemaError, match="symlink"):
        initialize_humansearch_storage(symlink_root)

    root = _root(tmp_path)
    root.mkdir(mode=0o700)
    outside = tmp_path / "outside.sqlite3"
    outside.write_text("", encoding="utf-8")
    (root / "humansearch.sqlite3").symlink_to(outside)
    with pytest.raises(StorageSchemaError, match="symlink"):
        initialize_humansearch_storage(root)


def test_rejects_broad_modes_and_path_escape(tmp_path: Path) -> None:
    root = _root(tmp_path)
    root.mkdir(mode=0o755)

    with pytest.raises(StorageSchemaError, match="0700"):
        initialize_humansearch_storage(root)

    safe = tmp_path / "safe"
    with pytest.raises(StorageSchemaError, match="db filename"):
        initialize_humansearch_storage(safe, db_filename="../escape.sqlite3")


def test_sqlite_runtime_keeps_journal_and_temp_boundary_inside_root(tmp_path: Path) -> None:
    result = initialize_humansearch_storage(_root(tmp_path))

    with sqlite3.connect(result.db_path) as connection:
        journal_mode = connection.execute("pragma journal_mode").fetchone()

    assert journal_mode == ("delete",)
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = result.db_path.with_name(result.db_path.name + suffix)
        assert sidecar.parent == result.db_path.parent


def test_rejects_existing_unprotected_sqlite_sidecars(tmp_path: Path) -> None:
    root = _root(tmp_path)
    root.mkdir(mode=0o700)
    journal = root / "humansearch.sqlite3-journal"
    journal.write_text("stale", encoding="utf-8")
    journal.chmod(0o644)

    with pytest.raises(StorageSchemaError, match="sidecar"):
        initialize_humansearch_storage(root)

    assert journal.exists()
    assert stat.S_IMODE(journal.stat().st_mode) == 0o644


def test_sqlite_rollback_journal_is_created_with_restricted_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _root(tmp_path)
    journal_modes: list[int] = []
    migration_sql = tuple(
        [
            "create table hs_schema_migrations (version integer primary key, name text not null, applied_at text not null default current_timestamp)",
            "create table hs_big(id integer primary key, payload text)",
        ]
        + [f"insert into hs_big(payload) values ('payload-{index}')" for index in range(4000)]
    )
    monkeypatch.setattr(
        storage_schema,
        "_MIGRATIONS",
        (storage_schema._Migration(1, "slow", migration_sql),),
    )

    old_umask = os.umask(0)
    try:
        journal = root / "humansearch.sqlite3-journal"
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(initialize_humansearch_storage, root)
            deadline = time.monotonic() + 5
            while not future.done() and time.monotonic() < deadline:
                if journal.exists() and not journal.is_symlink():
                    journal_modes.append(stat.S_IMODE(journal.stat().st_mode))
                time.sleep(0.001)
            result = future.result(timeout=5)
        assert result.schema_version == CURRENT_SCHEMA_VERSION
    finally:
        os.umask(old_umask)

    assert journal_modes
    assert set(journal_modes) == {0o600}


def test_migration_failure_is_atomic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = _root(tmp_path)
    monkeypatch.setattr(
        storage_schema,
        "_MIGRATIONS",
        (
            storage_schema._Migration(1, "bad", ("create table hs_partial(id text);", "not sql")),
        ),
    )

    with pytest.raises(StorageSchemaError, match="migration failed"):
        initialize_humansearch_storage(root)

    db_path = root / "humansearch.sqlite3"
    assert db_path.exists()
    assert _tables(db_path) == set()



def test_connect_failure_restores_process_umask(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_connect(_db_path: Path) -> sqlite3.Connection:
        raise sqlite3.OperationalError("connect failed")

    monkeypatch.setattr(sqlite3, "connect", fail_connect)
    previous_umask = os.umask(0o022)
    try:
        with pytest.raises(StorageSchemaError, match="migration failed"):
            initialize_humansearch_storage(_root(tmp_path))
        observed_umask = os.umask(previous_umask)
    finally:
        os.umask(previous_umask)

    assert observed_umask == 0o022
