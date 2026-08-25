#!/usr/bin/env bash
# check-ci-step-integrity.sh — 보호 CI step의 선언을 구조화 정본과 정확히 대조한다.
#
# 이 검사는 GitHub runner의 실제 실행을 증명하지 않는다. 지정 workflow가 승인된
# job·step·run·if·continue-on-error 계약을 선언했는지만 판정한다. 실행 귀속은 현재
# SHA의 원격 check 결과를 확인하는 별도 단계가 맡는다.
set -uo pipefail

WORKFLOW="${1:-.github/workflows/verify.yml}"
CONTRACT="${2:-docs/sot/ci-required-steps.json}"
EXPECTED_CONTRACT_SHA256="168c9527d393973fce462a795ab399557c1e6c9a848ab57264a9f8f9e507d27a"

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

def normalized_lines(value)
  return nil unless value.is_a?(String)
  lines = value.gsub("\r\n", "\n").split("\n", -1)
  lines.pop while lines.last == ""
  lines.map { |line| line.sub(/[ \t]+\z/, "") }
end

begin
  contract = JSON.parse(File.read(contract_path))
rescue JSON::ParserError => e
  not_run("CI step 계약 파싱 실패 — #{e.message.lines.first.to_s.strip}")
end

required_root = %w[protected_steps schema_version workflow]
unless contract.is_a?(Hash) && contract.keys.sort == required_root &&
       contract["schema_version"] == 1 &&
       contract["workflow"] == ".github/workflows/verify.yml"
  not_run("CI step 계약 root/schema가 올바르지 않다")
end

specs = contract["protected_steps"]
not_run("보호 대상이 0개다 — 0건 대조로 통과할 수 없다") unless specs.is_a?(Array) && !specs.empty?

spec_keys = %w[allow_continue_on_error if job name run_lines]
seen = {}
specs.each_with_index do |spec, index|
  unless spec.is_a?(Hash) && spec.keys.sort == spec_keys &&
         spec["job"].is_a?(String) && !spec["job"].empty? &&
         spec["name"].is_a?(String) && !spec["name"].empty? &&
         spec["run_lines"].is_a?(Array) && !spec["run_lines"].empty? &&
         spec["run_lines"].all? { |line| line.is_a?(String) } &&
         (spec["if"].nil? || spec["if"].is_a?(String)) &&
         spec["allow_continue_on_error"] == false
    not_run("보호 대상 ##{index + 1}의 schema가 올바르지 않다")
  end
  key = [spec["job"], spec["name"]]
  not_run("계약에 보호 대상이 중복됐다 — #{key.join(" / ")}") if seen[key]
  seen[key] = true
end

actual_digest = Digest::SHA256.file(contract_path).hexdigest
if actual_digest != expected_digest
  puts "FAIL: CI step 계약 digest 불일치 — 승인된 정본과 다르다"
  puts "CHECKED: 0"
  exit 1
end

begin
  workflow = Psych.safe_load(File.read(workflow_path), aliases: true, permitted_classes: [Date, Time])
rescue Psych::Exception => e
  not_run("워크플로 파싱 실패 — #{e.message.lines.first.to_s.strip}")
end

jobs = workflow.is_a?(Hash) ? workflow["jobs"] : nil
not_run("jobs를 읽지 못했다 — 검사 대상 0개는 합격이 아니다") unless jobs.is_a?(Hash) && !jobs.empty?

errors = []
jobs.each do |job_id, job|
  next unless job.is_a?(Hash)
  errors << "JOB_CONDITIONAL: jobs.#{job_id}에 if가 있다" if job.key?("if")
  errors << "JOB_CONTINUE_ON_ERROR: jobs.#{job_id}에 continue-on-error가 있다" if job.key?("continue-on-error")
  Array(job["steps"]).each_with_index do |step, index|
    next unless step.is_a?(Hash)
    name = step["name"]
    allowed_if = specs.any? { |spec| spec["job"] == job_id && spec["name"] == name && !spec["if"].nil? }
    errors << "STEP_CONDITIONAL: jobs.#{job_id}.steps[#{index}]에 허용되지 않은 if가 있다" if step.key?("if") && !allowed_if
    errors << "STEP_CONTINUE_ON_ERROR: jobs.#{job_id}.steps[#{index}]에 continue-on-error가 있다" if step.key?("continue-on-error")
  end
end

specs.each do |spec|
  job_id = spec["job"]
  name = spec["name"]
  job = jobs[job_id]
  unless job.is_a?(Hash)
    errors << "JOB_MISSING: #{job_id}"
    next
  end
  matches = Array(job["steps"]).select { |step| step.is_a?(Hash) && step["name"] == name }
  if matches.length != 1
    errors << "STEP_CARDINALITY: jobs.#{job_id}.#{name} count=#{matches.length} expected=1"
    next
  end

  step = matches.first
  actual_lines = normalized_lines(step["run"])
  errors << "RUN_MISMATCH: jobs.#{job_id}.#{name}" unless actual_lines == spec["run_lines"]
  if spec["if"].nil?
    errors << "IF_MISMATCH: jobs.#{job_id}.#{name}은 if가 없어야 한다" if step.key?("if")
  elsif !step.key?("if") || step["if"] != spec["if"]
    errors << "IF_MISMATCH: jobs.#{job_id}.#{name}의 if가 승인값과 다르다"
  else
    puts "ALLOWED: #{name} — exact if=#{spec["if"].inspect}"
  end
  errors << "CONTINUE_ON_ERROR: jobs.#{job_id}.#{name}은 continue-on-error가 없어야 한다" if step.key?("continue-on-error")
end

if errors.empty?
  puts "PASS: 보호 CI step의 job·name·run·if·continue-on-error 계약 일치"
  puts "CHECKED: #{specs.length}"
  exit 0
end

errors.uniq.each { |error| puts "FAIL: #{error}" }
puts "CHECKED: #{specs.length}"
exit 1
' "$WORKFLOW" "$CONTRACT" "$EXPECTED_CONTRACT_SHA256"
