#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
require "fileutils"
require "open3"
require "psych"
require "tmpdir"

repo_root = File.expand_path("../..", __dir__)
checker = File.join(repo_root, "scripts/verify/check-work-unit-manifest.rb")
fixture = File.join(repo_root, "scripts/verify/fixtures/work-unit/valid.yaml")
base_manifest = Psych.safe_load(File.read(fixture), aliases: false)
git_env = %w[
  GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
].map { |key| [key, nil] }.to_h

run = lambda do |dir, env, *command|
  out, err, status = Open3.capture3(git_env.merge(env), *command, chdir: dir)
  [status.exitstatus, out + err]
end

write_test = lambda do |path, syntax_error: false, expected: true|
  body = if syntax_error
           "def broken(\n"
         else
           <<~RUBY
             require_relative "../lib/feature"
             puts "WU_TESTS: 1"
             if Feature.enabled? == #{expected}
               puts "VERDICT: PASS"
               exit 0
             end
             puts "WU_FAILURE_KIND: missing_behavior"
             puts "VERDICT: FAIL"
             exit 1
           RUBY
         end
  File.write(path, body)
end

build_case = lambda do |root, kind|
  FileUtils.mkdir_p(File.join(root, "lib"))
  FileUtils.mkdir_p(File.join(root, "scripts"))
  FileUtils.mkdir_p(File.join(root, "test"))
  [%w[init -q], %w[config user.email wu@example.invalid], %w[config user.name wu-test]].each do |args|
    rc, out = run.call(root, {}, "git", *args)
    raise out unless rc.zero?
  end

  File.write(File.join(root, "contract.txt"), "database/api: NOT_APPLICABLE\ntype: boolean\n")
  run.call(root, {}, "git", "add", "contract.txt")
  run.call(root, {}, "git", "commit", "-q", "-m", "contract")
  _rc, contract_commit = run.call(root, {}, "git", "rev-parse", "HEAD")
  contract_commit.strip!

  File.write(File.join(root, "lib/feature.rb"), "module Feature\n  def self.enabled?\n    false\n  end\nend\n")
  write_test.call(File.join(root, "test/feature_test.rb"), syntax_error: kind == :syntax, expected: true)
  if kind == :marker_only
    File.write(
      File.join(root, "scripts/fake-red.sh"),
      "#!/usr/bin/env bash\necho 'WU_TESTS: 1'\necho 'WU_FAILURE_KIND: missing_behavior'\necho 'VERDICT: FAIL'\nexit 1\n"
    )
  end
  red_paths = ["lib/feature.rb", "test/feature_test.rb"]
  red_paths << "scripts/fake-red.sh" if kind == :marker_only
  run.call(root, {}, "git", "add", *red_paths)
  if kind == :late_contract
    File.write(File.join(root, "late-contract.txt"), "declared after the contract boundary\n")
    run.call(root, {}, "git", "add", "late-contract.txt")
  end
  run.call(root, {}, "git", "commit", "-q", "-m", "red")
  _rc, red_commit = run.call(root, {}, "git", "rev-parse", "HEAD")
  red_commit.strip!

  if kind == :marker_only
    File.write(
      File.join(root, "scripts/fake-red.sh"),
      "#!/usr/bin/env bash\necho 'WU_TESTS: 1'\necho 'VERDICT: PASS'\nexit 0\n"
    )
  elsif %i[drift restored_drift self_approved].include?(kind)
    write_test.call(File.join(root, "test/feature_test.rb"), expected: false)
  else
    File.write(File.join(root, "lib/feature.rb"), "module Feature\n  def self.enabled?\n    true\n  end\nend\n")
    write_test.call(File.join(root, "test/feature_test.rb"), expected: true) if kind == :syntax
  end
  green_paths = ["lib/feature.rb", "test/feature_test.rb"]
  green_paths << "scripts/fake-red.sh" if kind == :marker_only
  run.call(root, {}, "git", "add", *green_paths)
  commit_args = ["commit", "-q", "-m", "green"]
  if kind == :self_approved
    commit_args.concat(["-m", "Test-Expectation-Approval: WU-SELF_APPROVED"])
  end
  run.call(root, {}, "git", *commit_args)
  _rc, green_commit = run.call(root, {}, "git", "rev-parse", "HEAD")
  green_commit.strip!
  if kind == :post_green_drift
    write_test.call(File.join(root, "test/feature_test.rb"), expected: false)
    run.call(root, {}, "git", "add", "test/feature_test.rb")
    run.call(root, {}, "git", "commit", "-q", "-m", "drift after first green")
  elsif kind == :restored_drift
    File.write(File.join(root, "lib/feature.rb"), "module Feature\n  def self.enabled?\n    true\n  end\nend\n")
    write_test.call(File.join(root, "test/feature_test.rb"), expected: true)
    run.call(root, {}, "git", "add", "lib/feature.rb", "test/feature_test.rb")
    run.call(root, {}, "git", "commit", "-q", "-m", "restore test after fake green")
  end

  manifest = Marshal.load(Marshal.dump(base_manifest))
  unit = manifest.fetch("work_units").first
  unit["id"] = "WU-#{kind.to_s.upcase}"
  unit["tdd"]["contract_commit"] = contract_commit
  unit["tdd"]["red_commit"] = red_commit
  unit["tdd"]["green_commit"] = green_commit
  unit["tdd"]["red_commands"] = [kind == :marker_only ? "bash scripts/fake-red.sh" : "ruby test/feature_test.rb"]
  unit["tdd"]["red_tests"] = 1
  unit["tdd"]["test_files"] = ["test/feature_test.rb"]
  unit["tdd"]["expectation_change_approval_commit"] = green_commit if kind == :self_approved
  authority_path = kind == :late_contract ? "late-contract.txt" : "contract.txt"
  %w[database api types].each do |authority|
    unit["contracts"][authority]["paths"] = [authority_path]
  end
  unit["context"]["expected_head"] = green_commit
  unit["context"]["expected_worktree"] = "master"
  unit["context"]["files"].first["commit_sha"] = contract_commit
  unit["context"]["files"].first["sha256"] = Digest::SHA256.hexdigest("contract placeholder")
  manifest_path = File.join(File.dirname(root), "#{kind}.yaml")
  File.write(manifest_path, Psych.dump(manifest))
  [manifest_path, green_commit]
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
    puts "FAIL: #{label}"
    puts output
  end
end

Dir.mktmpdir("wu-tdd-contract-") do |tmp|
  cases = {}
  %i[normal syntax drift late_contract post_green_drift restored_drift marker_only self_approved].each do |kind|
    case_root = File.join(tmp, kind.to_s)
    FileUtils.mkdir_p(case_root)
    cases[kind] = build_case.call(case_root, kind)
  end

  manifest_path, = cases.fetch(:normal)
  tdd_env = { "WORK_UNIT_REPO" => File.join(tmp, "normal"), "WORK_UNIT_TDD_ONLY" => "1" }
  rc, out = run.call(repo_root, tdd_env, "ruby", checker, manifest_path)
  assert.call("authentic RED then GREEN", rc.zero? && out.include?("VERDICT: PASS"), out)

  zero_manifest = Psych.safe_load(File.read(manifest_path), aliases: false)
  zero_manifest["work_units"].first["tdd"]["red_commands"] = []
  zero_path = File.join(tmp, "zero-commands.yaml")
  File.write(zero_path, Psych.dump(zero_manifest))
  rc, out = run.call(repo_root, tdd_env, "ruby", checker, zero_path)
  assert.call("zero RED commands rejected", rc == 1 && out.include?("RED_COMMAND_REQUIRED"), out)

  manifest_path, = cases.fetch(:syntax)
  rc, out = run.call(repo_root, { "WORK_UNIT_REPO" => File.join(tmp, "syntax"), "WORK_UNIT_TDD_ONLY" => "1" }, "ruby", checker, manifest_path)
  syntax_ok = rc == 1 && out.include?("RED_FAILURE_INVALID")
  missing_behavior ||= rc.zero?
  assert.call("syntax-only RED rejected", syntax_ok, out)

  manifest_path, = cases.fetch(:drift)
  rc, out = run.call(repo_root, { "WORK_UNIT_REPO" => File.join(tmp, "drift"), "WORK_UNIT_TDD_ONLY" => "1" }, "ruby", checker, manifest_path)
  drift_ok = rc == 1 && out.include?("TEST_FILE_CHANGED_AFTER_RED")
  missing_behavior ||= rc.zero?
  assert.call("test expectation drift rejected", drift_ok, out)

  manifest_path, = cases.fetch(:late_contract)
  rc, out = run.call(
    repo_root,
    { "WORK_UNIT_REPO" => File.join(tmp, "late_contract"), "WORK_UNIT_TDD_ONLY" => "1" },
    "ruby", checker, manifest_path
  )
  late_ok = rc == 1 && out.include?("AUTHORITY_PATH_NOT_AT_CONTRACT")
  missing_behavior ||= rc.zero?
  assert.call("contract declared only after boundary rejected", late_ok, out)

  manifest_path, = cases.fetch(:post_green_drift)
  rc, out = run.call(
    repo_root,
    { "WORK_UNIT_REPO" => File.join(tmp, "post_green_drift"), "WORK_UNIT_TDD_ONLY" => "1" },
    "ruby", checker, manifest_path
  )
  post_green_ok = rc == 1 && out.include?("TEST_FILE_CHANGED_AFTER_RED")
  missing_behavior ||= rc.zero?
  assert.call("test drift after first GREEN rejected", post_green_ok, out)

  manifest_path, = cases.fetch(:restored_drift)
  rc, out = run.call(
    repo_root,
    { "WORK_UNIT_REPO" => File.join(tmp, "restored_drift"), "WORK_UNIT_TDD_ONLY" => "1" },
    "ruby", checker, manifest_path
  )
  restored_drift_ok = rc == 1 && out.include?("TEST_FILE_CHANGED_AFTER_RED")
  missing_behavior ||= rc.zero?
  assert.call("fake GREEN followed by restored expectation rejected", restored_drift_ok, out)

  manifest_path, = cases.fetch(:marker_only)
  rc, out = run.call(
    repo_root,
    { "WORK_UNIT_REPO" => File.join(tmp, "marker_only"), "WORK_UNIT_TDD_ONLY" => "1" },
    "ruby", checker, manifest_path
  )
  marker_only_ok = rc == 1 && out.match?(/RED_COMMAND_ENTRYPOINT_CHANGED|FIRST_GREEN_IMPLEMENTATION_MISSING/)
  missing_behavior ||= rc.zero?
  assert.call("marker-only RED and GREEN rejected", marker_only_ok, out)

  manifest_path, = cases.fetch(:self_approved)
  rc, out = run.call(
    repo_root,
    { "WORK_UNIT_REPO" => File.join(tmp, "self_approved"), "WORK_UNIT_TDD_ONLY" => "1" },
    "ruby", checker, manifest_path
  )
  self_approved_ok = rc == 1 && out.include?("EXPECTATION_APPROVAL_IS_GREEN")
  missing_behavior ||= rc.zero?
  assert.call("GREEN cannot self-approve expectation changes", self_approved_ok, out)
end

puts "WU_TESTS: #{checked}"
puts "CHECKED: #{checked}"
puts "WU_FAILURE_KIND: missing_behavior" if missing_behavior
puts "VERDICT: #{failed.zero? ? 'PASS' : 'FAIL'}"
exit(failed.zero? ? 0 : 1)
