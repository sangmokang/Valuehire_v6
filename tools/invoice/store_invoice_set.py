#!/usr/bin/env python3
"""Persist invoice agreements and document sets to SQLite, then sync to Supabase."""
from __future__ import annotations
import argparse
import json
import re
import sqlite3
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
import generate_deduction as settlement_core
import generate_invoice as invoice_core
import storage_agreements
import storage_remote
from storage_common import (
    StorageError,
    business_contract_identity,
    canonical as _canonical,
    digest_bytes as _digest_bytes,
    file_digest as _file_digest,
    iso_date as _iso_date,
    load_json as _load_json,
    load_storage_contract,
    reject_duplicate_placement,
    seal_payload,
    tenant_id,
)
from storage_schema import connect_db
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "data" / "invoice-ledger.sqlite3"
def register_agreement(connection: sqlite3.Connection, raw: dict[str, Any]) -> str:
    return storage_agreements.register_agreement(connection, raw, _enqueue)


resolve_fee = storage_agreements.resolve_fee
resolve_fee_authoritative = storage_agreements.resolve_fee_authoritative
def _enqueue(
    connection: sqlite3.Connection, operation: str, aggregate_key: str, payload: dict[str, Any]
) -> str:
    priorities = load_storage_contract()["sqlite"]["outbox_priority"]
    if operation not in priorities:
        raise StorageError(f"unsupported outbox operation: {operation}")
    payload_text = _canonical(payload)
    digest = _digest_bytes(payload_text.encode())
    connection.execute(
        """insert or ignore into invoice_sync_outbox
           (id,operation,aggregate_key,payload_sha256,payload,priority,status)
           values (?,?,?,?,?,?,'pending')""",
        (
            str(uuid.uuid4()), operation, aggregate_key, digest, payload_text,
            priorities[operation],
        ),
    )
    return digest


def _validated_invoice(input_path: Path, pdf_path: Path, metadata_path: Path):
    raw = _load_json(input_path, "invoice input")
    contract = invoice_core.load_contract(invoice_core.DEFAULT_CONTRACT)
    source = invoice_core.validate_input(raw, contract)
    result = invoice_core.calculate_invoice(source, contract)
    metadata = _load_json(metadata_path, "invoice metadata")
    expected = {
        "contract_version": contract["schema_version"],
        "input_sha256": _file_digest(input_path),
        "pdf_sha256": _file_digest(pdf_path),
        "requested_fee_krw": result.requested_fee_krw,
        "total_amount_krw": result.total_amount_krw,
        "due_date": result.due_date.isoformat(),
        "fee_percent": format(source.fee_percent.normalize(), "f"),
        "fee_agreement_ref": source.fee_agreement_ref,
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise StorageError("invoice metadata or PDF does not match the validated input")
    return result, expected


def _validated_settlement(input_path: Path, pdf_path: Path, metadata_path: Path):
    raw = _load_json(input_path, "settlement input")
    contract = settlement_core.load_contract()
    source = settlement_core.validate_input(raw, contract)
    result = settlement_core.calculate_settlement(source, contract)
    metadata = _load_json(metadata_path, "settlement metadata")
    expected = {
        "contract_version": contract["schema_version"],
        "input_sha256": _file_digest(input_path),
        "pdf_sha256": _file_digest(pdf_path),
        "invoice_number": source.invoice_number,
        "invoice_amount_krw": result.invoice_amount_krw,
        "fee_percent": format(source.fee_percent.normalize(), "f"),
        "fee_agreement_ref": source.fee_agreement_ref,
    }
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise StorageError("settlement metadata or PDF does not match the validated input")
    return result, expected


def _pair_matches(invoice: Any, settlement: Any) -> bool:
    left, right = invoice.source, settlement.source
    return (
        right.invoice_number == left.invoice_number
        and right.company_name == left.company_name
        and right.candidate_name == left.candidate_name
        and right.start_date == left.start_date
        and right.position == left.position
        and right.annual_salary_krw == left.annual_salary_krw
        and right.fee_percent == left.fee_percent
        and right.fee_agreement_ref == left.fee_agreement_ref
        and settlement.invoice_amount_krw == invoice.requested_fee_krw
    )


def build_document_payload(
    connection: sqlite3.Connection,
    invoice_files: tuple[Path, Path, Path],
    settlement_files: tuple[Path, Path, Path] | None,
    *,
    offline: bool = False,
) -> tuple[dict[str, Any], Any, Any | None, sqlite3.Row]:
    invoice, invoice_meta = _validated_invoice(*invoice_files)
    agreement, fee_source = resolve_fee_authoritative(
        connection, invoice.source.company_name, invoice.source.position,
        invoice.source.start_date, offline=offline,
    )
    if offline and not invoice.source.draft:
        raise StorageError("OFFLINE_FINAL_FORBIDDEN: offline fee data may create drafts only")
    if agreement["agreement_ref"] != invoice.source.fee_agreement_ref or Decimal(
        agreement["fee_percent"]
    ) != invoice.source.fee_percent:
        raise StorageError("FEE_AGREEMENT_MISMATCH")
    settlement = None
    settlement_meta = None
    if settlement_files:
        settlement, settlement_meta = _validated_settlement(*settlement_files)
        if not _pair_matches(invoice, settlement):
            raise StorageError("DOCUMENT_PAIR_MISMATCH")
    source = invoice.source
    invoice_data = {
        "invoice_number": source.invoice_number,
        "issue_date": source.issue_date.isoformat(),
        "company_name": source.company_name,
        "candidate_name": source.candidate_name,
        "start_date": source.start_date.isoformat(),
        "position": source.position,
        "annual_salary_krw": source.annual_salary_krw,
        "fee_percent": format(source.fee_percent.normalize(), "f"),
        "fee_agreement_ref": source.fee_agreement_ref,
        "invoice_amount_krw": invoice.requested_fee_krw,
        "due_date": invoice.due_date.isoformat(),
        "pdf_sha256": invoice_meta["pdf_sha256"],
        "draft": source.draft,
    }
    settlement_data = None
    if settlement:
        item = settlement.source
        settlement_data = {
            "settlement_number": item.settlement_number,
            "invoice_number": item.invoice_number,
            "issue_date": item.issue_date.isoformat(),
            "company_name": item.company_name,
            "candidate_name": item.candidate_name,
            "start_date": item.start_date.isoformat(),
            "position": item.position,
            "annual_salary_krw": item.annual_salary_krw,
            "fee_percent": format(item.fee_percent.normalize(), "f"),
            "fee_agreement_ref": item.fee_agreement_ref,
            "invoice_amount_krw": settlement.invoice_amount_krw,
            "guarantee_months": item.guarantee_months,
            "account_manager_name": item.account_manager_name,
            "account_manager_percent": format(item.account_manager_percent.normalize(), "f"),
            "coworker_name": item.coworker_name,
            "coworker_percent": format(item.coworker_percent.normalize(), "f"),
            "rps_status": item.rps_status,
            "rps_advance_krw": item.rps_advance_krw,
            "rps_bearer": item.rps_bearer,
            "pdf_sha256": settlement_meta["pdf_sha256"],
            "draft": item.draft,
        }
    version, contract_sha, _, _ = business_contract_identity()
    payload = seal_payload({
        "tenant_id": tenant_id(),
        "contract_version": version,
        "contract_sha256": contract_sha,
        "fee_source": fee_source,
        "invoice": invoice_data,
        "settlement": settlement_data,
    })
    return payload, invoice, settlement, agreement


def store_document_set(
    connection: sqlite3.Connection,
    invoice_files: tuple[Path, Path, Path],
    settlement_files: tuple[Path, Path, Path] | None,
    *,
    offline: bool = False,
) -> str:
    payload, invoice, settlement, agreement = build_document_payload(
        connection, invoice_files, settlement_files, offline=offline
    )
    source = invoice.source
    existing = connection.execute(
        "select payload_sha256 from revenue_invoices where tenant_id=? and document_number=?",
        (tenant_id(), source.invoice_number),
    ).fetchone()
    if existing:
        if existing["payload_sha256"] == payload["payload_sha256"]:
            return "idempotent"
        raise StorageError("IDEMPOTENCY_CONFLICT")
    reject_duplicate_placement(connection, (
        tenant_id(), source.company_name, source.candidate_name,
        source.start_date.isoformat(), source.position, agreement["id"],
        invoice.requested_fee_krw,
    ))
    invoice_id, placement_id = str(uuid.uuid4()), str(uuid.uuid4())
    with connection:
        connection.execute(
            """insert into revenue_invoices (
              id,tenant_id,document_number,issue_date,client_name,position_name,
              candidate_name,start_date,due_date,candidate_salary,commission_rate,
              supply_amount,vat_amount,fee_agreement_id,placement_set_id,
              invoice_pdf_sha256,payload_sha256,contract_version,contract_sha256,status
            ) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                invoice_id, tenant_id(), source.invoice_number, source.issue_date.isoformat(),
                source.company_name, source.position, source.candidate_name,
                source.start_date.isoformat(), invoice.due_date.isoformat(),
                source.annual_salary_krw, format((source.fee_percent / 100).normalize(), "f"),
                invoice.requested_fee_krw, 0, agreement["id"], placement_id,
                payload["invoice"]["pdf_sha256"], payload["payload_sha256"],
                payload["contract_version"], payload["contract_sha256"],
                "draft" if source.draft else "issued",
            ),
        )
        line_items = _canonical([{
            "candidate_name": source.candidate_name, "position": source.position,
            "salary": source.annual_salary_krw,
            "rate_percent": payload["invoice"]["fee_percent"],
            "fee_agreement_ref": source.fee_agreement_ref,
            "amount": invoice.requested_fee_krw,
        }])
        connection.execute(
            """insert into client_billing_statements (
              id,tenant_id,statement_no,linked_invoice_id,placement_set_id,
              recipient_name,issue_date,due_date,line_items,total_amount,
              pdf_sha256,payload_sha256,status,contract_version,contract_sha256,
              delivery_recipient
            ) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()), tenant_id(), source.invoice_number, invoice_id,
                placement_id, source.company_name, source.issue_date.isoformat(),
                invoice.due_date.isoformat(), line_items, invoice.requested_fee_krw,
                payload["invoice"]["pdf_sha256"], payload["payload_sha256"], "draft",
                payload["contract_version"], payload["contract_sha256"],
                business_contract_identity()[2]["delivery"]["default_recipient"],
            ),
        )
        if settlement:
            _store_settlement_rows(connection, invoice_id, placement_id, settlement, payload)
        if not offline:
            _enqueue(
                connection, "store_invoice_placement_set", source.invoice_number, payload
            )
    return "stored"


def _store_settlement_rows(
    connection: sqlite3.Connection, invoice_id: str, placement_id: str,
    result: Any, payload: dict[str, Any],
) -> None:
    source = result.source
    _, _, invoice_contract, settlement_contract = business_contract_identity()
    company_percent = Decimal(settlement_contract["company_share_percent"])
    withholding_rate = Decimal(settlement_contract["withholding_percent"]) / 100
    issuer_name = invoice_contract["issuer"]["company_name"]
    rows = (
        ("project_owner", source.account_manager_name, source.account_manager_percent,
         result.account_manager_gross_krw, result.account_manager_withholding_krw,
         result.account_manager_net_krw),
        ("coworker", source.coworker_name, source.coworker_percent,
         result.coworker_gross_krw, result.coworker_withholding_krw,
         result.coworker_net_krw),
        ("company", issuer_name, company_percent,
         result.company_share_krw, 0, result.company_net_krw),
    )
    for role, name, percent, gross, withholding, net in rows:
        connection.execute(
            "insert into commission_payouts values (?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(uuid.uuid4()), tenant_id(), invoice_id, role, name,
                format((percent / 100).normalize(), "f"), gross,
                "0" if role == "company" else format(withholding_rate.normalize(), "f"),
                withholding, net, "pending",
            ),
        )
    data = payload["settlement"]
    connection.execute(
        """insert into invoice_settlement_details (
          id,tenant_id,invoice_id,settlement_number,placement_set_id,
          guarantee_months,rps_status,rps_advance_krw,rps_bearer,
          settlement_pdf_sha256,payload_sha256,source_payload
        ) values (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            str(uuid.uuid4()), tenant_id(), invoice_id, source.settlement_number,
            placement_id, source.guarantee_months, source.rps_status,
            source.rps_advance_krw, source.rps_bearer, data["pdf_sha256"],
            payload["payload_sha256"], _canonical(data),
        ),
    )


def _delivery_payload(raw: dict[str, Any], statement: sqlite3.Row) -> dict[str, Any]:
    required = {
        "document_number", "recipient", "subject", "gmail_message_id", "sent_at",
        "attachment_sha256", "readback_confirmed",
    }
    if set(raw) != required:
        raise StorageError("delivery fields mismatch")
    for field in ("document_number", "recipient", "subject", "gmail_message_id"):
        if not isinstance(raw[field], str) or not raw[field].strip():
            raise StorageError(f"{field} must be non-empty text")
    if raw["readback_confirmed"] is not True:
        raise StorageError("DELIVERY_NOT_CONFIRMED")
    if not isinstance(raw["attachment_sha256"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", raw["attachment_sha256"]
    ):
        raise StorageError("attachment_sha256 is invalid")
    if not isinstance(raw["sent_at"], str):
        raise StorageError("sent_at must be an ISO timestamp")
    try:
        sent_at = datetime.fromisoformat(raw["sent_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise StorageError("sent_at must be an ISO timestamp") from error
    if sent_at.tzinfo is None:
        raise StorageError("sent_at must include a timezone")
    recipient = statement["delivery_recipient"]
    if not recipient or not statement["contract_version"] or not statement["contract_sha256"]:
        raise StorageError("CONTRACT_ERROR: statement contract snapshot is missing")
    if raw["recipient"].strip().casefold() != recipient.casefold():
        raise StorageError("DELIVERY_RECIPIENT_MISMATCH")
    return seal_payload({
        "tenant_id": tenant_id(),
        "contract_version": statement["contract_version"],
        "contract_sha256": statement["contract_sha256"],
        "document_number": raw["document_number"].strip(),
        "recipient": recipient,
        "subject": raw["subject"].strip(),
        "gmail_message_id": raw["gmail_message_id"].strip(),
        "sent_at": sent_at.isoformat(),
        "attachment_sha256": raw["attachment_sha256"],
        "readback_confirmed": True,
    })


def record_delivery(connection: sqlite3.Connection, raw: dict[str, Any]) -> str:
    if not isinstance(raw, dict) or not isinstance(raw.get("document_number"), str):
        raise StorageError("delivery fields mismatch")
    statement = connection.execute(
        """select * from client_billing_statements
           where tenant_id=? and statement_no=?""",
        (tenant_id(), raw["document_number"].strip()),
    ).fetchone()
    if statement is None:
        raise StorageError("DELIVERY_DOCUMENT_NOT_FOUND")
    payload = _delivery_payload(raw, statement)
    if statement["pdf_sha256"] != payload["attachment_sha256"]:
        raise StorageError("DELIVERY_ATTACHMENT_MISMATCH")
    digest = payload["payload_sha256"]
    existing = connection.execute(
        "select payload_sha256 from invoice_delivery_receipts where statement_id=?",
        (statement["id"],),
    ).fetchone()
    if existing:
        if existing["payload_sha256"] != digest:
            raise StorageError("IDEMPOTENCY_CONFLICT")
        return "idempotent"
    with connection:
        connection.execute(
            """insert into invoice_delivery_receipts (
              id,tenant_id,statement_id,document_number,recipient,subject,
              gmail_message_id,sent_at,attachment_sha256,payload_sha256,
              contract_version,contract_sha256,readback_confirmed
            ) values (?,?,?,?,?,?,?,?,?,?,?,?,1)""",
            (
                str(uuid.uuid4()), payload["tenant_id"], statement["id"],
                payload["document_number"], payload["recipient"], payload["subject"],
                payload["gmail_message_id"], payload["sent_at"],
                payload["attachment_sha256"], digest,
                payload["contract_version"], payload["contract_sha256"],
            ),
        )
        connection.execute(
            "update client_billing_statements set status='delivery_confirmed_local' where id=?",
            (statement["id"],),
        )
        _enqueue(
            connection, "record_invoice_delivery", payload["document_number"], payload
        )
    return "stored"


def outbox_counts(
    connection: sqlite3.Connection, operation: str, aggregate_key: str
) -> dict[str, int]:
    counts = {"pending": 0, "sent": 0, "failed": 0}
    for row in connection.execute(
        """select status,count(*) as count from invoice_sync_outbox
           where operation=? and aggregate_key=? group by status""",
        (operation, aggregate_key),
    ):
        counts[row["status"]] = row["count"]
    return counts


def _print_outbox_state(counts: dict[str, int]) -> None:
    print(f"SUPABASE_PENDING: {counts['pending']}")
    print(f"SUPABASE_SYNCED: {counts['sent']}")
    print(f"SUPABASE_FAILED: {counts['failed']}")


def _remote_request(operation: str, payload: dict[str, Any]) -> Any:
    try:
        return storage_remote.remote_request(operation, payload)
    except storage_remote.RemoteError as error:
        raise StorageError(str(error)) from error


def _confirmed_remote_result(
    operation: str, payload: dict[str, Any], response: Any
) -> dict[str, Any]:
    try:
        return storage_remote.validate_remote_response(operation, payload, response)
    except storage_remote.RemoteError as error:
        raise StorageError(str(error)) from error


def sync_pending(connection: sqlite3.Connection, limit: int) -> tuple[int, int]:
    rows = connection.execute(
        """select * from invoice_sync_outbox where status in ('pending','failed')
           order by priority, created_at, id limit ?""", (limit,),
    ).fetchall()
    sent = failed = 0
    for row in rows:
        if _has_blocking_prerequisite(connection, row):
            continue
        try:
            payload = json.loads(row["payload"])
            response = _remote_request(row["operation"], payload)
            confirmed = _confirmed_remote_result(row["operation"], payload, response)
        except (StorageError, json.JSONDecodeError) as error:
            failed += 1
            with connection:
                connection.execute(
                    """update invoice_sync_outbox set status='failed',
                       attempt_count=attempt_count+1,last_error=? where id=?""",
                    (str(error)[:500], row["id"]),
                )
        else:
            sent += 1
            with connection:
                connection.execute(
                    """update invoice_sync_outbox set status='sent',
                       attempt_count=attempt_count+1,last_error=null,
                       sent_at=current_timestamp,remote_result=? where id=?""",
                    (_canonical(confirmed), row["id"]),
                )
                if row["operation"] == "record_invoice_delivery":
                    connection.execute(
                        "update client_billing_statements set status='sent' "
                        "where tenant_id=? and statement_no=?",
                        (tenant_id(), row["aggregate_key"]),
                    )
    return sent, failed


def _has_blocking_prerequisite(
    connection: sqlite3.Connection, row: sqlite3.Row
) -> bool:
    payload = json.loads(row["payload"])
    dependency: tuple[str, str] | None = None
    missing_is_blocking = False
    if row["operation"] == "store_invoice_placement_set":
        dependency = ("upsert_fee_agreement", payload["invoice"]["fee_agreement_ref"])
    elif row["operation"] == "record_invoice_delivery":
        dependency = ("store_invoice_placement_set", payload["document_number"])
        missing_is_blocking = True
    if dependency is None:
        return False
    status = connection.execute(
        "select status from invoice_sync_outbox where operation=? and aggregate_key=? "
        "order by created_at desc limit 1",
        dependency,
    ).fetchone()
    if status is None:
        return missing_is_blocking
    return status["status"] != "sent"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init")
    register = commands.add_parser("register-agreement")
    register.add_argument("--input", required=True, type=Path)
    resolve = commands.add_parser("resolve-fee")
    resolve.add_argument("--company", required=True)
    resolve.add_argument("--position", required=True)
    resolve.add_argument("--on", required=True)
    resolve.add_argument("--offline", action="store_true")
    store = commands.add_parser("store")
    for name in ("invoice-input", "invoice-pdf", "invoice-metadata"):
        store.add_argument(f"--{name}", required=True, type=Path)
    for name in ("settlement-input", "settlement-pdf", "settlement-metadata"):
        store.add_argument(f"--{name}", type=Path)
    store.add_argument("--offline", action="store_true")
    delivery = commands.add_parser("record-delivery")
    delivery.add_argument("--input", required=True, type=Path)
    sync = commands.add_parser("sync")
    sync.add_argument("--limit", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        load_storage_contract()
        connection = connect_db(args.db.expanduser().resolve())
        if args.command == "init":
            print("SQLITE_STORED: schema initialized")
        elif args.command == "register-agreement":
            agreement_input = _load_json(args.input, "agreement")
            state = register_agreement(connection, agreement_input)
            print(f"SQLITE_STORED: agreement {state}")
            _print_outbox_state(outbox_counts(
                connection, "upsert_fee_agreement", agreement_input["agreement_ref"].strip()
            ))
        elif args.command == "resolve-fee":
            row, source = resolve_fee_authoritative(
                connection, args.company, args.position, _iso_date(args.on, "on"),
                offline=args.offline,
            )
            print(_canonical({
                "fee_percent": row["fee_percent"],
                "fee_agreement_ref": row["agreement_ref"],
                "fee_source": source,
            }))
        elif args.command == "store":
            settlement_paths = (
                args.settlement_input, args.settlement_pdf, args.settlement_metadata
            )
            if any(settlement_paths) and not all(settlement_paths):
                raise StorageError("all settlement paths must be supplied together")
            state = store_document_set(
                connection,
                (args.invoice_input, args.invoice_pdf, args.invoice_metadata),
                settlement_paths if all(settlement_paths) else None,
                offline=args.offline,
            )
            print(f"SQLITE_STORED: document set {state}")
            invoice_input = _load_json(args.invoice_input, "invoice input")
            print(f"FEE_SOURCE: {'SQLITE_OFFLINE' if args.offline else 'SUPABASE'}")
            _print_outbox_state(outbox_counts(
                connection, "store_invoice_placement_set", invoice_input["invoice_number"]
            ))
        elif args.command == "record-delivery":
            delivery_input = _load_json(args.input, "delivery")
            state = record_delivery(connection, delivery_input)
            print(f"SQLITE_STORED: delivery {state}")
            _print_outbox_state(outbox_counts(
                connection, "record_invoice_delivery", delivery_input["document_number"].strip()
            ))
        else:
            if args.limit < 1 or args.limit > 100:
                raise StorageError("sync limit must be from 1 to 100")
            sent, failed = sync_pending(connection, args.limit)
            print(f"SUPABASE_SYNCED: {sent}")
            print(f"SUPABASE_FAILED: {failed}")
            print(f"VERDICT: {'PASS' if failed == 0 else 'FAIL'}")
            return 0 if failed == 0 else 3
    except (StorageError, invoice_core.InvoiceError, sqlite3.Error, OSError) as error:
        print(f"STORAGE_ERROR: {error}", file=sys.stderr)
        return 2
    finally:
        if "connection" in locals():
            connection.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
