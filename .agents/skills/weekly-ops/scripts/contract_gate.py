"""Fail-closed input, lineage, and publication contracts for weekly operations."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable


CAPABILITY_STATUSES = {"PASS", "FAIL", "NOT_RUN", "STALE"}
REQUIRED_CAPABILITIES = {
    "db_read",
    "gmail_read",
    "clickup_read",
    "notion_read",
    "career_pages_read",
    "jobkorea_outreach_read",
    "saramin_outreach_read",
    "linkedin_outreach_read",
}
REQUIRED_PUBLICATION_TARGETS = {"database", "clickup", "notion", "admin_web", "email"}
RECEIPT_FIELDS = {
    "write_ahead_intent_id",
    "idempotency_key",
    "schema_readback_ref",
    "external_object_id",
    "receipt_id",
    "receipt_persisted_ref",
    "report_snapshot_id",
    "content_hash",
}
SOURCE_STATUSES = {"PASS", "PARTIAL", "FAIL", "NOT_RUN", "STALE"}
DEDUPE_RULE_VERSION = "weekly-dedupe-v1"
ZERO_RESULT_RULE_VERSION = "weekly-zero-result-v1"
ZERO_RESULT_COLLECTIONS = {"positions", "outreach_events"}


def capability_blockers(capabilities: Any, errors: list[str]) -> list[str]:
    if not isinstance(capabilities, list) or not capabilities:
        errors.extend(("CAPABILITIES_MISSING", "CAPABILITY_REQUIRED_MISSING"))
        return [f"{name}:NOT_RUN" for name in sorted(REQUIRED_CAPABILITIES)]
    blockers: list[str] = []
    seen: set[str] = set()
    for capability in capabilities:
        if not isinstance(capability, dict):
            errors.append("CAPABILITY_INVALID")
            continue
        name, status = capability.get("name"), capability.get("status")
        if not isinstance(name, str) or name in seen or status not in CAPABILITY_STATUSES:
            errors.append("CAPABILITY_INVALID")
            continue
        seen.add(name)
        if name in REQUIRED_CAPABILITIES and status != "PASS":
            blockers.append(f"{name}:{status}")
    missing = REQUIRED_CAPABILITIES - seen
    if missing:
        errors.append("CAPABILITY_REQUIRED_MISSING")
        blockers.extend(f"{name}:NOT_RUN" for name in missing)
    return sorted(blockers)


def validate_source_snapshots(
    snapshots: Any,
    parse_datetime: Callable[[str], datetime],
    errors: list[str],
) -> tuple[set[str], set[str], dict[str, set[str]], list[str]]:
    if not isinstance(snapshots, list) or not snapshots:
        errors.append("SOURCE_SNAPSHOTS_MISSING")
        return set(), set(), {}, []
    snapshot_ids: set[str] = set()
    evidence_refs: set[str] = set()
    snapshot_evidence_refs: dict[str, set[str]] = {}
    blockers: list[str] = []
    required = {
        "snapshot_id",
        "source_system",
        "source_uri_ref",
        "fetched_at",
        "status",
        "content_hash",
        "evidence_refs",
    }
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or not required.issubset(snapshot):
            errors.append("SOURCE_SNAPSHOT_INVALID")
            continue
        snapshot_id = snapshot["snapshot_id"]
        refs = snapshot["evidence_refs"]
        valid = (
            isinstance(snapshot_id, str)
            and bool(snapshot_id)
            and snapshot_id not in snapshot_ids
            and isinstance(snapshot["source_system"], str)
            and bool(snapshot["source_system"])
            and isinstance(snapshot["source_uri_ref"], str)
            and bool(snapshot["source_uri_ref"])
            and snapshot["status"] in SOURCE_STATUSES
            and isinstance(snapshot["content_hash"], str)
            and bool(re.fullmatch(r"[0-9a-f]{64}", snapshot["content_hash"]))
            and isinstance(refs, list)
            and bool(refs)
            and all(isinstance(ref, str) and bool(ref) for ref in refs)
        )
        try:
            parse_datetime(snapshot["fetched_at"])
        except (TypeError, ValueError):
            valid = False
        if not valid:
            errors.append("SOURCE_SNAPSHOT_INVALID")
            continue
        snapshot_ids.add(snapshot_id)
        evidence_refs.update(refs)
        snapshot_evidence_refs[snapshot_id] = set(refs)
        if snapshot["status"] != "PASS":
            blockers.append(f"source:{snapshot_id}:{snapshot['status']}")
    return snapshot_ids, evidence_refs, snapshot_evidence_refs, sorted(blockers)


def validate_dedupe_decisions(
    decisions: Any,
    canonical_ids: set[str],
    valid_evidence_refs: set[str],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(decisions, list):
        errors.append("DEDUPE_DECISIONS_MISSING")
        return []
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    required = {
        "decision_id",
        "kept_canonical_id",
        "removed_source_refs",
        "reason",
        "rule_version",
    }
    for decision in decisions:
        if not isinstance(decision, dict) or not required.issubset(decision):
            errors.append("DEDUPE_DECISION_INVALID")
            continue
        decision_id = decision["decision_id"]
        valid = (
            isinstance(decision_id, str)
            and bool(decision_id)
            and decision_id not in seen
            and isinstance(decision["kept_canonical_id"], str)
            and decision["kept_canonical_id"] in canonical_ids
            and isinstance(decision["removed_source_refs"], list)
            and bool(decision["removed_source_refs"])
            and all(ref in valid_evidence_refs for ref in decision["removed_source_refs"])
            and isinstance(decision["reason"], str)
            and bool(decision["reason"])
            and decision["rule_version"] == DEDUPE_RULE_VERSION
        )
        if not valid:
            errors.append("DEDUPE_DECISION_INVALID")
            continue
        seen.add(decision_id)
        validated.append(dict(decision))
    return validated


def validate_zero_result_assertions(
    assertions: Any,
    required_collections: set[str],
    snapshot_evidence_refs: dict[str, set[str]],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(assertions, list):
        if required_collections:
            errors.append("ZERO_RESULT_UNPROVEN")
        return []
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    required = {
        "collection",
        "rule_version",
        "source_snapshot_id",
        "provider_receipt_ref",
        "observed_count",
    }
    for assertion in assertions:
        if not isinstance(assertion, dict) or not required.issubset(assertion):
            errors.append("ZERO_RESULT_ASSERTION_INVALID")
            continue
        collection = assertion["collection"]
        snapshot_id = assertion["source_snapshot_id"]
        receipt_ref = assertion["provider_receipt_ref"]
        valid = (
            collection in ZERO_RESULT_COLLECTIONS
            and collection not in seen
            and assertion["rule_version"] == ZERO_RESULT_RULE_VERSION
            and isinstance(snapshot_id, str)
            and isinstance(receipt_ref, str)
            and receipt_ref in snapshot_evidence_refs.get(snapshot_id, set())
            and type(assertion["observed_count"]) is int
            and assertion["observed_count"] == 0
        )
        if not valid:
            errors.append("ZERO_RESULT_ASSERTION_INVALID")
            continue
        seen.add(collection)
        validated.append(dict(assertion))
    if required_collections - seen:
        errors.append("ZERO_RESULT_UNPROVEN")
    return validated


def publication_receipts(targets: Any) -> list[dict[str, Any]]:
    if not isinstance(targets, list):
        return []
    receipts: list[dict[str, Any]] = []
    for target in targets:
        if not isinstance(target, dict) or not isinstance(target.get("name"), str):
            continue
        receipt = {"name": target["name"], "status": target.get("status", "NOT_RUN")}
        if target.get("status") == "READBACK_VERIFIED":
            receipt.update({field: target.get(field) for field in sorted(RECEIPT_FIELDS)})
        receipts.append(receipt)
    return sorted(receipts, key=lambda item: item["name"])


def publication_state(
    targets: Any, snapshot_id: str, content_hash: str, errors: list[str]
) -> list[str]:
    if not isinstance(targets, list):
        errors.extend(("PUBLICATION_TARGETS_INVALID", "PUBLICATION_REQUIRED_MISSING"))
        return [f"{name}:NOT_RUN" for name in sorted(REQUIRED_PUBLICATION_TARGETS)]
    blockers: list[str] = []
    seen: set[str] = set()
    for target in targets:
        if (
            not isinstance(target, dict)
            or not isinstance(target.get("name"), str)
            or not target["name"]
            or not isinstance(target.get("target_id"), str)
            or not target["target_id"]
        ):
            errors.append("PUBLICATION_TARGET_INVALID")
            continue
        name = target["name"]
        if not isinstance(name, str) or name in seen:
            errors.append("PUBLICATION_TARGET_INVALID")
            continue
        seen.add(name)
        if target.get("status") == "READBACK_VERIFIED":
            if any(not isinstance(target.get(field), str) or not target[field] for field in RECEIPT_FIELDS):
                errors.append("PUBLICATION_RECEIPT_CONTRACT_INVALID")
                continue
            if (
                target["report_snapshot_id"] != snapshot_id
                or target["content_hash"] != content_hash
            ):
                errors.append("PUBLICATION_READBACK_MISMATCH")
        elif name in REQUIRED_PUBLICATION_TARGETS:
            blockers.append(f"{name}:{target.get('status', 'NOT_RUN')}")
    missing = REQUIRED_PUBLICATION_TARGETS - seen
    if missing:
        errors.append("PUBLICATION_REQUIRED_MISSING")
        blockers.extend(f"{name}:NOT_RUN" for name in missing)
    return sorted(blockers)
