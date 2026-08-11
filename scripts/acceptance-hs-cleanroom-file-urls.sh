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
printf 'file:///az/%s/x\n' "$segment" > "$SANDBOX/repo/file-url.txt"
printf 'git clone file:///Users/me/project/%s/other-task\n' "$segment" > "$SANDBOX/repo/file-clone.sh"
printf 'https://example.com/%s/demo\n' "$segment" > "$SANDBOX/repo/https-url.txt"
printf '$(pwd)/%s/demo\n' "$segment" > "$SANDBOX/repo/dynamic-command.sh"
git -C "$SANDBOX/repo" add .

rc=0
output=$(cd "$SANDBOX/repo" && bash scripts/acceptance-hs-cleanroom.sh 2>&1) || rc=$?
if [ "$rc" -ne 1 ] || ! printf '%s\n' "$output" | grep -qF 'FAIL: forbidden runtime refs 2'; then
  echo "FAIL: local file URLs were not isolated from safe URL/dynamic paths (exit=$rc)"
  printf '%s\n' "$output"
  exit 1
fi

echo "PASS: local file URLs blocked without URL/dynamic overreach 2/2"
