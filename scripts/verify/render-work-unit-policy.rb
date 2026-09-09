#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative "work_unit_policy"

policy_path = ARGV.fetch(0, "docs/sot/work-unit-policy.yaml")
data, errors = WorkUnitPolicy.load_policy(policy_path)

unless errors.empty?
  puts "VERDICT: FAIL"
  errors.each { |error| puts error }
  exit 1
end

print WorkUnitPolicy.render(data)
