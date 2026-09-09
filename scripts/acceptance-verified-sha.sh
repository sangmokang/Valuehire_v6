#!/usr/bin/env bash
# acceptance-verified-sha.sh — 초록불이 SHA 에 귀속되는지 판정기를 진리표로 검증한다.
#
# 차단 — 세 SHA 중 하나라도 다르거나, 모든 CI 실행이 completed/success가 아니거나,
#        작업트리가 더럽거나, 값 하나라도 없으면 UNVERIFIED 여야 한다.
# 통과 — 전부 일치하고 모든 실행이 completed/success이고 clean 일 때만 VERIFIED.
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

expect_runs() {
  local desc="$1" wanted_rc="$2" wanted_word="$3"
  shift 3
  local out rc=0
  out=$(bash "$CHECKER" --evaluate-runs "$A" "$A" clean "$@" 2>&1) || rc=$?
  checked=$((checked + 1))
  if [ "$rc" -eq "$wanted_rc" ] && printf '%s\n' "$out" | grep -q "^VERDICT: $wanted_word$"; then
    printf 'PASS: %s — %s (exit=%s)\n' "$desc" "$wanted_word" "$rc"
  else
    printf 'FAIL: %s — expected %s/exit=%s actual exit=%s\n%s\n' \
      "$desc" "$wanted_word" "$wanted_rc" "$rc" "$out"
    fail=1
  fi
}

expect_runs_not_run() {
  local desc="$1"
  shift
  local out rc=0
  out=$(bash "$CHECKER" --evaluate-runs "$A" "$A" clean "$@" 2>&1) || rc=$?
  checked=$((checked + 1))
  if [ "$rc" -eq 2 ] && printf '%s\n' "$out" | grep -q '^NOT_RUN: '; then
    printf 'PASS: %s — NOT_RUN (exit=2)\n' "$desc"
  else
    printf 'FAIL: %s — expected NOT_RUN/exit=2 actual exit=%s\n%s\n' \
      "$desc" "$rc" "$out"
    fail=1
  fi
}

expect_runs "verify 2개 모두 완료·성공 → 검증됨" 0 VERIFIED \
  completed:success completed:success
expect_runs "성공 1개·진행 중 1개 → 미검증" 1 UNVERIFIED \
  completed:success in_progress:none
expect_runs "성공 1개·실패 1개 → 미검증" 1 UNVERIFIED \
  completed:success completed:failure
expect_runs "실패 1개 뒤 성공 1개 → 미검증" 1 UNVERIFIED \
  completed:failure completed:success
expect_runs "성공 뒤 취소 → 미검증" 1 UNVERIFIED \
  completed:success completed:cancelled
expect_runs "취소 뒤 성공 → 미검증" 1 UNVERIFIED \
  completed:cancelled completed:success
expect_runs "verify 실행 0개 → 미검증" 1 UNVERIFIED
expect_runs "진행 중 뒤 성공 → 미검증" 1 UNVERIFIED \
  in_progress:none completed:success
expect_runs_not_run "진행 중 뒤 오형식도 끝까지 검사" \
  in_progress:none malformed
expect_runs_not_run "실패 뒤 알 수 없는 상태도 끝까지 검사" \
  completed:failure unknown:success
expect_runs_not_run "구분자 둘인 레코드 → 조회 불능" \
  completed:success:extra
expect_runs_not_run "빈 status 필드 → 조회 불능" \
  :success
expect_runs_not_run "빈 conclusion 필드 → 조회 불능" \
  completed:
expect_runs_not_run "정상 뒤 구분자 둘인 레코드도 끝까지 검사" \
  completed:success completed:success:extra

# 실제 조회부도 통과시킨다. 순수 판정부만 시험하면 Bash 3.2의 빈 배열 확장이나
# `gh api --paginate` 누락처럼 API→배열→판정부 연결에서 생기는 회귀를 놓친다.
expect_lookup() {
  local desc="$1" mode="$2" wanted_rc="$3" wanted_word="$4"
  local out rc=0
  out=$(CHECKER="$CHECKER" MOCK_SHA="$A" MOCK_RUN_MODE="$mode" bash -c '
    git() {
      case "$*" in
        "rev-parse --abbrev-ref HEAD")
          printf "%s\n" task/mock
          if [ "$MOCK_RUN_MODE" = branch_fail ]; then return 91; fi
          return 0
          ;;
        "rev-parse HEAD")
          printf "%s\n" "$MOCK_SHA"
          if [ "$MOCK_RUN_MODE" = local_sha_fail ]; then return 92; fi
          return 0
          ;;
        "ls-remote origin refs/heads/task/mock")
          printf "%s\t%s\n" "$MOCK_SHA" refs/heads/task/mock
          if [ "$MOCK_RUN_MODE" = remote_sha_fail ]; then return 93; fi
          return 0
          ;;
        "status --porcelain")
          [ "$MOCK_RUN_MODE" = status_fail ] && return 98
          [ "$MOCK_RUN_MODE" = dirty ] && printf "%s\n" " M scripts/mock-dirty.sh"
          :
          ;;
        *) return 97 ;;
      esac
    }
    gh() {
      [ "$1" = api ] && [ "$2" = --paginate ] \
        && [ "$3" = "repos/{owner}/{repo}/commits/$MOCK_SHA/check-runs" ] \
        && [ "$4" = --jq ] || return 96
      case "$MOCK_RUN_MODE" in
        zero) : ;;
        status_fail) printf "%s\n" completed:success ;;
        dirty|filter_fail|branch_fail|local_sha_fail|remote_sha_fail)
          printf "%s\n" completed:success
          ;;
        gh_fail)
          printf "%s\n" completed:success
          return 93
          ;;
        mixed_failure) printf "%s\n" completed:success completed:failure ;;
        reversed_failure) printf "%s\n" completed:failure completed:success ;;
        cancelled) printf "%s\n" completed:success completed:cancelled ;;
        pending) printf "%s\n" completed:success in_progress:none ;;
        many_failure)
          i=1
          while [ "$i" -le 35 ]; do
            printf "%s\n" completed:success
            i=$((i + 1))
          done
          printf "%s\n" completed:failure
          ;;
        many|many_bad)
          i=1
          while [ "$i" -le 35 ]; do
            printf "%s\n" completed:success
            i=$((i + 1))
          done
          [ "$MOCK_RUN_MODE" = many_bad ] && printf "%s\n" malformed
          return 0
          ;;
        blank)
          printf "%s\n\n%s\n" completed:success completed:success
          ;;
        *) return 95 ;;
      esac
    }
    awk() {
      if [ "$MOCK_RUN_MODE" = filter_fail ] \
        && [ "$1" = "{ printf \"R%s\\n\", \$0 }" ]; then
        return 94
      fi
      command awk "$@"
    }
    export -f git gh awk
    if [ "$MOCK_RUN_MODE" = branch_fail ]; then
      bash "$CHECKER"
    else
      bash "$CHECKER" task/mock
    fi
  ' 2>&1) || rc=$?
  checked=$((checked + 1))
  if [ "$rc" -eq "$wanted_rc" ] && printf '%s\n' "$out" | grep -q "^VERDICT: $wanted_word$"; then
    printf 'PASS: %s — %s (exit=%s)\n' "$desc" "$wanted_word" "$rc"
  elif [ "$rc" -eq "$wanted_rc" ] && [ "$wanted_word" = NOT_RUN ] \
    && printf '%s\n' "$out" | grep -q '^NOT_RUN: '; then
    printf 'PASS: %s — NOT_RUN (exit=%s)\n' "$desc" "$rc"
  else
    printf 'FAIL: %s — expected %s/exit=%s actual exit=%s\n%s\n' \
      "$desc" "$wanted_word" "$wanted_rc" "$rc" "$out"
    fail=1
  fi
}

expect_lookup "실제 조회 성공 뒤 실패 → 미검증" mixed_failure 1 UNVERIFIED
expect_lookup "실제 조회 실패 뒤 성공 → 미검증" reversed_failure 1 UNVERIFIED
expect_lookup "실제 조회 성공 뒤 취소 → 미검증" cancelled 1 UNVERIFIED
expect_lookup "실제 조회 성공 뒤 진행 중 → 미검증" pending 1 UNVERIFIED
expect_lookup "실제 조회 35건 성공 뒤 실패 → 미검증" many_failure 1 UNVERIFIED
expect_lookup "실제 조회 0건 → Bash 3.2에서도 미검증" zero 1 UNVERIFIED
expect_lookup "페이지 크기 초과 35건 전부 성공 → 검증됨" many 0 VERIFIED
expect_lookup "35건 뒤 오형식도 끝까지 검사 → 조회 불능" many_bad 2 NOT_RUN
expect_lookup "성공 레코드 사이 빈 줄도 손실 없이 검사 → 조회 불능" blank 2 NOT_RUN
expect_lookup "작업트리 상태 조회 실패 → 조회 불능" status_fail 2 NOT_RUN
expect_lookup "작업트리 변경 출력 → 미검증" dirty 1 UNVERIFIED
expect_lookup "조회가 일부 출력 뒤 실패 → 조회 불능" gh_fail 2 NOT_RUN
expect_lookup "레코드 필터 실패 → 조회 불능" filter_fail 2 NOT_RUN
expect_lookup "현재 브랜치 조회가 출력 뒤 실패 → 조회 불능" branch_fail 2 NOT_RUN
expect_lookup "로컬 SHA 조회가 출력 뒤 실패 → 조회 불능" local_sha_fail 2 NOT_RUN
expect_lookup "원격 SHA 조회가 출력 뒤 실패 → 조회 불능" remote_sha_fail 2 NOT_RUN

checked=$((checked + 1))
bad_runs_rc=0
bash "$CHECKER" --evaluate-runs "$A" "$A" clean malformed >/dev/null 2>&1 || bad_runs_rc=$?
if [ "$bad_runs_rc" -eq 2 ]; then
  echo "PASS: 잘못된 check-run 레코드 → NOT_RUN (exit=2)"
else
  echo "FAIL: 잘못된 check-run 레코드 → exit=$bad_runs_rc (기대 2)"
  fail=1
fi

checked=$((checked + 1))
unknown_status_rc=0
bash "$CHECKER" --evaluate-runs "$A" "$A" clean unknown:success >/dev/null 2>&1 || unknown_status_rc=$?
if [ "$unknown_status_rc" -eq 2 ]; then
  echo "PASS: 알 수 없는 check-run 상태 → NOT_RUN (exit=2)"
else
  echo "FAIL: 알 수 없는 check-run 상태 → exit=$unknown_status_rc (기대 2)"
  fail=1
fi

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
