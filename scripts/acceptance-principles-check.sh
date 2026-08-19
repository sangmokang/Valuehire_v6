#!/usr/bin/env bash
# acceptance-principles-check.sh — P1 32개 강제 목록의 구조·장치·CI 배선·회귀를 검사한다.
#
# 종료값: 0=선택한 모드 충족, 1=위반, 2=검사 환경/인자 오류.
# --schema-only 는 장부 구조와 기록된 장치의 정적 배선만 진단한다.
# --full(기본)은 회귀와 32개 전체 P1 조건까지 검사하며 CI/pre-push는 이 모드만 쓴다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

MODE=${1:---full}
case "$MODE" in
  --schema-only|--full) ;;
  *)
    echo "NOT_RUN: 지원하지 않는 모드 — $MODE"
    exit 2
    ;;
esac

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  exit 2
}
cd "$REPO" || {
  echo "NOT_RUN: 저장소 루트로 이동할 수 없다"
  exit 2
}

FILE=docs/sot/principles.yaml
SOURCE=docs/sot/coding-principles.md
WORKFLOW=.github/workflows/verify.yml
REQUIRED="$FILE scripts/acceptance-principles-check.sh"

for required in $REQUIRED; do
  if [ ! -f "$required" ]; then
    echo "REQUIRED_FILE_MISSING: $required"
    exit 1
  fi
done
if [ ! -x scripts/acceptance-principles-check.sh ]; then
  echo "REQUIRED_FILE_NOT_EXECUTABLE: scripts/acceptance-principles-check.sh"
  exit 1
fi
if [ ! -f "$SOURCE" ] || [ ! -f "$WORKFLOW" ]; then
  echo "NOT_RUN: SOT 또는 workflow를 읽을 수 없다"
  exit 2
fi
if ! command -v ruby >/dev/null 2>&1 || ! ruby -rpsych -e 'exit 0' >/dev/null 2>&1; then
  echo "NOT_RUN: Ruby Psych YAML 파서가 없다"
  exit 2
fi

ruby -rpsych -rjson -ropen3 - "$FILE" "$SOURCE" "$WORKFLOW" <<'RUBY'
file, source_file, workflow_file = ARGV
errors = []

begin
  raw = File.read(file)
  ast = Psych.parse_stream(raw, file)
rescue Psych::SyntaxError => e
  puts "YAML_PARSE_ERROR: #{e.problem} (line #{e.line}, column #{e.column})"
  exit 1
end

walk = nil
walk = lambda do |node, path|
  case node
  when Psych::Nodes::Mapping
    seen = {}
    node.children.each_slice(2).with_index do |(key_node, value_node), index|
      unless key_node.is_a?(Psych::Nodes::Scalar)
        errors << "MAPPING_KEY_INVALID: #{path}[#{index}]"
        next
      end
      key = key_node.value
      if seen.key?(key)
        errors << "DUPLICATE_KEY: #{path}.#{key}"
      else
        seen[key] = true
      end
      walk.call(value_node, "#{path}.#{key}")
    end
  when Psych::Nodes::Sequence
    node.children.each_with_index { |child, index| walk.call(child, "#{path}[#{index}]") }
  else
    if node.respond_to?(:children) && node.children
      node.children.each_with_index { |child, index| walk.call(child, "#{path}[#{index}]") }
    end
  end
end
walk.call(ast, "$")

begin
  data = Psych.safe_load(raw, permitted_classes: [], permitted_symbols: [], aliases: false)
rescue Psych::Exception => e
  errors << "YAML_PARSE_ERROR: #{e.message.lines.first.to_s.strip}"
  data = nil
end

unless data.is_a?(Array)
  errors << "ROOT_TYPE_INVALID: expected sequence"
  data = []
end

expected_ids = (1..22).map { |n| "P#{n}" } +
  (1..5).map { |n| "§1-B-#{n}" } +
  (1..5).map { |n| "V-#{n}" }
top_keys = %w[id principle mechanism_expected mechanism_found status evidence]
mechanism_keys = %w[path check stages]
statuses = %w[완전 부분 없음 해당없음 미확인]
active_statuses = %w[완전 부분]
allowed_stages = %w[pre-commit pre-push session-start acceptance ci]

source_titles = {}
in_browser = false
File.foreach(source_file) do |line|
  if line.start_with?("### §1-B.")
    in_browser = true
    next
  elsif line.start_with?("### 검증 체제")
    in_browser = false
  end
  if (match = line.match(/^\| \*\*((?:P\d+)|(?:V-\d+))\*\* \| \*\*(.+?)\*\*/))
    source_titles[match[1]] = match[2]
  elsif in_browser && (match = line.match(/^\| ([1-5]) \| \*\*(.+?)\*\*/))
    source_titles["§1-B-#{match[1]}"] = match[2]
  end
end
unless source_titles.keys.sort == expected_ids.sort
  errors << "SOT_ID_SET_MISMATCH: parsed=#{source_titles.keys.sort.join(',')}"
end

begin
  workflow = Psych.safe_load(
    File.read(workflow_file),
    permitted_classes: [],
    permitted_symbols: [],
    aliases: true
  )
rescue Psych::Exception => e
  errors << "WORKFLOW_PARSE_ERROR: #{e.message.lines.first.to_s.strip}"
  workflow = {}
end

ci_runs = []
jobs = workflow.is_a?(Hash) ? workflow["jobs"] : nil
if jobs.is_a?(Hash)
  jobs.each_value do |job|
    next unless job.is_a?(Hash) && job["steps"].is_a?(Array)
    job["steps"].each do |step|
      next unless step.is_a?(Hash)
      condition = step["if"]
      next if condition == false || condition.to_s.strip == "false"
      ci_runs << step["run"] if step["run"].is_a?(String)
    end
  end
end

settings_strings = []
collect_strings = nil
collect_strings = lambda do |value|
  case value
  when Hash
    value.each_value { |child| collect_strings.call(child) }
  when Array
    value.each { |child| collect_strings.call(child) }
  when String
    settings_strings << value
  end
end
begin
  collect_strings.call(JSON.parse(File.read(".claude/settings.json")))
rescue StandardError => e
  errors << "SESSION_SETTINGS_INVALID: #{e.class}"
end

seen_ids = {}
data.each_with_index do |entry, index|
  label = "item[#{index}]"
  unless entry.is_a?(Hash)
    errors << "ITEM_TYPE_INVALID: #{label}"
    next
  end

  unknown = entry.keys - top_keys
  missing = top_keys - entry.keys
  errors << "UNKNOWN_FIELD: #{label} #{unknown.join(',')}" unless unknown.empty?
  errors << "MISSING_FIELD: #{label} #{missing.join(',')}" unless missing.empty?
  next unless unknown.empty? && missing.empty?

  id = entry["id"]
  unless id.is_a?(String) && !id.strip.empty?
    errors << "EMPTY_FIELD: #{label}.id"
    next
  end
  if seen_ids.key?(id)
    errors << "ID_DUPLICATE: #{id}"
  else
    seen_ids[id] = true
  end

  %w[principle mechanism_expected evidence].each do |key|
    value = entry[key]
    errors << "EMPTY_FIELD: #{id}.#{key}" unless value.is_a?(String) && !value.strip.empty?
  end

  status = entry["status"]
  errors << "STATUS_INVALID: #{id}=#{status.inspect}" unless statuses.include?(status)

  expected_title = source_titles[id]
  if expected_title && entry["principle"] != expected_title
    errors << "PRINCIPLE_MISMATCH: #{id} expected=#{expected_title.inspect} actual=#{entry['principle'].inspect}"
  end

  mechanisms = entry["mechanism_found"]
  if active_statuses.include?(status)
    unless mechanisms.is_a?(Array) && !mechanisms.empty?
      errors << "MECHANISM_REQUIRED: #{id} status=#{status}"
      next
    end
  elsif !mechanisms.nil?
    errors << "MECHANISM_MUST_BE_NULL: #{id} status=#{status}"
    next
  end
  next if mechanisms.nil?
  unless mechanisms.is_a?(Array)
    errors << "MECHANISM_TYPE_INVALID: #{id}"
    next
  end

  mechanisms.each_with_index do |mechanism, mechanism_index|
    mlabel = "#{id}.mechanism_found[#{mechanism_index}]"
    unless mechanism.is_a?(Hash)
      errors << "MECHANISM_ITEM_INVALID: #{mlabel}"
      next
    end
    unknown_mechanism = mechanism.keys - mechanism_keys
    missing_mechanism = mechanism_keys - mechanism.keys
    errors << "MECHANISM_UNKNOWN_FIELD: #{mlabel} #{unknown_mechanism.join(',')}" unless unknown_mechanism.empty?
    errors << "MECHANISM_MISSING_FIELD: #{mlabel} #{missing_mechanism.join(',')}" unless missing_mechanism.empty?
    next unless unknown_mechanism.empty? && missing_mechanism.empty?

    path = mechanism["path"]
    check = mechanism["check"]
    stages = mechanism["stages"]
    { "path" => path, "check" => check }.each do |kind, value|
      unless value.is_a?(String) && !value.strip.empty?
        errors << "MECHANISM_#{kind.upcase}_INVALID: #{mlabel}"
        next
      end
      if value.start_with?("/", "~") || value.split("/").include?("..") ||
         value.include?("*") || value.match?(/:\d+\z/)
        errors << "MECHANISM_#{kind.upcase}_INVALID: #{mlabel}=#{value}"
        next
      end
      full_path = File.join(Dir.pwd, value)
      if File.symlink?(full_path)
        errors << "MECHANISM_#{kind.upcase}_SYMLINK: #{mlabel}=#{value}"
      elsif !File.file?(full_path)
        marker = kind == "path" ? "MECHANISM_PATH_MISSING" : "MECHANISM_CHECK_MISSING"
        errors << "#{marker}: #{mlabel}=#{value}"
      else
        _out, _err, status_result = Open3.capture3("git", "ls-files", "--error-unmatch", "--", value)
        errors << "MECHANISM_#{kind.upcase}_UNTRACKED: #{mlabel}=#{value}" unless status_result.success?
      end
    end

    if path == check
      errors << "MECHANISM_SELF_EVIDENCE: #{mlabel}=#{path}"
    end
    if check.is_a?(String) && File.file?(check) && !File.executable?(check)
      errors << "MECHANISM_CHECK_NOT_EXECUTABLE: #{mlabel}=#{check}"
    end
    if path.is_a?(String) && check.is_a?(String) && File.file?(check) &&
       !File.read(check).include?(path)
      errors << "MECHANISM_CHECK_DISCONNECTED: #{mlabel} path=#{path} check=#{check}"
    end

    unless stages.is_a?(Array) && !stages.empty? && stages.all? { |stage| stage.is_a?(String) }
      errors << "STAGES_INVALID: #{mlabel}"
      next
    end
    invalid_stages = stages - allowed_stages
    errors << "STAGE_INVALID: #{mlabel}=#{invalid_stages.join(',')}" unless invalid_stages.empty?
    errors << "STAGE_DUPLICATE: #{mlabel}" unless stages.uniq.length == stages.length

    stages.each do |stage|
      case stage
      when "pre-commit"
        errors << "WIRING_MISSING: #{mlabel} pre-commit path=#{path}" unless path == "hooks/pre-commit"
      when "pre-push"
        prepush_wired = path == "hooks/pre-push" ||
          (check.is_a?(String) && check.start_with?("scripts/acceptance-") &&
           File.read("hooks/pre-push").include?("acceptance-*.sh"))
        errors << "WIRING_MISSING: #{mlabel} pre-push check=#{check.inspect}" unless prepush_wired
      when "session-start"
        expected_command = "bash #{path}"
        unless settings_strings.any? { |value| value.include?(expected_command) }
          errors << "WIRING_MISSING: #{mlabel} session-start command=#{expected_command}"
        end
      when "acceptance"
        unless check.is_a?(String) && check.start_with?("scripts/acceptance-")
          errors << "WIRING_MISSING: #{mlabel} acceptance check=#{check.inspect}"
        end
      when "ci"
        escaped = Regexp.escape(check.to_s)
        command = /(?:^|[[:space:]])(?:bash|sh)[[:space:]]+#{escaped}(?:[[:space:]]|$)/
        unless ci_runs.any? { |run| run.lines.any? { |line| line.match?(command) } }
          errors << "WIRING_MISSING: #{mlabel} ci command=bash #{check}"
        end
      end
    end
  end
end

actual_ids = data.map { |entry| entry["id"] if entry.is_a?(Hash) }.compact
unless actual_ids.sort == expected_ids.sort
  missing_ids = expected_ids - actual_ids
  extra_ids = actual_ids - expected_ids
  errors << "ID_SET_MISMATCH: missing=#{missing_ids.join(',')} extra=#{extra_ids.join(',')}"
end

if errors.empty?
  counts = statuses.map { |status| "#{status}=#{data.count { |entry| entry['status'] == status }}" }
  puts "SCHEMA_OK: 32/32 exact fields, SOT titles, mechanism paths, static wiring"
  puts "STATUS_COUNTS: #{counts.join(' ')}"
  exit 0
end

errors.each { |error| puts error }
puts "SCHEMA_FAIL: #{errors.length} violation(s)"
exit 1
RUBY
schema_rc=$?
if [ "$schema_rc" -ne 0 ]; then
  exit 1
fi
if [ "$MODE" = "--schema-only" ]; then
  exit 0
fi

overall=0
if ! git fetch --quiet origin main; then
  echo "BASELINE_FETCH_FAILED: origin/main"
  overall=1
elif git cat-file -e "origin/main:$FILE" 2>/dev/null; then
  baseline=$(mktemp)
  trap 'rm -f "$baseline"' EXIT
  if ! git show "origin/main:$FILE" > "$baseline"; then
    echo "BASELINE_READ_FAILED: origin/main:$FILE"
    overall=1
  else
    ruby -rpsych - "$baseline" "$FILE" <<'RUBY'
old_file, new_file = ARGV
begin
  old_data = Psych.safe_load(File.read(old_file), permitted_classes: [], permitted_symbols: [], aliases: false)
  new_data = Psych.safe_load(File.read(new_file), permitted_classes: [], permitted_symbols: [], aliases: false)
rescue Psych::Exception => e
  puts "BASELINE_PARSE_FAILED: #{e.message.lines.first.to_s.strip}"
  exit 1
end
rank = { "해당없음" => 0, "없음" => 1, "미확인" => 1, "부분" => 2, "완전" => 3 }
old_status = old_data.to_h { |entry| [entry["id"], entry["status"]] }
regressions = []
new_data.each do |entry|
  id = entry["id"]
  next unless old_status.key?(id)
  before = old_status[id]
  after = entry["status"]
  regressions << [id, before, after] if rank.fetch(after, -1) < rank.fetch(before, -1)
end
if regressions.empty?
  puts "STATUS_REGRESSION_OK: 0"
  exit 0
end
regressions.each { |id, before, after| puts "STATUS_REGRESSION: #{id} #{before} -> #{after}" }
exit 1
RUBY
    regression_rc=$?
    [ "$regression_rc" -eq 0 ] || overall=1
  fi
else
  echo "BASELINE_NOT_AVAILABLE: origin/main:$FILE — first introduction; regression is not counted as PASS"
fi

ruby -rpsych - "$FILE" <<'RUBY'
data = Psych.safe_load(File.read(ARGV[0]), permitted_classes: [], permitted_symbols: [], aliases: false)
unmet = data.reject do |entry|
  entry["status"] == "완전" &&
    entry["mechanism_found"].is_a?(Array) &&
    entry["mechanism_found"].any? { |mechanism| mechanism["stages"].include?("ci") }
end
if unmet.empty?
  puts "P1_OK: 32/32 complete with CI-wired mechanisms"
  exit 0
end
puts "P1_UNMET: #{unmet.length}/32 — #{unmet.map { |entry| entry['id'] }.join(',')}"
exit 1
RUBY
p1_rc=$?
[ "$p1_rc" -eq 0 ] || overall=1

exit "$overall"
