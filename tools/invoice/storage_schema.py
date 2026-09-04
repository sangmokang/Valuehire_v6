"""SQLite schema and forward-only local migrations for the Invoice ledger."""
from __future__ import annotations

import sqlite3
from pathlib import Path


SQLITE_SCHEMA = """
pragma foreign_keys = on;
create table if not exists recruitment_fee_agreements (
  id text primary key,
  tenant_id text not null,
  agreement_ref text not null,
  client_key text not null,
  client_name text not null,
  position_key text not null,
  position_name text not null,
  fee_percent text not null,
  effective_from text not null,
  effective_to text,
  source_reference text not null,
  status text not null check (status in ('active','inactive')),
  unique (tenant_id, agreement_ref)
);
create index if not exists recruitment_fee_agreements_lookup_idx
  on recruitment_fee_agreements
  (tenant_id, client_key, position_key, effective_from, effective_to, status);
create table if not exists invoice_fee_mirror_receipts (
  agreement_id text primary key,
  remote_payload_sha256 text not null,
  confirmed_at text not null default current_timestamp,
  foreign key (agreement_id) references recruitment_fee_agreements(id) on delete cascade
);
create table if not exists revenue_invoices (
  id text primary key, tenant_id text not null, document_number text not null,
  issue_date text not null, client_name text not null, position_name text not null,
  candidate_name text not null, start_date text not null, due_date text not null,
  candidate_salary integer not null, commission_rate text not null,
  supply_amount integer not null, vat_amount integer not null,
  fee_agreement_id text not null, placement_set_id text not null,
  invoice_pdf_sha256 text not null, payload_sha256 text not null,
  contract_version text, contract_sha256 text,
  status text not null, unique (tenant_id, document_number),
  foreign key (fee_agreement_id) references recruitment_fee_agreements(id)
);
create table if not exists client_billing_statements (
  id text primary key, tenant_id text not null, statement_no text not null,
  linked_invoice_id text not null, placement_set_id text not null,
  recipient_name text not null, issue_date text not null, due_date text not null,
  line_items text not null, total_amount integer not null,
  pdf_sha256 text not null, payload_sha256 text not null, status text not null,
  contract_version text, contract_sha256 text, delivery_recipient text,
  unique (tenant_id, statement_no),
  foreign key (linked_invoice_id) references revenue_invoices(id) on delete cascade
);
create table if not exists commission_payouts (
  id text primary key, tenant_id text not null, invoice_id text not null,
  payee_role text not null, payee_name text, split_rate text not null,
  gross_amount integer not null, withholding_rate text not null,
  withholding_amount integer not null, net_amount integer not null,
  status text not null, unique (invoice_id, payee_role),
  foreign key (invoice_id) references revenue_invoices(id) on delete cascade
);
create table if not exists invoice_settlement_details (
  id text primary key, tenant_id text not null, invoice_id text not null unique,
  settlement_number text not null, placement_set_id text not null,
  guarantee_months integer not null, rps_status text not null,
  rps_advance_krw integer, rps_bearer text, settlement_pdf_sha256 text not null,
  payload_sha256 text not null, source_payload text not null,
  unique (tenant_id, settlement_number),
  foreign key (invoice_id) references revenue_invoices(id) on delete cascade
);
create table if not exists invoice_delivery_receipts (
  id text primary key, tenant_id text not null, statement_id text not null unique,
  document_number text not null, recipient text not null, subject text not null,
  gmail_message_id text not null unique, sent_at text not null,
  attachment_sha256 text not null, payload_sha256 text not null,
  contract_version text, contract_sha256 text,
  readback_confirmed integer not null check (readback_confirmed = 1),
  foreign key (statement_id) references client_billing_statements(id) on delete cascade,
  unique (tenant_id, document_number)
);
create table if not exists invoice_sync_outbox (
  id text primary key, operation text not null, aggregate_key text not null,
  payload_sha256 text not null, payload text not null,
  priority integer not null default 100,
  status text not null check (status in ('pending','sent','failed')),
  attempt_count integer not null default 0, last_error text,
  created_at text not null default current_timestamp, sent_at text,
  remote_result text,
  unique (operation, aggregate_key, payload_sha256)
);
create index if not exists invoice_sync_outbox_pending_idx
  on invoice_sync_outbox (status, priority, created_at, id);
"""


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"pragma table_info({table})")}


def _add_column(
    connection: sqlite3.Connection, table: str, column: str, definition: str
) -> None:
    if column not in _columns(connection, table):
        connection.execute(f"alter table {table} add column {column} {definition}")


def connect_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SQLITE_SCHEMA)
    with connection:
        _add_column(connection, "revenue_invoices", "contract_version", "text")
        _add_column(connection, "revenue_invoices", "contract_sha256", "text")
        _add_column(connection, "client_billing_statements", "contract_version", "text")
        _add_column(connection, "client_billing_statements", "contract_sha256", "text")
        _add_column(connection, "client_billing_statements", "delivery_recipient", "text")
        _add_column(
            connection, "invoice_sync_outbox", "priority", "integer not null default 100"
        )
        _add_column(connection, "invoice_sync_outbox", "remote_result", "text")
        _add_column(connection, "invoice_delivery_receipts", "contract_version", "text")
        _add_column(connection, "invoice_delivery_receipts", "contract_sha256", "text")
    return connection
