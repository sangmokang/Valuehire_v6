#!/usr/bin/env bash
set -euo pipefail

selector="${1:-}"

if [ "$selector" != "node-version" ]; then
  echo "FAIL: unsupported admin foundation selector: ${selector:-<missing>}"
  echo "ADMIN_FOUNDATION_NODE_VERSION checkedVersionFiles=0 targetCount=0 expected=24.19.0 reason=unsupported-selector"
  exit 2
fi

expected="24.19.0"
version_file=".node-version"
checked_version_files=0
target_count=0

if [ -f "$version_file" ]; then
  checked_version_files=1
  target_count=1
fi

if [ "$target_count" -eq 0 ]; then
  echo "FAIL: .node-version missing"
  echo "ADMIN_FOUNDATION_NODE_VERSION checkedVersionFiles=${checked_version_files} targetCount=${target_count} expected=${expected} reason=missing-node-version"
  exit 1
fi

if ! cmp -s "$version_file" <(printf '%s\n' "$expected"); then
  echo "FAIL: .node-version must contain exactly one line: ${expected}"
  echo "ADMIN_FOUNDATION_NODE_VERSION checkedVersionFiles=${checked_version_files} targetCount=${target_count} expected=${expected} reason=node-version-mismatch"
  exit 1
fi

echo "PASS: .node-version contains exactly ${expected}"
echo "ADMIN_FOUNDATION_NODE_VERSION checkedVersionFiles=${checked_version_files} targetCount=${target_count} expected=${expected} reason=null"
