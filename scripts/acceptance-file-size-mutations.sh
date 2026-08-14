#!/usr/bin/env bash
# 계약: docs/engineering/file-size-gate-goal-2026-08-15.md AC-FS1·AC-FS2·§⑩
# 경계·0개 차단, tests·.venv 제외, 시험 오버라이드 격리,
# 추적 심볼릭 링크·하위 저장소 연결 차단을 격리 저장소에서 검증한다.
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
failed=0
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

record_result() {
  local label="$1" expected_rc="$2" rc="$3" output="$4" expected_text
  shift 4
  if [ "$rc" -ne "$expected_rc" ]; then
    echo "FAIL: $label 종료값 불일치 (기대=$expected_rc, 실제=$rc)"
    printf '%s\n' "$output"
    failed=$((failed + 1))
    return
  fi
  for expected_text in "$@"; do
    if ! printf '%s\n' "$output" | grep -qF -- "$expected_text"; then
      echo "FAIL: $label 필수 출력 누락: $expected_text"
      printf '%s\n' "$output"
      failed=$((failed + 1))
      return
    fi
  done

  printf 'PASS: %s (exit=%s)\n' "$label" "$rc"
  passed=$((passed + 1))
}

run_case() {
  local label="$1" expected_rc="$2" output rc=0
  shift 2
  output=$(cd "$CASE_DIR" && FILE_SIZE_TEST=1 \
    FILE_SIZE_ROOTS=humansearch/src FILE_SIZE_LIMIT=500 bash "$GATE" 2>&1) || rc=$?
  record_result "$label" "$expected_rc" "$rc" "$output" "$@"
}

run_without_test_override() {
  local label="$1" expected_rc="$2" output rc=0
  shift 2
  output=$(cd "$CASE_DIR" && \
    env -u FILE_SIZE_TEST -u FILE_SIZE_LIMIT \
      FILE_SIZE_ROOTS=humansearch/src/allowed bash "$GATE" 2>&1) || rc=$?
  record_result "$label" "$expected_rc" "$rc" "$output" "$@"
}

init_case
make_lines 501 "$CASE_DIR/humansearch/src/my_tests_util.py"
make_lines 501 "$CASE_DIR/humansearch/src/contests.py"
git -C "$CASE_DIR" add humansearch/src/my_tests_util.py humansearch/src/contests.py
run_case "tests 글자가 이름에 든 501줄 일반 파일 차단" 1 \
  "초과: humansearch/src/my_tests_util.py 501줄" \
  "초과: humansearch/src/contests.py 501줄"

init_case
make_lines 500 "$CASE_DIR/humansearch/src/at-limit.ts"
make_lines 501 "$CASE_DIR/humansearch/src/untracked.js"
git -C "$CASE_DIR" add humansearch/src/at-limit.ts
run_case "정확히 500줄 허용·미추적 501줄 제외" 0 "PASS: 검사 대상 1개, 500줄 한도 준수"

init_case
printf 'not source\n' > "$CASE_DIR/humansearch/src/README.md"
git -C "$CASE_DIR" add humansearch/src/README.md
run_case "검사 대상 0개 차단" 1 "FAIL: 검사 대상 0개"

init_case
mkdir -p "$CASE_DIR/humansearch/src/feature/tests/fixtures"
printf 'small\n' > "$CASE_DIR/humansearch/src/app.py"
make_lines 501 "$CASE_DIR/humansearch/src/feature/tests/fixtures/test_oversized.py"
git -C "$CASE_DIR" add -- \
  humansearch/src/app.py \
  humansearch/src/feature/tests/fixtures/test_oversized.py
run_case "깊은 tests 디렉터리의 추적 501줄 파일 제외" 0 \
  "PASS: 검사 대상 1개, 500줄 한도 준수"

init_case
mkdir -p "$CASE_DIR/humansearch/src/vendor/.venv/lib"
printf 'small\n' > "$CASE_DIR/humansearch/src/app.py"
make_lines 501 "$CASE_DIR/humansearch/src/vendor/.venv/lib/vendor.py"
git -C "$CASE_DIR" add -f -- \
  humansearch/src/app.py \
  humansearch/src/vendor/.venv/lib/vendor.py
run_case "깊은 .venv 디렉터리의 추적 501줄 파일 제외" 0 \
  "PASS: 검사 대상 1개, 500줄 한도 준수"

init_case
mkdir -p "$CASE_DIR/humansearch/src/feature/tests/product"
printf 'small\n' > "$CASE_DIR/humansearch/src/app.py"
make_lines 501 "$CASE_DIR/humansearch/src/feature/tests/product/oversized.py"
ln -s feature/tests/product "$CASE_DIR/humansearch/src/product"
git -C "$CASE_DIR" add -- \
  humansearch/src/app.py \
  humansearch/src/feature/tests/product/oversized.py \
  humansearch/src/product
run_case "일반 이름의 추적 디렉터리 링크 차단" 2 \
  "FAIL: 검사 불능: 추적 경로가 심볼릭 링크임: humansearch/src/product"

init_case
mkdir -p "$CASE_DIR/humansearch/src/allowed" "$CASE_DIR/humansearch/src/blocked"
printf 'small\n' > "$CASE_DIR/humansearch/src/allowed/app.py"
make_lines 501 "$CASE_DIR/humansearch/src/blocked/oversized.py"
git -C "$CASE_DIR" add -- \
  humansearch/src/allowed/app.py \
  humansearch/src/blocked/oversized.py
run_without_test_override "FILE_SIZE_TEST 없는 검사 루트 축소 무시" 1 \
  "INFO: FILE_SIZE_TEST=1이 없어 시험용 오버라이드를 무시함" \
  "초과: humansearch/src/blocked/oversized.py 501줄"

init_case
printf 'small\n' > "$CASE_DIR/humansearch/src/app.py"
git -C "$CASE_DIR" add -- humansearch/src/app.py
gitlink_sha=$(git -C "$REPO" rev-parse HEAD)
git -C "$CASE_DIR" update-index --add \
  --cacheinfo "160000,$gitlink_sha,humansearch/src/product"
run_case "대상 루트 아래 하위 저장소 연결 차단" 2 \
  "FAIL: 검사 불능: 추적 경로가 하위 저장소 연결임: humansearch/src/product"

if [ "$failed" -ne 0 ]; then
  echo "FAIL: file-size mutations 통과 $passed/$total, 실패 $failed"
  exit 1
fi

echo "PASS: file-size mutations $passed/$total"
