#!/usr/bin/env bash
# Detect review-required changes to verification core files between two commits.
#
# Trust boundary: this script is useful only when the caller runs a reviewed copy
# retained outside the candidate HEAD. A copy supplied by the candidate HEAD can
# be edited by that same HEAD and cannot establish its own integrity.
set -euo pipefail

usage() {
  echo "usage: $0 [--allow-same-ref] <trusted-base-sha> <candidate-head-sha>"
}

allow_same_ref=0
if [ "${1:-}" = "--allow-same-ref" ]; then
  allow_same_ref=1
  shift
fi

if [ "$#" -ne 2 ]; then
  usage
  exit 2
fi

base_sha="$1"
head_sha="$2"
full_sha_re='^[0-9a-f]{40}$'

if ! [[ "$base_sha" =~ $full_sha_re ]]; then
  echo "FAIL: trusted base must be a full 40-character lowercase commit SHA"
  exit 2
fi
if ! [[ "$head_sha" =~ $full_sha_re ]]; then
  echo "FAIL: candidate head must be a full 40-character lowercase commit SHA"
  exit 2
fi
if [ "$base_sha" = "$head_sha" ] && [ "$allow_same_ref" -ne 1 ]; then
  echo "FAIL: trusted base and candidate head are identical; pass --allow-same-ref only for an explicit unchanged control, not a trust assertion"
  exit 2
fi

if ! git cat-file -e "${base_sha}^{commit}" 2>/dev/null; then
  echo "FAIL: trusted base commit is not readable: $base_sha"
  exit 2
fi
if ! git cat-file -e "${head_sha}^{commit}" 2>/dev/null; then
  echo "FAIL: candidate head commit is not readable: $head_sha"
  exit 2
fi

core_paths=(
  "verify.sh"
  "scripts/verify/"
  "scripts/acceptance-*"
  "scripts/acceptance/"
  ".github/workflows/"
  "hooks/"
  ".githooks/"
  "docs/sot/strict-workflow.md"
  "docs/sot/coding-principles.md"
  "docs/sot/principles.yaml"
  "docs/sot/work-unit-policy.yaml"
  "docs/sot/verification-commands.md"
  "docs/sot/mechanism-registry.yaml"
  "suppressions.yaml"
  "capabilities.yaml"
  ":(glob).verification*"
  "tests/test_jd_channels.py"
  "tests/test_rps_conditions.py"
  "tests/test_verification_core.py"
)

diff_out="$(git -c diff.external= diff --no-ext-diff --no-textconv --name-status --find-renames --find-copies "$base_sha" "$head_sha" -- "${core_paths[@]}")"
if [ -n "$diff_out" ]; then
  echo "VERIFICATION_CORE_CHANGED: review required before feature PASS can imply merge readiness"
  printf '%s\n' "$diff_out"
  echo "CHECKED: ${#core_paths[@]} pathspecs"
  exit 20
fi

echo "VERIFICATION_CORE_UNCHANGED: no verification core path changes between supplied commits"
echo "CHECKED: ${#core_paths[@]} pathspecs"
