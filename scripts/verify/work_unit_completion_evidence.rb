# frozen_string_literal: true

require "open3"

module WorkUnitCompletionEvidence
  EMPTY_COMMAND = /\A\s*(?:echo|printf|true|:)(?:\s|\z)/
  GIT_ENV_KEYS = %w[
    GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY
    GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH
  ].freeze
  CONTROL_ENV_KEYS = %w[
    WORK_UNIT_SCHEMA_ONLY WORK_UNIT_TDD_ONLY WORK_UNIT_CONTEXT_ONLY
    WORK_UNIT_NOT_APPLICABLE_ONLY WORK_UNIT_COMPLETION_ONLY
    WORK_UNIT_CONTEXT_AT_CONTRACT WORK_UNIT_REPO
  ].freeze

  module_function

  def validate(data, repo)
    errors = []
    checked = 0
    results = {}
    data.fetch("work_units").each do |unit|
      %w[regression adversarial].each do |kind|
        unit.fetch("#{kind}_commands").each do |command|
          checked += 1
          errors.concat(validate_command(unit.fetch("id"), kind, command, repo, results))
        end
      end
    end
    [errors, checked]
  end

  def validate_command(id, kind, command, repo, results)
    prefix = kind.upcase
    invalid = command.match?(EMPTY_COMMAND) || command.include?("\n") || command.match?(/\A\s*(?:bash|sh)\s+-c(?:\s|\z)/)
    return ["#{prefix}_COMMAND_INVALID: #{id} #{command.inspect}"] if invalid

    rc, output = results.fetch(command) do
      out, err, status = Open3.capture3(clean_env, "bash", "-c", command, chdir: repo)
      results[command] = [status.exitstatus, out + err]
    end
    errors = []
    unless rc.zero? && output.include?("VERDICT: PASS")
      detail = output.lines.last(4).map(&:strip).join(" | ")
      errors << "#{prefix}_VALIDATION_FAILED: #{id} exit=#{rc} output=#{detail.inspect}"
    end
    errors << "#{prefix}_ZERO_CHECKS: #{id}" unless check_count(output).positive?
    errors
  rescue Errno::ENOENT, SystemCallError => e
    ["#{prefix}_VALIDATION_NOT_RUN: #{id} #{e.class}"]
  end

  def check_count(output)
    values = output.scan(/^(?:WU_TESTS|CHECKED):\s*([0-9]+)/).flatten.map(&:to_i)
    values.empty? ? 0 : values.max
  end

  def clean_env
    (GIT_ENV_KEYS + CONTROL_ENV_KEYS).map { |key| [key, nil] }.to_h
  end
end
