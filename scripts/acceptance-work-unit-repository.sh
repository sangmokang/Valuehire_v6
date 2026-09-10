#!/usr/bin/env bash
# Repository WU acceptance: fixtures do not substitute for tracked Work Unit manifests.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

repo=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf 'VERDICT: NOT_RUN\nWU_TESTS: 0\nCHECKED: 0\n'
  exit 2
}
cd "$repo" || exit 2

manifest_dir=docs/engineering/work-units
checker=scripts/verify/check-work-unit-manifest.rb
ci=.github/workflows/verify.yml
fail=0
checked=0
manifests=()

if [ -d "$manifest_dir" ]; then
  while IFS= read -r -d '' path; do
    manifests+=("$path")
  done < <(find "$manifest_dir" -type f -name '*.yaml' -print0 | sort -z)
fi

checked=$((checked + 1))
if [ "${#manifests[@]}" -eq 0 ]; then
  echo "FAIL: repository WU manifest 0 — $manifest_dir/*.yaml"
  fail=1
else
  printf 'PASS: repository WU manifests discovered — %d\n' "${#manifests[@]}"
fi

checked=$((checked + 1))
if grep -Fq 'bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-repository.sh' "$ci"; then
  echo 'PASS: repository WU acceptance is wired in CI'
else
  echo 'FAIL: repository WU acceptance is not wired in CI'
  fail=1
fi

if [ "${#manifests[@]}" -gt 0 ]; then
  for manifest in "${manifests[@]}"; do
    checked=$((checked + 1))
    output=""
    rc=0
    output=$(WORK_UNIT_CONTEXT_AT_CONTRACT=1 ruby "$checker" "$manifest" 2>&1) || rc=$?
    if [ "$rc" -eq 0 ] && printf '%s\n' "$output" | grep -q '^VERDICT: PASS$'; then
      printf 'PASS: repository WU manifest — %s\n' "$manifest"
    else
      printf 'FAIL: repository WU manifest — %s exit=%s\n%s\n' "$manifest" "$rc" "$output"
      fail=1
    fi
  done
fi

printf 'WU_TESTS: %d\nCHECKED: %d\n' "$checked" "$checked"
if [ "$fail" -eq 0 ]; then
  echo 'VERDICT: PASS'
else
  echo 'WU_FAILURE_KIND: missing_behavior'
  echo 'VERDICT: FAIL'
fi
exit "$fail"
