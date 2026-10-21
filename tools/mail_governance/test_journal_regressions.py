"""Synthetic regressions for sharing identity, immutable rows, and minimal retention."""
import copy
import hashlib
import os
import sqlite3
import tempfile
import unittest

from tools.mail_governance.core import canonical, classify, digest
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
