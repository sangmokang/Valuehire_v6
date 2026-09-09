#!/usr/bin/env ruby
# frozen_string_literal: true

# Executable boundary contract; policy CLI is invoked, not source-text inspected.
require "open3"
require "tmpdir"
require "fileutils"
require "psych"
require "rbconfig"

repo = File.expand_path("../..", __dir__)
checker = File.join(repo, "scripts/verify/check-work-unit-policy.rb")
renderer = File.join(repo, "scripts/verify/render-work-unit-policy.rb")
policy = File.join(repo, "docs/sot/work-unit-policy.yaml")
document = File.join(repo, "docs/sot/work-unit-policy.md")
raw = File.read(policy)
original = Psych.safe_load(raw, aliases: false)
expected_document = File.read(document)
checks = 0
failures = 0

assert = lambda do |label, ok, detail|
  checks += 1
  if ok
    puts "PASS: #{label}"
  else
    failures += 1
    puts "FAIL: #{label}\n#{detail}"
  end
end
invoke = lambda do |program, *args|
  out, err, status = Open3.capture3(RbConfig.ruby, program, *args)
  [out, err, status.exitstatus]
end

Dir.mktmpdir("work-unit-contract-") do |tmp|
  input = File.join(tmp, "policy.yaml")
  doc = File.join(tmp, "document.md")
  File.write(input, raw)
  File.write(doc, expected_document)
  out, err, rc = invoke.call(checker, input, doc)
  assert.call("normal CLI output", rc == 0 && out.lines.map(&:strip) ==
    ["VERDICT: PASS", "POLICY_CHECKED: 22", "DOCUMENT_SYNC: PASS"], [rc, out, err].inspect)

  invalid = {
    "float units" => [raw.sub("max_units_per_pr: 5", "max_units_per_pr: 5.0"), "POLICY_VALUE_INVALID"],
    "float version" => [raw.sub("version: 1", "version: 1.0"), "POLICY_VALUE_INVALID"],
    "string integer" => [raw.sub("max_units_per_pr: 5", 'max_units_per_pr: "5"'), "POLICY_VALUE_INVALID"],
    "null integer" => [raw.sub("max_units_per_pr: 5", "max_units_per_pr: null"), "POLICY_VALUE_INVALID"],
    "boolean string" => [raw.sub("document_review_can_pass: false", 'document_review_can_pass: "false"'), "POLICY_VALUE_INVALID"],
    "extra YAML document" => [raw + "---\nversion: 999\n", "POLICY_YAML_INVALID"],
    "empty" => ["", "POLICY_FILE"],
    "whitespace" => [" \n\t", "POLICY_"],
    "empty root" => ["{}\n", "POLICY_SCHEMA_INVALID"],
    "integer key" => [raw + "123: value\n", "POLICY_SCHEMA_INVALID"],
    "duplicate nested key" => [raw.sub("  claims_per_unit: 1", "  claims_per_unit: 1\n  claims_per_unit: 1"), "POLICY_DUPLICATE_KEY"],
    "alias" => [raw.sub('title: "Work Unit policy"', 'title: &t "Work Unit policy"') + "alias: *t\n", "POLICY_"],
    "alias with valid schema" => [raw.sub("version: 1", "version: &one 1").sub("claims_per_unit: 1", "claims_per_unit: *one"), "POLICY_YAML_INVALID"],
    "inline merge" => [raw.sub("  claims_per_unit: 1", "  <<: {claims_per_unit: 1}"), "POLICY_SCHEMA_INVALID"],
    "shadowed inline merge" => [raw.sub("  claims_per_unit: 1", "  <<: {claims_per_unit: 2}\n  claims_per_unit: 1"), "POLICY_SCHEMA_INVALID"],
    "invalid bytes" => ["\xFF".b, "POLICY_"]
  }
  invalid.each do |label, (content, diagnostic)|
    File.binwrite(input, content)
    out, err, rc = invoke.call(checker, input, doc)
    assert.call(label, rc == 1 && out.include?("VERDICT: FAIL") &&
      out.include?(diagnostic) && !out.include?("VERDICT: PASS"), [rc, out, err].inspect)
    rendered, render_err, render_rc = invoke.call(renderer, input)
    assert.call("renderer rejects #{label}", render_rc == 1 && rendered.empty? &&
      render_err.include?("VERDICT: FAIL"), [render_rc, rendered, render_err].inspect)
  end

  # Property: every mapping permutation preserves meaning; list order does not.
  shuffle = nil
  seed = Integer(ENV.fetch("WORK_UNIT_PROPERTY_SEED", Random.new_seed.to_s))
  puts "PROPERTY_SEED: #{seed} (replay with WORK_UNIT_PROPERTY_SEED)"
  rng = Random.new(seed)
  shuffle = lambda do |value|
    case value
    when Hash
      value.to_a.shuffle(random: rng).map { |key, item| [key, shuffle.call(item)] }.to_h
    when Array
      value.map { |item| shuffle.call(item) }
    else
      value
    end
  end
  12.times do |index|
    content = Psych.dump(shuffle.call(original))
    File.write(input, "# same policy #{index}\n" + content)
    out, err, rc = invoke.call(checker, input, doc)
    assert.call("mapping permutation #{index}", rc == 0, [rc, out, err].inspect)
    first, first_err, first_rc = invoke.call(renderer, input)
    second, second_err, second_rc = invoke.call(renderer, input)
    assert.call("deterministic rendering #{index}", first_rc == 0 && second_rc == 0 &&
      first == expected_document && second == first, [first_rc, second_rc, first_err, second_err].inspect)
  end
  changed = Marshal.load(Marshal.dump(original))
  changed["pull_request"]["final_gates"].reverse!
  File.write(input, Psych.dump(changed))
  out, err, rc = invoke.call(checker, input, doc)
  assert.call("list order remains required", rc == 1 && out.include?("POLICY_VALUE_INVALID"),
    [rc, out, err].inspect)

  File.write(input, raw)
  [input, doc].each do |path|
    backup = path + ".original"
    FileUtils.mv(path, backup)
    File.symlink(backup, path)
    out, err, rc = invoke.call(checker, input, doc)
    assert.call("symlink #{File.basename(path)}", rc == 1 && out.include?("FILE_INVALID"),
      [rc, out, err].inspect)
    File.unlink(path)
    out, err, rc = invoke.call(checker, input, doc)
    assert.call("missing #{File.basename(path)}", rc == 1 && out.include?("FILE_MISSING"),
      [rc, out, err].inspect)
    Dir.mkdir(path)
    out, err, rc = invoke.call(checker, input, doc)
    assert.call("directory #{File.basename(path)}", rc == 1 && out.include?("FILE_INVALID"),
      [rc, out, err].inspect)
    Dir.rmdir(path)
    FileUtils.mv(backup, path)
    File.chmod(0o000, path)
    out, err, rc = invoke.call(checker, input, doc)
    assert.call("unreadable #{File.basename(path)}", rc == 1 && out.include?("FILE_UNREADABLE"),
      [rc, out, err].inspect)
    File.chmod(0o600, path)
  end
  [[checker, [input, doc, "unexpected"]], [renderer, [input, "unexpected"]]].each do |program, args|
    out, err, rc = invoke.call(program, *args)
    assert.call("extra arguments #{File.basename(program)}", rc == 2 &&
      (out + err).include?("VERDICT: NOT_RUN"), [rc, out, err].inspect)
  end
end

Dir.mktmpdir("work-unit-count-") do |tmp|
  input = File.join(tmp, "policy.yaml")
  {
    "parse failure count" => ["broken: [\n", 0],
    "root failure count" => ["version: 1\n", 1],
    "nested schema failure count" => [raw.sub("  claims_per_unit: 1\n", ""), 18],
    "value failure count" => [raw.sub("version: 1", "version: 2"), 22]
  }.each do |label, (content, count)|
    File.write(input, content)
    out, err, rc = invoke.call(checker, input, document)
    assert.call(label, rc == 1 && out.lines.map(&:strip).include?("POLICY_CHECKED: #{count}"),
      [rc, out, err].inspect)
  end
end

Dir.mktmpdir("work-unit-module-") do |tmp|
  [checker, renderer].each { |path| FileUtils.cp(path, tmp) }
  mod = File.join(tmp, "work_unit_policy.rb")
  original_module = File.read(File.join(repo, "scripts/verify/work_unit_policy.rb"))
  %w[missing empty symlink directory unreadable syntax].each do |kind|
    File.unlink(mod) if File.exist?(mod) || File.symlink?(mod)
    case kind
    when "empty" then File.write(mod, "")
    when "symlink" then File.symlink(File.join(repo, "scripts/verify/work_unit_policy.rb"), mod)
    when "directory" then Dir.mkdir(mod)
    when "unreadable" then File.write(mod, original_module); File.chmod(0o000, mod)
    when "syntax" then File.write(mod, "module WorkUnitPolicy; def(; end\n")
    end
    [checker, renderer].each do |program|
      out, err, rc = invoke.call(File.join(tmp, File.basename(program)), policy)
      assert.call("module #{kind} #{File.basename(program)}", rc == 2 && out.empty? &&
        err.include?("VERDICT: NOT_RUN"), [rc, out, err].inspect)
    end
    Dir.rmdir(mod) if kind == "directory"
    File.chmod(0o600, mod) if kind == "unreadable"
  end
end

puts "CHECKED: #{checks}"
puts "VERDICT: #{failures.zero? ? 'PASS' : 'FAIL'}"
exit(failures.zero? ? 0 : 1)
