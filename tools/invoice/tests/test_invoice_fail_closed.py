from __future__ import annotations

import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE_DIR = REPO_ROOT / "tools" / "invoice"
TEST_DIR = MODULE_DIR / "tests"
sys.path.insert(0, str(MODULE_DIR))
sys.path.insert(0, str(TEST_DIR))
import generate_deduction  # noqa: E402
import store_invoice_set as ledger  # noqa: E402
import test_store_invoice_set as ledger_fixtures  # noqa: E402


class InvoiceFailClosedTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "ledger.sqlite3"
        self.connection = ledger.connect_db(self.db_path)

    def tearDown(self) -> None:
        self.connection.close()
        self.temp.cleanup()

    def _write_document_files(
        self, invoice: dict[str, object] | None = None
    ) -> tuple[Path, Path, Path]:
        files, _ = ledger_fixtures.InvoiceLedgerTest._write_document_files(
            self, invoice or ledger_fixtures.InvoiceLedgerTest.invoice()
        )
        return files

    def test_document_sync_requires_remote_fee_mirror_receipt(self) -> None:
        invoice_files = self._write_document_files()
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[ledger_fixtures.InvoiceLedgerTest.remote_agreement()],
        ):
            ledger.store_document_set(self.connection, invoice_files, None)
        with self.connection:
            self.connection.execute("delete from invoice_fee_mirror_receipts")

        remote = mock.Mock()
        with mock.patch.object(ledger, "_remote_request", remote):
            self.assertEqual(ledger.sync_pending(self.connection, 20), (0, 0))
        remote.assert_not_called()
        self.assertEqual(
            self.connection.execute(
                "select status from invoice_sync_outbox "
                "where operation='store_invoice_placement_set'"
            ).fetchone()[0],
            "pending",
        )
        stdout = io.StringIO()
        with mock.patch.object(ledger, "_remote_request", remote), mock.patch(
            "sys.stdout", stdout
        ):
            result = ledger.main(["--db", str(self.db_path), "sync"])
        self.assertEqual(result, 3)
        self.assertIn("SUPABASE_PENDING: 1", stdout.getvalue())
        self.assertIn("VERDICT: FAIL", stdout.getvalue())

    def test_corrupt_outbox_payload_is_marked_failed(self) -> None:
        with self.connection:
            self.connection.execute(
                """insert into invoice_sync_outbox
                   (id,operation,aggregate_key,payload_sha256,payload,priority,status)
                   values (?,?,?,?,?,?,'pending')""",
                ("broken", "record_invoice_delivery", "VC-BROKEN", "0" * 64, "{", 30),
            )
        self.assertEqual(ledger.sync_pending(self.connection, 20), (0, 1))
        row = self.connection.execute(
            "select status,last_error,attempt_count from invoice_sync_outbox where id='broken'"
        ).fetchone()
        self.assertEqual((row["status"], row["attempt_count"]), ("failed", 1))
        self.assertIn("Expecting property name", row["last_error"])

    def test_local_delivery_rejects_draft_invoice(self) -> None:
        draft = ledger_fixtures.InvoiceLedgerTest.invoice(draft=True)
        invoice_files = self._write_document_files(draft)
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[ledger_fixtures.InvoiceLedgerTest.remote_agreement()],
        ):
            ledger.store_document_set(self.connection, invoice_files, None)
        delivery = {
            "document_number": draft["invoice_number"],
            "recipient": "sangmokang@valueconnect.kr",
            "subject": "draft must not be sent",
            "gmail_message_id": "gmail-draft-rejected",
            "sent_at": "2026-09-02T10:00:00+09:00",
            "attachment_sha256": hashlib.sha256(invoice_files[1].read_bytes()).hexdigest(),
            "readback_confirmed": True,
        }
        with self.assertRaisesRegex(ledger.StorageError, "DRAFT_DELIVERY_FORBIDDEN"):
            ledger.record_delivery(self.connection, delivery)

    def test_deduction_main_reports_contract_errors_as_contract_errors(self) -> None:
        stderr = io.StringIO()
        with mock.patch.object(
            generate_deduction,
            "generate_files",
            side_effect=generate_deduction.ContractError("contract drift"),
        ), mock.patch("sys.stderr", stderr):
            result = generate_deduction.main(
                ["--input", "input.json", "--output", "output.pdf"]
            )
        self.assertEqual(result, 2)
        self.assertIn("CONTRACT_ERROR: contract drift", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
