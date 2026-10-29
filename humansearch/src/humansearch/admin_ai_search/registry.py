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
        self._candidate_keys: set[str] | None = None
        for table in TABLES:
            self.db.execute(f"CREATE TABLE IF NOT EXISTS {table} "
                            "(id TEXT PRIMARY KEY, document TEXT NOT NULL)")
        self.db.execute("""CREATE TABLE IF NOT EXISTS batches (
            id TEXT PRIMARY KEY, week_year INTEGER NOT NULL, week_number INTEGER NOT NULL,
            sequence INTEGER, provisional_sequence INTEGER, grouping_status TEXT NOT NULL,
            display_number TEXT NOT NULL, document TEXT NOT NULL,
            UNIQUE(week_year,week_number,sequence),
            UNIQUE(week_year,week_number,provisional_sequence))""")
        self.db.execute("CREATE INDEX IF NOT EXISTS evaluation_pair ON candidate_position_evaluations "
                        "(json_extract(document,'$.candidate_id'),json_extract(document,'$.position_id'))")
        self.db.execute("CREATE INDEX IF NOT EXISTS review_source ON review_queue "
                        "(json_extract(document,'$.source_message_id'))")
        self.db.execute("CREATE INDEX IF NOT EXISTS batch_source_identity ON batch_source_messages "
                        "(json_extract(document,'$.source_message_id'),json_extract(document,'$.section_index'))")
        self.db.execute("CREATE INDEX IF NOT EXISTS batch_group_identity ON batches "
                        "(json_extract(document,'$.grouping_key'))")
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
        if table == "candidates" and self._candidate_keys is not None:
            self._candidate_keys.add(document["id"])

    def candidate_keys(self) -> set[str]:
        if self._candidate_keys is None:
            self._candidate_keys = {row[0] for row in self.db.execute("SELECT id FROM candidates")}
        return self._candidate_keys

    def resolve_batch_id(self, grouping_key: str | None, preferred: str,
                         message_id: str, section_index: int) -> str:
        prior = self.db.execute("SELECT document FROM batch_source_messages WHERE "
            "json_extract(document,'$.source_message_id')=? AND json_extract(document,'$.section_index')=? "
            "ORDER BY rowid DESC LIMIT 1", (message_id, section_index)).fetchone()
        prior_id = json.loads(prior[0])["batch_id"] if prior else None
        grouped = self.db.execute("SELECT id FROM batches WHERE json_extract(document,'$.grouping_key')=? "
            "AND json_extract(document,'$.superseded_by') IS NULL LIMIT 1", (grouping_key,)).fetchone() if grouping_key else None
        identity = grouped[0] if grouped else prior_id or preferred
        if prior_id and prior_id != identity:
            old = self.db.execute("SELECT grouping_status,document FROM batches WHERE id=?", (prior_id,)).fetchone()
            if old[0] == "CONFIRMED":
                raise ValueError("conflicting confirmed batch identities require review")
            with self.db:
                self.db.execute("UPDATE batches SET document=? WHERE id=?", (
                    json.dumps({**json.loads(old[1]), "superseded_by": identity,
                                "superseded_reason": "explicit_execution_evidence"}), prior_id))
        return str(identity)

    def register_batch(self, batch: dict[str, Any]) -> dict[str, Any]:
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            old = self.db.execute("SELECT * FROM batches WHERE id=?", (batch["id"],)).fetchone()
            if old is not None:
                result = dict(old)
                previous = json.loads(result["document"])
                if old["grouping_status"] == "PROVISIONAL" and batch["grouping_status"] == "CONFIRMED":
                    number = self.db.execute("SELECT COALESCE(MAX(sequence),0)+1 FROM batches "
                        "WHERE week_year=? AND week_number=?", (old["week_year"],old["week_number"])).fetchone()[0]
                    previous["display_number_history"] = [*previous.get("display_number_history", []), old["display_number"]]
                    result.update(sequence=number, grouping_status="CONFIRMED",
                                  display_number=f"W{old['week_number']:02d}-{number:02d}")
                if batch.get("document", {}).get("execution_time_source") == "received_at_fallback":
                    for field in ("executed_at", "execution_time_source", "execution_time_confidence", "execution_time_reason"):
                        if field in previous:
                            batch.setdefault("document", {})[field] = previous[field]
                if previous.get("execution_time_source") == "explicit_source_timestamp":
                    for field in ("executed_at", "execution_time_source", "execution_time_confidence", "execution_time_reason"):
                        batch.setdefault("document", {})[field] = previous[field]
                if "week_id" in previous:
                    batch.setdefault("document", {})["week_id"] = previous["week_id"]
                # Keep all source references and first execution anchor on rediscovery.
                for key in ("source_message_ids", "actor_evidence"):
                    values = [*previous.get(key, []), *batch.get("document", {}).get(key, [])]
                    batch.setdefault("document", {})[key] = list({
                        json.dumps(value, sort_keys=True): value for value in values
                    }.values())
                result["document"] = {**previous, **batch.get("document", {})}
                if previous.get("grouping_key") and not result["document"].get("grouping_key"):
                    result["document"]["grouping_key"] = previous["grouping_key"]
                self.db.execute("UPDATE batches SET document=?,sequence=?,grouping_status=?,display_number=? WHERE id=?",
                                (json.dumps(result["document"]),result["sequence"],result["grouping_status"],
                                 result["display_number"],batch["id"]))
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
