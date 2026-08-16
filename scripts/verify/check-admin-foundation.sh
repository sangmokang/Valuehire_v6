#!/usr/bin/env bash
set -euo pipefail

selector="${1:-}"

if [ "$selector" != "node-version" ]; then
  echo "FAIL: unsupported admin foundation selector: ${selector:-<missing>}"
  echo "targetCount=0"
  exit 2
fi

target=".node-version"
expected_version="24.19.0"

if [ ! -f "$target" ]; then
  echo "FAIL: $target is missing"
  echo "checkedVersionFiles=0"
  echo "targetCount=0"
  exit 1
fi

expected_file=$(mktemp)
trap 'rm -f "$expected_file"' EXIT
printf '%s\n' "$expected_version" > "$expected_file"

if ! cmp -s "$target" "$expected_file"; then
  echo "FAIL: $target must contain exactly $expected_version on one line"
  echo "checkedVersionFiles=1"
  echo "targetCount=1"
  exit 1
fi

echo "PASS: $target is exactly $expected_version"
echo "checkedVersionFiles=1"
echo "targetCount=1"
