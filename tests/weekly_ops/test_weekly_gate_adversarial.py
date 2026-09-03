import html
import importlib.util
import itertools
import unittest
from pathlib import Path

from fixtures import load_gate, mark_all_targets_verified, valid_bundle, valid_outreach_event


class WeeklyGateAdversarialTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_gate()

    def test_db_operating_snapshot_is_rendered_and_bound_to_identity(self):
        bundle = valid_bundle()
        first = self.gate.evaluate(bundle)

        self.assertEqual(first["operating_snapshot"]["closed_week"]["new_positions"], 14)
        self.assertIn("## 핵심 운영지표", first["brief_markdown"])
        self.assertIn("26W35 신규 포지션 14개 / 신규 고객사 9개", first["brief_markdown"])
        self.assertIn("현재 funnel은 별도 시점 snapshot", first["brief_markdown"])

        bundle["operating_snapshot"]["closed_week"]["new_positions"] = 15
        second = self.gate.evaluate(bundle)
        self.assertNotEqual(second["report_snapshot_id"], first["report_snapshot_id"])

    def test_client_requested_origin_rejects_none_intent(self):
        bundle = valid_bundle()
        bundle["positions"][0]["intent"] = "NONE"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["data_verdict"], "BLOCKED")
        self.assertIn("POSITION_ORIGIN_INTENT_MISMATCH", result["errors"])

    def test_client_shared_origin_rejects_requested_intent(self):
        bundle = valid_bundle()
        bundle["positions"][0]["origin"] = "CLIENT_SHARED"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["data_verdict"], "BLOCKED")
        self.assertIn("POSITION_ORIGIN_INTENT_MISMATCH", result["errors"])

    def test_existing_client_position_accepts_requirement_change(self):
        bundle = valid_bundle()
        bundle["positions"][0]["intent"] = "REQUIREMENT_CHANGED"

        result = self.gate.evaluate(bundle)

        self.assertNotIn("POSITION_ORIGIN_INTENT_MISMATCH", result["errors"])

    def test_db_read_pass_requires_verified_operating_snapshot(self):
        bundle = valid_bundle()
        del bundle["operating_snapshot"]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OPERATING_SNAPSHOT_MISSING", result["errors"])

    def test_operating_snapshot_must_match_closed_week_boundaries(self):
        bundle = valid_bundle()
        bundle["operating_snapshot"]["closed_week"]["week_start"] = "2026-08-23"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OPERATING_SNAPSHOT_INVALID", result["errors"])

    def test_operating_snapshot_rejects_future_freshness(self):
        bundle = valid_bundle()
        bundle["operating_snapshot"]["current"]["position_last_synced_at"] = (
            "2026-08-31T12:00:00+09:00"
        )

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OPERATING_SNAPSHOT_INVALID", result["errors"])

    def test_weekly_window_must_be_monday_to_monday(self):
        bundle = valid_bundle()
        bundle["run"]["window_start"] = "2026-08-19T00:00:00+09:00"
        bundle["run"]["window_end_exclusive"] = "2026-08-26T00:00:00+09:00"
        bundle["operating_snapshot"]["closed_week"]["week_start"] = "2026-08-19"
        bundle["operating_snapshot"]["closed_week"]["week_end"] = "2026-08-26"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("RUN_WINDOW_INVALID", result["errors"])

    def test_db_snapshot_requires_exact_rpc_source(self):
        bundle = valid_bundle()
        bundle["source_snapshots"][0]["source_uri_ref"] = "protected:manual-db-export"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OPERATING_SNAPSHOT_INVALID", result["errors"])

    def test_source_snapshot_rejects_fetch_after_meeting(self):
        bundle = valid_bundle()
        bundle["source_snapshots"][0]["fetched_at"] = "2026-08-31T12:30:00+09:00"

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("SOURCE_SNAPSHOT_INVALID", result["errors"])

    def test_operating_metric_sections_reject_unknown_keys(self):
        bundle = valid_bundle()
        bundle["operating_snapshot"]["current"]["funnel"]["weekly_proposals"] = 130

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OPERATING_SNAPSHOT_INVALID", result["errors"])

    def test_empty_positions_need_a_source_bound_zero_result_assertion(self):
        bundle = valid_bundle()
        bundle["positions"] = []

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("ZERO_RESULT_UNPROVEN", result["errors"])

    def test_empty_outreach_needs_a_source_bound_zero_result_assertion(self):
        bundle = valid_bundle()
        bundle["zero_result_assertions"] = []

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("ZERO_RESULT_UNPROVEN", result["errors"])

    def test_passed_outreach_capabilities_require_all_channel_diagnostics_even_at_zero(self):
        bundle = valid_bundle()
        del bundle["outreach_channel_diagnostics"]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_DIAGNOSTICS_MISSING", result["errors"])

    def test_nonpass_outreach_capability_still_requires_one_diagnostic_per_channel(self):
        bundle = valid_bundle()
        bundle["capabilities"][5]["status"] = "NOT_RUN"
        bundle["outreach_channel_diagnostics"] = bundle["outreach_channel_diagnostics"][1:]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_DIAGNOSTICS_MISSING", result["errors"])

    def test_passed_outreach_capabilities_require_consultant_roster_even_at_zero(self):
        bundle = valid_bundle()
        del bundle["consultant_roster"]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("CONSULTANT_ROSTER_INVALID", result["errors"])

    def test_provider_actor_cannot_belong_to_two_consultants(self):
        bundle = valid_bundle()
        shared_actor = bundle["consultant_roster"][0]["provider_accounts"]["jobkorea"][0]
        bundle["consultant_roster"].append(
            {
                "consultant_id": "consultant-b",
                "consultant_display": "Consultant B",
                "provider_accounts": {
                    "jobkorea": [shared_actor],
                    "saramin": ["provider-account:consultant-b-saramin"],
                    "linkedin_rps": ["provider-seat:consultant-b"],
                },
            }
        )

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("CONSULTANT_ROSTER_INVALID", result["errors"])

    def test_consultant_may_have_no_account_on_an_unused_channel(self):
        bundle = valid_bundle()
        bundle["consultant_roster"][0]["provider_accounts"]["linkedin_rps"] = []
        bundle["outreach_channel_diagnostics"][2]["covered_provider_actor_refs"] = []

        result = self.gate.evaluate(bundle)

        self.assertNotIn("CONSULTANT_ROSTER_INVALID", result["errors"])
        linkedin = next(
            item for item in result["channel_coverage"] if item["channel"] == "linkedin_rps"
        )
        self.assertEqual(linkedin["expected_account_count"], 0)
        self.assertEqual(linkedin["not_run_consultants"], [])

    def test_partial_coverage_forbids_peer_ranking(self):
        bundle = valid_bundle()
        bundle["consultant_roster"][0]["provider_accounts"]["jobkorea"].append("actor-a-2")
        bundle["consultant_roster"].append(
            {
                "consultant_id": "consultant-b",
                "consultant_display": "Consultant B",
                "provider_accounts": {
                    "jobkorea": ["actor-b-j"],
                    "saramin": ["actor-b-s"],
                    "linkedin_rps": ["actor-b-l"],
                },
            }
        )
        for diagnostic, actor in zip(
            bundle["outreach_channel_diagnostics"], ("actor-b-j", "actor-b-s", "actor-b-l")
        ):
            diagnostic["covered_provider_actor_refs"].append(actor)
        bundle["source_snapshots"][2]["evidence_refs"].append("sha256:receipt-3")
        event_a = valid_outreach_event()
        event_b = {
            **event_a,
            "event_id": "outreach-b-1",
            "consultant_id": "consultant-b",
            "consultant_display": "Consultant B",
            "provider_actor_ref": "actor-b-j",
            "provider_receipt_ref": "sha256:receipt-2",
            "candidate_key_hmac": "hmac:candidate-b-1",
        }
        bundle["outreach_events"] = [
            event_a,
            event_b,
            {
                **event_b,
                "event_id": "outreach-b-2",
                "provider_receipt_ref": "sha256:receipt-3",
                "candidate_key_hmac": "hmac:candidate-b-2",
            },
        ]

        result = self.gate.evaluate(bundle)

        self.assertEqual(
            [item["consultant_display"] for item in result["consultant_focus"]],
            ["Consultant A", "Consultant B"],
        )
        self.assertTrue(all(item["comparison_status"] == "NOT_COMPARABLE" for item in result["consultant_focus"]))
        self.assertIn("컨설턴트 간 순위 산정 안 함", result["brief_markdown"])

    def test_passed_career_capability_cannot_omit_daily_company_set(self):
        bundle = valid_bundle()
        bundle["career_page_summaries"] = []

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("CAREER_REQUIRED_COMPANY_MISSING", result["errors"])

    def test_dedupe_decision_requires_version_and_resolved_lineage(self):
        cases = (
            {
                "decision_id": "dedupe-1",
                "kept_canonical_id": "pos-codeit-backend",
                "removed_source_refs": ["sha256:codeit-request"],
                "reason": "exact provider identifier",
            },
            {
                "decision_id": "dedupe-2",
                "kept_canonical_id": "pos-unknown",
                "removed_source_refs": ["sha256:codeit-request"],
                "reason": "exact provider identifier",
                "rule_version": "weekly-dedupe-v1",
            },
            {
                "decision_id": "dedupe-3",
                "kept_canonical_id": "pos-codeit-backend",
                "removed_source_refs": ["sha256:unknown"],
                "reason": "exact provider identifier",
                "rule_version": "weekly-dedupe-v1",
            },
            {
                "decision_id": "dedupe-4",
                "kept_canonical_id": "pos-codeit-backend",
                "removed_source_refs": ["sha256:codeit-request"],
                "reason": "exact provider identifier",
                "rule_version": "weekly-dedupe-v0",
            },
        )
        for decision in cases:
            with self.subTest(decision=decision["decision_id"]):
                bundle = valid_bundle()
                bundle["dedupe_decisions"] = [decision]

                result = self.gate.evaluate(bundle)

                self.assertEqual(result["verdict"], "BLOCKED")
                self.assertIn("DEDUPE_DECISION_INVALID", result["errors"])

    def test_portal_activity_cannot_be_relabelled_as_generic_email(self):
        bundle = valid_bundle()
        bundle["outreach_events"] = [valid_outreach_event("email")]
        bundle["zero_result_assertions"] = []

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_EVENT_INVALID", result["errors"])
        self.assertEqual(result["consultant_focus"], [])

    def test_internal_handoff_cannot_be_counted_as_consultant_focus(self):
        bundle = valid_bundle()
        event = valid_outreach_event()
        event["provider_actor_ref"] = "gmail:internal-position-share"
        bundle["outreach_events"] = [event]

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("OUTREACH_CONSULTANT_UNMAPPED", result["errors"])
        self.assertEqual(result["consultant_focus"], [])

    def test_non_string_publication_target_fails_closed_without_exception(self):
        bundle = valid_bundle()
        bundle["publication_targets"][-1]["target_id"] = {"invalid": "shape"}

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("PUBLICATION_TARGET_INVALID", result["errors"])
        self.assertIn("FORBIDDEN_SENSITIVE_OUTPUT", result["errors"])
        self.assertEqual(result["publication_report_markdown"], "")
        self.assertEqual(result["receipts"], [])

    def test_unknown_sixth_publication_target_fails_closed(self):
        bundle = valid_bundle()
        bundle["publication_targets"].append(
            {"name": "unknown", "target_id": "unexpected", "status": "NOT_RUN"}
        )

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("PUBLICATION_TARGET_INVALID", result["errors"])

    def test_score_properties_hold_across_all_difficulty_labels(self):
        point_maps = self.gate.DIFFICULTY_POINTS
        prior = None
        for labels in itertools.product(("LOW", "MEDIUM", "HIGH"), repeat=4):
            bundle = valid_bundle()
            difficulty = dict(zip(point_maps, labels))
            bundle["positions"][0]["difficulty"] = difficulty

            first = self.gate.evaluate(bundle)["positions"][0]["score"]
            second = self.gate.evaluate(bundle)["positions"][0]["score"]

            self.assertEqual(first, second)
            self.assertGreaterEqual(first["difficulty"], 0)
            self.assertLessEqual(first["difficulty"], 100)
            if labels == ("LOW", "LOW", "LOW", "LOW"):
                prior = first["difficulty"]
            if labels == ("HIGH", "HIGH", "HIGH", "HIGH"):
                self.assertGreaterEqual(first["difficulty"], prior)

    def test_readbacks_do_not_turn_unproven_zero_rows_into_pass(self):
        bundle = valid_bundle()
        bundle["positions"] = []
        first = self.gate.evaluate(bundle)
        mark_all_targets_verified(bundle, first)

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("ZERO_RESULT_UNPROVEN", result["errors"])

    def test_publication_bundle_contains_machine_receipts(self):
        bundle = valid_bundle()
        first = self.gate.evaluate(bundle)
        mark_all_targets_verified(bundle, first)

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(len(result["receipts"]), 5)
        self.assertTrue(all(item["status"] == "READBACK_VERIFIED" for item in result["receipts"]))
        self.assertTrue(all(item["content_hash"] == result["content_hash"] for item in result["receipts"]))
        expected_targets = {item["name"]: item["target_id"] for item in bundle["publication_targets"]}
        self.assertEqual(
            {item["target_name"]: item["target_id"] for item in result["receipts"]},
            expected_targets,
        )

    def test_candidate_display_name_aliases_are_forbidden(self):
        for field in (
            "candidate_display_name",
            "candidateDisplayName",
            "candidate-display-name",
            "Candidate Display Name",
            "candidate_full_name",
            "applicant_name",
            "applicantName",
            "applicant-display-name",
        ):
            with self.subTest(field=field):
                bundle = valid_bundle()
                bundle["positions"][0][field] = "synthetic-person"
                result = self.gate.evaluate(bundle)
                self.assertEqual(result["data_verdict"], "BLOCKED")
                self.assertIn("FORBIDDEN_SENSITIVE_FIELD", result["errors"])

    def test_unlisted_pii_candidate_keys_fail_closed_via_allowlist(self):
        for field in (
            "email", "phone", "ssn", "jumin", "kakao_id", "resume_url",
            "profile_url", "linkedin_url", "name_ko",
            "이름", "연락처", "전화번호", "주소", "생년월일",
        ):
            with self.subTest(field=field):
                bundle = valid_bundle()
                bundle["positions"][0][field] = "synthetic-value"
                result = self.gate.evaluate(bundle)
                self.assertEqual(result["data_verdict"], "BLOCKED")
                self.assertIn("FORBIDDEN_UNKNOWN_FIELD", result["errors"])

    def test_novel_unlisted_keys_fail_closed_in_every_object(self):
        def with_outreach_extra(bundle):
            event = valid_outreach_event()
            event["totally_new_key"] = "x"
            bundle["outreach_events"] = [event]

        mutators = {
            "top_level": lambda bundle: bundle.update({"totally_new_key": "x"}),
            "run": lambda bundle: bundle["run"].update({"totally_new_key": "x"}),
            "capability": lambda bundle: bundle["capabilities"][0].update({"totally_new_key": "x"}),
            "source_snapshot": lambda bundle: bundle["source_snapshots"][0].update({"totally_new_key": "x"}),
            "career_summary": lambda bundle: bundle["career_page_summaries"][0].update({"totally_new_key": "x"}),
            "consultant_roster": lambda bundle: bundle["consultant_roster"][0].update({"totally_new_key": "x"}),
            "outreach_event": with_outreach_extra,
            "zero_result_assertion": lambda bundle: bundle["zero_result_assertions"][0].update({"totally_new_key": "x"}),
            "publication_target": lambda bundle: bundle["publication_targets"][0].update({"totally_new_key": "x"}),
            "operating_snapshot": lambda bundle: bundle["operating_snapshot"].update({"totally_new_key": "x"}),
        }
        for name, mutate in mutators.items():
            with self.subTest(object=name):
                bundle = valid_bundle()
                mutate(bundle)
                result = self.gate.evaluate(bundle)
                self.assertEqual(result["data_verdict"], "BLOCKED")
                self.assertIn("FORBIDDEN_UNKNOWN_FIELD", result["errors"])

    def test_structures_hidden_under_scalar_slots_fail_closed(self):
        bundle = valid_bundle()
        bundle["positions"][0]["evidence_refs"] = [
            "sha256:codeit-request", {"연락처": "synthetic-value"},
        ]
        result = self.gate.evaluate(bundle)
        self.assertEqual(result["data_verdict"], "BLOCKED")
        self.assertIn("FORBIDDEN_UNKNOWN_FIELD", result["errors"])

    def test_python_only_container_types_fail_closed(self):
        # 2026-09-04 Codex V2 지적: tuple/set은 list가 아니라 스키마 걷기를 통과했다
        self.assertTrue(
            self.gate.find_unknown_fields({"positions": ({"totally_new_key": "x"},)})
        )
        self.assertTrue(
            self.gate.find_unknown_fields({"positions": [{"evidence_refs": {"sha256:x"}}]})
        )

    def test_allowlisted_bundle_has_zero_unknown_field_false_positives(self):
        bundle = valid_bundle()
        bundle["source_snapshots"][3]["evidence_refs"].append("sha256:receipt-li")
        linkedin_event = valid_outreach_event("linkedin_rps")
        linkedin_event["provider_receipt_ref"] = "sha256:receipt-li"
        bundle["outreach_events"] = [valid_outreach_event(), linkedin_event]
        bundle["outreach_channel_diagnostics"][0]["blocker_reason"] = "정기 점검 안내"
        bundle["dedupe_decisions"] = [
            {
                "decision_id": "dedupe-ok",
                "kept_canonical_id": "pos-codeit-backend",
                "removed_source_refs": ["sha256:codeit-request"],
                "reason": "exact provider identifier",
                "rule_version": "weekly-dedupe-v1",
            }
        ]
        first = self.gate.evaluate(bundle)
        mark_all_targets_verified(bundle, first)

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["errors"], [])
        self.assertEqual(result["verdict"], "PASS")

    def test_legitimate_key_names_are_not_classified_as_pii(self):
        legitimate = (
            "position_id", "hiring_cycle_id", "candidate_key_hmac", "list_url",
            "official_url", "operator_url", "notion_parent_url", "search_url_ref",
            "metric_name", "risk_name", "target_name", "display_name_similarity",
        )
        payload = [{key: "synthetic"} for key in legitimate]
        self.assertEqual(self.gate.find_forbidden_fields(payload), [])

    def test_html_view_is_derived_from_the_canonical_brief_and_single_hash(self):
        renderer_path = (
            Path(__file__).resolve().parents[2]
            / ".agents/skills/weekly-ops/scripts/brief_renderer.py"
        )
        spec = importlib.util.spec_from_file_location("brief_renderer", renderer_path)
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        result = self.gate.evaluate(valid_bundle())

        rendered = renderer.render_html(
            result["brief_markdown"],
            result["report_snapshot_id"],
            result["content_hash"],
        )

        self.assertEqual(rendered.count('name="content-hash"'), 1)
        self.assertIn(html.escape(result["brief_markdown"]), rendered)
        self.assertIn(result["report_snapshot_id"], rendered)
        self.assertIn(result["content_hash"], rendered)

    def test_data_pass_does_not_hide_unverified_publication_targets(self):
        result = self.gate.evaluate(valid_bundle())

        self.assertEqual(result["data_verdict"], "PASS")
        self.assertEqual(result["publication_verdict"], "PARTIAL")
        self.assertEqual(result["verdict"], "PARTIAL")
        self.assertIn("데이터 판정은 발행 완료 판정이 아니다", result["brief_markdown"])
        for target in ("database", "clickup", "notion", "admin_web", "email"):
            self.assertIn(f"{target}:NOT_RUN", result["publication_report_markdown"])

    def test_html_shows_publication_report_outside_hashed_canonical_brief(self):
        renderer_path = (
            Path(__file__).resolve().parents[2]
            / ".agents/skills/weekly-ops/scripts/brief_renderer.py"
        )
        spec = importlib.util.spec_from_file_location("brief_renderer", renderer_path)
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        result = self.gate.evaluate(valid_bundle())

        rendered = renderer.render_html(
            result["brief_markdown"],
            result["report_snapshot_id"],
            result["content_hash"],
            result["publication_report_markdown"],
        )

        self.assertIn(html.escape(result["publication_report_markdown"]), rendered)
        self.assertIn("content hash 외부의 전달 통제 메타데이터", rendered)
        self.assertEqual(
            self.gate.hashlib.sha256(result["brief_markdown"].encode("utf-8")).hexdigest(),
            result["content_hash"],
        )


if __name__ == "__main__":
    unittest.main()
