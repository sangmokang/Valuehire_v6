"""Normalize a collected mailbox incrementally. Raw MIME remains private."""

import argparse
import json
import sqlite3
from pathlib import Path

from humansearch.admin_ai_search.evidence import load_evidence_contract
from humansearch.admin_ai_search.normalize import PARSER_VERSION, normalize_message, review
from humansearch.admin_ai_search.registry import Registry
from humansearch.admin_ai_search.contact_reports import ingest_report, ingest_gmail_sent
from humansearch.admin_ai_search.normalize import adapt_mime, headers
from humansearch.admin_ai_search.gmail_source import _message_body
from humansearch.admin_ai_search.gmail_subject import non_run_reason
import re

parser = argparse.ArgumentParser()
parser.add_argument("--database", type=Path, required=True)
args = parser.parse_args()
registry = Registry(args.database)
registry.db.execute("CREATE TABLE IF NOT EXISTS normalized_sources (id TEXT PRIMARY KEY, checksum TEXT, document TEXT)")
registry.db.commit()
contract = load_evidence_contract(Path(__file__).parents[2] / "contracts/admin-ai-search/evidence-contract-v1.json")
counts = {"PROCESSED": 0, "EXCLUDED": 0, "FAILED": 0, "REVIEW_REQUIRED": 0, "unchanged": 0}
label_ids: set[str] = set()
original_label_ids: set[str] = set()
for scope, encoded in registry.db.execute("SELECT scope,document FROM collection_checkpoints WHERE scope LIKE '02aisearch%'"):
    found = set(json.loads(encoded)["message_ids"])
    label_ids.update(found)
    if scope == "02aisearch":
        original_label_ids.update(found)
cursor = sqlite3.connect(args.database).execute("SELECT id,checksum,document FROM source_messages ORDER BY id")
for identity, checksum, encoded in cursor:
    old = registry.db.execute("SELECT checksum,document FROM normalized_sources WHERE id=?", (identity,)).fetchone()
    prior = json.loads(old[1]) if old else {}
    previous_label = prior.get("in_ai_search_label", identity in original_label_ids)
    if (old and old[0] == checksum and prior.get("parser_version") == PARSER_VERSION
            and prior.get("processing_status") != "FAILED" and previous_label == (identity in label_ids)):
        counts["unchanged"] += 1
        continue
    raw = json.loads(encoded)
    raw["_in_ai_search_label"] = identity in label_ids
    try:
        if raw.get("collection_error"):
            raise ValueError(raw["collection_error"])
        document = normalize_message(registry, raw, contract)
    except Exception as error:
        metadata = headers(raw)
        document = {"id": identity, "thread_id": raw.get("threadId"), "subject": metadata.get("subject"),
                    "sender": metadata.get("from"), "recipients": metadata.get("to"), "label_ids": raw.get("labelIds", []),
                    "gmail_url": f"https://mail.google.com/mail/u/0/#all/{identity}",
                    "processing_status": "FAILED", "reason": "parser_or_collection_failure",
                    "error_type": type(error).__name__, "original_error": str(error), "parser_version": PARSER_VERSION}
        review(registry, identity, "parser_or_collection_failure", error_type=type(error).__name__)
    document["checksum"] = checksum
    document["in_ai_search_label"] = identity in label_ids
    with registry.db:
        registry.db.execute("INSERT INTO normalized_sources VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET "
                            "checksum=excluded.checksum,document=excluded.document", (identity,checksum,json.dumps(document,ensure_ascii=False)))
    counts[document["processing_status"]] += 1
report_eligible = {row[0] for row in registry.db.execute(
    "SELECT id FROM normalized_sources WHERE json_extract(document,'$.processing_status')='PROCESSED'")}
for encoded, in sqlite3.connect(args.database).execute("SELECT document FROM source_messages"):
    raw = json.loads(encoded)
    subject = headers(raw).get("subject", "")
    if non_run_reason(subject):
        continue
    if not ("SENT" in raw.get("labelIds", []) or raw["id"] in label_ids or raw["id"] in report_eligible
            or re.search(r"컨택|발송|contact", subject, re.IGNORECASE)):
        continue
    try:
        text, _ = _message_body(adapt_mime(raw.get("payload", {})))
    except (ValueError, UnicodeError):
        continue
    if "SENT" in raw.get("labelIds", []):
        try:
            ingest_gmail_sent(registry, raw, contract, text)
        except (ValueError, TypeError):
            review(registry, raw["id"], "gmail_sent_parse_requires_review")
    if "ai-search-contact-report/v1" in text:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        try:
            report = json.loads(match[1] if match else text)
        except json.JSONDecodeError:
            review(registry, raw["id"], "contact_report_json_invalid")
            continue
        if isinstance(report, dict):
            ingest_report(registry, raw["id"], report)
    else:
        totals: dict[str, list[dict[str, object]]] = {}
        for channel, label in (("SARAMIN", "사람인"), ("JOBKOREA", "잡코리아"), ("LINKEDIN", "(?:LinkedIn|링크드인)")):
            matches = re.finditer(label + r".{0,40}?(?<!미)발송\s*(?:성공)?\s*[:：]?\s*(\d+)\s*(?:건|명)", text, re.IGNORECASE)
            found = [{"reported_count": int(match[1]), "source_label": match[0], "status": "REVIEW_REQUIRED"} for match in matches]
            if found:
                totals[channel] = found
        if totals or re.search(r"(?:컨택|발송).*(?:보고|집계|이력)", subject):
            ingest_report(registry, raw["id"], {"text": text, "subject": subject, "totals": totals})
print(json.dumps(counts))
