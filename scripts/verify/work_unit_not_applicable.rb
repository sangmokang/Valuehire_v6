# frozen_string_literal: true

require "open3"

module WorkUnitNotApplicable
  ALLOWED_KINDS = %w[
    ui documentation configuration migration other_test_inappropriate
  ].freeze
  EMPTY_COMMAND = /\A\s*(?:echo|printf|true|:)(?:\s|\z)/
  GIT_ENV_KEYS = %w[
    GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
  ].freeze

  module_function

  def validate(data, repo)
    errors = []
    checked = 0
    data.fetch("work_units").each do |unit|
      unit_errors, unit_checked = validate_unit(unit, repo)
      errors.concat(unit_errors)
      checked += unit_checked
    end
    [errors, checked]
  end

  def validate_unit(unit, repo)
    id = unit.fetch("id")
    mode = unit.fetch("tdd").fetch("mode")
    waiver = unit["not_applicable"]
    return [["NOT_APPLICABLE_MODE_CONFLICT: #{id}"], 1] if mode == "RED_GREEN" && !waiver.nil?
    return [[], 1] if mode == "RED_GREEN"
    return [["NOT_APPLICABLE_REQUIRED: #{id}"], 1] if waiver.nil?

    errors = []
    checked = 3
    kind = waiver.fetch("change_kind")
    errors << "NOT_APPLICABLE_KIND_INVALID: #{id}" unless ALLOWED_KINDS.include?(kind)
    commands = waiver.fetch("alternative_validation_commands")
    commands.each do |command|
      checked += 1
      if command.match?(EMPTY_COMMAND) || command.include?("\n")
        errors << "ALTERNATIVE_COMMAND_INVALID: #{id} #{command.inspect}"
        next
      end
      out, err, status = Open3.capture3(clean_env, "bash", "-c", command, chdir: repo)
      errors << "ALTERNATIVE_VALIDATION_FAILED: #{id} exit=#{status.exitstatus} #{out}#{err}" unless status.success?
    end
    [errors, checked]
  rescue Errno::ENOENT, SystemCallError => e
    [["ALTERNATIVE_VALIDATION_NOT_RUN: #{id} #{e.class}"], checked]
  end

  def clean_env
    GIT_ENV_KEYS.map { |key| [key, nil] }.to_h
  end
end
