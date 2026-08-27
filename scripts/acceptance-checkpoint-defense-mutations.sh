#!/usr/bin/env bash
# 원본 밖 임시 복제본에서 8개 공격군을 실행한다. candidate/worktree 미끼는 후속 24개 회귀가 맡는다.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || exit 2
OUT=$(mktemp) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -f "$OUT"' EXIT

rc=0
node --test --test-concurrency=1 tests/checkpoint-defense-mutations.test.mjs > "$OUT" 2>&1 || rc=$?
cat "$OUT"

field() { awk -v key="$1" '$1=="#" && $2==key { value=$3 } END { print value }' "$OUT"; }
tests=$(field tests); passed=$(field pass); failed=$(field fail)
cancelled=$(field cancelled); skipped=$(field skipped); todo=$(field todo)
if [ "$rc" -eq 0 ] && [ "$tests" = 8 ] && [ "$passed" = 8 ] && \
   [ "$failed" = 0 ] && [ "$cancelled" = 0 ] && [ "$skipped" = 0 ] && [ "$todo" = 0 ]; then
  echo "PASS: checkpoint 독립 방어 공격군 8/8 차단 (candidate/worktree 미끼는 followup 회귀에서 별도 검사)"
  echo "CHECKED: 8"
  echo "VERDICT: PASS"
  exit 0
fi
echo "FAIL: checkpoint 공격 TAP 계약 불일치 — exit=$rc tests=${tests:-NONE} pass=${passed:-NONE} fail=${failed:-NONE} cancelled=${cancelled:-NONE} skipped=${skipped:-NONE} todo=${todo:-NONE}"
echo "CHECKED: ${tests:-0}"
echo "VERDICT: FAIL"
exit 1
