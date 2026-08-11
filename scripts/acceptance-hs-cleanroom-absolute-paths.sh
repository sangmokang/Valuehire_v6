#!/usr/bin/env bash
set -euo pipefail

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
printf '/custom-root/project/%s/legacy.py\n' "$segment" > "$SANDBOX/repo/arbitrary-root.txt"
printf '"/custom root/project/%s/legacy.py"\n' "$segment" > "$SANDBOX/repo/quoted-space-root.txt"
printf '/%s/legacy.py\n' "$segment" > "$SANDBOX/repo/filesystem-root.txt"
git -C "$SANDBOX/repo" add .

rc=0
output=$(cd "$SANDBOX/repo" && bash scripts/acceptance-hs-cleanroom.sh 2>&1) || rc=$?
if [ "$rc" -ne 1 ] || ! printf '%s\n' "$output" | grep -qF 'FAIL: forbidden runtime refs 3'; then
  echo "FAIL: arbitrary absolute worktree paths were not all blocked (exit=$rc)"
  printf '%s\n' "$output"
  exit 1
fi

echo "PASS: arbitrary absolute worktree paths blocked 3/3"
