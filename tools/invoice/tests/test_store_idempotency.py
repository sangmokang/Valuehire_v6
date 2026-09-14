"""Business-key idempotency, contract drift, and outbox reporting regressions."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import unittest
from unittest import mock

import storage_common

from invoice_ledger_case import InvoiceLedgerCase, ledger


class PlacementBusinessKeyTest(InvoiceLedgerCase):
    """D-A: the same placement must not be billed twice under a new number."""

    def _store(self, invoice: dict[str, object], settlement: dict[str, object]) -> str:
        invoice_files, settlement_files = self._write_document_files(
            invoice=invoice, settlement=settlement
        )
        with mock.patch.object(
            ledger.storage_remote,
            "query_fee_agreements",
            return_value=[self.remote_agreement()],
        ):
            return ledger.store_document_set(
                self.connection, invoice_files, settlement_files
            )

    def test_same_placement_under_a_new_invoice_number_is_rejected(self) -> None:
        ledger.register_agreement(self.connection, self.agreement())
        self.assertEqual(self._store(self.invoice(), self.settlement()), "stored")
        with self.assertRaisesRegex(ledger.StorageError, "PLACEMENT_DUPLICATE"):
            self._store(
                self.invoice(invoice_number="VC-20260901-TEST-002"),
                self.settlement(
                    settlement_number="VC-SET-20260901-TEST-002",
                    invoice_number="VC-20260901-TEST-002",
                ),
            )
        self.assertEqual(
            self.connection.execute(
                "select count(*) from revenue_invoices"
            ).fetchone()[0],
            1,
        )

    def test_a_different_placement_is_still_accepted(self) -> None:
        """counter-AC: the business key must not block genuinely new placements."""
        ledger.register_agreement(self.connection, self.agreement())
        self.assertEqual(self._store(self.invoice(), self.settlement()), "stored")
        self.assertEqual(
            self._store(
                self.invoice(
                    invoice_number="VC-20260901-TEST-003", candidate_name="김철수"
                ),
                self.settlement(
                    settlement_number="VC-SET-20260901-TEST-003",
                    invoice_number="VC-20260901-TEST-003",
                    candidate_name="김철수",
                ),
            ),
            "stored",
        )

    def test_the_ledger_index_and_not_only_python_enforces_the_key(self) -> None:
        """A code-only guard would leave the mirror inconsistent; the index must exist."""
        indexes = {
            row["name"]
            for row in self.connection.execute("pragma index_list(revenue_invoices)")
        }
        self.assertIn("revenue_invoices_placement_uniq", indexes)
        columns = [
            row[2]
            for row in self.connection.execute(
                "pragma index_info(revenue_invoices_placement_uniq)"
            )
        ]
        self.assertEqual(
            columns,
            [
                "tenant_id", "client_name", "candidate_name", "start_date",
                "position_name", "fee_agreement_id", "supply_amount",
            ],
        )


if __name__ == "__main__":
    unittest.main()


class BusinessContractDriftTest(InvoiceLedgerCase):
    """D-D: the drift guard must be locked by a test that does not reuse it."""

    @staticmethod
    def _independent_digest() -> str:
        """Recompute the business contract digest without storage_common's helper.

        assert_contract_snapshot.py calls business_contract_identity(), so a test
        that trusted the same helper would drift together with the code it checks.
        """
        invoice = ledger.invoice_core.load_contract(ledger.invoice_core.DEFAULT_CONTRACT)
        settlement = ledger.settlement_core.load_contract()
        canonical = json.dumps(
            {"invoice": invoice, "settlement": settlement},
            ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    def test_the_committed_contract_sha_survives_independent_recomputation(self) -> None:
        contract = json.loads(
            storage_common.STORAGE_CONTRACT.read_text(encoding="utf-8")
        )
        self.assertEqual(
            contract["business_contract"]["sha256"], self._independent_digest()
        )

    def test_a_drifted_business_contract_is_refused(self) -> None:
        contract = json.loads(
            storage_common.STORAGE_CONTRACT.read_text(encoding="utf-8")
        )
        contract["business_contract"]["sha256"] = "0" * 64
        drifted = self.root / "storage-drifted.json"
        drifted.write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")
        with mock.patch.object(storage_common, "STORAGE_CONTRACT", drifted):
            with self.assertRaisesRegex(ledger.StorageError, "CONTRACT_ERROR"):
                ledger.business_contract_identity()

    def test_a_missing_business_contract_identity_is_refused(self) -> None:
        contract = json.loads(
            storage_common.STORAGE_CONTRACT.read_text(encoding="utf-8")
        )
        contract.pop("business_contract")
        broken = self.root / "storage-no-identity.json"
        broken.write_text(json.dumps(contract, ensure_ascii=False), encoding="utf-8")
        with mock.patch.object(storage_common, "STORAGE_CONTRACT", broken):
            with self.assertRaisesRegex(ledger.StorageError, "business_contract"):
                ledger.business_contract_identity()


class OutboxReportTest(InvoiceLedgerCase):
    """D-E: the printed synchronisation state must come from the ledger, not a constant."""

    def _counts_from_sql(self, key: str) -> dict[str, int]:
        counts = {"pending": 0, "sent": 0, "failed": 0}
        for status, count in self.connection.execute(
            "select status,count(*) from invoice_sync_outbox "
            "where operation='upsert_fee_agreement' and aggregate_key=? group by status",
            (key,),
        ):
            counts[status] = count
        return counts

    def _run_cli(self, database, agreement_file) -> dict[str, int]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = ledger.main([
                "--db", str(database), "register-agreement", "--input", str(agreement_file)
            ])
        self.assertEqual(code, 0)
        printed = {}
        for line in buffer.getvalue().splitlines():
            if line.startswith("SUPABASE_"):
                label, value = line.split(": ")
                printed[label.removeprefix("SUPABASE_").lower()] = int(value)
        return printed

    def test_the_printed_state_tracks_the_real_outbox(self) -> None:
        database = self.root / "cli.sqlite3"
        agreement_file = self.root / "agreement.json"
        agreement_file.write_text(
            json.dumps(self.agreement(), ensure_ascii=False), encoding="utf-8"
        )
        self.connection.close()
        self.connection = ledger.connect_db(database)
        key = "TEST-CLIENT-AI-2026"

        printed = self._run_cli(database, agreement_file)
        self.assertEqual(printed, {"pending": 1, "synced": 0, "failed": 0})
        self.assertEqual(printed["pending"], self._counts_from_sql(key)["pending"])

        with self.connection:
            self.connection.execute(
                "update invoice_sync_outbox set status='failed' where aggregate_key=?", (key,)
            )
        printed = self._run_cli(database, agreement_file)
        actual = self._counts_from_sql(key)
        self.assertEqual(
            printed,
            {"pending": actual["pending"], "synced": actual["sent"], "failed": actual["failed"]},
        )
        self.assertEqual(printed, {"pending": 0, "synced": 0, "failed": 1})
