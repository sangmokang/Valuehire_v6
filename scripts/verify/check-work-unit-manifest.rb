#!/usr/bin/env ruby
# frozen_string_literal: true

# Executable CLI/type boundary. The policy YAML remains the authority.
if ARGV.length != 1
  warn "VERDICT: NOT_RUN"
  warn "REASON: usage: check-work-unit-manifest.rb <manifest.yaml>"
  warn "CHECKED: 0"
  exit 2
end

module_path = File.join(__dir__, "work_unit_manifest.rb")
unless File.file?(module_path) && !File.symlink?(module_path) && !File.zero?(module_path)
  warn "VERDICT: NOT_RUN"
  warn "REASON: manifest validator module unavailable"
  warn "CHECKED: 0"
  exit 2
end

begin
  require_relative "work_unit_manifest"
rescue LoadError, SyntaxError, SystemCallError => e
  warn "VERDICT: NOT_RUN"
  warn "REASON: manifest validator runtime unavailable (#{e.class})"
  warn "CHECKED: 0"
  exit 2
end

data, errors, checked = WorkUnitManifest.load(ARGV.fetch(0))
unless !errors.empty? || ENV["WORK_UNIT_SCHEMA_ONLY"] == "1"
  evidence_module = File.join(__dir__, "work_unit_git_evidence.rb")
  unless File.file?(evidence_module) && !File.symlink?(evidence_module) && !File.zero?(evidence_module)
    warn "VERDICT: NOT_RUN"
    warn "REASON: git evidence module unavailable"
    warn "CHECKED: 0"
    exit 2
  end
  begin
    require_relative "work_unit_git_evidence"
  rescue LoadError, SyntaxError, SystemCallError => e
    warn "VERDICT: NOT_RUN"
    warn "REASON: git evidence runtime unavailable (#{e.class})"
    warn "CHECKED: 0"
    exit 2
  end
  repo = ENV.fetch("WORK_UNIT_REPO", Dir.pwd)
  evidence_errors, evidence_checked = WorkUnitGitEvidence.validate(data, repo)
  errors.concat(evidence_errors)
  checked += evidence_checked
end
if errors.empty?
  puts "VERDICT: PASS"
  puts "CHECKED: #{checked}"
  exit 0
end

puts "VERDICT: FAIL"
errors.each { |error| puts error }
puts "CHECKED: #{checked}"
exit 1
