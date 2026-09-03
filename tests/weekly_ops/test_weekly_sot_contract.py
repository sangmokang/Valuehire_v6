import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".agents/skills/weekly-ops/scripts/sot_gate.py"
spec = importlib.util.spec_from_file_location("weekly_sot_gate", MODULE_PATH)
sot_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sot_gate)
HEADINGS = (
    "## 권한과 정본 우선순위",
    "## 현재 구현 상태",
    "## 보고 주차와 4주 데이터",
    "## 실제 고객 포지션과 Scraped 경계",
    "## Task identity와 중복 제거",
    "## Pipeline 정의",
    "## 후보자 소싱",
    "## LinkedIn 시장 접근성",
    "## 소싱 커버리지 위험지수",
    "## Notion Golden Sample 형식",
    "## 외부 발행과 개인정보",
    "## 검증과 완료 조건",
    "## 롤백과 영향 반경",
)
def valid_files():
    sot = "\n".join(("# Weekly Ops", *HEADINGS)) + """
valuehire-report-calendar-v1
SCRAPED_STAGING CLIENT_REQUESTED CLIENT_SHARED
(candidate_key_hmac, position_id, hiring_cycle_id)
`run_id`가 있는 증거 행은 같은 run의 source snapshot만 참조한다.
위 네 terminal stage 어디에서든 active stage로 돌아가는 event type은 `REACTIVATED`만 허용한다.
RECOMMENDATION_PENDING CLIENT_REVIEW ASSIGNMENT INTERVIEW_1 INTERVIEW_2
FINAL_INTERVIEW OFFER FINAL_ACCEPTED JOINED REJECTED WITHDRAWN CLOSED
Saramin JobKorea LinkedIn Recruiter
market_accessibility = (pool_points * precision_points * 100) // 2500
Pool points는 `result_count_lower_bound`를 versioned 구간값에 매핑한다.
0/20 HARD 0 UNRANKED
A=70..100 B=40..69 C=0..39 `YELLOW_ELIGIBLE` 두 section의 row 수를 합산하지 않는다.
어느 쪽도 우선하지 않고 영향 셀은 tuple의 lexicographic maximum
`post_cutoff_alerts` `market-accessibility-v2` `sourcing-coverage-risk-v1`
`market_formula_version` `coverage_risk_formula_version`
다섯 source 모두 talent pool/general opening을 active requisition에서 제외한다.
두 표면이 같은 숫자 weight, enum 또는 schema 값을 모두 명시하면 반드시 동일해야 한다. 값 충돌은 machine contract의 우선권이 아니라 drift이며 위 순서대로 이 문서가 우선한다. `REQUESTED→CLIENT_REQUESTED`
`REFERENCE_ONLY|NONE`도 origin을 승격하지 않는다.
metric_window_end_exclusive 새 current-run source snapshot을 먼저 캡처한다. 허용 집합을 넓히거나 배제를 줄이거나
P0/P1 즉시 실행 해야 한다
MODE_FORBIDS_PUBLICATION CONTRACT_ONLY_NOT_EXECUTABLE
외부 호출 전에는 exact target, private visibility, write-ahead intent, idempotency key, current schema readback이 필요하다.
External object ID는 외부 쓰기 결과로 받은 뒤 readback receipt에 기록한다.
"""
    legacy = {
        "runtime_status": {
            "state": "CONTRACT_ONLY_NOT_EXECUTABLE",
            "publication_allowed": False,
            "replacement_required": "notion-weekly-golden-v2",
        }
    }
    return {
        "sot": sot,
        "index": "[weekly-ops-contract.md](weekly-ops-contract.md)",
        "skill": "Read `docs/sot/weekly-ops-contract.md` before acting.",
        "prompt_contract": "Authority: `docs/sot/weekly-ops-contract.md`; Golden v1 is NOT_RUN.",
        "golden_reference": "Authority: `docs/sot/weekly-ops-contract.md`; publication is NOT_RUN.",
        "verification": "단위 테스트 0건 거부·mutation 생존 0건·CHECKED 양수",
        "legacy_contract": json.dumps(legacy),
    }
def repository_files():
    return {
        key: (ROOT / relative).read_text(encoding="utf-8")
        for key, relative in sot_gate.REQUIRED_PATHS.items()
    }
def replace_once(files, key, old, new):
    assert files[key].count(old) == 1
    files[key] = files[key].replace(old, new, 1)
class WeeklySotContractTest(unittest.TestCase):
    def assert_error(self, files, code):
        self.assertIn(code, sot_gate.audit_bundle(files))

    def test_valid_contract_bundle_passes(self):
        self.assertEqual(sot_gate.audit_bundle(valid_files()), [])

    def test_machine_contract_drift_cannot_override_sot(self):
        rule = "두 표면이 같은 숫자 weight, enum 또는 schema 값을 모두 명시하면 반드시 동일해야 한다. 값 충돌은 machine contract의 우선권이 아니라 drift이며 위 순서대로 이 문서가 우선한다."
        files = repository_files()
        normalized = " ".join(files["sot"].split())
        self.assertIn(rule, normalized)
        files["sot"] = files["sot"].replace("값 충돌은 machine contract의 우선권이", "값 충돌은 machine contract의 지배권이", 1)
        self.assertIn("SOT_AUTHORITY_MEANING_DRIFT", sot_gate.audit_bundle(files))

    def test_missing_heading_fails(self):
        files = valid_files()
        files["sot"] = files["sot"].replace(HEADINGS[4], "")
        self.assert_error(files, "SOT_HEADING_MISSING:## Task identity와 중복 제거")

    def test_additive_market_formula_fails(self):
        files = valid_files()
        files["sot"] = files["sot"].replace(
            "(pool_points * precision_points * 100) // 2500",
            "pool_points + precision_points",
        )
        self.assert_error(files, "SOT_MARKET_FORMULA_MISSING")

    def test_market_pool_input_and_publication_sequence_are_explicit(self):
        cases = (
            (
                "pool-input",
                "Pool points는 `result_count_lower_bound`를 versioned 구간값에 매핑한다.",
                "Pool points는 versioned 구간값을 사용한다.",
                "SOT_MARKET_POOL_INPUT_DRIFT",
            ),
            (
                "pre-write",
                "외부 호출 전에는 exact target, private visibility, write-ahead intent, idempotency key, current schema\nreadback이 필요하다.",
                "외부 호출 전에는 external object ID가 필요하다.",
                "SOT_PUBLICATION_SEQUENCE_DRIFT",
            ),
            (
                "post-write",
                "External object ID는 외부 쓰기\n결과로 받은 뒤 readback receipt에 기록한다.",
                "External object ID는 외부 호출 전에 준비한다.",
                "SOT_PUBLICATION_SEQUENCE_DRIFT",
            ),
        )
        for name, old, new, error in cases:
            with self.subTest(name=name):
                files = repository_files()
                replace_once(files, "sot", old, new)
                self.assert_error(files, error)

    def test_pre_interview_stage_contract_fails_when_removed(self):
        files = valid_files()
        files["sot"] = files["sot"].replace("RECOMMENDATION_PENDING CLIENT_REVIEW", "")
        self.assert_error(files, "SOT_PIPELINE_STAGE_MISSING:CLIENT_REVIEW")

    def test_index_and_execution_surfaces_must_link_sot(self):
        for key in ("index", "skill", "prompt_contract", "golden_reference"):
            with self.subTest(key=key):
                files = valid_files()
                files[key] = "unrelated"
                self.assert_error(files, f"SOT_LINK_MISSING:{key}")

    def test_legacy_contract_cannot_claim_publication(self):
        files = valid_files()
        legacy = json.loads(files["legacy_contract"])
        legacy["runtime_status"]["publication_allowed"] = True
        files["legacy_contract"] = json.dumps(legacy)
        self.assert_error(files, "LEGACY_PUBLICATION_NOT_BLOCKED")

    def test_fixed_mutation_count_is_rejected(self):
        files = valid_files()
        files["verification"] = "62개 단위 계약·mutation 25종"
        self.assert_error(files, "VERIFICATION_COUNT_DRIFT_RISK")

    def test_repository_bundle_is_complete(self):
        self.assertEqual(sot_gate.audit_paths(ROOT), []); files = repository_files(); files["sot"] += "\n규격 밖 완화"; self.assertIn("SOT_CONTRACT_DIGEST_DRIFT", sot_gate.audit_bundle(files)); files = repository_files(); files["skill"] += "\nunsafe override"; self.assertIn("SKILL_DIGEST_DRIFT", sot_gate.audit_bundle(files)); files = repository_files(); files["data_contract"] += "\nunsafe override"; self.assertIn("DATA_CONTRACT_DIGEST_DRIFT", sot_gate.audit_bundle(files)); files = repository_files(); files["adversarial_review"] += "\nunsafe override"; self.assertIn("ADVERSARIAL_REVIEW_DIGEST_DRIFT", sot_gate.audit_bundle(files))

    def test_missing_repository_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = sot_gate.audit_paths(Path(directory))
        self.assertTrue(errors)
        self.assertIn("FILE_MISSING:docs/sot/weekly-ops-contract.md", errors)

    def test_meaning_reversals_and_decoys_fail(self):
        cases = (
            (
                "authority",
                "sot",
                "결정할 수 없다.",
                "결정할 수 있다.",
            ),
            (
                "scraped",
                "sot",
                "position만 포함한다. `SCRAPED_STAGING`, `INTERNAL_CREATED`, canonical lifecycle `CLOSED`, ClickUp의\n외부 terminal status `closedpositions|complete`는 제외한다.",
                "position과 `SCRAPED_STAGING`을 모두 포함한다.",
            ),
            (
                "unknown-zero",
                "sot",
                "미확인 주차는 0이 아니라 `—`, `PARTIAL`, `NOT_RUN`으로 표시한다.",
                "미확인 주차는 0으로 표시한다.",
            ),
            (
                "golden-route",
                "skill",
                "return `NOT_RUN`; do not route a Golden request through the general v1 renderer.",
                "return `PASS`; route a Golden request through the general v1 renderer.",
            ),
        )
        for name, key, old, new in cases:
            with self.subTest(name=name):
                files = repository_files()
                replace_once(files, key, old, new)
                files[key] += f"\n폐기 참고 문자열: {old}\n"
                self.assertTrue(sot_gate.audit_bundle(files))

    def test_identity_formula_and_pipeline_decoys_fail(self):
        files = repository_files()
        identity = "(candidate_key_hmac, position_id, hiring_cycle_id)"
        replace_once(files, "sot", identity, "(candidate_key_hmac, position_id)")
        files["sot"] += f"\n폐기 참고 문자열: {identity}\n"
        self.assertTrue(sot_gate.audit_bundle(files))

        files = repository_files()
        formula = sot_gate.MARKET_FORMULA
        replace_once(files, "sot", formula, "market_accessibility = pool_points + precision_points")
        files["sot"] += f"\n폐기 참고 문자열: {formula}\n"
        self.assertTrue(sot_gate.audit_bundle(files))

        files = repository_files()
        old = "Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:\n\n- `RECOMMENDATION_PENDING`\n- `CLIENT_REVIEW`"
        new = "Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:\n\n- `OFFER`\n- `FINAL_ACCEPTED`"
        replace_once(files, "sot", old, new)
        self.assertTrue(sot_gate.audit_bundle(files))

        for anchor, duplicate, error in (
            (formula, "market_accessibility = 100", "SOT_MARKET_FORMULA_MEANING_DRIFT"),
            ("Candidate Task identity:\n\n`" + identity + "`", "Candidate Task identity: `(external_task_id)`", "SOT_CANDIDATE_IDENTITY_DRIFT"),
            ("Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:", "Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:\n\n- `OFFER`", "SOT_PIPELINE_SET_DRIFT:Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:"),
        ):
            files = repository_files(); replace_once(files, "sot", anchor, anchor + "\n" + duplicate); self.assertIn(error, sot_gate.audit_bundle(files))

    def test_runtime_urls_require_exact_equality(self):
        files = repository_files()
        runtime = json.loads(files["runtime_contract"])
        runtime["publication"]["notion_parent_url"] += "&tampered=1"
        files["runtime_contract"] = json.dumps(runtime)
        self.assertIn("RUNTIME_URL_MISMATCH:notion_parent_url", sot_gate.audit_bundle(files))

        for mutate, code in (
            (lambda runtime: runtime["golden_projection_policy"].update(legacy_priority_score_excluded=False), "RUNTIME_GOLDEN_PROJECTION_DRIFT"),
            (lambda runtime: runtime["golden_projection_policy"].update(post_cutoff_projection_section="twelfth_section"), "RUNTIME_GOLDEN_PROJECTION_DRIFT"),
            (lambda runtime: runtime["outreach_sources"][2].update(navigation_boundary="unbounded_web"), "RUNTIME_BROWSER_BOUNDARY_DRIFT"),
            (lambda runtime: runtime["outreach_sources"][0].pop("navigation"), "RUNTIME_BROWSER_BOUNDARY_DRIFT"),
            (lambda runtime: runtime["career_sources"][3].pop("talent_pool_behavior"), "RUNTIME_BROWSER_BOUNDARY_DRIFT"),
            (lambda runtime: runtime["intent_origin_mapping"].update(REFERENCE_ONLY="CLIENT_SHARED"), "RUNTIME_INTENT_ORIGIN_MAPPING_DRIFT"),
            (lambda runtime: runtime["publication"]["receipt_required_fields"].remove("target_id"), "RUNTIME_PUBLICATION_RECEIPT_TARGET_DRIFT"),
            (lambda runtime: runtime.update(career_sources=None), "RUNTIME_STRUCTURE_INVALID"),
            (lambda runtime: runtime["outreach_sources"].append(dict(runtime["outreach_sources"][0])), "RUNTIME_DUPLICATE_OR_UNKNOWN_SOURCE_DRIFT"), (lambda runtime: runtime["zero_result_contract"].update(collections=["positions"]), "RUNTIME_ZERO_RESULT_DRIFT"), (lambda runtime: runtime["outreach_diagnostic_contract"].update(require_all_channels_on_every_run=False), "RUNTIME_OUTREACH_DIAGNOSTIC_DRIFT"), (lambda runtime: runtime.update(unexpected_runtime_bypass=True), "RUNTIME_CONTRACT_DIGEST_DRIFT"),
        ):
            files = repository_files()
            runtime = json.loads(files["runtime_contract"])
            mutate(runtime)
            files["runtime_contract"] = json.dumps(runtime)
            self.assertIn(code, sot_gate.audit_bundle(files))

    def test_pathological_json_and_runtime_publication_mutations_fail_closed(self):
        files = repository_files()
        files["legacy_contract"] = "9" * 10000
        self.assertIn("LEGACY_CONTRACT_INVALID", sot_gate.audit_bundle(files))

        files = repository_files()
        runtime = json.loads(files["runtime_contract"])
        runtime["publication"]["require_readback"] = False
        files["runtime_contract"] = json.dumps(runtime)
        self.assertIn("RUNTIME_PUBLICATION_GUARD_DRIFT", sot_gate.audit_bundle(files))

    def test_legacy_and_db_contracts_match_normative_identity_and_market_formula(self):
        files = repository_files()
        legacy = json.loads(files["legacy_contract"])
        identity = ["candidate_key_hmac", "position_id", "hiring_cycle_id"]
        self.assertEqual(legacy["metrics"]["new_task_count"]["dedupe_key"], identity)
        self.assertEqual(legacy["pipeline"]["dedupe_key"], identity)
        market = legacy["market_accessibility"]
        self.assertEqual(market["evaluated_sample_size"], 20)
        self.assertEqual(market["score_formula"], sot_gate.MARKET_FORMULA.split(" = ", 1)[1])
        db = (ROOT / "contracts/weekly-ops/db-contract-v1.sql").read_text(encoding="utf-8")
        self.assertIn("hiring_cycle_id text not null", db)
        self.assertIn("unique (candidate_key_hmac, position_id, hiring_cycle_id)", db)

    def test_db_ledgers_current_state_and_publication_lineage_are_enforced(self):
        db = (ROOT / "contracts/weekly-ops/db-contract-v1.sql").read_text(encoding="utf-8")
        required = (
            "create function weekly_reject_mutation()",
            "create function weekly_run_transition_is_valid()", "weekly_run_publication_is_complete(new.run_id)",
            "create trigger weekly_run_transition_guard",
            "create trigger source_snapshots_immutable",
            "unique (run_id, snapshot_id)",
            "foreign key (run_id, source_snapshot_id)",
            "references source_snapshots(run_id, snapshot_id)",
            "create trigger zero_result_assertions_immutable", "collection_name in ('position_state', 'outreach_events', 'pipeline_events', 'pipeline_state')", "create function weekly_metric_expected_value(", "create function weekly_metric_snapshot_zero_is_verified()", "create trigger weekly_metric_snapshot_zero_guard", "WEEKLY_METRIC_ZERO_RECEIPT_MISSING", "WEEKLY_METRIC_DERIVATION_INVALID", "metric_iso_week text not null", "check (status = 'VERIFIED' or value is null)",
            "create table canonical_position_state_events (", "create trigger canonical_position_state_events_immutable", "create table linkedin_market_result_receipts (", "create trigger linkedin_market_result_receipts_immutable", "create function weekly_proposal_send_transition_is_valid()",
            "create trigger proposal_send_attempts_transition_guard",
            "primary key (run_id, collection_name, dimension_key, week_index, source_snapshot_id)", "provider_receipt_ref is null or btrim(provider_receipt_ref) <> ''", "status = 'FAILED' and finalized_at is not null", "and sent_at is null and provider_receipt_ref is null", "check (coverage_status <> 'COVERED' or access_state = 'AUTHENTICATED')", "create function weekly_channel_mix_is_valid(channel_mix jsonb, expected_total integer)", "consultant_id text not null references consultants(consultant_id)",
            "create function weekly_pipeline_event_is_valid()", "new.to_stage is distinct from previous_stage", "next_to_stage is distinct from new.to_stage",
            "create trigger candidate_pipeline_event_transition_guard",
            "create trigger candidate_pipeline_events_immutable",
            "recorded_at timestamptz not null", "evidence_ref text not null check (btrim(evidence_ref) <> '')",
            "create view candidate_task_current_state as",
            "order by event_at desc, recorded_at desc, pipeline_event_id desc",
            "create function weekly_evidence_refs_are_valid(evidence_refs jsonb)", "check (weekly_evidence_refs_are_valid(evidence_refs))",
            "revision integer not null check (revision > 0)", "unique (run_id, revision)", "unique (report_snapshot_id, content_hash)", "create function weekly_report_snapshot_insert_is_valid()", "create trigger report_snapshot_insert_guard", "create function weekly_report_snapshot_is_current(target_report_snapshot_id text)", "PUBLICATION_INTENT_SNAPSHOT_NOT_CURRENT", "PUBLICATION_RECEIPT_SNAPSHOT_NOT_CURRENT", "create trigger publication_intent_snapshot_guard", "unique (report_snapshot_id, target_name)", "PUBLICATION_INTENT_RECEIPT_MISSING", "PUBLICATION_RECEIPT_INTENT_STATE_INVALID", "create function weekly_run_publication_is_complete(target_run_id text)",
            "foreign key (report_snapshot_id, expected_content_hash)",
            "references report_snapshots(report_snapshot_id, content_hash)",
            "readback_report_snapshot_id text not null references report_snapshots(report_snapshot_id)",
            "create function weekly_publication_receipt_matches_intent()",
            "create function weekly_publication_intent_transition_is_valid()",
            "create trigger publication_intent_transition_guard",
            "create trigger publication_receipt_lineage_guard",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, db)
        self.assertNotIn("current_stage text not null", db)
        self.assertNotIn("current_stage_at timestamptz not null", db)
        self.assertNotIn("create trigger weekly_runs_immutable", db)

    def test_reference_and_db_decoys_fail(self):
        files = repository_files()
        formula = sot_gate.MARKET_FORMULA
        replace_once(files, "golden_reference", formula, "market_accessibility = pool_points + precision_points")
        files["golden_reference"] += f"\n폐기 참고 문자열: {formula}\n"
        self.assertTrue(sot_gate.audit_bundle(files))

        files = repository_files()
        identity = "unique (candidate_key_hmac, position_id, hiring_cycle_id)"
        replace_once(files, "db_contract", identity, "unique (candidate_key_hmac, position_id)")
        files["db_contract"] += f"\n-- 폐기 참고 문자열: {identity}\n"
        self.assertTrue(sot_gate.audit_bundle(files))
    def test_golden_reference_negation_decoy_fails(self):
        files = repository_files()
        heading = "## Required source input\n"
        contradiction = "first 20 HMAC-unique 순서를 강제하지 않는다. 임의 표본도 허용한다.\n"
        replace_once(files, "golden_reference", heading, heading + contradiction)
        self.assertIn("GOLDEN_REFERENCE_DIGEST_DRIFT", sot_gate.audit_bundle(files))
    def test_db_publication_and_evidence_mutations_fail_semantically(self):
        db = (ROOT / "contracts/weekly-ops/db-contract-v1.sql").read_text(encoding="utf-8")
        for old, new in (("provider_receipt_ref text check (\n    provider_receipt_ref is null or btrim(provider_receipt_ref) <> ''\n  )", "provider_receipt_ref text"), ("check (coverage_status <> 'COVERED' or access_state = 'AUTHENTICATED')", "check (true)"), ("event_at timestamptz not null,\n  recorded_at timestamptz not null,\n  evidence_ref text not null check (btrim(evidence_ref) <> ''),\n  stable_event_fingerprint text not null,", "event_at timestamptz not null,\n  recorded_at timestamptz not null,\n  evidence_ref text not null,\n  stable_event_fingerprint text not null,"), ("unique (run_id, revision)", "unique (run_id, content_hash)"), ("if not weekly_report_snapshot_is_publishable(new.report_snapshot_id) then", "if false then"), ("if weekly_report_snapshot_is_publishable(intent_snapshot_id) then", "if false then")):
            with self.subTest(old=old): self.assertEqual(db.count(old), 1); self.assertIn("DB_LEDGER_OR_LINEAGE_DRIFT", sot_gate._db_errors(db.replace(old, new, 1)))
    def test_legacy_market_pipeline_and_risk_mutations_fail(self):
        mutations = (
            lambda contract: contract["market_accessibility"]["pool_points"][1].update(points=95),
            lambda contract: contract["market_accessibility"]["precision_points"][0].update(points=50),
            lambda contract: contract["market_accessibility"]["sample_evaluation_schema"].update(
                qualified_count_recomputed_from_predicates=False
            ),
            lambda contract: contract["metrics"]["active_pipeline_count"]["stages"].append("CLOSED"),
            lambda contract: contract["sourcing_coverage_risk"].update(score_formula="llm_priority"),
            lambda contract: contract["metrics"]["live_client_position_count"]["allowed_origins"].append("SCRAPED_STAGING"),
            lambda contract: contract["metrics"]["channel_outreach"].update(channels=["all"]),
            lambda contract: contract["four_week_series"].update(length=3),
            lambda contract: contract["authority"].update(managerial_directives_forbidden=False),
            lambda contract: contract["authority"].update(legacy_priority_score_fields_forbidden=False),
            lambda contract: contract["metrics"]["live_client_position_count"].update(excluded_origins=["SCRAPED_STAGING"]),
            lambda contract: contract["market_accessibility"].update(underfilled_unique_sample="SCORE_SHORT_SAMPLE"),
            lambda contract: contract["market_accessibility"].update(formula_version="unversioned"),
            lambda contract: contract["sourcing_coverage_risk"]["pipeline_gap_points"][-1].update(active_candidates_min=4),
            lambda contract: contract["sourcing_coverage_risk"].update(ineligible_lifecycle_result={"score": 0, "band": "C"}),
            lambda contract: contract["section_schemas"].pop("data_coverage"),
        )
        for mutate in mutations:
            files = repository_files()
            contract = json.loads(files["legacy_contract"])
            mutate(contract)
            files["legacy_contract"] = json.dumps(contract)
            self.assertTrue(sot_gate.audit_bundle(files))
    def test_valid_json_with_invalid_nested_shape_fails_without_exception(self):
        files = repository_files()
        runtime = json.loads(files["runtime_contract"])
        runtime["publication"] = []
        files["runtime_contract"] = json.dumps(runtime)
        self.assertIn("RUNTIME_STRUCTURE_INVALID", sot_gate.audit_bundle(files))

        files = repository_files()
        legacy = json.loads(files["legacy_contract"])
        legacy["metrics"] = []
        files["legacy_contract"] = json.dumps(legacy)
        self.assertIn("LEGACY_STRUCTURE_INVALID", sot_gate.audit_bundle(files))

        files = repository_files()
        legacy = json.loads(files["legacy_contract"])
        legacy["recent_client_positions"] = []
        files["legacy_contract"] = json.dumps(legacy)
        self.assertIn("LEGACY_STRUCTURE_INVALID", sot_gate.audit_bundle(files))
    def test_v2_sot_and_reference_meaning_reversals_fail(self):
        cases = (
            ("sot", "금지 표현:", "필수 표현:"),
            (
                "sot",
                "과거 주는 같은 형식의 raw history 또는 immutable VERIFIED snapshot만 사용한다.",
                "과거 주는 현재 상태를 네 주에 복사해 사용한다.",
            ),
            (
                "golden_reference",
                "It has no P0/P1 and no action verbs.",
                "It must have P0/P1 and imperative action verbs.",
            ),
            (
                "sot",
                "`rank`는\n캡처 순서와 같은 1..20이다.",
                "`rank`는\n임의 순서여도 된다.",
            ),
        )
        for key, old, new in cases:
            with self.subTest(key=key, new=new):
                files = repository_files()
                replace_once(files, key, old, new)
                self.assertTrue(sot_gate.audit_bundle(files))

    def test_v2_legacy_layout_and_unknown_top_level_drift_fail(self):
        files = repository_files()
        legacy = json.loads(files["legacy_contract"])
        legacy["template"]["detail_sections_collapsed"].remove("reactivated_tasks")
        files["legacy_contract"] = json.dumps(legacy)
        self.assertIn("LEGACY_GOLDEN_COLLAPSE_DRIFT", sot_gate.audit_bundle(files))

        files = repository_files()
        legacy = json.loads(files["legacy_contract"])
        legacy["unexpected_general_v1_renderer"] = {"publication_allowed": True}
        files["legacy_contract"] = json.dumps(legacy)
        self.assertIn("LEGACY_TOP_LEVEL_SHAPE_DRIFT", sot_gate.audit_bundle(files))

    def test_v2_db_market_formula_and_sample_contract_drift_fail(self):
        cases = (
            (
                "accessibility_score = (pool_points * precision_points * 100) / 2500",
                "accessibility_score = 100",
                "DB_MARKET_FORMULA_DRIFT",
            ),
            (
                "jsonb_array_length(sample_evaluations) = 20",
                "jsonb_array_length(sample_evaluations) = 19",
                "DB_MARKET_SAMPLE_DRIFT",
            ),
            (
                "where evaluation->'predicate_results'->>predicate_key = 'TRUE'",
                "where false",
                "DB_MARKET_QUALIFIED_COUNT_DRIFT",
            ), ("from jsonb_object_keys(evaluation->'predicate_results') as result_keys(key)\n                ) is not distinct from (", "from jsonb_object_keys(evaluation->'predicate_results') as result_keys(key)\n                ) = (", "DB_MARKET_SAMPLE_DRIFT"), ("primary key (run_id, collection_name, dimension_key, week_index, source_snapshot_id)", "primary key (run_id, collection_name, source_snapshot_id)", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("week_index smallint not null check (week_index between 0 and 3),\n  window_start", "week_index text not null check (week_index between 0 and 3),\n  window_start", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("week_index smallint not null check (week_index between 0 and 3),\n  week_label", "week_index text not null check (week_index between 0 and 3),\n  week_label", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("metric_iso_week text not null", "metric_iso_week text", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("check (window_start < window_end_exclusive),\n  check (window_end_exclusive = window_start + interval '7 days'),\n  check (", "check (window_start < window_end_exclusive),\n  check (window_end_exclusive = window_start + interval '8 days'),\n  check (", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("raise exception 'WEEKLY_METRIC_DERIVATION_INVALID'", "raise notice 'WEEKLY_METRIC_DERIVATION_INVALID'", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("then 'pipeline_state'", "then 'pipeline_events'", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("new.result_count_lower_bound is distinct from receipt_result_count", "false", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("publication_eligible boolean not null", "publication_eligible text not null", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("jsonb_array_length(value) = 0", "jsonb_array_length(value) < 0", "DB_MARKET_FORMULA_DRIFT"), ("weekly_market_filter_set_is_valid(filter_set) is true", "weekly_market_filter_set_is_valid(filter_set)", "DB_MARKET_FORMULA_DRIFT"), ("create trigger consultants_immutable", "create trigger consultants_mutable", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("new.active_candidate_count is distinct from expected_active_candidate_count", "new.active_candidate_count is not distinct from expected_active_candidate_count", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("join weekly_runs as target_run on target_run.run_id = new.run_id\n  join source_snapshots as source\n    on source.run_id = send.run_id and source.snapshot_id = send.source_snapshot_id\n  where send.consultant_id = new.consultant_id\n    and send.position_id", "join weekly_runs as target_run on send.run_id = new.run_id\n  join source_snapshots as source\n    on source.run_id = send.run_id and source.snapshot_id = send.source_snapshot_id\n  where send.consultant_id = new.consultant_id\n    and send.position_id", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("new.position_lifecycle = 'ACTIVE' and (", "true and (", "DB_LEDGER_OR_LINEAGE_DRIFT"), ("unique (readback_report_snapshot_id, target_name, external_object_id)", "unique (target_name, external_object_id)", "DB_LEDGER_OR_LINEAGE_DRIFT"),
        )
        for old, new, error in cases:
            with self.subTest(error=error):
                files = repository_files()
                replace_once(files, "db_contract", old, new)
                self.assertIn(error, sot_gate.audit_bundle(files))

    def test_v2_db_comment_decoy_does_not_hide_formula_drift(self):
        files = repository_files()
        formula = "accessibility_score = (pool_points * precision_points * 100) / 2500"
        replacement = "accessibility_score = 100 -- " + formula
        replace_once(files, "db_contract", formula, replacement)
        self.assertIn("DB_MARKET_FORMULA_DRIFT", sot_gate.audit_bundle(files))

    def test_v2_db_contract_recomputes_unique_sample_and_points(self):
        db = repository_files()["db_contract"]
        required = (
            "weekly_market_sample_is_valid",
            "count(distinct evaluation->>'candidate_key_hmac') = 20",
            "weekly_market_qualified_count(sample_evaluations, must_have_predicates)", "jsonb_typeof(evaluation->'candidate_key_hmac') = 'string'", "jsonb_typeof(evaluation->'rank') = 'number'", "is not distinct from", "weekly_market_filter_set_is_valid(filter_set) is true", "jsonb_array_length(value) = 0", "coverage_risk_score = recency_points + pipeline_gap_points + scarcity_points", "MARKET_COVERAGE_RISK_DERIVATION_INVALID", "weekly_consultant_position_focus_is_valid", "target_run.run_id = new.run_id", "source.fetched_at <= target_run.meeting_at", "new.position_lifecycle = 'ACTIVE' and (", "create trigger consultants_immutable", "weekly_report_snapshot_is_publishable", "unique (readback_report_snapshot_id, target_name, external_object_id)",
            "pool_points = case",
            "precision_points = case",
        )
        for token in required:
            with self.subTest(token=token):
                self.assertIn(token, db)

    def test_v2_briefing_style_and_checker_forbid_managerial_drift(self):
        files = repository_files()
        briefing = files.get("briefing_style", "")
        self.assertIn("Do not issue management priorities or action directives.", briefing)
        self.assertNotIn("이번 주 고객 액션 — ordered by deterministic priority.", briefing)
        mutated = briefing.replace(
            "Do not issue management priorities or action directives.",
            "Issue management priorities and action directives.",
            1,
        )
        self.assertNotEqual(briefing, mutated)
        files["briefing_style"] = mutated
        self.assertIn("BRIEFING_STYLE_AUTHORITY_DRIFT", sot_gate.audit_bundle(files)); files = repository_files(); replace_once(files, "briefing_style", "chronological facts, never an LLM priority list", "모델이 판단한 경영 중요도 순"); self.assertIn("BRIEFING_STYLE_DIGEST_DRIFT", sot_gate.audit_bundle(files)); files = repository_files(); replace_once(files, "prompt_contract", "Missing/stale/error is NOT_RUN/PARTIAL, never zero", "Missing/stale/error may be reported as zero"); self.assertIn("PROMPT_CONTRACT_DIGEST_DRIFT", sot_gate.audit_bundle(files)); files = repository_files(); replace_once(files, "brief_renderer", "## 이번 주 고객 액션", "## 일반 Weekly v1 계약 파손"); self.assertIn("BRIEF_RENDERER_DIGEST_DRIFT", sot_gate.audit_bundle(files))

    def test_v2_mutation_harness_proves_clean_baseline_and_copies_db(self):
        script = (ROOT / "scripts/acceptance-weekly-ops-skill.sh").read_text(encoding="utf-8")
        self.assertIn('DB_CONTRACT=contracts/weekly-ops/db-contract-v1.sql', script)
        self.assertIn('cp "$DB_CONTRACT"', script)
        self.assertIn("mutation baseline unit contracts failed", script)
        self.assertIn('[ "$fail" -eq 0 ] || { printf \'CHECKED: %s\\n\' "$checked"; exit "$fail"; }', script)
        self.assertIn("mutation suite did not collect tests", script)

    def test_v3_markdown_comments_and_contradictions_do_not_satisfy_rules(self):
        cases = (
            (
                "sot",
                "과거 주는 같은 형식의 raw history 또는 immutable VERIFIED snapshot만 사용한다.",
                "과거 주는 현재 상태를 네 주에 복제한 값도 사용한다.\n<!-- 과거 주는 같은 형식의 raw history 또는 immutable VERIFIED snapshot만 사용한다. -->",
                "SOT_FOUR_WEEK_SOURCE_DRIFT",
            ),
            (
                "sot",
                "Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:\n\n- `RECOMMENDATION_PENDING`\n- `CLIENT_REVIEW`",
                "<!--\nPre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:\n\n- `RECOMMENDATION_PENDING`\n- `CLIENT_REVIEW`\n-->\nPre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:\n\n- `OFFER`\n- `FINAL_ACCEPTED`",
                "SOT_PIPELINE_SET_DRIFT:Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:",
            ),
            (
                "sot",
                "고객 Gmail의\n`REQUESTED|POSITION_SHARED` evidence와 canonical position이 연결돼야 고객 origin으로 승격할 수 있다.",
                "고객 evidence 없이도 고객 origin으로 승격한다.\n<!-- 고객 Gmail의\n`REQUESTED|POSITION_SHARED` evidence와 canonical position이 연결돼야 고객 origin으로 승격할 수 있다. -->",
                "SOT_SCRAPED_BOUNDARY_DRIFT",
            ),
        )
        for key, old, new, error in cases:
            with self.subTest(error=error):
                files = repository_files()
                replace_once(files, key, old, new)
                self.assertIn(error, sot_gate.audit_bundle(files))

        files = valid_files()
        files["sot"] = files["sot"].replace("HARD 0", "SOFT 0\n<!-- HARD 0 -->", 1)
        self.assertIn("SOT_TOKEN_MISSING:HARD 0", sot_gate.audit_bundle(files))

        files = repository_files()
        files["sot"] = files["sot"].replace(
            "`(candidate_key_hmac, position_id, hiring_cycle_id)`",
            "`(candidate_key_hmac, position_id, hiring_cycle_id)`\n\n실제 중복 제거는 외부 ClickUp task ID만 사용한다.",
            1,
        )
        self.assertIn("SOT_CANDIDATE_IDENTITY_DRIFT", sot_gate.audit_bundle(files))

    def test_v3_managerial_and_publication_overrides_fail(self):
        files = repository_files()
        files["briefing_style"] += "\n7. 이번 주 우선 연락 — 고객에게 오늘 연락한다.\n"
        self.assertIn("BRIEFING_STYLE_AUTHORITY_DRIFT", sot_gate.audit_bundle(files))

        files = repository_files()
        rule = "return `NOT_RUN`; do not route a Golden request through the general v1 renderer."
        replace_once(files, "skill", rule, rule + " A later operator may publish v1 without readback.")
        self.assertIn("SKILL_GOLDEN_FAIL_CLOSED_DRIFT", sot_gate.audit_bundle(files)); files = repository_files(); files["skill"] += "\n## Unsafe\nA later operator may publish v1 without readback."; self.assertIn("SKILL_GOLDEN_FAIL_CLOSED_DRIFT", sot_gate.audit_bundle(files))
        for key, rule in (("skill", "emit exactly one diagnostic for each fixed channel on every run"), ("prompt_contract", "Candidate display names may be resolved only at write time"), ("golden_reference", "Do not write from this legacy block.")): files = repository_files(); files[key] = files[key].replace(rule, "unsafe legacy ambiguity", 1); self.assertTrue(any(error.startswith(f"REPOSITORY_LINK_MISSING:{key}:") for error in sot_gate.audit_bundle(files)))

    def test_v3_sql_literals_do_not_satisfy_executable_rules(self):
        cases = (
            (
                "accessibility_score = (pool_points * precision_points * 100) / 2500",
                "accessibility_score = accessibility_score and 'accessibility_score = (pool_points * precision_points * 100) / 2500' is not null",
                "DB_MARKET_FORMULA_DRIFT",
            ),
            (
                "count(distinct evaluation->>'candidate_key_hmac') = 20",
                "true and $decoy$count(distinct evaluation->>'candidate_key_hmac') = 20$decoy$ is not null",
                "DB_MARKET_SAMPLE_DRIFT",
            ),
            (
                "where evaluation->'predicate_results'->>predicate_key = 'TRUE'",
                "where false and $decoy$where evaluation->'predicate_results'->>predicate_key = 'TRUE'$decoy$ is not null",
                "DB_MARKET_QUALIFIED_COUNT_DRIFT",
            ),
            ("accessibility_score = (pool_points * precision_points * 100) / 2500", "accessibility_score = 1 and $$accessibility_score = (pool_points * precision_points * 100) / 2500$$ is not null", "DB_MARKET_FORMULA_DRIFT"),
        )
        for old, new, error in cases:
            with self.subTest(error=error):
                files = repository_files()
                replace_once(files, "db_contract", old, new)
                self.assertIn(error, sot_gate.audit_bundle(files))

    def test_v3_legacy_nested_shape_and_fail_closed_values_are_exact(self):
        mutations = (
            lambda contract: contract["template"].update(runtime_callable="publish_without_readback"),
            lambda contract: contract["hooks"].append("execute_without_readback"),
            lambda contract: contract["four_week_series"].update(contiguous_iso_weeks=False),
            lambda contract: contract["recent_client_positions"]["allowed_origins"].append("SCRAPED_STAGING"),
            lambda contract: contract["pipeline"].update(latest_event_at_cutoff_wins=False),
            lambda contract: contract["fail_closed"].update(publication_without_readback_is_partial=False), lambda contract: contract["privacy"].update(forbidden_targets_for_candidate_display_name=["git"]),
        )
        for mutate in mutations:
            files = repository_files()
            contract = json.loads(files["legacy_contract"])
            mutate(contract)
            files["legacy_contract"] = json.dumps(contract)
            self.assertTrue(sot_gate.audit_bundle(files))

        files = repository_files()
        contract = json.loads(files["legacy_contract"])
        contract["metrics"]["new_task_count"] = []
        files["legacy_contract"] = json.dumps(contract)
        self.assertIn("LEGACY_STRUCTURE_INVALID", sot_gate.audit_bundle(files))

    def test_v3_all_required_weekly_metrics_exist_in_json_and_sql(self):
        required = {
            "live_client_position_count",
            "new_task_count",
            "reactivated_task_count",
            "active_pipeline_count",
            "interview_pipeline_count",
            "pre_interview_pipeline_count",
            "channel_outreach",
        }
        contract = json.loads(repository_files()["legacy_contract"])
        self.assertEqual(set(contract["metrics"]), required); self.assertEqual(contract["privacy"]["forbidden_targets_for_candidate_display_name"], ["canonical_input", "git", "email", "admin_web", "logs", "hashes", "receipts", "exceptions", "review_bundle"])
        db = repository_files()["db_contract"]
        for metric in required:
            with self.subTest(metric=metric):
                self.assertIn(f"'{metric}'", db)

    def test_v3_mutation_harness_rejects_import_failures(self):
        script = (ROOT / "scripts/acceptance-weekly-ops-skill.sh").read_text(encoding="utf-8")
        self.assertIn("mutation infrastructure failure", script)
        self.assertIn("ImportError|ModuleNotFoundError|SyntaxError", script)
        self.assertIn("IndentationError|TabError|unittest.loader._FailedTest", script)
if __name__ == "__main__":
    unittest.main()
