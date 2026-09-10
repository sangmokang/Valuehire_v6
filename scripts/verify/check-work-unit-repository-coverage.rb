#!/usr/bin/env ruby
# frozen_string_literal: true

require "psych"

if ARGV.length < 2
  warn "VERDICT: NOT_RUN"
  warn "REASON: usage: check-work-unit-repository-coverage.rb <policy.yaml> <manifest.yaml>..."
  warn "CHECKED: 0"
  exit 2
end

begin
  policy = Psych.safe_load(File.read(ARGV.fetch(0)), permitted_classes: [], aliases: false)
  required = policy.dig("enforcement", "required_repository_work_unit_ids")
  raise "required Work Unit IDs unavailable" unless required.is_a?(Array) && !required.empty?

  actual = ARGV.drop(1).flat_map do |path|
    manifest = Psych.safe_load(File.read(path), permitted_classes: [], aliases: false)
    units = manifest.fetch("work_units")
    units.map { |unit| unit.fetch("id") }
  end
rescue Psych::Exception, KeyError, SystemCallError, RuntimeError => e
  warn "VERDICT: NOT_RUN"
  warn "REASON: repository WU coverage unavailable (#{e.class}: #{e.message})"
  warn "CHECKED: 0"
  exit 2
end

errors = []
counts = actual.each_with_object(Hash.new(0)) { |id, memo| memo[id] += 1 }
duplicates = counts.select { |_id, count| count > 1 }.keys
missing = required - actual
unexpected = actual - required
errors << "REPOSITORY_WU_ID_DUPLICATE: #{duplicates.join(',')}" unless duplicates.empty?
errors << "REQUIRED_WU_MISSING: #{missing.join(',')}" unless missing.empty?
errors << "UNDECLARED_WU_PRESENT: #{unexpected.join(',')}" unless unexpected.empty?

puts "VERDICT: #{errors.empty? ? 'PASS' : 'FAIL'}"
errors.each { |error| puts error }
puts "CHECKED: #{required.length + actual.length}"
exit(errors.empty? ? 0 : 1)
