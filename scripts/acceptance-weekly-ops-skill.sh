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
  "$CANONICAL/SKILL.md" "$GATE" "$ACTIVITY" "$CONTRACT_GATE" \
  "$TESTS/test_weekly_gate.py" "$CONTRACT" contracts/weekly-ops/db-contract-v1.sql; do
  if [ -f "$required" ] && [ -s "$required" ] && [ ! -L "$required" ]; then
    pass_check "required file $required"
  else
    fail_check "required file invalid $required"
  fi
done

if [ -f "$CANONICAL/SKILL.md" ] && [ ! -L "$CANONICAL/SKILL.md" ]; then
  pass_check "Codex canonical skill is discoverable under .agents/skills"
else
  fail_check "Codex canonical skill is not a regular file"
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

if python3 -m py_compile "$GATE" "$ACTIVITY" "$CONTRACT_GATE"; then
  pass_check "weekly gates compile"
else
  fail_check "weekly gates do not compile"
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

printf 'CHECKED: %s\n' "$checked"
exit "$fail"
