#!/usr/bin/env bash
# 두 Strict 스킬의 공통 원칙 직접 로드 계약과 플랫폼별 엔진 순서를 검증한다.
set -uo pipefail

# 기본값을 두지 않는다. 예전에는 개인 전역 지침 파일이 기본값이라, 인자 없이 부르면
# 저장소 밖 상태를 판정하고 그 결과가 배송을 막았다(2026-08-21). 대상은 부르는 쪽이 정한다.
if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
  echo 'FAIL: 검사 대상 두 경로를 인자로 받아야 한다 — 사용법: $0 <codex-skill.md> <claude-skill.md>'
  exit 2
fi
CODEX_SKILL=$1
CLAUDE_SKILL=$2

for file in "$CODEX_SKILL" "$CLAUDE_SKILL"; do
  if [ ! -f "$file" ] || [ -L "$file" ] || [ ! -s "$file" ]; then
    printf 'VERDICT: FAIL\nSKILL_FILE_INVALID: %s\nCHECKED: 0\n' "$file"
    exit 1
  fi
done

if ! command -v ruby >/dev/null 2>&1; then
  printf 'VERDICT: NOT_RUN\nREASON: ruby unavailable\nCHECKED: 0\n'
  exit 2
fi

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P) || {
  printf 'VERDICT: NOT_RUN\nREASON: script directory unavailable\nCHECKED: 0\n'
  exit 2
}
REPO=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd -P) || {
  printf 'VERDICT: NOT_RUN\nREASON: repository root unavailable\nCHECKED: 0\n'
  exit 2
}
SOT_PATH="$REPO/docs/sot/coding-principles.md"

ruby - "$SOT_PATH" "$CODEX_SKILL" "$CLAUDE_SKILL" <<'RUBY'
sot_path, codex_file, claude_file = ARGV
errors = []
unless File.file?(sot_path) && !File.zero?(sot_path)
  puts "VERDICT: NOT_RUN"
  puts "SOT_FILE_MISSING: #{sot_path}"
  puts "CHECKED: 0"
  exit 2
end

sot = File.read(sot_path)
p11_lines = sot.lines.select { |line| line.include?("**P11**") }
file_clause = p11_lines.length == 1 ? p11_lines.first.split("②", 2).first : ""
line_limit_matches = file_clause.scan(/\bhard\s+(\d+)\s+LOC\b/i).flatten.map(&:to_i)
unless line_limit_matches.length == 1
  puts "VERDICT: NOT_RUN"
  puts "SOT_LIMIT_PARSE_FAILED: #{sot_path}"
  puts "CHECKED: 0"
  exit 2
end
line_limit = line_limit_matches.fetch(0)
start_marker = "<!-- STRICT_PRINCIPLES_CONTRACT:START -->"
end_marker = "<!-- STRICT_PRINCIPLES_CONTRACT:END -->"

extract = lambda do |path|
  text = File.read(path)
  starts = text.scan(Regexp.new(Regexp.escape(start_marker))).length
  ends = text.scan(Regexp.new(Regexp.escape(end_marker))).length
  if starts != 1 || ends != 1
    errors << "MARKER_COUNT_INVALID: #{path} start=#{starts} end=#{ends}"
    next ""
  end
  text[/#{Regexp.escape(start_marker)}.*?#{Regexp.escape(end_marker)}/m].to_s
end

codex = File.read(codex_file)
claude = File.read(claude_file)
codex_block = extract.call(codex_file)
claude_block = extract.call(claude_file)
errors << "COMMON_CONTRACT_MISMATCH" unless codex_block == claude_block

required = [
  "docs/sot/coding-principles.md",
  "docs/sot/principles.yaml",
  "bash scripts/acceptance-principles-check.sh",
  "T 계약",
  "goal의 검증 장부",
  "PASS / FAIL / NOT_RUN",
  ".omx/project-memory.json",
  "보조 정보",
  "직접 로드",
  "전체 Strict 판정을 PASS로 만들지 않는다",
  "V1이 FAIL이면",
  "V2를 실제 실행"
]
required.each do |token|
  errors << "COMMON_TOKEN_MISSING: #{token}" unless codex_block.include?(token)
end

codex_order = "Codex판은 `G=Codex → V1=Claude → V2=Codex`"
claude_order = "Claude판은 `G=Claude → V1=Codex → V2=Claude`"
errors << "CODEX_ENGINE_ORDER_INVALID" unless codex.include?(codex_order)
errors << "CLAUDE_ENGINE_ORDER_INVALID" unless claude.include?(claude_order)

{ codex_file => codex, claude_file => claude }.each do |path, text|
  lines = text.lines.length
  errors << "LINE_LIMIT_EXCEEDED: #{path}=#{lines} hard=#{line_limit}" if lines > line_limit
end

if errors.empty?
  puts "VERDICT: PASS"
  puts "COMMON_CONTRACT: PASS byte-identical"
  puts "ENGINE_ORDER: PASS Codex/Claude platform-only difference"
  puts "LINE_LIMIT: hard=#{line_limit}"
  puts "LINES: codex=#{codex.lines.length} claude=#{claude.lines.length}"
  puts "CHECKED: 2"
  exit 0
end

puts "VERDICT: FAIL"
errors.each { |error| puts error }
puts "CHECKED: 2"
puts "FAILURES: #{errors.length}"
exit 1
RUBY
