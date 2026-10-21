"""Synthetic regressions for CE1, CE2 and CE12; no mailbox access."""
import copy
import os
import tempfile
import unittest

from tools.mail_governance import core
from tools.mail_governance.journal import Journal


def rich_fixture():
    introduction = "김민수님, 결제 API 장애를 줄이고 정산 서비스를 확장하신 경험이 이번 백엔드 플랫폼 과제와 연결되어 연락드립니다."
    company = "회사 소개: 합성커머스는 연 매출 120억원과 누적 투자 80억원을 기반으로 해외 결제 사업을 새로 시작합니다."
    role = "담당 업무와 자격: 결제 API와 정산 파이프라인을 설계하고 실패율을 관리합니다. Python 운영 경험과 분산 트랜잭션 역량이 필요합니다."
    closing = "지원 안내: 플랫폼 팀과 과제를 논의하는 두 차례 면접을 진행하며 지원 일정과 보상 범위는 개별 협의합니다."
    text = "\n\n".join((introduction, company, role, closing))
    message = dict(account="owner@valueconnect.kr", message_id="synthetic-rich",
                   rfc_message_id="<synthetic-rich@example.test>", source_hash=core.content_hash(text),
                   from_address="hr@example.test", to_addresses=["owner@valueconnect.kr"], subject="백엔드 채용",
                   authored_text=text, observed_at="2026-10-21T10:00:00+09:00", occurred_at=None,
                   existing_labels=[], source_kind="direct_customer", company_id="company-synthetic")
    quotes = dict(company=company, role=role, personalization=introduction, layout=text)
    axes = {axis: dict(status="met", evidence=citation(text, quote)) for axis, quote in quotes.items()}
    review = dict(content_hash=message["source_hash"], rule_version="2026-10-21.v1", reviewer="reviewer:synthetic",
                  mail_types=["jd"], golden_axes=axes, candidate_ready=True,
                  internal_confidential=False, ontology_events=[])
    return message, review


def citation(source, quote, representation="authored_text"):
    start = source.index(quote)
    return dict(quote=quote, representation=representation, start=start, end=start + len(quote))


def html_layout(message, review, html):
    message["html"] = html
    message["source_hash"] = review["content_hash"] = core.content_hash(message["authored_text"], html)
    review["golden_axes"]["layout"]["evidence"] = citation(html, html, "html")


class GoldenInputRegressions(unittest.TestCase):
    def test_rich_plaintext_and_structured_html_remain_golden(self):
        message, review = rich_fixture()
        self.assertTrue(core.classify(message, review)["is_golden_sample"])
        html = "<article>" + "".join("<p>" + line + "</p>" for line in message["authored_text"].split("\n\n")) + "</article>"
        html_layout(message, review, html)
        self.assertTrue(core.classify(message, review)["is_golden_sample"])

    def test_ce1_one_character_evidence_and_break_are_not_golden(self):
        message, review = rich_fixture()
        for axis in ("company", "role", "personalization"):
            quote = review["golden_axes"][axis]["evidence"]["quote"][0]
            review["golden_axes"][axis]["evidence"] = citation(message["authored_text"], quote)
        html_layout(message, review, "<br>")
        self.assertFalse(core.classify(message, review)["is_golden_sample"])

    def test_layout_requires_visible_content_in_multiple_readable_blocks(self):
        message, review = rich_fixture()
        text = message["authored_text"]
        variants = ("<br>", "<div><br><br><br></div>",
                    "<script>" + text + "</script>", "<style>" + text + "</style>",
                    "<!-- " + text + " -->", "<p></p><p>&nbsp;</p><p> </p>",
                    "<div hidden>" + text + "</div>",
                    "<div style='display:none'>" + text + "</div>",
                    "<p>" + text.replace("\n", " ") + "</p>")
        for html in variants:
            with self.subTest(html=html[:45]):
                html_layout(message, review, html)
                self.assertFalse(core.classify(message, review)["is_golden_sample"])

    def test_name_only_personalization_is_not_golden(self):
        message, review = rich_fixture()
        quote = "김민수님"
        review["golden_axes"]["personalization"]["evidence"] = citation(message["authored_text"], quote)
        self.assertFalse(core.classify(message, review)["is_golden_sample"])

    def test_each_content_axis_rejects_a_single_character_independently(self):
        for axis in ("company", "role", "personalization"):
            with self.subTest(axis=axis):
                message, review = rich_fixture()
                quote = review["golden_axes"][axis]["evidence"]["quote"][0]
                review["golden_axes"][axis]["evidence"] = citation(message["authored_text"], quote)
                self.assertFalse(core.classify(message, review)["is_golden_sample"])

    def test_personalized_message_must_precede_company_and_role(self):
        message, review = rich_fixture()
        old = message["authored_text"]
        paragraphs = old.split("\n\n")
        message["authored_text"] = "\n\n".join(paragraphs[1:3] + paragraphs[:1] + paragraphs[3:])
        message["source_hash"] = review["content_hash"] = core.content_hash(message["authored_text"])
        for axis in ("company", "role", "personalization"):
            quote = review["golden_axes"][axis]["evidence"]["quote"]
            review["golden_axes"][axis]["evidence"] = citation(message["authored_text"], quote)
        review["golden_axes"]["layout"]["evidence"] = citation(message["authored_text"], message["authored_text"])
        self.assertFalse(core.classify(message, review)["is_golden_sample"])


class TrustedVersionRegressions(unittest.TestCase):
    def test_ce2_rule_version_is_pinned_by_the_application(self):
        self.assertEqual(getattr(core, "RULE_VERSION", None), "2026-10-21.v1")
        for version in ("2026-10-21.v1 ", " 2026-10-21.v1", "20261022-v2", "2026-10-21.v1\n"):
            with self.subTest(version=repr(version)):
                message, review = rich_fixture()
                review["rule_version"] = version
                with self.assertRaises(ValueError):
                    core.classify(message, review)

    def test_ce2_modified_version_cannot_create_a_new_golden_review(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Journal(os.path.join(directory, "journal.sqlite"))
            try:
                message, original = rich_fixture()
                original["candidate_ready"] = False
                key = db.import_review(message, original)
                changed = copy.deepcopy(original)
                changed.update(candidate_ready=True, rule_version="2026-10-21.v1 ")
                with self.assertRaises(ValueError):
                    db.import_review(message, changed)
                self.assertEqual(db.db.execute("SELECT count(*) FROM reviews").fetchone()[0], 1)
                self.assertNotIn("01JD/goldensample", db.review(key)["result"]["labels"])
            finally:
                db.close()


class AddressInputRegressions(unittest.TestCase):
    def test_ce12_display_recipient_prevents_dev_resend(self):
        for recipient in ("Dev <dev@valueconnect.kr>", '"Dev, Mirror" <DEV@VALUECONNECT.KR>'):
            with self.subTest(recipient=recipient), tempfile.TemporaryDirectory() as directory:
                db = Journal(os.path.join(directory, "journal.sqlite"))
                try:
                    message, review = rich_fixture()
                    message["to_addresses"] = [recipient]
                    plan = db.plan(db.import_review(message, review))
                    self.assertEqual(plan["sharing"], "already_recipient_label_pending")
                    self.assertFalse(any(operation["kind"] == "share" for operation in plan["operations"]))
                finally:
                    db.close()

    def test_display_sender_and_account_are_dev_sources(self):
        for field in ("account", "from_address"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                db = Journal(os.path.join(directory, "journal.sqlite"))
                try:
                    message, review = rich_fixture()
                    message[field] = "Dev <DEV@VALUECONNECT.KR>"
                    self.assertEqual(db.plan(db.import_review(message, review))["sharing"], "mirror_or_dev_source")
                finally:
                    db.close()

    def test_malformed_or_multi_address_values_are_rejected(self):
        for field in ("account", "from_address", "to_addresses"):
            for address in ("Dev <dev@valueconnect.kr", "dev@valueconnect.kr, other@example.test",
                            "dev@valueconnect.kr\r\nBcc: other@example.test", "not-an-address"):
                with self.subTest(field=field, address=repr(address)):
                    message, review = rich_fixture()
                    message[field] = [address] if field == "to_addresses" else address
                    with self.assertRaises(ValueError):
                        core.validate(message, review)


if __name__ == "__main__":
    unittest.main()
