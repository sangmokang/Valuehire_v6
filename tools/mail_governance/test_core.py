import copy
import itertools
import os
import sqlite3
import tempfile
import unittest

from tools.mail_governance.core import classify, content_hash, validate
from tools.mail_governance.journal import Journal


def fixture():
    text = "회사: 매출 성장과 신규 사업\n\n역할: 제품 API와 핵심 지표\n\n개인화: 김님 결제 경험\n\n지원 안내: 정돈된 안내"
    message = dict(account="owner@valueconnect.kr", message_id="m1", rfc_message_id="<one@example.test>",
                   source_hash=content_hash(text, None), from_address="hr@example.test",
                   to_addresses=["owner@valueconnect.kr"], subject="백엔드 채용", authored_text=text,
                   observed_at="2026-10-21T10:00:00+09:00", occurred_at=None, existing_labels=["KEEP"],
                   source_kind="direct_customer", company_id="company-1")
    quotes = dict(company="회사: 매출 성장과 신규 사업", role="역할: 제품 API와 핵심 지표",
                  personalization="개인화: 김님 결제 경험", layout=text)
    axes = {key: dict(status="met", evidence=dict(representation="authored_text", start=text.index(q),
                                                 end=text.index(q) + len(q), quote=q)) for key, q in quotes.items()}
    review = dict(content_hash=message["source_hash"], rule_version="20261021-v1", reviewer="reviewer:test",
                  mail_types=["jd", "ontology"], golden_axes=axes, candidate_ready=True,
                  internal_confidential=False, ontology_events=[])
    return message, review


class ClassificationTests(unittest.TestCase):
    def test_golden_truth_table(self):
        message, base = fixture()
        for statuses in itertools.product(("met", "missing", "unknown"), repeat=4):
            for ready, confidential in itertools.product((True, False, None), repeat=2):
                review = copy.deepcopy(base)
                for axis, status in zip(review["golden_axes"].values(), statuses):
                    axis["status"] = status
                review.update(candidate_ready=ready, internal_confidential=confidential)
                result = classify(message, review)
                expected = all(s == "met" for s in statuses) and ready is True and confidential is False
                self.assertEqual(result["is_golden_sample"], expected)
                self.assertIn("01JD", result["labels"])
                self.assertEqual("01JD/goldensample" in result["labels"], expected)

    def test_non_jd_and_multiple_labels_preserve_existing(self):
        message, review = fixture()
        review["mail_types"] = ["interview", "daily_weekly", "ontology"]
        result = classify(message, review)
        self.assertFalse(result["is_golden_sample"])
        self.assertEqual(result["labels"], ["04dailyweekly", "05인터뷰메일", "06온톨로지"])
        self.assertIn("KEEP", result["resulting_labels"])

    def test_malformed_and_tampered_reviews_fail(self):
        message, review = fixture()
        mutations = [lambda m, r: r.update(content_hash="0" * 64),
                     lambda m, r: r.update(candidate_ready="true"),
                     lambda m, r: r.update(internal_confidential=0),
                     lambda m, r: r.update(mail_types="jd"),
                     lambda m, r: r.update(mail_types=["other"]),
                     lambda m, r: r["golden_axes"]["company"]["evidence"].update(quote="invented"),
                     lambda m, r: r["golden_axes"]["role"]["evidence"].update(start=True),
                     lambda m, r: r["golden_axes"]["layout"]["evidence"].update(representation="rendered"),
                     lambda m, r: m.update(authored_text=m["authored_text"] + "tampered"),
                     lambda m, r: m.update(to_addresses="dev@valueconnect.kr"),
                     lambda m, r: m.update(occurred_at="yesterday")]
        for mutate in mutations:
            m, r = copy.deepcopy(message), copy.deepcopy(review)
            mutate(m, r)
            with self.assertRaises(ValueError):
                classify(m, r)

    def test_layout_requires_readable_evidence(self):
        message, review = fixture()
        review["golden_axes"]["layout"]["evidence"] = review["golden_axes"]["company"]["evidence"]
        self.assertFalse(classify(message, review)["is_golden_sample"])
        message["html"] = "<article><p>회사 소개</p><p>역할과 지원 안내</p></article>"
        message["source_hash"] = review["content_hash"] = content_hash(message["authored_text"], message["html"])
        review["golden_axes"]["layout"]["evidence"] = dict(representation="html", start=0,
            end=len(message["html"]), quote=message["html"])
        self.assertTrue(classify(message, review)["is_golden_sample"])

    def test_ontology_unknown_entities_and_reasons(self):
        message, review = fixture()
        event = dict(actor="client", event_type="client_rejection", stage="document", reason_quote=None,
                     company_id="company-1", position_id="position-1", candidate_id=None,
                     application_id=None, review_status="confirmed", evidence=review["golden_axes"]["role"]["evidence"])
        review["ontology_events"] = [event]
        result = classify(message, review)["events"][0]
        self.assertEqual(result["review_status"], "unresolved")
        self.assertEqual(result["reason_status"], "reason_unknown")
        event.update(candidate_id="candidate-1", application_id="application-1")
        self.assertEqual(classify(message, review)["events"][0]["review_status"], "confirmed")
        message["source_kind"] = "internal"
        self.assertEqual(classify(message, review)["events"][0]["review_status"], "unresolved")
        event["reason_quote"] = "invented rejection reason"
        with self.assertRaises(ValueError):
            validate(message, review)

    def test_hold_and_feedback_clarification_are_not_rejections(self):
        message, review = fixture()
        quote = "후보자 A는 보류합니다. 피드백 기준을 추가 확인해 주세요."
        message["authored_text"] += "\n\n" + quote
        message["source_hash"] = review["content_hash"] = content_hash(message["authored_text"])
        start = message["authored_text"].index(quote)
        event = dict(actor="client", event_type="client_hold", stage="document", reason_quote=None,
                     company_id="company-1", position_id="position-1", candidate_id="candidate-1",
                     application_id="application-1", review_status="confirmed",
                     evidence=dict(representation="authored_text", start=start, end=start + len(quote), quote=quote))
        review["ontology_events"] = [event, dict(event, event_type="feedback_clarification")]
        result = classify(message, review)["events"]
        self.assertEqual([e["event_type"] for e in result], ["client_hold", "feedback_clarification"])
        self.assertTrue(all(e["review_status"] == "confirmed" for e in result))


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "journal.sqlite")
        self.db = Journal(self.path)
        self.message, self.review = fixture()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_journal_append_only_idempotent_and_private(self):
        first = self.db.import_review(self.message, self.review)
        self.assertEqual(first, self.db.import_review(self.message, self.review))
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)
        for sql in ("UPDATE reviews SET payload_json='{}'", "DELETE FROM reviews"):
            with self.assertRaises(sqlite3.IntegrityError):
                self.db.db.execute(sql)
        altered = copy.deepcopy(self.review)
        altered["reviewer"] = "other"
        with self.assertRaises(ValueError):
            self.db.import_review(self.message, altered)
        self.assertEqual(self.db.db.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_minimizes_raw_body_except_direct_customer_ontology(self):
        key = self.db.import_review(self.message, self.review)
        self.assertEqual(self.db.review(key)["message"]["authored_text"], self.message["authored_text"])
        self.message.update(message_id="m2", source_kind="internal")
        key = self.db.import_review(self.message, self.review)
        stored = self.db.review(key)["message"]
        self.assertNotIn("authored_text", stored)
        self.assertNotIn("html", stored)

    def test_global_share_dedup_and_pending_receiver_labels(self):
        key = self.db.import_review(self.message, self.review)
        ops = self.db.plan(key)
        share = next(o for o in ops["operations"] if o["kind"] == "share")
        self.message.update(account="other@valueconnect.kr", message_id="different")
        key2 = self.db.import_review(self.message, self.review)
        self.assertEqual(next(o for o in self.db.plan(key2)["operations"] if o["kind"] == "share")["id"], share["id"])
        self.message.update(message_id="m3", rfc_message_id="<two@example.test>", to_addresses=["dev@valueconnect.kr"])
        key3 = self.db.import_review(self.message, self.review)
        plan = self.db.plan(key3)
        self.assertEqual(plan["sharing"], "already_recipient_label_pending")
        self.assertEqual(next(o for o in plan["operations"] if o["kind"] == "receiver_labels")["state"], "PLANNED")
        self.assertFalse(any(o["kind"] == "share" for o in plan["operations"]))

    def test_mirror_and_dev_source_do_not_relay(self):
        for n, fields in enumerate((dict(account="dev@valueconnect.kr"),
                                    dict(subject="[VC-MIRROR:v1] source"),
                                    dict(from_address="dev@valueconnect.kr"))):
            self.message.update(fields, message_id=str(n), rfc_message_id=str(n))
            key = self.db.import_review(self.message, self.review)
            self.assertEqual(self.db.plan(key)["sharing"], "mirror_or_dev_source")

    def test_same_rfc_different_representation_is_quarantined(self):
        first_key = self.db.import_review(self.message, self.review)
        self.db.plan(first_key)
        self.message.update(account="other@valueconnect.kr", message_id="other-m1", html="<p>Different renderer</p>")
        self.message["source_hash"] = self.review["content_hash"] = content_hash(self.message["authored_text"], self.message["html"])
        key = self.db.import_review(self.message, self.review)
        plan = self.db.plan(key)
        self.assertEqual(plan["sharing"], "rfc_variant_review_required")
        self.assertEqual([operation["kind"] for operation in plan["operations"]], ["source_labels"])
        self.assertEqual(self.db.db.execute("SELECT count(*) FROM operations WHERE kind='share'").fetchone()[0], 1)
        self.db.close()
        self.db = Journal(self.path)
        self.assertEqual(self.db.plan(key)["sharing"], "rfc_variant_review_required")

    def test_existing_share_intents_seed_variant_guard_after_upgrade(self):
        key = self.db.import_review(self.message, self.review)
        self.db.plan(key)
        self.db.db.execute("DROP TABLE share_scopes")
        self.db.db.commit()
        self.db.close()
        self.db = Journal(self.path)
        self.message.update(account="other@valueconnect.kr", message_id="new-m1", html="<p>Variant</p>")
        self.message["source_hash"] = self.review["content_hash"] = content_hash(self.message["authored_text"], self.message["html"])
        key = self.db.import_review(self.message, self.review)
        self.assertEqual(self.db.plan(key)["sharing"], "rfc_variant_review_required")

    def test_receipts_fail_closed_and_readback_separate(self):
        key = self.db.import_review(self.message, self.review)
        op = next(o for o in self.db.plan(key)["operations"] if o["kind"] == "share")
        with self.assertRaises(ValueError):
            self.db.receipt(op["id"], "VERIFIED", {})
        self.db.receipt(op["id"], "SENDING", {})
        with self.assertRaises(ValueError):
            self.db.receipt(op["id"], "SENDING", {})
        self.db.receipt(op["id"], "SENT_UNVERIFIED", {"sender_message_id": "sent1"})
        body = dict(account="dev@valueconnect.kr", message_id="receiver1", content_hash=self.message["source_hash"])
        labels = dict(account="dev@valueconnect.kr", message_id="receiver1", labels=op["payload"]["labels"])
        for receipt in ({"receiver_observation": body},
                        {"receiver_observation": body, "label_observation": dict(labels, account="fake@example.test")},
                        {"receiver_observation": dict(body, content_hash="0" * 64), "label_observation": labels}):
            with self.assertRaises(ValueError):
                self.db.receipt(op["id"], "VERIFIED", receipt)
        self.db.receipt(op["id"], "VERIFIED", dict(receiver_observation=body, label_observation=labels))
        self.assertEqual(self.db.operation(op["id"])["state"], "VERIFIED")

    def test_multiple_events_survive_and_coverage_cannot_fake_complete(self):
        evidence = self.review["golden_axes"]["role"]["evidence"]
        event = dict(actor="client", event_type="position_update", stage="unknown", reason_quote=None,
                     company_id="company-1", position_id="position-1", candidate_id=None, application_id=None,
                     review_status="confirmed", evidence=evidence)
        self.review["ontology_events"] = [event, dict(event, position_id="position-2")]
        self.db.import_review(self.message, self.review)
        self.assertEqual(self.db.db.execute("SELECT count(*) FROM events").fetchone()[0], 2)
        self.db.coverage("a", "q", None, "next", 3, "ok", False)
        self.assertFalse(self.db.coverage_status("a", "q")["complete"])
        self.db.coverage("a", "q", "next", None, 1, "failed", False)
        self.assertFalse(self.db.coverage_status("a", "q")["complete"])
        self.db.coverage("b", "q", None, None, 1, "ok", False)
        self.assertTrue(self.db.coverage_status("b", "q")["complete"])
        self.db.coverage("c", "q", None, None, 100, "ok", True)
        self.assertFalse(self.db.coverage_status("c", "q")["complete"])


if __name__ == "__main__":
    unittest.main()
