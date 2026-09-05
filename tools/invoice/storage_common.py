"""Shared validation and contract helpers for Invoice persistence."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
STORAGE_CONTRACT = REPO_ROOT / "contracts" / "invoice" / "storage-v1.json"


class StorageError(Exception):
    """Raised when a ledger or synchronization invariant fails."""


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def seal_payload(value: dict[str, Any]) -> dict[str, Any]:
    if "payload_canonical" in value or "payload_sha256" in value:
        raise StorageError("payload is already sealed")
    canonical_payload = canonical(value)
    return {
        **value,
        "payload_canonical": canonical_payload,
        "payload_sha256": digest_bytes(canonical_payload.encode()),
    }


def file_digest(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StorageError(f"{label} JSON cannot be read: {error}") from error
    if not isinstance(value, dict):
        raise StorageError(f"{label} must contain a JSON object")
    return value


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def percent(value: Any, label: str) -> Decimal:
    if not isinstance(value, str):
        raise StorageError(f"{label} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise StorageError(f"{label} is invalid") from error
    if not parsed.is_finite() or parsed <= 0 or parsed > 100:
        raise StorageError(f"{label} must be greater than 0 and at most 100")
    return parsed


def iso_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise StorageError(f"{label} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise StorageError(f"{label} must be a valid ISO date") from error


def load_storage_contract() -> dict[str, Any]:
    contract = load_json(STORAGE_CONTRACT, "storage contract")
    if contract.get("schema_version") != "1.2":
        raise StorageError("storage contract schema_version must be 1.2")
    authority = contract.get("authority")
    if not isinstance(authority, dict) or authority.get("operational_source") != "SUPABASE":
        raise StorageError("Supabase must remain the operational source")
    if authority.get("local_mirror") != "SQLITE":
        raise StorageError("SQLite must remain the local mirror")
    if authority.get("local_pending_is_remote_success") is not False:
        raise StorageError("local pending must not be reported as remote success")
    if not isinstance(contract.get("tenant_id"), str) or not contract["tenant_id"]:
        raise StorageError("storage contract tenant_id is invalid")
    priorities = contract.get("sqlite", {}).get("outbox_priority")
    successes = contract.get("supabase", {}).get("remote_success")
    operations = {
        "upsert_fee_agreement", "store_invoice_placement_set",
        "record_invoice_delivery",
    }
    if not isinstance(priorities, dict) or set(priorities) != operations:
        raise StorageError("storage contract outbox priorities are invalid")
    if any(not isinstance(value, int) or value < 1 for value in priorities.values()):
        raise StorageError("storage contract outbox priorities are invalid")
    if not isinstance(successes, dict) or set(successes) != operations:
        raise StorageError("storage contract remote success fields are invalid")
    return contract


def tenant_id() -> str:
    return load_storage_contract()["tenant_id"]


def business_contract_identity() -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    import generate_deduction as settlement_core
    import generate_invoice as invoice_core

    storage = load_storage_contract()
    invoice = invoice_core.load_contract(invoice_core.DEFAULT_CONTRACT)
    settlement = settlement_core.load_contract()
    digest = digest_bytes(canonical({"invoice": invoice, "settlement": settlement}).encode())
    identity = storage.get("business_contract")
    if not isinstance(identity, dict):
        raise StorageError("storage contract business_contract is missing")
    version = identity.get("version")
    if not isinstance(version, str) or not version:
        raise StorageError("business contract version is invalid")
    if identity.get("sha256") != digest:
        raise StorageError("CONTRACT_ERROR: business contract SHA-256 drift")
    return version, digest, invoice, settlement
