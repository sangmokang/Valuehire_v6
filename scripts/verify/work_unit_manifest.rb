# frozen_string_literal: true

require "psych"

module WorkUnitManifest
  ROOT_KEYS = %w[manifest_version work_units].freeze
  UNIT_KEYS = %w[
    id claim acceptance_criterion counter_acceptance_criteria contracts tdd
    regression_commands adversarial_commands context not_applicable
  ].freeze
  CONTRACT_KEYS = %w[input output errors boundaries database api types].freeze
  AUTHORITY_KEYS = %w[status reason paths].freeze
  TDD_KEYS = %w[
    mode contract_commit red_commit green_commit red_commands red_tests
    red_failure_kind test_files expectation_change_approval_commit
  ].freeze
  CONTEXT_KEYS = %w[expected_head expected_worktree scope files observed_reads].freeze
  CONTEXT_FILE_KEYS = %w[path commit_sha sha256 read_evidence].freeze
  SHA_PATTERN = /\A[0-9a-f]{40}\z/
  HASH_PATTERN = /\A[0-9a-f]{64}\z/
  ID_PATTERN = /\AWU-[A-Z0-9][A-Z0-9._-]*\z/

  module_function

  def load(path)
    raw, errors = read_file(path)
    return [nil, errors, 0] unless errors.empty?

    duplicate_errors = duplicate_keys(raw, path)
    return [nil, duplicate_errors, 0] unless duplicate_errors.empty?

    data = Psych.safe_load(raw, permitted_classes: [], permitted_symbols: [], aliases: false)
    validation_errors = []
    checked = validate(data, validation_errors)
    [data, validation_errors, checked]
  rescue Psych::SyntaxError => e
    [nil, ["YAML_INVALID: #{e.problem} line=#{e.line}"], 0]
  rescue Psych::Exception => e
    [nil, ["YAML_INVALID: #{e.message.lines.first.to_s.strip}"], 0]
  end

  def read_file(path)
    stat = File.lstat(path)
    return [nil, ["MANIFEST_INVALID: #{path}"]] unless stat.file? && !stat.symlink?
    return [nil, ["MANIFEST_EMPTY: #{path}"]] if stat.size.zero?
    return [nil, ["MANIFEST_UNREADABLE: #{path}"]] if (stat.mode & 0o444).zero?

    raw = File.read(path, encoding: "UTF-8")
    return [nil, ["YAML_INVALID: invalid UTF-8"]] unless raw.valid_encoding?

    [raw, []]
  rescue Errno::ENOENT
    [nil, ["MANIFEST_MISSING: #{path}"]]
  rescue SystemCallError, IOError => e
    [nil, ["MANIFEST_UNREADABLE: #{path} (#{e.class})"]]
  end

  def duplicate_keys(raw, path)
    ast = Psych.parse_stream(raw, filename: path)
    return ["YAML_INVALID: exactly one document required"] unless ast.children.length == 1

    errors = []
    walk_mapping(ast, "$", errors)
    errors
  end

  def walk_mapping(node, path, errors)
    case node
    when Psych::Nodes::Mapping
      seen = {}
      node.children.each_slice(2) do |key_node, value_node|
        unless key_node.is_a?(Psych::Nodes::Scalar)
          errors << "SCHEMA_INVALID: #{path}"
          next
        end
        key = key_node.value
        errors << "YAML_MERGE_KEY_FORBIDDEN: #{path}" if key == "<<"
        errors << "YAML_DUPLICATE_KEY: #{path}.#{key}" if seen.key?(key)
        seen[key] = true
        walk_mapping(value_node, "#{path}.#{key}", errors)
      end
    when Psych::Nodes::Sequence, Psych::Nodes::Document, Psych::Nodes::Stream
      node.children.each_with_index { |child, index| walk_mapping(child, "#{path}[#{index}]", errors) }
    end
  end

  def validate(data, errors)
    unless exact_mapping?(data, ROOT_KEYS)
      errors << "SCHEMA_INVALID: root"
      return 1
    end

    checked = 1
    errors << "MANIFEST_VERSION_INVALID: #{data['manifest_version'].inspect}" unless data["manifest_version"] == 1
    units = data["work_units"]
    unless units.is_a?(Array) && !units.empty?
      errors << "WORK_UNITS_REQUIRED: at least one"
      return checked + 1
    end

    ids = {}
    units.each_with_index do |unit, index|
      checked += validate_unit(unit, index, ids, errors)
    end
    checked
  end

  def validate_unit(unit, index, ids, errors)
    label = "work_units[#{index}]"
    unless exact_mapping?(unit, UNIT_KEYS)
      errors << "UNIT_SCHEMA_INVALID: #{label}"
    end
    return 1 unless unit.is_a?(Hash)

    id = unit["id"]
    errors << "ID_REQUIRED: #{label}" unless string?(id) && id.match?(ID_PATTERN)
    errors << "ID_DUPLICATE: #{id}" if string?(id) && ids.key?(id)
    ids[id] = true if string?(id)
    errors << "CLAIM_REQUIRED: #{label}" unless string?(unit["claim"])
    errors << "AC_REQUIRED: #{label}" unless string?(unit["acceptance_criterion"])
    counters = unit["counter_acceptance_criteria"]
    unless counters.is_a?(Array) && !counters.empty? && counters.all? { |item| string?(item) }
      errors << "COUNTER_AC_REQUIRED: #{label}"
    end
    validate_contracts(unit["contracts"], label, errors)
    validate_tdd_shape(unit["tdd"], label, errors)
    validate_commands(unit["regression_commands"], "REGRESSION_COMMAND_REQUIRED", label, errors)
    validate_commands(unit["adversarial_commands"], "ADVERSARIAL_COMMAND_REQUIRED", label, errors)
    validate_context_shape(unit["context"], label, errors)
    unless unit["not_applicable"].nil? || unit["not_applicable"].is_a?(Hash)
      errors << "NOT_APPLICABLE_SCHEMA_INVALID: #{label}"
    end
    10
  end

  def validate_contracts(contracts, label, errors)
    unless exact_mapping?(contracts, CONTRACT_KEYS)
      errors << "CONTRACTS_REQUIRED: #{label}"
      return
    end
    %w[input output errors].each do |key|
      errors << "CONTRACT_REQUIRED: #{label}.#{key}" unless string?(contracts[key])
    end
    boundaries = contracts["boundaries"]
    errors << "BOUNDARY_REQUIRED: #{label}" unless string_array?(boundaries)
    %w[database api types].each do |key|
      authority = contracts[key]
      unless exact_mapping?(authority, AUTHORITY_KEYS)
        errors << "AUTHORITY_CONTRACT_REQUIRED: #{label}.#{key}"
        next
      end
      errors << "AUTHORITY_STATUS_INVALID: #{label}.#{key}" unless %w[APPLICABLE NOT_APPLICABLE].include?(authority["status"])
      errors << "AUTHORITY_REASON_REQUIRED: #{label}.#{key}" unless string?(authority["reason"])
      paths = authority["paths"]
      errors << "AUTHORITY_PATHS_INVALID: #{label}.#{key}" unless paths.is_a?(Array) && paths.all? { |item| string?(item) }
    end
  end

  def validate_tdd_shape(tdd, label, errors)
    unless exact_mapping?(tdd, TDD_KEYS)
      errors << "TDD_SCHEMA_INVALID: #{label}"
      return
    end
    errors << "TDD_MODE_INVALID: #{label}" unless %w[RED_GREEN NOT_APPLICABLE].include?(tdd["mode"])
    %w[contract_commit red_commit green_commit].each do |key|
      errors << "COMMIT_INVALID: #{label}.#{key}" unless tdd[key].is_a?(String) && tdd[key].match?(SHA_PATTERN)
    end
    validate_commands(tdd["red_commands"], "RED_COMMAND_REQUIRED", label, errors)
    errors << "RED_TESTS_INVALID: #{label}" unless tdd["red_tests"].is_a?(Integer) && tdd["red_tests"] >= 0
    errors << "RED_FAILURE_KIND_REQUIRED: #{label}" unless string?(tdd["red_failure_kind"])
    errors << "TEST_FILES_REQUIRED: #{label}" unless string_array?(tdd["test_files"])
    approval = tdd["expectation_change_approval_commit"]
    errors << "APPROVAL_COMMIT_INVALID: #{label}" unless approval.nil? || (approval.is_a?(String) && approval.match?(SHA_PATTERN))
  end

  def validate_context_shape(context, label, errors)
    unless exact_mapping?(context, CONTEXT_KEYS)
      errors << "CONTEXT_SCHEMA_INVALID: #{label}"
      return
    end
    errors << "CONTEXT_HEAD_INVALID: #{label}" unless context["expected_head"].is_a?(String) && context["expected_head"].match?(SHA_PATTERN)
    errors << "CONTEXT_WORKTREE_REQUIRED: #{label}" unless string?(context["expected_worktree"])
    errors << "CONTEXT_SCOPE_REQUIRED: #{label}" unless string?(context["scope"])
    files = context["files"]
    unless files.is_a?(Array) && !files.empty?
      errors << "CONTEXT_FILES_REQUIRED: #{label}"
      return
    end
    files.each_with_index do |file, file_index|
      file_label = "#{label}.context.files[#{file_index}]"
      unless exact_mapping?(file, CONTEXT_FILE_KEYS)
        errors << "CONTEXT_FILE_SCHEMA_INVALID: #{file_label}"
        next
      end
      errors << "CONTEXT_PATH_REQUIRED: #{file_label}" unless string?(file["path"])
      errors << "CONTEXT_COMMIT_INVALID: #{file_label}" unless file["commit_sha"].is_a?(String) && file["commit_sha"].match?(SHA_PATTERN)
      errors << "CONTEXT_HASH_INVALID: #{file_label}" unless file["sha256"].is_a?(String) && file["sha256"].match?(HASH_PATTERN)
      errors << "READ_EVIDENCE_REQUIRED: #{file_label}" unless string?(file["read_evidence"])
    end
    errors << "CONTEXT_OBSERVED_READS_REQUIRED: #{label}" unless string_array?(context["observed_reads"])
  end

  def validate_commands(value, code, label, errors)
    errors << "#{code}: #{label}" unless string_array?(value)
  end

  def exact_mapping?(value, keys)
    value.is_a?(Hash) && value.size == keys.size && keys.all? { |key| value.key?(key) }
  end

  def string?(value)
    value.is_a?(String) && !value.strip.empty?
  end

  def string_array?(value)
    value.is_a?(Array) && !value.empty? && value.all? { |item| string?(item) }
  end
end
