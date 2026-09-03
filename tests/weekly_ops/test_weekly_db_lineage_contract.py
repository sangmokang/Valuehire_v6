import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".agents/skills/weekly-ops/scripts/sot_gate.py"
SPEC = importlib.util.spec_from_file_location("weekly_sot_gate_lineage", MODULE_PATH)
SOT_GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOT_GATE)


def db_contract() -> str:
    return (ROOT / "contracts/weekly-ops/db-contract-v1.sql").read_text(encoding="utf-8")


def semantic_errors_with_current_digest(mutant: str) -> list[str]:
    original = SOT_GATE.DB_CONTRACT_SHA256
    try:
        SOT_GATE.DB_CONTRACT_SHA256 = hashlib.sha256(mutant.encode()).hexdigest()
        return SOT_GATE._db_errors(mutant)
    finally:
        SOT_GATE.DB_CONTRACT_SHA256 = original


class WeeklyDbLineageContractTest(unittest.TestCase):
    def test_provider_receipt_must_belong_to_immutable_source_evidence(self):
        db = db_contract()
        self.assertIn("evidence_refs jsonb not null", db)
        self.assertIn("and source.evidence_refs ? new.provider_receipt_ref", db)

    def test_provider_receipt_membership_bypass_is_detected_without_digest_help(self):
        db = db_contract()
        start = db.index("create function weekly_proposal_send_transition_is_valid()")
        mutant = db[:start] + db[start:].replace(
            "and source.evidence_refs ? new.provider_receipt_ref",
            "and true",
            1,
        )
        self.assertNotEqual(mutant, db)
        self.assertIn(
            "DB_PROPOSAL_RECEIPT_LINEAGE_DRIFT",
            semantic_errors_with_current_digest(mutant),
        )

    def test_new_task_metric_must_derive_from_first_created_event(self):
        db = db_contract()
        self.assertIn("event.event_type = 'CREATED'", db)
        self.assertIn("event.event_at = task.first_created_at", db)
        self.assertIn("event.source_snapshot_id = task.source_snapshot_id", db)

    def test_new_task_zero_override_is_detected_without_digest_help(self):
        db = db_contract()
        start = db.index("elsif target_metric_name = 'new_task_count' then")
        end = db.index("elsif target_metric_name = 'reactivated_task_count' then", start)
        mutant = db[:start] + "elsif target_metric_name = 'new_task_count' then\n    select 0 into expected_value;\n  " + db[end:]
        self.assertIn(
            "DB_NEW_TASK_DERIVATION_DRIFT",
            semantic_errors_with_current_digest(mutant),
        )

    def test_initial_created_event_lineage_bypass_is_detected_without_digest_help(self):
        db = db_contract()
        mutant = db.replace(
            "or new.source_snapshot_id <> task_source_snapshot_id\n"
            "      or new.event_at <> task_first_created_at",
            "or false",
            1,
        )
        self.assertNotEqual(mutant, db)
        self.assertIn(
            "DB_NEW_TASK_DERIVATION_DRIFT",
            semantic_errors_with_current_digest(mutant),
        )

    def test_live_client_metric_origin_expansion_is_detected_without_digest_help(self):
        db = db_contract()
        mutant = db.replace(
            "where current_state.origin in ('CLIENT_REQUESTED', 'CLIENT_SHARED')",
            "where current_state.origin in ('CLIENT_REQUESTED', 'CLIENT_SHARED', 'SCRAPED_STAGING')",
            1,
        )
        self.assertNotEqual(mutant, db)
        self.assertIn("DB_LIVE_CLIENT_POSITION_DERIVATION_DRIFT", semantic_errors_with_current_digest(mutant))

    def test_client_intent_promotion_expansion_is_detected_without_digest_help(self):
        db = db_contract()
        mutant = db.replace(
            "(new.origin = 'CLIENT_REQUESTED' and intent.intent_type = 'REQUESTED')",
            "(new.origin = 'CLIENT_REQUESTED' and intent.intent_type in ('REQUESTED', 'REFERENCE_ONLY'))",
            1,
        )
        self.assertNotEqual(mutant, db)
        self.assertIn("DB_CLIENT_INTENT_PROMOTION_DRIFT", semantic_errors_with_current_digest(mutant))

    def test_position_state_intent_promotion_expansion_is_detected_without_digest_help(self):
        db = db_contract()
        start = db.index("create function weekly_position_state_event_is_valid()")
        mutant = db[:start] + db[start:].replace(
            "(new.origin = 'CLIENT_SHARED' and intent.intent_type = 'POSITION_SHARED')",
            "(new.origin = 'CLIENT_SHARED' and intent.intent_type in ('POSITION_SHARED', 'REFERENCE_ONLY'))",
            1,
        )
        self.assertNotEqual(mutant, db)
        self.assertIn("DB_CLIENT_INTENT_PROMOTION_DRIFT", semantic_errors_with_current_digest(mutant))

    def test_publication_target_reduction_is_detected_without_digest_help(self):
        db = db_contract()
        mutant = db.replace(
            "target_name in ('database', 'clickup', 'notion', 'admin_web', 'email')",
            "target_name in ('database', 'clickup', 'notion', 'admin_web')",
        ).replace("select count(*) = 5", "select count(*) = 4", 1).replace(
            "count(distinct intent.target_name) = 5", "count(distinct intent.target_name) = 4", 1
        )
        self.assertNotEqual(mutant, db)
        self.assertIn("DB_PUBLICATION_TARGET_SET_DRIFT", semantic_errors_with_current_digest(mutant))

    def test_normalized_fact_evidence_must_belong_to_its_source_snapshot(self):
        db = db_contract()
        self.assertGreaterEqual(db.count("source.evidence_refs ? new.evidence_ref"), 3)

    def test_normalized_evidence_membership_bypass_is_detected_without_digest_help(self):
        db = db_contract()
        mutant = db.replace("and source.evidence_refs ? new.evidence_ref", "and true", 1)
        self.assertNotEqual(mutant, db)
        self.assertIn("DB_NORMALIZED_EVIDENCE_LINEAGE_DRIFT", semantic_errors_with_current_digest(mutant))

    def test_zero_result_receipt_membership_bypass_is_detected_without_digest_help(self):
        db = db_contract()
        start = db.index("create function weekly_zero_result_assertion_is_valid()")
        mutant = db[:start] + db[start:].replace(
            "and source.evidence_refs ? new.provider_receipt_ref", "and true", 1
        )
        self.assertNotEqual(mutant, db)
        self.assertIn("DB_NORMALIZED_EVIDENCE_LINEAGE_DRIFT", semantic_errors_with_current_digest(mutant))

    def test_market_receipt_membership_bypass_is_detected_without_digest_help(self):
        db = db_contract()
        mutant = db.replace(
            "and source.evidence_refs ? new.protected_provider_receipt_ref", "and true", 1
        )
        self.assertNotEqual(mutant, db)
        self.assertIn("DB_NORMALIZED_EVIDENCE_LINEAGE_DRIFT", semantic_errors_with_current_digest(mutant))


if __name__ == "__main__":
    unittest.main()
