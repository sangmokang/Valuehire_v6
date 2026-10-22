import copy
import hashlib
import io
import itertools
import os
import sqlite3
import tempfile
import unittest
import zipfile

from tools.mail_governance.core import classify, content_hash, validate
from tools.mail_governance.journal import Journal


def fixture():
    intro = "김님, 결제 API 장애를 줄이고 정산 서비스를 확장하신 경험이 이번 백엔드 플랫폼 과제와 연결되어 연락드립니다."
    company = "회사: 합성 커머스는 판매자 정산 서비스를 제공하며 매출 120억과 투자 80억을 바탕으로 해외 결제 사업을 시작합니다."
    role = "역할: 결제 API와 정산 서비스를 설계하고 실패율을 개선합니다. Python 분산 트랜잭션 경험이 필수이며 제품팀과 협업합니다."
    text = "\n\n".join((intro, company, role, "지원 안내: 전형은 두 차례 면접이며 보상은 협의합니다. 관심이 있으시면 이 메일로 회신해 주세요."))
    message = dict(account="owner@valueconnect.kr", message_id="m1", rfc_message_id="<one@example.test>",
                   source_hash=content_hash(text, None), from_address="hr@example.test",
                   to_addresses=["owner@valueconnect.kr"], subject="백엔드 채용", authored_text=text,
                   observed_at="2026-10-21T10:00:00+09:00", occurred_at=None, existing_labels=["KEEP"],
                   source_kind="direct_customer", company_id="company-1")
    quotes = dict(company=company, role=role, personalization=intro, layout=text)
    axes = {key: dict(status="met", evidence=dict(representation="authored_text", start=text.index(q),
                                                 end=text.index(q) + len(q), quote=q)) for key, q in quotes.items()}
    review = dict(content_hash=message["source_hash"], rule_version="2026-10-21.v1", reviewer="reviewer:test",
                  mail_types=["jd", "ontology"], golden_axes=axes, candidate_ready=True,
                  internal_confidential=False, ontology_events=[])
    return message, review


class ClassificationTests(unittest.TestCase):
    def test_rule_version_is_owned_by_the_running_code(self):
        message, review = fixture()
        for version in (review["rule_version"] + " ", "arbitrary-version", "20261021-v1"):
            with self.subTest(version=version):
                altered = copy.deepcopy(review)
                altered["rule_version"] = version
                with self.assertRaises(ValueError):
                    classify(message, altered)

    def test_mailbox_addresses_require_one_unambiguous_mailbox(self):
        message, review = fixture()
        for field in ("account", "from_address", "to_addresses"):
            for address in (" dev@valueconnect.kr", "dev@valueconnect.kr ",
                            "dev@valueconnect.kr\n", "dev", "dev@", "dev@example.test, other@example.test"):
                with self.subTest(field=field, address=address):
                    altered = copy.deepcopy(message)
                    altered[field] = [address] if field == "to_addresses" else address
                    with self.assertRaises(ValueError):
                        classify(altered, review)
        message.update(from_address="DEV@VALUECONNECT.KR", to_addresses=["DEV@VALUECONNECT.KR"])
        classify(message, review)
        for address in ('"two words"@example.test', '"dev"@valueconnect.kr', "Dev <dev@valueconnect.kr>"):
            message["to_addresses"] = [address]
            classify(message, review)

    def test_each_met_axis_requires_its_own_evidence(self):
        message, base = fixture()
        for name in base["golden_axes"]:
            with self.subTest(axis=name):
                review = copy.deepcopy(base)
                review["golden_axes"][name]["evidence"] = None
                with self.assertRaises(ValueError):
                    classify(message, review)

    def test_confirmed_event_company_matches_verified_message_company(self):
        message, review = fixture()
        review["ontology_events"] = [dict(
            actor="client", event_type="position_update", stage="unknown", reason_quote=None,
            company_id="company-1", position_id="position-1", candidate_id=None, application_id=None,
            review_status="confirmed", evidence=review["golden_axes"]["role"]["evidence"])]
        for company_id in (None, "company-2"):
            with self.subTest(company_id=company_id):
                message["company_id"] = company_id
                self.assertEqual(classify(message, review)["events"][0]["review_status"], "unresolved")
        message["company_id"] = "company-1"
        self.assertEqual(classify(message, review)["events"][0]["review_status"], "confirmed")

    def test_candidate_events_can_confirm_from_candidate_original(self):
        message, review = fixture()
        event = dict(actor="candidate", event_type="candidate_withdrawal", stage="document", reason_quote=None,
                     company_id="company-1", position_id="position-1", candidate_id="candidate-1",
                     application_id="application-1", review_status="confirmed",
                     evidence=review["golden_axes"]["role"]["evidence"])
        review["ontology_events"] = [event]
        for event_type in ("candidate_withdrawal", "candidate_no_response"):
            event["event_type"] = event_type
            message["source_kind"] = "candidate"
            self.assertEqual(classify(message, review)["events"][0]["review_status"], "confirmed")
            message["source_kind"] = "internal"
            self.assertEqual(classify(message, review)["events"][0]["review_status"], "unresolved")
            message["source_kind"] = "direct_customer"
            event["actor"] = "client"
            self.assertEqual(classify(message, review)["events"][0]["review_status"], "confirmed")
            event["actor"] = "candidate"
        message["source_kind"] = "candidate"
        event["event_type"] = "client_rejection"
        self.assertEqual(classify(message, review)["events"][0]["review_status"], "unresolved")

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
        message["html"] = "<article>" + "".join("<p>" + block + "</p>" for block in message["authored_text"].split("\n\n")) + "</article>"
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
        self.original = b"Message-ID: <one@example.test>\r\n\r\nSynthetic original with attachment\x00\xff"
        self.original_sha256 = hashlib.sha256(self.original).hexdigest()

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

    def test_review_version_cannot_bypass_an_existing_decision(self):
        self.review["candidate_ready"] = False
        first = self.db.import_review(self.message, self.review)
        altered = copy.deepcopy(self.review)
        altered["candidate_ready"] = True
        for version in (altered["rule_version"] + " ", "arbitrary-version", "20261021-v1"):
            altered["rule_version"] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.db.import_review(self.message, altered)
        self.assertEqual(self.db.db.execute("SELECT count(*) FROM reviews").fetchone()[0], 1)
        self.assertFalse(self.db.review(first)["result"]["is_golden_sample"])

    def test_append_only_blocks_replace_on_every_table_and_connection(self):
        self.review["ontology_events"] = [dict(
            actor="client", event_type="position_update", stage="unknown", reason_quote=None,
            company_id="company-1", position_id="position-1", candidate_id=None, application_id=None,
            review_status="confirmed", evidence=self.review["golden_axes"]["role"]["evidence"])]
        key = self.db.import_review(self.message, self.review)
        self.db.plan(key)
        self.db.coverage("mailbox", "query", None, None, 1, "ok", False)
        for connection_kind in ("journal", "plain", "reopened"):
            if connection_kind == "reopened":
                self.db.close()
                self.db = Journal(self.path)
            connection = sqlite3.connect(self.path) if connection_kind == "plain" else self.db.db
            try:
                for table in ("reviews", "events", "operations", "receipts", "coverage", "share_scopes"):
                    row = tuple(connection.execute(f"SELECT * FROM {table} LIMIT 1").fetchone())
                    marks = ",".join("?" for _ in row)
                    for insert in ("INSERT OR REPLACE", "REPLACE"):
                        with self.subTest(connection=connection_kind, table=table, insert=insert):
                            try:
                                with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only journal"):
                                    connection.execute(f"{insert} INTO {table} VALUES({marks})", row)
                            finally:
                                connection.rollback()
                            self.assertEqual(tuple(connection.execute(f"SELECT * FROM {table} LIMIT 1").fetchone()), row)
                    if table in ("reviews", "operations"):
                        alternate = ("different-primary-key",) + row[1:]
                        with self.subTest(connection=connection_kind, table=table, alternate_unique=True):
                            try:
                                with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only journal"):
                                    connection.execute(f"INSERT OR REPLACE INTO {table} VALUES({marks})", alternate)
                            finally:
                                connection.rollback()
                    if table in ("reviews", "events", "operations", "share_scopes"):
                        rowid = connection.execute(f"SELECT rowid FROM {table} LIMIT 1").fetchone()[0]
                        alternate = list(row)
                        alternate[0] = "different-key"
                        if table == "reviews":
                            alternate[1:3] = ["different-account", "different-message"]
                        if table == "operations":
                            alternate[3] = "different-dedup-key"
                        with self.subTest(connection=connection_kind, table=table, rowid=True):
                            columns = ",".join(c[1] for c in connection.execute(f"PRAGMA table_info({table})"))
                            try:
                                with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only journal"):
                                    connection.execute(f"INSERT OR REPLACE INTO {table}(rowid,{columns}) VALUES(?,{marks})", [rowid, *alternate])
                            finally:
                                connection.rollback()
            finally:
                if connection_kind == "plain":
                    connection.close()
        self.assertEqual(self.db.import_review(self.message, self.review), key)
        self.assertEqual(self.db.plan(key), self.db.plan(key))

    def test_reobservation_retains_immutable_review_and_additive_plan(self):
        first = self.db.import_review(self.message, self.review)
        operations = self.db.plan(first)["operations"]
        self.message["observed_at"] = "2026-10-21T11:00:00+09:00"
        self.assertEqual(self.db.import_review(self.message, self.review), first)
        self.message["existing_labels"] += ["01JD", "NEW-LABEL"]
        self.assertEqual(self.db.import_review(self.message, self.review), first)
        self.assertEqual(self.db.plan(first)["operations"], operations)
        stored = self.db.review(first)
        self.assertEqual(stored["message"]["observed_at"], "2026-10-21T10:00:00+09:00")
        self.assertEqual(stored["message"]["existing_labels"], ["KEEP"])
        self.assertEqual(self.db.db.execute("SELECT count(*) FROM reviews").fetchone()[0], 1)
        self.message["company_id"] = "different-company"
        with self.assertRaises(ValueError):
            self.db.import_review(self.message, self.review)

    def test_known_recipient_reserves_scope_and_prevents_cross_mailbox_resend(self):
        self.message["to_addresses"] = ["dev@valueconnect.kr"]
        first = self.db.import_review(self.message, self.review)
        self.assertEqual(self.db.plan(first)["sharing"], "already_recipient_label_pending")
        self.message.update(account="other@example.test", message_id="other-m1", to_addresses=[])
        same = self.db.import_review(self.message, self.review)
        plan = self.db.plan(same)
        self.assertEqual(plan["sharing"], "already_recipient_label_pending")
        self.assertFalse(any(o["kind"] == "share" for o in plan["operations"]))
        self.message.update(message_id="variant", html="<p>Variant</p>")
        self.message["source_hash"] = self.review["content_hash"] = content_hash(self.message["authored_text"], self.message["html"])
        variant = self.db.import_review(self.message, self.review)
        self.assertEqual(self.db.plan(variant)["sharing"], "rfc_variant_review_required")
        self.db.db.execute("DROP TABLE share_scopes")
        self.db.db.commit()
        self.db.close()
        self.db = Journal(self.path)
        self.assertEqual(self.db.plan(variant)["sharing"], "rfc_variant_review_required")

    def test_later_known_recipient_suppresses_pending_share_on_future_plans(self):
        first = self.db.import_review(self.message, self.review)
        pending = next(o for o in self.db.plan(first)["operations"] if o["kind"] == "share")
        self.message.update(account="other@example.test", message_id="other-m1", to_addresses=["dev@valueconnect.kr"])
        known = self.db.import_review(self.message, self.review)
        self.assertEqual(self.db.plan(known)["sharing"], "already_recipient_label_pending")
        self.message.update(account="third@example.test", message_id="third-m1", to_addresses=[])
        third = self.db.import_review(self.message, self.review)
        for key in (first, third):
            plan = self.db.plan(key)
            self.assertEqual(plan["sharing"], "already_recipient_label_pending")
            self.assertFalse(any(o["kind"] == "share" for o in plan["operations"]))
        self.assertEqual(self.db.operation(pending["id"])["state"], "PLANNED")

    def test_receiver_labels_cannot_reuse_readback_for_another_original(self):
        self.message["to_addresses"] = ["dev@valueconnect.kr"]
        first = self.db.import_review(self.message, self.review)
        self.db.plan(first)
        self.message.update(message_id="different", rfc_message_id="<different@example.test>")
        second = self.db.import_review(self.message, self.review)
        op = next(o for o in self.db.plan(second)["operations"] if o["kind"] == "receiver_labels")
        self.db.receipt(op["id"], "SENDING", {})
        self.db.receipt(op["id"], "SENT_UNVERIFIED", {})
        body = dict(account="dev@valueconnect.kr", message_id="receiver1", content_hash=self.message["source_hash"],
                    source_identity=["rfc", "<one@example.test>"])
        labels = dict(account="dev@valueconnect.kr", message_id="receiver1", labels=op["payload"]["labels"])
        with self.assertRaises(ValueError):
            self.db.receipt(op["id"], "VERIFIED", dict(receiver_observation=body, label_observation=labels))
        body["source_identity"] = ["rfc", self.message["rfc_message_id"]]
        self.assertEqual(self.db.receipt(op["id"], "VERIFIED", dict(receiver_observation=body, label_observation=labels))["state"], "VERIFIED")

    def test_share_send_intent_requires_original_rfc_hash(self):
        key = self.db.import_review(self.message, self.review)
        op = next(o for o in self.db.plan(key)["operations"] if o["kind"] == "share")
        for receipt in ({}, {"original_sha256": "wrong"}, {"original_sha256": 42}):
            with self.assertRaises(ValueError):
                self.db.receipt(op["id"], "SENDING", receipt)
            self.assertEqual(self.db.operation(op["id"])["state"], "PLANNED")

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
            message = dict(self.message, **fields)
            message.update(message_id=str(n), rfc_message_id=str(n))
            key = self.db.import_review(message, self.review)
            self.assertEqual(self.db.plan(key)["sharing"], "mirror_or_dev_source")

    def test_source_labels_require_original_message_id_with_valid_other_observations(self):
        key = self.db.import_review(self.message, self.review)
        op = next(o for o in self.db.plan(key)["operations"] if o["kind"] == "source_labels")
        body = dict(account=self.message["account"], message_id=self.message["message_id"],
                    content_hash=self.message["source_hash"])
        labels = dict(account=body["account"], message_id=body["message_id"], labels=op["payload"]["labels"])
        receipt = dict(receiver_observation=body, label_observation=labels)
        with self.assertRaises(ValueError):
            self.db.receipt(op["id"], "VERIFIED", receipt)
        self.db.receipt(op["id"], "SENDING", {})
        self.db.receipt(op["id"], "SENT_UNVERIFIED", {})
        body["message_id"] = labels["message_id"] = "different-message"
        with self.assertRaises(ValueError):
            self.db.receipt(op["id"], "VERIFIED", receipt)
        body["message_id"] = labels["message_id"] = self.message["message_id"]
        self.assertEqual(self.db.receipt(op["id"], "VERIFIED", receipt)["state"], "VERIFIED")

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
        self.db.receipt(op["id"], "SENDING", {"original_sha256": self.original_sha256})
        with self.assertRaises(ValueError):
            self.db.receipt(op["id"], "SENDING", {})
        self.db.receipt(op["id"], "SENT_UNVERIFIED", {"sender_message_id": "sent1"})
        body = dict(account="dev@valueconnect.kr", message_id="receiver1", content_hash=self.message["source_hash"],
                    source_identity=["rfc", self.message["rfc_message_id"]])
        labels = dict(account="dev@valueconnect.kr", message_id="receiver1", labels=op["payload"]["labels"])
        received_zip = io.BytesIO()
        with zipfile.ZipFile(received_zip, "w") as archive:
            archive.writestr("original.eml", self.original)
        with zipfile.ZipFile(io.BytesIO(received_zip.getvalue())) as archive:
            received_sha256 = hashlib.sha256(archive.read("original.eml")).hexdigest()
        original = dict(account=body["account"], message_id=body["message_id"], original_sha256=received_sha256)
        for receipt in ({"receiver_observation": body},
                        {"receiver_observation": body, "label_observation": dict(labels, account="fake@example.test"), "archive_observation": original},
                        {"receiver_observation": body, "label_observation": dict(labels, message_id="other-message"), "archive_observation": original},
                        {"receiver_observation": body, "label_observation": dict(labels, labels=[]), "archive_observation": original},
                        {"receiver_observation": dict(body, content_hash="0" * 64), "label_observation": labels, "archive_observation": original},
                        {"receiver_observation": body, "label_observation": labels},
                        {"receiver_observation": body, "label_observation": labels, "archive_observation": dict(original, original_sha256=hashlib.sha256(self.original + b"changed attachment").hexdigest())},
                        {"receiver_observation": body, "label_observation": labels, "archive_observation": dict(original, message_id="other-message")}):
            with self.assertRaises(ValueError):
                self.db.receipt(op["id"], "VERIFIED", receipt)
        self.db.receipt(op["id"], "VERIFIED", dict(receiver_observation=body, label_observation=labels, archive_observation=original))
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
