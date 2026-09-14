"""HS-03.01 SQLite schema bootstrap placeholder for RED tests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

CURRENT_SCHEMA_VERSION = 1
SUPPORTED_MIGRATION_RANGE = (0, CURRENT_SCHEMA_VERSION)


class StorageSchemaError(ValueError):
    """Closed storage schema setup error."""


@dataclass(frozen=True, slots=True)
class StorageSchemaResult:
    """Result returned after schema setup."""

    db_path: Path
    schema_version: int
    applied_migrations: tuple[int, ...]


def initialize_humansearch_storage(protected_root: Path) -> StorageSchemaResult:
    """Install the HS SQLite schema. Placeholder intentionally fails RED tests."""

    return StorageSchemaResult(
        db_path=protected_root / "humansearch.sqlite3",
        schema_version=0,
        applied_migrations=(),
    )
