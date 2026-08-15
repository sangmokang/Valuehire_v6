#!/usr/bin/env bash
# 계약: docs/engineering/file-size-gate-goal-2026-08-15.md AC-FS1·AC-FS2·§⑩
# 경계·0개 차단, 확장자 대소문자·개행 규칙, tests·.venv 제외, 시험 오버라이드 격리,
# 추적 심볼릭 링크·하위 저장소 연결 차단과 pre-push 환경 격리를 검증한다.
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: 저장소 루트를 찾을 수 없음"
  exit 2
}
GATE="$REPO/scripts/acceptance-file-size.sh"
HOOK="$REPO/hooks/pre-push"

if [ ! -f "$GATE" ]; then
  echo "FAIL: 본체 부재: scripts/acceptance-file-size.sh"
  exit 1
fi
if [ ! -f "$HOOK" ]; then
  echo "FAIL: 훅 부재: hooks/pre-push"
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

make_cr_only_lines() {
  local count="$1" destination="$2"
  awk -v count="$count" 'BEGIN { for (i = 1; i <= count; i++) printf "sample\r" }' \
    > "$destination"
}

make_crlf_lines() {
  local count="$1" destination="$2"
  awk -v count="$count" 'BEGIN { for (i = 1; i <= count; i++) printf "sample\r\n" }' \
    > "$destination"
}

make_mixed_newline_lines() {
  local destination="$1"
  awk 'BEGIN {
    for (i = 1; i <= 499; i++) printf "sample\r\n"
    printf "sample\r"
    printf "sample\r\n"
  }' > "$destination"
}

make_lf_crlf_mixed_lines() {
  local count="$1" destination="$2"
  awk -v count="$count" 'BEGIN {
    for (i = 1; i <= count; i++) {
      if (i % 2) printf "sample\n"
      else printf "sample\r\n"
    }
  }' > "$destination"
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

prepare_hook_case() {
  mkdir -p "$CASE_DIR/hooks" "$CASE_DIR/scripts" "$CASE_DIR/.github/workflows"
  cp "$HOOK" "$CASE_DIR/hooks/pre-push"
  chmod +x "$CASE_DIR/hooks/pre-push"
  cat > "$CASE_DIR/.github/workflows/verify.yml" <<'EOF'
steps:
  - run: bash scripts/acceptance-0-5.sh
  - run: bash scripts/acceptance-0-7.sh
  - run: git cat-file blob "$object"
EOF
}

commit_hook_case() {
  git -C "$CASE_DIR" add -- .
  git -C "$CASE_DIR" -c user.name='File Size Test' \
    -c user.email='file-size-test@example.invalid' commit -qm baseline
}

run_default_roots_case() {
  local label="$1" expected_rc="$2" output rc=0
  shift 2
  output=$(cd "$CASE_DIR" && \
    env -u BASH_ENV -u ENV -u FILE_SIZE_TEST -u FILE_SIZE_ROOTS -u FILE_SIZE_LIMIT \
      bash "$GATE" 2>&1) || rc=$?
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
printf 'small\n' > "$CASE_DIR/humansearch/src/app.py"
for source in upper.PY upper.TS upper.TSX upper.JS mixed.Sh; do
  make_lines 501 "$CASE_DIR/humansearch/src/$source"
done
git -C "$CASE_DIR" add -- humansearch/src
run_case "대문자·혼합 확장자 5종의 501줄 파일 차단" 1 \
  "초과: humansearch/src/upper.PY 501줄" \
  "초과: humansearch/src/upper.TS 501줄" \
  "초과: humansearch/src/upper.TSX 501줄" \
  "초과: humansearch/src/upper.JS 501줄" \
  "초과: humansearch/src/mixed.Sh 501줄"

init_case
make_cr_only_lines 501 "$CASE_DIR/humansearch/src/cr-only.py"
git -C "$CASE_DIR" add -- humansearch/src/cr-only.py
run_case "CR 전용 501줄 파일 검사 불능" 2 \
  "FAIL: 검사 불능: LF가 바로 뒤따르지 않는 CR이 있음: humansearch/src/cr-only.py"

init_case
make_mixed_newline_lines "$CASE_DIR/humansearch/src/mixed-newlines.py"
git -C "$CASE_DIR" add -- humansearch/src/mixed-newlines.py
run_case "혼합 줄바꿈 501줄 파일 검사 불능" 2 \
  "FAIL: 검사 불능: LF가 바로 뒤따르지 않는 CR이 있음: humansearch/src/mixed-newlines.py"

init_case
make_crlf_lines 500 "$CASE_DIR/humansearch/src/crlf-at-limit.py"
git -C "$CASE_DIR" add -- humansearch/src/crlf-at-limit.py
run_case "CRLF 500줄 파일 허용" 0 \
  "PASS: 검사 대상 1개, 500줄 한도 준수"

init_case
make_crlf_lines 501 "$CASE_DIR/humansearch/src/crlf-over-limit.py"
git -C "$CASE_DIR" add -- humansearch/src/crlf-over-limit.py
run_case "CRLF 501줄 파일 차단" 1 \
  "초과: humansearch/src/crlf-over-limit.py 501줄"

init_case
make_lf_crlf_mixed_lines 500 "$CASE_DIR/humansearch/src/lf-crlf-at-limit.py"
git -C "$CASE_DIR" add -- humansearch/src/lf-crlf-at-limit.py
run_case "LF·CRLF 혼합 500줄 파일 허용" 0 \
  "PASS: 검사 대상 1개, 500줄 한도 준수"

init_case
make_lf_crlf_mixed_lines 501 "$CASE_DIR/humansearch/src/lf-crlf-over-limit.py"
git -C "$CASE_DIR" add -- humansearch/src/lf-crlf-over-limit.py
run_case "LF·CRLF 혼합 501줄 파일 차단" 1 \
  "초과: humansearch/src/lf-crlf-over-limit.py 501줄"

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

init_case
mkdir -p "$CASE_DIR/humansearch/src/allowed" "$CASE_DIR/humansearch/src/blocked"
printf 'small\n' > "$CASE_DIR/humansearch/src/allowed/app.py"
make_lines 501 "$CASE_DIR/humansearch/src/blocked/oversized.py"
prepare_hook_case
cp "$GATE" "$CASE_DIR/scripts/acceptance-file-size.sh"
printf '%s\n' \
  'if [ "$PWD" = "'"$CASE_DIR"'" ]; then' \
  '  export FILE_SIZE_TEST=1' \
  '  export FILE_SIZE_ROOTS=humansearch/src/allowed' \
  '  export FILE_SIZE_LIMIT=999999' \
  'fi' > "$CASE_DIR/reinject-file-size-env.sh"
commit_hook_case
output=""
rc=0
output=$(cd "$CASE_DIR" && \
  env -u BASH_ENV -u ENV -u FILE_SIZE_TEST -u FILE_SIZE_ROOTS -u FILE_SIZE_LIMIT \
    -u VH_PREPUSH_DEPTH BASH_ENV="$CASE_DIR/reinject-file-size-env.sh" \
    bash hooks/pre-push origin https://example.invalid/valuehire.git 2>&1) || rc=$?
record_result "pre-push 자식 Bash의 BASH_ENV 오버라이드 재주입 차단" 1 "$rc" "$output" \
  "BLOCKED: ./scripts/acceptance-file-size.sh exit=1"

init_case
prepare_hook_case
cat > "$CASE_DIR/scripts/acceptance-env-probe.sh" <<'EOF'
#!/usr/bin/env bash
if [ -n "${FILE_SIZE_TEST+x}" ]; then exit 41; fi
if [ -n "${FILE_SIZE_ROOTS+x}" ]; then exit 42; fi
if [ -n "${FILE_SIZE_LIMIT+x}" ]; then exit 43; fi
if [ -n "${BASH_ENV+x}" ]; then exit 44; fi
if [ -n "${ENV+x}" ]; then exit 45; fi
exit 0
EOF
chmod +x "$CASE_DIR/scripts/acceptance-env-probe.sh"
printf '%s\n' \
  'export FILE_SIZE_TEST=1' \
  'export FILE_SIZE_ROOTS=humansearch/src/allowed' \
  'export FILE_SIZE_LIMIT=999999' > "$CASE_DIR/reinject-file-size-env.sh"
commit_hook_case
output=""
rc=0
output=$(cd "$CASE_DIR" && \
  env -u BASH_ENV -u ENV -u FILE_SIZE_TEST -u FILE_SIZE_ROOTS -u FILE_SIZE_LIMIT \
    -u VH_PREPUSH_DEPTH BASH_ENV="$CASE_DIR/reinject-file-size-env.sh" \
    ENV="$CASE_DIR/reinject-file-size-env.sh" \
    bash hooks/pre-push origin https://example.invalid/valuehire.git 2>&1) || rc=$?
record_result "pre-push 인수 스크립트 환경 5종 제거" 0 "$rc" "$output" \
  "ok  ./scripts/acceptance-env-probe.sh"

init_case
mkdir -p "$CASE_DIR/extension/src"
printf 'small\n' > "$CASE_DIR/extension/src/app.ts"
git -C "$CASE_DIR" add -- extension/src/app.ts
gitlink_sha=$(git -C "$REPO" rev-parse HEAD)
git -C "$CASE_DIR" update-index --add \
  --cacheinfo "160000,$gitlink_sha,humansearch/src"
rmdir "$CASE_DIR/humansearch/src"
git -C "$CASE_DIR" update-index --skip-worktree humansearch/src
run_default_roots_case "작업 폴더에서 숨긴 대상 루트 하위 저장소 연결 차단" 2 \
  "FAIL: 검사 불능: 추적 경로가 하위 저장소 연결임: humansearch/src"

init_case
mkdir -p "$CASE_DIR/extension/src"
printf 'small\n' > "$CASE_DIR/extension/src/app.ts"
rmdir "$CASE_DIR/humansearch/src"
ln -s elsewhere "$CASE_DIR/humansearch/src"
git -C "$CASE_DIR" add -- extension/src/app.ts humansearch/src
unlink "$CASE_DIR/humansearch/src"
git -C "$CASE_DIR" update-index --skip-worktree humansearch/src
run_default_roots_case "작업 폴더에서 숨긴 대상 루트 심볼릭 링크 차단" 2 \
  "FAIL: 검사 불능: 추적 경로가 심볼릭 링크임: humansearch/src"

if [ "$failed" -ne 0 ]; then
  echo "FAIL: file-size mutations 통과 $passed/$total, 실패 $failed"
  exit 1
fi

echo "PASS: file-size mutations $passed/$total"
