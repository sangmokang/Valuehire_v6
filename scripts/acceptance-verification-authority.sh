#!/usr/bin/env bash
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_COMMON_DIR \
  GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || exit 2
cd "$REPO" || exit 2

RESULT=$(mktemp) || exit 2
trap 'rm -f "$RESULT"' EXIT
if ! ruby scripts/verify/verification_authority.rb verify-all "$@" | tee "$RESULT"; then
  exit 1
fi

grep -Eq '^AUTHORITY_RESULT: (LOCAL_CANDIDATE|POLICY_REVIEW_REQUIRED)$' "$RESULT" || {
  echo 'VERIFIER_FAIL: authority result marker missing or unauthorized'
  exit 1
}
grep -Eq '^TARGET_SHA: .+' "$RESULT" || {
  echo 'VERIFIER_FAIL: target SHA marker missing'
  exit 1
}
grep -qx 'MUTATION_SURVIVED: 0' "$RESULT" || {
  echo 'VERIFIER_FAIL: mutation survival marker missing or nonzero'
  exit 1
}
