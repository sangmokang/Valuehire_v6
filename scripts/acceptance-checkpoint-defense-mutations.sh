#!/usr/bin/env bash
# 원본 밖 임시 복제본에서 9개 공격군을 실행한다.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || exit 2
OUT=$(mktemp) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -f "$OUT"' EXIT

rc=0
node --test --test-concurrency=1 \
  tests/checkpoint-defense-mutations.test.mjs \
  tests/checkpoint-defense-staged-bait.test.mjs > "$OUT" 2>&1 || rc=$?
cat "$OUT"

field() { awk -v key="$1" '$1=="#" && $2==key { value=$3 } END { print value }' "$OUT"; }
tests=$(field tests); passed=$(field pass); failed=$(field fail)
cancelled=$(field cancelled); skipped=$(field skipped); todo=$(field todo)
if [ "$rc" -eq 0 ] && [ "$tests" = 9 ] && [ "$passed" = 9 ] && \
   [ "$failed" = 0 ] && [ "$cancelled" = 0 ] && [ "$skipped" = 0 ] && [ "$todo" = 0 ]; then
  echo "PASS: checkpoint 독립 방어 공격군 9/9 차단"
  echo "CHECKED: 9"
  echo "VERDICT: PASS"
  exit 0
fi
echo "FAIL: checkpoint 공격 TAP 계약 불일치 — exit=$rc tests=${tests:-NONE} pass=${passed:-NONE} fail=${failed:-NONE} cancelled=${cancelled:-NONE} skipped=${skipped:-NONE} todo=${todo:-NONE}"
echo "CHECKED: ${tests:-0}"
echo "VERDICT: FAIL"
exit 1
