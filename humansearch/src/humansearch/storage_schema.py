"""HS-03.01 SQLite schema bootstrap for the HumanSearch local source DB."""

from __future__ import annotations

import os
import sqlite3
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Final

CURRENT_SCHEMA_VERSION: Final = 1
SUPPORTED_MIGRATION_RANGE: Final = (0, CURRENT_SCHEMA_VERSION)
_DB_FILENAME: Final = "humansearch.sqlite3"
_HEX64: Final = "[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]"
_SHA64_CHECK: Final = "glob '" + (_HEX64 * 8) + "'"


class StorageSchemaError(ValueError):
    """Closed storage schema setup error without private payload values."""


@dataclass(frozen=True, slots=True)
class StorageSchemaResult:
    """Result returned after schema setup."""

    db_path: Path
    schema_version: int
    applied_migrations: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class _Migration:
    version: int
    name: str
    statements: tuple[str, ...]


_MIGRATIONS: tuple[_Migration, ...] = (
    _Migration(
        1,
        "initial_hs_source_schema",
        (
            """
            create table hs_schema_migrations (
              version integer primary key,
              name text not null,
              applied_at text not null default current_timestamp
            )
            """,
            f"""
            create table hs_candidates (
              candidate_key_hmac text primary key not null check (candidate_key_hmac {_SHA64_CHECK}),
              position_ref text not null,
              channel text not null check (channel in ('saramin','jobkorea','linkedin_rps')),
              candidate_ref_state text not null
                check (candidate_ref_state in ('observed','not_observed','not_available')),
              candidate_ref_hash text check (candidate_ref_hash is null or candidate_ref_hash {_SHA64_CHECK}),
              storage_status text not null default 'schema_only'
                check (storage_status in ('schema_only','pending','partial','failed','confirmed')),
              created_at text not null default current_timestamp
            )
            """,
            f"""
            create table hs_evidence_manifests (
              evidence_id text primary key not null,
              candidate_key_hmac text not null references hs_candidates(candidate_key_hmac),
              run_id text not null,
              position_ref text not null,
              channel text not null check (channel in ('saramin','jobkorea','linkedin_rps')),
              source_url_hash text not null check (source_url_hash {_SHA64_CHECK}),
              observed_at text not null,
              evidence_manifest_ref text not null,
              evidence_manifest_sha256 text not null check (evidence_manifest_sha256 {_SHA64_CHECK}),
              encrypted_payload_refs_ref text not null,
              coverage_status text not null check (coverage_status in ('complete','partial','failed')),
              readback_status text not null check (readback_status in ('not_run','matched','mismatch','blocked')),
              storage_status text not null default 'schema_only'
                check (storage_status in ('schema_only','pending','partial','failed','confirmed')),
              created_at text not null default current_timestamp
            )
            """,
        ),
    ),
)


_REQUIRED_TABLE_COLUMNS: Final = {
    "hs_schema_migrations": ("version", "name", "applied_at"),
    "hs_candidates": (
        "candidate_key_hmac",
        "position_ref",
        "channel",
        "candidate_ref_state",
        "candidate_ref_hash",
        "storage_status",
        "created_at",
    ),
    "hs_evidence_manifests": (
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
    ),
}
_SCHEMA_SQL_FRAGMENTS: Final = {
    "hs_schema_migrations": ("version integer primary key", "name text not null"),
    "hs_candidates": (
        "candidate_key_hmac text primary key not null check",
        "position_ref text not null",
        "channel text not null check",
        "candidate_ref_state text not null",
        "candidate_ref_hash text check",
        "storage_status text not null default 'schema_only'",
    ),
    "hs_evidence_manifests": (
        "evidence_id text primary key not null",
        "candidate_key_hmac text not null references hs_candidates(candidate_key_hmac)",
        "source_url_hash text not null check",
        "evidence_manifest_sha256 text not null check",
        "coverage_status text not null check",
        "readback_status text not null check",
    ),
}


def initialize_humansearch_storage(
    protected_root: Path,
    *,
    db_filename: str = _DB_FILENAME,
) -> StorageSchemaResult:
    """Install the HS SQLite source schema under a checked protected root."""

    root = _prepare_root(protected_root)
    db_path = _db_path(root, db_filename)
    _prepare_db_file(db_path)
    _verify_existing_sidecars(db_path)
    applied = _apply_schema(db_path)
    _verify_path(db_path, expected_mode=0o600, label="db file")
    return StorageSchemaResult(
        db_path=db_path,
        schema_version=_schema_version(db_path),
        applied_migrations=applied,
    )


def _prepare_root(root: Path) -> Path:
    if root.is_symlink():
        raise StorageSchemaError("protected root must not be a symlink")
    if _inside_git_worktree(root):
        raise StorageSchemaError("protected root must be outside the git worktree")
    if not root.exists():
        old_umask = os.umask(0o077)
        try:
            root.mkdir(mode=0o700, parents=True)
        finally:
            os.umask(old_umask)
    _verify_path(root, expected_mode=0o700, label="protected root")
    if not root.is_dir():
        raise StorageSchemaError("protected root must be a directory")
    return root.resolve(strict=True)


def _db_path(root: Path, db_filename: str) -> Path:
    name = Path(db_filename)
    if name.name != db_filename or name.is_absolute() or db_filename != _DB_FILENAME:
        raise StorageSchemaError("db filename must be the approved basename")
    db_path = root / db_filename
    resolved_parent = db_path.parent.resolve(strict=True)
    if resolved_parent != root:
        raise StorageSchemaError("db filename must stay inside protected root")
    if db_path.is_symlink():
        raise StorageSchemaError("db file must not be a symlink")
    return db_path


def _prepare_db_file(db_path: Path) -> None:
    if db_path.exists():
        _verify_path(db_path, expected_mode=0o600, label="db file")
        if not db_path.is_file():
            raise StorageSchemaError("db file must be a regular file")
        return
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    fd = os.open(db_path, flags, 0o600)
    os.close(fd)
    _verify_path(db_path, expected_mode=0o600, label="db file")


def _apply_schema(db_path: Path) -> tuple[int, ...]:
    applied: list[int] = []
    old_umask = os.umask(0o077)
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(db_path)
        connection.execute("pragma foreign_keys = on")
        connection.execute("pragma temp_store = memory")
        connection.execute("pragma journal_mode = delete")
        connection.execute("begin")
        current = _current_version(connection)
        for migration in _MIGRATIONS:
            if migration.version <= current:
                continue
            _run_migration(connection, migration)
            applied.append(migration.version)
        _verify_schema_contract(connection)
        connection.commit()
    except StorageSchemaError:
        if connection is not None:
            connection.rollback()
        raise
    except sqlite3.Error as exc:
        if connection is not None:
            connection.rollback()
        raise StorageSchemaError("migration failed") from exc
    finally:
        if connection is not None:
            connection.close()
        os.umask(old_umask)
    return tuple(applied)


def _run_migration(connection: sqlite3.Connection, migration: _Migration) -> None:
    for statement in migration.statements:
        connection.execute(statement)
    connection.execute(
        "insert into hs_schema_migrations(version, name) values (?, ?)",
        (migration.version, migration.name),
    )


def _current_version(connection: sqlite3.Connection) -> int:
    exists = connection.execute(
        "select 1 from sqlite_master where type = 'table' and name = 'hs_schema_migrations'"
    ).fetchone()
    if exists is None:
        return 0
    rows = connection.execute("select version from hs_schema_migrations").fetchall()
    if not rows:
        return 0
    known_versions = {migration.version for migration in _MIGRATIONS}
    versions: list[int] = []
    for row in rows:
        version = row[0]
        if (
            not isinstance(version, int)
            or version < 1
            or version > CURRENT_SCHEMA_VERSION
            or version not in known_versions
        ):
            raise StorageSchemaError("unsupported schema version")
        versions.append(version)
    return max(versions)


def _verify_schema_contract(connection: sqlite3.Connection) -> None:
    rows = connection.execute(
        "select name, sql from sqlite_master where type = 'table' "
        "and name in ('hs_schema_migrations','hs_candidates','hs_evidence_manifests')"
    ).fetchall()
    table_sql = {row[0]: row[1] for row in rows if isinstance(row[0], str) and isinstance(row[1], str)}
    if set(table_sql) != set(_REQUIRED_TABLE_COLUMNS):
        raise StorageSchemaError("schema mismatch")
    for table, expected_columns in _REQUIRED_TABLE_COLUMNS.items():
        observed = tuple(row[1] for row in connection.execute(f"pragma table_info({table})"))
        normalized_sql = " ".join(table_sql[table].lower().split())
        if observed != expected_columns:
            raise StorageSchemaError("schema mismatch")
        if any(fragment not in normalized_sql for fragment in _SCHEMA_SQL_FRAGMENTS[table]):
            raise StorageSchemaError("schema mismatch")


def _schema_version(db_path: Path) -> int:
    connection = sqlite3.connect(db_path)
    try:
        return _current_version(connection)
    finally:
        connection.close()


def _verify_existing_sidecars(db_path: Path) -> None:
    for suffix in ("-journal", "-wal", "-shm"):
        sidecar = db_path.with_name(db_path.name + suffix)
        if not sidecar.exists() and not sidecar.is_symlink():
            continue
        if sidecar.parent.resolve(strict=True) != db_path.parent.resolve(strict=True):
            raise StorageSchemaError("sqlite sidecar must stay inside protected root")
        _verify_path(sidecar, expected_mode=0o600, label="sqlite sidecar")
        if not sidecar.is_file():
            raise StorageSchemaError("sqlite sidecar must be a regular file")


def _verify_path(path: Path, *, expected_mode: int, label: str) -> None:
    try:
        info = path.stat(follow_symlinks=False)
    except FileNotFoundError as exc:
        raise StorageSchemaError(f"{label} is missing") from exc
    if stat.S_ISLNK(info.st_mode):
        raise StorageSchemaError(f"{label} must not be a symlink")
    if info.st_uid != os.getuid():
        raise StorageSchemaError(f"{label} owner mismatch")
    actual_mode = stat.S_IMODE(info.st_mode)
    if actual_mode != expected_mode:
        raise StorageSchemaError(f"{label} mode must be {expected_mode:04o}")


def _inside_git_worktree(path: Path) -> bool:
    resolved = path.resolve(strict=False)
    for candidate in (resolved, *resolved.parents):
        git_marker = candidate / ".git"
        if git_marker.exists() or git_marker.is_symlink():
            return True
    return False
