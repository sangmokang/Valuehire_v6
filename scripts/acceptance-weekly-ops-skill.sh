#!/usr/bin/env bash
# acceptance-weekly-ops-skill.sh — Weekly Ops 공용 Skill과 fail-closed mutation 게이트.
# 종료값: 0=PASS, 1=FAIL, 2=NOT_RUN. CHECKED 0건은 통과하지 않는다.
set -uo pipefail
if [ "${1:---full}" != "--full" ]; then
  printf 'NOT_RUN: unsupported mode %s\nCHECKED: 0\n' "$1"
  exit 2
fi
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf 'NOT_RUN: git repository unavailable\nCHECKED: 0\n'
  exit 2
}
cd "$REPO" || {
  printf 'NOT_RUN: repository root unavailable\nCHECKED: 0\n'
  exit 2
}
CANONICAL=.agents/skills/weekly-ops
GATE=$CANONICAL/scripts/weekly_gate.py
ACTIVITY=$CANONICAL/scripts/activity_gate.py
CONTRACT_GATE=$CANONICAL/scripts/contract_gate.py
RENDERER=$CANONICAL/scripts/brief_renderer.py
OPERATING=$CANONICAL/scripts/operating_gate.py
TESTS=tests/weekly_ops
CONTRACT=contracts/weekly-ops/runtime-contract-v1.json
GOLDEN_CONTRACT=contracts/weekly-ops/notion-golden-sample-v1.json
DB_CONTRACT=contracts/weekly-ops/db-contract-v1.sql
GOLDEN_SPEC=$CANONICAL/references/notion-golden-sample.md
checked=0
fail=0
pass_check() {
  checked=$((checked + 1))
  printf 'PASS: %s\n' "$1"
}
fail_check() {
  checked=$((checked + 1))
  fail=1
  printf 'FAIL: %s\n' "$1"
}
for required in \
  "$CANONICAL/SKILL.md" "$GATE" "$ACTIVITY" "$CONTRACT_GATE" "$RENDERER" "$OPERATING" \
  "$TESTS/fixtures.py" "$TESTS/test_weekly_gate.py" \
  "$TESTS/test_weekly_gate_adversarial.py" "$TESTS/test_weekly_sot_contract.py" "$TESTS/test_weekly_db_lineage_contract.py" \
  "$CANONICAL/scripts/sot_gate.py" "$CANONICAL/scripts/schema_gate.py" "$CANONICAL/references/data-contract.md" "$CANONICAL/references/adversarial-review.md" docs/sot/weekly-ops-contract.md "$CONTRACT" contracts/weekly-ops/db-contract-v1.sql; do
  if [ -f "$required" ] && [ -s "$required" ] && [ ! -L "$required" ] && git ls-files --error-unmatch "$required" >/dev/null 2>&1; then
    pass_check "required file $required"
  else
    fail_check "required file invalid $required"
  fi
done
python3 "$CANONICAL/scripts/sot_gate.py" --repo "$REPO" && pass_check "Weekly SOT semantics are wired" || fail_check "Weekly SOT semantics are missing or drifting"
for required in "$GOLDEN_CONTRACT" "$GOLDEN_SPEC"; do
  if [ -f "$required" ] && [ -s "$required" ] && [ ! -L "$required" ]; then
    pass_check "required Golden Sample file $required"
  else
    fail_check "required Golden Sample file invalid $required"
  fi
done

if [ -f "$CANONICAL/SKILL.md" ] && [ ! -L "$CANONICAL/SKILL.md" ]; then
  pass_check "engine-neutral canonical skill is present under .agents/skills"
else
  fail_check "engine-neutral canonical skill is not a regular file"
fi

CODEX_ADAPTER=.codex/skills/weekly-ops/SKILL.md
CODEX_UI=.codex/skills/weekly-ops/agents/openai.yaml
CANONICAL_UI=$CANONICAL/agents/openai.yaml
codex_file_count=$(find .codex/skills/weekly-ops -type f 2>/dev/null | wc -l | tr -d ' ')
if [ -f "$CODEX_ADAPTER" ] && [ ! -L "$CODEX_ADAPTER" ] && \
   [ -f "$CODEX_UI" ] && [ ! -L "$CODEX_UI" ] && \
   [ -f "$CANONICAL_UI" ] && [ ! -L "$CANONICAL_UI" ] && \
   grep -q '`\.agents/skills/weekly-ops/SKILL.md`' "$CODEX_ADAPTER" && \
   grep -q '\$weekly-ops' "$CODEX_UI" && cmp -s "$CODEX_UI" "$CANONICAL_UI" && \
   [ "$codex_file_count" = 2 ]; then
  pass_check "Codex project adapter discovers only the canonical skill"
else
  fail_check "Codex project adapter is missing, drifting, or contains copied assets"
fi

CLAUDE_ADAPTER=.claude/skills/weekly-ops/SKILL.md
if [ -f "$CLAUDE_ADAPTER" ] && [ ! -L "$CLAUDE_ADAPTER" ] && \
   grep -q '`\.agents/skills/weekly-ops/SKILL.md`' "$CLAUDE_ADAPTER" && \
   ! find .claude/skills/weekly-ops -mindepth 1 -maxdepth 1 ! -name SKILL.md | grep -q .; then
  pass_check "Claude adapter points only to canonical skill"
else
  fail_check "Claude adapter is missing, drifting, or contains copied assets"
fi

frontmatter=$(sed -n '1,/^---$/p' "$CANONICAL/SKILL.md" 2>/dev/null)
if printf '%s\n' "$frontmatter" | grep -q '^name: weekly-ops$' && \
   printf '%s\n' "$frontmatter" | grep -q '^description: .[^[:space:]]'; then
  pass_check "skill frontmatter identifies weekly-ops"
else
  fail_check "skill frontmatter invalid"
fi

if python3 -m json.tool "$CONTRACT" >/dev/null 2>&1; then
  pass_check "runtime contract parses as JSON"
else
  fail_check "runtime contract JSON invalid"
fi

if python3 -m json.tool "$GOLDEN_CONTRACT" >/dev/null 2>&1; then
  pass_check "Notion Golden Sample contract parses as JSON"
else
  fail_check "Notion Golden Sample contract JSON invalid"
fi

if python3 - "$GOLDEN_CONTRACT" "$GOLDEN_SPEC" contracts/weekly-ops/db-contract-v1.sql <<'PY'
import json
from pathlib import Path
import sys

contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
spec = Path(sys.argv[2]).read_text(encoding="utf-8")
db = Path(sys.argv[3]).read_text(encoding="utf-8")
assert contract["contract_version"] == "notion-weekly-golden-v1"
assert contract["authority"]["managerial_directives_forbidden"] is True
assert contract["authority"]["llm_may_not_choose_work"] is True and contract["authority"]["legacy_priority_score_fields_forbidden"] is True
assert contract["four_week_series"]["length"] == 4
assert contract["four_week_series"]["missing_is_never_zero"] is True
assert contract["four_week_series"]["trend_requires_verified_points"] == 3
metrics = contract["metrics"]
assert metrics["live_client_position_count"]["excluded_origins"] == ["SCRAPED_STAGING", "INTERNAL_CREATED"]
identity = ["candidate_key_hmac", "position_id", "hiring_cycle_id"]
assert metrics["new_task_count"]["dedupe_key"] == identity and contract["pipeline"]["dedupe_key"] == identity
assert metrics["new_task_count"]["reactivation_is_separate_metric"] is True
assert set(metrics) == {"live_client_position_count", "new_task_count", "reactivated_task_count", "active_pipeline_count", "interview_pipeline_count", "pre_interview_pipeline_count", "channel_outreach"}
assert metrics["channel_outreach"]["channels"] == ["saramin", "jobkorea", "linkedin_rps"]
market = contract["market_accessibility"]
assert market["formula_version"] == "market-accessibility-v2" and market["evaluated_sample_size"] == 20 and market["sample_selection"] == "ordered_first_20_hmac_unique" and market["underfilled_unique_sample"] == "UNRANKED" and market["pool_points_input"] == "result_count_lower_bound" and market["result_count_source"] == "immutable_pass_bound_provider_receipt" and "provider_result_receipt_ref" in market["required_fields"] and market["precision_rate_formula"] == "qualified_sample_matches / evaluated_sample_size" and market["precision_points_input"] == "precision_rate" and market["score_formula"] == "(pool_points * precision_points * 100) // 2500" and market["zero_qualified_override"] == {"score": 0, "band": "HARD"} and market["missing_or_partial_result"] == "UNRANKED" and market["source_system"] == "linkedin_rps" and market["filter_dimensions_require_nonempty_string_arrays"] is True and market["ordered_result_snapshot_hash_equals_source_raw_hash"] is True
assert market["sample_evaluation_schema"]["qualified_count_recomputed_from_predicates"] is True
assert contract["sourcing_coverage_risk"]["score_formula"] == (
    "recency_points + pipeline_gap_points + scarcity_points"
) and contract["sourcing_coverage_risk"]["formula_version"] == "sourcing-coverage-risk-v1" and contract["sourcing_coverage_risk"]["ineligible_lifecycle_result"] == {"score": None, "band": "UNRANKED", "reason": "INELIGIBLE_LIFECYCLE"} and contract["sourcing_coverage_risk"]["pipeline_gap_points"][-1] == {"active_candidates_min": 3, "points": 0} and contract["sourcing_coverage_risk"]["inputs_recomputed_by_db"] is True
assert contract["template"]["section_order"] == ["four_week_kpis", "recent_client_positions", "market_accessibility", "position_changes", "candidate_sourcing", "new_tasks", "reactivated_tasks", "pipeline_movements", "active_pipeline", "pre_interview_pipeline", "data_coverage"] and set(contract["section_schemas"]) == set(contract["template"]["section_order"]) and contract["section_schemas"]["candidate_sourcing"]["required_collections"] == ["channel_coverage", "consultant_focus", "excluded_rows"] and contract["section_schemas"]["data_coverage"]["required_collections"] == ["requirement_status", "post_cutoff_alerts"] and {"market_formula_version", "coverage_risk_formula_version"}.issubset(contract["section_schemas"]["market_accessibility"]["row_required_fields"]) and {"week_label", "metric_iso_week"}.issubset(contract["section_schemas"]["four_week_kpis"]["row_required_fields"])
assert contract["privacy"]["candidate_display_name_allowed_only_in_user_authorized_private_notion"] is True and contract["privacy"]["forbidden_targets_for_candidate_display_name"] == ["canonical_input", "git", "email", "admin_web", "logs", "hashes", "receipts", "exceptions", "review_bundle"]
assert contract["fail_closed"]["unknown_is_not_zero"] is True
for phrase in (
    "최근 인입 포지션", "시장 접근성", "후보자 소싱", "지난주 신규 Task",
    "지난주 재활성 Task", "활성 Pipeline", "NOTION_WEEKLY_GOLDEN_SAMPLE_V1", "즉시 실행",
):
    assert phrase in spec
assert "hiring_cycle_id text not null" in db and "unique (candidate_key_hmac, position_id, hiring_cycle_id)" in db and "weekly_market_sample_is_valid" in db and "weekly_market_filter_set_is_valid(filter_set) is true" in db and "primary key (run_id, collection_name, dimension_key, week_index, source_snapshot_id)" in db and "weekly_channel_mix_is_valid" in db and "target_run.run_id = new.run_id" in db and "source.fetched_at <= target_run.meeting_at" in db and "new.position_lifecycle = 'ACTIVE' and (" in db and "weekly_report_snapshot_is_publishable" in db and "publication_eligible boolean not null" in db and "MARKET_COVERAGE_RISK_DERIVATION_INVALID" in db and "WEEKLY_METRIC_DERIVATION_INVALID" in db and "canonical_position_state_events" in db and "linkedin_market_result_receipts" in db and "metric_iso_week text not null" in db and "unique (readback_report_snapshot_id, target_name, external_object_id)" in db
for table in (
    "candidate_position_tasks", "candidate_pipeline_events", "weekly_metric_snapshots",
    "linkedin_market_search_snapshots",
):
    assert f"create table {table}" in db
PY
then
  pass_check "Notion Golden Sample prompt, metric, DB, and fail-closed contracts are machine-checked"
else
  fail_check "Notion Golden Sample contract drifted"
fi

if python3 - "$CONTRACT" "$CANONICAL/SKILL.md" "$CANONICAL/references/prompt-contract.md" "$GATE" <<'PY'
import importlib.util
import json
from pathlib import Path
import sys

contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
skill = Path(sys.argv[2]).read_text(encoding="utf-8")
prompt = Path(sys.argv[3]).read_text(encoding="utf-8")
gate_path = Path(sys.argv[4])
spec = importlib.util.spec_from_file_location("weekly_gate_contract_check", gate_path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
expected_states = {
    "AUTHENTICATED",
    "AUTH_REQUIRED",
    "TUTORIAL_OR_DEMO",
    "AUTOMATION_DENIED",
    "CHALLENGE",
    "MISSING_PROFILE",
    "STALE_PAGE",
}
sources = {item["channel"]: item for item in contract["outreach_sources"]}
assert set(contract["outreach_access_states"]) == expected_states
assert set(sources) == {"jobkorea", "saramin", "linkedin_rps"}
assert "integrated_login" in sources["jobkorea"]["invalid_surfaces"]
assert "tutorial" in sources["saramin"]["invalid_surfaces"]
assert sources["linkedin_rps"]["preferred_surface"] == "inmail_audit_report_or_equivalent_export" and sources["linkedin_rps"]["navigation_boundary"] == "existing_authenticated_aside_tab_only"
assert sources["jobkorea"]["accepted_surface_kind"] == "position_offer_history" and sources["jobkorea"]["operator_url"] == "https://www.jobkorea.co.kr/corp/person/position" and sources["jobkorea"]["navigation"] == "operator_url > sent_history > position_offer_history"
assert sources["saramin"]["accepted_surface_kind"] == "detailed_usage_history" and sources["saramin"]["operator_url"] == "https://billing.saramin.co.kr/manage/7791926?svcAypdTgtNos=31463970"
assert set(sources["linkedin_rps"]["accepted_surface_kind"]) == {
    "inmail_audit_report", "recruiter_inbox_thread"
}
assert all("open_tab" in source["invalid_surfaces"] for source in sources.values())
diagnostic = contract["outreach_diagnostic_contract"]
assert diagnostic["require_all_channels_for_portal_events"] is True
assert diagnostic["require_all_channels_on_every_run"] is True
assert diagnostic["diagnostic_and_event_snapshot_must_match"] is True
assert "covered_provider_actor_refs" in diagnostic["required_fields"]
roster = contract["consultant_roster_contract"]
assert roster["required_when_outreach_capabilities_pass_or_events_exist"] is True
assert roster["provider_actor_unique_per_channel"] is True
assert roster["event_provider_actor_must_match_roster"] is True
assert roster["linkedin_actor_must_equal_seat"] is True
assert roster["provider_receipt_dedupe_key"] == ["channel", "provider_receipt_ref"]
assert roster["coverage_gap_comparison_status"] == "NOT_COMPARABLE"
assert roster["unread_account_metric"] == "NOT_RUN"
assert roster["required_output_collections"] == [
    "channel_coverage", "consultant_focus", "excluded_rows"
]
assert roster["zero_result_scope"] == "accepted_sent_inside_closed_weekly_window" and contract["golden_projection_policy"]["legacy_priority_score_excluded"] is True and contract["golden_projection_policy"]["required_output_collection_section"] == "candidate_sourcing" and contract["golden_projection_policy"]["post_cutoff_projection_section"] == "data_coverage"
focus_schema = contract["consultant_focus_output_schema"]
assert focus_schema["shape"] == "consultant_summary_with_nested_positions"
assert focus_schema["top_level_required_fields"] == [
    "consultant_id", "consultant_display", "verified_sent_count", "unique_candidate_count",
    "active_days", "channel_mix", "comparison_status", "positions",
]
assert focus_schema["position_required_fields"] == [
    "position_id", "company", "title", "verified_sent_count", "unique_candidate_count",
    "active_days", "channels", "channel_mix", "evidence_refs", "focus_share", "grass_evidence",
]
assert focus_schema["db_projection"] == (
    "flatten_parent_consultant_id_plus_nested_position_id_without_recompute"
)
assert focus_schema["grass_projection_source"] == "consultant_focus.positions"
assert focus_schema["forbid_rejoin_or_recompute"] is True
assert "consultant_focus[].positions[]: position_id" in prompt
assert "consultant_id + positions[].position_id" in prompt
assert contract["score_points"] == gate.DIFFICULTY_POINTS and next(row for row in contract["career_sources"] if row["company"] == "Codeit")["empty_allowlist_behavior"] == "NOT_RUN" and all(row["talent_pool_behavior"] == "exclude_from_active_requisition" for row in contract["career_sources"]) and contract["intent_origin_mapping"] == {"REQUESTED": "CLIENT_REQUESTED", "POSITION_SHARED": "CLIENT_SHARED", "REQUIREMENT_CHANGED": "EXISTING_CLIENT_POSITION_ONLY_NO_PROMOTION", "PIPELINE_FEEDBACK": "EXISTING_CLIENT_POSITION_ONLY_NO_PROMOTION", "REFERENCE_ONLY": "NO_PROMOTION", "NONE": "NO_PROMOTION"}
assert contract["consultant_focus_version"] == gate.CONSULTANT_FOCUS_VERSION
assert contract["dedupe_rule_version"] == "weekly-dedupe-v1"
assert contract["zero_result_contract"]["rule_version"] == "weekly-zero-result-v1"
assert contract["zero_result_contract"]["collections"] == ["positions", "position_state", "outreach_events", "pipeline_events", "pipeline_state"]
operating = contract["operating_snapshot_contract"]
assert operating["required_when_db_read_pass"] is True
assert operating["closed_week_must_equal_run_window"] is True
assert operating["current_funnel_is_not_weekly_performance"] is True
assert operating["source_uri_pattern"] == "rpc:weekly_brief_snapshot:{meeting_date}"
assert operating["run_timezone"] == "Asia/Seoul"
assert operating["run_window_requires_monday_midnight_and_seven_days"] is True
assert operating["source_fetched_at_not_after_meeting"] is True
assert operating["exact_key_sets"] is True
assert contract["weekly_window"]["start"] == "previous ISO-week Monday at 00:00"
assert contract["weekly_window"]["end_exclusive"] == "current ISO-week Monday at 00:00"
publication = contract["publication"]
assert contract["clickup"]["list_url"] == "https://app.clickup.com/9018789656/v/li/901814621569" and publication["notion_parent_url"] == "https://app.notion.com/p/valueconnect/1975f52f80964fb1996eed3b0226e633?v=c5aa2180f3b24feda8408f20547aed54"
assert publication["data_and_publication_verdicts_separate"] is True
assert publication["publication_report_outside_content_hash"] is True
assert publication["canonical_brief_warns_not_publication_complete"] is True
assert publication["publication_report_names_contract_errors"] is True and {"target_name", "target_id"}.issubset(publication["receipt_required_fields"])
for required in (
    "stable thread/message identity", "screenshots", "AUTOMATION_DENIED",
    "provider_actor_ref", "internal position-share email", "NOT_RUN coverage gap",
):
    assert required in skill + prompt
PY
then
  pass_check "outreach browser and consultant-roster contracts are machine-checked"
else
  fail_check "outreach browser readback contract drifted"
fi

if python3 -m py_compile "$CANONICAL"/scripts/*.py "$TESTS"/*.py; then
  pass_check "weekly gates compile"
else
  fail_check "weekly gates do not compile"
fi

if python3 - "$CANONICAL/scripts" "$TESTS" <<'PY'
import ast
from pathlib import Path
import sys

FILE_HARD_LIMIT = 600
FUNCTION_HARD_LIMIT = 100


def file_within_budget(text):
    return len(text.splitlines()) <= FILE_HARD_LIMIT


assert file_within_budget("line\n" * 600) is True
assert file_within_budget("line\n" * 601) is False
paths = sorted(
    path
    for raw_root in sys.argv[1:]
    for path in Path(raw_root).rglob("*.py")
    if "__pycache__" not in path.parts
)
assert paths, "no Python files discovered for hard-limit enforcement"
for path in paths:
    text = path.read_text(encoding="utf-8")
    assert file_within_budget(text), f"{path}: file hard limit exceeded"
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = node.end_lineno - node.lineno + 1
            assert size <= FUNCTION_HARD_LIMIT, f"{path}:{node.lineno} function={size}"
PY
then
  pass_check "weekly code respects 600-line file and 100-line function hard limits"
else
  fail_check "weekly code or hard-limit boundary contract failed"
fi

unit_output=$(mktemp) || {
  printf 'NOT_RUN: unit output tempfile unavailable\nCHECKED: %s\n' "$checked"
  exit 2
}
TEMP_ROOT=$(mktemp -d) || {
  rm -f "$unit_output"
  printf 'NOT_RUN: mutation tempdir unavailable\nCHECKED: %s\n' "$checked"
  exit 2
}
cleanup() {
  rm -f -- "$unit_output"
  if [ -d "$TEMP_ROOT" ] && [ "${TEMP_ROOT##*/}" != "$TEMP_ROOT" ] && \
     printf '%s' "${TEMP_ROOT##*/}" | grep -q '^tmp\.'; then
    find "$TEMP_ROOT" -depth -delete
  else
    printf 'FAIL: unsafe temp path retained: %s\n' "$TEMP_ROOT"
    exit 1
  fi
}
trap cleanup EXIT

if python3 -m unittest discover -s "$TESTS" -v >"$unit_output" 2>&1 && \
   grep -qE '^Ran ([1-9][0-9]*) tests' "$unit_output" && grep -q '^OK$' "$unit_output"; then
  pass_check "weekly unit contracts execute and pass"
else
  fail_check "weekly unit contracts failed or collected zero tests"
  sed -n '1,160p' "$unit_output"
fi

MUTATION_BASE="$TEMP_ROOT/baseline"
baseline_output="$TEMP_ROOT/baseline.out"
mkdir -p "$MUTATION_BASE/.agents/skills" "$MUTATION_BASE/tests" "$MUTATION_BASE/docs/sot" "$MUTATION_BASE/contracts/weekly-ops" "$MUTATION_BASE/.github/workflows" "$MUTATION_BASE/scripts"
cp -R "$CANONICAL" "$MUTATION_BASE/.agents/skills/weekly-ops"
cp -R "$TESTS" "$MUTATION_BASE/tests/weekly_ops"
cp docs/sot/{weekly-ops-contract.md,INDEX.md,verification-commands.md,mechanism-registry.yaml} "$MUTATION_BASE/docs/sot"
cp "$GOLDEN_CONTRACT" "$CONTRACT" "$MUTATION_BASE/contracts/weekly-ops"
cp "$DB_CONTRACT" "$MUTATION_BASE/contracts/weekly-ops"
cp .github/workflows/verify.yml "$MUTATION_BASE/.github/workflows"
cp scripts/acceptance-weekly-ops-skill.sh "$MUTATION_BASE/scripts"
if (cd "$MUTATION_BASE" && python3 -m unittest discover -s tests/weekly_ops -v) >"$baseline_output" 2>&1 && \
   grep -qE '^Ran ([1-9][0-9]*) tests' "$baseline_output" && grep -q '^OK$' "$baseline_output"; then
  pass_check "mutation baseline unit contracts execute and pass"
else
  fail_check "mutation baseline unit contracts failed"
  sed -n '1,80p' "$baseline_output"
fi; [ "$fail" -eq 0 ] || { printf 'CHECKED: %s\n' "$checked"; exit "$fail"; }
prepare_mutation() {
  local destination="$TEMP_ROOT/$1"
  cp -R "$MUTATION_BASE" "$destination" || return 1
  printf '%s\n' "$destination"
}
mutate_exact() {
  local file="$1" old="$2" new="$3"
  python3 - "$file" "$old" "$new" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
old, new = sys.argv[2], sys.argv[3]
text = path.read_text(encoding="utf-8")
if text.count(old) != 1:
    raise SystemExit(3)
path.write_text(text.replace(old, new), encoding="utf-8")
PY
}
expect_mutation_red() {
  local name="$1" destination="$2"
  local mutation_output="$destination/mutation.out"
  if (cd "$destination" && python3 -m unittest discover -s tests/weekly_ops -v) >"$mutation_output" 2>&1; then
    fail_check "mutation $name survived"
  elif ! grep -qE '^Ran ([1-9][0-9]*) tests' "$mutation_output"; then
    fail_check "mutation suite did not collect tests: $name"
    sed -n '1,80p' "$mutation_output"
  elif grep -qE 'ImportError|ModuleNotFoundError|SyntaxError|IndentationError|TabError|unittest.loader._FailedTest|Failed to import test module|No module named' "$mutation_output"; then
    fail_check "mutation infrastructure failure: $name"
    sed -n '1,80p' "$mutation_output"
  else
    pass_check "mutation $name is killed by tests"
  fi
}
case_dir=$(prepare_mutation scraped-cap)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  'priority = min(20, priority)' 'priority = min(100, priority)'; then
  expect_mutation_red "scraped priority cap removal" "$case_dir"
else
  fail_check "scraped priority mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation capability-fail-open)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'if name in REQUIRED_CAPABILITIES and status != "PASS":' \
  'if name in REQUIRED_CAPABILITIES and status == "PASS":'; then
  expect_mutation_red "required capability fail-open" "$case_dir"
else
  fail_check "capability mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation readback-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'target["report_snapshot_id"] != snapshot_id' 'False' && \
   mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'target["content_hash"] != content_hash' 'False'; then
  expect_mutation_red "publication readback bypass" "$case_dir"
else
  fail_check "readback mutations were not applied exactly once"
fi
case_dir=$(prepare_mutation required-target-omission)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'REQUIRED_PUBLICATION_TARGETS = {"database", "clickup", "notion", "admin_web", "email"}' \
  'REQUIRED_PUBLICATION_TARGETS = {"database"}'; then
  expect_mutation_red "required publication target removal" "$case_dir"
else
  fail_check "required target mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation pii-value-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'return bool(EMAIL_PATTERN.search(value) or PHONE_PATTERN.search(value))' \
  'return False'; then
  expect_mutation_red "rendered PII value bypass" "$case_dir"
else
  fail_check "PII value mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation lineage-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  'if any(not isinstance(ref, str) or ref not in valid_evidence_refs for ref in position["evidence_refs"]):' \
  'if False:'; then
  expect_mutation_red "position evidence lineage bypass" "$case_dir"
else
  fail_check "lineage mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation origin-intent-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  'if position["intent"] not in ORIGIN_INTENTS[position["origin"]]:' 'if False:'; then
  expect_mutation_red "position origin-intent mapping bypass" "$case_dir"
else
  fail_check "origin-intent mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation source-status-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'if snapshot["status"] != "PASS":' 'if False:'; then
  expect_mutation_red "non-PASS source status bypass" "$case_dir"
else
  fail_check "source status mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-receipt-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/activity_gate.py" \
  'if event["status"] == "SENT" and event["provider_receipt_ref"] not in snapshot_evidence_refs.get(' \
  'if False and event["provider_receipt_ref"] not in snapshot_evidence_refs.get('; then
  expect_mutation_red "outreach receipt lineage bypass" "$case_dir"
else
  fail_check "outreach receipt mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-surface-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/activity_gate.py" \
  'if event["status"] == "SENT" and not diagnostic_allows_event(' \
  'if False and not diagnostic_allows_event('; then
  expect_mutation_red "outreach surface verification bypass" "$case_dir"
else
  fail_check "outreach surface mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-roster-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/activity_gate.py" \
  'if not consultant_matches_roster(event, consultant_roster):' 'if False:'; then
  expect_mutation_red "outreach consultant roster bypass" "$case_dir"
else
  fail_check "outreach roster mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-receipt-dedupe-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/activity_gate.py" \
  'if receipt_key in seen_receipts:' 'if False:'; then
  expect_mutation_red "outreach provider receipt dedupe bypass" "$case_dir"
else
  fail_check "outreach receipt dedupe mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-window-zero-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  'if outreach_complete and not consultant_focus:' 'if False:'; then
  expect_mutation_red "out-of-window outreach cannot bypass zero proof" "$case_dir"
else
  fail_check "outreach window-zero mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-coverage-output-removal)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  '"channel_coverage": channel_coverage,' '"channel_coverage_removed": channel_coverage,'; then
  expect_mutation_red "outreach coverage output removal" "$case_dir"
else
  fail_check "outreach coverage-output mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-comparison-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/activity_gate.py" \
  'status = "NOT_COMPARABLE" if coverage_blockers else "COMPARABLE"' \
  'status = "COMPARABLE"'; then
  expect_mutation_red "partial outreach coverage cannot be ranked" "$case_dir"
else
  fail_check "outreach comparison mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-position-shape-drift)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/activity_gate.py" \
  '"position_id": position_id,' '"canonical_position_id": position_id,'; then
  expect_mutation_red "consultant focus nested position schema drift" "$case_dir"
else
  fail_check "consultant focus position-schema mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation zero-result-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'if required_collections - seen:' 'if False:'; then
  expect_mutation_red "unproven zero-result bypass" "$case_dir"
else
  fail_check "zero-result mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation dedupe-version-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'and decision["rule_version"] == DEDUPE_RULE_VERSION' 'and True'; then
  expect_mutation_red "dedupe rule-version bypass" "$case_dir"
else
  fail_check "dedupe version mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation career-completeness-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/activity_gate.py" \
  'if require_complete and EXPECTED_CAREER_COMPANIES - seen:' 'if False:'; then
  expect_mutation_red "career company completeness bypass" "$case_dir"
else
  fail_check "career completeness mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation outreach-email-relabel)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/activity_gate.py" \
  'OUTREACH_CHANNELS = PORTAL_CHANNELS' \
  'OUTREACH_CHANNELS = PORTAL_CHANNELS | {"email"}'; then
  expect_mutation_red "portal outreach relabelled as email" "$case_dir"
else
  fail_check "outreach email mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation publication-warning-removal)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/brief_renderer.py" \
  '데이터 판정은 발행 완료 판정이 아니다.' \
  '데이터 판정과 발행 완료 판정은 같다.'; then
  expect_mutation_red "data verdict relabelled as publication success" "$case_dir"
else
  fail_check "publication warning mutation was not applied exactly once"
fi

case_dir=$(prepare_mutation operating-snapshot-omission)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  'require_snapshot=capability_passed(bundle.get("capabilities"), "db_read"),' \
  'require_snapshot=False,'; then
  expect_mutation_red "db PASS operating snapshot omission" "$case_dir"
else
  fail_check "operating snapshot omission mutation was not applied exactly once"
fi

case_dir=$(prepare_mutation operating-window-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/operating_gate.py" \
  'and week_start == run["window_start"].date()' 'and True'; then
  expect_mutation_red "DB closed-week window mismatch" "$case_dir"
else
  fail_check "operating window mutation was not applied exactly once"
fi

case_dir=$(prepare_mutation weekly-run-window-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  'if not window_is_week or not (' 'if False and not ('; then
  expect_mutation_red "Monday-to-Monday run window bypass" "$case_dir"
else
  fail_check "weekly run-window mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation operating-rpc-lineage-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/operating_gate.py" \
  'and snapshot.get("source_uri_ref") == f"rpc:weekly_brief_snapshot:{meeting_date}"' \
  'and True'; then
  expect_mutation_red "DB RPC source lineage bypass" "$case_dir"
else
  fail_check "DB RPC lineage mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation source-cutoff-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/contract_gate.py" \
  'if meeting_cutoff is not None and fetched_at > meeting_cutoff:' \
  'if False:'; then
  expect_mutation_red "source snapshot meeting cutoff bypass" "$case_dir"
else
  fail_check "source cutoff mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation operating-extra-funnel-key-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/operating_gate.py" \
  'and set(funnel) == FUNNEL_METRICS' \
  'and FUNNEL_METRICS.issubset(funnel)'; then
  expect_mutation_red "operating funnel extra-key bypass" "$case_dir"
else
  fail_check "operating funnel key-set mutation was not applied exactly once"
fi

case_dir=$(prepare_mutation weekly-sot-fail-open)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/sot_gate.py" \
  'return sorted(set(errors + audit_bundle(files)))' 'return []'; then
  expect_mutation_red "Weekly SOT checker fail-open" "$case_dir"
else
  fail_check "Weekly SOT checker mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation renderer-pii-injection)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/brief_renderer.py" \
  'lines.extend(["", f"`report_snapshot_id: {snapshot_id}`", ""])' \
  'lines.extend(["", "- 문의: synthetic.person@example.com", f"`report_snapshot_id: {snapshot_id}`", ""])'; then
  expect_mutation_red "renderer synthetic PII injection" "$case_dir"
else
  fail_check "renderer PII injection mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation final-output-rescan-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  'if final_output_violations(result):' 'if False:'; then
  expect_mutation_red "final output rescan bypass" "$case_dir"
else
  fail_check "final output rescan mutation was not applied exactly once"
fi
case_dir=$(prepare_mutation input-allowlist-fail-open)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/schema_gate.py" \
  'return sorted(set(found))' 'return []'; then
  expect_mutation_red "input key allowlist fail-open" "$case_dir"
else
  fail_check "input allowlist mutation was not applied exactly once"
fi
printf 'CHECKED: %s\n' "$checked"
exit "$fail"
