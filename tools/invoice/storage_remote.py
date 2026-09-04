"""Supabase transport and operation-specific response validation."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from storage_common import load_storage_contract, normalize, tenant_id


class RemoteError(Exception):
    """Raised when Supabase cannot prove the requested operation succeeded."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _credentials() -> tuple[str, str]:
    url = (
        os.environ.get("SUPABASE_URL")
        or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        or ""
    ).rstrip("/")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_SECRET_KEY")
        or ""
    )
    if not url or not key:
        raise RemoteError("Supabase URL and service-role key are required")
    return url, key


def _request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    prefer: str | None = None,
) -> Any:
    url, key = _credentials()
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    data = None
    if payload is not None:
        data = _canonical(payload).encode()
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    request = urllib.request.Request(
        f"{url}/rest/v1/{path}", data=data, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:500]
        raise RemoteError(f"Supabase HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RemoteError(f"Supabase network error: {error.reason}") from error
    try:
        return json.loads(raw) if raw else None
    except json.JSONDecodeError as error:
        raise RemoteError("Supabase returned invalid JSON") from error


def query_fee_agreements(
    tenant_id: str, client_key: str, position_key: str, on_date: str
) -> Any:
    query = urllib.parse.urlencode(
        [
            ("tenant_id", f"eq.{tenant_id}"),
            ("client_key", f"eq.{client_key}"),
            ("position_key", f"eq.{position_key}"),
            ("status", "eq.active"),
            ("effective_from", f"lte.{on_date}"),
            ("or", f"(effective_to.is.null,effective_to.gte.{on_date})"),
            (
                "select",
                "id,tenant_id,agreement_ref,client_key,client_name,position_key,"
                "position_name,fee_rate,effective_from,effective_to,source_reference,status",
            ),
        ]
    )
    table = load_storage_contract()["supabase"]["tables"]["fee_agreements"]
    return _request("GET", f"{table}?{query}")


def verify_fee_authority(
    company: str,
    position: str,
    on_date: date,
    fee_percent: Decimal,
    agreement_ref: str,
) -> dict[str, Any]:
    matches = query_fee_agreements(
        tenant_id(), normalize(company), normalize(position), on_date.isoformat()
    )
    if not isinstance(matches, list):
        raise RemoteError("FEE_AGREEMENT_REMOTE_INVALID")
    if not matches:
        raise RemoteError("FEE_AGREEMENT_NOT_FOUND")
    if len(matches) != 1:
        raise RemoteError("FEE_AGREEMENT_CONFLICT")
    row = matches[0]
    required = {
        "id", "tenant_id", "agreement_ref", "client_key", "client_name",
        "position_key", "position_name", "fee_rate", "effective_from",
        "effective_to", "source_reference", "status",
    }
    if not isinstance(row, dict) or set(row) != required:
        raise RemoteError("FEE_AGREEMENT_REMOTE_INVALID")
    _uuid_text(row.get("id"), "agreement id")
    try:
        rate = Decimal(str(row.get("fee_rate")))
        effective_from = date.fromisoformat(str(row.get("effective_from")))
        effective_to = (
            None if row.get("effective_to") is None
            else date.fromisoformat(str(row["effective_to"]))
        )
    except (InvalidOperation, ValueError) as error:
        raise RemoteError("FEE_AGREEMENT_REMOTE_INVALID") from error
    if (
        row.get("tenant_id") != tenant_id()
        or row.get("agreement_ref") != agreement_ref
        or row.get("client_key") != normalize(company)
        or row.get("position_key") != normalize(position)
        or normalize(str(row.get("client_name", ""))) != normalize(company)
        or normalize(str(row.get("position_name", ""))) != normalize(position)
        or row.get("status") != "active"
        or rate != fee_percent / 100
        or effective_from > on_date
        or (effective_to is not None and effective_to < on_date)
    ):
        raise RemoteError("FEE_AGREEMENT_MISMATCH")
    return row


def remote_request(operation: str, payload: dict[str, Any]) -> Any:
    storage = load_storage_contract()["supabase"]
    if operation == "store_invoice_placement_set":
        return _request(
            "POST",
            f"rpc/{storage['rpcs']['store_document_set']}",
            payload={"p_payload": payload},
            prefer="return=representation",
        )
    if operation == "upsert_fee_agreement":
        table = storage["tables"]["fee_agreements"]
        return _request(
            "POST",
            f"{table}?on_conflict=tenant_id,agreement_ref",
            payload=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
    if operation == "record_invoice_delivery":
        return _request(
            "POST",
            f"rpc/{storage['rpcs']['record_delivery']}",
            payload={"p_payload": payload},
            prefer="return=representation",
        )
    raise RemoteError(f"unsupported outbox operation: {operation}")


def _uuid_text(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise RemoteError(f"REMOTE_CONFIRMATION_ERROR: {label} is missing")
    try:
        uuid.UUID(value)
    except ValueError as error:
        raise RemoteError(f"REMOTE_CONFIRMATION_ERROR: {label} is invalid") from error
    return value


def _same_decimal(left: Any, right: Any) -> bool:
    try:
        return Decimal(str(left)) == Decimal(str(right))
    except InvalidOperation:
        return False


def _same_instant(left: Any, right: Any) -> bool:
    try:
        return datetime.fromisoformat(str(left).replace("Z", "+00:00")) == datetime.fromisoformat(
            str(right).replace("Z", "+00:00")
        )
    except ValueError:
        return False


def validate_remote_response(
    operation: str, payload: dict[str, Any], response: Any
) -> dict[str, Any]:
    required = set(
        load_storage_contract()["supabase"]["remote_success"].get(operation, [])
    )
    if not required:
        raise RemoteError(f"unsupported outbox operation: {operation}")
    if operation == "upsert_fee_agreement":
        if isinstance(response, list) and len(response) == 1:
            result = response[0]
        elif isinstance(response, dict):
            result = response
        else:
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: agreement response is empty")
        if not isinstance(result, dict):
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: agreement response is invalid")
        if not required.issubset(result):
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: agreement fields are missing")
        _uuid_text(result.get("id"), "agreement id")
        exact_fields = required - {"id", "fee_rate"}
        if any(result.get(field) != payload.get(field) for field in exact_fields) or not (
            _same_decimal(result.get("fee_rate"), payload.get("fee_rate"))
        ):
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: agreement identity mismatch")
        return result
    if operation == "store_invoice_placement_set":
        if not isinstance(response, dict) or response.get("status") not in {
            "stored",
            "idempotent",
        }:
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: invoice response is invalid")
        if not required.issubset(response):
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: invoice fields are missing")
        for field in ("invoice_id", "placement_set_id", "fee_agreement_id"):
            _uuid_text(response.get(field), field)
        invoice = payload.get("invoice") or {}
        settlement = payload.get("settlement")
        expected = {
            "tenant_id": payload.get("tenant_id"),
            "document_number": invoice.get("invoice_number"),
            "fee_agreement_ref": invoice.get("fee_agreement_ref"),
            "invoice_pdf_sha256": invoice.get("pdf_sha256"),
            "settlement_number": settlement.get("settlement_number") if settlement else None,
            "settlement_pdf_sha256": settlement.get("pdf_sha256") if settlement else None,
            "contract_version": payload.get("contract_version"),
            "contract_sha256": payload.get("contract_sha256"),
            "payload_sha256": payload.get("payload_sha256"),
        }
        if any(response.get(field) != value for field, value in expected.items()):
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: invoice identity mismatch")
        return response
    if operation == "record_invoice_delivery":
        if not isinstance(response, dict) or response.get("status") not in {
            "stored",
            "idempotent",
        }:
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: delivery response is invalid")
        if not required.issubset(response):
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: delivery fields are missing")
        for field in ("statement_id", "delivery_receipt_id"):
            _uuid_text(response.get(field), field)
        exact_fields = {
            "tenant_id", "document_number", "recipient", "subject",
            "gmail_message_id", "attachment_sha256", "contract_version",
            "contract_sha256", "payload_sha256",
        }
        if any(response.get(field) != payload.get(field) for field in exact_fields) or not (
            _same_instant(response.get("sent_at"), payload.get("sent_at"))
        ):
            raise RemoteError("REMOTE_CONFIRMATION_ERROR: delivery identity mismatch")
        return response
    raise RemoteError(f"unsupported outbox operation: {operation}")
