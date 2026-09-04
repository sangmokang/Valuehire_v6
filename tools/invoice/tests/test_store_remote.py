"""Read-back regressions: a confirmed response is not proof that a row exists."""
from __future__ import annotations

import json
import unittest
from unittest import mock

from invoice_ledger_case import InvoiceLedgerCase, ledger


class RemoteReadbackTest(InvoiceLedgerCase):
    def setUp(self) -> None:
        super().setUp()
        ledger.register_agreement(self.connection, self.agreement())
        self.payload = json.loads(
            self.connection.execute(
                "select payload from invoice_sync_outbox"
            ).fetchone()[0]
        )
        self.response = self.remote_confirmation("upsert_fee_agreement", self.payload)

    def _sync(self, readback) -> tuple[int, int]:
        with mock.patch.object(
            ledger, "_remote_request", return_value=self.response
        ), mock.patch.object(
            ledger.storage_remote, "readback_rows", side_effect=readback
        ):
            return ledger.sync_pending(self.connection, 20)

    def _outbox(self) -> tuple[str, str | None]:
        row = self.connection.execute(
            "select status,last_error from invoice_sync_outbox"
        ).fetchone()
        return row["status"], row["last_error"]

    def test_a_row_that_cannot_be_read_back_is_never_promoted_to_sent(self) -> None:
        self.assertEqual(self._sync(lambda *_: []), (0, 1))
        status, error = self._outbox()
        self.assertEqual(status, "failed")
        self.assertIn("REMOTE_READBACK_MISSING", error or "")

    def test_read_back_failures_are_reported_by_their_own_cause(self) -> None:
        good = self.readback_of(self.response)
        cases = {
            "REMOTE_READBACK_AMBIGUOUS": lambda t, i, c: good(t, i, c) * 2,
            "REMOTE_READBACK_INVALID": lambda *_: {"id": "not-a-list"},
            "REMOTE_READBACK_MISMATCH": lambda t, i, c: [
                {**good(t, i, c)[0], "agreement_ref": "SOMETHING-ELSE"}
            ],
        }
        for expected, readback in cases.items():
            with self.subTest(expected=expected):
                with self.connection:
                    self.connection.execute(
                        "update invoice_sync_outbox set status='pending',last_error=null"
                    )
                self.assertEqual(self._sync(readback), (0, 1))
                status, error = self._outbox()
                self.assertEqual(status, "failed")
                self.assertIn(expected, error or "")

    def test_a_read_back_of_a_different_row_is_not_accepted(self) -> None:
        def other_row(table: str, row_id: str, columns: tuple[str, ...]):
            return [
                {
                    name: (
                        "00000000-0000-4000-8000-0000000000ff"
                        if name == "id" else self.response[name]
                    )
                    for name in columns
                }
            ]

        self.assertEqual(self._sync(other_row), (0, 1))
        status, error = self._outbox()
        self.assertEqual(status, "failed")
        self.assertIn("REMOTE_READBACK_MISMATCH", error or "")

    def test_a_failing_read_back_request_never_promotes_the_row(self) -> None:
        def unreachable(*_: object):
            raise ledger.storage_remote.RemoteError("Supabase network error: down")

        self.assertEqual(self._sync(unreachable), (0, 1))
        self.assertEqual(self._outbox()[0], "failed")

    def test_a_row_that_reads_back_intact_is_promoted(self) -> None:
        """counter-AC: the read-back must not block genuine successes."""
        self.assertEqual(self._sync(self.readback_of(self.response)), (1, 0))
        status, error = self._outbox()
        self.assertEqual((status, error), ("sent", None))

    def test_every_synchronised_operation_has_a_read_back_plan(self) -> None:
        contract = ledger.load_storage_contract()
        self.assertEqual(
            set(ledger.storage_remote.READBACK_PLAN),
            set(contract["sqlite"]["outbox_priority"]),
        )
        tables = contract["supabase"]["tables"]
        for table_key, _, _ in ledger.storage_remote.READBACK_PLAN.values():
            self.assertIn(table_key, tables)


if __name__ == "__main__":
    unittest.main()
