"""Business-key idempotency, contract drift, and outbox reporting regressions."""
from __future__ import annotations

import unittest
from unittest import mock

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
