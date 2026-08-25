#!/usr/bin/env bash
# acceptance-verified-sha.sh — 초록불이 SHA 에 귀속되는지 판정기를 진리표로 검증한다.
#
# 차단 — 세 SHA 중 하나라도 다르거나, CI 결론이 success 가 아니거나, 작업트리가
#        더럽거나, 값 하나라도 없으면 UNVERIFIED 여야 한다.
# 통과 — 전부 일치하고 success 이고 clean 일 때만 VERIFIED.
# fail-closed — 인자 개수가 틀리면 NOT_RUN(2).
set -uo pipefail

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || exit 2
CHECKER="$REPO/scripts/verify/check-verified-sha.sh"
if [ ! -f "$CHECKER" ]; then
  echo "FAIL: 판정기가 없다 — $CHECKER (fail-closed)"; echo "CHECKED: 0"; exit 2
fi

SNAPSHOT=$(git status --porcelain)
fail=0
checked=0

expect() {
  local desc="$1" wanted_rc="$2" wanted_word="$3"
  shift 3
  local out rc=0
  out=$(bash "$CHECKER" --evaluate "$@" 2>&1) || rc=$?
  checked=$((checked + 1))
  if [ "$rc" -eq "$wanted_rc" ] && printf '%s\n' "$out" | grep -q "^VERDICT: $wanted_word$"; then
    printf 'PASS: %s — %s (exit=%s)\n' "$desc" "$wanted_word" "$rc"
  else
    printf 'FAIL: %s — expected %s/exit=%s actual exit=%s\n%s\n' \
      "$desc" "$wanted_word" "$wanted_rc" "$rc" "$out"
    fail=1
  fi
}

A=1111111111111111111111111111111111111111
B=2222222222222222222222222222222222222222

expect "전부 일치·성공·깨끗 → 검증됨"        0 VERIFIED   "$A" "$A" "$A" success clean
expect "로컬 HEAD 만 다름 → 미검증"           1 UNVERIFIED "$B" "$A" "$A" success clean
expect "CI 가 검사한 SHA 만 다름 → 미검증"     1 UNVERIFIED "$A" "$A" "$B" success clean
expect "원격 HEAD 만 다름 → 미검증"           1 UNVERIFIED "$A" "$B" "$A" success clean
expect "CI 결론 failure → 미검증"             1 UNVERIFIED "$A" "$A" "$A" failure clean
expect "CI 결론 없음 → 미검증"                1 UNVERIFIED "$A" "$A" "$A" none    clean
expect "CI 실행 자체가 없음 → 미검증"          1 UNVERIFIED "$A" "$A" none  none    clean
expect "작업트리 dirty → 미검증"              1 UNVERIFIED "$A" "$A" "$A" success dirty
expect "빈 값 섞임 → 미검증"                  1 UNVERIFIED ""    "$A" "$A" success clean

# 미검증 사유가 실제로 출력되는가 — 이유 없는 판정은 다음 사람이 고칠 수 없다.
checked=$((checked + 1))
# 판정기는 UNVERIFIED 일 때 종료값 1 이다. 파이프로 넘기면 pipefail 이 그 1 을
# 파이프라인 실패로 만들어 조건이 뒤집힌다 — 출력을 먼저 변수에 담고 본다.
reason_out=$(bash "$CHECKER" --evaluate "$B" "$A" "$A" success clean 2>&1)
if printf '%s\n' "$reason_out" | grep -q '^UNVERIFIED_REASON: '; then
  echo "PASS: 미검증 사유 출력 — UNVERIFIED_REASON 존재"
else
  echo "FAIL: 미검증 사유 출력 — 사유 없이 판정만 냈다"
  fail=1
fi

# fail-closed: 인자 개수가 틀리면 통과로 세지 않는다.
checked=$((checked + 1))
argrc=0
bash "$CHECKER" --evaluate "$A" "$A" >/dev/null 2>&1 || argrc=$?
if [ "$argrc" -eq 2 ]; then
  echo "PASS: 인자 부족 → NOT_RUN (exit=2)"
else
  echo "FAIL: 인자 부족 → exit=$argrc (기대 2)"
  fail=1
fi

checked=$((checked + 1))
current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  echo "PASS: 원본 저장소 상태 불변"
else
  echo "FAIL: 원본 저장소 상태 변경"
  fail=1
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS"; else echo "VERDICT: FAIL"; fi
exit "$fail"
