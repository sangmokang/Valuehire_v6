#!/usr/bin/env bash
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
SCANNER="$REPO/scripts/acceptance-hs-cleanroom.sh"
PATTERNS="$REPO/contracts/cleanroom-deny-patterns.txt"

for required in "$SCANNER" "$PATTERNS"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: required G1 implementation missing: ${required#"$REPO"/}"
    exit 1
  fi
done

SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

total=0
blocked=0
CASE_DIR=""

init_case() {
  total=$((total + 1))
  CASE_DIR="$SANDBOX/case-$total"
  mkdir -p "$CASE_DIR/scripts" "$CASE_DIR/contracts"
  git -C "$CASE_DIR" init -q
  cp "$SCANNER" "$CASE_DIR/scripts/acceptance-hs-cleanroom.sh"
  cp "$PATTERNS" "$CASE_DIR/contracts/cleanroom-deny-patterns.txt"
  printf 'safe fixture\n' > "$CASE_DIR/safe.txt"
  git -C "$CASE_DIR" add scripts contracts safe.txt
}

expect_blocked() {
  local label="$1" expected="$2" output rc=0
  output=$(cd "$CASE_DIR" && bash scripts/acceptance-hs-cleanroom.sh 2>&1) || rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "FAIL: mutation passed: $label"
    printf '%s\n' "$output"
    exit 1
  fi
  if ! printf '%s\n' "$output" | grep -qE "^FAIL: ${expected} [1-9][0-9]*$"; then
    echo "FAIL: mutation failed for the wrong reason: $label (exit=$rc)"
    printf '%s\n' "$output"
    exit 1
  fi
  blocked=$((blocked + 1))
}

block_content() {
  local label="$1" payload="$2"
  init_case
  printf '%s\n' "$payload" > "$CASE_DIR/planted.txt"
  git -C "$CASE_DIR" add planted.txt
  expect_blocked "$label" "forbidden runtime refs"
}

legacy_prefix='Valuehire_'
block_content "legacy generation 1 path" "/tmp/${legacy_prefix}v1/module.py"
block_content "legacy generation 2 path" "/tmp/${legacy_prefix}v2/module.py"
block_content "legacy generation 3 import" "from ${legacy_prefix}v3.apps import host"
block_content "legacy generation 4 process" "subprocess.run(['/tmp/${legacy_prefix}v4/tool.py'])"
block_content "legacy generation 5 shell" ". /tmp/${legacy_prefix}v5/run.sh"

legacy_sha='cce'
legacy_sha="${legacy_sha}9280"
block_content "legacy revision" "$legacy_sha"

legacy_driver='cdp_'
legacy_driver="${legacy_driver}driver"
block_content "legacy driver import" "from ${legacy_driver} import Driver"

external_root='/tmp/external'
external_ref="${external_root}/worktrees/legacy.py"
block_content "external worktree absolute path" "$external_ref"

init_case
mkdir -p "$SANDBOX/outside"
printf 'outside\n' > "$SANDBOX/outside/target.txt"
ln -s "$SANDBOX/outside/target.txt" "$CASE_DIR/escape-link"
git -C "$CASE_DIR" add escape-link
expect_blocked "absolute escaping symlink" "escaping symlinks"

init_case
ln -s ../../outside-does-not-exist "$CASE_DIR/dangling-escape-link"
git -C "$CASE_DIR" add dangling-escape-link
expect_blocked "relative dangling escaping symlink" "escaping symlinks"

BASELINE="$SANDBOX/baseline"
mkdir -p "$BASELINE/scripts" "$BASELINE/contracts"
git -C "$BASELINE" init -q
cp "$SCANNER" "$BASELINE/scripts/acceptance-hs-cleanroom.sh"
cp "$PATTERNS" "$BASELINE/contracts/cleanroom-deny-patterns.txt"
printf 'inside\n' > "$BASELINE/inside.txt"
ln -s inside.txt "$BASELINE/inside-link"
git -C "$BASELINE" add scripts contracts inside.txt inside-link
baseline_output=$(cd "$BASELINE" && bash scripts/acceptance-hs-cleanroom.sh) || {
  echo "FAIL: safe baseline rejected"
  printf '%s\n' "$baseline_output"
  exit 1
}
checked=$(printf '%s\n' "$baseline_output" | awk '/^CHECKED: /{print $2}')
if [ -z "$checked" ] || [ "$checked" -lt 2 ]; then
  echo "FAIL: safe baseline did not report CHECKED >= 2"
  printf '%s\n' "$baseline_output"
  exit 1
fi

echo "PASS: clean-room mutations blocked $blocked/$total"
