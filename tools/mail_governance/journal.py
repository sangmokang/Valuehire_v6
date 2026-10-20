"""Append-only intent/observation journal. Imported receipts are not provider attestation."""
import json
import os
import sqlite3
from datetime import datetime, timezone

from .core import DESTINATION, MIRROR_MARKER, canonical, classify, digest, require, strings

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
 id TEXT PRIMARY KEY, account TEXT NOT NULL, message_id TEXT NOT NULL,
 content_hash TEXT NOT NULL, rule_version TEXT NOT NULL, payload_json TEXT NOT NULL,
 UNIQUE(account,message_id,content_hash,rule_version));
CREATE TABLE IF NOT EXISTS events (
 id TEXT PRIMARY KEY, review_id TEXT NOT NULL REFERENCES reviews(id), payload_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS operations (
 id TEXT PRIMARY KEY, review_id TEXT NOT NULL REFERENCES reviews(id), kind TEXT NOT NULL,
 dedup_key TEXT NOT NULL UNIQUE, payload_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS receipts (
 id INTEGER PRIMARY KEY, operation_id TEXT NOT NULL REFERENCES operations(id),
 state TEXT NOT NULL, payload_json TEXT NOT NULL, recorded_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS coverage (
 id INTEGER PRIMARY KEY, account TEXT NOT NULL, query TEXT NOT NULL, cursor TEXT,
 next_cursor TEXT, count INTEGER NOT NULL, outcome TEXT NOT NULL, capped INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS share_scopes (
 scope TEXT NOT NULL, content_hash TEXT NOT NULL, review_id TEXT NOT NULL REFERENCES reviews(id),
 PRIMARY KEY(scope,content_hash));
"""
TRANSITIONS = {"PLANNED": {"SENDING"}, "SENDING": {"SENT_UNVERIFIED", "AMBIGUOUS", "FAILED"},
               "SENT_UNVERIFIED": {"VERIFIED", "AMBIGUOUS", "FAILED"}, "AMBIGUOUS": {"VERIFIED"},
               "VERIFIED": set(), "FAILED": set()}


class Journal:
    def __init__(self, path):
        fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        os.fchmod(fd, 0o600)
        os.close(fd)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(SCHEMA)
        for table in ("reviews", "events", "operations", "receipts", "coverage", "share_scopes"):
            for action in ("UPDATE", "DELETE"):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'append-only journal'); END")
        self._seed_share_scopes()
        require(self.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "SQLite integrity failure")
        require(not self.db.execute("PRAGMA foreign_key_check").fetchall(), "SQLite foreign key failure")
        self.db.commit()

    def close(self):
        self.db.close()

    def _seed_share_scopes(self):
        rows = self.db.execute("SELECT o.review_id,o.payload_json,r.payload_json AS review_json FROM operations o JOIN reviews r ON r.id=o.review_id WHERE o.kind='share'").fetchall()
        for row in rows:
            message = json.loads(row["review_json"])["message"]
            payload = json.loads(row["payload_json"])
            if message["rfc_message_id"]:
                scope = digest([message["rfc_message_id"], payload["account"]])
                self.db.execute("INSERT OR IGNORE INTO share_scopes VALUES(?,?,?)", (scope, message["source_hash"], row["review_id"]))

    def _claim_share_scope(self, message, review_id, reserve):
        if message["rfc_message_id"] is None:
            return True
        scope = digest([message["rfc_message_id"], DESTINATION])
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            rows = self.db.execute("SELECT content_hash FROM share_scopes WHERE scope=?", (scope,)).fetchall()
            if any(row[0] != message["source_hash"] for row in rows):
                return False
            if reserve:
                self.db.execute("INSERT OR IGNORE INTO share_scopes VALUES(?,?,?)", (scope, message["source_hash"], review_id))
        return True

    def import_review(self, message, review):
        result = classify(message, review)
        key = digest([message["account"], message["message_id"], message["source_hash"], review["rule_version"]])
        stored_message = dict(message)
        if not (message["source_kind"] == "direct_customer" and "ontology" in review["mail_types"]):
            stored_message.pop("authored_text")
            stored_message.pop("html", None)
        payload = canonical(dict(message=stored_message, review=review, result=result))
        previous = self.db.execute("SELECT payload_json FROM reviews WHERE id=?", (key,)).fetchone()
        if previous:
            require(previous[0] == payload, "immutable review conflict: use a new rule_version")
            return key
        with self.db:
            self.db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?)", (key, message["account"], message["message_id"], message["source_hash"], review["rule_version"], payload))
            for event in result["events"]:
                event_id = digest([key, event])
                self.db.execute("INSERT OR IGNORE INTO events VALUES(?,?,?)", (event_id, key, canonical(event)))
        return key

    def review(self, key):
        row = self.db.execute("SELECT payload_json FROM reviews WHERE id=?", (key,)).fetchone()
        require(row is not None, "unknown review")
        return json.loads(row[0])

    def _plan_operation(self, review_id, kind, dedup_key, payload):
        key = digest([kind, dedup_key])
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO operations VALUES(?,?,?,?,?)", (key, review_id, kind, dedup_key, canonical(payload)))
            if not self.db.execute("SELECT 1 FROM receipts WHERE operation_id=?", (key,)).fetchone():
                self._append_receipt(key, "PLANNED", {})
        return self.operation(key)

    def plan(self, review_id):
        data = self.review(review_id)
        message, result = data["message"], data["result"]
        common = dict(content_hash=message["source_hash"], labels=result["labels"], mode="additive")
        ops = []
        if result["labels"]:
            payload = dict(common, account=message["account"], message_id=message["message_id"],
                           labels=result["resulting_labels"], add_labels=sorted(set(result["labels"]) - set(message["existing_labels"])))
            ops.append(self._plan_operation(review_id, "source_labels", "source:" + review_id, payload))
        mirror = (MIRROR_MARKER in message["subject"] or message["account"].casefold() == DESTINATION
                  or message["from_address"].casefold() == DESTINATION)
        if mirror:
            return dict(operations=ops, sharing="mirror_or_dev_source")
        if not result["labels"]:
            return dict(operations=ops, sharing="not_shareable_type")
        source = ["rfc", message["rfc_message_id"]] if message["rfc_message_id"] else ["local", message["account"], message["message_id"]]
        global_key = digest([source, message["source_hash"], DESTINATION])
        already_recipient = DESTINATION in [address.casefold() for address in message["to_addresses"]]
        if not self._claim_share_scope(message, review_id, reserve=not already_recipient):
            return dict(operations=ops, sharing="rfc_variant_review_required")
        receiver = dict(common, account=DESTINATION, source_review_id=review_id, mirror_marker=MIRROR_MARKER)
        ops.append(self._plan_operation(review_id, "receiver_labels", "receiver:" + digest([global_key, result["labels"]]), receiver))
        if already_recipient:
            return dict(operations=ops, sharing="already_recipient_label_pending")
        ops.append(self._plan_operation(review_id, "share", "share:" + global_key, receiver))
        return dict(operations=ops, sharing="forward_planned")

    def operation(self, key):
        row = self.db.execute("SELECT * FROM operations WHERE id=?", (key,)).fetchone()
        require(row is not None, "unknown operation")
        state = self.db.execute("SELECT state FROM receipts WHERE operation_id=? ORDER BY id DESC LIMIT 1", (key,)).fetchone()
        require(state is not None, "operation has no journal state")
        return dict(id=row["id"], review_id=row["review_id"], kind=row["kind"], state=state[0], payload=json.loads(row["payload_json"]))

    def _append_receipt(self, key, state, receipt):
        self.db.execute("INSERT INTO receipts(operation_id,state,payload_json,recorded_at) VALUES(?,?,?,?)",
                        (key, state, canonical(receipt), datetime.now(timezone.utc).isoformat()))

    def receipt(self, key, state, receipt):
        require(type(receipt) is dict, "receipt must be an object")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            operation = self.operation(key)
            require(state in TRANSITIONS.get(operation["state"], set()), "unsafe or invalid state transition")
            if state == "VERIFIED":
                self._verify_readback(operation, receipt)
            self._append_receipt(key, state, receipt)
        return self.operation(key)

    @staticmethod
    def _verify_readback(operation, receipt):
        expected = operation["payload"]
        observed = receipt.get("receiver_observation")
        labels = receipt.get("label_observation")
        require(type(observed) is dict and type(labels) is dict, "independent body and label readbacks required")
        require(observed.get("account") == expected["account"] and observed.get("content_hash") == expected["content_hash"], "receiver identity/body mismatch")
        require(type(observed.get("message_id")) is str and bool(observed["message_id"]), "receiver message id missing")
        if operation["kind"] == "source_labels":
            require(observed["message_id"] == expected["message_id"], "source message mismatch")
        require(labels.get("account") == observed["account"] and labels.get("message_id") == observed["message_id"], "label readback identity mismatch")
        strings(labels.get("labels"), "readback labels")
        require(set(expected["labels"]) <= set(labels["labels"]), "required labels not observed")

    def coverage(self, account, query, cursor, next_cursor, count, outcome, capped):
        require(type(account) is str and account and type(query) is str and query, "account/query required")
        require(all(v is None or (type(v) is str and v) for v in (cursor, next_cursor)), "invalid cursor")
        require(type(count) is int and count >= 0 and type(capped) is bool, "invalid coverage count/cap")
        require(outcome in ("ok", "failed", "unknown"), "invalid coverage outcome")
        with self.db:
            self.db.execute("INSERT INTO coverage(account,query,cursor,next_cursor,count,outcome,capped) VALUES(?,?,?,?,?,?,?)", (account, query, cursor, next_cursor, count, outcome, int(capped)))
        return self.coverage_status(account, query)

    def coverage_status(self, account, query):
        rows = self.db.execute("SELECT * FROM coverage WHERE account=? AND query=? ORDER BY id", (account, query)).fetchall()
        cursor, complete, count = None, False, 0
        for row in rows:
            if row["cursor"] != cursor or row["outcome"] != "ok" or row["capped"] or complete:
                return dict(complete=False, outcome="unknown", count=count, next_cursor=cursor)
            count += row["count"]
            cursor = row["next_cursor"]
            complete = cursor is None
        return dict(complete=bool(rows) and complete, outcome="ok" if rows else "unknown", count=count, next_cursor=cursor)
