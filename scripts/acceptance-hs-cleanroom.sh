#!/usr/bin/env bash
set -euo pipefail

unset GIT_DIR GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_WORK_TREE GIT_COMMON_DIR
unset GIT_ALTERNATE_OBJECT_DIRECTORIES

REPO=$(git rev-parse --show-toplevel) || {
  echo "FAIL: repository root unavailable"
  exit 2
}
cd "$REPO"

PATTERNS=contracts/cleanroom-deny-patterns.txt
if [ ! -f "$PATTERNS" ] || [ ! -r "$PATTERNS" ] || [ ! -s "$PATTERNS" ]; then
  echo "FAIL: clean-room pattern contract missing, unreadable, or empty"
  exit 2
fi

CLEAN=$(mktemp)
FILES=$(mktemp)
ERRS=$(mktemp)
cleanup() { rm -f -- "$CLEAN" "$FILES" "$ERRS"; }
trap cleanup EXIT
trap 'cleanup; trap - EXIT; exit 143' TERM
trap 'cleanup; trap - EXIT; exit 130' INT
trap 'cleanup; trap - EXIT; exit 129' HUP

sed -e 's/\r$//' -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' "$PATTERNS" > "$CLEAN"
if [ ! -s "$CLEAN" ]; then
  echo "FAIL: clean-room pattern contract has zero effective patterns"
  exit 2
fi

pattern_rc=0
printf '\n' | LC_ALL=C grep -aEiqf "$CLEAN" > /dev/null 2> "$ERRS" || pattern_rc=$?
if [ "$pattern_rc" -gt 1 ]; then
  echo "FAIL: clean-room pattern contract contains an invalid expression"
  exit 2
fi
if [ "$pattern_rc" -eq 0 ]; then
  echo "FAIL: clean-room pattern contract contains an empty-matching expression"
  exit 2
fi

if ! git ls-files -z > "$FILES"; then
  echo "FAIL: tracked-file enumeration failed"
  exit 2
fi

checked=0
forbidden=0
escaping=0
errors=0

scan_text() {
  local path="$1" rc=0
  LC_ALL=C grep -aEiqf "$CLEAN" "./$path" 2>> "$ERRS" || rc=$?
  if [ "$rc" -eq 0 ]; then
    forbidden=$((forbidden + 1))
    printf '  forbidden: %q\n' "$path"
  elif [ "$rc" -gt 1 ]; then
    errors=$((errors + 1))
    printf '  unreadable: %q\n' "$path"
  fi
}

scan_symlink() {
  local path="$1" target rc=0 resolved
  target=$(readlink "./$path") || {
    errors=$((errors + 1))
    printf '  unreadable-symlink: %q\n' "$path"
    return
  }

  printf '%s\n' "$target" | LC_ALL=C grep -aEiqf "$CLEAN" 2>> "$ERRS" || rc=$?
  if [ "$rc" -eq 0 ]; then
    forbidden=$((forbidden + 1))
    printf '  forbidden-symlink-target: %q\n' "$path"
  elif [ "$rc" -gt 1 ]; then
    errors=$((errors + 1))
    printf '  invalid-symlink-scan: %q\n' "$path"
  fi

  resolved=$(python3 - "$REPO" "$path" <<'PY'
import os
import sys

root = os.path.realpath(sys.argv[1])
candidate = os.path.join(root, sys.argv[2])
print(os.path.realpath(candidate))
PY
  ) || {
    errors=$((errors + 1))
    printf '  unresolved-symlink: %q\n' "$path"
    return
  }

  case "$resolved" in
    "$REPO"|"$REPO"/*) ;;
    *)
      escaping=$((escaping + 1))
      printf '  escaping-symlink: %q\n' "$path"
      ;;
  esac
}

while IFS= read -r -d '' path; do
  case "$path" in
    docs/engineering/*) continue ;;
  esac

  checked=$((checked + 1))
  if [ -L "./$path" ]; then
    scan_symlink "$path"
  else
    scan_text "$path"
  fi
done < "$FILES"

if [ "$checked" -lt 2 ]; then
  echo "FAIL: checked files $checked (<2)"
  exit 2
fi

if [ "$forbidden" -eq 0 ]; then
  echo "PASS: forbidden runtime refs 0"
else
  echo "FAIL: forbidden runtime refs $forbidden"
fi

if [ "$escaping" -eq 0 ]; then
  echo "PASS: escaping symlinks 0"
else
  echo "FAIL: escaping symlinks $escaping"
fi

echo "CHECKED: $checked"

if [ "$errors" -ne 0 ] || [ -s "$ERRS" ]; then
  echo "FAIL: scanner errors $errors"
  exit 2
fi
if [ "$forbidden" -ne 0 ] || [ "$escaping" -ne 0 ]; then
  exit 1
fi
