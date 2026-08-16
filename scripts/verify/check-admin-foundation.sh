#!/usr/bin/env bash
set -euo pipefail

selector="${1:-}"

if [ "$selector" = "pnpm-version" ]; then
  expected="pnpm@11.22.0"
  package_file="package.json"
  checked_package_manager_fields=0
  target_count=0

  if [ ! -f "$package_file" ]; then
    echo "FAIL: package.json missing"
    echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=missing-package-json"
    exit 1
  fi

  target_count=1
  actual="$(
    ruby -rjson -e '
      package = JSON.parse(File.read(ARGV.fetch(0)))
      value = package["packageManager"]
      exit 3 unless value.is_a?(String)
      print value
    ' "$package_file"
  )" || status=$?

  if [ "${status:-0}" -ne 0 ]; then
    echo "FAIL: package.json packageManager must be a string exactly equal to ${expected}"
    echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=package-manager-missing-or-malformed"
    exit 1
  fi

  checked_package_manager_fields=1

  if [ "$actual" != "$expected" ]; then
    echo "FAIL: package.json packageManager must equal ${expected}"
    echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} actual=${actual} reason=package-manager-mismatch"
    exit 1
  fi

  echo "PASS: package.json packageManager equals ${expected}"
  echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} actual=${actual} reason=null"
  exit 0
fi

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
