#!/usr/bin/env ruby
# frozen_string_literal: true

require "fileutils"
require "open3"
require "psych"
require "tmpdir"

repo_root = File.expand_path("../..", __dir__)
checker = File.join(repo_root, "scripts/verify/check-work-unit-manifest.rb")
base = Psych.safe_load(
  File.read(File.join(repo_root, "scripts/verify/fixtures/work-unit/valid.yaml")),
  aliases: false
)
clean_env = %w[
  GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
].map { |key| [key, nil] }.to_h

run = lambda do |dir, env, *command|
  out, err, status = Open3.capture3(clean_env.merge(env), *command, chdir: dir)
  [status.exitstatus, out + err]
end

checked = 0
failed = 0
missing_behavior = false
assert = lambda do |label, ok, output|
  checked += 1
  if ok
    puts "PASS: #{label}"
  else
    failed += 1
    missing_behavior = true
    puts "FAIL: #{label}"
    puts output
  end
end

Dir.mktmpdir("wu-not-applicable-") do |tmp|
  repo = File.join(tmp, "repo")
  FileUtils.mkdir_p(repo)
  [%w[init -q], %w[config user.email na@example.invalid], %w[config user.name na-test]].each do |args|
    rc, out = run.call(repo, {}, "git", *args)
    raise out unless rc.zero?
  end
  File.write(File.join(repo, "README.md"), "# Documentation-only change\n")
  run.call(repo, {}, "git", "add", "README.md")
  run.call(repo, {}, "git", "commit", "-q", "-m", "documentation contract")
  _rc, head = run.call(repo, {}, "git", "rev-parse", "HEAD")
  head.strip!

  manifest = Marshal.load(Marshal.dump(base))
  unit = manifest.fetch("work_units").first
  unit["id"] = "WU-NOT-APPLICABLE"
  unit["tdd"] = {
    "mode" => "NOT_APPLICABLE", "contract_commit" => head,
    "red_commit" => nil, "green_commit" => nil, "red_commands" => [],
    "red_tests" => 0, "red_failure_kind" => nil, "test_files" => [],
    "expectation_change_approval_commit" => nil
  }
  unit["not_applicable"] = {
    "change_kind" => "documentation",
    "reason" => "Only prose changed, so executable unit behavior does not exist.",
    "alternative_validation_commands" => ["test -s README.md"]
  }

  invoke = lambda do |name, candidate|
    path = File.join(tmp, "#{name}.yaml")
    File.write(path, Psych.dump(candidate))
    run.call(
      repo_root,
      { "WORK_UNIT_REPO" => repo, "WORK_UNIT_NOT_APPLICABLE_ONLY" => "1" },
      "ruby", checker, path
    )
  end

  rc, out = invoke.call("normal", manifest)
  assert.call("documented alternative validation", rc.zero? && out.include?("VERDICT: PASS"), out)

  missing_reason = Marshal.load(Marshal.dump(manifest))
  missing_reason["work_units"].first["not_applicable"]["reason"] = ""
  rc, out = invoke.call("missing-reason", missing_reason)
  assert.call("missing reason rejected", rc == 1 && out.include?("NOT_APPLICABLE_REASON_REQUIRED"), out)

  zero_commands = Marshal.load(Marshal.dump(manifest))
  zero_commands["work_units"].first["not_applicable"]["alternative_validation_commands"] = []
  rc, out = invoke.call("zero-commands", zero_commands)
  assert.call("zero alternative commands rejected", rc == 1 && out.include?("ALTERNATIVE_COMMAND_REQUIRED"), out)

  unsupported = Marshal.load(Marshal.dump(manifest))
  unsupported["work_units"].first["not_applicable"]["change_kind"] = "backend_behavior"
  rc, out = invoke.call("unsupported-kind", unsupported)
  assert.call("unsupported change kind rejected", rc == 1 && out.include?("NOT_APPLICABLE_KIND_INVALID"), out)

  mixed = Marshal.load(Marshal.dump(manifest))
  mixed_unit = mixed["work_units"].first
  mixed_unit["tdd"] = Marshal.load(Marshal.dump(base["work_units"].first["tdd"]))
  rc, out = invoke.call("red-green-mixed", mixed)
  assert.call("RED_GREEN with waiver rejected", rc == 1 && out.include?("NOT_APPLICABLE_MODE_CONFLICT"), out)
end

puts "WU_TESTS: #{checked}"
puts "CHECKED: #{checked}"
puts "WU_FAILURE_KIND: missing_behavior" if missing_behavior
puts "VERDICT: #{failed.zero? ? 'PASS' : 'FAIL'}"
exit(failed.zero? ? 0 : 1)
