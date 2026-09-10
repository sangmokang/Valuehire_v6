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
git_env = %w[
  GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
].map { |key| [key, nil] }.to_h

run = lambda do |dir, env, *command|
  out, err, status = Open3.capture3(git_env.merge(env), *command, chdir: dir)
  [status.exitstatus, out + err]
end

commit = lambda do |dir, message|
  rc, out = run.call(dir, {}, "git", "add", ".")
  raise out unless rc.zero?
  rc, out = run.call(dir, {}, "git", "commit", "-q", "-m", message)
  raise out unless rc.zero?
  run.call(dir, {}, "git", "rev-parse", "HEAD").last.strip
end

build_repository = lambda do |root|
  FileUtils.mkdir_p(File.join(root, "docs/sot"))
  FileUtils.mkdir_p(File.join(root, "lib"))
  FileUtils.mkdir_p(File.join(root, "scripts"))
  FileUtils.mkdir_p(File.join(root, "test"))
  [%w[init -q], %w[config user.email wu@example.invalid], %w[config user.name wu-test]].each do |args|
    rc, out = run.call(root, {}, "git", *args)
    raise out unless rc.zero?
  end

  File.write(File.join(root, "contract.txt"), "database/api: NOT_APPLICABLE\ntype: boolean\n")
  File.write(File.join(root, "docs/sot/work-unit-policy.yaml"), <<~YAML)
    completion:
      approved_commands:
        - "bash scripts/acceptance-synthetic.sh"
        - "bash scripts/acceptance-failing.sh"
        - "bash scripts/acceptance-zero.sh"
  YAML
  File.write(File.join(root, "scripts/acceptance-synthetic.sh"), "#!/usr/bin/env bash\necho 'WU_TESTS: 1'\necho 'VERDICT: PASS'\n")
  File.write(File.join(root, "scripts/acceptance-failing.sh"), "#!/usr/bin/env bash\necho 'WU_TESTS: 1'\necho 'VERDICT: FAIL'\nexit 1\n")
  File.write(File.join(root, "scripts/acceptance-zero.sh"), "#!/usr/bin/env bash\necho 'CHECKED: 0'\necho 'VERDICT: PASS'\n")
  File.write(File.join(root, "scripts/acceptance-forged-count.sh"), "#!/usr/bin/env bash\necho 'CHECKED: 1'\necho 'VERDICT: PASS'\n")
  contract_commit = commit.call(root, "contract")

  File.write(File.join(root, "lib/feature.rb"), "module Feature\n  def self.enabled?\n    false\n  end\nend\n")
  File.write(File.join(root, "test/feature_test.rb"), <<~RUBY)
    require_relative "../lib/feature"
    puts "WU_TESTS: 1"
    if Feature.enabled?
      puts "VERDICT: PASS"
      exit 0
    end
    puts "WU_FAILURE_KIND: missing_behavior"
    puts "VERDICT: FAIL"
    exit 1
  RUBY
  red_commit = commit.call(root, "red")

  File.write(File.join(root, "lib/feature.rb"), "module Feature\n  def self.enabled?\n    true\n  end\nend\n")
  green_commit = commit.call(root, "green")
  branch = run.call(root, {}, "git", "branch", "--show-current").last.strip
  [contract_commit, red_commit, green_commit, branch]
end

checked = 0
failed = 0
missing_behavior = false

Dir.mktmpdir("wu-completion-contract-") do |tmp|
  repository = File.join(tmp, "repository")
  FileUtils.mkdir_p(repository)
  contract_commit, red_commit, green_commit, branch = build_repository.call(repository)
  contract_content = File.read(File.join(repository, "contract.txt"))
  contract_hash = Digest::SHA256.hexdigest(contract_content)
  base = Psych.safe_load(File.read(fixture), aliases: false)
  unit = base.fetch("work_units").first
  unit["id"] = "WU-COMPLETION"
  %w[database api types].each { |authority| unit["contracts"][authority]["paths"] = ["contract.txt"] }
  unit["tdd"]["contract_commit"] = contract_commit
  unit["tdd"]["red_commit"] = red_commit
  unit["tdd"]["green_commit"] = green_commit
  unit["tdd"]["red_commands"] = ["ruby test/feature_test.rb"]
  unit["tdd"]["red_tests"] = 1
  unit["tdd"]["test_files"] = ["test/feature_test.rb"]
  context = unit.fetch("context")
  context["expected_head"] = green_commit
  context["expected_worktree"] = branch
  file = context.fetch("files").first
  file["path"] = "contract.txt"
  file["commit_sha"] = green_commit
  file["sha256"] = contract_hash
  receipt = "git:#{green_commit}:contract.txt:#{contract_hash}"
  file["read_evidence"] = receipt
  context["observed_reads"] = [receipt]

  cases = [
    ["executed completion commands", "bash scripts/acceptance-synthetic.sh", "bash scripts/acceptance-synthetic.sh", 0, "VERDICT: PASS"],
    ["failing regression command rejected", "bash scripts/acceptance-failing.sh", "bash scripts/acceptance-synthetic.sh", 1, "REGRESSION_VALIDATION_FAILED"],
    ["failing adversarial command rejected", "bash scripts/acceptance-synthetic.sh", "bash scripts/acceptance-failing.sh", 1, "ADVERSARIAL_VALIDATION_FAILED"],
    ["no-op completion command rejected", "true", "bash scripts/acceptance-synthetic.sh", 1, "REGRESSION_COMMAND_INVALID"],
    ["zero-check completion output rejected", "bash scripts/acceptance-zero.sh", "bash scripts/acceptance-synthetic.sh", 1, "REGRESSION_ZERO_CHECKS"],
    ["echo-only positive-count forgery rejected", "bash -c 'echo WU_TESTS: 1; echo VERDICT: PASS'", "bash scripts/acceptance-synthetic.sh", 1, "REGRESSION_COMMAND_INVALID"],
    ["unapproved forged-count script rejected", "bash scripts/acceptance-forged-count.sh", "bash scripts/acceptance-synthetic.sh", 1, "REGRESSION_COMMAND_NOT_APPROVED"]
  ]

  cases.each_with_index do |(label, regression, adversarial, wanted, diagnostic), index|
    manifest = Marshal.load(Marshal.dump(base))
    manifest.fetch("work_units").first["regression_commands"] = [regression]
    manifest.fetch("work_units").first["adversarial_commands"] = [adversarial]
    path = File.join(tmp, "case-#{index}.yaml")
    File.write(path, Psych.dump(manifest))
    rc, output = run.call(
      repo_root,
      { "WORK_UNIT_REPO" => repository, "WORK_UNIT_COMPLETION_ONLY" => "1" },
      "ruby", checker, path
    )
    checked += 1
    if rc == wanted && output.include?(diagnostic)
      puts "PASS: #{label}"
    else
      failed += 1
      missing_behavior ||= wanted == 1 && rc.zero?
      puts "FAIL: #{label}"
      puts output
    end
  end
end

puts "WU_TESTS: #{checked}"
puts "CHECKED: #{checked}"
puts "WU_FAILURE_KIND: missing_behavior" if missing_behavior
puts "VERDICT: #{failed.zero? ? 'PASS' : 'FAIL'}"
exit(failed.zero? ? 0 : 1)
