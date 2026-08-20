#!/usr/bin/env bash
# 계약: docs/engineering/humansearch-g2-gates-goal-2026-08-12.md §4
# G2 행동 뮤테이션: 진짜 게이트 스크립트가 고장 난 사본에서 불합격을 낼 줄 아는지 검증한다.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
cd "$REPO"

GATES="scripts/acceptance-hs-gates.sh"

for required in "$GATES" "scripts/hs_import_spy.py" "humansearch/pyproject.toml" \
  "humansearch/uv.lock" "humansearch/.python-version" \
  "humansearch/src/humansearch/__init__.py" "humansearch/tests" \
  "contracts/admin-weekly-dashboard/metric-contract-v1.json" "apps/admin"; do
  if [ ! -e "$required" ]; then
    echo "FAIL: required G2 implementation missing: $required"
    exit 1
  fi
done

# CI 는 scripts/verify/run-acceptance.sh 래퍼를 거쳐 실행한다(2026-08-21). 래퍼는
# 대상을 실제로 실행하므로 배선으로 인정하고, 래퍼 없는 직접 실행도 계속 인정한다.
for wired in scripts/acceptance-hs-gates.sh scripts/acceptance-hs-gates-mutations.sh; do
  if ! grep -qE "^[[:space:]]*bash (scripts/verify/run-acceptance\.sh )?${wired//./\\.}([[:space:]]|$)" .github/workflows/verify.yml; then
    echo "FAIL: CI wiring missing: bash $wired"
    exit 1
  fi
done

SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

# Dashboard tests load their product contract from the repository-level contracts tree.
# Every isolated project lives one directory below SANDBOX, so this preserves the same
# relative boundary without letting a mutation case read files from the real worktree.
mkdir -p "$SANDBOX/contracts/admin-weekly-dashboard"
cp contracts/admin-weekly-dashboard/metric-contract-v1.json \
  "$SANDBOX/contracts/admin-weekly-dashboard/"
mkdir -p "$SANDBOX/apps"
cp -R apps/admin "$SANDBOX/apps/"

total=0
blocked=0
CASE_DIR=""

init_case() {
  total=$((total + 1))
  CASE_DIR="$SANDBOX/case-$total"
  mkdir -p "$CASE_DIR"
  cp humansearch/pyproject.toml humansearch/uv.lock humansearch/.python-version "$CASE_DIR/"
  cp -R humansearch/src humansearch/tests "$CASE_DIR/"
}

expect_blocked() {
  local label="$1" marker="$2" output rc=0
  output=$(HS_GATES_PROJECT="$CASE_DIR" bash "$GATES" 2>&1) || rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: mutation passed: $label"
    printf '%s\n' "$output"
    exit 1
  fi
  if ! printf '%s\n' "$output" | grep -qF "$marker"; then
    echo "FAIL: mutation failed for the wrong reason: $label (exit=$rc)"
    printf '%s\n' "$output"
    exit 1
  fi
  blocked=$((blocked + 1))
}

init_case
printf 'def test_planted_failure() -> None:\n    raise AssertionError("planted")\n' \
  > "$CASE_DIR/tests/test_planted_failure.py"
expect_blocked "planted failing test" "FAIL: pytest"

init_case
printf 'PLANTED_NUMBER: int = "not a number"\n' \
  > "$CASE_DIR/src/humansearch/planted_types.py"
expect_blocked "planted strict type error" "FAIL: mypy"

init_case
printf 'import os\n' > "$CASE_DIR/src/humansearch/planted_lint.py"
expect_blocked "planted lint violation" "FAIL: ruff"

init_case
rm -f "$CASE_DIR"/tests/test_*.py
expect_blocked "zero collected tests" "FAIL: collected 0"

init_case
printf 'raise RuntimeError("planted import breakage")\n' \
  >> "$CASE_DIR/src/humansearch/__init__.py"
expect_blocked "broken package import" "FAIL:"

init_case
rm -rf "$CASE_DIR/src"
expect_blocked "missing package sources" "FAIL:"

BASELINE="$SANDBOX/baseline"
mkdir -p "$BASELINE"
cp humansearch/pyproject.toml humansearch/uv.lock humansearch/.python-version "$BASELINE/"
cp -R humansearch/src humansearch/tests "$BASELINE/"
baseline_output=$(HS_GATES_PROJECT="$BASELINE" bash "$GATES") || {
  echo "FAIL: clean baseline rejected"
  printf '%s\n' "$baseline_output"
  exit 1
}
collected=$(printf '%s\n' "$baseline_output" | awk '/^COLLECTED: /{print $2}')
if [ -z "$collected" ] || [ "$collected" -lt 1 ]; then
  echo "FAIL: baseline did not report COLLECTED >= 1"
  printf '%s\n' "$baseline_output"
  exit 1
fi
if ! printf '%s\n' "$baseline_output" | grep -qF "PASS: runtime import proof"; then
  echo "FAIL: baseline did not prove a runtime import"
  printf '%s\n' "$baseline_output"
  exit 1
fi

echo "PASS: gates mutations blocked $blocked/$total"
