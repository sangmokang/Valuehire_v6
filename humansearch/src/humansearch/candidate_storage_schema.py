"""HS-03.02 v2 SQLite schema: raw+normalized candidate identity + observation history.

Design decision (2026-09-17): the v1 schema (task/hs-0301-schema-20260917 stack)
stored only irreversible HMAC/hash digests of candidate identity and never the raw
email/URL — making the data unusable for actually contacting a candidate. This
schema stores raw values as evidence, normalized values for dedup, and treats
"the same candidate seen again" as a new observation row, not an overwrite.
"""

from __future__ import annotations

import os
import sqlite3
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Final

CURRENT_SCHEMA_VERSION: Final = 1
_DB_FILENAME: Final = "humansearch_candidates.sqlite3"
_ROOT_MODE: Final = 0o700
_DB_FILE_MODE: Final = 0o600

_MIGRATIONS: Final[tuple[tuple[int, str, tuple[str, ...]], ...]] = (
    (
        1,
        "initial_candidate_storage_v2",
        (
            """
            create table hs_schema_migrations (
              version integer primary key,
              name text not null,
              applied_at text not null default current_timestamp
            )
            """,
            """
            create table hs_candidates (
              candidate_id integer primary key autoincrement,
              position_ref text not null,
              channel text not null check (channel in ('saramin','jobkorea','linkedin_rps')),
              candidate_ref_raw text not null,
              candidate_ref_normalized text not null,
              email_raw text,
              email_normalized text,
              profile_url_raw text,
              profile_url_normalized text,
              candidate_key_hmac text,
              created_at text not null default current_timestamp,
              unique (position_ref, channel, candidate_ref_normalized)
            )
            """,
            """
            create table hs_candidate_observations (
              observation_id integer primary key autoincrement,
              candidate_id integer not null references hs_candidates(candidate_id),
              source_type text not null check (source_type in ('saramin','jobkorea','linkedin_rps')),
              source_url_raw text,
              source_url_normalized text,
              observed_at text not null,
              ingestion_id text not null,
              created_at text not null default current_timestamp,
              unique (candidate_id, ingestion_id)
            )
            """,
        ),
    ),
)


class CandidateStorageSchemaError(ValueError):
    """Closed schema setup error without leaking a raw filesystem path."""


@dataclass(frozen=True, slots=True)
class StorageSchemaResult:
    db_path: Path
    protected_root: Path
    schema_version: int


def initialize_candidate_storage(
    protected_root: Path, *, db_filename: str = _DB_FILENAME
) -> StorageSchemaResult:
    """Bootstrap (idempotently) the candidate storage DB under a checked local root."""
    root = _prepare_root(protected_root)
    db_path = root / db_filename
    if db_path.is_symlink():
        raise CandidateStorageSchemaError("db file must not be a symlink")
    _prepare_db_file(db_path)
    applied_version = _apply_schema(db_path)
    return StorageSchemaResult(db_path=db_path, protected_root=root, schema_version=applied_version)


def _prepare_root(root: Path) -> Path:
    if root.is_symlink():
        raise CandidateStorageSchemaError("protected root must not be a symlink")
    if not root.exists():
        old_umask = os.umask(0o077)
        try:
            root.mkdir(mode=_ROOT_MODE, parents=True)
        finally:
            os.umask(old_umask)
    info = root.stat(follow_symlinks=False)
    if not root.is_dir():
        raise CandidateStorageSchemaError("protected root must be a directory")
    if stat.S_IMODE(info.st_mode) != _ROOT_MODE:
        raise CandidateStorageSchemaError(f"protected root mode must be {_ROOT_MODE:04o}")
    return root.resolve(strict=True)


def _prepare_db_file(db_path: Path) -> None:
    if db_path.exists():
        info = db_path.stat(follow_symlinks=False)
        if not db_path.is_file():
            raise CandidateStorageSchemaError("db file must be a regular file")
        if stat.S_IMODE(info.st_mode) != _DB_FILE_MODE:
            raise CandidateStorageSchemaError(f"db file mode must be {_DB_FILE_MODE:04o}")
        return
    old_umask = os.umask(0o077)
    try:
        fd = os.open(db_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, _DB_FILE_MODE)
        os.close(fd)
    finally:
        os.umask(old_umask)


def _apply_schema(db_path: Path) -> int:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("pragma foreign_keys = on")
        connection.execute("begin")
        current = _current_version(connection)
        applied = current
        for version, name, statements in _MIGRATIONS:
            if version <= current:
                continue
            for statement in statements:
                connection.execute(statement)
            connection.execute(
                "insert into hs_schema_migrations(version, name) values (?, ?)", (version, name)
            )
            applied = version
        connection.commit()
        return applied
    except sqlite3.Error as exc:
        connection.rollback()
        raise CandidateStorageSchemaError("migration failed") from exc
    finally:
        connection.close()


def _current_version(connection: sqlite3.Connection) -> int:
    exists = connection.execute(
        "select 1 from sqlite_master where type = 'table' and name = 'hs_schema_migrations'"
    ).fetchone()
    if exists is None:
        return 0
    row = connection.execute("select max(version) from hs_schema_migrations").fetchone()
    return int(row[0] or 0)
