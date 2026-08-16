#!/usr/bin/env bash
set -euo pipefail

selector="${1:-}"

if [ "$selector" = "root-workspace" ]; then
  package_file="package.json"
  workspace_file="pnpm-workspace.yaml"
  checked_private_fields=0
  workspace_pattern_count=0
  target_count=2

  if [ ! -f "$package_file" ]; then
    echo "FAIL: package.json missing"
    echo "ADMIN_FOUNDATION_ROOT_WORKSPACE checkedPrivateFields=${checked_private_fields} workspacePatternCount=${workspace_pattern_count} targetCount=${target_count} expectedPrivate=true expectedPattern=apps/* reason=missing-package-json"
    exit 1
  fi

  actual_private="$(
    ruby -rjson -e '
      package = JSON.parse(File.read(ARGV.fetch(0)))
      value = package["private"]
      exit 3 unless value == true || value == false
      print value
    ' "$package_file"
  )" || status=$?

  if [ "${status:-0}" -ne 0 ]; then
    echo "FAIL: package.json private must be boolean true"
    echo "ADMIN_FOUNDATION_ROOT_WORKSPACE checkedPrivateFields=${checked_private_fields} workspacePatternCount=${workspace_pattern_count} targetCount=${target_count} expectedPrivate=true expectedPattern=apps/* reason=private-missing-or-malformed"
    exit 1
  fi

  checked_private_fields=1

  if [ "$actual_private" != "true" ]; then
    echo "FAIL: package.json private must be true"
    echo "ADMIN_FOUNDATION_ROOT_WORKSPACE checkedPrivateFields=${checked_private_fields} workspacePatternCount=${workspace_pattern_count} targetCount=${target_count} expectedPrivate=true actualPrivate=${actual_private} expectedPattern=apps/* reason=private-not-true"
    exit 1
  fi

  if [ ! -f "$workspace_file" ]; then
    echo "FAIL: pnpm-workspace.yaml missing"
    echo "ADMIN_FOUNDATION_ROOT_WORKSPACE checkedPrivateFields=${checked_private_fields} workspacePatternCount=${workspace_pattern_count} targetCount=${target_count} expectedPrivate=true actualPrivate=${actual_private} expectedPattern=apps/* reason=missing-pnpm-workspace"
    exit 1
  fi

  if ! cmp -s "$workspace_file" <(printf 'packages:\n  - apps/*\n'); then
    echo "FAIL: pnpm-workspace.yaml must declare exactly one package pattern: apps/*"
    echo "ADMIN_FOUNDATION_ROOT_WORKSPACE checkedPrivateFields=${checked_private_fields} workspacePatternCount=${workspace_pattern_count} targetCount=${target_count} expectedPrivate=true actualPrivate=${actual_private} expectedPattern=apps/* reason=workspace-pattern-mismatch"
    exit 1
  fi

  workspace_pattern_count=1

  echo "PASS: root package is private and pnpm workspace declares exactly apps/*"
  echo "ADMIN_FOUNDATION_ROOT_WORKSPACE checkedPrivateFields=${checked_private_fields} workspacePatternCount=${workspace_pattern_count} targetCount=${target_count} expectedPrivate=true actualPrivate=${actual_private} expectedPattern=apps/* reason=null"
  exit 0
fi

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

if [ "$selector" = "artifact-ignore" ]; then
  target_count=5
  required_ignore_paths=(
    "node_modules/.artifact-canary"
    "apps/admin/.next/.artifact-canary"
    "apps/admin/test-results/.artifact-canary"
    "apps/admin/playwright-report/.artifact-canary"
    "apps/admin/coverage/.artifact-canary"
  )
  required_ignore_path_count="${#required_ignore_paths[@]}"
  checked_ignored_path_count=0
  tracked_forbidden_artifact_count=0

  for required_path in "${required_ignore_paths[@]}"; do
    if git check-ignore --quiet -- "$required_path"; then
      checked_ignored_path_count=$((checked_ignored_path_count + 1))
    fi
  done

  while IFS= read -r -d '' tracked_path; do
    case "$tracked_path" in
      node_modules/*|apps/admin/.next/*|apps/admin/test-results/*|apps/admin/playwright-report/*|apps/admin/coverage/*)
        tracked_forbidden_artifact_count=$((tracked_forbidden_artifact_count + 1))
        ;;
    esac
  done < <(git ls-files -z -- node_modules apps/admin/.next apps/admin/test-results apps/admin/playwright-report apps/admin/coverage)

  if [ "$checked_ignored_path_count" -ne "$required_ignore_path_count" ]; then
    echo "FAIL: admin generated artifact paths must be ignored by Git"
    echo "ADMIN_FOUNDATION_ARTIFACT_IGNORE requiredIgnorePathCount=${required_ignore_path_count} checkedIgnoredPathCount=${checked_ignored_path_count} trackedForbiddenArtifactCount=${tracked_forbidden_artifact_count} targetCount=${target_count} reason=required-path-not-ignored"
    exit 1
  fi

  if [ "$tracked_forbidden_artifact_count" -ne 0 ]; then
    echo "FAIL: generated artifact paths must not be tracked"
    echo "ADMIN_FOUNDATION_ARTIFACT_IGNORE requiredIgnorePathCount=${required_ignore_path_count} checkedIgnoredPathCount=${checked_ignored_path_count} trackedForbiddenArtifactCount=${tracked_forbidden_artifact_count} targetCount=${target_count} reason=tracked-forbidden-artifact"
    exit 1
  fi

  echo "PASS: pnpm/admin generated artifact paths are ignored and no forbidden artifacts are tracked"
  echo "ADMIN_FOUNDATION_ARTIFACT_IGNORE requiredIgnorePathCount=${required_ignore_path_count} checkedIgnoredPathCount=${checked_ignored_path_count} trackedForbiddenArtifactCount=${tracked_forbidden_artifact_count} targetCount=${target_count} reason=null"
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
