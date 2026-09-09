#!/usr/bin/env ruby
# frozen_string_literal: true

module_path = File.join(__dir__, "work_unit_policy.rb")
if ARGV.length > 2 || !File.file?(module_path) || File.symlink?(module_path) || File.zero?(module_path)
  warn "VERDICT: NOT_RUN\nREASON: invalid arguments or policy module"
  exit 2
end
begin
  require_relative "work_unit_policy"
rescue LoadError, SyntaxError, SystemCallError => e
  warn "VERDICT: NOT_RUN\nREASON: policy runtime unavailable (#{e.class})"
  exit 2
end

policy_path = ARGV.fetch(0, "docs/sot/work-unit-policy.yaml")
document_path = ARGV.fetch(1, "docs/sot/work-unit-policy.md")

data, errors, checked = WorkUnitPolicy.load_policy(policy_path)

if errors.empty?
  actual_document, document_errors = WorkUnitPolicy.read_input(document_path, "DOCUMENT")
  errors.concat(document_errors)
  if errors.empty? && actual_document != WorkUnitPolicy.render(data)
    errors << "DOCUMENT_OUT_OF_SYNC: #{document_path}"
  end
end

if errors.empty?
  puts "VERDICT: PASS"
  puts "POLICY_CHECKED: #{checked}"
  puts "DOCUMENT_SYNC: PASS"
  exit 0
end

puts "VERDICT: FAIL"
errors.each { |error| puts error }
puts "POLICY_CHECKED: #{checked}"
puts "DOCUMENT_SYNC: FAIL"
exit 1
