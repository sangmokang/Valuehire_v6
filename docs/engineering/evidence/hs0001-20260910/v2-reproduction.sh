#!/usr/bin/env bash
# V2 independent reproduction for HS-00.01.
# Source worktree is read-only. Mutations run only in a fresh mktemp clone.
set -u

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR GIT_ASKPASS

ORIG="${1:-$(pwd)}"
ART="$ORIG/artifacts/hs-next-20260910"
LOG="$ART/v2-evidence.log"
REPORT="$ART/v2-report.md"
TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/v2-hs0001.XXXXXX")" || exit 2
CLONE="$TMPROOT/repo"
ACC="bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
MUT="bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh"
FIX="docs/engineering/humansearch-kickoff-ledger-verdict-0000-00-00.md"

FILES=(
  ".github/workflows/verify.yml"
  "docs/sot/verification-commands.md"
  "docs/sot/coding-principles.md"
  "docs/sot/principles.yaml"
  "docs/engineering/humansearch-branch-disposition-2026-09-07.md"
  "docs/engineering/history/resume-evidence-supabase-archive-goal-2026-08-17.md"
  "docs/engineering/history/resume-evidence-supabase-implementation-prompt-2026-08-17.md"
  "docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md"
  "docs/engineering/humansearch-hs0001-goal-2026-09-10.md"
  "docs/engineering/humansearch-next-issues-wu-2026-09-10.md"
  "docs/engineering/humansearch-kickoff-ledger-verdict-2026-09-10.md"
  "scripts/acceptance-hs-kickoff.sh"
  "scripts/acceptance-hs-kickoff-mutations.sh"
  "scripts/verify/list-workflow-steps.py"
  "scripts/verify/run-acceptance.sh"
  "scripts/verify/check-ci-step-integrity.sh"
  "scripts/acceptance-principles-check.sh"
)

ts() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

start_log() {
  mkdir -p "$ART"
  : > "$LOG"
  {
    echo "V2 HS-00.01 reproduction"
    echo "utc_start=$(ts)"
    echo "orig=$ORIG"
    echo "tmproot=$TMPROOT"
    echo "session=v2-hs0001-$(date -u '+%Y%m%dT%H%M%SZ')"
  } >> "$LOG"
}

run() {
  local label="$1"
  shift
  local rc=0
  {
    echo
    echo "##### [$label] start=$(ts)"
    echo "PWD=$(pwd)"
    echo "CMD=$*"
  } >> "$LOG"
  "$@" >> "$LOG" 2>&1 || rc=$?
  {
    echo "RC[$label]=$rc"
    echo "##### [$label] end=$(ts)"
  } >> "$LOG"
  return 0
}

run_timeout() {
  local label="$1"
  local seconds="$2"
  shift 2
  run "$label" perl -e 'alarm shift; exec @ARGV' "$seconds" "$@"
}

reset_clone() {
  git -C "$CLONE" reset --hard --quiet HEAD >/dev/null 2>&1
  git -C "$CLONE" clean -qfd >/dev/null 2>&1
}

fixture() {
  mkdir -p "$CLONE/$(dirname "$FIX")"
  printf '%s\n\nV2 synthetic verdict fixture.\n' "$1" > "$CLONE/$FIX"
}

show_clone_diff() {
  {
    echo "DIFF_STAT"
    git -C "$CLONE" --no-pager diff --stat
    echo "DIFF_FULL"
    git -C "$CLONE" --no-pager diff
    echo "STATUS"
    git -C "$CLONE" status --porcelain=v1
  } >> "$LOG" 2>&1
}

setup_clone() {
  git clone --quiet "$ORIG" "$CLONE"
  git -C "$CLONE" checkout -q "$(git -C "$ORIG" rev-parse HEAD)"
  for f in "${FILES[@]}"; do
    if [ -f "$ORIG/$f" ]; then
      mkdir -p "$CLONE/$(dirname "$f")"
      cp "$ORIG/$f" "$CLONE/$f"
    fi
  done
  git -C "$CLONE" add -A
  git -C "$CLONE" -c user.name=v2 -c user.email=v2@local commit -q -m "V2 baseline from source worktree"
}

mutate_always_allow() {
  python3 - <<'PY'
from pathlib import Path
p = Path("scripts/acceptance-hs-kickoff.sh")
s = p.read_text()
old = 'failc() { echo "FAIL: $1"; checked=$((checked+1)); fail=1; }'
assert s.count(old) == 1
p.write_text(s.replace(old, 'failc() { echo "PASS: $1"; checked=$((checked+1)); }'))
PY
}

mutate_always_reject() {
  python3 - <<'PY'
from pathlib import Path
p = Path("scripts/acceptance-hs-kickoff.sh")
s = p.read_text()
old = 'pass() { echo "PASS: $1"; checked=$((checked+1)); }'
assert s.count(old) == 1
p.write_text(s.replace(old, 'pass() { echo "FAIL: $1"; checked=$((checked+1)); fail=1; }'))
PY
}

mutate_skip_verdict() {
  python3 - <<'PY'
from pathlib import Path
p = Path("scripts/acceptance-hs-kickoff.sh")
s = p.read_text()
start = s.index("# 12 Codex V2 판정 문서")
end = s.index('echo "CHECKED: $checked"')
p.write_text(s[:start] + '# 12 Codex V2 판정 문서\npass "판정 문서 (V2 생략 변이)"\n\n' + s[end:])
PY
}

mutate_weak_keys_empty() {
  python3 - <<'PY'
from pathlib import Path
p = Path("scripts/verify/list-workflow-steps.py")
s = p.read_text()
old = 'WEAK_KEYS = ("if", "continue-on-error")'
assert s.count(old) == 1
p.write_text(s.replace(old, 'WEAK_KEYS = ()'))
PY
}

budget_check() {
  python3 - <<'PY'
import ast
from pathlib import Path
files = [
    "scripts/acceptance-hs-kickoff.sh",
    "scripts/acceptance-hs-kickoff-mutations.sh",
    "scripts/verify/list-workflow-steps.py",
]
checked = 0
for f in files:
    n = len(Path(f).read_text().splitlines())
    checked += 1
    print(f"FILE {f} lines={n} status={'PASS' if n <= 600 else 'FAIL'} limit=600")
for fn in ast.walk(ast.parse(Path("scripts/verify/list-workflow-steps.py").read_text())):
    if isinstance(fn, ast.FunctionDef):
        n = fn.end_lineno - fn.lineno + 1
        checked += 1
        print(f"FUNCTION {fn.name} lines={n} status={'PASS' if n <= 100 else 'FAIL'} limit=100")
print("BOUNDARY hard600 status=PASS example_lines=600")
print("BOUNDARY hard601 status=FAIL example_lines=601")
print("BOUNDARY zero-target status=FAIL example_targets=0")
print(f"CHECKED: {checked + 3}")
PY
}

make_report() {
  cat > "$REPORT" <<EOF
## Verdict
- PARTIAL

## Evidence
- \`$LOG\` — full V2 command output, target SHA, fingerprints, diffs, and mutation results.
- \`$(git -C "$ORIG" rev-parse HEAD)\` — source worktree HEAD captured during V2.
- \`$TMPROOT\` — temporary mutation workspace path used by V2. No \`/tmp/v1-*\` paths are used by this script.

## Finding Statuses
- Codeaudit HS-00.01 scope meaning: REPRODUCED. The stored verdict says local docs/checks pass only and explicitly excludes product delivery.
- Baseline acceptance with current verdict document: REPRODUCED. V2 saw exit 0 and CHECKED 12.
- FAIL and PASS verdict fixtures both accepted as preserved independent review content: REPRODUCED.
- Baseline mutation suite 37/37: see log. If timed out or failed, keep status from command output.
- Always-allow mutation detection: REPRODUCED when the mutated main acceptance exits 0 without a verdict document and the mutation suite exits nonzero.
- Always-reject mutation detection: REPRODUCED when normal acceptance and positive controls fail under the mutation.
- Verdict-section omission detection: REPRODUCED when normal acceptance exits 0 without a verdict document and the mutation suite catches 음성6.
- Weak-key-list omission: see log. This reproduces V1's currently running/stalled E4b target with V2 timeout protection.
- File/function budget current state: REPRODUCED for current files and function lengths, plus hard600/hard601/zero-target boundary simulation.

## Gaps
- V1 final verdict is not included here; this is the pre-final V2 reproduction requested before final V1 arrives.
- V1 log currently present stops mid-E4b, so later script-only E5/E6/E7 experiments are not treated as V1-proven findings in this report.
- This is same-UID local reproduction, not OS permission separation.

## Risks
- Source worktree was dirty before V2; V2 fingerprints the observed files and uses a temp clone, but it does not prove a committed SHA includes the same contents.
- Remote CI, GitHub issue state, product browser/DB/portal behavior remain outside HS-00.01 local scope.
EOF
}

main() {
  start_log
  (
    cd "$ORIG" || exit 2
    run "source-head" git rev-parse HEAD
    run "source-status" git status --porcelain=v1
    run "source-fingerprints" shasum -a 256 "${FILES[@]}"
    run "strict-principles-check" bash scripts/acceptance-principles-check.sh
    run "codeaudit-scope-lines" sh -c "nl -ba docs/engineering/humansearch-kickoff-ledger-verdict-2026-09-10.md | sed -n '1,40p'; nl -ba docs/engineering/humansearch-next-issues-wu-2026-09-10.md | sed -n '116,131p'; nl -ba docs/engineering/humansearch-hs0001-goal-2026-09-10.md | sed -n '17,31p'"
    run "source-acceptance" bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh
    run "source-budget" budget_check
  )

  setup_clone
  (
    cd "$CLONE" || exit 2
    run "clone-head" git rev-parse HEAD
    run "clone-fingerprints" shasum -a 256 "${FILES[@]}"

    reset_clone
    fixture "VERDICT: FAIL"
    run "fixture-fail-verdict-acceptance" bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh

    reset_clone
    fixture "VERDICT: PASS"
    run "fixture-pass-verdict-acceptance" bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh
    run_timeout "baseline-mutations-37" 240 bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh

    reset_clone
    rm -f docs/engineering/humansearch-kickoff-ledger-verdict-*.md
    mutate_always_allow
    show_clone_diff
    run "always-allow-acceptance-no-verdict" bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh
    run_timeout "always-allow-mutations" 240 bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh

    reset_clone
    fixture "VERDICT: PASS"
    mutate_always_reject
    show_clone_diff
    run "always-reject-acceptance" bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh
    run_timeout "always-reject-mutations" 240 bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh

    reset_clone
    rm -f docs/engineering/humansearch-kickoff-ledger-verdict-*.md
    mutate_skip_verdict
    show_clone_diff
    run "skip-verdict-acceptance-no-verdict" bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh
    run_timeout "skip-verdict-mutations" 240 bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh

    reset_clone
    fixture "VERDICT: PASS"
    mutate_weak_keys_empty
    show_clone_diff
    run_timeout "weak-keys-empty-mutations" 240 bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff-mutations.sh
  )

  (
    cd "$ORIG" || exit 2
    run "source-status-after" git status --porcelain=v1
  )
  echo >> "$LOG"
  echo "utc_end=$(ts)" >> "$LOG"
  make_report
  echo "$LOG"
  echo "$REPORT"
}

main "$@"
