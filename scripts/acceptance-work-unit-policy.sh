#!/usr/bin/env bash
# 구조화된 Work Unit 정책과 사람이 읽는 생성 문서가 같은 계약을 말하는지 검증한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "VERDICT: NOT_RUN"
  echo "REASON: not a git repository"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

POLICY=docs/sot/work-unit-policy.yaml
DOCUMENT=docs/sot/work-unit-policy.md
CHECKER=scripts/verify/check-work-unit-policy.rb
RENDERER=scripts/verify/render-work-unit-policy.rb
fail=0
checked=0

require_file() {
  local path="$1"
  checked=$((checked + 1))
  if [ -f "$path" ] && [ ! -L "$path" ] && [ -s "$path" ]; then
    printf 'PASS: required file %s\n' "$path"
  else
    printf 'FAIL: required file missing, empty, or symlink — %s\n' "$path"
    fail=1
  fi
}

require_file "$POLICY"
require_file "$DOCUMENT"
require_file "$CHECKER"
require_file "$RENDERER"

if [ "$fail" -eq 0 ]; then
  rc=0
  output=$(ruby "$CHECKER" "$POLICY" "$DOCUMENT" 2>&1) || rc=$?
  checked=$((checked + 1))
  if [ "$rc" -eq 0 ] && printf '%s\n' "$output" | grep -q '^VERDICT: PASS$' && \
     printf '%s\n' "$output" | grep -q '^POLICY_CHECKED: 19$' && \
     printf '%s\n' "$output" | grep -q '^DOCUMENT_SYNC: PASS$'; then
    echo "PASS: structured policy and generated document"
  else
    printf 'FAIL: structured policy checker — exit=%s\n%s\n' "$rc" "$output"
    fail=1
  fi
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$fail"
