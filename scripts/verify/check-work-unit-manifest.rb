#!/usr/bin/env ruby
# frozen_string_literal: true

# Executable CLI/type boundary. WU-1 RED proves the validation behavior is absent.
if ARGV.length != 1
  warn "VERDICT: NOT_RUN"
  warn "REASON: usage: check-work-unit-manifest.rb <manifest.yaml>"
  warn "CHECKED: 0"
  exit 2
end

puts "VERDICT: NOT_RUN"
puts "REASON: work unit manifest validation not implemented"
puts "CHECKED: 0"
exit 2
