#!/usr/bin/env bash
# acceptance-docs-workflow-sync.sh — 검증 지침의 단계 목록이 실제 워크플로와 맞는가 (AC11).
#
# 겨냥하는 결함: docs/sot/verification-commands.md 는 "워크플로 스텝 NN개 전부"라고 손으로
# 적어 둔다. 스텝이 늘거나 줄어도 아무도 그 숫자를 확인하지 않는다. 실제로 2026-08-27
# 시점에 문서는 24개라고 적혀 있었고 워크플로는 그 뒤로 계속 늘었다. 운영자가 "무엇이
# 도는가"를 이 문서로 판단하는데 그 표가 사실과 다르면 판단 자체가 틀린다.
#
#   통과 — 손대지 않은 문서와 워크플로는 exit 0 과 양수 CHECKED
#   차단 — 행 삭제·유령 행·순서 뒤바뀜·id 오타·워크플로만 늘어남·수동 숫자 불일치
#   무효 — 문서 없음·표 없음은 통과가 아니라 exit 2 (P20)
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

CHECKER="$REPO/scripts/verify/check-docs-workflow-sync.sh"
DOC="$REPO/docs/sot/verification-commands.md"
WF="$REPO/.github/workflows/verify.yml"

for required in "$CHECKER" "$DOC" "$WF"; do
  if [ ! -f "$required" ]; then
    echo "FAIL: 필요한 파일이 없다 — $required (fail-closed)"
    echo "CHECKED: 0"
    exit 2
  fi
done

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || {
  echo "NOT_RUN: mktemp 실패"
  echo "CHECKED: 0"
  exit 2
}
case "$TMP" in
  /tmp/*|/private/tmp/*|/var/folders/*|/private/var/folders/*) ;;
  *) echo "NOT_RUN: 안전하지 않은 임시 경로 — $TMP"; echo "CHECKED: 0"; exit 2 ;;
esac
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

TOTAL=12
checked=0
failed=0

record() {
  local ok="$1"
  local label="$2"
  local detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$label" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$label" "$detail"
    failed=1
  fi
}

# expect <설명> <기대 종료값> <문서> <워크플로>
expect() {
  local label="$1"
  local wanted="$2"
  local doc="$3"
  local wf="$4"
  local rc=0
  local out=""
  if [ -z "$doc" ] || [ -z "$wf" ]; then
    record 1 "$label" "주입 실패 — 사본 경로가 비었다(공격이 실행되지 않았다)"
    return
  fi
  out=$(WORKFLOW_FILE="$wf" bash "$CHECKER" "$doc" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ]; then
    record 0 "$label" "exit=$rc"
  else
    record 1 "$label" "expected exit=$wanted actual=$rc / $(printf '%s' "$out" | grep '^FAIL:' | head -2 | tr '\n' ' ')"
  fi
}

mutate_doc() {
  local name="$1"
  local code="$2"
  local path
  path="$TMP/doc-$name.md"
  cp "$DOC" "$path" || return 1
  ruby -e "$code" "$path" || return 1
  if cmp -s "$DOC" "$path"; then
    return 1
  fi
  printf '%s' "$path"
}

mutate_wf() {
  local name="$1"
  local code="$2"
  local path
  path="$TMP/wf-$name.yml"
  cp "$WF" "$path" || return 1
  ruby -e "$code" "$path" || return 1
  if cmp -s "$WF" "$path"; then
    return 1
  fi
  printf '%s' "$path"
}

# ── 통과 쪽 ──────────────────────────────────────────────────────────────────
expect "실제 문서·워크플로 → 통과" 0 "$DOC" "$WF"

clean_out=$(WORKFLOW_FILE="$WF" bash "$CHECKER" "$DOC" 2>&1)
clean_checked=$(printf '%s\n' "$clean_out" | awk -F'CHECKED:' '/CHECKED:/ { gsub(/[^0-9]/, "", $2); v=$2 } END { print v + 0 }')
if [ "$clean_checked" -ge 1 ]; then
  record 0 "정상 대조의 CHECKED 양수" "CHECKED=$clean_checked"
else
  record 1 "정상 대조의 CHECKED 양수" "CHECKED=$clean_checked — 0건 대조는 합격이 아니다"
fi

# ── 차단 쪽: 문서를 고친다 ───────────────────────────────────────────────────
p=$(mutate_doc row-deleted '
path = ARGV[0]
lines = File.readlines(path)
idx = lines.index { |l| l =~ /^\|\s*\d+\s*\|\s*`hs-a4`/ }
raise "대상 행 없음" if idx.nil?
lines.delete_at(idx)
File.write(path, lines.join)
')
expect "문서에서 단계 1행 삭제 → 불합격" 1 "$p" "$WF"

p=$(mutate_doc row-ghost '
path = ARGV[0]
lines = File.readlines(path)
idx = lines.index { |l| l =~ /^\|\s*\d+\s*\|\s*`hs-a4`/ }
raise "대상 행 없음" if idx.nil?
lines.insert(idx, "| 99 | `ghost-step` | 존재하지 않는 단계 | 아무것도 아님 |\n")
File.write(path, lines.join)
')
expect "문서에 유령 단계 추가 → 불합격" 1 "$p" "$WF"

p=$(mutate_doc row-id-typo '
path = ARGV[0]
s = File.read(path)
s = s.sub("`hs-a4`", "`hs-a4x`")
File.write(path, s)
')
expect "문서의 단계 id 오타 → 불합격" 1 "$p" "$WF"

p=$(mutate_doc rows-swapped '
path = ARGV[0]
lines = File.readlines(path)
i = lines.index { |l| l =~ /^\|\s*\d+\s*\|\s*`hs-a3`/ }
j = lines.index { |l| l =~ /^\|\s*\d+\s*\|\s*`hs-a4`/ }
raise "대상 행 없음" if i.nil? || j.nil?
lines[i], lines[j] = lines[j], lines[i]
File.write(path, lines.join)
')
expect "문서에서 단계 순서 뒤바꿈 → 불합격" 1 "$p" "$WF"

p=$(mutate_doc count-wrong '
path = ARGV[0]
s = File.read(path)
s = s.sub(/워크플로 스텝 \d+개 전부/, "워크플로 스텝 3개 전부")
File.write(path, s)
')
expect "문서의 수동 숫자가 실제와 다름 → 불합격" 1 "$p" "$WF"

p=$(mutate_doc table-gone '
path = ARGV[0]
lines = File.readlines(path)
lines.reject! { |l| l =~ /^\|\s*\d+\s*\|\s*`[a-z0-9-]+`/ }
File.write(path, lines.join)
')
expect "문서에서 단계 표 전체 삭제 → 스캔 무효" 2 "$p" "$WF"

# ── 차단 쪽: 워크플로만 바꾸고 문서를 두면 ──────────────────────────────────
p=$(mutate_wf step-added '
require "psych"
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
d["jobs"]["verify"]["steps"] << { "name" => "문서에 없는 새 스텝", "id" => "undocumented", "run" => "echo hi\n" }
File.write(path, Psych.dump(d))
')
expect "워크플로에만 스텝 추가 → 불합격" 1 "$DOC" "$p"

p=$(mutate_wf step-removed '
require "psych"
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
d["jobs"]["verify"]["steps"].reject! { |s| s["id"] == "hs-a4" }
File.write(path, Psych.dump(d))
')
expect "워크플로에서만 스텝 삭제 → 불합격" 1 "$DOC" "$p"

# ── fail-closed ─────────────────────────────────────────────────────────────
expect "문서 없음 → 스캔 무효" 2 "$TMP/no-such-doc.md" "$WF"

# ── 원본 불변 ────────────────────────────────────────────────────────────────
current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then
  record 0 "원본 저장소 상태 불변" "before/after 동일"
else
  record 1 "원본 저장소 상태 불변" "변경 발생"
fi

printf 'CHECKED: %d\n' "$checked"
if [ "$checked" -ne "$TOTAL" ]; then
  printf 'FAIL: 실행 사례 수 불일치 — expected=%d actual=%d\n' "$TOTAL" "$checked"
  failed=1
fi
if [ "$failed" -eq 0 ]; then
  echo "VERDICT: PASS"
else
  echo "VERDICT: FAIL"
fi
exit "$failed"
