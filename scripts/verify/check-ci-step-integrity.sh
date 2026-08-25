#!/usr/bin/env bash
# check-ci-step-integrity.sh — 보호 CI step의 선언을 구조화 정본과 정확히 대조한다.
#
# 이 검사는 GitHub runner의 실제 실행을 증명하지 않는다. 지정 workflow가 승인된
# job·step·run·if·continue-on-error 계약을 선언했는지만 판정한다. 실행 귀속은 현재
# SHA의 원격 check 결과를 확인하는 별도 단계가 맡는다.
set -uo pipefail

WORKFLOW="${1:-.github/workflows/verify.yml}"
CONTRACT="${2:-docs/sot/ci-required-steps.json}"
EXPECTED_CONTRACT_SHA256="550bdefbd824dacc066b98241e94991285b329a371200923b595e3e5032b2d3a"

if [ ! -f "$WORKFLOW" ]; then
  echo "NOT_RUN: 워크플로 파일이 없다 — $WORKFLOW"
  echo "CHECKED: 0"
  exit 2
fi
if [ ! -f "$CONTRACT" ]; then
  echo "NOT_RUN: CI step 계약 파일이 없다 — $CONTRACT"
  echo "CHECKED: 0"
  exit 2
fi

ruby -rpsych -rdate -rjson -rdigest -e '
workflow_path, contract_path, expected_digest = ARGV

def not_run(message)
  puts "NOT_RUN: #{message}"
  puts "CHECKED: 0"
  exit 2
end

class JsonDuplicateKeyScanner
  def initialize(source)
    @source = source
    @index = 0
  end

  def scan
    skip_whitespace
    scan_value
    skip_whitespace
    raise JSON::ParserError, "JSON 뒤에 해석되지 않은 입력이 있다" unless @index == @source.length
  end

  private

  def scan_value
    skip_whitespace
    case @source[@index]
    when "{" then scan_object
    when "[" then scan_array
    when "\"" then scan_string
    else scan_scalar
    end
  end

  def scan_object
    @index += 1
    skip_whitespace
    return @index += 1 if @source[@index] == "}"

    seen = {}
    loop do
      key = scan_string
      raise JSON::ParserError, "중복 object key — #{key}" if seen[key]
      seen[key] = true
      skip_whitespace
      expect(":")
      scan_value
      skip_whitespace
      break if consume("}")
      expect(",")
      skip_whitespace
    end
  end

  def scan_array
    @index += 1
    skip_whitespace
    return @index += 1 if @source[@index] == "]"

    loop do
      scan_value
      skip_whitespace
      break if consume("]")
      expect(",")
      skip_whitespace
    end
  end

  def scan_string
    start = @index
    expect("\"")
    loop do
      char = @source[@index]
      raise JSON::ParserError, "끝나지 않은 JSON string" if char.nil?
      @index += char == "\\" ? 2 : 1
      break if char == "\""
    end
    JSON.parse(@source[start...@index])
  end

  def scan_scalar
    start = @index
    @index += 1 while @source[@index] && @source[@index] !~ /[\s,}\]]/
    raise JSON::ParserError, "비어 있는 JSON 값" if start == @index
  end

  def skip_whitespace
    @index += 1 while @source[@index] =~ /\s/
  end

  def consume(token)
    return false unless @source[@index] == token
    @index += 1
    true
  end

  def expect(token)
    raise JSON::ParserError, "JSON token #{token.inspect} 누락" unless consume(token)
  end
end

def load_contract(path)
  source = File.read(path)
  contract = JSON.parse(source)
  JsonDuplicateKeyScanner.new(source).scan
  contract
rescue JSON::ParserError => error
  not_run("CI step 계약 파싱 실패 — #{error.message.lines.first.to_s.strip}")
end

def validate_contract(contract)
  root_keys = %w[protected_jobs protected_steps schema_version workflow workflow_context]
  valid_root = contract.is_a?(Hash) && contract.keys.sort == root_keys &&
               contract["schema_version"] == 2 &&
               contract["workflow"] == ".github/workflows/verify.yml" &&
               contract["workflow_context"].is_a?(Hash) &&
               contract["workflow_context"].keys.sort == %w[defaults env] &&
               contract["workflow_context"].values.all? { |value| value == "absent" }
  not_run("CI step 계약 root/schema가 올바르지 않다") unless valid_root

  job_specs = contract["protected_jobs"]
  specs = contract["protected_steps"]
  not_run("보호 job이 0개다 — 0건 대조로 통과할 수 없다") unless job_specs.is_a?(Array) && !job_specs.empty?
  not_run("보호 대상이 0개다 — 0건 대조로 통과할 수 없다") unless specs.is_a?(Array) && !specs.empty?

  job_ids = {}
  job_specs.each_with_index do |spec, index|
    allowed = spec.is_a?(Hash) ? spec["allowed_keys"] : nil
    valid = spec.is_a?(Hash) && spec.keys.sort == %w[allowed_keys id runs_on] &&
            spec["id"].is_a?(String) && !spec["id"].empty? &&
            spec["runs_on"].is_a?(String) && !spec["runs_on"].empty? &&
            allowed.is_a?(Array) && !allowed.empty? && allowed.all? { |key| key.is_a?(String) } &&
            allowed.uniq.length == allowed.length && allowed.include?("runs-on") && allowed.include?("steps")
    not_run("보호 job ##{index + 1}의 schema가 올바르지 않다") unless valid
    not_run("계약에 보호 job이 중복됐다 — #{spec["id"]}") if job_ids[spec["id"]]
    job_ids[spec["id"]] = true
  end

  seen = {}
  specs.each_with_index do |spec, index|
    allowed = spec.is_a?(Hash) ? spec["allowed_keys"] : nil
    valid = spec.is_a?(Hash) && spec.keys.sort == %w[allowed_keys if job name run_lines] &&
            job_ids[spec["job"]] && spec["name"].is_a?(String) && !spec["name"].empty? &&
            spec["run_lines"].is_a?(Array) && !spec["run_lines"].empty? &&
            spec["run_lines"].all? { |line| line.is_a?(String) } &&
            allowed.is_a?(Array) && allowed.uniq.length == allowed.length &&
            allowed.all? { |key| key.is_a?(String) } && allowed.include?("name") && allowed.include?("run") &&
            (spec["if"].nil? ? !allowed.include?("if") : spec["if"].is_a?(String) && allowed.include?("if"))
    not_run("보호 대상 ##{index + 1}의 schema가 올바르지 않다") unless valid
    key = [spec["job"], spec["name"]]
    not_run("계약에 보호 대상이 중복됐다 — #{key.join(" / ")}") if seen[key]
    seen[key] = true
  end
  [job_specs, specs]
end

def reject_ambiguous_yaml(source)
  ast = Psych.parse_stream(source)
  violations = []
  walk = nil
  walk = lambda do |node|
    violations << "alias" if node.is_a?(Psych::Nodes::Alias)
    violations << "anchor" if node.respond_to?(:anchor) && node.anchor
    if node.is_a?(Psych::Nodes::Mapping)
      keys = Array(node.children).each_slice(2).map(&:first)
      violations << "non-scalar mapping key" unless keys.all? { |key| key.is_a?(Psych::Nodes::Scalar) }
      scalar_keys = keys.select { |key| key.is_a?(Psych::Nodes::Scalar) }.map(&:value)
      violations << "merge key <<" if scalar_keys.include?("<<")
      duplicates = scalar_keys.group_by(&:itself).select { |_key, values| values.length > 1 }.keys
      violations.concat(duplicates.map { |key| "duplicate mapping key #{key}" })
    end
    Array(node.respond_to?(:children) ? node.children : nil).each { |child| walk.call(child) }
  end
  walk.call(ast)
  not_run("워크플로 YAML 모호성 거부 — #{violations.uniq.join(", ")}") unless violations.empty?
rescue Psych::Exception => error
  not_run("워크플로 파싱 실패 — #{error.message.lines.first.to_s.strip}")
end

def normalized_lines(value)
  return nil unless value.is_a?(String)
  lines = value.gsub("\r\n", "\n").split("\n", -1)
  lines.pop if lines.last == ""
  lines.map { |line| line.sub(/[ \t]+\z/, "") }
end

contract = load_contract(contract_path)
job_specs, specs = validate_contract(contract)

actual_digest = Digest::SHA256.file(contract_path).hexdigest
if actual_digest != expected_digest
  puts "FAIL: CI step 계약 digest 불일치 — 승인된 정본과 다르다"
  puts "CHECKED: 0"
  exit 1
end

workflow_source = File.read(workflow_path)
reject_ambiguous_yaml(workflow_source)
begin
  workflow = Psych.safe_load(workflow_source, aliases: false, permitted_classes: [Date, Time])
rescue Psych::Exception => error
  not_run("워크플로 파싱 실패 — #{error.message.lines.first.to_s.strip}")
end

jobs = workflow.is_a?(Hash) ? workflow["jobs"] : nil
not_run("jobs를 읽지 못했다 — 검사 대상 0개는 합격이 아니다") unless jobs.is_a?(Hash) && !jobs.empty?

errors = []
context = contract["workflow_context"]
%w[env defaults].each do |key|
  errors << "WORKFLOW_CONTEXT: root.#{key}는 없어야 한다" if context[key] == "absent" && workflow.key?(key)
end

job_specs.each do |spec|
  job_id = spec["id"]
  job = jobs[job_id]
  unless job.is_a?(Hash)
    errors << "JOB_MISSING: #{job_id}"
    next
  end
  errors << "JOB_KEYS_MISMATCH: jobs.#{job_id} actual=#{job.keys.sort.inspect} expected=#{spec["allowed_keys"].sort.inspect}" unless job.keys.sort == spec["allowed_keys"].sort
  errors << "RUNS_ON_MISMATCH: jobs.#{job_id}" unless job["runs-on"] == spec["runs_on"]
  errors << "JOB_STEPS_INVALID: jobs.#{job_id}" unless job["steps"].is_a?(Array)
end

specs.each do |spec|
  job_id = spec["job"]
  name = spec["name"]
  job = jobs[job_id]
  next unless job.is_a?(Hash)
  matches = Array(job["steps"]).select { |step| step.is_a?(Hash) && step["name"] == name }
  if matches.length != 1
    errors << "STEP_CARDINALITY: jobs.#{job_id}.#{name} count=#{matches.length} expected=1"
    next
  end

  step = matches.first
  errors << "STEP_KEYS_MISMATCH: jobs.#{job_id}.#{name} actual=#{step.keys.sort.inspect} expected=#{spec["allowed_keys"].sort.inspect}" unless step.keys.sort == spec["allowed_keys"].sort
  errors << "RUN_MISMATCH: jobs.#{job_id}.#{name}" unless normalized_lines(step["run"]) == spec["run_lines"]
  if spec["if"].nil?
    errors << "IF_MISMATCH: jobs.#{job_id}.#{name}은 if가 없어야 한다" if step.key?("if")
  elsif !step.key?("if") || step["if"] != spec["if"]
    errors << "IF_MISMATCH: jobs.#{job_id}.#{name}의 if가 승인값과 다르다"
  else
    puts "ALLOWED: #{name} — exact if=#{spec["if"].inspect}"
  end
end

if errors.empty?
  puts "PASS: workflow context와 보호 CI job·step exact 계약 일치"
  puts "CHECKED: #{specs.length}"
  exit 0
end

errors.uniq.each { |error| puts "FAIL: #{error}" }
puts "CHECKED: #{specs.length}"
exit 1
' "$WORKFLOW" "$CONTRACT" "$EXPECTED_CONTRACT_SHA256"
