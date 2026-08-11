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
    exit 2
  fi
done

SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT

mkdir -p "$SANDBOX/repo/scripts" "$SANDBOX/repo/contracts"
git -C "$SANDBOX/repo" init -q
cp "$SCANNER" "$SANDBOX/repo/scripts/acceptance-hs-cleanroom.sh"
cp "$PATTERNS" "$SANDBOX/repo/contracts/cleanroom-deny-patterns.txt"
printf 'safe\n' > "$SANDBOX/repo/safe.txt"

segment='work'
segment="${segment}trees"
printf "sys.path.append('/custom-root/project/%s')\n" "$segment" > "$SANDBOX/repo/root-reference.py"
printf 'paths = ["/custom-root/project/%s/legacy.py"]\n' "$segment" > "$SANDBOX/repo/array-reference.py"
printf '\140/custom-root/project/%s/legacy.py\140\n' "$segment" > "$SANDBOX/repo/backtick-reference.md"
printf '>/custom-root/project/%s/out.py\n' "$segment" > "$SANDBOX/repo/redirect-reference.sh"
printf '/custom\\ root/project/%s/legacy.py\n' "$segment" > "$SANDBOX/repo/escaped-space.sh"
printf '/custom{x}/project/%s/legacy.py\n' "$segment" > "$SANDBOX/repo/brace-reference.txt"
printf '//%s/legacy.py\n' "$segment" > "$SANDBOX/repo/double-slash.txt"
git -C "$SANDBOX/repo" add .

rc=0
output=$(cd "$SANDBOX/repo" && bash scripts/acceptance-hs-cleanroom.sh 2>&1) || rc=$?
if [ "$rc" -ne 1 ] || ! printf '%s\n' "$output" | grep -qF 'FAIL: forbidden runtime refs 7'; then
  echo "FAIL: absolute worktree path contexts were not all blocked (exit=$rc)"
  printf '%s\n' "$output"
  exit 1
fi

echo "PASS: absolute worktree path contexts blocked 7/7"
