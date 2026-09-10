#!/usr/bin/env bash
# WU contract mutation gate: the checker and its CI path must fail when disabled.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

repo=$(git rev-parse --show-toplevel 2>/dev/null)
repo_rc=$?
if [ "$repo_rc" -ne 0 ]; then
  printf 'VERDICT: NOT_RUN\nWU_TESTS: 0\nCHECKED: 0\n'
  exit 2
fi
cd "$repo" || exit 2

snapshot=$(git status --porcelain=v1 -uall)
tmp=$(mktemp -d) || { printf 'VERDICT: NOT_RUN\nCHECKED: 0\n'; exit 2; }
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$tmp"' EXIT

fail=0
checked=0
record() {
  checked=$((checked + 1))
  if [ "$1" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$2" "$3"
  else
    printf 'FAIL: %s — %s\n' "$2" "$3"
    fail=1
  fi
}

baseline_rc=0
bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-contract.sh >/dev/null 2>&1 || baseline_rc=$?
if [ "$baseline_rc" -eq 0 ]; then
  record 0 "정상 WU gate" "all modes exit=0"
else
  record 1 "정상 WU gate" "exit=$baseline_rc"
fi

sandbox="$tmp/repo"
mkdir -p "$sandbox/scripts/verify/fixtures/work-unit"
cp scripts/acceptance-work-unit-contract.sh "$sandbox/scripts/"
cp scripts/verify/work_unit*.rb scripts/verify/check-work-unit-manifest.rb \
  scripts/verify/work-unit-*-contract-test.rb "$sandbox/scripts/verify/"
cp scripts/verify/fixtures/work-unit/*.yaml "$sandbox/scripts/verify/fixtures/work-unit/"
git -C "$sandbox" init -q
git -C "$sandbox" config user.email mutation@example.invalid
git -C "$sandbox" config user.name mutation-test
git -C "$sandbox" add .
git -C "$sandbox" commit -q -m baseline
original="$sandbox/scripts/verify/check-work-unit-manifest.rb"
source_checker="$tmp/checker.rb"
cp "$original" "$source_checker"

write_mutant() {
  cp "$source_checker" "$original"
  case "$1" in
    exit-zero) printf '#!/usr/bin/env ruby\nexit 0\n' > "$original" ;;
    noop) printf '#!/usr/bin/env ruby\ntrue\n' > "$original" ;;
    echo-only) printf '#!/usr/bin/env ruby\nputs "VERDICT: PASS"\nputs "CHECKED: 1"\nexit 0\n' > "$original" ;;
    always-false)
      ruby -e 'p=ARGV[0]; s=File.read(p); abort "needle missing" unless s.include?("if errors.empty?"); File.write(p, s.sub("if errors.empty?", "if false"))' "$original"
      ;;
  esac
}

for kind in exit-zero noop echo-only always-false; do
  write_mutant "$kind"
  mutation_rc=0
  (cd "$sandbox" && bash scripts/acceptance-work-unit-contract.sh schema >/dev/null 2>&1) || mutation_rc=$?
  if [ "$mutation_rc" -ne 0 ]; then
    record 0 "검사기 무력화 차단: $kind" "exit=$mutation_rc"
  else
    record 1 "검사기 무력화 차단: $kind" "mutant survived"
  fi
done

workflow=.github/workflows/verify.yml
contract_line='bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-contract.sh'
mutation_line='bash scripts/verify/run-acceptance.sh scripts/acceptance-work-unit-contract-mutations.sh'
ruby -rpsych -e '
  doc = Psych.safe_load(File.read(ARGV[0]), aliases: true)
  lines = doc.fetch("jobs").values.flat_map { |job| job.fetch("steps", []) }
    .filter_map { |step| step.is_a?(Hash) ? step["run"] : nil }
    .flat_map(&:lines).map(&:strip)
  wanted = ARGV.drop(1)
  exit(wanted.all? { |line| lines.include?(line) } ? 0 : 1)
' "$workflow" "$contract_line" "$mutation_line" 2>/dev/null
wiring_rc=$?
if [ "$wiring_rc" -eq 0 ]; then
  record 0 "WU CI 배선" "contract and mutation commands present"
else
  record 1 "WU CI 배선" "one or more executable commands missing"
fi

mutated_workflow="$tmp/verify.yml"
if ruby -e '
  source = File.read(ARGV[0])
  needle = "      - name: Work Unit TDD·맥락 계약"
  abort "needle missing" unless source.include?(needle)
  File.write(ARGV[1], source.sub(needle, needle + "\n        if: ${{ false }}"))
' "$workflow" "$mutated_workflow" 2>/dev/null; then
  ci_rc=0
  bash scripts/verify/check-ci-step-integrity.sh "$mutated_workflow" >/dev/null 2>&1 || ci_rc=$?
  if [ "$ci_rc" -eq 1 ]; then
    record 0 "WU CI 항상-거짓 조건 차단" "exit=1"
  else
    record 1 "WU CI 항상-거짓 조건 차단" "expected exit=1 actual=$ci_rc"
  fi
else
  record 1 "WU CI 항상-거짓 조건 차단" "target step missing"
fi

current=$(git status --porcelain=v1 -uall)
if [ "$current" = "$snapshot" ]; then
  record 0 "원본 worktree 상태 불변" "before/after identical"
else
  record 1 "원본 worktree 상태 불변" "repository changed"
fi

printf 'WU_TESTS: %d\nCHECKED: %d\n' "$checked" "$checked"
if [ "$fail" -eq 0 ]; then
  echo 'VERDICT: PASS'
else
  echo 'WU_FAILURE_KIND: missing_behavior'
  echo 'VERDICT: FAIL'
fi
exit "$fail"
