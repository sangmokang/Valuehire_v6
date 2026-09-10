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

def require_validator(name, label)
  module_path = File.join(__dir__, "#{name}.rb")
  unless File.file?(module_path) && !File.symlink?(module_path) && !File.zero?(module_path)
    warn "VERDICT: NOT_RUN"
    warn "REASON: #{label} module unavailable"
    warn "CHECKED: 0"
    exit 2
  end
  require_relative name
rescue LoadError, SyntaxError, SystemCallError => e
  warn "VERDICT: NOT_RUN"
  warn "REASON: #{label} runtime unavailable (#{e.class})"
  warn "CHECKED: 0"
  exit 2
end

data, errors, checked = WorkUnitManifest.load(ARGV.fetch(0))
unless !errors.empty? || ENV["WORK_UNIT_SCHEMA_ONLY"] == "1"
  repo = ENV.fetch("WORK_UNIT_REPO", Dir.pwd)
  unless ENV["WORK_UNIT_CONTEXT_ONLY"] == "1"
    require_validator("work_unit_git_evidence", "git evidence")
    evidence_errors, evidence_checked = WorkUnitGitEvidence.validate(data, repo)
    errors.concat(evidence_errors)
    checked += evidence_checked
  end
  unless ENV["WORK_UNIT_TDD_ONLY"] == "1"
    require_validator("work_unit_context_evidence", "context evidence")
    context_errors, context_checked = WorkUnitContextEvidence.validate(data, repo)
    errors.concat(context_errors)
    checked += context_checked
  end
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
