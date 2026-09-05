from __future__ import annotations

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


class InvoiceLedgerTest(unittest.TestCase):
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

    def test_resolves_exact_customer_position_and_never_defaults(self) -> None:
        self.assertEqual(ledger.register_agreement(self.connection, self.agreement()), "stored")
        row = ledger.resolve_fee(
            self.connection, "  가상회사  ", "ai ENGINEER", ledger.date(2026, 9, 1)
        )
        self.assertEqual(row["fee_percent"], "20")
        self.assertEqual(row["agreement_ref"], "TEST-CLIENT-AI-2026")
        with self.assertRaisesRegex(ledger.StorageError, "FEE_AGREEMENT_NOT_FOUND"):
            ledger.resolve_fee(
                self.connection, "가상회사", "전장 엔지니어", ledger.date(2026, 9, 1)
            )

    def test_rejects_overlapping_agreement_and_conflicting_retry(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        self.assertEqual(ledger.register_agreement(self.connection, self.agreement()), "idempotent")
        with self.assertRaisesRegex(ledger.StorageError, "IDEMPOTENCY_CONFLICT"):
            ledger.register_agreement(self.connection, self.agreement(fee_percent="25"))
        with self.assertRaisesRegex(ledger.StorageError, "FEE_AGREEMENT_CONFLICT"):
            ledger.register_agreement(
                self.connection,
                self.agreement(
                    agreement_ref="TEST-OVERLAP", effective_from="2026-06-01"
                ),
            )

    def test_stores_invoice_and_settlement_atomically_with_outbox(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        invoice_files, settlement_files = self._write_document_files(
            settlement=self.settlement()
        )
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            self.assertEqual(
                ledger.store_document_set(self.connection, invoice_files, settlement_files),
                "stored",
            )
        expected = {
            "revenue_invoices": 1,
            "client_billing_statements": 1,
            "commission_payouts": 3,
            "invoice_settlement_details": 1,
            "invoice_sync_outbox": 2,
        }
        for table, count in expected.items():
            with self.subTest(table=table):
                actual = self.connection.execute(f"select count(*) from {table}").fetchone()[0]
                self.assertEqual(actual, count)
        payout_sum = self.connection.execute(
            "select sum(gross_amount) from commission_payouts"
        ).fetchone()[0]
        self.assertEqual(payout_sum, 12_000_000)
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            self.assertEqual(
                ledger.store_document_set(self.connection, invoice_files, settlement_files),
                "idempotent",
            )

    def test_rejects_document_pair_and_metadata_mismatch_before_write(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        invoice_files, settlement_files = self._write_document_files(
            settlement=self.settlement(candidate_name="다른 사람")
        )
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ), self.assertRaisesRegex(ledger.StorageError, "DOCUMENT_PAIR_MISMATCH"):
            ledger.store_document_set(self.connection, invoice_files, settlement_files)
        self.assertEqual(
            self.connection.execute("select count(*) from revenue_invoices").fetchone()[0], 0
        )
        invoice_files, _ = self._write_document_files()
        metadata = json.loads(invoice_files[2].read_text())
        metadata["requested_fee_krw"] = 1
        invoice_files[2].write_text(json.dumps(metadata), encoding="utf-8")
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ), self.assertRaisesRegex(ledger.StorageError, "metadata"):
            ledger.store_document_set(self.connection, invoice_files, None)

    def test_sync_marks_only_confirmed_remote_success(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        payload = json.loads(self.connection.execute(
            "select payload from invoice_sync_outbox"
        ).fetchone()[0])
        response = self.remote_confirmation("upsert_fee_agreement", payload)
        with mock.patch.object(ledger, "_remote_request", return_value=response):
            sent, failed = ledger.sync_pending(self.connection, 20)
        self.assertEqual((sent, failed), (1, 0))
        row = self.connection.execute(
            "select status,attempt_count,last_error from invoice_sync_outbox"
        ).fetchone()
        self.assertEqual((row["status"], row["attempt_count"], row["last_error"]), ("sent", 1, None))

        second = self.agreement(
            agreement_ref="TEST-CLIENT-EE-2026", position="전장 엔지니어"
        )
        ledger.register_agreement(self.connection, second)
        with mock.patch.object(
            ledger, "_remote_request", side_effect=ledger.StorageError("network down")
        ):
            sent, failed = ledger.sync_pending(self.connection, 20)
        self.assertEqual((sent, failed), (0, 1))
        status = self.connection.execute(
            "select status from invoice_sync_outbox where aggregate_key='TEST-CLIENT-EE-2026'"
        ).fetchone()[0]
        self.assertEqual(status, "failed")

    def test_empty_or_mismatched_remote_confirmation_is_failure(self) -> None:
        invalid_responses = (
            None,
            [],
            {},
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "agreement_ref": "WRONG",
            },
        )
        for index, response in enumerate(invalid_responses):
            with self.subTest(response=response):
                agreement = self.agreement(
                    agreement_ref=f"TEST-REMOTE-{index}",
                    position=f"Position {index}",
                )
                ledger.register_agreement(self.connection, agreement)
                with mock.patch.object(ledger, "_remote_request", return_value=response):
                    sent, failed = ledger.sync_pending(self.connection, 1)
                self.assertEqual((sent, failed), (0, 1))
                row = self.connection.execute(
                    "select status,last_error from invoice_sync_outbox "
                    "where aggregate_key=?",
                    (agreement["agreement_ref"],),
                ).fetchone()
                self.assertEqual(row["status"], "failed")
                self.assertIn("REMOTE_CONFIRMATION_ERROR", row["last_error"])
                with self.connection:
                    self.connection.execute(
                        "delete from invoice_sync_outbox where aggregate_key=?",
                        (agreement["agreement_ref"],),
                    )

    def test_remote_fee_is_authoritative_and_mirrored(self) -> None:
        ledger.register_agreement(
            self.connection,
            self.agreement(
                agreement_ref="STALE-LOCAL",
                fee_percent="15",
                source_reference="stale local mirror",
            ),
        )
        remote = self.remote_agreement(
            agreement_ref="REMOTE-CURRENT",
            fee_rate="0.2",
            source_reference="Supabase current agreement",
        )
        with mock.patch.object(
            ledger.storage_remote, "query_fee_agreements", return_value=[remote]
        ):
            row, source = ledger.resolve_fee_authoritative(
                self.connection, "가상회사", "AI Engineer", ledger.date(2026, 9, 1)
            )
        self.assertEqual((row["agreement_ref"], row["fee_percent"], source), (
            "REMOTE-CURRENT", "20", "SUPABASE"
        ))
        stale = self.connection.execute(
            "select status from recruitment_fee_agreements where agreement_ref='STALE-LOCAL'"
        ).fetchone()[0]
        self.assertEqual(stale, "inactive")

    def test_default_remote_resolution_fails_closed_without_credentials(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(
            ledger.StorageError, "service-role key"
        ):
            ledger.resolve_fee_authoritative(
                self.connection, "가상회사", "AI Engineer", ledger.date(2026, 9, 1)
            )

    def test_ambiguous_supabase_key_is_not_accepted_as_service_role(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_KEY": "anon"},
            clear=True,
        ), self.assertRaisesRegex(ledger.storage_remote.RemoteError, "service-role key"):
            ledger.storage_remote._credentials()

    def test_offline_allows_draft_only_and_never_enqueues_final_rpc(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        final_files, _ = self._write_document_files()
        with self.assertRaisesRegex(ledger.StorageError, "OFFLINE_FINAL_FORBIDDEN"):
            ledger.store_document_set(self.connection, final_files, None, offline=True)
        draft_files, _ = self._write_document_files(self.invoice(draft=True))
        self.assertEqual(
            ledger.store_document_set(
                self.connection, draft_files, None, offline=True
            ),
            "stored",
        )
        document_jobs = self.connection.execute(
            "select count(*) from invoice_sync_outbox "
            "where operation='store_invoice_placement_set'"
        ).fetchone()[0]
        self.assertEqual(document_jobs, 0)

    def test_records_delivery_only_with_matching_gmail_readback(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        invoice_files, _ = self._write_document_files()
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            ledger.store_document_set(self.connection, invoice_files, None)
        statement = self.connection.execute(
            "select * from client_billing_statements"
        ).fetchone()
        delivery = {
            "document_number": "VC-20260901-TEST-001",
            "recipient": "sangmokang@valueconnect.kr",
            "subject": "[밸류커넥트] 토트 채용 수수료 인보이스",
            "gmail_message_id": "gmail-message-001",
            "sent_at": "2026-09-02T09:30:00+09:00",
            "attachment_sha256": statement["pdf_sha256"],
            "readback_confirmed": True,
        }
        self.assertEqual(ledger.record_delivery(self.connection, delivery), "stored")
        self.assertEqual(ledger.record_delivery(self.connection, delivery), "idempotent")
        with mock.patch.object(
            ledger, "business_contract_identity",
            return_value=("rotated", "c" * 64, {}, {}),
        ):
            self.assertEqual(ledger.record_delivery(self.connection, delivery), "idempotent")
        receipt = self.connection.execute(
            "select * from invoice_delivery_receipts"
        ).fetchone()
        version, contract_sha, _, _ = ledger.business_contract_identity()
        self.assertEqual(
            (receipt["contract_version"], receipt["contract_sha256"]),
            (version, contract_sha),
        )
        self.assertEqual(
            self.connection.execute(
                "select status from client_billing_statements"
            ).fetchone()[0],
            "delivery_confirmed_local",
        )
        receipt_payload = json.loads(self.connection.execute(
            "select payload from invoice_sync_outbox where operation='record_invoice_delivery'"
        ).fetchone()[0])
        with self.connection:
            self.connection.execute(
                "update invoice_sync_outbox set status='sent' "
                "where operation<>'record_invoice_delivery'"
            )
        with mock.patch.object(
            ledger,
            "_remote_request",
            return_value=self.remote_confirmation("record_invoice_delivery", receipt_payload),
        ):
            ledger.sync_pending(self.connection, 20)
        self.assertEqual(self.connection.execute(
            "select status from client_billing_statements"
        ).fetchone()[0], "sent")
        with self.assertRaisesRegex(ledger.StorageError, "DELIVERY_NOT_CONFIRMED"):
            ledger.record_delivery(
                self.connection, {**delivery, "readback_confirmed": False}
            )

    def test_outbox_priority_prevents_document_before_agreement(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        invoice_files, _ = self._write_document_files()
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            ledger.store_document_set(self.connection, invoice_files, None)
        operations: list[str] = []

        def confirm(operation: str, payload: dict[str, object]) -> object:
            operations.append(operation)
            return self.remote_confirmation(operation, payload)

        with mock.patch.object(ledger, "_remote_request", side_effect=confirm):
            self.assertEqual(ledger.sync_pending(self.connection, 20), (2, 0))
        self.assertEqual(
            operations, ["upsert_fee_agreement", "store_invoice_placement_set"]
        )

    def test_failed_prerequisite_blocks_dependent_outbox_call(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        invoice_files, _ = self._write_document_files()
        with mock.patch.object(
            ledger.storage_remote, "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            ledger.store_document_set(self.connection, invoice_files, None)
        operations: list[str] = []

        def fail_first(operation: str, _payload: dict[str, object]) -> object:
            operations.append(operation)
            raise ledger.StorageError("network down")

        with mock.patch.object(ledger, "_remote_request", side_effect=fail_first):
            self.assertEqual(ledger.sync_pending(self.connection, 20), (0, 1))
        self.assertEqual(operations, ["upsert_fee_agreement"])
        self.assertEqual(self.connection.execute(
            "select status from invoice_sync_outbox "
            "where operation='store_invoice_placement_set'"
        ).fetchone()[0], "pending")

    def test_missing_document_prerequisite_blocks_delivery_rpc(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        invoice_files, _ = self._write_document_files()
        with mock.patch.object(
            ledger.storage_remote, "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            ledger.store_document_set(self.connection, invoice_files, None)
        delivery = {
            "document_number": self.invoice()["invoice_number"],
            "recipient": "sangmokang@valueconnect.kr",
            "subject": "invoice",
            "gmail_message_id": "gmail-missing-prerequisite",
            "sent_at": "2026-09-02T10:00:00+09:00",
            "attachment_sha256": hashlib.sha256(
                (self.root / "invoice.pdf").read_bytes()).hexdigest(),
            "readback_confirmed": True,
        }
        ledger.record_delivery(self.connection, delivery)
        with self.connection:
            self.connection.execute(
                "delete from invoice_sync_outbox "
                "where operation='store_invoice_placement_set'"
            )
        operations: list[str] = []
        def confirm(operation: str, payload: dict[str, object]) -> object:
            operations.append(operation)
            return self.remote_confirmation(operation, payload)
        with mock.patch.object(ledger, "_remote_request", side_effect=confirm):
            self.assertEqual(ledger.sync_pending(self.connection, 20), (1, 0))
        self.assertEqual(operations, ["upsert_fee_agreement"])
        self.assertEqual(self.connection.execute(
            "select status from invoice_sync_outbox "
            "where operation='record_invoice_delivery'"
        ).fetchone()[0], "pending")

    def test_remote_fee_receipt_allows_document_without_agreement_outbox(self) -> None:
        invoice_files, _ = self._write_document_files()
        with mock.patch.object(
            ledger.storage_remote, "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            ledger.store_document_set(self.connection, invoice_files, None)
        operations: list[str] = []
        def confirm(operation: str, payload: dict[str, object]) -> object:
            operations.append(operation)
            return self.remote_confirmation(operation, payload)
        with mock.patch.object(ledger, "_remote_request", side_effect=confirm):
            self.assertEqual(ledger.sync_pending(self.connection, 20), (1, 0))
        self.assertEqual(operations, ["store_invoice_placement_set"])

    def test_remote_confirmation_rejects_wrong_aggregate_identity(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        agreement_payload = json.loads(self.connection.execute(
            "select payload from invoice_sync_outbox"
        ).fetchone()[0])
        wrong = self.remote_confirmation(
            "upsert_fee_agreement", agreement_payload, tenant_id="evil"
        )
        with self.assertRaisesRegex(ledger.StorageError, "identity mismatch"):
            ledger._confirmed_remote_result("upsert_fee_agreement", agreement_payload, wrong)

        invoice_files, _ = self._write_document_files()
        with mock.patch.object(
            ledger.storage_remote, "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            document_payload, *_ = ledger.build_document_payload(
                self.connection, invoice_files, None
            )
        wrong_document = self.remote_confirmation(
            "store_invoice_placement_set", document_payload,
            document_number="VC-WRONG",
        )
        with self.assertRaisesRegex(ledger.StorageError, "identity mismatch"):
            ledger._confirmed_remote_result(
                "store_invoice_placement_set", document_payload, wrong_document
            )

    def test_storage_contract_keeps_remote_and_local_states_distinct(self) -> None:
        contract = ledger.load_storage_contract()
        self.assertEqual(contract["authority"]["operational_source"], "SUPABASE")
        self.assertEqual(contract["authority"]["local_mirror"], "SQLITE")
        self.assertFalse(contract["authority"]["local_pending_is_remote_success"])


if __name__ == "__main__":
    unittest.main()
