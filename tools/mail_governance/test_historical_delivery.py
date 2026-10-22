"""Synthetic imported historical receipts; never sends or alters a mailbox."""
import copy
import hashlib
import json
import os
import sqlite3
import tempfile
import unittest

from tools.mail_governance.core import DESTINATION, MIRROR_MARKER, normalize_address
from tools.mail_governance.historical_delivery import (
    delivery_status, resolve_delivery_archive, resolve_delivery_repair,
)
from tools.mail_governance.journal import Journal
from tools.mail_governance.test_core import fixture


class HistoricalDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "history.sqlite")
        self.journal = Journal(self.path)
        self.message, self.review = fixture()

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    def snapshot(self):
        tables = ("reviews", "events", "operations", "receipts", "delivery_resolutions")
        return {table: [tuple(row) for row in self.journal.db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
                for table in tables}

    def legacy_delivery(self, index=0, *, original=None, current_identity=False,
                        sender_message_id=None, receiver_message_id=None, source_account=None):
        if original is None:
            message = dict(self.message, message_id=f"source-{index}", rfc_message_id=f"<{index}@example.test>")
            if source_account is not None:
                message["account"] = source_account
            review_id = self.journal.import_review(message, self.review)
            payload = dict(account=DESTINATION, content_hash=message["source_hash"], labels=["01JD", "06온톨로지"],
                           mirror_marker=MIRROR_MARKER, mode="additive", source_review_id=review_id)
            if current_identity:
                payload["source_identity"] = ["rfc", message["rfc_message_id"]]
            kind = "share"
        else:
            message = self.journal.review(original["review_id"])["message"]
            review_id = original["review_id"]
            payload = dict(original["payload"], prior_operation_id=original["id"],
                           prior_receiver_message_id=f"receiver-{index}", prior_sender_message_id=f"sender-{index}",
                           source_message_id=message["message_id"], failure="original_archive_missing")
            kind = "share_repair"
        operation = self.journal._plan_operation(review_id, kind, f"historical:{kind}:{index}", payload)
        original_sha = hashlib.sha256(message["rfc_message_id"].encode()).hexdigest()
        suffix = "-repair" if original is not None else ""
        # Append an imported pre-upgrade fixture; the current send API must still reject this legacy intent.
        with self.journal.db:
            intent = {"prior_operation_id": original["id"]} if original else {"raw_sha256": original_sha}
            self.journal._append_receipt(operation["id"], "SENDING", intent)
            self.journal._append_receipt(operation["id"], "SENT_UNVERIFIED", dict(
                sender_message_id=sender_message_id or f"sender-{index}{suffix}",
                receiver_message_id=receiver_message_id or f"receiver-{index}{suffix}",
                receiver_account=DESTINATION))
        return self.journal.operation(operation["id"])

    def proof(self, operation):
        message = self.journal.review(operation["review_id"])["message"]
        record = json.loads(self.journal.db.execute(
            "SELECT payload_json FROM receipts WHERE operation_id=? ORDER BY id DESC LIMIT 1", (operation["id"],)).fetchone()[0])
        common = dict(source_identity=["rfc", message["rfc_message_id"]], content_hash=message["source_hash"],
                      original_sha256=hashlib.sha256(message["rfc_message_id"].encode()).hexdigest())
        return dict(sender_message_id=record["sender_message_id"],
                    source_observation=dict(common, account=normalize_address(message["account"]), message_id=message["message_id"]),
                    receiver_observation=dict(common, account=DESTINATION, message_id=record["receiver_message_id"],
                                              mirror_marker=MIRROR_MARKER, operation_id=operation["id"]),
                    label_observation=dict(account=DESTINATION, message_id=record["receiver_message_id"],
                                           labels=operation["payload"]["labels"] + ["EXTRA"]),
                    report_sha256s=["a" * 64])

    def failure_proof(self, operation):
        good = self.proof(operation)
        observed = dict(good["receiver_observation"])
        observed.pop("original_sha256")
        observed["original_archive_preserved"] = False
        return dict(sender_message_id=good["sender_message_id"], receiver_observation=observed,
                    report_sha256s=["b" * 64])

    def test_confirmed_archive_is_separate_immutable_resolution_not_a_rewritten_intent(self):
        original = self.legacy_delivery()
        before = self.snapshot()
        result = resolve_delivery_archive(self.journal, original["id"], self.proof(original))
        self.assertTrue(result["resolved"])
        self.assertEqual(result["outcome"], "ARCHIVE_CONFIRMED_AFTER_DELIVERY")
        self.assertTrue(result["original_archive_preserved"])
        self.assertEqual(result["historical_state"], "SENT_UNVERIFIED")
        for table in ("reviews", "events", "operations", "receipts"):
            self.assertEqual(self.snapshot()[table], before[table])
        self.assertEqual(len(self.snapshot()["delivery_resolutions"]), 1)
        self.assertNotIn("original_sha256", json.loads(before["receipts"][-2][3]))

    def test_same_proof_is_idempotent_and_conflicting_resolution_is_rejected(self):
        original = self.legacy_delivery()
        proof = self.proof(original)
        result = resolve_delivery_archive(self.journal, original["id"], proof)
        before = self.snapshot()
        self.assertEqual(resolve_delivery_archive(self.journal, original["id"], copy.deepcopy(proof)), result)
        changed = dict(proof, report_sha256s=["c" * 64])
        with self.assertRaises(ValueError):
            resolve_delivery_archive(self.journal, original["id"], changed)
        self.assertEqual(self.snapshot(), before)

    def test_each_identity_hash_marker_label_and_recorded_delivery_binding_is_required(self):
        original = self.legacy_delivery()
        good = self.proof(original)
        mutations = [
            ("sender_message_id", None, "other-sender"),
            ("source_observation", "account", "other@example.test"),
            ("source_observation", "message_id", "other-source"),
            ("source_observation", "source_identity", ["rfc", "<other@example.test>"]),
            ("source_observation", "content_hash", "0" * 64),
            ("source_observation", "original_sha256", "0" * 64),
            ("receiver_observation", "account", "other@example.test"),
            ("receiver_observation", "message_id", "other-copy"),
            ("receiver_observation", "source_identity", ["rfc", "<other@example.test>"]),
            ("receiver_observation", "content_hash", "0" * 64),
            ("receiver_observation", "original_sha256", "0" * 64),
            ("receiver_observation", "mirror_marker", "other-marker"),
            ("receiver_observation", "operation_id", "other-operation"),
            ("label_observation", "account", "other@example.test"),
            ("label_observation", "message_id", "other-copy"),
            ("label_observation", "labels", []),
            ("report_sha256s", None, []), ("report_sha256s", None, ["bad"]),
        ]
        for section, field, value in mutations:
            with self.subTest(section=section, field=field):
                proof = copy.deepcopy(good)
                if field is None:
                    proof[section] = value
                else:
                    proof[section][field] = value
                before = self.snapshot()
                with self.assertRaises(ValueError):
                    resolve_delivery_archive(self.journal, original["id"], proof)
                self.assertEqual(self.snapshot(), before)

    def test_resolution_does_not_bypass_current_share_presend_hash_contract(self):
        original = self.legacy_delivery(current_identity=True)
        proof = self.proof(original)
        resolve_delivery_archive(self.journal, original["id"], proof)
        receipt = dict(receiver_observation=proof["receiver_observation"],
                       label_observation=proof["label_observation"],
                       archive_observation=dict(account=DESTINATION,
                                                message_id=proof["receiver_observation"]["message_id"],
                                                original_sha256=proof["receiver_observation"]["original_sha256"]))
        with self.assertRaisesRegex(ValueError, "source RFC SHA-256 intent missing"):
            self.journal.receipt(original["id"], "VERIFIED", receipt)
        self.assertEqual(self.journal.operation(original["id"])["state"], "SENT_UNVERIFIED")

    def test_matching_new_hash_claims_cannot_override_recorded_legacy_source_bytes(self):
        original = self.legacy_delivery()
        proof = self.proof(original)
        proof["source_observation"]["original_sha256"] = "0" * 64
        proof["receiver_observation"]["original_sha256"] = "0" * 64
        before = self.snapshot()
        with self.assertRaises(ValueError):
            resolve_delivery_archive(self.journal, original["id"], proof)
        self.assertEqual(self.snapshot(), before)

    def test_repair_requires_confirmed_archive_and_exact_prior_delivery_links(self):
        original = self.legacy_delivery()
        repair = self.legacy_delivery(original=original)
        self.assertNotEqual(self.proof(original)["sender_message_id"], self.proof(repair)["sender_message_id"])
        self.assertNotEqual(self.proof(original)["receiver_observation"]["message_id"],
                            self.proof(repair)["receiver_observation"]["message_id"])
        before = self.snapshot()
        with self.assertRaises(ValueError):
            resolve_delivery_repair(self.journal, original["id"], repair["id"], self.failure_proof(original))
        self.assertEqual(self.snapshot(), before)
        resolve_delivery_archive(self.journal, repair["id"], self.proof(repair))
        result = resolve_delivery_repair(self.journal, original["id"], repair["id"], self.failure_proof(original))
        self.assertEqual(result["outcome"], "REPAIRED_BY_CONFIRMED_DELIVERY")
        self.assertFalse(result["original_archive_preserved"])
        self.assertEqual(result["repair_operation_id"], repair["id"])
        self.assertEqual(result["historical_state"], "SENT_UNVERIFIED")

    def assert_reused_delivery_ids_rejected(self, *, reuse_sender, reuse_receiver):
        original = self.legacy_delivery()
        original_proof = self.proof(original)
        repair = self.legacy_delivery(
            original=original,
            sender_message_id=original_proof["sender_message_id"] if reuse_sender else None,
            receiver_message_id=original_proof["receiver_observation"]["message_id"] if reuse_receiver else None)
        repair_proof = self.proof(repair)
        self.assertEqual(original_proof["sender_message_id"] == repair_proof["sender_message_id"], reuse_sender)
        self.assertEqual(original_proof["receiver_observation"]["message_id"] ==
                         repair_proof["receiver_observation"]["message_id"], reuse_receiver)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "historical delivery message ID collision|repair must have distinct sender and receiver"):
            resolve_delivery_archive(self.journal, repair["id"], repair_proof)
        self.assertEqual(self.snapshot(), before)

    def test_repair_cannot_reuse_original_sender_message_id(self):
        self.assert_reused_delivery_ids_rejected(reuse_sender=True, reuse_receiver=False)

    def test_repair_cannot_reuse_original_receiver_message_id(self):
        self.assert_reused_delivery_ids_rejected(reuse_sender=False, reuse_receiver=True)

    def test_repair_cannot_reuse_both_original_delivery_message_ids(self):
        self.assert_reused_delivery_ids_rejected(reuse_sender=True, reuse_receiver=True)

    def assert_delivery_collision_rejected(self, operation):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "historical delivery message ID collision"):
            resolve_delivery_archive(self.journal, operation["id"], self.proof(operation))
        self.assertEqual(self.snapshot(), before)

    def test_originals_cannot_share_dev_receiver_even_from_different_sender_accounts(self):
        original = self.legacy_delivery()
        other = self.legacy_delivery(1, source_account="other@valueconnect.kr", receiver_message_id="receiver-0")
        for operation in (original, other):
            with self.subTest(operation=operation["id"]):
                self.assert_delivery_collision_rejected(operation)

    def test_originals_cannot_share_sender_message_id_in_same_normalized_account(self):
        original = self.legacy_delivery()
        other = self.legacy_delivery(1, source_account="Owner <OWNER@VALUECONNECT.KR>", sender_message_id="sender-0")
        for operation in (original, other):
            with self.subTest(operation=operation["id"]):
                self.assert_delivery_collision_rejected(operation)

    def assert_repair_unrelated_collision_rejected(self, field):
        original = self.legacy_delivery()
        other = self.legacy_delivery(1)
        repair = self.legacy_delivery(original=original, **{field: "sender-1" if field == "sender_message_id" else "receiver-1"})
        for operation in (repair, other):
            with self.subTest(operation=operation["id"]):
                self.assert_delivery_collision_rejected(operation)

    def test_repair_cannot_reuse_unrelated_share_sender_message_id(self):
        self.assert_repair_unrelated_collision_rejected("sender_message_id")

    def test_repair_cannot_reuse_unrelated_share_receiver_message_id(self):
        self.assert_repair_unrelated_collision_rejected("receiver_message_id")

    def assert_old_foreign_receipt_collision_rejected(self, field):
        original = self.legacy_delivery()
        other = self.legacy_delivery(1, **{field: "sender-0" if field == "sender_message_id" else "receiver-0"})
        with self.journal.db:
            self.journal._append_receipt(other["id"], "SENT_UNVERIFIED", dict(
                sender_message_id="later-sender", dev_message_id="later-receiver", receiver_account=DESTINATION))
        # Resolve the nonconflicting single-receipt operation: inspecting only
        # the other operation's latest receipt would conceal its older clash.
        self.assert_delivery_collision_rejected(original)

    def test_older_foreign_sender_receipt_cannot_be_hidden_by_latest_result(self):
        self.assert_old_foreign_receipt_collision_rejected("sender_message_id")

    def test_older_foreign_receiver_receipt_cannot_be_hidden_by_latest_result(self):
        self.assert_old_foreign_receipt_collision_rejected("receiver_message_id")

    def test_foreign_legacy_dev_message_id_alias_is_checked_for_collision(self):
        original = self.legacy_delivery()
        other = self.legacy_delivery(1)
        with self.journal.db:
            self.journal._append_receipt(other["id"], "SENT_UNVERIFIED", dict(
                sender_message_id="other-sender", dev_message_id="receiver-0", receiver_account=DESTINATION))
            self.journal._append_receipt(other["id"], "SENT_UNVERIFIED", dict(
                sender_message_id="later-sender", receiver_message_id="later-receiver", receiver_account=DESTINATION))
        self.assert_delivery_collision_rejected(original)

    def assert_conflicting_own_receipts_rejected(self, field):
        original = self.legacy_delivery()
        record = dict(sender_message_id="sender-0", receiver_message_id="receiver-0", receiver_account=DESTINATION)
        record[field] = "conflicting-message-id"
        with self.journal.db:
            self.journal._append_receipt(original["id"], "SENT_UNVERIFIED", record)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "conflicting historical send results"):
            resolve_delivery_archive(self.journal, original["id"], self.proof(original))
        self.assertEqual(self.snapshot(), before)

    def test_own_sender_receipt_contradiction_is_rejected(self):
        self.assert_conflicting_own_receipts_rejected("sender_message_id")

    def test_own_receiver_receipt_contradiction_is_rejected(self):
        self.assert_conflicting_own_receipts_rejected("receiver_message_id")

    def test_sender_message_ids_are_local_to_source_account(self):
        original = self.legacy_delivery()
        other = self.legacy_delivery(1, source_account="Other <OTHER@VALUECONNECT.KR>", sender_message_id="sender-0")
        for operation in (original, other):
            with self.subTest(operation=operation["id"]):
                self.assertTrue(resolve_delivery_archive(self.journal, operation["id"], self.proof(operation))["resolved"])

    def test_repeated_identical_delivery_ids_with_legacy_alias_are_idempotent_observations(self):
        original = self.legacy_delivery()
        proof = self.proof(original)
        with self.journal.db:
            self.journal._append_receipt(original["id"], "SENT_UNVERIFIED", dict(
                sender_message_id="sender-0", dev_message_id="receiver-0", receiver_account="Dev <DEV@VALUECONNECT.KR>"))
        result = resolve_delivery_archive(self.journal, original["id"], proof)
        self.assertTrue(result["resolved"])

    def test_existing_nonarchive_repair_resolution_cannot_confirm_original(self):
        original = self.legacy_delivery()
        repair = self.legacy_delivery(original=original)
        # An imported row can contain a valid archive proof but the wrong outcome.
        # Reject that outcome before considering the independently valid proof.
        with self.journal.db:
            self.journal.db.execute("INSERT INTO delivery_resolutions VALUES(?,?,?,?)", (
                repair["id"], "REPAIRED_BY_CONFIRMED_DELIVERY",
                json.dumps(dict(proof=self.proof(repair))), "2026-10-22T00:00:00+00:00"))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "repair archive must be confirmed first"):
            resolve_delivery_repair(self.journal, original["id"], repair["id"], self.failure_proof(original))
        self.assertEqual(self.snapshot(), before)

    def test_repair_cannot_be_applied_to_a_different_original_or_unproven_failure(self):
        original = self.legacy_delivery()
        other = self.legacy_delivery(1)
        repair = self.legacy_delivery(original=original)
        resolve_delivery_archive(self.journal, repair["id"], self.proof(repair))
        for old, proof in ((other, self.failure_proof(other)),
                           (original, dict(self.failure_proof(original), receiver_observation=dict(
                               self.failure_proof(original)["receiver_observation"], original_archive_preserved=True)))):
            before = self.snapshot()
            with self.assertRaises(ValueError):
                resolve_delivery_repair(self.journal, old["id"], repair["id"], proof)
            self.assertEqual(self.snapshot(), before)

    def test_wrong_kind_and_unknown_resolution_stay_unresolved_without_new_delivery(self):
        key = self.journal.import_review(self.message, self.review)
        source = next(op for op in self.journal.plan(key)["operations"] if op["kind"] == "source_labels")
        status = delivery_status(self.journal, source["id"])
        self.assertFalse(status["resolved"])
        self.assertEqual(status["outcome"], "UNRESOLVED")
        original = self.legacy_delivery()
        before = self.snapshot()
        with self.assertRaises(ValueError):
            resolve_delivery_archive(self.journal, source["id"], self.proof(original))
        self.assertEqual(self.snapshot(), before)

    def test_resolution_survives_reopen_and_rejects_replace_on_fresh_sqlite_connection(self):
        original = self.legacy_delivery()
        result = resolve_delivery_archive(self.journal, original["id"], self.proof(original))
        self.journal.close()
        self.journal = Journal(self.path)
        self.assertEqual(delivery_status(self.journal, original["id"]), result)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            self.assertEqual(connection.execute("PRAGMA recursive_triggers").fetchone()[0], 0)
            row = dict(connection.execute("SELECT * FROM delivery_resolutions").fetchone())
            changed = dict(row, payload_json="{}")
            names, slots = ",".join(changed), ",".join("?" for _ in changed)
            for query, parameters in (("UPDATE delivery_resolutions SET payload_json='{}'", ()),
                                      ("DELETE FROM delivery_resolutions", ()),
                                      (f"INSERT OR REPLACE INTO delivery_resolutions ({names}) VALUES ({slots})", tuple(changed.values()))):
                with self.subTest(query=query), self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(query, parameters)
                connection.rollback()
            self.assertEqual(dict(connection.execute("SELECT * FROM delivery_resolutions").fetchone()), row)
        finally:
            connection.close()

    def test_nine_historical_outcomes_resolve_seven_unique_originals_without_resending(self):
        originals = [self.legacy_delivery(index) for index in range(7)]
        repairs = [self.legacy_delivery(index, original=originals[index]) for index in range(2)]
        before = self.snapshot()
        for operation in originals[2:] + repairs:
            resolve_delivery_archive(self.journal, operation["id"], self.proof(operation))
        for original, repair in zip(originals, repairs):
            resolve_delivery_repair(self.journal, original["id"], repair["id"], self.failure_proof(original))
        statuses = [delivery_status(self.journal, operation["id"]) for operation in originals + repairs]
        self.assertEqual(sum(status["resolved"] for status in statuses), 9)
        self.assertEqual(sum(status["original_archive_preserved"] for status in statuses), 7)
        self.assertEqual(len({operation["review_id"] for operation in originals + repairs}), 7)
        for table in ("reviews", "events", "operations", "receipts"):
            self.assertEqual(self.snapshot()[table], before[table])
        self.assertEqual({status["historical_state"] for status in statuses}, {"SENT_UNVERIFIED"})


if __name__ == "__main__":
    unittest.main()
