#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "work_unit_policy"

policy_path = ARGV.fetch(0, "docs/sot/work-unit-policy.yaml")
document_path = ARGV.fetch(1, "docs/sot/work-unit-policy.md")

data, errors = WorkUnitPolicy.load_policy(policy_path)

if errors.empty?
  begin
    expected_document = WorkUnitPolicy.render(data)
    actual_document = File.read(document_path)
    errors << "DOCUMENT_OUT_OF_SYNC: #{document_path}" unless actual_document == expected_document
  rescue Errno::ENOENT
    errors << "DOCUMENT_FILE_MISSING: #{document_path}"
  end
end

if errors.empty?
  puts "VERDICT: PASS"
  puts "POLICY_CHECKED: #{WorkUnitPolicy::POLICY_CHECKED}"
  puts "DOCUMENT_SYNC: PASS"
  exit 0
end

puts "VERDICT: FAIL"
errors.each { |error| puts error }
puts "POLICY_CHECKED: 0"
puts "DOCUMENT_SYNC: FAIL"
exit 1
