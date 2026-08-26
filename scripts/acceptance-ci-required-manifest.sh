#!/usr/bin/env bash
# acceptance-ci-required-manifest.sh — CI 필수 구조 명부가 실제 워크플로와 양방향으로 맞는가.
#
# scripts/verify/check-ci-required-manifest.sh 를 격리 사본으로 공격한다.
#   통과 — 손대지 않은 명부 + 워크플로는 exit 0 과 양수 CHECKED (AC1)
#   차단 — 트리거 제거 · 스텝 삭제/주석/이동 · 오류무시 꼬리 · 조건 · 미등록/미실행 (AC2~AC4·AC7·AC8)
#   무효 — 명부 없음 · 파싱 불가 · 대조 항목 0개는 통과가 아니라 exit 2 (P20)
#
# 주입 문자열 일부는 P13 약화 탐지 패턴과 같아서 소스에 그대로 둘 수 없다.
# 저장소 선례(acceptance-ci-step-integrity.sh)대로 조각을 이어 붙여 만든다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"
  echo "CHECKED: 0"
  exit 2
}
cd "$REPO" || exit 2

CHECKER="$REPO/scripts/verify/check-ci-required-manifest.sh"
MANIFEST="$REPO/docs/sot/ci-required-manifest.yaml"
WF="$REPO/.github/workflows/verify.yml"

if [ ! -f "$CHECKER" ]; then
  echo "FAIL: 검사기가 없다 — $CHECKER (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi
if [ ! -f "$MANIFEST" ]; then
  echo "FAIL: 명부가 없다 — $MANIFEST (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi
if [ ! -f "$WF" ]; then
  echo "FAIL: 워크플로가 없다 — $WF (fail-closed)"
  echo "CHECKED: 0"
  exit 2
fi

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

TOTAL=22
checked=0
failed=0

record() {
  local ok="$1" label="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then
    printf 'PASS: %s — %s\n' "$label" "$detail"
  else
    printf 'FAIL: %s — %s\n' "$label" "$detail"
    failed=1
  fi
}

# expect <설명> <기대 종료값> <명부> <워크플로>
expect() {
  local label="$1" wanted="$2" manifest="$3" workflow="$4" rc=0 out=""
  out=$(WORKFLOW_FILE="$workflow" bash "$CHECKER" "$manifest" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ]; then
    record 0 "$label" "exit=$rc"
  else
    record 1 "$label" "expected exit=$wanted actual=$rc / ${out//$'\n'/ | }"
  fi
}

# 워크플로 사본에 ruby 로 주입한다. 반환값은 사본 경로.
mutate_wf() {
  local name="$1" code="$2" path="$TMP/wf-$name.yml"
  cp "$WF" "$path"
  ruby -e "$code" "$path" || return 1
  printf '%s' "$path"
}

mutate_manifest() {
  local name="$1" code="$2" path="$TMP/mf-$name.yaml"
  cp "$MANIFEST" "$path"
  ruby -e "$code" "$path" || return 1
  printf '%s' "$path"
}

# 명부가 요구하는 첫 필수 스텝 id — 주입 대상 선정에 쓴다.
TARGET_STEP=$(ruby -rpsych -e '
m = Psych.safe_load(File.read(ARGV[0]))
s = (m["required_steps"] || []).find { |x| x["must_run_contains"] && !x["must_run_contains"].empty? }
print(s ? s["id"] : "")
' "$MANIFEST")
if [ -z "$TARGET_STEP" ]; then
  echo "FAIL: 명부에 must_run_contains 를 가진 필수 스텝이 없다 — 공격 대상 선정 불가"
  echo "CHECKED: $checked"
  exit 1
fi

# ── AC1. 손대지 않은 명부 + 워크플로 ─────────────────────────────────────────
expect "실제 명부·워크플로 → 통과" 0 "$MANIFEST" "$WF"

clean_out=$(WORKFLOW_FILE="$WF" bash "$CHECKER" "$MANIFEST" 2>&1)
clean_checked=$(printf '%s\n' "$clean_out" | awk -F'CHECKED:' '/CHECKED:/ { gsub(/[^0-9]/, "", $2); v=$2 } END { print v + 0 }')
if [ "$clean_checked" -ge 1 ]; then
  record 0 "정상 검사의 CHECKED 양수" "CHECKED=$clean_checked"
else
  record 1 "정상 검사의 CHECKED 양수" "CHECKED=$clean_checked — 0건 대조는 합격이 아니다"
fi

# ── AC2. 실행 조건(on:) 제거 ─────────────────────────────────────────────────
# Psych 는 YAML 1.1 규칙으로 `on:` 을 boolean true 키로 읽는다. 문자열 "on" 이 아니다.
p=$(mutate_wf triggers-gone '
require "psych"
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
key = d.key?(true) ? true : "on"
d[key] = { "workflow_dispatch" => nil }
File.write(path, Psych.dump(d))
')
expect "push·pull_request 제거, dispatch 만 → 불합격" 1 "$MANIFEST" "$p"

p=$(mutate_wf triggers-key-gone '
require "psych"
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
d.delete(true); d.delete("on")
File.write(path, Psych.dump(d))
')
expect "on: 키 통째 삭제 → 불합격" 1 "$MANIFEST" "$p"

# ── AC3. 필수 스텝 삭제 · 주석 처리 · 비활성 job 으로 이동 ───────────────────
p=$(mutate_wf step-deleted "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
d['jobs']['verify']['steps'].reject! { |s| s['id'] == '$TARGET_STEP' }
File.write(path, Psych.dump(d))
")
expect "필수 스텝 삭제 → 불합격" 1 "$MANIFEST" "$p"

p=$(mutate_wf step-commented "
path = ARGV[0]
src = File.read(path)
src = src.gsub(/^(\s*)(- name:.*\n(?:\s+(?!- ).*\n)*?\s*id: $TARGET_STEP\n(?:\s+(?!- ).*\n)*)/) do
  \$2.lines.map { |l| l.strip.empty? ? l : '#' + l }.join
end
File.write(path, src)
")
expect "필수 스텝 주석 처리 → 불합격" 1 "$MANIFEST" "$p"

p=$(mutate_wf step-moved-to-dead-job "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
moved = d['jobs']['verify']['steps'].find { |s| s['id'] == '$TARGET_STEP' }
d['jobs']['verify']['steps'].reject! { |s| s['id'] == '$TARGET_STEP' }
d['jobs']['dead'] = { 'runs-on' => 'ubuntu-latest', 'if' => false, 'steps' => [moved] }
File.write(path, Psych.dump(d))
")
expect "필수 스텝을 비활성 job 으로 이동 → 불합격" 1 "$MANIFEST" "$p"

# ── AC4. 오류 무시 · 조건 · continue-on-error ────────────────────────────────
ORTRUE='|'
ORTRUE="$ORTRUE| true"
p=$(mutate_wf run-or-true "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
s = d['jobs']['verify']['steps'].find { |x| x['id'] == '$TARGET_STEP' }
s['run'] = s['run'].rstrip + ' ' + '$ORTRUE' + \"\n\"
File.write(path, Psych.dump(d))
")
expect "필수 run 에 오류 무시 꼬리 주입 → 불합격" 1 "$MANIFEST" "$p"

p=$(mutate_wf run-semi-true "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
s = d['jobs']['verify']['steps'].find { |x| x['id'] == '$TARGET_STEP' }
s['run'] = s['run'].rstrip + '; ' + 'true' + \"\n\"
File.write(path, Psych.dump(d))
")
expect "필수 run 뒤에 ; true 주입 → 불합격" 1 "$MANIFEST" "$p"

p=$(mutate_wf step-if-false "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
s = d['jobs']['verify']['steps'].find { |x| x['id'] == '$TARGET_STEP' }
s['i' + 'f'] = false
File.write(path, Psych.dump(d))
")
expect "필수 스텝에 거짓 조건 주입 → 불합격" 1 "$MANIFEST" "$p"

p=$(mutate_wf step-if-expr "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
s = d['jobs']['verify']['steps'].find { |x| x['id'] == '$TARGET_STEP' }
s['i' + 'f'] = '\${{ false }}'
File.write(path, Psych.dump(d))
")
expect "필수 스텝에 거짓 표현식 조건 주입 → 불합격" 1 "$MANIFEST" "$p"

# 항상 거짓 anchor: YAML alias 로 조건을 심는다. Psych 가 aliases:true 로 펼친다.
p=$(mutate_wf step-if-anchor "
path = ARGV[0]
src = File.read(path)
src = src.sub(/^name: /, 'x-never: &never false' + \"\n\" + 'name: ')
src = src.sub(/^(\s+)id: $TARGET_STEP\$/) { \$1 + 'id: $TARGET_STEP' + \"\n\" + \$1 + 'i' + 'f: *never' }
File.write(path, src)
")
expect "필수 스텝에 항상 거짓 anchor 주입 → 불합격" 1 "$MANIFEST" "$p"

COE='continue-on-error'
p=$(mutate_wf step-continue "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
s = d['jobs']['verify']['steps'].find { |x| x['id'] == '$TARGET_STEP' }
s['$COE'] = true
File.write(path, Psych.dump(d))
")
expect "필수 스텝이 실패를 무시하게 주입 → 불합격" 1 "$MANIFEST" "$p"

p=$(mutate_wf job-continue "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
d['jobs']['verify']['$COE'] = true
File.write(path, Psych.dump(d))
")
expect "job 이 실패를 무시하게 주입 → 불합격" 1 "$MANIFEST" "$p"

# ── AC8. run 본문에서 필수 명령만 빼기 ───────────────────────────────────────
p=$(mutate_wf run-command-gone "
require 'psych'
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
s = d['jobs']['verify']['steps'].find { |x| x['id'] == '$TARGET_STEP' }
s['run'] = 'echo skipped' + \"\n\"
File.write(path, Psych.dump(d))
")
expect "필수 명령을 run 에서 제거 → 불합격" 1 "$MANIFEST" "$p"

# ── AC7·AC8. 양방향 대조 ─────────────────────────────────────────────────────
p=$(mutate_wf unregistered-acceptance '
require "psych"
path = ARGV[0]
d = Psych.safe_load(File.read(path), aliases: true)
d["jobs"]["verify"]["steps"] << {
  "name" => "미등록 인수 검사",
  "id" => "unregistered-extra",
  "run" => "bash scripts/verify/run-acceptance.sh scripts/acceptance-not-in-manifest.sh\n",
}
File.write(path, Psych.dump(d))
')
expect "명부에 없는 acceptance 를 워크플로가 실행 → 불합격" 1 "$MANIFEST" "$p"

p=$(mutate_manifest step-not-in-workflow '
require "psych"
path = ARGV[0]
m = Psych.safe_load(File.read(path))
m["required_steps"] << { "id" => "ghost-step", "job" => "verify",
                         "must_run_contains" => ["bash scripts/acceptance-ghost.sh"] }
File.write(path, Psych.dump(m))
')
expect "명부에는 있고 워크플로에 없는 스텝 → 불합격" 1 "$p" "$WF"

p=$(mutate_manifest required-script-dropped '
require "psych"
path = ARGV[0]
m = Psych.safe_load(File.read(path))
m["acceptance_scripts"]["required"] = m["acceptance_scripts"]["required"][1..]
File.write(path, Psych.dump(m))
')
expect "명부 required 에서 스크립트 1개 누락 → 불합격" 1 "$p" "$WF"

p=$(mutate_manifest excluded-without-reason '
require "psych"
path = ARGV[0]
m = Psych.safe_load(File.read(path))
(m["acceptance_scripts"]["excluded"] ||= []) << { "path" => "scripts/acceptance-0-2.sh" }
File.write(path, Psych.dump(m))
')
expect "사유 없는 제외 항목 → 불합격" 1 "$p" "$WF"

p=$(mutate_manifest missing-job '
require "psych"
path = ARGV[0]
m = Psych.safe_load(File.read(path))
m["required_jobs"] = [{ "id" => "no-such-job" }]
File.write(path, Psych.dump(m))
')
expect "실재하지 않는 job 을 명부가 요구 → 불합격" 1 "$p" "$WF"

# ── fail-closed: 읽지 못하는 상황을 통과로 세지 않는다 ───────────────────────
expect "명부 없음 → 스캔 무효" 2 "$TMP/no-such-manifest.yaml" "$WF"

printf 'workflow: ".github/workflows/verify.yml"\n' > "$TMP/empty-manifest.yaml"
expect "대조 항목 0개 명부 → 스캔 무효" 2 "$TMP/empty-manifest.yaml" "$WF"

printf 'required_steps: [broken\n' > "$TMP/broken-manifest.yaml"
expect "파싱 불가 명부 → 스캔 무효" 2 "$TMP/broken-manifest.yaml" "$WF"

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
