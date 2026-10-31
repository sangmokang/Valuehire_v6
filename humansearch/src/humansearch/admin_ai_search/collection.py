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
    refresh_since_start: bool = False,
    incremental: bool = False,
) -> dict[str, Any]:
    """Inbox UNION the live label, never a keyword-limited intersection.

    Read full MIME for every message: neither subject nor snippet silently excludes
    a potential result. A page checkpoint advances only after every body is durable.
    """
    run_id = run_id or str(uuid.uuid4())
    existing = store.db.execute(
        "SELECT document FROM collection_runs WHERE id=?", (run_id,)
    ).fetchone()
    baseline = None
    if incremental and not existing:
        required = {"INBOX", "02aisearch", *({"SENT"} if include_sent else set())}
        completed = [json.loads(row[0]) for row in store.db.execute(
            "SELECT document FROM collection_runs WHERE json_extract(document,'$.status')='SUCCEEDED'")]
        eligible = [r for r in completed if required <= r["scopes"].keys()
                    and all(s["exhausted"] for s in r["scopes"].values())]
        if not eligible:
            raise ValueError("incremental collection requires a complete baseline for every scope")
        baseline = max(eligible, key=lambda r: r["started_at"])
    run = json.loads(existing[0]) if existing else {
        "id": run_id, "started_at": now(), "last_success_at": None,
        "retry_count": 0, "scopes": {},
    }
    if existing and incremental != bool(run.get("incremental_since")):
        raise ValueError("resumed collection mode differs from its checkpoint")
    saved_scopes = set(run["scopes"]) | {row[0] for row in store.db.execute(
        "SELECT scope FROM collection_checkpoints WHERE run_id=?", (run_id,))}
    if run.get("active_scope"):
        saved_scopes.add(run["active_scope"])
    if existing and include_sent != run.get("include_sent", "SENT" in saved_scopes):
        raise ValueError("resumed collection scope differs from its checkpoint")
    if (existing and not refresh_since_start
            and run.get("refresh_since_start", any(s.endswith("_DELTA") for s in saved_scopes))):
        raise ValueError("resumed collection refresh scope differs from its checkpoint")
    run["include_sent"] = include_sent
    run["refresh_since_start"] = refresh_since_start
    if baseline:
        run.update(parent_run_id=baseline["id"], incremental_since=baseline["started_at"])
    run.update(status="RUNNING", finished_at=None, error=None)
    run.pop("error_type", None)
    run.setdefault("errors", [])
    run["attempt_count"] = run.get("attempt_count", 0) + 1
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
        if refresh_since_start:
            scopes.update({f"{name}_DELTA": label for name, label in list(scopes.items())})
        for scope, label_id in scopes.items():
            run["active_scope"] = scope
            state = store.checkpoint(run_id, scope)
            if state.get("label_id", label_id) != label_id:
                raise ValueError("live label identity changed during resumed collection")
            since = run.get("incremental_since")
            if scope.endswith("_DELTA"):
                since = run["started_at"]
            query = (f"after:{int(datetime.fromisoformat(since).timestamp())}"
                     if since and not scope.startswith("02aisearch") else None)
            state.update(label_id=label_id, query=query)
            while not state["exhausted"]:
                _collect_page(store, reader, run_id, scope, state, reuse_cached=incremental)
                run["scopes"][scope] = state
                run["retry_count"] = retry_base + int(getattr(reader, "retry_count", 0))
                store.save_run(run)
            run["scopes"][scope] = state
        all_ids = [set().union(*(set(state["message_ids"]) for scope, state in run["scopes"].items()
                                if scope in {base, base + "_DELTA"}))
                   for base in ("INBOX", "02aisearch")]
        run["union_count"] = len(set.union(*all_ids))
        run["overlap_count"] = sum(map(len, all_ids)) - run["union_count"]
        run["scope_unique_counts"] = dict(zip(("INBOX", "02aisearch"), map(len, all_ids), strict=True))
        if any(not state["exhausted"] for state in run["scopes"].values()):
            raise ValueError("a prior scope is incomplete; resume with the original scope flags")
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
        run["retry_count"] = retry_base + int(getattr(reader, "retry_count", 0))
        run["errors"].append({"message": str(error), "type": type(error).__name__,
                              "occurred_at": now(), "scope": run.get("active_scope"),
                              "attempt": run["attempt_count"]})
        store.save_run(run)
        raise


def _collect_page(
    store: CollectionStore, reader: GmailReader, run_id: str, scope: str, state: dict[str, Any],
    *, reuse_cached: bool = False,
) -> None:
    token = state["next_page_token"]
    pending = state.get("pending_page")
    if pending is None:
        page = _object(reader.request("list", {"label_id": state["label_id"], "page_token": token, "query": state["query"]}))
        state["pending_page"] = dict(page)
        store.save_checkpoint(run_id, scope, state)
    else:
        page = _object(pending)
    ids = [item["id"] for item in page.get("messages", [])]
    for offset in range(0, len(ids), 50):
        chunk = ids[offset:offset + 50]
        # Read overlap only once per run, but refresh each message on subsequent runs.
        fresh = [i for i in chunk if store.db.execute(
            "SELECT 1 FROM collection_run_messages WHERE run_id=? AND message_id=?", (run_id, i)
        ).fetchone() is None]
        if not fresh:
            continue
        if reuse_cached:
            for identity in fresh.copy():
                saved = store.db.execute("SELECT document FROM source_messages WHERE id=?",
                                         (identity,)).fetchone()
                if saved and json.loads(saved[0]).get("collection_status") != "FAILED":
                    store.upsert(run_id, json.loads(saved[0]))
                    fresh.remove(identity)
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
    state.pop("pending_page", None)
    store.save_checkpoint(run_id, scope, state)


def _object(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("Gmail response must be an object")
    return value
