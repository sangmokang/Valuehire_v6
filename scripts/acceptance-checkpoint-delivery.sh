#!/usr/bin/env bash
# acceptance-checkpoint-delivery.sh — trusted scope, evidence and delivery-state regressions.
set -euo pipefail

REPO=$(git rev-parse --show-toplevel)
cd "$REPO"

output=$(mktemp)
trap 'rm -f "$output"' EXIT

if ! node --test \
  tests/checkpoint-gate-mutation.test.mjs \
  tests/checkpoint-ledger-trust.test.mjs \
  tests/checkpoint-secret-trust.test.mjs \
  tests/trace-ledger.test.mjs \
  tests/adversarial-evidence.test.mjs \
  tests/delivery-state.test.mjs \
  tests/delivery-wiring.test.mjs \
  tests/pr-draft.test.mjs >"$output" 2>&1; then
  cat "$output"
  echo "FAIL: checkpoint delivery regression"
  exit 1
fi

tests=$(awk '/^# tests /{print $3}' "$output" | tail -1)
passed=$(awk '/^# pass /{print $3}' "$output" | tail -1)
failed=$(awk '/^# fail /{print $3}' "$output" | tail -1)
if [ -z "$tests" ] || [ "$tests" -lt 1 ] || [ "$passed" != "$tests" ] || [ "$failed" != "0" ]; then
  cat "$output"
  echo "FAIL: checkpoint delivery test summary is missing or partial"
  exit 1
fi

syntax_checked=0
for target in \
  tools/strict/checkpoint-gate.mjs \
  tools/strict/checkpoint-js-scan.mjs \
  tools/strict/checkpoint-policy.mjs \
  tools/strict/checkpoint-secrets.mjs \
  tools/strict/trace-ledger.mjs \
  tools/strict/adversarial-evidence.mjs \
  tools/strict/delivery-state.mjs; do
  node --check "$target"
  syntax_checked=$((syntax_checked + 1))
done

checked=$((tests + syntax_checked))
echo "PASS: checkpoint delivery tests=$tests syntax=$syntax_checked"
echo "CHECKED: $checked"
