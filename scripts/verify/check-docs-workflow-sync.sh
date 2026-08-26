#!/usr/bin/env bash
# check-docs-workflow-sync.sh — 검증 지침의 단계 목록이 실제 워크플로와 맞는지 대조한다 (AC11).
#
# 왜 필요한가:
#   docs/sot/verification-commands.md 는 운영자가 "서버에서 무엇이 도는가"를 판단하는
#   문서다. 그런데 스텝 수를 손으로 적어 두고 아무도 확인하지 않았다. 스텝이 늘거나
#   줄면 그 표는 조용히 사실과 갈라지고, 그 표를 믿은 판단도 함께 틀린다.
#
#   대조는 표시 이름이 아니라 **안정된 step id** 로 한다. 이름을 기준으로 삼으면
#   ci-step-integrity 예외 목록에서 겪은 것과 같은 함정에 다시 빠진다(이름은 복사가
#   자유롭다). 그래서 문서 표에 step id 열을 두고 그 열로 맞춘다.
#
# 입력 : $1 = 문서 경로 (기본 docs/sot/verification-commands.md)
#        WORKFLOW_FILE = 워크플로 경로 (기본 .github/workflows/verify.yml)
# 출력 : PASS:/FAIL: 줄과 마지막 줄 `CHECKED: <대조 항목 수>`
# exit : 0 = 일치 | 1 = 불일치 | 2 = 스캔 무효(파일 없음·파싱 실패·표 0행)
#
# 막지 못하는 것: 표의 "실행 내용" 설명이 실제와 다른 것. 그 열은 사람이 쓰는 산문이라
#   기계가 뜻을 대조할 수 없다. 여기서 보장하는 것은 **어떤 단계가 몇 번째로 도는가**다.
set -uo pipefail

DOC="${1:-docs/sot/verification-commands.md}"
WORKFLOW="${WORKFLOW_FILE:-.github/workflows/verify.yml}"

if [ ! -f "$DOC" ]; then
  echo "NOT_RUN: 문서가 없다 — $DOC (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi
if [ ! -f "$WORKFLOW" ]; then
  echo "NOT_RUN: 워크플로가 없다 — $WORKFLOW (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

ruby -rpsych -rdate -e '
doc_path, wf_path = ARGV

def bail(msg, code)
  puts msg
  puts "CHECKED: 0"
  exit code
end

begin
  wf = Psych.safe_load(File.read(wf_path), aliases: true, permitted_classes: [Date, Time])
rescue Psych::Exception => e
  bail("FAIL: 워크플로 파싱 실패 — #{e.message.lines.first.to_s.strip}", 2)
end
jobs = wf.is_a?(Hash) ? wf["jobs"] : nil
bail("FAIL: jobs 를 읽지 못했다 — #{wf_path}", 2) unless jobs.is_a?(Hash) && !jobs.empty?

# 문서 표에 적는 대상은 `- name:` 이 붙은 스텝이다(checkout 은 uses 라 각주로 뺀다).
actual = []
jobs.each do |_jn, job|
  next unless job.is_a?(Hash)
  (job["steps"] || []).each do |s|
    next unless s.is_a?(Hash)
    next unless s["name"]
    actual << { id: s["id"].to_s, name: s["name"].to_s }
  end
end
bail("FAIL: 워크플로에 이름 붙은 스텝이 0개 — 대조 대상 0개는 합격이 아니다 (P20)", 2) if actual.empty?

missing_ids = actual.select { |s| s[:id].empty? }
unless missing_ids.empty?
  puts "FAIL: id 없는 스텝이 #{missing_ids.size}개 — 표시 이름으로는 안정된 대조를 할 수 없다"
  missing_ids.each { |s| puts "  이름: #{s[:name]}" }
  puts "CHECKED: 0"
  exit 1
end

doc = File.read(doc_path)

# 표 행: | N | `step-id` | 이름 | 설명 |
documented = []
doc.each_line do |line|
  m = line.match(/\A\|\s*(\d+)\s*\|\s*`([A-Za-z0-9._-]+)`\s*\|\s*([^|]*?)\s*\|/)
  next if m.nil?
  documented << { order: m[1].to_i, id: m[2], name: m[3] }
end

if documented.empty?
  bail("FAIL: 문서에서 단계 표를 찾지 못했다 — `| N | \\`step-id\\` | 이름 |` 행이 0개 (P20)", 2)
end

errors = []
passes = []
checked = 0

# ── ① 순번이 1부터 빠짐없이 이어지는가 ──────────────────────────────────────
documented.each_with_index do |row, i|
  checked += 1
  if row[:order] != i + 1
    errors << "DOC_ORDER_BROKEN: 문서 #{i + 1}번째 행의 번호가 #{row[:order]} — 번호가 이어지지 않는다"
  end
end

# ── ② 문서와 워크플로의 id 순서가 같은가 ────────────────────────────────────
doc_ids = documented.map { |r| r[:id] }
wf_ids  = actual.map { |s| s[:id] }

(doc_ids - wf_ids).each do |id|
  checked += 1
  errors << "DOC_GHOST_STEP: 문서에 적힌 `#{id}` 가 워크플로에 없다 — 돌지 않는 단계를 돈다고 적었다"
end
(wf_ids - doc_ids).each do |id|
  checked += 1
  errors << "DOC_MISSING_STEP: 워크플로의 `#{id}` 가 문서에 없다 — 운영자가 모르는 검사가 돈다"
end

if doc_ids.size == wf_ids.size && (doc_ids - wf_ids).empty? && (wf_ids - doc_ids).empty?
  doc_ids.each_with_index do |id, i|
    checked += 1
    if id == wf_ids[i]
      passes << "STEP #{i + 1} #{id}"
    else
      errors << "DOC_ORDER_MISMATCH: #{i + 1}번째가 문서는 `#{id}`, 워크플로는 `#{wf_ids[i]}` — 순서가 다르다"
    end
  end

  # ── ③ 표시 이름까지 맞는가 (사람이 읽는 열의 신뢰도) ──────────────────────
  documented.each_with_index do |row, i|
    checked += 1
    if row[:name] == actual[i][:name]
      passes << "NAME #{row[:id]}"
    else
      errors << "DOC_NAME_MISMATCH: `#{row[:id]}` 의 이름이 문서는 #{row[:name].inspect}, " \
                "워크플로는 #{actual[i][:name].inspect}"
    end
  end
end

# ── ④ 손으로 적은 개수가 실제와 맞는가 ──────────────────────────────────────
checked += 1
count_match = doc.match(/워크플로 스텝 (\d+)개 전부/)
if count_match.nil?
  errors << "DOC_COUNT_ABSENT: 문서에 `워크플로 스텝 N개 전부` 문장이 없다 — 개수 대조 지점이 사라졌다"
elsif count_match[1].to_i != actual.size
  errors << "DOC_COUNT_WRONG: 문서는 스텝 #{count_match[1]}개라 적었는데 실제는 #{actual.size}개 — " \
            "손으로 적은 숫자가 사실과 갈라졌다"
else
  passes << "COUNT #{actual.size}"
end

if checked.zero?
  bail("FAIL: 대조 항목이 0개 — 검사할 것이 없어서 통과하는 것은 합격이 아니다 (P20)", 2)
end

passes.each { |p| puts "PASS: #{p}" }
if errors.empty?
  puts "PASS: 문서 단계 #{documented.size}행이 워크플로 스텝 #{actual.size}개와 순서까지 일치"
  puts "CHECKED: #{checked}"
  exit 0
else
  errors.each { |e| puts "FAIL: #{e}" }
  puts "CHECKED: #{checked}"
  exit 1
end
' "$DOC" "$WORKFLOW"
