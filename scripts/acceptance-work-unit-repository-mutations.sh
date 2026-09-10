#!/usr/bin/env bash
# Adversarial proof that repository adoption cannot be replaced by absent or untracked manifests.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

repo=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf 'VERDICT: NOT_RUN\nWU_TESTS: 0\nCHECKED: 0\n'
  exit 2
}
cd "$repo" || exit 2

before=$(git status --porcelain=v1 -uall)
parent=$(mktemp -d)
checkout="$parent/checkout"
fail=0
checked=0

cleanup() {
  if [ -d "$checkout" ]; then
    git worktree remove --force "$checkout" >/dev/null 2>&1
  fi
  rm -rf "$parent"
}
trap cleanup EXIT

if ! git worktree add --detach "$checkout" HEAD >/dev/null 2>&1; then
  printf 'VERDICT: NOT_RUN\nREASON: detached mutation worktree unavailable\nWU_TESTS: 0\nCHECKED: 0\n'
  exit 2
fi
cp "$repo/scripts/acceptance-work-unit-repository.sh" \
  "$checkout/scripts/acceptance-work-unit-repository.sh"
cp "$repo/scripts/verify/check-work-unit-repository-coverage.rb" \
  "$checkout/scripts/verify/check-work-unit-repository-coverage.rb"
cp "$repo/docs/sot/work-unit-policy.yaml" "$checkout/docs/sot/work-unit-policy.yaml"

run_case() {
  local label=$1 wanted=$2 diagnostic=$3
  local output="" rc=0
  output=$(cd "$checkout" && bash scripts/acceptance-work-unit-repository.sh 2>&1) || rc=$?
  checked=$((checked + 1))
  if [ "$rc" -eq "$wanted" ] && printf '%s\n' "$output" | grep -q "$diagnostic"; then
    printf 'PASS: %s — exit=%s\n' "$label" "$rc"
  else
    printf 'FAIL: %s — expected exit=%s diagnostic=%s actual=%s\n%s\n' \
      "$label" "$wanted" "$diagnostic" "$rc" "$output"
    fail=1
  fi
}

manifest=docs/engineering/work-units/work-unit-tdd-context.yaml
disabled="$manifest.disabled"

run_case "normal repository WU gate" 0 '^VERDICT: PASS$'

mv "$checkout/$manifest" "$checkout/$disabled"
run_case "missing repository manifests rejected" 1 'repository WU manifest 0'
mv "$checkout/$disabled" "$checkout/$manifest"

mv "$checkout/$manifest" "$checkout/$disabled"
cp "$checkout/$disabled" "$checkout/docs/engineering/work-units/untracked.yaml"
run_case "untracked manifest substitute rejected" 1 'untracked WU manifest is not repository evidence'
mv "$checkout/docs/engineering/work-units/untracked.yaml" "$parent/untracked.yaml"
mv "$checkout/$disabled" "$checkout/$manifest"

cp "$checkout/$manifest" "$parent/complete-manifest.yaml"
ruby -rpsych -e '
  path = ARGV.fetch(0)
  data = Psych.safe_load(File.read(path), permitted_classes: [], aliases: false)
  data.fetch("work_units").reject! { |unit| unit.fetch("id") == "WU-5" }
  File.write(path, Psych.dump(data))
' "$checkout/$manifest"
run_case "missing required WU ID rejected" 1 'REQUIRED_WU_MISSING: WU-5'
cp "$parent/complete-manifest.yaml" "$checkout/$manifest"

ruby -pi -e 'gsub("bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-repository.sh", "echo repository-WU-gate-disabled")' \
  "$checkout/.github/workflows/verify.yml"
run_case "disabled repository CI wiring rejected" 1 'not wired in CI'

after=$(git status --porcelain=v1 -uall)
checked=$((checked + 1))
if [ "$before" = "$after" ]; then
  echo 'PASS: original worktree state unchanged'
else
  echo 'FAIL: original worktree state changed'
  fail=1
fi

printf 'WU_TESTS: %d\nCHECKED: %d\n' "$checked" "$checked"
if [ "$fail" -eq 0 ]; then echo 'VERDICT: PASS'; else echo 'VERDICT: FAIL'; fi
exit "$fail"
