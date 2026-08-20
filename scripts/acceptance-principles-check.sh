#!/usr/bin/env bash
# acceptance-principles-check.sh — Strict 원칙 정본·장부·로컬/CI 배선을 fail-closed로 검증한다.
# 종료값: 0=PASS, 1=FAIL, 2=NOT_RUN(환경/호출 문제).
set -uo pipefail

if [ "$#" -gt 0 ]; then
  MODE="$1"
else
  MODE="--full"
fi
case "$MODE" in
  --full) ;;
  *)
    printf 'VERDICT: NOT_RUN\nREASON: unsupported mode %s\n' "$MODE"
    exit 2
    ;;
esac

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf 'VERDICT: NOT_RUN\nREASON: not a git repository\n'
  exit 2
}
cd "$REPO" || {
  printf 'VERDICT: NOT_RUN\nREASON: cannot enter repository root\n'
  exit 2
}

LEDGER="docs/sot/principles.yaml"
SOURCE="docs/sot/coding-principles.md"
SELF="scripts/acceptance-principles-check.sh"
PRE_PUSH="hooks/pre-push"
WORKFLOW=".github/workflows/verify.yml"
RUNTIME_CHECKER="scripts/verify/check-pre-push-runtime.sh"
GIT_WORKFLOW_SOT="docs/sot/git-workflow.md"
VERIFICATION_SOT="docs/sot/verification-commands.md"

for required in "$SOURCE" "$LEDGER" "$SELF" "$PRE_PUSH" "$WORKFLOW" "$RUNTIME_CHECKER" \
  "$GIT_WORKFLOW_SOT" "$VERIFICATION_SOT"; do
  if [ ! -f "$required" ] || [ -L "$required" ]; then
    printf 'VERDICT: FAIL\nREQUIRED_FILE_INVALID: %s\nCHECKED: 0\n' "$required"
    exit 1
  fi
  if [ ! -s "$required" ] || ! grep -q '[^[:space:]]' "$required"; then
    printf 'VERDICT: FAIL\nREQUIRED_FILE_EMPTY: %s\nCHECKED: 0\n' "$required"
    exit 1
  fi
done

if [ ! -x "$SELF" ]; then
  printf 'VERDICT: FAIL\nCHECKER_NOT_EXECUTABLE: %s\nCHECKED: 0\n' "$SELF"
  exit 1
fi

if ! command -v ruby >/dev/null 2>&1 || ! ruby -rpsych -e 'exit 0' >/dev/null 2>&1; then
  printf 'VERDICT: NOT_RUN\nREASON: Ruby Psych YAML parser unavailable\nCHECKED: 0\n'
  exit 2
fi

runtime_output=$(bash "$RUNTIME_CHECKER" "$PRE_PUSH" 2>&1)
runtime_rc=$?
if [ "$runtime_rc" -ne 0 ]; then
  printf 'VERDICT: FAIL\nPRE_PUSH_RUNTIME_PROOF_FAILED: exit=%s\n%s\nCHECKED: 0\n' \
    "$runtime_rc" "$runtime_output"
  exit 1
fi

ruby -rpsych - "$LEDGER" "$SOURCE" "$SELF" "$PRE_PUSH" "$WORKFLOW" \
  "$GIT_WORKFLOW_SOT" "$VERIFICATION_SOT" <<'RUBY'
ledger_file, source_file, self_file, pre_push_file, workflow_file,
  git_workflow_file, verification_file = ARGV
errors = []

git_workflow_text = File.read(git_workflow_file)
verification_text = File.read(verification_file)
git_workflow_lines = git_workflow_text.lines.map(&:strip)
verification_lines = verification_text.lines.map(&:strip)

work_unit_contracts = [
  ["GIT_ONE_GOAL", :line, git_workflow_lines,
   "Issue 또는 goal 문서 1개 = worktree 1개 = 브랜치 1개 = PR 1개다. PR 하나에는 Work Unit 1~5개만 둘 수 있다."],
  ["GIT_ONE_CLAIM", :line, git_workflow_lines,
   "**Work Unit은 하나의 주장만 만들고, 그 주장을 반증하는 시험까지 통과한 뒤 완료 커밋으로 닫는 최소 작업 단위다.** 파일 수나 줄 수가 아니라 실행으로 참·거짓을 가릴 수 있는 불변조건으로 나눈다."],
  ["GIT_COMMIT_BOUNDARY", :fragment, git_workflow_text,
   "서로 다른 Work Unit 구현을 한 완료 커밋에 섞지 않는다."],
  ["GIT_REVIEW_FIX", :line, git_workflow_lines,
   "독립 검토가 여러 Work Unit에 걸친 결함을 찾으면 하나의 검토 보정 커밋이 영향받은 Work Unit들을 함께 고칠 수 있다. goal 장부는 그 커밋 해시를 영향받은 각 Work Unit의 완료 경계에 기록하며, 이 보정 커밋이 서로 다른 주장을 하나의 Work Unit으로 합치지는 않는다."],
  ["GIT_WU_LIMIT", :fragment, git_workflow_text,
   "여섯 번째 Work Unit이 필요하면 새 Issue 또는 goal 문서와 PR로 나눈다."],
  ["GIT_BRANCH_LIFETIME", :line, git_workflow_lines,
   "- 24~48시간 수명 상한이 Work Unit 1~5개 상한보다 우선한다. 48시간을 넘길 것으로 예상되면 Work Unit이 5개 미만이어도 새 goal·worktree·브랜치·PR로 일찍 나눈다."],
  ["GIT_SQUASH_BOUNDARY", :fragment, git_workflow_text,
   "squash 뒤 `main`의 롤백 경계는 PR 전체 커밋"],
  ["GIT_EXTERNAL_OPTIONAL", :fragment, git_workflow_text,
   "외부 모델·유료 서비스·별도 오케스트레이터가 없어도 기본 절차는 중단되지 않는다."],
  ["VERIFY_STEP_7", :line, verification_lines, "7. 전체 strict"],
  ["VERIFY_STEP_8", :line, verification_lines, "8. 전체 codeaudit"],
  ["VERIFY_STEP_9", :line, verification_lines, "9. 전체 적대검증"],
  ["VERIFY_STEP_10", :line, verification_lines, "10. PR"],
  ["VERIFY_STEP_11", :line, verification_lines, "11. GitHub verify CI"],
  ["VERIFY_STEP_12", :line, verification_lines, "12. CI GREEN 확인 뒤 MERGE"],
  ["VERIFY_PRE_PUSH_NOT_SUBSTITUTE", :fragment, verification_text,
   "9번 전체 적대검증의 Work Unit 결합 공격을 대신하지 않는다."],
  ["VERIFY_GENERAL_WU", :fragment, verification_text,
   "일반 Work Unit은 `IMPLEMENT → 해당 AC 실행 → 반증 1~3개 → 완료 커밋`으로 닫는다."],
  ["VERIFY_HIGH_RISK_CI", :line, verification_lines, "- `.github/workflows/**`"],
  ["VERIFY_HIGH_RISK_HOOKS", :line, verification_lines, "- `hooks/**`"],
  ["VERIFY_HIGH_RISK_ACCEPTANCE", :line, verification_lines,
   "- `scripts/acceptance-*`, `verify*`, `mechanism-registry`"],
  ["VERIFY_HIGH_RISK_DATA", :line, verification_lines, "- 비밀·후보자 데이터 노출 검사"],
  ["VERIFY_HIGH_RISK_RUNTIME", :line, verification_lines, "- 배포·인증·로그인"],
  ["VERIFY_EXECUTION_REVIEW", :fragment, verification_text,
   "고위험 Work Unit을 닫으려면 실행 REVIEW가 필요하다."],
  ["VERIFY_DOCUMENT_REVIEW", :fragment, verification_text,
   "문서 REVIEW의 PASS만으로 고위험 Work Unit을 닫을 수 없다."],
  ["VERIFY_REVIEW_NOT_RUN", :fragment, verification_text,
   "재실행할 수 없으면 실행 REVIEW는 `NOT_RUN`"],
  ["VERIFY_WU_NOT_PR", :fragment, verification_text,
   "Work Unit PASS만으로 PR을 만들거나 병합 완료를 주장하지 않는다."]
]
work_unit_contracts.each do |label, mode, haystack, needle|
  found = mode == :line ? haystack.include?(needle) : haystack.include?(needle)
  errors << "WORK_UNIT_CONTRACT_MISSING: #{label}" unless found
end

raw = File.read(ledger_file)
begin
  ast = Psych.parse_stream(raw, filename: ledger_file)
rescue Psych::SyntaxError => e
  puts "VERDICT: FAIL"
  puts "YAML_PARSE_ERROR: #{e.problem} line=#{e.line} column=#{e.column}"
  puts "CHECKED: 0"
  exit 1
end

walk = nil
walk = lambda do |node, path|
  case node
  when Psych::Nodes::Mapping
    seen = {}
    node.children.each_slice(2).with_index do |(key_node, value_node), index|
      unless key_node.is_a?(Psych::Nodes::Scalar)
        errors << "MAPPING_KEY_INVALID: #{path}[#{index}]"
        next
      end
      key = key_node.value
      errors << "DUPLICATE_KEY: #{path}.#{key}" if seen.key?(key)
      seen[key] = true
      walk.call(value_node, "#{path}.#{key}")
    end
  when Psych::Nodes::Sequence
    node.children.each_with_index { |child, index| walk.call(child, "#{path}[#{index}]") }
  end
end
walk.call(ast, "$")

begin
  data = Psych.safe_load(raw, permitted_classes: [], permitted_symbols: [], aliases: false)
rescue Psych::Exception => e
  errors << "YAML_PARSE_ERROR: #{e.message.lines.first.to_s.strip}"
  data = []
end
unless data.is_a?(Array)
  errors << "ROOT_TYPE_INVALID: expected sequence"
  data = []
end

expected_ids = (1..24).map { |n| "P#{n}" } +
  (1..5).map { |n| "§1-B-#{n}" } +
  (1..5).map { |n| "V-#{n}" }
top_keys = %w[id principle mechanism_expected mechanism_found status evidence]
mechanism_keys = %w[path check stages]
required_stages = %w[strict pre-push ci]
allowed_statuses = %w[PASS FAIL NOT_RUN]

source_titles = {}
in_browser = false
File.foreach(source_file) do |line|
  if line.start_with?("### §1-B.")
    in_browser = true
    next
  elsif line.start_with?("### 검증 체제")
    in_browser = false
  end
  if (match = line.match(/^\| \*\*((?:P\d+)|(?:V-\d+))\*\* \| \*\*(.+?)\*\*/))
    source_titles[match[1]] = match[2]
  elsif in_browser && (match = line.match(/^\| ([1-5]) \| \*\*(.+?)\*\*/))
    source_titles["§1-B-#{match[1]}"] = match[2]
  end
end
if source_titles.keys.sort != expected_ids.sort
  missing = expected_ids - source_titles.keys
  extra = source_titles.keys - expected_ids
  errors << "SOT_ID_SET_MISMATCH: missing=#{missing.join(',')} extra=#{extra.join(',')}"
end

seen_ids = {}
self_targets = 0
data.each_with_index do |entry, index|
  label = "item[#{index}]"
  unless entry.is_a?(Hash)
    errors << "ITEM_TYPE_INVALID: #{label}"
    next
  end
  unknown = entry.keys - top_keys
  missing = top_keys - entry.keys
  errors << "UNKNOWN_FIELD: #{label} #{unknown.join(',')}" unless unknown.empty?
  errors << "MISSING_FIELD: #{label} #{missing.join(',')}" unless missing.empty?
  next unless unknown.empty? && missing.empty?

  id = entry["id"]
  unless id.is_a?(String) && !id.strip.empty?
    errors << "EMPTY_FIELD: #{label}.id"
    next
  end
  errors << "UNKNOWN_ID: #{id}" unless expected_ids.include?(id)
  errors << "ID_DUPLICATE: #{id}" if seen_ids.key?(id)
  seen_ids[id] = true

  %w[principle mechanism_expected evidence].each do |key|
    value = entry[key]
    errors << "EMPTY_FIELD: #{id}.#{key}" unless value.is_a?(String) && !value.strip.empty?
  end
  if source_titles.key?(id) && entry["principle"] != source_titles[id]
    errors << "PRINCIPLE_MISMATCH: #{id} expected=#{source_titles[id].inspect} actual=#{entry['principle'].inspect}"
  end

  status = entry["status"]
  errors << "STATUS_INVALID: #{id}=#{status.inspect}" unless allowed_statuses.include?(status)
  errors << "STATUS_NOT_PASS: #{id}=#{status}" unless status == "PASS"

  mechanisms = entry["mechanism_found"]
  unless mechanisms.is_a?(Array) && !mechanisms.empty?
    errors << "MECHANISM_REQUIRED: #{id}"
    next
  end

  mechanisms.each_with_index do |mechanism, mechanism_index|
    mlabel = "#{id}.mechanism_found[#{mechanism_index}]"
    unless mechanism.is_a?(Hash)
      errors << "MECHANISM_ITEM_INVALID: #{mlabel}"
      next
    end
    unknown_mechanism = mechanism.keys - mechanism_keys
    missing_mechanism = mechanism_keys - mechanism.keys
    errors << "MECHANISM_UNKNOWN_FIELD: #{mlabel} #{unknown_mechanism.join(',')}" unless unknown_mechanism.empty?
    errors << "MECHANISM_MISSING_FIELD: #{mlabel} #{missing_mechanism.join(',')}" unless missing_mechanism.empty?
    next unless unknown_mechanism.empty? && missing_mechanism.empty?

    path = mechanism["path"]
    check = mechanism["check"]
    stages = mechanism["stages"]
    { "PATH" => path, "CHECK" => check }.each do |kind, value|
      unless value.is_a?(String) && !value.strip.empty?
        errors << "MECHANISM_#{kind}_INVALID: #{mlabel}"
        next
      end
      if value.start_with?("/", "~") || value.split("/").include?("..") ||
         value.include?("*") || value.match?(/:\d+\z/)
        errors << "MECHANISM_#{kind}_INVALID: #{mlabel}=#{value}"
        next
      end
      if File.symlink?(value) || !File.file?(value)
        errors << "MECHANISM_#{kind}_MISSING: #{mlabel}=#{value}"
      end
    end
    errors << "MECHANISM_PATH_NOT_SOT: #{mlabel}=#{path}" unless path == source_file
    errors << "MECHANISM_CHECK_NOT_CANONICAL: #{mlabel}=#{check}" unless check == self_file
    self_targets += 1 if check == self_file
    if check.is_a?(String) && File.file?(check) && !File.executable?(check)
      errors << "MECHANISM_CHECK_NOT_EXECUTABLE: #{mlabel}=#{check}"
    end
    unless stages.is_a?(Array) && stages.all? { |stage| stage.is_a?(String) }
      errors << "STAGES_INVALID: #{mlabel}"
      next
    end
    errors << "STAGE_DUPLICATE: #{mlabel}" unless stages.uniq.length == stages.length
    errors << "STAGE_SET_MISMATCH: #{mlabel}=#{stages.inspect}" unless stages.sort == required_stages.sort
  end
end

actual_ids = data.map { |entry| entry["id"] if entry.is_a?(Hash) }.compact
missing_ids = expected_ids - actual_ids
extra_ids = actual_ids - expected_ids
errors << "ID_SET_MISMATCH: missing=#{missing_ids.join(',')} extra=#{extra_ids.join(',')}" unless missing_ids.empty? && extra_ids.empty?
errors << "TARGET_COUNT_INVALID: expected=34 actual=#{data.length}" unless data.length == 34
errors << "SELF_TARGET_COUNT_INVALID: expected=34 actual=#{self_targets}" unless self_targets == 34

pre_push_lines = File.readlines(pre_push_file, chomp: true)
active_pre_push = pre_push_lines.map(&:strip)
  .reject { |line| line.empty? || line.start_with?("#") }
command = "bash scripts/acceptance-principles-check.sh"
# CI 는 2026-08-21 부터 실행 래퍼를 거친다. 래퍼는 종료값 0 인데 판정을 한 건도 내지
# 않은 검사를 불합격시킨다 — 본문을 `exit 0` 으로 바꿔도 초록이던 구멍을 막기 위해서다.
ci_command = "bash scripts/verify/run-acceptance.sh scripts/acceptance-principles-check.sh"
command_lines = active_pre_push.select { |line| line == command }
errors << "PRE_PUSH_EXPLICIT_COMMAND_MISSING: #{command}" unless command_lines.length == 1
active_pre_push.each do |line|
  next unless line.include?("acceptance-principles-check.sh")
  errors << "PRE_PUSH_WEAKENED: #{line}" if line.include?("|| true") || line.match?(/\bif\b.*\bexists\b/i)
end
glob_contract = "-name 'verify.sh' -o -name 'acceptance-*.sh'"
collectors = []
pre_push_lines.each_with_index do |raw, index|
  stripped = raw.strip
  next if stripped.empty? || stripped.start_with?("#")
  collectors << [stripped, index] if stripped.start_with?("found=$(find ")
end
top_level_exit = pre_push_lines.index { |raw| raw.match?(/\Aexit(?:\s|$)/) }
collector_valid = collectors.length == 1 &&
  collectors[0][0].include?(glob_contract) &&
  (top_level_exit.nil? || collectors[0][1] < top_level_exit)
unless collector_valid
  errors << "PRE_PUSH_GLOB_CONTRACT_MISSING: acceptance-*.sh"
end
glob_targets = Dir.glob("scripts/acceptance-*.sh").select { |path| File.file?(path) }
errors << "PRE_PUSH_GLOB_ZERO_TARGETS" if glob_targets.empty?
unless glob_targets.include?(self_file)
  errors << "PRE_PUSH_GLOB_EXCLUDES_SELF: #{self_file}"
end

begin
  workflow = Psych.safe_load(
    File.read(workflow_file),
    permitted_classes: [],
    permitted_symbols: [],
    aliases: false
  )
rescue Psych::Exception => e
  errors << "WORKFLOW_PARSE_ERROR: #{e.message.lines.first.to_s.strip}"
  workflow = {}
end
matched_steps = []
jobs = workflow.is_a?(Hash) ? workflow["jobs"] : nil
if jobs.is_a?(Hash)
  jobs.each do |job_name, job|
    next unless job.is_a?(Hash) && job["steps"].is_a?(Array)
    job["steps"].each_with_index do |step, step_index|
      next unless step.is_a?(Hash) && step["run"].is_a?(String)
      next unless step["run"].strip == ci_command
      matched_steps << [job_name, job, step_index, step]
    end
  end
end
errors << "CI_EXPLICIT_COMMAND_COUNT_INVALID: expected=1 actual=#{matched_steps.length} (#{ci_command})" unless matched_steps.length == 1
matched_steps.each do |job_name, job, step_index, step|
  label = "jobs.#{job_name}.steps[#{step_index}]"
  errors << "CI_JOB_CONDITIONAL: #{label}" if job.key?("if")
  errors << "CI_STEP_CONDITIONAL: #{label}" if step.key?("if")
  errors << "CI_CONTINUE_ON_ERROR: #{label}" if step.key?("continue-on-error")
end

if data.empty?
  errors << "ZERO_TARGETS: no principles inspected"
end

if errors.empty?
  puts "VERDICT: PASS"
  puts "SOT_LOAD: PASS #{source_file}"
  puts "LEDGER_LOAD: PASS #{ledger_file}"
  puts "MECHANISMS: PASS #{self_targets}/34 strict-contract-bindings"
  puts "WIRING: PASS pre-push=1 ci=1"
  puts "WORK_UNIT_METHOD: PASS #{work_unit_contracts.length}/#{work_unit_contracts.length}"
  puts "CHECKED: #{data.length}"
  exit 0
end

puts "VERDICT: FAIL"
errors.each { |error| puts error }
puts "CHECKED: #{data.length}"
puts "FAILURES: #{errors.length}"
exit 1
RUBY
