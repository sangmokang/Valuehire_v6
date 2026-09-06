from __future__ import annotations

import hashlib
import json
import os
import unittest
from unittest import mock

from invoice_ledger_case import InvoiceLedgerCase, ledger


class InvoiceLedgerTest(InvoiceLedgerCase):
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
        with self.patched_remote( return_value=response):
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
        with self.patched_remote( side_effect=ledger.StorageError("network down")
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
                with self.patched_remote( return_value=response):
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
        with self.patched_remote(
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

        with self.patched_remote( side_effect=confirm):
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

        with self.patched_remote( side_effect=fail_first):
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
        with self.patched_remote( side_effect=confirm):
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
        with self.patched_remote( side_effect=confirm):
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
