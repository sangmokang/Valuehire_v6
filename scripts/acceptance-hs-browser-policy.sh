#!/usr/bin/env bash
# acceptance-hs-browser-policy.sh — HS-05.01 최신 Aside 브라우저 정책 계약이 정본에 남아 있는가.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "VERDICT: NOT_RUN"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

SOT=docs/sot/humansearch-browser-contract.md
POLICY=contracts/humansearch/browser-policy.yaml
GOAL=docs/engineering/humansearch-aside-browser-policy-goal-2026-09-14.md

fail=0
checked=0

pass() {
  checked=$((checked + 1))
  printf 'PASS: %s\n' "$1"
}

fail_case() {
  checked=$((checked + 1))
  printf 'FAIL: %s\n' "$1"
  fail=1
}

require_file() {
  local path="$1" label="$2"
  if [ -f "$path" ] && [ -s "$path" ]; then
    pass "$label 파일 존재 — $path"
  else
    fail_case "$label 파일 없음 또는 빈 파일 — $path"
  fi
}

require_text() {
  local path="$1" pattern="$2" label="$3"
  if [ -f "$path" ] && LC_ALL=C grep -Fq "$pattern" "$path"; then
    pass "$label"
  else
    fail_case "$label 누락 — $path 에 '$pattern' 없음"
  fi
}

forbid_text() {
  local path="$1" pattern="$2" label="$3"
  if [ -f "$path" ] && LC_ALL=C grep -Fq "$pattern" "$path"; then
    fail_case "$label 위반 — $path 에 '$pattern' 남음"
  else
    pass "$label"
  fi
}

require_policy_yaml_values() {
  local out rc=0
  out=$(ruby -rpsych - "$POLICY" 2>&1 <<'RUBY'
path = ARGV.fetch(0)
errors = []

begin
  ast = Psych.parse_stream(File.read(path), filename: path)
rescue Psych::SyntaxError => e
  puts "YAML_PARSE_ERROR: #{e.message.lines.first.to_s.strip}"
  exit 1
end

walk = nil
walk = lambda do |node, label|
  case node
  when Psych::Nodes::Stream, Psych::Nodes::Document
    node.children.each_with_index { |child, index| walk.call(child, "#{label}[#{index}]") }
  when Psych::Nodes::Mapping
    seen = {}
    node.children.each_slice(2).with_index do |(key_node, value_node), index|
      unless key_node.is_a?(Psych::Nodes::Scalar)
        errors << "INVALID_KEY: #{label}[#{index}]"
        next
      end
      key = key_node.value
      errors << "DUPLICATE_KEY: #{label}.#{key}" if seen.key?(key)
      seen[key] = true
      walk.call(value_node, "#{label}.#{key}")
    end
  when Psych::Nodes::Sequence
    node.children.each_with_index { |child, index| walk.call(child, "#{label}[#{index}]") }
  end
end
walk.call(ast, "$")

begin
  data = Psych.safe_load(File.read(path), permitted_classes: [], permitted_symbols: [], aliases: false)
rescue Psych::Exception => e
  errors << "YAML_LOAD_ERROR: #{e.message.lines.first.to_s.strip}"
  data = nil
end

expected = {
  "version" => "2026-09-14.aside-policy",
  "automation_app" => "Aside",
  "forbidden_app" => "Chrome",
  "input_attribution" => "target_app_profile_tab",
  "resume_requires" => "fresh_observation_and_fresh_lease",
  "explicit_stop_requires_user_clear" => true,
  "live_authority_verified" => false,
}
expected_channels = {
  "saramin" => "aside_dedicated_profile",
  "jobkorea" => "aside_dedicated_profile",
  "linkedin_rps" => "aside_owner_real_profile",
}
expected_chrome = {
  "windows_tabs_ports_profiles_extensions_settings" => "do_not_change",
  "input_policy" => "do_not_steal_focus_or_type",
  "chrome_input_is_owner_activity" => true,
}
expected_non_scope = %w[
  rps_project_write
  linkedin_resume_save
  portal_live_run
  chrome_control
]

unless data.is_a?(Hash)
  errors << "ROOT_TYPE_INVALID"
  data = {}
end

allowed_keys = expected.keys + %w[chrome_non_interference channels non_scope]
unknown = data.keys - allowed_keys
missing = allowed_keys - data.keys
errors << "UNKNOWN_KEYS: #{unknown.join(',')}" unless unknown.empty?
errors << "MISSING_KEYS: #{missing.join(',')}" unless missing.empty?

expected.each do |key, value|
  actual = data[key]
  if actual != value
    errors << "VALUE_MISMATCH: #{key} expected=#{value.inspect} actual=#{actual.inspect}"
  end
end

channels = data["channels"]
if channels != expected_channels
  errors << "CHANNELS_MISMATCH: expected=#{expected_channels.inspect} actual=#{channels.inspect}"
end

chrome = data["chrome_non_interference"]
if chrome != expected_chrome
  errors << "CHROME_POLICY_MISMATCH: expected=#{expected_chrome.inspect} actual=#{chrome.inspect}"
end

non_scope = data["non_scope"]
if non_scope != expected_non_scope
  errors << "NON_SCOPE_MISMATCH: expected=#{expected_non_scope.inspect} actual=#{non_scope.inspect}"
end

if errors.empty?
  puts "POLICY_YAML_VALUES: PASS"
  exit 0
end

puts "POLICY_YAML_VALUES: FAIL"
errors.each { |error| puts error }
exit 1
RUBY
  ) || rc=$?
  if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -q '^POLICY_YAML_VALUES: PASS$'; then
    pass "browser-policy 실제 YAML 값·타입·중복키 검사"
  else
    fail_case "browser-policy 실제 YAML 값·타입·중복키 검사 실패 — ${out//$'\n'/; }"
  fi
}

require_file "$SOT" "브라우저 SOT"
require_file "$POLICY" "browser-policy 계약"
require_file "$GOAL" "goal"
require_policy_yaml_values

require_text "$SOT" "실제 자동화 채널은 Aside" "SOT가 Aside 전용 자동화를 명시"
require_text "$SOT" "Chrome의 창·탭·포트·프로필·확장·설정을 변경하지 않는다" "SOT가 Chrome 비간섭을 명시"
require_text "$SOT" "사람인·잡코리아는 Aside 전용 프로필" "SOT가 사람인·잡코리아 Aside 전용 프로필을 명시"
require_text "$SOT" "RPS는 Aside 안의 사장님 실제 LinkedIn Recruiter 프로필" "SOT가 RPS 실프로필 차이를 명시"
require_text "$SOT" "대상 앱·프로필·탭에 귀속" "SOT가 입력 신호 귀속을 명시"
require_text "$SOT" "Chrome 입력을 Aside 사용자 개입으로 해석하지 않는다" "SOT가 Chrome 입력 오인을 금지"
require_text "$SOT" "새 관측과 새 사용권" "SOT가 새 관측·새 lease 재개 조건을 명시"
require_text "$SOT" "명시적 STOP은 새 사용자 해제 없이는 자동 해제하지 않는다" "SOT가 STOP 해제 경계를 명시"
require_text "$SOT" "AppleScript 실행 가능성과 CDP 인증 필요는 라이브 권한 충족 증거가 아니다" "SOT가 현재 Aside 실측의 한계를 명시"
forbid_text "$SOT" "자동 재개하지 않는다." "일반 사람 입력 뒤 영구 재개 금지 문구 제거"

require_text "$POLICY" "automation_app: Aside" "계약이 자동화 앱을 Aside로 고정"
require_text "$POLICY" "forbidden_app: Chrome" "계약이 Chrome 제어 금지를 고정"
require_text "$POLICY" "jobkorea: aside_dedicated_profile" "계약이 잡코리아 Aside 전용 프로필을 고정"
require_text "$POLICY" "saramin: aside_dedicated_profile" "계약이 사람인 Aside 전용 프로필을 고정"
require_text "$POLICY" "linkedin_rps: aside_owner_real_profile" "계약이 RPS Aside 실프로필을 고정"
require_text "$POLICY" "input_attribution: target_app_profile_tab" "계약이 입력 귀속 범위를 고정"
require_text "$POLICY" "resume_requires: fresh_observation_and_fresh_lease" "계약이 재개 조건을 고정"
require_text "$POLICY" "explicit_stop_requires_user_clear: true" "계약이 STOP 수동 해제를 고정"
require_text "$POLICY" "live_authority_verified: false" "계약이 라이브 권한 미충족을 고정"

if [ "$checked" -lt 10 ]; then
  echo "VERDICT: NOT_RUN"
  echo "CHECKED: $checked"
  exit 2
fi

if [ "$fail" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
echo "CHECKED: $checked"
exit "$fail"
