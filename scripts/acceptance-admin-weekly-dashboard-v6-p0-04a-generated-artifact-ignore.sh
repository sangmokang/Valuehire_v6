#!/usr/bin/env bash
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR GIT_ALTERNATE_OBJECT_DIRECTORIES

TARGETS=(
  "node_modules/.artifact-canary"
  "apps/admin/.next/.artifact-canary"
  "apps/admin/test-results/.artifact-canary"
  "apps/admin/playwright-report/.artifact-canary"
  "apps/admin/coverage/.artifact-canary"
)

NORMAL_SOURCE_PATHS=(
  "package.json"
  "pnpm-lock.yaml"
  "apps/admin/package.json"
  "apps/admin/src/index.ts"
)

TARGET_COUNT=${#TARGETS[@]}
MUTATION="${P0_04A_MUTATION:-none}"

receipt() {
  local checked_ignored="$1"
  local tracked_forbidden="$2"
  local reason="${3:-}"

  printf 'receipt required=%s checkedIgnored=%s trackedForbidden=%s target=%s' \
    "$TARGET_COUNT" "$checked_ignored" "$tracked_forbidden" "$TARGET_COUNT"
  if [ -n "$reason" ]; then
    printf ' reason=%s' "$reason"
  fi
  printf '\n'
}

count_ignored_targets() {
  local checked_ignored=0
  local target

  for target in "${TARGETS[@]}"; do
    if git check-ignore --no-index -- "$target" >/dev/null 2>&1; then
      checked_ignored=$((checked_ignored + 1))
    fi
  done

  printf '%s\n' "$checked_ignored"
}

count_tracked_forbidden_targets() {
  local tracked_forbidden=0
  local target

  for target in "${TARGETS[@]}"; do
    if git ls-files --error-unmatch -- "$target" >/dev/null 2>&1; then
      tracked_forbidden=$((tracked_forbidden + 1))
    fi
  done

  printf '%s\n' "$tracked_forbidden"
}

assert_normal_sources_unignored() {
  local source_path

  for source_path in "${NORMAL_SOURCE_PATHS[@]}"; do
    if git check-ignore --no-index -- "$source_path" >/dev/null 2>&1; then
      echo "FAIL: normal source path is ignored: $source_path"
      return 1
    fi
  done
}

assert_default_state() {
  local tracked_forbidden
  local checked_ignored

  tracked_forbidden=$(count_tracked_forbidden_targets)
  checked_ignored=$(count_ignored_targets)

  if [ "$tracked_forbidden" -ne 0 ]; then
    receipt "$checked_ignored" "$tracked_forbidden" "tracked-forbidden-artifact"
    echo "FAIL: tracked forbidden artifact canary present"
    return 1
  fi

  if [ "$checked_ignored" -ne "$TARGET_COUNT" ]; then
    receipt "$checked_ignored" "$tracked_forbidden" "ignore-coverage"
    echo "FAIL: generated artifact ignore coverage incomplete"
    return 1
  fi

  if ! assert_normal_sources_unignored; then
    receipt "$checked_ignored" "$tracked_forbidden" "broad-source-ignore"
    return 1
  fi

  receipt "$checked_ignored" "$tracked_forbidden"
  echo "PASS: P0-04A generated artifact ignore coverage"
}

with_restored_gitignore() {
  local backup
  backup=$(mktemp)
  cp .gitignore "$backup"
  restore_gitignore() {
    cp "$backup" .gitignore
    rm -f "$backup"
  }
  trap 'restore_gitignore' RETURN
  "$@"
}

drop_ignore_rule_and_assert_red() {
  local pattern="$1"
  local expected_ignored="$2"
  local tracked_forbidden
  local checked_ignored

  perl -0pi -e 'BEGIN { $pattern = shift @ARGV } s/\Q$pattern\E\n//g' "$pattern" .gitignore
  tracked_forbidden=$(count_tracked_forbidden_targets)
  checked_ignored=$(count_ignored_targets)
  receipt "$checked_ignored" "$tracked_forbidden" "ignore-coverage"
  if [ "$tracked_forbidden" -ne 0 ]; then
    echo "FAIL: mutation expected trackedForbidden=0"
    return 1
  fi
  if [ "$checked_ignored" -ne "$expected_ignored" ]; then
    echo "FAIL: mutation expected checkedIgnored=$expected_ignored"
    return 1
  fi
  echo "PASS: mutation produced expected RED receipt"
}

with_tracked_canary_and_assert_red() {
  local canary="apps/admin/coverage/.artifact-canary"
  mkdir -p "$(dirname "$canary")"
  printf 'P0-04A tracked artifact canary\n' > "$canary"
  git add -f -- "$canary"
  cleanup_tracked_canary() {
    if ! git rm -f --cached -- "$canary" >/dev/null 2>&1; then
      :
    fi
    rm -f -- "$canary"
    if ! rmdir -p -- "$(dirname "$canary")" >/dev/null 2>&1; then
      :
    fi
  }
  trap 'cleanup_tracked_canary' RETURN

  local tracked_forbidden
  local checked_ignored
  tracked_forbidden=$(count_tracked_forbidden_targets)
  checked_ignored=$(count_ignored_targets)
  receipt "$checked_ignored" "$tracked_forbidden" "tracked-forbidden-artifact"
  if [ "$tracked_forbidden" -ne 1 ]; then
    echo "FAIL: mutation expected trackedForbidden=1"
    return 1
  fi
  echo "PASS: tracked canary mutation produced expected RED receipt"
}

case "$MUTATION" in
  none)
    assert_default_state
    ;;
  drop-node-modules)
    with_restored_gitignore drop_ignore_rule_and_assert_red "node_modules/" 4
    ;;
  drop-next)
    with_restored_gitignore drop_ignore_rule_and_assert_red ".next/" 4
    ;;
  tracked-canary)
    with_tracked_canary_and_assert_red
    ;;
  *)
    echo "FAIL: unknown P0_04A_MUTATION=$MUTATION"
    exit 2
    ;;
esac
