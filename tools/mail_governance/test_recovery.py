"""Synthetic zero-effect preflight recovery; no mailbox or network effects."""
import copy
import os
import tempfile
import unittest

from tools.mail_governance.journal import Journal
from tools.mail_governance.recovery import recover_label_preflight
from tools.mail_governance.test_core import fixture


class LabelPreflightRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal = Journal(os.path.join(self.tmp.name, "recovery.sqlite"))
        self.message, self.review = fixture()
        key = self.journal.import_review(self.message, self.review)
        self.operations = self.journal.plan(key)["operations"]
        self.original = next(op for op in self.operations if op["kind"] == "receiver_labels")
        self.journal.receipt(self.original["id"], "SENDING", {})
        self.proof = dict(reason="preflight_failed", provider_mutation_attempts=0,
                          report_sha256s=["1" * 64, "2" * 64])

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    def snapshot(self):
        return {table: [tuple(row) for row in self.journal.db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
                for table in ("reviews", "events", "operations", "receipts")}

    def states(self, operation_id):
        return [row[0] for row in self.journal.db.execute(
            "SELECT state FROM receipts WHERE operation_id=? ORDER BY id", (operation_id,))]

    def test_recovery_appends_failure_and_distinct_label_intent_without_rewriting(self):
        before = self.snapshot()
        successor = recover_label_preflight(self.journal, self.original["id"], self.proof)
        after = self.snapshot()
        self.assertEqual(after["reviews"], before["reviews"])
        self.assertEqual(after["events"], before["events"])
        self.assertEqual(after["operations"][:-1], before["operations"])
        self.assertEqual(after["receipts"][:len(before["receipts"])], before["receipts"])
        self.assertEqual(self.states(self.original["id"]), ["PLANNED", "SENDING", "FAILED"])
        self.assertNotEqual(successor["id"], self.original["id"])
        self.assertEqual(successor["kind"], "receiver_labels")
        self.assertEqual(successor["state"], "PLANNED")
        self.assertEqual(successor["payload"], dict(self.original["payload"], supersedes_operation_id=self.original["id"]))
        self.assertEqual(len([row for row in after["operations"] if row[2] == "share"]), 1)

    def test_identical_proof_is_idempotent_even_after_successor_started(self):
        successor = recover_label_preflight(self.journal, self.original["id"], self.proof)
        self.journal.receipt(successor["id"], "SENDING", {})
        before = self.snapshot()
        repeated = recover_label_preflight(self.journal, self.original["id"], copy.deepcopy(self.proof))
        self.assertEqual(repeated["id"], successor["id"])
        self.assertEqual(repeated["state"], "SENDING")
        self.assertEqual(self.snapshot(), before)
        with self.assertRaises(ValueError):
            self.journal.receipt(self.original["id"], "SENDING", {})

    def test_interruption_after_failure_can_create_only_one_successor(self):
        self.journal.receipt(self.original["id"], "FAILED", self.proof)
        successor = recover_label_preflight(self.journal, self.original["id"], self.proof)
        self.assertEqual(recover_label_preflight(self.journal, self.original["id"], self.proof), successor)
        self.assertEqual(self.states(self.original["id"]), ["PLANNED", "SENDING", "FAILED"])
        self.assertEqual(self.states(successor["id"]), ["PLANNED"])

    def test_conflicting_proof_does_not_create_another_successor(self):
        recover_label_preflight(self.journal, self.original["id"], self.proof)
        before = self.snapshot()
        with self.assertRaises(ValueError):
            recover_label_preflight(self.journal, self.original["id"], dict(self.proof, report_sha256s=["3" * 64]))
        self.assertEqual(self.snapshot(), before)

    def test_wrong_kind_and_unproven_zero_effect_are_rejected_without_append(self):
        for operation in (op for op in self.operations if op["kind"] != "receiver_labels"):
            with self.subTest(kind=operation["kind"]):
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    recover_label_preflight(self.journal, operation["id"], self.proof)
                self.assertEqual(self.snapshot(), before)
        invalid = [dict(self.proof, reason="unknown"), dict(self.proof, provider_mutation_attempts=1),
                   dict(self.proof, provider_mutation_attempts=True), dict(self.proof, report_sha256s=[]),
                   dict(self.proof, report_sha256s=["bad"]), dict(self.proof, report_sha256s=["G" * 64]),
                   dict(self.proof, report_sha256s="1" * 64), {"reason": "preflight_failed"}]
        for proof in invalid:
            with self.subTest(proof=proof):
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    recover_label_preflight(self.journal, self.original["id"], proof)
                self.assertEqual(self.snapshot(), before)

    def test_ambiguous_or_differently_failed_original_cannot_be_recovered(self):
        for state, evidence in (("AMBIGUOUS", {}), ("FAILED", {"reason": "provider_response_lost"})):
            message = dict(self.message, message_id=state, rfc_message_id=f"<{state}@example.test>")
            key = self.journal.import_review(message, self.review)
            original = next(op for op in self.journal.plan(key)["operations"] if op["kind"] == "receiver_labels")
            self.journal.receipt(original["id"], "SENDING", {})
            self.journal.receipt(original["id"], state, evidence)
            before = self.snapshot()
            with self.subTest(state=state), self.assertRaises(ValueError):
                recover_label_preflight(self.journal, original["id"], self.proof)
            self.assertEqual(self.snapshot(), before)

    def test_successor_still_requires_valid_independent_source_and_label_readback(self):
        successor = recover_label_preflight(self.journal, self.original["id"], self.proof)
        observed = dict(account="dev@valueconnect.kr", message_id="existing-dev-copy",
                        content_hash=self.message["source_hash"],
                        source_identity=["rfc", self.message["rfc_message_id"]])
        labels = dict(account=observed["account"], message_id=observed["message_id"], labels=successor["payload"]["labels"])
        receipt = dict(receiver_observation=observed, label_observation=labels)
        with self.assertRaises(ValueError):
            self.journal.receipt(successor["id"], "VERIFIED", receipt)
        self.journal.receipt(successor["id"], "SENDING", {})
        self.journal.receipt(successor["id"], "SENT_UNVERIFIED", {})
        invalid = [dict(receipt, receiver_observation=dict(observed, source_identity=["rfc", "<other@example.test>"])),
                   dict(receipt, label_observation=dict(labels, labels=[]))]
        for bad in invalid:
            with self.assertRaises(ValueError):
                self.journal.receipt(successor["id"], "VERIFIED", bad)
        result = self.journal.receipt(successor["id"], "VERIFIED", receipt)
        self.assertEqual(result["state"], "VERIFIED")
        self.assertEqual(self.journal.operation(self.original["id"])["state"], "FAILED")


if __name__ == "__main__":
    unittest.main()
