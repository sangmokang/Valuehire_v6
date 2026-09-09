#!/usr/bin/env ruby
# frozen_string_literal: true

module_path = File.join(__dir__, "work_unit_policy.rb")
if ARGV.length > 1 || !File.file?(module_path) || File.symlink?(module_path) || File.zero?(module_path)
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
data, errors = WorkUnitPolicy.load_policy(policy_path)

unless errors.empty?
  warn "VERDICT: FAIL"
  errors.each { |error| warn error }
  exit 1
end

print WorkUnitPolicy.render(data)
