# frozen_string_literal: true

require "psych"

module WorkUnitPolicy
  EXPECTED_ROOT_KEYS = %w[version title work_unit pull_request review enforcement].freeze
  EXPECTED_WORK_UNIT_KEYS = %w[
    claims_per_unit max_units_per_pr max_branch_lifetime_hours completion_requires
  ].freeze
  EXPECTED_PULL_REQUEST_KEYS = %w[final_gates squash_rollback_boundary].freeze
  EXPECTED_REVIEW_KEYS = %w[high_risk].freeze
  EXPECTED_HIGH_RISK_KEYS = %w[
    paths execution_review_required document_review_can_pass paid_external_review_required
  ].freeze
  EXPECTED_ENFORCEMENT_KEYS = %w[policy_source generated_document checker renderer].freeze

  EXPECTED_COMPLETION_REQUIRES = %w[
    local_validation adversarial_checks_1_to_3 completion_commit
  ].freeze
  EXPECTED_FINAL_GATES = %w[
    strict codeaudit integrated_adversarial pull_request github_verify merge
  ].freeze
  EXPECTED_HIGH_RISK_PATHS = [
    ".github/workflows/**",
    "hooks/**",
    "scripts/acceptance-*",
    "verify*",
    "mechanism-registry",
    "비밀·후보자 데이터 노출 검사",
    "배포·인증·로그인"
  ].freeze
  EXPECTED_ENFORCEMENT = {
    "policy_source" => "docs/sot/work-unit-policy.yaml",
    "generated_document" => "docs/sot/work-unit-policy.md",
    "checker" => "scripts/verify/check-work-unit-policy.rb",
    "renderer" => "scripts/verify/render-work-unit-policy.rb"
  }.freeze

  POLICY_CHECKED = 19

  module_function

  def load_policy(path)
    raw = File.read(path)
    duplicates = duplicate_keys(raw, path)
    return [nil, duplicates] unless duplicates.empty?

    data = Psych.safe_load(raw, permitted_classes: [], permitted_symbols: [], aliases: false)
    errors = []
    validate(data, errors)
    [data, errors]
  rescue Psych::SyntaxError => e
    [nil, ["POLICY_YAML_INVALID: #{e.problem} line=#{e.line} column=#{e.column}"]]
  rescue Psych::Exception => e
    [nil, ["POLICY_YAML_INVALID: #{e.message.lines.first.to_s.strip}"]]
  rescue Errno::ENOENT
    [nil, ["POLICY_FILE_MISSING: #{path}"]]
  end

  def duplicate_keys(raw, path)
    ast = Psych.parse_stream(raw, filename: path)
    errors = []
    walk_duplicates(ast, "$", errors)
    errors
  rescue Psych::SyntaxError => e
    ["POLICY_YAML_INVALID: #{e.problem} line=#{e.line} column=#{e.column}"]
  end

  def walk_duplicates(node, path, errors)
    case node
    when Psych::Nodes::Mapping
      seen = {}
      node.children.each_slice(2) do |key_node, value_node|
        unless key_node.is_a?(Psych::Nodes::Scalar)
          errors << "POLICY_SCHEMA_INVALID: #{path}"
          next
        end
        key = key_node.value
        errors << "POLICY_DUPLICATE_KEY: #{path}.#{key}" if seen.key?(key)
        seen[key] = true
        walk_duplicates(value_node, "#{path}.#{key}", errors)
      end
    when Psych::Nodes::Sequence, Psych::Nodes::Document, Psych::Nodes::Stream
      node.children.each_with_index { |child, index| walk_duplicates(child, "#{path}[#{index}]", errors) }
    end
  end

  def validate(data, errors)
    unless exact_mapping?(data, EXPECTED_ROOT_KEYS)
      errors << "POLICY_SCHEMA_INVALID: root"
      return
    end

    expect_value(errors, "version", data["version"], 1)
    expect_value(errors, "title", data["title"], "Work Unit policy")
    validate_work_unit(data["work_unit"], errors)
    validate_pull_request(data["pull_request"], errors)
    validate_review(data["review"], errors)
    validate_enforcement(data["enforcement"], errors)
  end

  def validate_work_unit(section, errors)
    unless exact_mapping?(section, EXPECTED_WORK_UNIT_KEYS)
      errors << "POLICY_SCHEMA_INVALID: work_unit"
      return
    end
    expect_value(errors, "work_unit.claims_per_unit", section["claims_per_unit"], 1)
    expect_value(errors, "work_unit.max_units_per_pr", section["max_units_per_pr"], 5)
    expect_value(errors, "work_unit.max_branch_lifetime_hours",
                 section["max_branch_lifetime_hours"], 48)
    expect_value(errors, "work_unit.completion_requires",
                 section["completion_requires"], EXPECTED_COMPLETION_REQUIRES)
  end

  def validate_pull_request(section, errors)
    unless exact_mapping?(section, EXPECTED_PULL_REQUEST_KEYS)
      errors << "POLICY_SCHEMA_INVALID: pull_request"
      return
    end
    expect_value(errors, "pull_request.final_gates", section["final_gates"], EXPECTED_FINAL_GATES)
    expect_value(errors, "pull_request.squash_rollback_boundary",
                 section["squash_rollback_boundary"], "pull_request")
  end

  def validate_review(section, errors)
    unless exact_mapping?(section, EXPECTED_REVIEW_KEYS)
      errors << "POLICY_SCHEMA_INVALID: review"
      return
    end
    high_risk = section["high_risk"]
    unless exact_mapping?(high_risk, EXPECTED_HIGH_RISK_KEYS)
      errors << "POLICY_SCHEMA_INVALID: review.high_risk"
      return
    end
    expect_value(errors, "review.high_risk.paths", high_risk["paths"], EXPECTED_HIGH_RISK_PATHS)
    expect_value(errors, "review.high_risk.execution_review_required",
                 high_risk["execution_review_required"], true)
    expect_value(errors, "review.high_risk.document_review_can_pass",
                 high_risk["document_review_can_pass"], false)
    expect_value(errors, "review.high_risk.paid_external_review_required",
                 high_risk["paid_external_review_required"], false)
  end

  def validate_enforcement(section, errors)
    unless exact_mapping?(section, EXPECTED_ENFORCEMENT_KEYS)
      errors << "POLICY_SCHEMA_INVALID: enforcement"
      return
    end
    EXPECTED_ENFORCEMENT.each do |key, value|
      expect_value(errors, "enforcement.#{key}", section[key], value)
    end
  end

  def exact_mapping?(value, keys)
    value.is_a?(Hash) && value.keys == keys
  end

  def expect_value(errors, path, actual, expected)
    return if actual == expected

    errors << "POLICY_VALUE_INVALID: #{path}"
  end

  def render(data)
    work_unit = data.fetch("work_unit")
    pull_request = data.fetch("pull_request")
    high_risk = data.fetch("review").fetch("high_risk")
    enforcement = data.fetch("enforcement")

    lines = []
    lines << "# Work Unit 정책"
    lines << ""
    lines << "이 문서는 `#{enforcement.fetch("policy_source")}`에서 생성한다."
    lines << "손으로 고치지 말고 `ruby #{enforcement.fetch("renderer")} #{enforcement.fetch("policy_source")}`로 다시 만든다."
    lines << ""
    lines << "## Work Unit"
    lines << ""
    lines << "- Work Unit 하나는 주장 #{work_unit.fetch("claims_per_unit")}개만 담는다."
    lines << "- PR 하나는 Work Unit 1~#{work_unit.fetch("max_units_per_pr")}개만 담는다."
    lines << "- Work Unit이 #{work_unit.fetch("max_units_per_pr")}개 미만이어도 브랜치는 #{work_unit.fetch("max_branch_lifetime_hours")}시간 안에 닫는다."
    lines << "- 완료 조건:"
    work_unit.fetch("completion_requires").each { |item| lines << "  - `#{item}`" }
    lines << ""
    lines << "## Pull Request"
    lines << ""
    lines << "- 최종 관문은 이 순서 그대로 실행한다:"
    pull_request.fetch("final_gates").each { |item| lines << "  - `#{item}`" }
    lines << "- squash 뒤 롤백 경계는 `#{pull_request.fetch("squash_rollback_boundary")}` 전체다."
    lines << ""
    lines << "## 고위험 REVIEW"
    lines << ""
    lines << "- 고위험 경로와 표면:"
    high_risk.fetch("paths").each { |item| lines << "  - `#{item}`" }
    lines << "- 고위험 Work Unit은 실행 REVIEW가 필요하다: `#{high_risk.fetch("execution_review_required")}`."
    lines << "- 문서 REVIEW만으로 고위험 Work Unit을 닫을 수 있다: `#{high_risk.fetch("document_review_can_pass")}`."
    lines << "- 유료 외부 REVIEW가 기본 필수다: `#{high_risk.fetch("paid_external_review_required")}`."
    lines << ""
    lines << "## 강제 장치"
    lines << ""
    lines << "- 정책 정본: `#{enforcement.fetch("policy_source")}`"
    lines << "- 생성 문서: `#{enforcement.fetch("generated_document")}`"
    lines << "- 검사기: `#{enforcement.fetch("checker")}`"
    lines << "- 렌더러: `#{enforcement.fetch("renderer")}`"
    lines.join("\n") + "\n"
  end
end
