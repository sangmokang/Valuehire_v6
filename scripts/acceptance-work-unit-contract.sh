#!/usr/bin/env bash
# WU contract acceptance: each mode is one falsifiable claim and reports a count.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

repo=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf 'VERDICT: NOT_RUN\nWU_TESTS: 0\nCHECKED: 0\n'
  exit 2
}
cd "$repo" || exit 2

mode=${1:-all}
checker=scripts/verify/check-work-unit-manifest.rb
fixtures=scripts/verify/fixtures/work-unit
fail=0
checked=0

run_case() {
  local label=$1 path=$2 wanted=$3 diagnostic=$4
  local output="" rc=0
  output=$(WORK_UNIT_SCHEMA_ONLY=1 ruby "$checker" "$path" 2>&1) || rc=$?
  checked=$((checked + 1))
  if [ "$rc" -eq "$wanted" ] && printf '%s\n' "$output" | grep -q "$diagnostic"; then
    printf 'PASS: %s — exit=%s\n' "$label" "$rc"
  else
    printf 'FAIL: %s — expected exit=%s diagnostic=%s actual=%s\n%s\n' \
      "$label" "$wanted" "$diagnostic" "$rc" "$output"
    fail=1
  fi
}

case "$mode" in
  schema|all)
    run_case "normal manifest" "$fixtures/valid.yaml" 0 '^VERDICT: PASS$'
    run_case "missing AC" "$fixtures/ac-missing.yaml" 1 'AC_REQUIRED:'
    run_case "missing counter-AC" "$fixtures/counter-ac-missing.yaml" 1 'COUNTER_AC_REQUIRED:'
    run_case "duplicate ID" "$fixtures/duplicate-id.yaml" 1 'ID_DUPLICATE:'
    ;;
  tdd)
    ruby scripts/verify/work-unit-tdd-contract-test.rb
    exit $?
    ;;
  context)
    ruby scripts/verify/work-unit-context-contract-test.rb
    exit $?
    ;;
  not-applicable)
    ruby scripts/verify/work-unit-not-applicable-contract-test.rb
    exit $?
    ;;
  *)
    printf 'VERDICT: NOT_RUN\nREASON: unknown mode %s\nWU_TESTS: 0\nCHECKED: 0\n' "$mode"
    exit 2
    ;;
esac

printf 'WU_TESTS: %d\nCHECKED: %d\n' "$checked" "$checked"
if [ "$fail" -eq 0 ]; then
  echo 'VERDICT: PASS'
else
  probe=""
  probe_rc=0
  probe=$(WORK_UNIT_SCHEMA_ONLY=1 ruby "$checker" "$fixtures/valid.yaml" 2>&1) || probe_rc=$?
  if [ "$probe_rc" -eq 2 ] && printf '%s\n' "$probe" | grep -q 'validation not implemented'; then
    echo 'WU_FAILURE_KIND: missing_behavior'
  fi
  echo 'VERDICT: FAIL'
fi
exit "$fail"
