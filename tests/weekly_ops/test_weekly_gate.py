import copy
import unittest

from fixtures import (
    load_gate,
    mark_all_targets_verified,
    valid_bundle,
    valid_outreach_diagnostics,
    valid_outreach_event,
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

    def test_post_cutoff_event_is_rendered_as_late_alert(self):
        bundle = valid_bundle()
        bundle["positions"][0]["event_at"] = "2026-08-31T09:00:00+09:00"

        result = self.gate.evaluate(bundle)

        self.assertIn("마감 후 경보", result["brief_markdown"])
        self.assertIn("Codeit", result["brief_markdown"])

    def test_career_parser_failure_is_partial_not_zero_openings(self):
        bundle = valid_bundle()
        for capability in bundle["capabilities"]:
            if capability["name"] == "career_pages_read":
                capability["status"] = "FAIL"
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
        bundle["outreach_channel_diagnostics"] = valid_outreach_diagnostics()
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
                "provider_actor_ref": "provider-account:consultant-a-jobkorea",
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
                "provider_actor_ref": "provider-seat:consultant-a",
                "provider_receipt_ref": "sha256:receipt-2",
                "source_snapshot_id": "snap-outreach-fixture",
                "provider_seat_ref": "provider-seat:consultant-a",
                "provider_project_ref": "provider-project:codeit-backend",
            },
        ]

        result = self.gate.evaluate(bundle)

        focus = result["consultant_focus"][0]
        self.assertEqual(focus["verified_sent_count"], 2)
        self.assertEqual(focus["unique_candidate_count"], 2)
        self.assertEqual(focus["active_days"], 2)
        self.assertEqual(focus["comparison_status"], "COMPARABLE")
        self.assertEqual(focus["positions"][0]["focus_share"], 1.0)
        self.assertEqual(focus["positions"][0]["channel_mix"], {"jobkorea": 1, "linkedin_rps": 1})
        self.assertEqual(
            focus["positions"][0]["evidence_refs"],
            ["sha256:receipt-1", "sha256:receipt-2"],
        )
        self.assertEqual(focus["positions"][0]["grass_evidence"], "YELLOW_ELIGIBLE")
        self.assertEqual(len(result["channel_coverage"]), 3)
        self.assertEqual(result["excluded_rows"], [])
        self.assertIn("컨설턴트별 몰입", result["brief_markdown"])

    def test_out_of_window_sent_event_does_not_replace_zero_result_proof(self):
        bundle = valid_bundle()
        event = valid_outreach_event()
        event["sent_at"] = bundle["run"]["window_end_exclusive"]
        bundle["outreach_events"] = [event]
        bundle["zero_result_assertions"] = []

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("ZERO_RESULT_UNPROVEN", result["errors"])
        self.assertEqual(result["consultant_focus"], [])
        self.assertEqual(result["excluded_rows"][0]["reason"], "OUTSIDE_WEEKLY_WINDOW")

    def test_unread_consultant_account_is_coverage_gap_not_zero(self):
        bundle = valid_bundle()
        bundle["outreach_channel_diagnostics"][0]["covered_provider_actor_refs"] = []

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["data_verdict"], "PARTIAL")
        self.assertIn("outreach:jobkorea:consultant-a:NOT_RUN", result["blockers"])
        jobkorea = next(item for item in result["channel_coverage"] if item["channel"] == "jobkorea")
        self.assertEqual(jobkorea["covered_consultants"], [])
        self.assertEqual(jobkorea["not_run_consultants"], ["consultant-a"])

    def test_pending_and_failed_attempts_are_excluded_without_fake_sent_time(self):
        bundle = valid_bundle()
        pending = valid_outreach_event()
        pending.update(event_id="pending-1", status="PENDING", sent_at=None)
        failed = valid_outreach_event()
        failed.update(event_id="failed-1", status="FAILED", sent_at=None)
        bundle["outreach_events"] = [pending, failed]

        result = self.gate.evaluate(bundle)

        self.assertNotIn("OUTREACH_EVENT_INVALID", result["errors"])
        self.assertEqual(result["consultant_focus"], [])
        self.assertEqual(
            [item["reason"] for item in result["excluded_rows"]],
            ["STATUS_NOT_SENT", "STATUS_NOT_SENT"],
        )

    def test_sent_outreach_without_provider_readback_is_blocked(self):
        bundle = valid_bundle()
        bundle["outreach_channel_diagnostics"] = valid_outreach_diagnostics()
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
                "provider_actor_ref": "provider-account:consultant-a-saramin",
                "source_snapshot_id": "snap-outreach-fixture",
            }
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_SENT_WITHOUT_READBACK", result["errors"])

    def test_outreach_requires_roster_bound_provider_actor(self):
        cases = (
            ("missing_roster", None, "provider-account:consultant-a-jobkorea"),
            ("invented_consultant", "consultant-b", "provider-account:consultant-a-jobkorea"),
            ("wrong_provider_actor", "consultant-a", "provider-account:consultant-b-jobkorea"),
        )
        for name, consultant_id, actor_ref in cases:
            with self.subTest(name=name):
                bundle = valid_bundle()
                event = valid_outreach_event()
                event["provider_actor_ref"] = actor_ref
                if consultant_id is not None:
                    event["consultant_id"] = consultant_id
                if name == "missing_roster":
                    del bundle["consultant_roster"]
                bundle["outreach_events"] = [event]

                result = self.gate.evaluate(bundle)

                self.assertEqual(result["verdict"], "BLOCKED")
                self.assertTrue(
                    {"CONSULTANT_ROSTER_INVALID", "OUTREACH_CONSULTANT_UNMAPPED"}
                    & set(result["errors"])
                )
                self.assertEqual(result["consultant_focus"], [])

    def test_duplicate_provider_receipt_cannot_inflate_focus(self):
        bundle = valid_bundle()
        first = valid_outreach_event()
        second = {**first, "event_id": "outreach-duplicate-id"}
        bundle["outreach_events"] = [first, second]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_RECEIPT_DUPLICATE", result["errors"])
        self.assertEqual(result["consultant_focus"], [])

    def test_portal_outreach_without_channel_diagnostics_is_blocked(self):
        bundle = valid_bundle()
        del bundle["outreach_channel_diagnostics"]
        bundle["outreach_events"] = [valid_outreach_event()]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_DIAGNOSTICS_MISSING", result["errors"])
        self.assertIn("OUTREACH_SURFACE_UNVERIFIED", result["errors"])
        self.assertEqual(result["consultant_focus"], [])

    def test_browser_visible_or_unreadable_surfaces_cannot_create_sent_rows(self):
        cases = (
            ("access_state", "AUTH_REQUIRED"),
            ("access_state", "TUTORIAL_OR_DEMO"),
            ("access_state", "AUTOMATION_DENIED"),
            ("surface_kind", "screenshot"),
            ("surface_kind", "ocr"),
            ("surface_kind", "open_tab"),
            ("stable_receipt_available", False),
            ("covered_provider_actor_refs", []),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                bundle = valid_bundle()
                bundle["outreach_channel_diagnostics"] = valid_outreach_diagnostics()
                diagnostic = bundle["outreach_channel_diagnostics"][0]
                diagnostic[field] = value
                diagnostic["blocker_reason"] = "provider history is not readable"
                bundle["outreach_events"] = [valid_outreach_event()]

                result = self.gate.evaluate(bundle)

                self.assertEqual(result["verdict"], "BLOCKED")
                self.assertIn("OUTREACH_SURFACE_UNVERIFIED", result["errors"])
                self.assertEqual(result["consultant_focus"], [])

    def test_linkedin_sent_event_requires_seat_and_project_dimensions(self):
        for missing_field in ("provider_seat_ref", "provider_project_ref"):
            with self.subTest(missing_field=missing_field):
                bundle = valid_bundle()
                bundle["outreach_channel_diagnostics"] = valid_outreach_diagnostics()
                event = valid_outreach_event("linkedin_rps")
                del event[missing_field]
                bundle["outreach_events"] = [event]

                result = self.gate.evaluate(bundle)

                self.assertEqual(result["verdict"], "BLOCKED")
                self.assertIn("LINKEDIN_OUTREACH_DIMENSIONS_MISSING", result["errors"])
                self.assertEqual(result["consultant_focus"], [])

    def test_channel_diagnostic_must_share_the_event_source_snapshot(self):
        bundle = valid_bundle()
        bundle["source_snapshots"].append(
            {
                "snapshot_id": "snap-outreach-other",
                "source_system": "sourcing_outreach",
                "source_uri_ref": "protected:other-outreach-surface",
                "fetched_at": "2026-08-30T00:06:00+09:00",
                "status": "PASS",
                "content_hash": "d" * 64,
                "evidence_refs": ["sha256:receipt-other"],
            }
        )
        bundle["outreach_channel_diagnostics"] = valid_outreach_diagnostics()
        bundle["outreach_channel_diagnostics"][0]["source_snapshot_id"] = "snap-outreach-other"
        bundle["outreach_events"] = [valid_outreach_event()]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_SURFACE_UNVERIFIED", result["errors"])
        self.assertEqual(result["consultant_focus"], [])

    def test_channel_diagnostics_are_bound_into_snapshot_identity(self):
        bundle = valid_bundle()
        bundle["outreach_channel_diagnostics"] = valid_outreach_diagnostics()
        bundle["outreach_events"] = [valid_outreach_event()]
        first = self.gate.evaluate(bundle)

        bundle["outreach_channel_diagnostics"][0]["surface_ref"] = (
            "protected:jobkorea-position-offer-history-v2"
        )
        second = self.gate.evaluate(bundle)

        self.assertNotEqual(first["input_hash"], second["input_hash"])
        self.assertNotEqual(first["report_snapshot_id"], second["report_snapshot_id"])

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
        gmail_snapshot = next(
            item for item in bundle["source_snapshots"]
            if item["snapshot_id"] == "snap-gmail-fixture"
        )
        gmail_snapshot["status"] = "FAIL"
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
        bundle["outreach_channel_diagnostics"] = valid_outreach_diagnostics()
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
                "provider_actor_ref": "provider-account:consultant-a-jobkorea",
                "provider_receipt_ref": "sha256:receipt-1",
                "source_snapshot_id": "snap-unknown",
            }
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_EVENT_INVALID", result["errors"])

    def test_outreach_receipt_must_resolve_inside_its_source_snapshot(self):
        bundle = valid_bundle()
        bundle["outreach_channel_diagnostics"] = valid_outreach_diagnostics()
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
                "provider_actor_ref": "provider-account:consultant-a-jobkorea",
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

if __name__ == "__main__":
    unittest.main()
