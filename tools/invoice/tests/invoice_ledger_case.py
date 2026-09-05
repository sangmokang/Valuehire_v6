"""Shared fixtures for the Invoice ledger test suites."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_DIR = REPO_ROOT / "tools" / "invoice"
sys.path.insert(0, str(MODULE_DIR))
import store_invoice_set as ledger  # noqa: E402


class InvoiceLedgerCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.connection = ledger.connect_db(self.root / "ledger.sqlite3")

    def tearDown(self) -> None:
        self.connection.close()
        self.temp.cleanup()

    @staticmethod
    def agreement(**overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "agreement_ref": "TEST-CLIENT-AI-2026",
            "company_name": "가상회사",
            "position": "AI Engineer",
            "fee_percent": "20",
            "effective_from": "2026-01-01",
            "effective_to": None,
            "source_reference": "사용자 확정 테스트 계약",
            "status": "active",
        }
        value.update(overrides)
        return value

    @staticmethod
    def invoice(**overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "invoice_number": "VC-20260901-TEST-001",
            "issue_date": "2026-09-01",
            "company_name": "가상회사",
            "candidate_name": "홍길동",
            "start_date": "2026-09-01",
            "position": "AI Engineer",
            "annual_salary_manwon": 6000,
            "fee_percent": "20",
            "fee_agreement_ref": "TEST-CLIENT-AI-2026",
            "draft": False,
        }
        value.update(overrides)
        return value

    @staticmethod
    def settlement(**overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "settlement_number": "VC-SET-20260901-TEST-001",
            "invoice_number": "VC-20260901-TEST-001",
            "fee_agreement_ref": "TEST-CLIENT-AI-2026",
            "issue_date": "2026-09-01",
            "company_name": "가상회사",
            "candidate_name": "홍길동",
            "start_date": "2026-09-01",
            "position": "AI Engineer",
            "annual_salary_manwon": 6000,
            "guarantee_months": 3,
            "fee_percent": "20",
            "account_manager_name": "담당자",
            "account_manager_percent": "45",
            "coworker_name": "코웍자",
            "coworker_percent": "30",
            "rps_status": "deferred",
            "rps_advance_krw": 0,
            "rps_bearer": None,
            "draft": False,
        }
        value.update(overrides)
        return value

    @staticmethod
    def remote_agreement(**overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "id": "00000000-0000-4000-8000-000000000001",
            "tenant_id": "valueconnect",
            "agreement_ref": "TEST-CLIENT-AI-2026",
            "client_key": "가상회사",
            "client_name": "가상회사",
            "position_key": "ai engineer",
            "position_name": "AI Engineer",
            "fee_rate": "0.2",
            "effective_from": "2026-01-01",
            "effective_to": None,
            "source_reference": "사용자 확정 테스트 계약",
            "status": "active",
        }
        value.update(overrides)
        return value

    @staticmethod
    def remote_confirmation(
        operation: str, payload: dict[str, object], **overrides: object
    ) -> dict[str, object]:
        if operation == "upsert_fee_agreement":
            value = {"id": str(uuid.uuid4()), **payload}
        elif operation == "store_invoice_placement_set":
            invoice = payload["invoice"]
            settlement = payload["settlement"]
            value = {
                "status": "stored",
                "invoice_id": str(uuid.uuid4()),
                "placement_set_id": str(uuid.uuid4()),
                "fee_agreement_id": str(uuid.uuid4()),
                "tenant_id": payload["tenant_id"],
                "document_number": invoice["invoice_number"],
                "fee_agreement_ref": invoice["fee_agreement_ref"],
                "invoice_pdf_sha256": invoice["pdf_sha256"],
                "settlement_number": settlement["settlement_number"] if settlement else None,
                "settlement_pdf_sha256": settlement["pdf_sha256"] if settlement else None,
                "contract_version": payload["contract_version"],
                "contract_sha256": payload["contract_sha256"],
                "payload_sha256": payload["payload_sha256"],
            }
        else:
            value = {
                "status": "stored",
                "statement_id": str(uuid.uuid4()),
                "delivery_receipt_id": str(uuid.uuid4()),
                **{key: payload[key] for key in (
                    "tenant_id", "document_number", "recipient", "subject",
                    "gmail_message_id", "sent_at", "attachment_sha256",
                    "contract_version", "contract_sha256", "payload_sha256",
                )},
            }
        value.update(overrides)
        return value

    @contextlib.contextmanager
    def patched_remote(self, **kwargs):
        """Patch the Supabase write and let the independent read-back mirror it.

        The read-back is a separate request in production, so tests must stub it
        separately too — a confirmed response alone no longer means success.
        """
        write = mock.MagicMock(**kwargs)
        stored: dict[str, object] = {}

        def perform(operation: str, payload: dict[str, object]):
            response = write(operation, payload)
            stored.clear()
            if isinstance(response, dict):
                stored.update(response)
            elif isinstance(response, list) and response and isinstance(response[0], dict):
                stored.update(response[0])
            stored.update(self.ledger_columns(payload))
            return response

        def rows(table: str, row_id: str, columns: tuple[str, ...]):
            return [
                {name: (row_id if name == "id" else stored.get(name)) for name in columns}
            ]

        with mock.patch.object(ledger, "_remote_request", side_effect=perform), \
                mock.patch.object(
                    ledger.storage_remote, "readback_rows", side_effect=rows
                ):
            yield

    @staticmethod
    def ledger_columns(payload: dict[str, object]) -> dict[str, object]:
        """Ledger column names for the invoice fields the read-back now compares."""
        invoice = payload.get("invoice")
        if not isinstance(invoice, dict):
            return {}
        return {
            "client_name": invoice.get("company_name"),
            "candidate_name": invoice.get("candidate_name"),
            "start_date": invoice.get("start_date"),
            "position_name": invoice.get("position"),
            "supply_amount": invoice.get("invoice_amount_krw"),
        }

    @staticmethod
    def readback_of(confirmed: dict[str, object]):
        """Mimic Supabase returning the very row the write claims to have stored."""

        def rows(table: str, row_id: str, columns: tuple[str, ...]):
            return [
                {name: (row_id if name == "id" else confirmed[name]) for name in columns}
            ]

        return rows

    def _write_document_files(
        self, invoice: dict[str, object] | None = None,
        settlement: dict[str, object] | None = None,
    ) -> tuple[tuple[Path, Path, Path], tuple[Path, Path, Path] | None]:
        invoice_value = invoice or self.invoice()
        invoice_input = self.root / "invoice.json"
        invoice_pdf = self.root / "invoice.pdf"
        invoice_meta = self.root / "invoice.metadata.json"
        invoice_input.write_text(json.dumps(invoice_value, ensure_ascii=False), encoding="utf-8")
        invoice_pdf.write_bytes(b"%PDF-1.7\ninvoice-test\n%%EOF\n")
        contract = ledger.invoice_core.load_contract(ledger.invoice_core.DEFAULT_CONTRACT)
        source = ledger.invoice_core.validate_input(invoice_value, contract)
        result = ledger.invoice_core.calculate_invoice(source, contract)
        invoice_meta.write_text(json.dumps({
            "contract_version": contract["schema_version"],
            "input_sha256": hashlib.sha256(invoice_input.read_bytes()).hexdigest(),
            "pdf_sha256": hashlib.sha256(invoice_pdf.read_bytes()).hexdigest(),
            "requested_fee_krw": result.requested_fee_krw,
            "total_amount_krw": result.total_amount_krw,
            "due_date": result.due_date.isoformat(),
            "fee_percent": "20",
            "fee_agreement_ref": source.fee_agreement_ref,
        }), encoding="utf-8")
        if settlement is None:
            return (invoice_input, invoice_pdf, invoice_meta), None
        settlement_input = self.root / "settlement.json"
        settlement_pdf = self.root / "settlement.pdf"
        settlement_meta = self.root / "settlement.metadata.json"
        settlement_input.write_text(json.dumps(settlement, ensure_ascii=False), encoding="utf-8")
        settlement_pdf.write_bytes(b"%PDF-1.7\nsettlement-test\n%%EOF\n")
        contract = ledger.settlement_core.load_contract()
        source = ledger.settlement_core.validate_input(settlement, contract)
        result = ledger.settlement_core.calculate_settlement(source, contract)
        settlement_meta.write_text(json.dumps({
            "contract_version": contract["schema_version"],
            "input_sha256": hashlib.sha256(settlement_input.read_bytes()).hexdigest(),
            "pdf_sha256": hashlib.sha256(settlement_pdf.read_bytes()).hexdigest(),
            "invoice_number": source.invoice_number,
            "invoice_amount_krw": result.invoice_amount_krw,
            "fee_percent": "20",
            "fee_agreement_ref": source.fee_agreement_ref,
        }), encoding="utf-8")
        return (
            (invoice_input, invoice_pdf, invoice_meta),
            (settlement_input, settlement_pdf, settlement_meta),
        )
