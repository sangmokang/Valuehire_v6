# frozen_string_literal: true

require "digest"
require "open3"

module WorkUnitContextEvidence
  MAXIMUM_FILES_PER_UNIT = 20
  NEAR_WHOLE_OMISSION_MINIMUM = 2
  GIT_ENV_KEYS = %w[
    GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
  ].freeze

  module_function

  def validate(data, repo)
    return [["REPOSITORY_INVALID: #{repo}"], 1] unless git_repository?(repo)

    errors = []
    checked = 1
    current_head = git(repo, "rev-parse", "HEAD").last.strip
    current_worktree = git(repo, "branch", "--show-current").last.strip
    archive = ENV["WORK_UNIT_CONTEXT_AT_CONTRACT"] == "1"
    data.fetch("work_units").each do |unit|
      head = archive ? unit.fetch("tdd").fetch("contract_commit") : current_head
      worktree = archive ? nil : current_worktree
      tracked = tracked_files(repo, head)
      unit_errors, unit_checked = validate_unit(unit, repo, head, worktree, tracked, archive)
      errors.concat(unit_errors)
      checked += unit_checked
    end
    [errors, checked]
  end

  def validate_unit(unit, repo, head, worktree, tracked, archive)
    context = unit.fetch("context")
    id = unit.fetch("id")
    errors = []
    checked = 4
    errors << "CONTEXT_HEAD_MISMATCH: #{id}" unless context.fetch("expected_head") == head
    if worktree && context.fetch("expected_worktree") != worktree
      errors << "CONTEXT_WORKTREE_MISMATCH: #{id}"
    elsif archive && !historical_worktree_evidence?(context, repo, head)
      errors << "CONTEXT_WORKTREE_EVIDENCE_MISSING: #{id}"
    end
    errors << "CONTEXT_SCOPE_TOO_BROAD: #{id}" unless context.fetch("scope") == "minimal"

    files = context.fetch("files")
    paths = files.map { |file| file.fetch("path") }
    errors << "CONTEXT_PATH_DUPLICATE: #{id}" unless paths.uniq.length == paths.length
    errors << "CONTEXT_SCOPE_TOO_BROAD: #{id}" if !tracked.empty? && paths.sort == tracked
    omitted = tracked - paths
    if paths.length > MAXIMUM_FILES_PER_UNIT || (paths.length > 1 && omitted.length < NEAR_WHOLE_OMISSION_MINIMUM)
      errors << "CONTEXT_SCOPE_TOO_BROAD: #{id}"
    end

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

  def historical_worktree_evidence?(context, repo, head)
    expected = context.fetch("expected_worktree")
    context.fetch("files").any? do |file|
      path = file.fetch("path")
      next false unless repository_path?(path)

      rc, content = git(repo, "show", "#{head}:#{path}")
      rc.zero? && content.lines.any? { |line| line.include?(expected) }
    end
  end

  def repository_path?(path)
    path.is_a?(String) && !path.empty? && !path.start_with?("/", "~", ".") &&
      !path.split("/").include?("..") && !path.match?(/[\*?\[\]{}]/)
  end

  def tracked_files(repo, commit)
    rc, output = git(repo, "ls-tree", "-r", "--name-only", commit)
    rc.zero? ? output.lines.map(&:strip).reject(&:empty?).sort : []
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
