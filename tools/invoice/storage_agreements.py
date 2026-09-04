"""Customer and position fee-agreement authority and SQLite mirroring."""
from __future__ import annotations

import sqlite3
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

import storage_remote
from storage_common import (
    StorageError,
    canonical,
    digest_bytes,
    iso_date,
    normalize,
    percent,
    tenant_id,
)


Enqueue = Callable[[sqlite3.Connection, str, str, dict[str, Any]], str]


def agreement_payload(value: dict[str, Any]) -> dict[str, Any]:
    required = {
        "agreement_ref", "company_name", "position", "fee_percent",
        "effective_from", "effective_to", "source_reference", "status",
    }
    unknown = set(value) - required
    missing = required - set(value)
    if unknown or missing:
        raise StorageError(
            f"agreement fields mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    for key in ("agreement_ref", "company_name", "position", "source_reference"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise StorageError(f"{key} must be non-empty text")
    start = iso_date(value["effective_from"], "effective_from")
    end = None if value["effective_to"] is None else iso_date(
        value["effective_to"], "effective_to"
    )
    if end is not None and end < start:
        raise StorageError("effective_to must not precede effective_from")
    if value["status"] not in {"active", "inactive"}:
        raise StorageError("agreement status is invalid")
    fee = percent(value["fee_percent"], "fee_percent")
    return {
        "tenant_id": tenant_id(),
        "agreement_ref": value["agreement_ref"].strip(),
        "client_key": normalize(value["company_name"]),
        "client_name": value["company_name"].strip(),
        "position_key": normalize(value["position"]),
        "position_name": value["position"].strip(),
        "fee_percent": format(fee.normalize(), "f"),
        "fee_rate": format((fee / 100).normalize(), "f"),
        "effective_from": start.isoformat(),
        "effective_to": end.isoformat() if end else None,
        "source_reference": value["source_reference"].strip(),
        "status": value["status"],
    }


def _find(
    connection: sqlite3.Connection, tenant_id: str, agreement_ref: str
) -> sqlite3.Row | None:
    return connection.execute(
        "select * from recruitment_fee_agreements where tenant_id=? and agreement_ref=?",
        (tenant_id, agreement_ref),
    ).fetchone()


def _assert_no_overlap(connection: sqlite3.Connection, agreement: dict[str, Any]) -> None:
    if agreement["status"] != "active":
        return
    overlaps = connection.execute(
        """select count(*) from recruitment_fee_agreements
           where tenant_id=? and client_key=? and position_key=? and status='active'
             and agreement_ref<>?
             and effective_from <= coalesce(?, '9999-12-31')
             and coalesce(effective_to, '9999-12-31') >= ?""",
        (
            agreement["tenant_id"], agreement["client_key"], agreement["position_key"],
            agreement["agreement_ref"], agreement["effective_to"],
            agreement["effective_from"],
        ),
    ).fetchone()[0]
    if overlaps:
        raise StorageError("FEE_AGREEMENT_CONFLICT")


def _insert(
    connection: sqlite3.Connection, agreement: dict[str, Any], agreement_id: str
) -> None:
    comparable = {key: agreement[key] for key in agreement if key != "fee_rate"}
    columns = tuple(comparable)
    connection.execute(
        f"insert into recruitment_fee_agreements (id,{','.join(columns)}) "
        f"values (?,{','.join('?' for _ in columns)})",
        (agreement_id, *(comparable[key] for key in columns)),
    )


def register_agreement(
    connection: sqlite3.Connection, raw: dict[str, Any], enqueue: Enqueue
) -> str:
    agreement = agreement_payload(raw)
    current = _find(connection, agreement["tenant_id"], agreement["agreement_ref"])
    comparable = {key: agreement[key] for key in agreement if key != "fee_rate"}
    if current:
        if {key: current[key] for key in comparable} != comparable:
            raise StorageError("IDEMPOTENCY_CONFLICT: agreement_ref has different data")
        return "idempotent"
    _assert_no_overlap(connection, agreement)
    with connection:
        _insert(connection, agreement, str(uuid.uuid4()))
        remote = {key: agreement[key] for key in agreement if key != "fee_percent"}
        enqueue(connection, "upsert_fee_agreement", agreement["agreement_ref"], remote)
    return "stored"


def resolve_fee(
    connection: sqlite3.Connection, company: str, position: str, on_date: date
) -> sqlite3.Row:
    rows = connection.execute(
        """select * from recruitment_fee_agreements
           where tenant_id=? and client_key=? and position_key=?
             and status='active' and effective_from<=?
             and (effective_to is null or effective_to>=?)""",
        (
            tenant_id(), normalize(company), normalize(position),
            on_date.isoformat(), on_date.isoformat(),
        ),
    ).fetchall()
    if not rows:
        raise StorageError("FEE_AGREEMENT_NOT_FOUND")
    if len(rows) > 1:
        raise StorageError("FEE_AGREEMENT_CONFLICT")
    return rows[0]


def _remote_agreement(raw: Any) -> tuple[dict[str, Any], str]:
    if not isinstance(raw, dict):
        raise StorageError("FEE_AGREEMENT_REMOTE_INVALID")
    required = {
        "id", "tenant_id", "agreement_ref", "client_key", "client_name",
        "position_key", "position_name", "fee_rate", "effective_from",
        "effective_to", "source_reference", "status",
    }
    if set(raw) != required or raw.get("tenant_id") != tenant_id():
        raise StorageError("FEE_AGREEMENT_REMOTE_INVALID")
    try:
        agreement_id = str(uuid.UUID(str(raw["id"])))
        rate = Decimal(str(raw["fee_rate"]))
    except (ValueError, InvalidOperation) as error:
        raise StorageError("FEE_AGREEMENT_REMOTE_INVALID") from error
    if rate <= 0 or rate > 1:
        raise StorageError("FEE_AGREEMENT_REMOTE_INVALID")
    local = agreement_payload({
        "agreement_ref": raw["agreement_ref"],
        "company_name": raw["client_name"],
        "position": raw["position_name"],
        "fee_percent": format((rate * 100).normalize(), "f"),
        "effective_from": raw["effective_from"],
        "effective_to": raw["effective_to"],
        "source_reference": raw["source_reference"],
        "status": raw["status"],
    })
    if local["client_key"] != raw["client_key"] or local["position_key"] != raw["position_key"]:
        raise StorageError("FEE_AGREEMENT_REMOTE_INVALID")
    return local, agreement_id


def _mirror(connection: sqlite3.Connection, raw: dict[str, Any]) -> sqlite3.Row:
    agreement, remote_id = _remote_agreement(raw)
    current = _find(connection, agreement["tenant_id"], agreement["agreement_ref"])
    comparable = {key: agreement[key] for key in agreement if key != "fee_rate"}
    with connection:
        if current:
            if {key: current[key] for key in comparable} != comparable:
                raise StorageError("LOCAL_MIRROR_CONFLICT")
            agreement_id = current["id"]
        else:
            connection.execute(
                """update recruitment_fee_agreements set status='inactive'
                   where tenant_id=? and client_key=? and position_key=? and status='active'
                     and agreement_ref<>?
                     and effective_from<=coalesce(?, '9999-12-31')
                     and coalesce(effective_to, '9999-12-31')>=?""",
                (
                    agreement["tenant_id"], agreement["client_key"],
                    agreement["position_key"], agreement["agreement_ref"],
                    agreement["effective_to"], agreement["effective_from"],
                ),
            )
            _assert_no_overlap(connection, agreement)
            agreement_id = remote_id
            _insert(connection, agreement, agreement_id)
        connection.execute(
            """insert into invoice_fee_mirror_receipts
               (agreement_id,remote_payload_sha256) values (?,?)
               on conflict(agreement_id) do update set
                 remote_payload_sha256=excluded.remote_payload_sha256,
                 confirmed_at=current_timestamp""",
            (agreement_id, digest_bytes(canonical(raw).encode())),
        )
    result = _find(connection, agreement["tenant_id"], agreement["agreement_ref"])
    if result is None:
        raise StorageError("LOCAL_MIRROR_WRITE_FAILED")
    return result


def resolve_fee_authoritative(
    connection: sqlite3.Connection,
    company: str,
    position: str,
    on_date: date,
    *,
    offline: bool = False,
) -> tuple[sqlite3.Row, str]:
    if offline:
        return resolve_fee(connection, company, position, on_date), "SQLITE_OFFLINE"
    try:
        matches = storage_remote.query_fee_agreements(
            tenant_id(), normalize(company), normalize(position), on_date.isoformat()
        )
    except storage_remote.RemoteError as error:
        raise StorageError(str(error)) from error
    if not isinstance(matches, list):
        raise StorageError("FEE_AGREEMENT_REMOTE_INVALID")
    if not matches:
        raise StorageError("FEE_AGREEMENT_NOT_FOUND")
    if len(matches) > 1:
        raise StorageError("FEE_AGREEMENT_CONFLICT")
    return _mirror(connection, matches[0]), "SUPABASE"
