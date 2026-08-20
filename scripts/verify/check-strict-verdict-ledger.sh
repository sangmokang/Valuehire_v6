#!/usr/bin/env bash
# G/V1/V2/T 실행 장부가 실제 실행 증거와 fail-closed 상태를 갖는지 검증한다.
set -uo pipefail

LEDGER=${1:-docs/engineering/strict-principles-verdict-2026-08-20.yaml}
if [ ! -f "$LEDGER" ] || [ -L "$LEDGER" ] || [ ! -s "$LEDGER" ]; then
  printf 'VERDICT: FAIL\nLEDGER_INVALID: %s\nCHECKED: 0\n' "$LEDGER"
  exit 1
fi
if ! command -v ruby >/dev/null 2>&1 || ! ruby -rpsych -e 'exit 0' >/dev/null 2>&1; then
  printf 'VERDICT: NOT_RUN\nREASON: Ruby Psych unavailable\nCHECKED: 0\n'
  exit 2
fi
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  printf 'VERDICT: NOT_RUN\nREASON: not a git repository\nCHECKED: 0\n'
  exit 2
}
cd "$REPO" || {
  printf 'VERDICT: NOT_RUN\nREASON: cannot enter repository root\nCHECKED: 0\n'
  exit 2
}

ruby -rpsych - "$LEDGER" <<'RUBY'
require "digest"

file = ARGV[0]
errors = []
begin
  data = Psych.safe_load(File.read(file), permitted_classes: [], permitted_symbols: [], aliases: false)
rescue Psych::Exception => e
  puts "VERDICT: FAIL"
  puts "YAML_PARSE_ERROR: #{e.message.lines.first.to_s.strip}"
  puts "CHECKED: 0"
  exit 1
end
unless data.is_a?(Hash)
  puts "VERDICT: FAIL"
  puts "ROOT_TYPE_INVALID"
  puts "CHECKED: 0"
  exit 1
end

roles = %w[g v1 v2 t]
allowed_statuses = %w[PASS FAIL NOT_RUN]
top_keys = ["verdict", *roles]
role_keys = %w[status command exit output artifact artifact_hash session_id]
errors << "TOP_LEVEL_KEYS_INVALID: #{data.keys.inspect}" unless data.keys.sort == top_keys.sort
final_verdict = data["verdict"]
errors << "FINAL_VERDICT_INVALID: #{final_verdict.inspect}" unless allowed_statuses.include?(final_verdict)
roles.each do |role|
  item = data[role]
  unless item.is_a?(Hash)
    errors << "ROLE_MISSING: #{role}"
    next
  end
  unknown_keys = item.keys - role_keys
  missing_keys = role_keys - item.keys
  errors << "ROLE_UNKNOWN_FIELDS: #{role}=#{unknown_keys.join(',')}" unless unknown_keys.empty?
  errors << "ROLE_MISSING_FIELDS: #{role}=#{missing_keys.join(',')}" unless missing_keys.empty?
  status = item["status"]
  errors << "STATUS_INVALID: #{role}=#{status.inspect}" unless allowed_statuses.include?(status)
  %w[command output artifact artifact_hash session_id].each do |key|
    value = item[key]
    errors << "EVIDENCE_MISSING: #{role}.#{key}" unless value.is_a?(String) && !value.strip.empty?
  end
  exit_value = item["exit"]
  unless exit_value.is_a?(Integer)
    errors << "EXIT_INVALID: #{role}=#{exit_value.inspect}"
  end
  if status == "PASS" && exit_value != 0
    errors << "PASS_WITH_NONZERO_EXIT: #{role}=#{exit_value.inspect}"
  end
  hash = item["artifact_hash"]
  errors << "HASH_INVALID: #{role}" unless hash.is_a?(String) && hash.match?(/\A[0-9a-f]{64}\z/)
  artifact = item["artifact"]
  artifact_valid = artifact.is_a?(String) && !artifact.strip.empty? &&
    !artifact.start_with?("/", "~") && !artifact.split("/").include?("..") &&
    !artifact.match?(/[\*?\[]/) && !artifact.match?(/:\d+\z/)
  unless artifact_valid
    errors << "ARTIFACT_PATH_INVALID: #{role}=#{artifact.inspect}"
    next
  end
  if File.symlink?(artifact) || !File.file?(artifact)
    errors << "ARTIFACT_MISSING: #{role}=#{artifact}"
    next
  end
  if hash.is_a?(String) && hash.match?(/\A[0-9a-f]{64}\z/)
    actual_hash = Digest::SHA256.file(artifact).hexdigest
    errors << "ARTIFACT_HASH_MISMATCH: #{role}=#{artifact}" unless actual_hash == hash
  end
end

v1_status = data.dig("v1", "status")
v2_status = data.dig("v2", "status")
statuses = roles.map { |role| data.dig(role, "status") }
derived_verdict = if statuses.include?("FAIL")
  "FAIL"
elsif statuses.include?("NOT_RUN")
  "NOT_RUN"
elsif statuses.all? { |status| status == "PASS" }
  "PASS"
end
errors << "FINAL_VERDICT_MISMATCH: expected=#{derived_verdict.inspect} actual=#{final_verdict.inspect}" unless final_verdict == derived_verdict
if v1_status == "FAIL" && final_verdict == "PASS"
  errors << "FALSE_PASS_AFTER_V1_FAIL"
end
if v1_status == "FAIL" && v2_status == "NOT_RUN"
  errors << "V2_REQUIRED_AFTER_V1_FAIL: #{v2_status.inspect}"
end

unless errors.empty?
  puts "VERDICT: FAIL"
  errors.each { |error| puts error }
  puts "CHECKED: 4"
  puts "FAILURES: #{errors.length}"
  exit 1
end

if final_verdict == "PASS"
  puts "VERDICT: PASS"
  puts "ROLES: PASS G/V1/V2/T"
  puts "CHECKED: 4"
  exit 0
end
puts "VERDICT: #{final_verdict}"
puts "ROLES: #{roles.zip(statuses).map { |role, status| "#{role.upcase}=#{status}" }.join(' ')}"
puts "CHECKED: 4"
exit(final_verdict == "NOT_RUN" ? 2 : 1)
RUBY
