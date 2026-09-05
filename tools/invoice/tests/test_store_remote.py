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


class PlacementReadbackColumnsTest(InvoiceLedgerCase):
    """V1 반례(2026-09-05): 문서 번호와 hash 만 다시 읽으면, 고객사·입사자·입사일·
    포지션·계약·금액이 뒤바뀐 채 저장된 행도 성공으로 센다."""

    PAYLOAD = {
        "tenant_id": "valueconnect",
        "payload_sha256": "a" * 64,
        "invoice": {
            "invoice_number": "VC-READBACK-001",
            "company_name": "가상회사",
            "candidate_name": "홍길동",
            "start_date": "2026-09-01",
            "position": "AI Engineer",
            "invoice_amount_krw": 12_000_000,
        },
    }
    CONFIRMED = {
        "invoice_id": "00000000-0000-4000-8000-000000000001",
        "placement_set_id": "00000000-0000-4000-8000-000000000002",
        "fee_agreement_id": "00000000-0000-4000-8000-000000000003",
    }

    def _stored_row(self, **overrides: object) -> dict[str, object]:
        row = {
            "id": self.CONFIRMED["invoice_id"],
            "tenant_id": self.PAYLOAD["tenant_id"],
            "document_number": self.PAYLOAD["invoice"]["invoice_number"],
            "placement_set_id": self.CONFIRMED["placement_set_id"],
            "fee_agreement_id": self.CONFIRMED["fee_agreement_id"],
            "payload_sha256": self.PAYLOAD["payload_sha256"],
            **self.ledger_columns(self.PAYLOAD),
        }
        row.update(overrides)
        return row

    def _confirm(self, **overrides: object):
        row = self._stored_row(**overrides)

        def rows(table: str, row_id: str, columns: tuple[str, ...]):
            return [{name: row[name] for name in columns}]

        with mock.patch.object(ledger.storage_remote, "readback_rows", side_effect=rows):
            return ledger.storage_remote.confirm_stored_rows(
                "store_invoice_placement_set", self.PAYLOAD, self.CONFIRMED
            )

    def test_an_intact_placement_row_is_accepted(self) -> None:
        self.assertEqual(
            self._confirm()["document_number"], "VC-READBACK-001"
        )

    def test_a_row_stored_against_another_placement_is_refused(self) -> None:
        tampered = {
            "client_name": "엉뚱한회사",
            "candidate_name": "다른사람",
            "start_date": "2027-01-01",
            "position_name": "Backend Engineer",
            "supply_amount": 999,
            "fee_agreement_id": "00000000-0000-4000-8000-0000000000ff",
        }
        for field, value in tampered.items():
            with self.subTest(field=field):
                with self.assertRaisesRegex(
                    ledger.storage_remote.RemoteError, "REMOTE_READBACK_MISMATCH"
                ):
                    self._confirm(**{field: value})


if __name__ == "__main__":
    unittest.main()
