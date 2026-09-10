# frozen_string_literal: true

require "digest"
require "fileutils"
require "open3"
require "tmpdir"

module WorkUnitGitEvidence
  GIT_ENV_KEYS = %w[
    GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
  ].freeze
  FORBIDDEN_RED = /syntax error|SyntaxError|LoadError|cannot load such file|collection error|no tests|WU_TESTS:\s*0/i
  EMPTY_COMMAND = /\A\s*(?:echo|printf|true|:)(?:\s|\z)/

  module_function

  def validate(data, repo)
    errors = []
    checked = 0
    unless git_repository?(repo)
      return [["REPOSITORY_INVALID: #{repo}"], 1]
    end

    data.fetch("work_units").each do |unit|
      next unless unit.fetch("tdd").fetch("mode") == "RED_GREEN"

      unit_errors, unit_checked = validate_unit(unit, repo)
      errors.concat(unit_errors)
      checked += unit_checked
    end
    [errors, checked]
  end

  def validate_unit(unit, repo)
    errors = []
    checked = 0
    tdd = unit.fetch("tdd")
    id = unit.fetch("id")
    contract_commit = tdd.fetch("contract_commit")
    red_commit = tdd.fetch("red_commit")
    green_commit = tdd.fetch("green_commit")

    commits = [contract_commit, red_commit, green_commit]
    commits.each do |commit|
      checked += 1
      errors << "COMMIT_NOT_FOUND: #{id} #{commit}" unless commit_exists?(repo, commit)
    end
    return [errors, checked] unless errors.empty?

    checked += 2
    unless strict_ancestor?(repo, contract_commit, red_commit)
      errors << "CONTRACT_NOT_BEFORE_RED: #{id}"
    end
    unless strict_ancestor?(repo, red_commit, green_commit)
      errors << "GREEN_NOT_AFTER_RED: #{id}"
    end

    command_errors, command_checked = validate_commands(repo, red_commit, green_commit, tdd)
    errors.concat(command_errors)
    checked += command_checked
    file_errors, file_checked = validate_test_files(repo, id, tdd)
    errors.concat(file_errors)
    checked += file_checked
    [errors, checked]
  end

  def validate_commands(repo, red_commit, green_commit, tdd)
    errors = []
    checked = 0
    red_total = 0
    tdd.fetch("red_commands").each do |command|
      checked += 2
      if command.match?(EMPTY_COMMAND) || command.include?("\n")
        errors << "RED_COMMAND_NOT_EXECUTABLE: #{command.inspect}"
        next
      end
      red_rc, red_output = run_at_commit(repo, red_commit, command)
      red_count = test_count(red_output)
      red_total += red_count
      valid_red = red_rc != 0 && red_count.positive? &&
                  red_output.include?("WU_FAILURE_KIND: missing_behavior") &&
                  !red_output.match?(FORBIDDEN_RED)
      errors << "RED_FAILURE_INVALID: exit=#{red_rc} command=#{command}" unless valid_red

      green_rc, green_output = run_at_commit(repo, green_commit, command)
      valid_green = green_rc.zero? && test_count(green_output).positive? &&
                    green_output.include?("VERDICT: PASS")
      errors << "FIRST_GREEN_INVALID: exit=#{green_rc} command=#{command}" unless valid_green
    end
    checked += 1
    unless red_total == tdd.fetch("red_tests") && red_total.positive?
      errors << "RED_TEST_COUNT_MISMATCH: expected=#{tdd.fetch('red_tests')} actual=#{red_total}"
    end
    [errors, checked]
  end

  def validate_test_files(repo, id, tdd)
    errors = []
    checked = 0
    changed = []
    tdd.fetch("test_files").each do |path|
      checked += 1
      unless repository_path?(path)
        errors << "TEST_FILE_PATH_INVALID: #{path}"
        next
      end
      red_blob = blob(repo, tdd.fetch("red_commit"), path)
      green_blob = blob(repo, tdd.fetch("green_commit"), path)
      if red_blob.nil? || green_blob.nil?
        errors << "TEST_FILE_MISSING: #{path}"
      elsif Digest::SHA256.hexdigest(red_blob) != Digest::SHA256.hexdigest(green_blob)
        changed << path
      end
    end
    return [errors, checked] if changed.empty?

    approval = tdd["expectation_change_approval_commit"]
    unless approved_change?(repo, id, approval, tdd, changed)
      errors << "TEST_FILE_CHANGED_AFTER_RED: #{changed.join(',')}"
    end
    [errors, checked + 1]
  end

  def approved_change?(repo, id, approval, tdd, changed)
    return false unless approval && commit_exists?(repo, approval)
    return false unless strict_ancestor?(repo, tdd.fetch("red_commit"), approval)
    return false unless ancestor?(repo, approval, tdd.fetch("green_commit"))

    rc, message = git(repo, "show", "-s", "--format=%B", approval)
    return false unless rc.zero? && message.lines.any? { |line| line.strip == "Test-Expectation-Approval: #{id}" }

    rc, names = git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", approval)
    files = names.lines.map(&:strip).reject(&:empty?)
    rc.zero? && !files.empty? && files.sort == changed.sort
  end

  def run_at_commit(repo, commit, command)
    Dir.mktmpdir("wu-commit-run-") do |parent|
      checkout = File.join(parent, "checkout")
      rc, output = git(repo, "worktree", "add", "--detach", checkout, commit)
      return [2, "WORKTREE_ADD_FAILED: #{output}"] unless rc.zero?

      begin
        out, err, status = Open3.capture3(clean_env, "bash", "-c", command, chdir: checkout)
        [status.exitstatus, out + err]
      ensure
        git(repo, "worktree", "remove", "--force", checkout)
      end
    end
  end

  def test_count(output)
    matches = output.scan(/WU_TESTS:\s*([0-9]+)/)
    matches.empty? ? 0 : matches.last.first.to_i
  end

  def commit_exists?(repo, commit)
    git(repo, "cat-file", "-e", "#{commit}^{commit}").first.zero?
  end

  def strict_ancestor?(repo, older, newer)
    older != newer && ancestor?(repo, older, newer)
  end

  def ancestor?(repo, older, newer)
    git(repo, "merge-base", "--is-ancestor", older, newer).first.zero?
  end

  def blob(repo, commit, path)
    rc, output = git(repo, "show", "#{commit}:#{path}")
    rc.zero? ? output : nil
  end

  def repository_path?(path)
    path.is_a?(String) && !path.empty? && !path.start_with?("/", "~") && !path.split("/").include?("..")
  end

  def git_repository?(repo)
    File.directory?(repo) && git(repo, "rev-parse", "--git-dir").first.zero?
  end

  def git(repo, *args)
    out, err, status = Open3.capture3(clean_env, "git", *args, chdir: repo)
    [status.exitstatus, out + err]
  end

  def clean_env
    GIT_ENV_KEYS.map { |key| [key, nil] }.to_h
  end
end
