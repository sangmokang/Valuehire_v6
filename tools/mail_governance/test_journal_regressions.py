"""Synthetic regressions for sharing identity, immutable rows, and minimal retention."""
import copy
import hashlib
import os
import sqlite3
import tempfile
import unittest

from tools.mail_governance.core import DESTINATION, canonical, classify, content_hash, digest
from tools.mail_governance.journal import Journal
from tools.mail_governance.test_core import fixture


class JournalGuardRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "journal.sqlite")
        self.journal = Journal(self.path)
        self.message, self.review = fixture()

    def tearDown(self):
        self.journal.close()
        self.tmp.cleanup()

    def test_equivalent_account_cannot_bypass_the_immutable_review(self):
        self.review["candidate_ready"] = False
        key = self.journal.import_review(self.message, self.review)
        original = self.journal.db.execute("SELECT payload_json FROM reviews WHERE id=?", (key,)).fetchone()[0]
        for account in ("OWNER@VALUECONNECT.KR", "Owner <owner@valueconnect.kr>"):
            with self.subTest(account=account):
                message = dict(self.message, account=account)
                self.assertEqual(self.journal.import_review(message, self.review), key)
                with self.assertRaisesRegex(ValueError, "immutable review conflict"):
                    self.journal.import_review(message, dict(self.review, candidate_ready=True))
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM reviews").fetchone()[0], 1)
        self.assertEqual(self.journal.db.execute("SELECT payload_json FROM reviews WHERE id=?", (key,)).fetchone()[0], original)

    def test_legacy_display_account_review_keeps_its_original_id_and_bytes(self):
        self.message["account"] = "Owner <OWNER@VALUECONNECT.KR>"
        result = classify(self.message, self.review)
        key = digest([self.message["account"], self.message["message_id"],
                      self.message["source_hash"], self.review["rule_version"]])
        payload = canonical(dict(message=self.message, review=self.review, result=result))
        with self.journal.db:
            self.journal.db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?)", (
                key, self.message["account"], self.message["message_id"], self.message["source_hash"],
                self.review["rule_version"], payload))
        self.message["account"] = "owner@valueconnect.kr"
        self.assertEqual(self.journal.import_review(self.message, self.review), key)
        self.assertEqual(self.journal.db.execute("SELECT payload_json FROM reviews WHERE id=?", (key,)).fetchone()[0], payload)

    def test_conflicting_legacy_account_aliases_fail_even_for_an_exact_key(self):
        for account, ready in ((self.message["account"], True), ("Owner <OWNER@VALUECONNECT.KR>", False)):
            message = dict(self.message, account=account)
            review = dict(self.review, candidate_ready=ready)
            key = digest([account, message["message_id"], message["source_hash"], review["rule_version"]])
            with self.journal.db:
                self.journal.db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?)", (
                    key, account, message["message_id"], message["source_hash"], review["rule_version"],
                    canonical(dict(message=message, review=review, result=classify(message, review)))))
        with self.assertRaisesRegex(ValueError, "immutable review conflict"):
            self.journal.import_review(self.message, self.review)
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM reviews").fetchone()[0], 2)

    def test_share_plan_reports_actual_state_without_authorizing_a_retry(self):
        for final_state, expected in (("FAILED", "forward_failed_reconciliation_required"),
                                      ("AMBIGUOUS", "forward_ambiguous_reconciliation_required"),
                                      ("SENDING", "forward_sending"),
                                      ("SENT_UNVERIFIED", "forward_sent_unverified"),
                                      ("VERIFIED", "forward_verified")):
            with self.subTest(state=final_state):
                message = dict(self.message, message_id=final_state, rfc_message_id=f"<{final_state}@example.test>")
                key = self.journal.import_review(message, self.review)
                plan = self.journal.plan(key)
                self.assertEqual(plan["sharing"], "forward_planned")
                share = next(op for op in plan["operations"] if op["kind"] == "share")
                self.journal.receipt(share["id"], "SENDING", {"original_sha256": "a" * 64})
                if final_state in ("SENT_UNVERIFIED", "VERIFIED"):
                    self.journal.receipt(share["id"], "SENT_UNVERIFIED", {})
                if final_state == "VERIFIED":
                    self.journal.receipt(share["id"], "VERIFIED", dict(
                        receiver_observation=dict(account=DESTINATION, message_id="received", content_hash=message["source_hash"], source_identity=["rfc", message["rfc_message_id"]]),
                        label_observation=dict(account=DESTINATION, message_id="received", labels=share["payload"]["labels"]),
                        archive_observation=dict(account=DESTINATION, message_id="received", original_sha256="a" * 64)))
                elif final_state not in ("SENDING", "SENT_UNVERIFIED"):
                    self.journal.receipt(share["id"], final_state, {})
                for source in (key, self.journal.import_review(dict(message, account="second@example.test"), self.review)):
                    repeated = self.journal.plan(source)
                    self.assertEqual(repeated["sharing"], expected)
                    self.assertEqual(next(op for op in repeated["operations"] if op["kind"] == "share")["id"], share["id"])
                with self.assertRaises(ValueError):
                    self.journal.receipt(share["id"], "SENDING", {"original_sha256": "a" * 64})

    def test_rfc_spelling_variants_share_one_global_intent(self):
        first = self.journal.plan(self.journal.import_review(self.message, self.review))
        share = next(op for op in first["operations"] if op["kind"] == "share")
        for spelling in ("one@example.test", " <one@example.test> "):
            with self.subTest(spelling=spelling):
                message = dict(self.message, account="second@example.test", message_id=spelling, rfc_message_id=spelling)
                plan = self.journal.plan(self.journal.import_review(message, self.review))
                self.assertEqual(next(op for op in plan["operations"] if op["kind"] == "share")["id"], share["id"])
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM operations WHERE kind='share'").fetchone()[0], 1)

    def test_legacy_unbracketed_rfc_intents_are_reused_without_rewriting(self):
        self.message["rfc_message_id"] = "one@example.test"
        key = self.journal.import_review(self.message, self.review)
        identity = ["rfc", self.message["rfc_message_id"]]
        global_key = digest([identity, self.message["source_hash"], DESTINATION])
        labels = self.journal.review(key)["result"]["labels"]
        payload = dict(content_hash=self.message["source_hash"], labels=labels, mode="additive", account=DESTINATION,
                       source_review_id=key, mirror_marker="[VC-MIRROR:v1]", source_identity=identity)
        receiver = self.journal._plan_operation(key, "receiver_labels", "receiver:" + digest([global_key, labels]), payload)
        share = self.journal._plan_operation(key, "share", "share:" + global_key, payload)
        before = {table: [tuple(row) for row in self.journal.db.execute(f"SELECT * FROM {table} ORDER BY rowid")]
                  for table in ("reviews", "operations", "receipts")}
        self.journal.close()
        self.journal = Journal(self.path)
        message = dict(self.message, account="second@example.test", rfc_message_id="<one@example.test>")
        plan = self.journal.plan(self.journal.import_review(message, self.review))
        self.assertEqual(next(op for op in plan["operations"] if op["kind"] == "share")["id"], share["id"])
        self.assertEqual(next(op for op in plan["operations"] if op["kind"] == "receiver_labels")["id"], receiver["id"])
        for table, rows in before.items():
            self.assertEqual([tuple(row) for row in self.journal.db.execute(f"SELECT * FROM {table} ORDER BY rowid")][:len(rows)], rows)
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM operations WHERE kind='share'").fetchone()[0], 1)
        for operation in (receiver, share):
            self.journal.receipt(operation["id"], "SENDING", {"original_sha256": "a" * 64})
            self.journal.receipt(operation["id"], "SENT_UNVERIFIED", {})
            readback = dict(
                receiver_observation=dict(account=DESTINATION, message_id="received", content_hash=message["source_hash"], source_identity=["rfc", "<one@example.test>"]),
                label_observation=dict(account=DESTINATION, message_id="received", labels=labels),
                archive_observation=dict(account=DESTINATION, message_id="received", original_sha256="a" * 64))
            self.assertEqual(self.journal.receipt(operation["id"], "VERIFIED", readback)["state"], "VERIFIED")

    def test_unrelated_mirror_rfc_text_does_not_block_a_valid_source_plan(self):
        message = dict(self.message, account=DESTINATION, message_id="unrelated-dev", rfc_message_id="malformed-id")
        self.assertEqual(self.journal.plan(self.journal.import_review(message, self.review))["sharing"], "mirror_or_dev_source")
        plan = self.journal.plan(self.journal.import_review(self.message, self.review))
        self.assertEqual(plan["sharing"], "forward_planned")

    def test_legacy_scope_reservation_without_operations_still_blocks_variants(self):
        self.message["rfc_message_id"] = "one@example.test"
        key = self.journal.import_review(self.message, self.review)
        old_scope = digest([self.message["rfc_message_id"], DESTINATION])
        with self.journal.db:
            self.journal.db.execute("INSERT INTO share_scopes VALUES(?,?,?)", (old_scope, self.message["source_hash"], key))
        self.journal.close()
        self.journal = Journal(self.path)
        message = dict(self.message, account="second@example.test", rfc_message_id="<one@example.test>", html="<p>Variant</p>")
        review = dict(self.review, content_hash=content_hash(message["authored_text"], message["html"]))
        message["source_hash"] = review["content_hash"]
        plan = self.journal.plan(self.journal.import_review(message, review))
        self.assertEqual(plan["sharing"], "rfc_variant_review_required")
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM operations WHERE kind='share'").fetchone()[0], 0)
        self.assertIsNotNone(self.journal.db.execute("SELECT 1 FROM share_scopes WHERE scope=?", (old_scope,)).fetchone())

    def test_conflicting_legacy_rfc_groups_require_reconciliation(self):
        key = self.journal.import_review(self.message, self.review)
        labels = self.journal.review(key)["result"]["labels"]
        for spelling in ("<one@example.test>", "one@example.test"):
            identity = ["rfc", spelling]
            global_key = digest([identity, self.message["source_hash"], DESTINATION])
            payload = dict(content_hash=self.message["source_hash"], labels=labels, mode="additive", account=DESTINATION,
                           source_review_id=key, mirror_marker="[VC-MIRROR:v1]", source_identity=identity)
            self.journal._plan_operation(key, "share", "share:" + global_key, payload)
        plan = self.journal.plan(key)
        self.assertEqual(plan["sharing"], "rfc_identity_reconciliation_required")
        self.assertEqual([op["kind"] for op in plan["operations"]], ["source_labels"])
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM operations WHERE kind='share'").fetchone()[0], 2)

    def test_rfc_alias_preserves_known_recipient_and_variant_quarantine(self):
        self.message["to_addresses"] = [DESTINATION]
        self.journal.plan(self.journal.import_review(self.message, self.review))
        message = dict(self.message, account="second@example.test", rfc_message_id="one@example.test", to_addresses=[])
        plan = self.journal.plan(self.journal.import_review(message, self.review))
        self.assertEqual(plan["sharing"], "already_recipient_label_pending")
        self.assertFalse(any(op["kind"] == "share" for op in plan["operations"]))
        message.update(message_id="variant", html="<p>Different representation</p>")
        review = dict(self.review, content_hash=content_hash(message["authored_text"], message["html"]))
        message["source_hash"] = review["content_hash"]
        plan = self.journal.plan(self.journal.import_review(message, review))
        self.assertEqual(plan["sharing"], "rfc_variant_review_required")
        self.assertEqual([op["kind"] for op in plan["operations"]], ["source_labels"])

    def test_missing_rfc_stays_local_without_automatic_duplicate_delivery(self):
        self.message["rfc_message_id"] = None
        for account in ("first@example.test", "second@example.test"):
            with self.subTest(account=account):
                message = dict(self.message, account=account)
                key = self.journal.import_review(message, self.review)
                plan = self.journal.plan(key)
                self.assertEqual(plan["sharing"], "local_identity_reconciliation_required")
                self.assertTrue(plan["duplicate_risk"])
                self.assertEqual(plan["source_identity"], ["local", account, message["message_id"]])
                self.assertEqual([op["kind"] for op in plan["operations"]], ["source_labels"])
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM operations WHERE kind='share'").fetchone()[0], 0)
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM reviews").fetchone()[0], 2)

    def _populate_all_tables(self):
        event = dict(actor="client", event_type="position_update", stage="unknown", reason_quote=None,
                     company_id="company-1", position_id="position-1", candidate_id=None,
                     application_id=None, review_status="confirmed",
                     evidence=self.review["golden_axes"]["role"]["evidence"])
        self.review["ontology_events"] = [event]
        key = self.journal.import_review(self.message, self.review)
        self.journal.plan(key)
        other = self.journal.import_review(dict(self.message, message_id="other"), self.review)
        self.journal.coverage("owner@example.test", "synthetic", None, None, 1, "ok", False)
        return key, other

    def test_replace_cannot_overwrite_any_journal_table_even_on_fresh_connection(self):
        _, other = self._populate_all_tables()
        replacements = {"reviews": ("payload_json", "{}"), "events": ("payload_json", "{}"),
                        "operations": ("payload_json", "{}"), "receipts": ("payload_json", "{}"),
                        "coverage": ("count", 99), "share_scopes": ("review_id", other)}
        fresh = sqlite3.connect(self.path)
        fresh.row_factory = sqlite3.Row
        self.assertEqual(fresh.execute("PRAGMA recursive_triggers").fetchone()[0], 0)
        try:
            for connection in (self.journal.db, fresh):
                for table, (field, value) in replacements.items():
                    with self.subTest(connection="application" if connection is self.journal.db else "fresh", table=table):
                        row = dict(connection.execute(f"SELECT * FROM {table} LIMIT 1").fetchone())
                        replacement = dict(row, **{field: value})
                        columns = ",".join(replacement)
                        placeholders = ",".join("?" for _ in replacement)
                        try:
                            with self.assertRaises(sqlite3.IntegrityError):
                                connection.execute(f"INSERT OR REPLACE INTO {table} ({columns}) VALUES ({placeholders})", tuple(replacement.values()))
                        finally:
                            connection.rollback()
                        self.assertEqual(dict(connection.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()), row)
        finally:
            fresh.close()

    def test_reopen_preserves_replay_and_scope_seeding(self):
        key = self.journal.import_review(self.message, self.review)
        first_plan = self.journal.plan(key)
        self.journal.close()
        self.journal = Journal(self.path)
        self.assertEqual(self.journal.import_review(self.message, self.review), key)
        self.assertEqual(self.journal.plan(key), first_plan)
        self.assertEqual(self.journal.db.execute("SELECT count(*) FROM share_scopes").fetchone()[0], 1)

    def test_source_operation_uses_address_spec_without_replacing_legacy_intent(self):
        self.message["account"] = "Owner <OWNER@EXAMPLE.TEST>"
        key = self.journal.import_review(self.message, self.review)
        source = next(op for op in self.journal.plan(key)["operations"] if op["kind"] == "source_labels")
        self.assertEqual(source["payload"]["account"], "owner@example.test")
        self.assertEqual(self.journal.review(key)["message"]["account"], self.message["account"])
        self.assertEqual(self.journal.plan(key)["operations"][0], source)

    def test_internal_full_layout_quote_is_hashed_not_an_extra_body_copy(self):
        self.message["source_kind"] = "internal"
        original = copy.deepcopy(self.review)
        key = self.journal.import_review(self.message, self.review)
        stored = self.journal.review(key)
        self.assertNotIn("authored_text", stored["message"])
        layout = stored["review"]["golden_axes"]["layout"]["evidence"]
        self.assertNotIn("quote", layout)
        self.assertEqual(layout["quote_sha256"], hashlib.sha256(self.message["authored_text"].encode()).hexdigest())
        self.assertEqual(layout["start"], 0)
        self.assertEqual(layout["end"], len(self.message["authored_text"]))
        self.assertEqual(self.review, original)
        self.assertEqual(self.journal.import_review(self.message, self.review), key)

    def test_legacy_full_quote_reimports_without_rewriting_history(self):
        self.message["source_kind"] = "internal"
        result = classify(self.message, self.review)
        key = digest([self.message["account"], self.message["message_id"],
                      self.message["source_hash"], self.review["rule_version"]])
        legacy_message = dict(self.message)
        legacy_message.pop("authored_text")
        original = canonical(dict(message=legacy_message, review=self.review, result=result))
        with self.journal.db:
            self.journal.db.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?)", (
                key, self.message["account"], self.message["message_id"], self.message["source_hash"],
                self.review["rule_version"], original))
        self.assertEqual(self.journal.import_review(self.message, self.review), key)
        self.assertEqual(self.journal.db.execute("SELECT payload_json FROM reviews WHERE id=?", (key,)).fetchone()[0], original)
        altered = dict(self.review, reviewer="changed-reviewer")
        with self.assertRaises(ValueError):
            self.journal.import_review(self.message, altered)

    def test_direct_customer_ontology_keeps_exact_body_and_event_reason(self):
        quote = self.review["golden_axes"]["role"]["evidence"]
        self.review["ontology_events"] = [dict(
            actor="client", event_type="feedback", stage="document", reason_quote=quote["quote"],
            company_id="company-1", position_id="position-1", candidate_id="candidate-1",
            application_id="application-1", review_status="confirmed", evidence=quote)]
        key = self.journal.import_review(self.message, self.review)
        stored = self.journal.review(key)
        self.assertEqual(stored["message"]["authored_text"], self.message["authored_text"])
        self.assertEqual(stored["result"]["events"][0]["reason_quote"], quote["quote"])
        self.assertEqual(stored["review"], self.review)


if __name__ == "__main__":
    unittest.main()
