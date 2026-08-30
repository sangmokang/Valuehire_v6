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
TESTS=tests/weekly_ops
CONTRACT=contracts/weekly-ops/runtime-contract-v1.json
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
  "$CANONICAL/SKILL.md" "$GATE" "$ACTIVITY" "$CONTRACT_GATE" "$RENDERER" \
  "$TESTS/fixtures.py" "$TESTS/test_weekly_gate.py" \
  "$TESTS/test_weekly_gate_adversarial.py" "$CONTRACT" contracts/weekly-ops/db-contract-v1.sql; do
  if [ -f "$required" ] && [ -s "$required" ] && [ ! -L "$required" ]; then
    pass_check "required file $required"
  else
    fail_check "required file invalid $required"
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
assert sources["linkedin_rps"]["preferred_surface"] == "inmail_audit_report_or_equivalent_export"
assert sources["jobkorea"]["accepted_surface_kind"] == "position_offer_history"
assert sources["saramin"]["accepted_surface_kind"] == "detailed_usage_history"
assert set(sources["linkedin_rps"]["accepted_surface_kind"]) == {
    "inmail_audit_report", "recruiter_inbox_thread"
}
assert all("open_tab" in source["invalid_surfaces"] for source in sources.values())
diagnostic = contract["outreach_diagnostic_contract"]
assert diagnostic["require_all_channels_for_portal_events"] is True
assert diagnostic["require_all_channels_when_capabilities_pass"] is True
assert diagnostic["diagnostic_and_event_snapshot_must_match"] is True
assert contract["score_points"] == gate.DIFFICULTY_POINTS
assert contract["dedupe_rule_version"] == "weekly-dedupe-v1"
assert contract["zero_result_contract"]["rule_version"] == "weekly-zero-result-v1"
assert contract["zero_result_contract"]["collections"] == ["positions", "outreach_events"]
publication = contract["publication"]
assert publication["data_and_publication_verdicts_separate"] is True
assert publication["publication_report_outside_content_hash"] is True
assert publication["canonical_brief_warns_not_publication_complete"] is True
assert publication["publication_report_names_contract_errors"] is True
for required in ("stable thread/message identity", "screenshots", "AUTOMATION_DENIED"):
    assert required in skill + prompt
PY
then
  pass_check "outreach browser readback contract is machine-checked"
else
  fail_check "outreach browser readback contract drifted"
fi

if python3 -m py_compile "$GATE" "$ACTIVITY" "$CONTRACT_GATE" "$RENDERER" "$TESTS"/*.py; then
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

prepare_mutation() {
  local name="$1"
  local destination="$TEMP_ROOT/$name"
  mkdir -p "$destination/.agents/skills" "$destination/tests"
  cp -R "$CANONICAL" "$destination/.agents/skills/weekly-ops"
  cp -R "$TESTS" "$destination/tests/weekly_ops"
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
  if (cd "$destination" && python3 -m unittest discover -s tests/weekly_ops -v) >/dev/null 2>&1; then
    fail_check "mutation $name survived"
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

case_dir=$(prepare_mutation lineage-bypass)
if mutate_exact "$case_dir/.agents/skills/weekly-ops/scripts/weekly_gate.py" \
  'if any(ref not in valid_evidence_refs for ref in position["evidence_refs"]):' \
  'if False:'; then
  expect_mutation_red "position evidence lineage bypass" "$case_dir"
else
  fail_check "lineage mutation was not applied exactly once"
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
  'if not diagnostic_allows_event(diagnostic, event):' 'if False:'; then
  expect_mutation_red "outreach surface verification bypass" "$case_dir"
else
  fail_check "outreach surface mutation was not applied exactly once"
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

printf 'CHECKED: %s\n' "$checked"
exit "$fail"
