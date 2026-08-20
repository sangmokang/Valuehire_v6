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

for required in "$SOURCE" "$LEDGER" "$SELF" "$PRE_PUSH" "$WORKFLOW" "$RUNTIME_CHECKER"; do
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

ruby -rpsych - "$LEDGER" "$SOURCE" "$SELF" "$PRE_PUSH" "$WORKFLOW" <<'RUBY'
ledger_file, source_file, self_file, pre_push_file, workflow_file = ARGV
errors = []

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

expected_ids = (1..22).map { |n| "P#{n}" } +
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
errors << "TARGET_COUNT_INVALID: expected=32 actual=#{data.length}" unless data.length == 32
errors << "SELF_TARGET_COUNT_INVALID: expected=32 actual=#{self_targets}" unless self_targets == 32

pre_push_lines = File.readlines(pre_push_file, chomp: true)
active_pre_push = pre_push_lines.map(&:strip)
  .reject { |line| line.empty? || line.start_with?("#") }
command = "bash scripts/acceptance-principles-check.sh"
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
      next unless step["run"].strip == command
      matched_steps << [job_name, job, step_index, step]
    end
  end
end
errors << "CI_EXPLICIT_COMMAND_COUNT_INVALID: expected=1 actual=#{matched_steps.length}" unless matched_steps.length == 1
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
  puts "MECHANISMS: PASS #{self_targets}/32 strict-contract-bindings"
  puts "WIRING: PASS pre-push=1 ci=1"
  puts "CHECKED: #{data.length}"
  exit 0
end

puts "VERDICT: FAIL"
errors.each { |error| puts error }
puts "CHECKED: #{data.length}"
puts "FAILURES: #{errors.length}"
exit 1
RUBY
