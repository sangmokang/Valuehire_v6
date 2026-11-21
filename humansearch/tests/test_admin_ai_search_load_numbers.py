"""The PostgreSQL loader must never publish numbers that differ from staging."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from humansearch.admin_ai_search.registry import Registry

LOADER = Path(__file__).parents[2] / "tools/admin-ai-search/load-postgres.py"


def test_loader_numbers_legacy_rows_and_compares_before_publishing(tmp_path: Path) -> None:
    path = tmp_path / "stage.sqlite"
    registry = Registry(path)
    registry.register_batch({"id": "a", "week_year": 2026, "week_number": 45,
                             "grouping_status": "PROVISIONAL", "document": {"id": "a"}})
    with registry.db:
        registry.db.execute("INSERT INTO batches VALUES (?,?,?,?,?,?,?,?)",
                            ("legacy", 2026, 45, None, 1, "PROVISIONAL", "W45-P01", json.dumps({"id": "legacy"})))
    registry.db.close()
    # An unreachable DSN stops the loader before any write; staging must be numbered first.
    result = subprocess.run([sys.executable, str(LOADER), "--database", str(path),
                             "--dsn", "postgresql://invalid@127.0.0.1:1/none"],
                            capture_output=True, text=True, check=False,
                            env={"PYTHONPATH": str(LOADER.parents[2] / "humansearch/src"), "PATH": "/usr/bin:/bin:/opt/homebrew/opt/postgresql@16/bin"})
    assert result.returncode != 0
    numbers = dict(sqlite3.connect(path).execute("SELECT id,display_number FROM batches").fetchall())
    assert numbers == {"a": "W45-01", "legacy": "W45-02"}


def test_batch_registration_and_number_check_share_one_transaction() -> None:
    source = LOADER.read_text()
    batch_block = source[source.index("staged_batches"):source.index("for table in TABLES:")]
    assert "BEGIN" in batch_block and "RAISE EXCEPTION" in batch_block and "COMMIT" in batch_block
