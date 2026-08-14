#!/usr/bin/env bash
# 계약: docs/engineering/file-size-gate-goal-2026-08-15.md AC-FS1·AC-FS2·§⑩
# 501줄 차단, 500줄 허용, 검사 대상 0개 차단을 격리된 Git 저장소에서 검증한다.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: 저장소 루트를 찾을 수 없음"
  exit 2
}
GATE="$REPO/scripts/acceptance-file-size.sh"

if [ ! -f "$GATE" ]; then
  echo "FAIL: 본체 부재: scripts/acceptance-file-size.sh"
  exit 1
fi

SANDBOX=$(mktemp -d "$REPO/.tmp-file-size-mutations.XXXXXX")
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

total=0
passed=0
CASE_DIR=""

init_case() {
  total=$((total + 1))
  CASE_DIR="$SANDBOX/case-$total"
  mkdir -p "$CASE_DIR/humansearch/src"
  git -C "$CASE_DIR" init -q
}

make_lines() {
  local count="$1" destination="$2"
  awk -v count="$count" 'BEGIN { for (i = 1; i <= count; i++) print "sample" }' \
    > "$destination"
}

run_case() {
  local label="$1" expected_rc="$2" expected_text="$3" output rc=0
  output=$(cd "$CASE_DIR" && FILE_SIZE_ROOTS=humansearch/src bash "$GATE" 2>&1) || rc=$?

  if [ "$rc" -ne "$expected_rc" ]; then
    echo "FAIL: $label 종료값 불일치 (기대=$expected_rc, 실제=$rc)"
    printf '%s\n' "$output"
    exit 1
  fi
  if ! printf '%s\n' "$output" | grep -qF -- "$expected_text"; then
    echo "FAIL: $label 필수 출력 누락: $expected_text"
    printf '%s\n' "$output"
    exit 1
  fi

  printf 'PASS: %s (exit=%s)\n' "$label" "$rc"
  passed=$((passed + 1))
}

init_case
make_lines 501 "$CASE_DIR/humansearch/src/too-large.py"
git -C "$CASE_DIR" add humansearch/src/too-large.py
run_case "501줄 파일 차단" 1 "초과: humansearch/src/too-large.py 501줄"

init_case
make_lines 500 "$CASE_DIR/humansearch/src/at-limit.ts"
make_lines 501 "$CASE_DIR/humansearch/src/untracked.js"
git -C "$CASE_DIR" add humansearch/src/at-limit.ts
run_case "정확히 500줄 허용·미추적 501줄 제외" 0 "PASS: 검사 대상 1개, 500줄 한도 준수"

init_case
printf 'not source\n' > "$CASE_DIR/humansearch/src/README.md"
git -C "$CASE_DIR" add humansearch/src/README.md
run_case "검사 대상 0개 차단" 1 "FAIL: 검사 대상 0개"

echo "PASS: file-size mutations $passed/$total"
