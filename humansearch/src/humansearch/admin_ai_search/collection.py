"""Private SQLite staging for exhaustive, read-only Gmail collection jobs."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast


class GmailReader(Protocol):
    def request(self, operation: str, args: dict[str, object]) -> object: ...


def now() -> str:
    return datetime.now(UTC).isoformat()


class CollectionStore:
    """No credentials or raw messages are written under public assets."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(path)
        os.chmod(path, 0o600)
        self.db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS collection_runs (
                id TEXT PRIMARY KEY, document TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS source_messages (
                id TEXT PRIMARY KEY, checksum TEXT NOT NULL, document TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS collection_checkpoints (
                run_id TEXT NOT NULL, scope TEXT NOT NULL, document TEXT NOT NULL,
                PRIMARY KEY(run_id, scope)
            );
            CREATE TABLE IF NOT EXISTS collection_run_messages (
                run_id TEXT NOT NULL, message_id TEXT NOT NULL, outcome TEXT NOT NULL,
                PRIMARY KEY(run_id, message_id)
            );
        """)

    def save_run(self, run: dict[str, Any]) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO collection_runs VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET document=excluded.document",
                (run["id"], json.dumps(run)),
            )

    def checkpoint(self, run_id: str, scope: str) -> dict[str, Any]:
        row = self.db.execute(
            "SELECT document FROM collection_checkpoints WHERE run_id=? AND scope=?",
            (run_id, scope),
        ).fetchone()
        if row:
            return cast(dict[str, Any], json.loads(row[0]))
        return {"pages": 0, "exhausted": False, "next_page_token": None,
                "message_ids": [], "page_history": []}

    def save_checkpoint(self, run_id: str, scope: str, state: dict[str, Any]) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO collection_checkpoints VALUES (?, ?, ?) "
                "ON CONFLICT(run_id,scope) DO UPDATE SET document=excluded.document",
                (run_id, scope, json.dumps(state)),
            )

    def upsert(self, run_id: str, message: dict[str, Any]) -> None:
        encoded = json.dumps(message, sort_keys=True, ensure_ascii=False)
        checksum = hashlib.sha256(encoded.encode()).hexdigest()
        message_id = message["id"]
        old = self.db.execute(
            "SELECT checksum FROM source_messages WHERE id=?", (message_id,)
        ).fetchone()
        outcome = "new" if old is None else ("unchanged" if old[0] == checksum else "updated")
        with self.db:
            self.db.execute(
                "INSERT INTO source_messages VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET checksum=excluded.checksum,document=excluded.document",
                (message_id, checksum, encoded),
            )
            self.db.execute(
                "INSERT INTO collection_run_messages VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                (run_id, message_id, outcome),
            )


def collect_mailbox(
    store: CollectionStore, reader: GmailReader, *, run_id: str | None = None,
    include_sent: bool = False,
) -> dict[str, Any]:
    """Inbox UNION the live label, never a keyword-limited intersection.

    Read full MIME for every message: neither subject nor snippet silently excludes
    a potential result. A page checkpoint advances only after every body is durable.
    """
    run_id = run_id or str(uuid.uuid4())
    existing = store.db.execute(
        "SELECT document FROM collection_runs WHERE id=?", (run_id,)
    ).fetchone()
    run = json.loads(existing[0]) if existing else {
        "id": run_id, "started_at": now(), "last_success_at": None,
        "retry_count": 0, "scopes": {},
    }
    run.update(status="RUNNING", finished_at=None, error=None)
    retry_base = run["retry_count"]
    store.save_run(run)
    try:
        labels = _object(reader.request("labels", {})).get("labels", [])
        matching = [item for item in labels if item.get("name") == "02aisearch"]
        if len(matching) != 1:
            raise ValueError("02aisearch label must be resolved uniquely from current account")
        scopes = {"02aisearch": matching[0]["id"], "INBOX": "INBOX"}
        if include_sent:
            scopes["SENT"] = "SENT"
        for scope, label_id in scopes.items():
            state = store.checkpoint(run_id, scope)
            if state.get("label_id", label_id) != label_id:
                raise ValueError("live label identity changed during resumed collection")
            state.update(label_id=label_id, query=None)
            while not state["exhausted"]:
                _collect_page(store, reader, run_id, scope, state)
                run["scopes"][scope] = state
                run["retry_count"] = retry_base + int(getattr(reader, "retry_count", 0))
                store.save_run(run)
            run["scopes"][scope] = state
        all_ids = [set(state["message_ids"]) for scope, state in run["scopes"].items()
                   if scope in {"INBOX", "02aisearch"}]
        run["union_count"] = len(set.union(*all_ids))
        run["overlap_count"] = sum(map(len, all_ids)) - run["union_count"]
        for outcome in ("new", "updated", "unchanged"):
            run[outcome] = store.db.execute(
                "SELECT count(*) FROM collection_run_messages WHERE run_id=? AND outcome=?",
                (run_id, outcome),
            ).fetchone()[0]
        total = len(set().union(*(set(state["message_ids"]) for state in run["scopes"].values())))
        run["total_message_count"] = total
        if sum(run[key] for key in ("new", "updated", "unchanged")) != total:
            raise ValueError("collection union/body reconciliation failed")
        failed = store.db.execute(
            "SELECT count(*) FROM collection_run_messages rm JOIN source_messages m "
            "ON m.id=rm.message_id WHERE rm.run_id=? AND "
            "json_extract(m.document,'$.collection_status')='FAILED'", (run_id,),
        ).fetchone()[0]
        run.update(status="PARTIAL" if failed else "SUCCEEDED", failed=failed, finished_at=now())
        if not failed:
            run["last_success_at"] = now()
        store.save_run(run)
        return cast(dict[str, Any], run)
    except Exception as error:
        # Original error lives only in the private job DB, never the API or PII logs.
        run.update(status="PARTIAL", finished_at=now(), error=str(error),
                   error_type=type(error).__name__)
        store.save_run(run)
        raise


def _collect_page(
    store: CollectionStore, reader: GmailReader, run_id: str, scope: str, state: dict[str, Any],
) -> None:
    token = state["next_page_token"]
    page = _object(reader.request("list", {"label_id": state["label_id"], "page_token": token}))
    ids = [item["id"] for item in page.get("messages", [])]
    for offset in range(0, len(ids), 50):
        chunk = ids[offset:offset + 50]
        # Read overlap only once per run, but refresh each message on subsequent runs.
        fresh = [i for i in chunk if store.db.execute(
            "SELECT 1 FROM collection_run_messages WHERE run_id=? AND message_id=?", (run_id, i)
        ).fetchone() is None]
        if not fresh:
            continue
        messages = reader.request("messages", {"ids": fresh})
        if not isinstance(messages, list) or [m.get("id") for m in messages] != fresh:
            raise ValueError("Gmail body response IDs differ from requested IDs")
        for message in messages:
            store.upsert(run_id, message)
    next_token = page.get("nextPageToken")
    seen = {p["request_page_token"] for p in state["page_history"]}
    if next_token is not None and (next_token == token or next_token in seen):
        raise ValueError("Gmail pagination token cycle")
    state["page_history"].append({"request_page_token": token, "next_page_token": next_token,
                                  "message_count": len(ids), "completed_at": now()})
    state["message_ids"] = list(dict.fromkeys([*state["message_ids"], *ids]))
    state.update(pages=state["pages"] + 1, exhausted=next_token is None,
                 next_page_token=next_token, last_success_at=now())
    store.save_checkpoint(run_id, scope, state)


def _object(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("Gmail response must be an object")
    return value
