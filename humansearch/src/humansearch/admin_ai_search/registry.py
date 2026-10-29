"""Normalized private staging and permanent weekly display-number allocation."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast
from zoneinfo import ZoneInfo

TABLES = (
    "source_attachments", "positions", "candidates", "batch_source_messages",
    "candidate_batches", "candidate_position_evaluations", "score_components",
    "contact_events", "contact_evidence", "review_queue",
)


def operation_week(instant: datetime) -> tuple[str, int, int]:
    if instant.tzinfo is None:
        raise ValueError("operation week requires an aware timestamp")
    day = instant.astimezone(ZoneInfo("Asia/Seoul")).date()
    sunday = day - timedelta(days=(day.weekday() + 1) % 7)
    # Preserve the existing administrator meeting-week convention.
    year, week, _ = (sunday + timedelta(days=8)).isocalendar()
    return f"{year}-W{week:02d}", year, week


class Registry:
    def __init__(self, path: Path) -> None:
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        for table in TABLES:
            self.db.execute(f"CREATE TABLE IF NOT EXISTS {table} "
                            "(id TEXT PRIMARY KEY, document TEXT NOT NULL)")
        self.db.execute("""CREATE TABLE IF NOT EXISTS batches (
            id TEXT PRIMARY KEY, week_year INTEGER NOT NULL, week_number INTEGER NOT NULL,
            sequence INTEGER, provisional_sequence INTEGER, grouping_status TEXT NOT NULL,
            display_number TEXT NOT NULL, document TEXT NOT NULL,
            UNIQUE(week_year,week_number,sequence),
            UNIQUE(week_year,week_number,provisional_sequence))""")
        self.db.commit()

    def put(self, table: str, document: dict[str, Any]) -> None:
        if table not in TABLES:
            raise ValueError("unknown normalized table")
        with self.db:
            self.db.execute(
                f"INSERT INTO {table} VALUES (?,?) ON CONFLICT(id) "
                "DO UPDATE SET document=excluded.document",
                (document["id"], json.dumps(document, ensure_ascii=False)),
            )

    def register_batch(self, batch: dict[str, Any]) -> dict[str, Any]:
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            old = self.db.execute("SELECT * FROM batches WHERE id=?", (batch["id"],)).fetchone()
            if old is not None:
                result = dict(old)
                previous = json.loads(result["document"])
                # Keep all source references and first execution anchor on rediscovery.
                for key in ("source_message_ids", "actor_evidence"):
                    values = [*previous.get(key, []), *batch.get("document", {}).get(key, [])]
                    batch.setdefault("document", {})[key] = list({
                        json.dumps(value, sort_keys=True): value for value in values
                    }.values())
                result["document"] = {**previous, **batch.get("document", {})}
                self.db.execute("UPDATE batches SET document=? WHERE id=?",
                                (json.dumps(result["document"]), batch["id"]))
                return result
            provisional = batch["grouping_status"] == "PROVISIONAL"
            sequence_column = "provisional_sequence" if provisional else "sequence"
            number = self.db.execute(
                f"SELECT COALESCE(MAX({sequence_column}),0)+1 FROM batches "
                "WHERE week_year=? AND week_number=?", (batch["week_year"], batch["week_number"]),
            ).fetchone()[0]
            result = {**batch, "sequence": None if provisional else number,
                      "provisional_sequence": number if provisional else None,
                      "display_number": f"W{batch['week_number']:02d}-{'P' if provisional else ''}{number:02d}"}
            self.db.execute("INSERT INTO batches VALUES (?,?,?,?,?,?,?,?)", (
                result["id"], result["week_year"], result["week_number"], result["sequence"],
                result["provisional_sequence"], result["grouping_status"], result["display_number"],
                json.dumps(result["document"]),
            ))
            return result

    def documents(self, table: str) -> list[dict[str, Any]]:
        if table not in (*TABLES, "source_messages", "collection_runs", "batches"):
            raise ValueError("unknown table")
        return [cast(dict[str, Any], json.loads(row[0])) for row in self.db.execute(
            f"SELECT document FROM {table} ORDER BY id"
        )]
