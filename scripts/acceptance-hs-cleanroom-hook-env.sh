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

if [ "$#" -gt 1 ]; then
  echo "FAIL: expected zero arguments or one suite root"
  exit 2
fi
SUITE_ROOT=${1:-$REPO}
if [ ! -d "$SUITE_ROOT" ]; then
  echo "FAIL: suite root unavailable"
  exit 2
fi

SUITES=(
  scripts/acceptance-hs-cleanroom-mutations.sh
  scripts/acceptance-hs-cleanroom-absolute-paths.sh
  scripts/acceptance-hs-cleanroom-absolute-contexts.sh
  scripts/acceptance-hs-cleanroom-colon-paths.sh
  scripts/acceptance-hs-cleanroom-file-urls.sh
)
REQUIRED_VARS=(
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

capture_refs() {
  local git_dir="$1" output_file="$2" error_file="$3" rc=0
  if git --git-dir="$git_dir" show-ref > "$output_file" 2> "$error_file"; then
    rc=0
  else
    rc=$?
  fi
  if [ "$rc" -gt 1 ] || [ -s "$error_file" ]; then
    echo "FAIL: scratch refs unavailable"
    exit 2
  fi
}

total=0
isolated=0
live_before=$(shasum -a 256 "$INDEX" | awk '{print $1}')
for suite in "${SUITES[@]}"; do
  total=$((total + 1))
  suite_file="$SUITE_ROOT/$suite"
  if [ ! -f "$suite_file" ]; then
    echo "FAIL: suite unavailable: $suite"
    exit 2
  fi
  for variable in "${REQUIRED_VARS[@]}"; do
    if ! grep -Eq "^unset .*($variable)( |$)" "$suite_file"; then
      echo "  hook-env leak: $suite does not clear $variable"
      continue 2
    fi
  done

  scratch_work="$SANDBOX/work-$total"
  scratch_git="$SANDBOX/git-$total"
  mkdir -p "$scratch_work"
  git init -q --separate-git-dir="$scratch_git" "$scratch_work"
  printf 'safe\n' > "$scratch_work/safe.txt"
  git -C "$scratch_work" add safe.txt
  before_index=$(shasum -a 256 "$scratch_git/index" | awk '{print $1}')
  before_objects=$(git --git-dir="$scratch_git" count-objects -v | shasum -a 256 | awk '{print $1}')
  capture_refs "$scratch_git" "$SANDBOX/before-refs-$total" "$SANDBOX/before-refs-$total.err"
  before_refs=$(sed -n '1,$p' "$SANDBOX/before-refs-$total")
  rc=0
  GIT_DIR="$scratch_git" \
  GIT_INDEX_FILE="$scratch_git/index" \
  GIT_OBJECT_DIRECTORY="$scratch_git/objects" \
  GIT_WORK_TREE="$scratch_work" \
  GIT_COMMON_DIR="$scratch_git" \
  GIT_ALTERNATE_OBJECT_DIRECTORIES="$scratch_git/objects" \
    bash "$suite_file" >/dev/null 2>&1 || rc=$?
  after_index=$(shasum -a 256 "$scratch_git/index" | awk '{print $1}')
  after_objects=$(git --git-dir="$scratch_git" count-objects -v | shasum -a 256 | awk '{print $1}')
  capture_refs "$scratch_git" "$SANDBOX/after-refs-$total" "$SANDBOX/after-refs-$total.err"
  after_refs=$(sed -n '1,$p' "$SANDBOX/after-refs-$total")
  if [ "$rc" -eq 0 ] \
     && [ "$before_index" = "$after_index" ] \
     && [ "$before_objects" = "$after_objects" ] \
     && [ "$before_refs" = "$after_refs" ]; then
    isolated=$((isolated + 1))
  else
    printf '  hook-env leak: %s exit=%s repo_changed=%s\n' \
      "$suite" "$rc" \
      "$([ "$before_index$before_objects$before_refs" = "$after_index$after_objects$after_refs" ] && echo no || echo yes)"
  fi
done

live_after=$(shasum -a 256 "$INDEX" | awk '{print $1}')
if [ "$live_before" != "$live_after" ]; then
  echo "FAIL: live repository index changed"
  exit 1
fi

if [ "$isolated" -ne "$total" ]; then
  echo "FAIL: hook Git environment isolated $isolated/$total"
  exit 1
fi

echo "PASS: hook Git environment isolated $isolated/$total"
