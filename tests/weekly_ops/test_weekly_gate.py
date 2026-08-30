import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".agents/skills/weekly-ops/scripts/weekly_gate.py"


def load_gate():
    spec = importlib.util.spec_from_file_location("weekly_gate", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_bundle():
    capability_names = (
        "db_read",
        "gmail_read",
        "clickup_read",
        "notion_read",
        "career_pages_read",
        "jobkorea_outreach_read",
        "saramin_outreach_read",
        "linkedin_outreach_read",
    )
    return {
        "schema_version": "weekly-ops-input-v1",
        "run": {
            "meeting_at": "2026-08-31T11:00:00+09:00",
            "window_start": "2026-08-23T00:00:00+09:00",
            "window_end_exclusive": "2026-08-30T00:00:00+09:00",
            "late_alert_end": "2026-08-31T11:00:00+09:00",
        },
        "capabilities": [
            {"name": name, "status": "PASS", "required": True}
            for name in capability_names
        ],
        "source_snapshots": [
            {
                "snapshot_id": "snap-gmail-fixture",
                "source_system": "gmail",
                "source_uri_ref": "protected:gmail-fixture",
                "fetched_at": "2026-08-29T10:05:00+09:00",
                "status": "PASS",
                "content_hash": "a" * 64,
                "evidence_refs": ["sha256:codeit-request"],
            },
            {
                "snapshot_id": "snap-career-fixture",
                "source_system": "career_page",
                "source_uri_ref": "https://careers.codeit.com/recruit",
                "fetched_at": "2026-08-31T01:29:00+09:00",
                "status": "PASS",
                "content_hash": "b" * 64,
                "evidence_refs": ["sha256:career-codeit"],
            },
            {
                "snapshot_id": "snap-outreach-fixture",
                "source_system": "sourcing_outreach",
                "source_uri_ref": "protected:outreach-fixture",
                "fetched_at": "2026-08-30T00:05:00+09:00",
                "status": "PASS",
                "content_hash": "c" * 64,
                "evidence_refs": ["sha256:receipt-1", "sha256:receipt-2"],
            },
        ],
        "dedupe_decisions": [],
        "positions": [
            {
                "canonical_id": "pos-codeit-backend",
                "company": "Codeit",
                "title": "Backend Engineer",
                "category": "backend/fullstack/cto",
                "origin": "CLIENT_REQUESTED",
                "intent": "REQUESTED",
                "event_at": "2026-08-29T10:00:00+09:00",
                "deadline_days": None,
                "late_stage": True,
                "difficulty": {
                    "scarcity": "HIGH",
                    "seniority": "HIGH",
                    "constraints": "MEDIUM",
                    "funnel_friction": "HIGH",
                },
                "evidence_refs": ["sha256:codeit-request"],
                "action": "후보군 확장과 1차 추천 일정 확정",
            }
        ],
        "publication_targets": [
            {
                "name": name,
                "target_id": f"{name}-fixture",
                "required": True,
                "status": "NOT_RUN",
            }
            for name in ("database", "clickup", "notion", "admin_web", "email")
        ],
    }


def mark_all_targets_verified(bundle, result):
    for target in bundle["publication_targets"]:
        target.update(
            status="READBACK_VERIFIED",
            write_ahead_intent_id=f"intent-{target['name']}",
            idempotency_key=f"idem-{target['name']}",
            schema_readback_ref=f"sha256:schema-{target['name']}",
            external_object_id=f"object-{target['name']}",
            receipt_id=f"receipt-{target['name']}",
            receipt_persisted_ref=f"db:receipt-{target['name']}",
            report_snapshot_id=result["report_snapshot_id"],
            content_hash=result["content_hash"],
        )


class WeeklyGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()

    def test_requested_position_score_is_deterministic(self):
        result = self.gate.evaluate(valid_bundle())

        score = result["positions"][0]["score"]
        self.assertEqual(score["urgency"], 75)
        self.assertEqual(score["difficulty"], 90)
        self.assertEqual(score["priority"], 80)
        self.assertEqual(score["version"], "weekly-priority-v1")

    def test_scraped_only_position_is_capped_and_not_in_customer_actions(self):
        bundle = valid_bundle()
        position = bundle["positions"][0]
        position.update(
            canonical_id="pos-scraped",
            origin="SCRAPED_STAGING",
            intent="NONE",
        )

        result = self.gate.evaluate(bundle)

        self.assertLessEqual(result["positions"][0]["score"]["priority"], 20)
        self.assertNotIn("pos-scraped", result["customer_priority_ids"])

    def test_scraped_origin_cannot_claim_customer_request(self):
        bundle = valid_bundle()
        bundle["positions"][0]["origin"] = "SCRAPED_STAGING"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("SCRAPED_CUSTOMER_INTENT_CONFLICT", result["errors"])

    def test_required_capability_failure_is_partial_not_zero(self):
        bundle = valid_bundle()
        bundle["capabilities"][2]["status"] = "NOT_RUN"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "PARTIAL")
        self.assertIn("clickup_read:NOT_RUN", result["blockers"])

    def test_exact_duplicate_with_different_ids_is_blocked(self):
        bundle = valid_bundle()
        duplicate = copy.deepcopy(bundle["positions"][0])
        duplicate["canonical_id"] = "pos-codeit-backend-duplicate"
        bundle["positions"].append(duplicate)

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("DUPLICATE_CANONICAL_KEY", result["errors"])

    def test_publication_receipts_do_not_change_snapshot_identity(self):
        bundle = valid_bundle()
        first = self.gate.evaluate(bundle)
        self.assertEqual(first["verdict"], "PARTIAL")

        mark_all_targets_verified(bundle, first)
        second = self.gate.evaluate(bundle)

        self.assertEqual(second["verdict"], "PASS")
        self.assertEqual(second["report_snapshot_id"], first["report_snapshot_id"])
        self.assertEqual(second["content_hash"], first["content_hash"])

    def test_mismatched_readback_blocks_publication(self):
        bundle = valid_bundle()
        first = self.gate.evaluate(bundle)
        mark_all_targets_verified(bundle, first)
        bundle["publication_targets"][0]["content_hash"] = "wrong-hash"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("PUBLICATION_READBACK_MISMATCH", result["errors"])

    def test_raw_message_body_is_rejected(self):
        bundle = valid_bundle()
        bundle["positions"][0]["raw_body"] = "private customer content"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("FORBIDDEN_SENSITIVE_FIELD", result["errors"])

    def test_post_cutoff_event_is_rendered_as_late_alert(self):
        bundle = valid_bundle()
        bundle["positions"][0]["event_at"] = "2026-08-30T09:00:00+09:00"

        result = self.gate.evaluate(bundle)

        self.assertIn("마감 후 경보", result["brief_markdown"])
        self.assertIn("Codeit", result["brief_markdown"])

    def test_career_parser_failure_is_partial_not_zero_openings(self):
        bundle = valid_bundle()
        bundle["career_page_summaries"] = [
            {
                "company": "Codeit",
                "official_url": "https://careers.codeit.com/recruit",
                "status": "FAIL",
                "active_requisitions": 0,
                "talent_pools": 0,
                "freshness_at": "2026-08-31T01:29:00+09:00",
                "limitation": "title mapping unavailable",
                "source_snapshot_id": "snap-career-fixture",
            }
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "PARTIAL")
        self.assertIn("career:Codeit:FAIL", result["blockers"])
        self.assertIn("수집 실패", result["brief_markdown"])
        self.assertNotIn("Codeit: 실공고 0개", result["brief_markdown"])

    def test_verified_outreach_builds_consultant_position_focus(self):
        bundle = valid_bundle()
        bundle["outreach_events"] = [
            {
                "event_id": "outreach-1",
                "consultant_id": "consultant-a",
                "consultant_display": "Consultant A",
                "position_id": "pos-codeit-backend",
                "channel": "jobkorea",
                "status": "SENT",
                "sent_at": "2026-08-24T09:00:00+09:00",
                "candidate_key_hmac": "hmac:candidate-1",
                "provider_receipt_ref": "sha256:receipt-1",
                "source_snapshot_id": "snap-outreach-fixture",
            },
            {
                "event_id": "outreach-2",
                "consultant_id": "consultant-a",
                "consultant_display": "Consultant A",
                "position_id": "pos-codeit-backend",
                "channel": "linkedin_rps",
                "status": "SENT",
                "sent_at": "2026-08-25T09:00:00+09:00",
                "candidate_key_hmac": "hmac:candidate-2",
                "provider_receipt_ref": "sha256:receipt-2",
                "source_snapshot_id": "snap-outreach-fixture",
            },
        ]

        result = self.gate.evaluate(bundle)

        focus = result["consultant_focus"][0]
        self.assertEqual(focus["verified_sent_count"], 2)
        self.assertEqual(focus["unique_candidate_count"], 2)
        self.assertEqual(focus["active_days"], 2)
        self.assertEqual(focus["positions"][0]["focus_share"], 1.0)
        self.assertEqual(focus["positions"][0]["grass_evidence"], "YELLOW_ELIGIBLE")
        self.assertIn("컨설턴트별 몰입", result["brief_markdown"])

    def test_sent_outreach_without_provider_readback_is_blocked(self):
        bundle = valid_bundle()
        bundle["outreach_events"] = [
            {
                "event_id": "outreach-no-receipt",
                "consultant_id": "consultant-a",
                "consultant_display": "Consultant A",
                "position_id": "pos-codeit-backend",
                "channel": "saramin",
                "status": "SENT",
                "sent_at": "2026-08-24T09:00:00+09:00",
                "candidate_key_hmac": "hmac:candidate-1",
                "source_snapshot_id": "snap-outreach-fixture",
            }
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_SENT_WITHOUT_READBACK", result["errors"])

    def test_missing_outreach_sources_are_not_rendered_as_zero_activity(self):
        bundle = valid_bundle()
        for capability in bundle["capabilities"]:
            if capability["name"].endswith("_outreach_read"):
                capability["status"] = "NOT_RUN"

        result = self.gate.evaluate(bundle)

        self.assertIn("컨설턴트별 몰입", result["brief_markdown"])
        self.assertIn("0건으로 해석하지 않는다", result["brief_markdown"])

    def test_explicit_client_priority_adds_versioned_urgency(self):
        bundle = valid_bundle()
        bundle["positions"][0]["client_priority"] = "TOP"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["positions"][0]["score"]["urgency"], 100)

    def test_closed_position_is_an_operating_update_not_customer_priority(self):
        bundle = valid_bundle()
        bundle["positions"][0]["lifecycle"] = "CLOSED"

        result = self.gate.evaluate(bundle)

        self.assertNotIn("pos-codeit-backend", result["customer_priority_ids"])
        self.assertIn("운영 변경", result["brief_markdown"])

    def test_omitted_required_capability_names_are_blocked(self):
        bundle = valid_bundle()
        bundle["capabilities"] = [
            item for item in bundle["capabilities"] if "outreach_read" not in item["name"]
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("CAPABILITY_REQUIRED_MISSING", result["errors"])

    def test_omitted_required_publication_targets_are_blocked(self):
        bundle = valid_bundle()
        bundle["publication_targets"] = bundle["publication_targets"][:1]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("PUBLICATION_REQUIRED_MISSING", result["errors"])

    def test_weak_readback_receipts_are_blocked(self):
        bundle = valid_bundle()
        first = self.gate.evaluate(bundle)
        for target in bundle["publication_targets"]:
            target.update(
                status="READBACK_VERIFIED",
                receipt_id=f"receipt-{target['name']}",
                report_snapshot_id=first["report_snapshot_id"],
                content_hash=first["content_hash"],
            )

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("PUBLICATION_RECEIPT_CONTRACT_INVALID", result["errors"])

    def test_missing_source_snapshots_are_blocked(self):
        bundle = valid_bundle()
        del bundle["source_snapshots"]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("SOURCE_SNAPSHOTS_MISSING", result["errors"])

    def test_non_pass_source_snapshot_cannot_become_full_pass(self):
        bundle = valid_bundle()
        bundle["source_snapshots"][0]["status"] = "FAIL"
        first = self.gate.evaluate(bundle)
        mark_all_targets_verified(bundle, first)

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "PARTIAL")
        self.assertIn("source:snap-gmail-fixture:FAIL", result["blockers"])

    def test_position_evidence_must_resolve_to_source_snapshot(self):
        bundle = valid_bundle()
        bundle["positions"][0]["evidence_refs"] = ["sha256:unknown"]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("POSITION_EVIDENCE_UNRESOLVED", result["errors"])

    def test_career_summary_must_resolve_to_source_snapshot(self):
        bundle = valid_bundle()
        bundle["career_page_summaries"] = [
            {
                "company": "Codeit",
                "official_url": "https://careers.codeit.com/recruit",
                "status": "PASS",
                "active_requisitions": 58,
                "talent_pools": 0,
                "freshness_at": "2026-08-31T01:29:00+09:00",
                "limitation": "",
                "source_snapshot_id": "snap-unknown",
            }
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("CAREER_SUMMARY_INVALID", result["errors"])

    def test_outreach_event_must_resolve_to_source_snapshot(self):
        bundle = valid_bundle()
        bundle["outreach_events"] = [
            {
                "event_id": "outreach-unresolved-source",
                "consultant_id": "consultant-a",
                "consultant_display": "Consultant A",
                "position_id": "pos-codeit-backend",
                "channel": "jobkorea",
                "status": "SENT",
                "sent_at": "2026-08-24T09:00:00+09:00",
                "candidate_key_hmac": "hmac:candidate-1",
                "provider_receipt_ref": "sha256:receipt-1",
                "source_snapshot_id": "snap-unknown",
            }
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_EVENT_INVALID", result["errors"])

    def test_outreach_receipt_must_resolve_inside_its_source_snapshot(self):
        bundle = valid_bundle()
        bundle["outreach_events"] = [
            {
                "event_id": "outreach-unresolved-receipt",
                "consultant_id": "consultant-a",
                "consultant_display": "Consultant A",
                "position_id": "pos-codeit-backend",
                "channel": "jobkorea",
                "status": "SENT",
                "sent_at": "2026-08-24T09:00:00+09:00",
                "candidate_key_hmac": "hmac:candidate-1",
                "provider_receipt_ref": "local:draft-or-open-tab-not-source-evidence",
                "source_snapshot_id": "snap-outreach-fixture",
            }
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_RECEIPT_UNRESOLVED", result["errors"])
        self.assertEqual(result["consultant_focus"], [])

    def test_identical_canonical_id_duplicate_is_blocked(self):
        bundle = valid_bundle()
        bundle["positions"].append(copy.deepcopy(bundle["positions"][0]))

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("DUPLICATE_CANONICAL_ID", result["errors"])

    def test_email_hidden_in_rendered_value_is_blocked(self):
        bundle = valid_bundle()
        bundle["positions"][0]["action"] = "contact candidate@example.com"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("FORBIDDEN_SENSITIVE_VALUE", result["errors"])
        self.assertNotIn("candidate@example.com", result["brief_markdown"])


if __name__ == "__main__":
    unittest.main()
