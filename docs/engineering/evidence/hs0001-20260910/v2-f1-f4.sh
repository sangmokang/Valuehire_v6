#!/usr/bin/env bash
# Focused V2 reproduction for final V1 findings F1-F4.
set -u

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR GIT_ASKPASS

ORIG="${1:-$(pwd)}"
ART="$ORIG/artifacts/hs-next-20260910"
LOG="$ART/v2-f1-f4-evidence.log"
TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/v2-hs0001-f1f4.XXXXXX")" || exit 2
CLONE="$TMPROOT/repo"
ACC=(bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh)
FIX="docs/engineering/humansearch-kickoff-ledger-verdict-0000-00-00.md"
FILES=(
  ".github/workflows/verify.yml"
  "docs/sot/verification-commands.md"
  "docs/engineering/humansearch-branch-disposition-2026-09-07.md"
  "docs/engineering/history/resume-evidence-supabase-archive-goal-2026-08-17.md"
  "docs/engineering/history/resume-evidence-supabase-implementation-prompt-2026-08-17.md"
  "docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md"
  "docs/engineering/humansearch-kickoff-ledger-verdict-2026-09-10.md"
  "scripts/acceptance-hs-kickoff.sh"
  "scripts/acceptance-hs-kickoff-mutations.sh"
  "scripts/verify/list-workflow-steps.py"
  "scripts/verify/run-acceptance.sh"
  "scripts/verify/check-ci-step-integrity.sh"
)

ts() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

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

reset_clone() {
  git -C "$CLONE" reset --hard --quiet HEAD >/dev/null 2>&1
  git -C "$CLONE" clean -qfd >/dev/null 2>&1
  mkdir -p "$CLONE/$(dirname "$FIX")"
  printf 'VERDICT: PASS\n\nV2 F1-F4 fixture.\n' > "$CLONE/$FIX"
}

show_diff() {
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
    [ -f "$ORIG/$f" ] || continue
    mkdir -p "$CLONE/$(dirname "$f")"
    cp "$ORIG/$f" "$CLONE/$f"
  done
  git -C "$CLONE" add -A
  git -C "$CLONE" -c user.name=v2 -c user.email=v2@local commit -q -m "V2 F1-F4 baseline"
}

ast_lengths_staged_and_worktree() {
  python3 - <<'PY'
import ast, subprocess
from pathlib import Path
def lengths(src):
    tree = ast.parse(src)
    return [(n.name, n.end_lineno - n.lineno + 1) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
staged = subprocess.check_output(["git", "show", ":scripts/verify/list-workflow-steps.py"], text=True)
worktree = Path("scripts/verify/list-workflow-steps.py").read_text()
print("STAGED", lengths(staged))
print("WORKTREE", lengths(worktree))
print("STAGED_SHA", subprocess.check_output(["git", "show", ":scripts/verify/list-workflow-steps.py"], text=False).hex()[:64])
print("WORKTREE_SHA256", subprocess.check_output(["shasum", "-a", "256", "scripts/verify/list-workflow-steps.py"], text=True).strip())
PY
}

main() {
  mkdir -p "$ART"
  : > "$LOG"
  {
    echo "V2 F1-F4 focused reproduction"
    echo "utc_start=$(ts)"
    echo "orig=$ORIG"
    echo "tmproot=$TMPROOT"
    echo "source_head=$(git -C "$ORIG" rev-parse HEAD)"
  } >> "$LOG"

  (
    cd "$ORIG" || exit 2
    run "source-status-before" git status --porcelain=v1
    run "v1-artifact-fingerprints" shasum -a 256 artifacts/hs-next-20260910/v1-cli.log artifacts/hs-next-20260910/v1-verdict.md artifacts/hs-next-20260910/v1-cli.json
    run "f2-staged-vs-worktree-ast" ast_lengths_staged_and_worktree
  )

  setup_clone
  (
    cd "$CLONE" || exit 2
    run "clone-head" git rev-parse HEAD
    run "clone-fingerprints" shasum -a 256 "${FILES[@]}"

    reset_clone
    python3 - <<'PY'
from pathlib import Path
p = Path(".github/workflows/verify.yml")
s = p.read_text()
old = "        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old) == 1
p.write_text(s.replace(old, '        shell: bash -c "true" {0}\n' + old))
PY
    show_diff
    run "f1a-shell-acceptance" "${ACC[@]}"
    run "f1a-shell-ci-integrity" bash scripts/verify/check-ci-step-integrity.sh
    printf 'bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh\n' > "$TMPROOT/v2-step-script.sh"
    run "f1a-shell-semantic-local" bash -c "bash -c 'true' '$TMPROOT/v2-step-script.sh'; echo step-exit=\$?"

    reset_clone
    python3 - <<'PY'
from pathlib import Path
p = Path(".github/workflows/verify.yml")
s = p.read_text()
assert s.count("jobs:\n") == 1
p.write_text(s.replace("jobs:\n", "defaults:\n  run:\n    shell: cat\n\njobs:\n", 1))
PY
    show_diff
    run "f1b-defaults-acceptance" "${ACC[@]}"
    run "f1b-defaults-ci-integrity" bash scripts/verify/check-ci-step-integrity.sh

    reset_clone
    printf 'exit 0\n' > scripts/v2-bait-env.sh
    python3 - <<'PY'
from pathlib import Path
p = Path(".github/workflows/verify.yml")
s = p.read_text()
old = "        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
assert s.count(old) == 1
p.write_text(s.replace(old, '        env:\n          BASH_ENV: scripts/v2-bait-env.sh\n' + old))
PY
    show_diff
    run "f1c-bash-env-acceptance" "${ACC[@]}"
    run "f1c-bash-env-ci-integrity" bash scripts/verify/check-ci-step-integrity.sh
    run "f1c-bash-env-semantic-local" bash -c "BASH_ENV=scripts/v2-bait-env.sh bash -e '$TMPROOT/v2-step-script.sh'; echo step-exit=\$?"

    reset_clone
    python3 - <<'PY'
from pathlib import Path
p = Path("docs/engineering/humansearch-branch-disposition-2026-09-07.md")
s = p.read_text()
old = "| 1 | PR #13 `task/humansearch-g3-portal-constants`"
assert s.count(old) == 1
p.write_text(s.replace(old, "| 1 | PR #131 `task/humansearch-g3-portal-constants`"))
PY
    show_diff
    run "f3-pr131-acceptance" "${ACC[@]}"

    reset_clone
    printf 'VERDICT: PASSED\n\nV2 prefix fixture.\n' > "$FIX"
    run "f4-passed-prefix-acceptance" "${ACC[@]}"

    reset_clone
    printf 'VERDICT: PASS\n\nV2 first fixture.\n' > "$FIX"
    printf 'VERDICT: FAIL\n\nV2 second fixture.\n' > docs/engineering/humansearch-kickoff-ledger-verdict-2026-09-10.md
    run "f4-two-verdict-docs-acceptance" "${ACC[@]}"

    reset_clone
    : > "$FIX"
    run "f4-empty-verdict-direct-acceptance" "${ACC[@]}"
  )

  (
    cd "$ORIG" || exit 2
    run "source-status-after" git status --porcelain=v1
  )
  echo "utc_end=$(ts)" >> "$LOG"
  echo "$LOG"
}

main "$@"
