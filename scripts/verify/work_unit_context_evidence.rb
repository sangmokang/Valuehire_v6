# frozen_string_literal: true

require "digest"
require "open3"

module WorkUnitContextEvidence
  GIT_ENV_KEYS = %w[
    GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
  ].freeze

  module_function

  def validate(data, repo)
    return [["REPOSITORY_INVALID: #{repo}"], 1] unless git_repository?(repo)

    errors = []
    checked = 1
    head = git(repo, "rev-parse", "HEAD").last.strip
    worktree = git(repo, "branch", "--show-current").last.strip
    tracked = git(repo, "ls-files").last.lines.map(&:strip).reject(&:empty?).sort
    data.fetch("work_units").each do |unit|
      unit_errors, unit_checked = validate_unit(unit, repo, head, worktree, tracked)
      errors.concat(unit_errors)
      checked += unit_checked
    end
    [errors, checked]
  end

  def validate_unit(unit, repo, head, worktree, tracked)
    context = unit.fetch("context")
    id = unit.fetch("id")
    errors = []
    checked = 4
    errors << "CONTEXT_HEAD_MISMATCH: #{id}" unless context.fetch("expected_head") == head
    errors << "CONTEXT_WORKTREE_MISMATCH: #{id}" unless context.fetch("expected_worktree") == worktree
    errors << "CONTEXT_SCOPE_TOO_BROAD: #{id}" unless context.fetch("scope") == "minimal"

    files = context.fetch("files")
    paths = files.map { |file| file.fetch("path") }
    errors << "CONTEXT_PATH_DUPLICATE: #{id}" unless paths.uniq.length == paths.length
    errors << "CONTEXT_SCOPE_TOO_BROAD: #{id}" if !tracked.empty? && paths.sort == tracked

    declared_receipts = []
    files.each do |file|
      file_errors, file_checked, receipt = validate_file(file, repo, head)
      errors.concat(file_errors.map { |error| "#{error}: #{id}" })
      checked += file_checked
      declared_receipts << receipt
    end
    observed = context.fetch("observed_reads")
    errors << "CONTEXT_READ_SET_MISMATCH: #{id}" unless observed.sort == declared_receipts.sort && observed.uniq.length == observed.length
    [errors.uniq, checked + 1]
  end

  def validate_file(file, repo, head)
    errors = []
    checked = 4
    path = file.fetch("path")
    commit = file.fetch("commit_sha")
    digest = file.fetch("sha256")
    errors << "CONTEXT_PATH_INVALID" unless repository_path?(path)
    errors << "CONTEXT_FILE_COMMIT_MISMATCH" unless commit == head

    content = repository_path?(path) ? git(repo, "show", "#{commit}:#{path}") : [1, ""]
    if !content.first.zero?
      errors << "CONTEXT_FILE_MISSING"
    elsif Digest::SHA256.hexdigest(content.last) != digest
      errors << "CONTEXT_HASH_MISMATCH"
    end
    receipt = "git:#{commit}:#{path}:#{digest}"
    errors << "CONTEXT_READ_EVIDENCE_INVALID" unless file.fetch("read_evidence") == receipt
    [errors, checked, receipt]
  end

  def repository_path?(path)
    path.is_a?(String) && !path.empty? && !path.start_with?("/", "~", ".") &&
      !path.split("/").include?("..") && !path.match?(/[\*?\[\]{}]/)
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
