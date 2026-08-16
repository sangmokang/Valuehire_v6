#!/usr/bin/env bash
set -euo pipefail

selector="${1:-}"

if [ "$selector" != "node-version" ] && [ "$selector" != "pnpm-version" ]; then
  echo "FAIL: unsupported admin foundation selector: ${selector:-<missing>}"
  echo "ADMIN_FOUNDATION_NODE_VERSION checkedVersionFiles=0 targetCount=0 expected=24.19.0 reason=unsupported-selector"
  exit 2
fi

if [ "$selector" = "node-version" ]; then
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
exit 0
fi

expected="pnpm@11.22.0"
package_file="package.json"
checked_package_manager_fields=0
target_count=0
parse_status="not-run"
package_manager_value=""

if [ ! -f "$package_file" ]; then
  echo "FAIL: package.json missing"
  echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=missing-package-json"
  exit 1
fi

parse_output=$(node -e '
const fs = require("fs");
try {
  const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
  if (!Object.prototype.hasOwnProperty.call(pkg, "packageManager")) {
    process.exit(3);
  }
  if (typeof pkg.packageManager !== "string") {
    process.exit(4);
  }
  process.stdout.write(pkg.packageManager);
} catch {
  process.exit(2);
}
' 2>/dev/null) || parse_status=$?

if [ "$parse_status" = "not-run" ]; then
  parse_status=0
  checked_package_manager_fields=1
  target_count=1
  package_manager_value="$parse_output"
elif [ "$parse_status" -eq 2 ]; then
  echo "FAIL: package.json is not valid JSON"
  echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=malformed-package-json"
  exit 1
elif [ "$parse_status" -eq 3 ]; then
  echo "FAIL: package.json packageManager missing"
  echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=missing-package-manager"
  exit 1
elif [ "$parse_status" -eq 4 ]; then
  checked_package_manager_fields=1
  target_count=1
  echo "FAIL: package.json packageManager must be a string"
  echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=non-string-package-manager"
  exit 1
else
  echo "FAIL: package.json packageManager could not be read"
  echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=package-manager-read-error"
  exit 1
fi

if [ "$package_manager_value" != "$expected" ]; then
  echo "FAIL: package.json packageManager must be exactly ${expected}"
  echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=package-manager-mismatch"
  exit 1
fi

echo "PASS: package.json packageManager is exactly ${expected}"
echo "ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=${checked_package_manager_fields} targetCount=${target_count} expected=${expected} reason=null"
