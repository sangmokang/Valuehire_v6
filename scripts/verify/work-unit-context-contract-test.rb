#!/usr/bin/env ruby
# frozen_string_literal: true

require "digest"
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

Dir.mktmpdir("wu-context-contract-") do |tmp|
  repo = File.join(tmp, "repo")
  FileUtils.mkdir_p(repo)
  [%w[init -q], %w[config user.email context@example.invalid], %w[config user.name context-test]].each do |args|
    rc, out = run.call(repo, {}, "git", *args)
    raise out unless rc.zero?
  end
  File.write(File.join(repo, "contract.txt"), "context contract\n")
  run.call(repo, {}, "git", "add", "contract.txt")
  run.call(repo, {}, "git", "commit", "-q", "-m", "context contract")
  _rc, old_head = run.call(repo, {}, "git", "rev-parse", "HEAD")
  old_head.strip!
  File.write(File.join(repo, "other.txt"), "not declared by default\n")
  run.call(repo, {}, "git", "add", "other.txt")
  run.call(repo, {}, "git", "commit", "-q", "-m", "head moves")
  _rc, head = run.call(repo, {}, "git", "rev-parse", "HEAD")
  head.strip!
  _rc, branch = run.call(repo, {}, "git", "branch", "--show-current")
  branch.strip!

  content = "context contract\n"
  content_hash = Digest::SHA256.hexdigest(content)
  receipt = "git:#{head}:contract.txt:#{content_hash}"
  manifest = Marshal.load(Marshal.dump(base))
  unit = manifest.fetch("work_units").first
  unit["id"] = "WU-CONTEXT"
  unit["tdd"]["mode"] = "NOT_APPLICABLE"
  unit["context"] = {
    "expected_head" => head,
    "expected_worktree" => branch,
    "scope" => "minimal",
    "files" => [{
      "path" => "contract.txt", "commit_sha" => head,
      "sha256" => content_hash, "read_evidence" => receipt
    }],
    "observed_reads" => [receipt]
  }

  invoke = lambda do |name, candidate|
    path = File.join(tmp, "#{name}.yaml")
    File.write(path, Psych.dump(candidate))
    run.call(
      repo_root,
      { "WORK_UNIT_REPO" => repo, "WORK_UNIT_CONTEXT_ONLY" => "1" },
      "ruby", checker, path
    )
  end

  rc, out = invoke.call("normal", manifest)
  assert.call("current exact context", rc.zero? && out.include?("VERDICT: PASS"), out)

  filename_only = Marshal.load(Marshal.dump(manifest))
  filename_only["work_units"].first["context"]["files"].first["sha256"] = ""
  filename_only["work_units"].first["context"]["files"].first["read_evidence"] = ""
  filename_only["work_units"].first["context"]["observed_reads"] = []
  rc, out = invoke.call("filename-only", filename_only)
  assert.call("filename-only declaration rejected", rc == 1 && out.include?("CONTEXT_HASH_INVALID"), out)

  mismatch = Marshal.load(Marshal.dump(manifest))
  mismatch["work_units"].first["context"]["files"].first["sha256"] = "0" * 64
  rc, out = invoke.call("hash-mismatch", mismatch)
  assert.call("context hash mismatch rejected", rc == 1 && out.include?("CONTEXT_HASH_MISMATCH"), out)

  stale = Marshal.load(Marshal.dump(manifest))
  stale_context = stale["work_units"].first["context"]
  stale_context["expected_head"] = old_head
  stale_context["files"].first["commit_sha"] = old_head
  stale_receipt = "git:#{old_head}:contract.txt:#{content_hash}"
  stale_context["files"].first["read_evidence"] = stale_receipt
  stale_context["observed_reads"] = [stale_receipt]
  rc, out = invoke.call("stale-head", stale)
  assert.call("stale HEAD rejected", rc == 1 && out.include?("CONTEXT_HEAD_MISMATCH"), out)

  other_worktree = Marshal.load(Marshal.dump(manifest))
  other_worktree["work_units"].first["context"]["expected_worktree"] = "other-worktree"
  rc, out = invoke.call("other-worktree", other_worktree)
  assert.call("other worktree rejected", rc == 1 && out.include?("CONTEXT_WORKTREE_MISMATCH"), out)

  broad = Marshal.load(Marshal.dump(manifest))
  broad["work_units"].first["context"]["scope"] = "whole_repository"
  rc, out = invoke.call("whole-repository", broad)
  assert.call("whole repository scope rejected", rc == 1 && out.include?("CONTEXT_SCOPE_TOO_BROAD"), out)

  undeclared = Marshal.load(Marshal.dump(manifest))
  other_hash = Digest::SHA256.hexdigest("not declared by default\n")
  undeclared["work_units"].first["context"]["observed_reads"] << "git:#{head}:other.txt:#{other_hash}"
  rc, out = invoke.call("undeclared-read", undeclared)
  assert.call("undeclared observed read rejected", rc == 1 && out.include?("CONTEXT_READ_SET_MISMATCH"), out)
end

puts "WU_TESTS: #{checked}"
puts "CHECKED: #{checked}"
puts "WU_FAILURE_KIND: missing_behavior" if missing_behavior
puts "VERDICT: #{failed.zero? ? 'PASS' : 'FAIL'}"
exit(failed.zero? ? 0 : 1)
