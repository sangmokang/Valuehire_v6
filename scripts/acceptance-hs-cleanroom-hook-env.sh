#!/usr/bin/env bash
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
INDEX=$(git rev-parse --git-path index)
if [ ! -f "$INDEX" ]; then
  echo "FAIL: repository index unavailable"
  exit 2
fi

SUITES=(
  scripts/acceptance-hs-cleanroom-mutations.sh
  scripts/acceptance-hs-cleanroom-absolute-paths.sh
  scripts/acceptance-hs-cleanroom-absolute-contexts.sh
  scripts/acceptance-hs-cleanroom-colon-paths.sh
  scripts/acceptance-hs-cleanroom-file-urls.sh
)

SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT

total=0
isolated=0
for suite in "${SUITES[@]}"; do
  total=$((total + 1))
  hook_index="$SANDBOX/hook-$total.index"
  cp "$INDEX" "$hook_index"
  before=$(shasum -a 256 "$hook_index" | awk '{print $1}')
  rc=0
  GIT_INDEX_FILE="$hook_index" bash "$REPO/$suite" >/dev/null 2>&1 || rc=$?
  after=$(shasum -a 256 "$hook_index" | awk '{print $1}')
  if [ "$rc" -eq 0 ] && [ "$before" = "$after" ]; then
    isolated=$((isolated + 1))
  else
    printf '  hook-env leak: %s exit=%s index_changed=%s\n' \
      "$suite" "$rc" "$([ "$before" = "$after" ] && echo no || echo yes)"
  fi
done

if [ "$isolated" -ne "$total" ]; then
  echo "FAIL: hook Git environment isolated $isolated/$total"
  exit 1
fi

echo "PASS: hook Git environment isolated $isolated/$total"
