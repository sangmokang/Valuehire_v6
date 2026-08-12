#!/usr/bin/env bash
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
HARNESS="$REPO/scripts/acceptance-hs-cleanroom-hook-env.sh"
if [ ! -f "$HARNESS" ]; then
  echo "FAIL: hook environment harness missing"
  exit 2
fi

SUITES=(
  scripts/acceptance-hs-cleanroom-mutations.sh
  scripts/acceptance-hs-cleanroom-absolute-paths.sh
  scripts/acceptance-hs-cleanroom-absolute-contexts.sh
  scripts/acceptance-hs-cleanroom-colon-paths.sh
  scripts/acceptance-hs-cleanroom-file-urls.sh
)
VARS=(
  GIT_DIR
  GIT_INDEX_FILE
  GIT_OBJECT_DIRECTORY
  GIT_WORK_TREE
  GIT_COMMON_DIR
  GIT_ALTERNATE_OBJECT_DIRECTORIES
)

SANDBOX=$(mktemp -d)
cleanup() { rm -rf -- "$SANDBOX"; }
trap cleanup EXIT

blocked=0
for variable in "${VARS[@]}"; do
  mutant_root="$SANDBOX/$variable"
  mkdir -p "$mutant_root/scripts"
  for suite in "${SUITES[@]}"; do
    cp "$REPO/$suite" "$mutant_root/$suite"
  done

  target="$mutant_root/${SUITES[0]}"
  sed -e "s/$variable //" -e "s/ $variable//" "$target" > "$target.tmp"
  mv "$target.tmp" "$target"
  if cmp -s "$REPO/${SUITES[0]}" "$target"; then
    echo "FAIL: mutation did not remove $variable"
    exit 2
  fi

  rc=0
  bash "$HARNESS" "$mutant_root" >/dev/null 2>&1 || rc=$?
  if [ "$rc" -eq 1 ]; then
    blocked=$((blocked + 1))
  else
    echo "  mutation escaped: $variable (exit=$rc)"
  fi
done

if [ "$blocked" -ne "${#VARS[@]}" ]; then
  echo "FAIL: hook environment unset mutations blocked $blocked/${#VARS[@]}"
  exit 1
fi

echo "PASS: hook environment unset mutations blocked $blocked/${#VARS[@]}"
