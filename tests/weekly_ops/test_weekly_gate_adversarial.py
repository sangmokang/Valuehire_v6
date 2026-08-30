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

    def test_non_string_publication_target_fails_closed_without_exception(self):
        bundle = valid_bundle()
        bundle["publication_targets"][-1]["target_id"] = {"invalid": "shape"}

        result = self.gate.evaluate(bundle)

        self.assertEqual(result["verdict"], "BLOCKED")
        self.assertIn("PUBLICATION_TARGET_INVALID", result["errors"])
        self.assertIn("PUBLICATION_TARGET_INVALID", result["publication_report_markdown"])

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
