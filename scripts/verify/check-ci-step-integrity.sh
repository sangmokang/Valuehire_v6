#!/usr/bin/env bash
# check-ci-step-integrity.sh — 서버 자동검사의 시작 조건·스텝을 조용히 끄지 못하게 한다.
#
# 왜 필요한가:
#   hooks/pre-push 는 워크플로를 문자열로 훑어 `if: false` 만 잡는다. 그래서
#   `if: ${{ false }}`, `if: github.event_name == 'never'`, `continue-on-error: true`
#   같은 변형은 그대로 통과했다(2026-08-12 V1 D4 실측: 데이터 노출 검사 스텝을 영구히
#   꺼도 인수검사·pre-commit·pre-push 가 전부 초록이었다).
#   문자열 규칙은 하나 추가할 때마다 우회가 하나씩 는다. 그래서 여기서는 워크플로를
#   실제 YAML 로 파싱해 "조건이 붙었는가 / 실패를 무시하는가"를 구조로 본다.
#
# 계약: verify 워크플로는 모든 branch push·기본 pull request·수동 실행에서 시작하고,
#       모든 job·step 은 조건 없이 실행되어 실패를 전파해야 한다.
#       정당한 예외는 이 파일에 이유와 함께 적고, 적히지 않은 예외는 전부 불합격이다.
#
# 막지 못하는 것: 스텝 자체를 삭제하는 것. 그것은 mechanism-registry 와 pre-push 의
#       실행줄 검사가 맡는다. 여기서 다 막는다고 주장하지 않는다.
set -uo pipefail

WORKFLOW="${1:-.github/workflows/verify.yml}"
if [ ! -f "$WORKFLOW" ]; then
  echo "FAIL: 워크플로 파일이 없다 — $WORKFLOW (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

ruby -rpsych -rdate -rbase64 -e '
workflow_path = ARGV[0]
SCALAR_SCANNER = Psych::ScalarScanner.new(Psych::ClassLoader::Restricted.new(%w[Date Time], []))
BOOL_TAG = "tag:yaml.org,2002:bool"
STRING_TAG = "tag:yaml.org,2002:str"
BINARY_TAG = "tag:yaml.org,2002:binary"

def fail_structure(message)
  puts "FAIL: WORKFLOW_STRUCTURE: #{message}"
  puts "CHECKED: 0"
  exit 2
end

def mapping_pairs(node)
  node.children.each_slice(2).to_a
end

def scalar_key(pair)
  key = pair.first
  key.value if key.is_a?(Psych::Nodes::Scalar)
end

def duplicate_keys(pairs)
  keys = pairs.map { |pair| scalar_key(pair) }
  return ["비문자 key"] if keys.any?(&:nil?)

  keys.group_by { |key| key }.select { |_key, matches| matches.length > 1 }.keys
end

def semantic_string_key?(node)
  return false unless node.is_a?(Psych::Nodes::Scalar)
  return node.tag == STRING_TAG if node.tag
  return true unless node.plain
  SCALAR_SCANNER.tokenize(node.value).is_a?(String)
end

def unique_mapping_pairs(node, scope, semantic_keys: false)
  fail_structure("#{scope} mapping을 읽지 못했다") unless node.is_a?(Psych::Nodes::Mapping)

  pairs = mapping_pairs(node)
  duplicates = duplicate_keys(pairs)
  fail_structure("#{scope} key 중복 또는 비문자 key — #{duplicates.join(", ")}") unless duplicates.empty?
  if semantic_keys && !pairs.all? { |pair| semantic_string_key?(pair.first) }
    fail_structure("#{scope} key는 YAML 문자열이어야 한다")
  end
  keys = pairs.map { |pair| scalar_key(pair) }
  fail_structure("#{scope} merge key는 허용하지 않는다") if keys.include?("<<")
  pairs
end

def validate_mapping_tree(node, scope)
  case node
  when Psych::Nodes::Mapping
    unique_mapping_pairs(node, scope, semantic_keys: true).each do |key_node, value_node|
      validate_mapping_tree(value_node, "#{scope}.#{key_node.value}")
    end
  when Psych::Nodes::Sequence
    node.children.each_with_index { |child, index| validate_mapping_tree(child, "#{scope}[#{index}]") }
  when Psych::Nodes::Alias
    fail_structure("#{scope} alias는 허용하지 않는다")
  end
end

def yaml_boolean_key?(node)
  return false unless node.is_a?(Psych::Nodes::Scalar)

  node.tag == BOOL_TAG ||
    (node.plain && node.tag.nil? && node.value.match?(/\A(?:yes|no|true|false|on|off)\z/i))
end

def valid_on_key?(node)
  node.is_a?(Psych::Nodes::Scalar) && node.value == "on" &&
    (node.tag.nil? || node.tag == STRING_TAG)
end

def semantic_on_node?(node)
  return true if valid_on_key?(node)
  return SCALAR_SCANNER.tokenize(node.value) == true if yaml_boolean_key?(node)

  node.is_a?(Psych::Nodes::Scalar) && node.tag == BINARY_TAG && Base64.decode64(node.value).bytes == [111, 110]
end

def trigger_contract_errors(trigger)
  required = %w[push pull_request workflow_dispatch]
  trigger = [trigger] if trigger.is_a?(String)
  if trigger.is_a?(Array)
    return ["sequence event는 문자열이어야 한다"] unless trigger.all? { |event| event.is_a?(String) }

    return required.reject { |event| trigger.include?(event) }.map { |event| "필수 event #{event} 누락" }
  end
  return ["on은 mapping 또는 sequence여야 한다"] unless trigger.is_a?(Hash)

  errors = required.reject { |event| trigger.key?(event) }.map { |event| "필수 event #{event} 누락" }
  if trigger.key?("push")
    push = trigger["push"]
    allowed = push.nil? || push == {} || push == { "branches" => ["**"] }
    errors << "push 범위를 축소하는 filter가 있다" unless allowed
  end
  if trigger.key?("pull_request")
    pull_request = trigger["pull_request"]
    errors << "pull_request 범위를 축소하는 filter가 있다" unless pull_request.nil? || pull_request == {}
  end
  if trigger.key?("workflow_dispatch")
    dispatch = trigger["workflow_dispatch"]
    errors << "workflow_dispatch는 null 또는 mapping이어야 한다" unless dispatch.nil? || dispatch.is_a?(Hash)
  end
  errors
end

# 이름으로 지정한 예외. 이유 없이 늘리지 않는다.
ALLOWED_STEP_IF = {
  "인수 검사 0-5 (push · CI 연결)" =>
    "origin/main==main 을 보는 검사라 main push 에서만 의미가 있다. PR 실행에서 요구하면 상시 실패한다.",
}

begin
  source = File.binread(workflow_path)
  source = source.byteslice(3..) if source.start_with?("\xEF\xBB\xBF".b)
  source = source.force_encoding(Encoding::UTF_8)
  syntax_tree = Psych.parse_stream(source)
  doc = Psych.safe_load(source, aliases: true, permitted_classes: [Date, Time])
rescue Psych::Exception, SystemCallError, EncodingError, ArgumentError => e
  puts "FAIL: 워크플로 읽기·파싱 실패 — #{e.message.lines.first.to_s.strip}"
  puts "CHECKED: 0"
  exit 2
end

errors = []
checked = 0

document = syntax_tree.children.one? ? syntax_tree.children.first : nil
root = document&.root
fail_structure("top-level mapping을 읽지 못했다") unless root.is_a?(Psych::Nodes::Mapping) && doc.is_a?(Hash)

root_pairs = unique_mapping_pairs(root, "top-level")
on_pairs = root_pairs.select { |pair| scalar_key(pair) == "on" }
fail_structure("top-level on은 정확히 하나여야 한다") unless on_pairs.one?
fail_structure("top-level on key tag를 읽지 못했다") unless valid_on_key?(on_pairs.first.first)
on_like_pairs = root_pairs.select do |pair|
  scalar_key(pair) == "on" || yaml_boolean_key?(pair.first)
end
fail_structure("on과 boolean/case 유사 key가 충돌한다") unless on_like_pairs == on_pairs
fail_structure("on 값 후보는 정확히 하나여야 한다") unless root_pairs.count { |pair| semantic_on_node?(pair.first) } == 1

on_node = on_pairs.first.last
unless on_node.is_a?(Psych::Nodes::Mapping) || on_node.is_a?(Psych::Nodes::Sequence) ||
       on_node.is_a?(Psych::Nodes::Scalar)
  fail_structure("on은 mapping, sequence 또는 scalar event여야 한다")
end
validate_mapping_tree(on_node, "on")

trigger_key = doc.keys.find { |key| key == true || (key.is_a?(String) && key.bytes == [111, 110]) }
fail_structure("on 값을 읽지 못했다") unless trigger_key
trigger = doc[trigger_key]
if trigger.is_a?(Hash)
  fail_structure("on event key는 문자열이어야 한다") unless trigger.keys.all? { |key| key.is_a?(String) }
elsif trigger.is_a?(Array)
  fail_structure("sequence event는 문자열이어야 한다") unless trigger.all? { |event| event.is_a?(String) }
elsif !trigger.is_a?(String)
  fail_structure("on은 mapping, sequence 또는 scalar event여야 한다")
end

jobs_pair = root_pairs.find { |pair| scalar_key(pair) == "jobs" }
fail_structure("jobs mapping을 읽지 못했다") unless jobs_pair
job_pairs = unique_mapping_pairs(jobs_pair.last, "jobs")
jobs = doc["jobs"]
unless jobs.is_a?(Hash) && !jobs.empty? && jobs.keys.all? { |key| key.is_a?(String) }
  fail_structure("jobs 를 읽지 못했다 — 검사 대상 0개는 합격이 아니다")
end
job_pairs.each do |job_pair|
  job_name = scalar_key(job_pair)
  job = jobs[job_name]
  fail_structure("jobs.#{job_name} 은 mapping이어야 한다") unless job.is_a?(Hash)
  fail_structure("jobs.#{job_name} key는 문자열이어야 한다") unless job.keys.all? { |key| key.is_a?(String) }
  fields = unique_mapping_pairs(job_pair.last, "jobs.#{job_name}")
  steps_pair = fields.find { |pair| scalar_key(pair) == "steps" }
  next unless steps_pair

  fail_structure("jobs.#{job_name}.steps 는 sequence여야 한다") unless steps_pair.last.is_a?(Psych::Nodes::Sequence)
  steps = job["steps"]
  fail_structure("jobs.#{job_name}.steps 를 읽지 못했다") unless steps.is_a?(Array)
  steps_pair.last.children.each_with_index do |step_node, index|
    step = steps[index]
    fail_structure("jobs.#{job_name}.steps[#{index}] 은 mapping이어야 한다") unless step.is_a?(Hash)
    fail_structure("jobs.#{job_name}.steps[#{index}] key는 문자열이어야 한다") unless step.keys.all? { |key| key.is_a?(String) }
    unique_mapping_pairs(step_node, "jobs.#{job_name}.steps[#{index}]")
  end
end

trigger_errors = trigger_contract_errors(trigger)
checked += 1
if trigger_errors.empty?
  puts "PASS: TRIGGER_CONTRACT: push·pull_request·workflow_dispatch 시작 범위 유지"
else
  trigger_errors.each { |error| errors << "TRIGGER_CONTRACT: #{error}" }
end

jobs.each do |job_name, job|
  checked += 1
  errors << "JOB_CONDITIONAL: jobs.#{job_name} 에 if 가 있다 — job 을 통째로 끌 수 있다" if job.key?("if")
  errors << "JOB_CONTINUE_ON_ERROR: jobs.#{job_name} 이 실패를 무시한다" if job["continue-on-error"]

  steps = job["steps"]
  unless steps.is_a?(Array) && !steps.empty?
    errors << "JOB_NO_STEPS: jobs.#{job_name} 에 스텝이 없다 — 빈 job 은 항상 초록이다"
    next
  end

  steps.each_with_index do |step, i|
    checked += 1
    label = step["name"] || step["uses"] || "steps[#{i}]"

    if step.key?("if")
      reason = ALLOWED_STEP_IF[step["name"]]
      if reason
        puts "ALLOWED: #{label} — if 허용 (#{reason})"
      else
        errors << "STEP_CONDITIONAL: jobs.#{job_name}.#{label} 에 if 가 있다 (#{step["if"].inspect}) — " \
                  "조건부 스텝은 조건이 거짓이면 실행되지 않고도 초록이다"
      end
    end

    if step["continue-on-error"]
      errors << "STEP_CONTINUE_ON_ERROR: jobs.#{job_name}.#{label} 이 실패를 무시한다 — " \
                "빨개져야 할 검사가 초록으로 남는다"
    end

    run = step["run"]
    if run.is_a?(String)
      # 실행처럼 보이지만 실행하지 않는 형태.
      run.each_line do |line|
        stripped = line.strip
        next if stripped.empty? || stripped.start_with?("#")
        if stripped =~ /\Aecho\s+(bash|sh)\s+\S+\.sh/
          errors << "STEP_ECHO_ONLY: jobs.#{job_name}.#{label} 의 `#{stripped}` 는 실행이 아니라 출력이다"
        end
        if stripped =~ /\A(bash|sh)\s+-n\s+\S+\.sh/
          errors << "STEP_SYNTAX_ONLY: jobs.#{job_name}.#{label} 의 `#{stripped}` 는 문법 검사일 뿐 실행이 아니다"
        end
      end
    end
  end
end

if errors.empty?
  puts "PASS: 조건부·오류무시 스텝 없음 (job·step #{checked}개 검사)"
  puts "CHECKED: #{checked}"
  exit 0
else
  errors.each { |e| puts "FAIL: #{e}" }
  puts "CHECKED: #{checked}"
  exit 1
end
' "$WORKFLOW"
