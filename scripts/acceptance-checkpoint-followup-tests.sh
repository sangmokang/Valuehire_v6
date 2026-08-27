#!/usr/bin/env bash
# RED에서 봉인한 checkpoint 후속 회귀의 정확한 TAP 계약을 검사한다.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || exit 2
OUT=$(mktemp) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -f "$OUT"' EXIT

rc=0
node --test --test-concurrency=1 \
  tests/checkpoint-test-strength.test.mjs \
  tests/checkpoint-test-strength-ignored-source.test.mjs \
  tests/checkpoint-test-strength-control-flow.test.mjs \
  tests/checkpoint-test-strength-static-analysis.test.mjs \
  tests/checkpoint-test-strength-structural-context.test.mjs \
  tests/checkpoint-test-strength-expression-context.test.mjs \
  tests/checkpoint-test-strength-termination-context.test.mjs \
  tests/checkpoint-test-strength-async-boundaries.test.mjs \
  tests/checkpoint-function-budget-followup.test.mjs \
  tests/checkpoint-defense.test.mjs \
  tests/checkpoint-defense-staged-bait.test.mjs \
  tests/checkpoint-defense-checker-bait.test.mjs \
  tests/checkpoint-defense-cleanup.test.mjs > "$OUT" 2>&1 || rc=$?
cat "$OUT"

field() { awk -v key="$1" '$1=="#" && $2==key { value=$3 } END { print value }' "$OUT"; }
tests=$(field tests); passed=$(field pass); failed=$(field fail)
cancelled=$(field cancelled); skipped=$(field skipped); todo=$(field todo)
if [ "$rc" -eq 0 ] && [ "$tests" = 61 ] && [ "$passed" = 61 ] && \
   [ "$failed" = 0 ] && [ "$cancelled" = 0 ] && [ "$skipped" = 0 ] && [ "$todo" = 0 ]; then
  echo "PASS: checkpoint 후속 회귀 61/61, fail·cancelled·skipped·todo 0"
  echo "CHECKED: 61"
  echo "VERDICT: PASS"
  exit 0
fi
echo "FAIL: checkpoint 후속 TAP 계약 불일치 — exit=$rc tests=${tests:-NONE} pass=${passed:-NONE} fail=${failed:-NONE} cancelled=${cancelled:-NONE} skipped=${skipped:-NONE} todo=${todo:-NONE}"
echo "CHECKED: ${tests:-0}"
echo "VERDICT: FAIL"
exit 1
