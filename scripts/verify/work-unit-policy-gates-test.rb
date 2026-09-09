#!/usr/bin/env ruby
# frozen_string_literal: true

# Run real gates against an isolated repository, never against modified originals.
require "open3"
require "tmpdir"
require "fileutils"
require "digest"

repo = File.expand_path("../..", __dir__)
git_env = %w[GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
             GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH]
env = git_env.map { |key| [key, nil] }.to_h
run = lambda do |dir, *args|
  out, err, status = Open3.capture3(env, *args, chdir: dir)
  [status.exitstatus, out + err]
end
rc, listing = run.call(repo, "git", "ls-files", "-z")
abort "VERDICT: NOT_RUN\nCHECKED: 0" unless rc == 0 && !listing.empty?
files = listing.split("\0")
snapshot = lambda do
  rc, status = run.call(repo, "git", "status", "--porcelain=v1")
  raise "source status failed" unless rc == 0

  [status, files.map { |path| [path, Digest::SHA256.file(File.join(repo, path)).hexdigest] }]
end
before = snapshot.call
checked = 0
failed = 0
assert = lambda do |label, ok, detail|
  checked += 1
  puts "#{ok ? 'PASS' : 'FAIL'}: #{label}"
  unless ok
    failed += 1
    puts detail
  end
end

Dir.mktmpdir("work-unit-gates-") do |tmp|
  files.each do |path|
    destination = File.join(tmp, path)
    FileUtils.mkdir_p(File.dirname(destination))
    FileUtils.cp(File.join(repo, path), destination, preserve: true)
  end
  [["git", "init", "-q"], ["git", "add", "-A"]].each do |command|
    rc, out = run.call(tmp, *command)
    raise out unless rc == 0
  end
  acceptance = "scripts/acceptance-work-unit-policy.sh"
  mutations = "scripts/acceptance-work-unit-policy-mutations.sh"
  checker = "scripts/verify/check-work-unit-policy.rb"
  registry = "scripts/verify/check-mechanism-registry.sh"
  integrity = "scripts/verify/check-ci-step-integrity.sh"
  workflow = ".github/workflows/verify.yml"
  [acceptance, mutations, registry, integrity].each do |script|
    rc, out = run.call(tmp, "bash", script)
    assert.call("normal #{script}", rc == 0, out)
  end

  checker_original = File.read(File.join(tmp, checker))
  fakes = {
    "exit0" => "exit 0\n", "true" => "true\n", "empty" => "", "noop" => "# noop\n",
    "PASS22" => "puts 'VERDICT: PASS'\nputs 'POLICY_CHECKED: 22'\nputs 'DOCUMENT_SYNC: PASS'\n"
  }
  fakes.each do |name, body|
    File.write(File.join(tmp, checker), body)
    rc, out = run.call(tmp, "bash", acceptance)
    if name == "PASS22"
      # A stronger positive gate may also reject this fake; do not forbid that improvement.
      puts "OBSERVED: fake PASS22 positive gate exit=#{rc}"
      rc, out = run.call(tmp, "bash", mutations)
      assert.call("fake PASS22 rejected by negative runtime tests", rc == 1 && out.include?("VERDICT: FAIL"), out)
    else
      assert.call("fake #{name} rejected", rc == 1, out)
    end
  end
  File.write(File.join(tmp, checker), checker_original)

  module_path = "scripts/verify/work_unit_policy.rb"
  mutations_to_detect = [
    ["forged failure count", checker,
     'puts "POLICY_CHECKED: #{checked}"' + "\nputs \"DOCUMENT_SYNC: FAIL\"",
     'puts "POLICY_CHECKED: 22"' + "\nputs \"DOCUMENT_SYNC: FAIL\""],
    ["aliases enabled", module_path, "aliases: false", "aliases: true"],
    ["float equality", module_path, "unless actual.eql?(expected)", "unless actual == expected"]
  ]
  mutations_to_detect.each do |label, path, needle, replacement|
    file = File.join(tmp, path)
    original = File.read(file)
    raise "missing mutation target #{label}" unless original.include?(needle)

    File.write(file, original.sub(needle, replacement))
    rc, out = run.call(tmp, "ruby", "scripts/verify/work-unit-policy-contract-test.rb")
    assert.call("#{label} rejected by contract", rc == 1 && out.include?("VERDICT: FAIL"), out)
    File.write(file, original)
  end

  policy = File.join(tmp, "docs/sot/work-unit-policy.yaml")
  document = File.join(tmp, "docs/sot/work-unit-policy.md")
  File.write(policy, File.read(policy).sub("max_units_per_pr: 5", "max_units_per_pr: 6"))
  File.write(document, File.read(document).sub("1~5개", "1~6개").sub("5개 미만", "6개 미만"))
  rc, out = run.call(tmp, "bash", acceptance)
  assert.call("policy and document changed together rejected", rc == 1 && out.include?("POLICY_VALUE_INVALID"), out)

  original_workflow = File.read(File.join(tmp, workflow))
  [acceptance, mutations].each do |target|
    needle = "        run: bash scripts/verify/run-acceptance.sh #{target}\n"
    raise "missing workflow target: #{target}" unless original_workflow.scan(needle).length == 1

    variants = {
      "deletion" => ["", registry, "죽은 ci target"],
      "echo" => [needle.sub("run: bash", "run: echo bash"), integrity, "STEP_ECHO_ONLY"],
      "conditional" => ["        if: false\n" + needle, integrity, "STEP_CONDITIONAL"],
      "ignore failure" => ["        continue-on-error: true\n" + needle, integrity, "STEP_CONTINUE_ON_ERROR"]
    }
    variants.each do |label, (replacement, gate, diagnostic)|
      File.write(File.join(tmp, workflow), original_workflow.sub(needle, replacement))
      rc, out = run.call(tmp, "bash", gate)
      assert.call("#{target} #{label} rejected", rc == 1 && out.include?(diagnostic), out)
    end
  end
end
assert.call("SOURCE-TREE bytes and status unchanged", before == snapshot.call, "source changed")
puts "CHECKED: #{checked}"
puts "VERDICT: #{failed.zero? ? 'PASS' : 'FAIL'}"
exit(failed.zero? ? 0 : 1)
