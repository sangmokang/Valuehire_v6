"""Append-only intent/observation journal. Imported receipts are not provider attestation."""
import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone

from .core import DESTINATION, MIRROR_MARKER, canonical, classify, digest, normalize_address, require, strings

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


def stored_payload(message, review, result):
    """Minimize Golden evidence without losing exact ontology event evidence."""
    payload = json.loads(canonical(dict(message=message, review=review, result=result)))
    if not (message["source_kind"] == "direct_customer" and "ontology" in review["mail_types"]):
        payload["message"].pop("authored_text", None)
        payload["message"].pop("html", None)
        for axis in payload["review"]["golden_axes"].values():
            item = axis["evidence"]
            if item is not None and "quote" in item:
                item["quote_sha256"] = hashlib.sha256(item.pop("quote").encode("utf-8")).hexdigest()
    return payload


class Journal:
    def __init__(self, path):
        fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        os.fchmod(fd, 0o600)
        os.close(fd)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(SCHEMA)
        immutable_keys = {
            "reviews": "id=NEW.id OR (account=NEW.account AND message_id=NEW.message_id AND content_hash=NEW.content_hash AND rule_version=NEW.rule_version)",
            "events": "id=NEW.id",
            "operations": "id=NEW.id OR dedup_key=NEW.dedup_key",
            "receipts": "id=NEW.id",
            "coverage": "id=NEW.id",
            "share_scopes": "scope=NEW.scope AND content_hash=NEW.content_hash",
        }
        for table, keys in immutable_keys.items():
            for action in ("UPDATE", "DELETE"):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'append-only journal'); END")
            self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_INSERT BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {table} WHERE rowid=NEW.rowid OR ({keys})) BEGIN SELECT RAISE(ABORT,'append-only journal'); END")
        self._seed_share_scopes()
        require(self.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "SQLite integrity failure")
        require(not self.db.execute("PRAGMA foreign_key_check").fetchall(), "SQLite foreign key failure")
        self.db.commit()

    def close(self):
        self.db.close()

    def _seed_share_scopes(self):
        rows = self.db.execute("SELECT o.review_id,o.payload_json,r.payload_json AS review_json FROM operations o JOIN reviews r ON r.id=o.review_id WHERE o.kind IN ('share','receiver_labels')").fetchall()
        for row in rows:
            message = json.loads(row["review_json"])["message"]
            payload = json.loads(row["payload_json"])
            if message["rfc_message_id"]:
                scope = digest([message["rfc_message_id"], payload["account"]])
                self.db.execute("INSERT INTO share_scopes SELECT ?,?,? WHERE NOT EXISTS(SELECT 1 FROM share_scopes WHERE scope=? AND content_hash=?)", (scope, message["source_hash"], row["review_id"], scope, message["source_hash"]))

    def _claim_share_scope(self, message, review_id):
        if message["rfc_message_id"] is None:
            return True
        scope = digest([message["rfc_message_id"], DESTINATION])
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            rows = self.db.execute("SELECT content_hash FROM share_scopes WHERE scope=?", (scope,)).fetchall()
            if any(row[0] != message["source_hash"] for row in rows):
                return False
            self.db.execute("INSERT INTO share_scopes SELECT ?,?,? WHERE NOT EXISTS(SELECT 1 FROM share_scopes WHERE scope=? AND content_hash=?)", (scope, message["source_hash"], review_id, scope, message["source_hash"]))
        return True

    def import_review(self, message, review):
        result = classify(message, review)
        key = digest([message["account"], message["message_id"], message["source_hash"], review["rule_version"]])
        payload = stored_payload(message, review, result)
        previous = self.db.execute("SELECT payload_json FROM reviews WHERE id=?", (key,)).fetchone()
        if previous:
            first = json.loads(previous[0])
            for field in ("observed_at", "existing_labels"):
                payload["message"][field] = first["message"][field]
            payload["result"]["resulting_labels"] = first["result"]["resulting_labels"]
            # Older rows retain their original bytes; compare equivalent minimized views.
            require(stored_payload(**first) == payload, "immutable review conflict: explicit rule migration required")
            return key
        with self.db:
            self.db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?)", (key, message["account"], message["message_id"], message["source_hash"], review["rule_version"], canonical(payload)))
            for event in result["events"]:
                event_id = digest([key, event])
                self.db.execute("INSERT INTO events SELECT ?,?,? WHERE NOT EXISTS(SELECT 1 FROM events WHERE id=?)", (event_id, key, canonical(event), event_id))
        return key

    def review(self, key):
        row = self.db.execute("SELECT payload_json FROM reviews WHERE id=?", (key,)).fetchone()
        require(row is not None, "unknown review")
        return json.loads(row[0])

    def _plan_operation(self, review_id, kind, dedup_key, payload):
        key = digest([kind, dedup_key])
        with self.db:
            self.db.execute("INSERT INTO operations SELECT ?,?,?,?,? WHERE NOT EXISTS(SELECT 1 FROM operations WHERE id=? OR dedup_key=?)", (key, review_id, kind, dedup_key, canonical(payload), key, dedup_key))
            if not self.db.execute("SELECT 1 FROM receipts WHERE operation_id=?", (key,)).fetchone():
                self._append_receipt(key, "PLANNED", {})
        return self.operation(key)

    def plan(self, review_id):
        data = self.review(review_id)
        message, result = data["message"], data["result"]
        common = dict(content_hash=message["source_hash"], labels=result["labels"], mode="additive")
        ops = []
        if result["labels"]:
            payload = dict(common, account=normalize_address(message["account"]), message_id=message["message_id"],
                           labels=result["resulting_labels"], add_labels=sorted(set(result["labels"]) - set(message["existing_labels"])))
            ops.append(self._plan_operation(review_id, "source_labels", "source:" + review_id, payload))
        mirror = (MIRROR_MARKER in message["subject"] or normalize_address(message["account"]) == DESTINATION
                  or normalize_address(message["from_address"]) == DESTINATION)
        if mirror:
            return dict(operations=ops, sharing="mirror_or_dev_source")
        if not result["labels"]:
            return dict(operations=ops, sharing="not_shareable_type")
        source = ["rfc", message["rfc_message_id"]] if message["rfc_message_id"] else ["local", message["account"], message["message_id"]]
        if message["rfc_message_id"] is None:
            return dict(operations=ops, sharing="local_identity_reconciliation_required",
                        source_identity=source, duplicate_risk=True)
        global_key = digest([source, message["source_hash"], DESTINATION])
        already_recipient = DESTINATION in [normalize_address(address) for address in message["to_addresses"]]
        if not self._claim_share_scope(message, review_id):
            return dict(operations=ops, sharing="rfc_variant_review_required")
        if message["rfc_message_id"] and not already_recipient:
            for row in self.db.execute("SELECT payload_json FROM reviews WHERE content_hash=?", (message["source_hash"],)):
                known = json.loads(row[0])["message"]
                if known["rfc_message_id"] == message["rfc_message_id"] and DESTINATION in [normalize_address(address) for address in known["to_addresses"]]:
                    already_recipient = True
                    break
        receiver = dict(common, account=DESTINATION, source_review_id=review_id, mirror_marker=MIRROR_MARKER, source_identity=source)
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
            if state == "SENDING" and operation["kind"] == "share":
                original_hash = receipt.get("original_sha256")
                require(type(original_hash) is str and len(original_hash) == 64 and all(c in "0123456789abcdef" for c in original_hash), "source RFC SHA-256 required before sending")
            if state == "VERIFIED":
                self._verify_readback(operation, receipt)
            self._append_receipt(key, state, receipt)
        return self.operation(key)

    def _verify_readback(self, operation, receipt):
        expected = operation["payload"]
        observed = receipt.get("receiver_observation")
        labels = receipt.get("label_observation")
        require(type(observed) is dict and type(labels) is dict, "independent body and label readbacks required")
        require(observed.get("account") == expected["account"] and observed.get("content_hash") == expected["content_hash"], "receiver identity/body mismatch")
        require(type(observed.get("message_id")) is str and bool(observed["message_id"]), "receiver message id missing")
        if operation["kind"] == "source_labels":
            require(observed["message_id"] == expected["message_id"], "source message mismatch")
        else:
            require(expected.get("source_identity") is not None and observed.get("source_identity") == expected["source_identity"], "receiver original identity mismatch")
        if operation["kind"] == "share":
            intent = self.db.execute("SELECT payload_json FROM receipts WHERE operation_id=? AND state='SENDING' ORDER BY id LIMIT 1", (operation["id"],)).fetchone()
            original_hash = json.loads(intent[0]).get("original_sha256") if intent else None
            archive = receipt.get("archive_observation")
            require(type(original_hash) is str and len(original_hash) == 64, "source RFC SHA-256 intent missing")
            require(type(archive) is dict and archive.get("account") == observed["account"] and archive.get("message_id") == observed["message_id"], "receiver archive identity mismatch")
            require(archive.get("original_sha256") == original_hash, "received original RFC bytes mismatch")
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
