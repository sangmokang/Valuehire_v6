#!/usr/bin/env bash
# acceptance-ci-step-integrity.sh — 워크플로 시작 조건·스텝을 끄면 반드시 빨개지는가.
#
# scripts/verify/check-ci-step-integrity.sh 를 격리 사본으로 공격한다.
# 차단 — 실행 0 trigger, 조건부·오류무시·빈 job·출력만 하는 스텝을 주입하면 전부 불합격
# 통과 — 의미 동등 trigger, 손대지 않은 실제 워크플로와 이유가 적힌 예외는 그대로 합격
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || exit 2
CHECKER="$REPO/scripts/verify/check-ci-step-integrity.sh"
WF="$REPO/.github/workflows/verify.yml"
if [ ! -f "$CHECKER" ] || [ ! -f "$WF" ]; then
  echo "FAIL: 검사기 또는 워크플로가 없다 (fail-closed)"; echo "CHECKED: 0"; exit 2
fi

SNAPSHOT=$(git status --porcelain)
TMP=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'ruby -rfileutils -e "FileUtils.remove_entry(ARGV[0]) if File.exist?(ARGV[0])" "$TMP"' EXIT

fail=0
checked=0
record() {
  local ok="$1" desc="$2" detail="$3"
  checked=$((checked + 1))
  if [ "$ok" -eq 0 ]; then printf 'PASS: %s — %s\n' "$desc" "$detail"
  else printf 'FAIL: %s — %s\n' "$desc" "$detail"; fail=1; fi
}

expect_rc() {
  local desc="$1" path="$2" wanted="$3" rc=0
  bash "$CHECKER" "$path" >/dev/null 2>&1 || rc=$?
  if [ "$rc" -eq "$wanted" ]; then record 0 "$desc" "exit=$rc"
  else record 1 "$desc" "expected exit=$wanted actual=$rc"; fi
}

expect_trigger_contract() {
  local desc="$1" path="$2" wanted="$3" marker="$4" checked_pattern="$5" rc=0 out
  out=$(bash "$CHECKER" "$path" 2>&1) || rc=$?
  if [ "$rc" -eq "$wanted" ] && printf '%s\n' "$out" | grep -q "$marker" \
      && printf '%s\n' "$out" | grep -Eq "$checked_pattern"; then
    record 0 "$desc" "exit=$rc, 출력 계약 일치"
  else
    record 1 "$desc" "expected exit=$wanted/$marker/$checked_pattern actual exit=$rc"
  fi
}

expect_structure() {
  expect_trigger_contract "$1" "$2" 2 '^FAIL:' '^CHECKED: 0$'
}

trigger_variant() {
  local name="$1" trigger="$2" path
  path="$TMP/$name.yml"
  cp "$WF" "$path"
  ruby -e '
    path, replacement = ARGV
    source = File.read(path)
    first = source.index("\non:\n")
    last = first && source.index("\npermissions:", first + 1)
    abort "trigger block not found" unless first && last
    source[(first + 1)...last] = replacement
    File.write(path, source)
  ' "$path" "$trigger"
  printf '%s' "$path"
}

# ── 통과 쪽: 손대지 않은 실제 워크플로 ───────────────────────────────────────
expect_rc "실제 워크플로 → 통과" "$WF" 0

# ── 통과 쪽: trigger 의미 동등 표현을 과잉 차단하지 않는다 ────────────────
p=$(trigger_variant trigger-quoted '"on":
  push: {}
  pull_request: {}
  workflow_dispatch:
    inputs:
      reason:
        required: false
  schedule:
    - cron: "17 3 * * 1"')
expect_trigger_contract "quoted on·빈 mapping·dispatch inputs·추가 event → 통과" "$p" 0 \
  '^PASS: TRIGGER_CONTRACT:' '^CHECKED: [1-9][0-9]*$'

p=$(trigger_variant trigger-null 'on:
  push:
  pull_request:
  workflow_dispatch:')
expect_trigger_contract "필수 event null mapping → 통과" "$p" 0 \
  '^PASS: TRIGGER_CONTRACT:' '^CHECKED: [1-9][0-9]*$'

p=$(trigger_variant trigger-sequence 'on: [push, pull_request, workflow_dispatch]')
expect_trigger_contract "필수 event sequence shorthand → 통과" "$p" 0 \
  '^PASS: TRIGGER_CONTRACT:' '^CHECKED: [1-9][0-9]*$'

# ── 차단 쪽: 워크플로 자체가 실행되지 않는 trigger 축소 ──────────────────
p=$(trigger_variant trigger-no-push 'on:
  pull_request:
  workflow_dispatch:')
expect_trigger_contract "push 삭제 → 계약 위반" "$p" 1 \
  '^FAIL: TRIGGER_CONTRACT:.*push' '^CHECKED: [1-9][0-9]*$'

p=$(trigger_variant trigger-no-pr 'on:
  push:
  workflow_dispatch:')
expect_trigger_contract "pull_request 삭제 → 계약 위반" "$p" 1 \
  '^FAIL: TRIGGER_CONTRACT:.*pull_request' '^CHECKED: [1-9][0-9]*$'

p=$(trigger_variant trigger-no-dispatch 'on:
  push:
  pull_request:')
expect_trigger_contract "workflow_dispatch 삭제 → 계약 위반" "$p" 1 \
  '^FAIL: TRIGGER_CONTRACT:.*workflow_dispatch' '^CHECKED: [1-9][0-9]*$'

for key in branches branches-ignore paths paths-ignore tags; do
  p=$(trigger_variant "push-$key" "on:
  push:
    $key: [main]
  pull_request:
  workflow_dispatch:")
  expect_trigger_contract "push.$key 축소 → 계약 위반" "$p" 1 \
    '^FAIL: TRIGGER_CONTRACT:.*push' '^CHECKED: [1-9][0-9]*$'
done

for key in branches branches-ignore paths paths-ignore types; do
  p=$(trigger_variant "pr-$key" "on:
  push:
  pull_request:
    $key: [main]
  workflow_dispatch:")
  expect_trigger_contract "pull_request.$key 축소 → 계약 위반" "$p" 1 \
    '^FAIL: TRIGGER_CONTRACT:.*pull_request' '^CHECKED: [1-9][0-9]*$'
done

p=$(trigger_variant trigger-sequence-missing 'on: [push, pull_request]')
expect_trigger_contract "sequence shorthand 필수 event 누락 → 계약 위반" "$p" 1 \
  '^FAIL: TRIGGER_CONTRACT:.*workflow_dispatch' '^CHECKED: [1-9][0-9]*$'

# ── 데이터 오류: YAML 덮어쓰기·비정상 구조를 fail-closed 한다 ─────────────
p=$(trigger_variant trigger-none 'x-trigger: ignored')
expect_trigger_contract "top-level on 없음 → 구조 오류" "$p" 2 \
  '^FAIL:' '^CHECKED: 0$'

p=$(trigger_variant trigger-top-list '- push
- pull_request
- workflow_dispatch')
expect_trigger_contract "top-level list → 구조 오류" "$p" 2 \
  '^FAIL:' '^CHECKED: 0$'

p=$(trigger_variant trigger-duplicate-on 'on: [push, pull_request, workflow_dispatch]
on: [push, pull_request, workflow_dispatch]')
expect_trigger_contract "duplicate plain on → 구조 오류" "$p" 2 \
  '^FAIL:' '^CHECKED: 0$'

p=$(trigger_variant trigger-duplicate-quoted '"on": [push, pull_request, workflow_dispatch]
"on": [push, pull_request, workflow_dispatch]')
expect_trigger_contract "duplicate quoted on → 구조 오류" "$p" 2 \
  '^FAIL:' '^CHECKED: 0$'

p=$(trigger_variant trigger-mixed-on 'on: [push, pull_request, workflow_dispatch]
"on": [push, pull_request, workflow_dispatch]')
expect_trigger_contract "plain/quoted on 중복 → 구조 오류" "$p" 2 \
  '^FAIL:' '^CHECKED: 0$'

p=$(trigger_variant trigger-duplicate-event 'on:
  push:
  push: {}
  pull_request:
  workflow_dispatch:')
expect_trigger_contract "duplicate event key → 구조 오류" "$p" 2 \
  '^FAIL:' '^CHECKED: 0$'

# ── V1/V2 반례: AST와 값 계층이 다른 trigger를 고르지 못하게 한다 ─────────
p=$(trigger_variant trigger-true-before-on 'true: {push: null, pull_request: null, workflow_dispatch: null}
"on": {push: {paths-ignore: ["**"]}, pull_request: null, workflow_dispatch: null}')
expect_structure "literal true 뒤 축소 on → 구조 오류" "$p"
p=$(trigger_variant trigger-on-before-true 'on: {push: {paths-ignore: ["**"]}, pull_request: null, workflow_dispatch: null}
true: {push: null, pull_request: null, workflow_dispatch: null}')
expect_structure "축소 on 뒤 literal true → 구조 오류" "$p"
p=$(trigger_variant trigger-On-before-on 'On: {push: null, pull_request: null, workflow_dispatch: null}
"on": {push: {paths-ignore: ["**"]}, pull_request: null, workflow_dispatch: null}')
expect_structure "case-changed On과 on 충돌 → 구조 오류" "$p"
p=$(trigger_variant trigger-merge 'x-events: &events {push: null, pull_request: null}
on: {<<: *events, workflow_dispatch: null}')
expect_structure "on merge key → 구조 오류" "$p"
p=$(trigger_variant trigger-numeric-key 'on: {push: null, pull_request: null, workflow_dispatch: null, 7: null}')
expect_structure "비문자 event key → 구조 오류" "$p"
p=$(trigger_variant trigger-numeric-sequence 'on: [push, pull_request, workflow_dispatch, 7]')
expect_structure "비문자 sequence event → 구조 오류" "$p"
p=$(trigger_variant push-star-plus-path 'on: {push: {branches: ["**"], paths-ignore: ["**"]}, pull_request: null, workflow_dispatch: null}')
expect_trigger_contract "전체 branch와 path 제외 조합 → 계약 위반" "$p" 1 '^FAIL: TRIGGER_CONTRACT:.*push' '^CHECKED: [1-9][0-9]*$'
p=$(trigger_variant dispatch-sequence 'on: {push: null, pull_request: null, workflow_dispatch: []}')
expect_trigger_contract "workflow_dispatch sequence 값 → 계약 위반" "$p" 1 '^FAIL: TRIGGER_CONTRACT:.*workflow_dispatch' '^CHECKED: [1-9][0-9]*$'

for key in yes Yes YES no No NO true True TRUE false False FALSE On ON off Off OFF; do
  p=$(trigger_variant "boolean-$key-before" "$key: {push: null, pull_request: null, workflow_dispatch: null}
\"on\": {push: null, pull_request: null, workflow_dispatch: null}")
  expect_structure "YAML boolean $key 뒤 quoted on 충돌 → 구조 오류" "$p"
  p=$(trigger_variant "boolean-$key-after" "\"on\": {push: null, pull_request: null, workflow_dispatch: null}
$key: {push: null, pull_request: null, workflow_dispatch: null}")
  expect_structure "quoted on 뒤 YAML boolean $key 충돌 → 구조 오류" "$p"
done

p=$(trigger_variant duplicate-push-branches 'on:
  push:
    branches: [main]
    branches: ["**"]
  pull_request:
  workflow_dispatch:')
expect_structure "push.branches 축소를 뒤 정상 값으로 은닉 → 구조 오류" "$p"
p=$(trigger_variant duplicate-dispatch-input 'on:
  push:
  pull_request:
  workflow_dispatch:
    inputs:
      reason: {required: true}
      reason: {required: false}')
expect_structure "workflow_dispatch.inputs 중복 → 구조 오류" "$p"
p=$(trigger_variant trigger-scalar 'on: push')
expect_trigger_contract "scalar on은 누락 event 계약 위반" "$p" 1 '^FAIL: TRIGGER_CONTRACT:.*pull_request' '^CHECKED: [1-9][0-9]*$'
p="$TMP/trigger-bom.yml"; { printf '\357\273\277'; cat "$WF"; } > "$p"
expect_trigger_contract "UTF-8 BOM 정상 workflow → 통과" "$p" 0 '^PASS: TRIGGER_CONTRACT:' '^CHECKED: [1-9][0-9]*$'

# ── 차단 쪽: 무력화 주입 ─────────────────────────────────────────────────────
mutate() {
  local name="$1" ruby_code="$2"
  local path="$TMP/$name.yml"
  cp "$WF" "$path"
  ruby -e "$ruby_code" "$path"
  printf '%s' "$path"
}

p=$(mutate duplicate-jobs 'p=ARGV[0]; s=File.read(p).sub(/^jobs:/, "jobs:\n  decoy: {runs-on: ubuntu-latest, steps: [{run: true}]}\njobs:"); File.write(p,s)')
expect_structure "duplicate top-level jobs → 구조 오류" "$p"
p=$(mutate duplicate-job-id 'p=ARGV[0]; s=File.read(p).sub("jobs:\n  verify:", "jobs:\n  verify: {runs-on: ubuntu-latest, steps: [{run: true}]}\n  verify:"); File.write(p,s)')
expect_structure "duplicate job id → 구조 오류" "$p"
p=$(mutate duplicate-step-key 'p=ARGV[0]; s=File.read(p).sub("        uses: actions/checkout@v4", "        uses: actions/checkout@v3\n        uses: actions/checkout@v4"); File.write(p,s)')
expect_structure "duplicate step key → 구조 오류" "$p"
p=$(mutate duplicate-run 'p=ARGV[0]; s=File.read(p).sub("        run: bash verify.sh", "        run: echo skipped\n        run: bash verify.sh"); File.write(p,s)')
expect_structure "duplicate step run → 구조 오류" "$p"
p=$(mutate nonmapping-job 'p=ARGV[0]; s=File.read(p).sub(/^jobs:\n.*\z/m, "jobs:\n  verify: true\n"); File.write(p,s)')
expect_structure "non-mapping job → 구조 오류" "$p"
p=$(mutate nonmapping-step 'p=ARGV[0]; s=File.read(p).sub("    steps:\n", "    steps:\n      - true\n"); File.write(p,s)')
expect_structure "non-mapping step → 구조 오류" "$p"
p=$(mutate unreadable '')
chmod 000 "$p"
expect_structure "읽기 권한 없는 workflow → 구조 오류" "$p"
chmod 600 "$p"

p=$(mutate step-if-false 'p=ARGV[0]; s=File.read(p).sub("      - name: 인수 검사 hs-a4", "      - name: 인수 검사 hs-a4\n        if: ${{ false }}"); File.write(p,s)')
expect_rc "스텝에 if: \${{ false }} 주입 → 불합격" "$p" 1

p=$(mutate step-if-never 'p=ARGV[0]; s=File.read(p).sub("      - name: 인수 검사 hs-a4", "      - name: 인수 검사 hs-a4\n        if: github.event_name == \x27never\x27"); File.write(p,s)')
expect_rc "스텝에 항상-거짓 조건 주입 → 불합격" "$p" 1

p=$(mutate step-if-always 'p=ARGV[0]; s=File.read(p).sub("      - name: 인수 검사 hs-a4", "      - name: 인수 검사 hs-a4\n        if:" + " always()"); File.write(p,s)')
expect_rc "스텝에 항상-참 조건(always) 주입 → 불합격" "$p" 1

p=$(mutate step-continue 'p=ARGV[0]; s=File.read(p).sub("      - name: 인수 검사 hs-a4", "      - name: 인수 검사 hs-a4\n        continue-on-error:" + " true"); File.write(p,s)')
expect_rc "스텝에 continue-on-error 주입 → 불합격" "$p" 1

p=$(mutate job-if 'p=ARGV[0]; s=File.read(p).sub("    runs-on: ubuntu-latest", "    if: ${{ false }}\n    runs-on: ubuntu-latest"); File.write(p,s)')
expect_rc "job 에 if 주입 → 불합격" "$p" 1

p=$(mutate echo-only 'p=ARGV[0]; s=File.read(p).sub("        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh", "        run: echo bash scripts/acceptance-hs-a4.sh"); File.write(p,s)')
expect_rc "실행 대신 echo → 불합격" "$p" 1

p=$(mutate syntax-only 'p=ARGV[0]; s=File.read(p).sub("        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh", "        run: bash -n scripts/acceptance-hs-a4.sh"); File.write(p,s)')
expect_rc "실행 대신 bash -n → 불합격" "$p" 1

p=$(mutate empty-steps 'p=ARGV[0]; s=File.read(p).sub(/^    steps:\n.*\z/m, "    steps: []\n"); File.write(p,s)')
expect_rc "job 의 스텝 전량 삭제 → 불합격" "$p" 1

# ── fail-closed: 읽지 못하는 상황을 통과로 세지 않는다 ───────────────────────
expect_rc "워크플로 파일 없음 → NOT_RUN" "$TMP/does-not-exist.yml" 2

printf 'jobs: [broken\n' > "$TMP/broken.yml"
expect_rc "파싱 불가 워크플로 → NOT_RUN" "$TMP/broken.yml" 2

printf 'name: x\njobs: {}\n' > "$TMP/nojobs.yml"
expect_rc "job 0개 → NOT_RUN" "$TMP/nojobs.yml" 2

# ── 예외 목록이 살아 있는가(과잉 차단 방지) ─────────────────────────────────
if bash "$CHECKER" "$WF" 2>&1 | grep -q '^ALLOWED: 인수 검사 0-5'; then
  record 0 "이유가 적힌 예외는 통과" "0-5 의 main 전용 조건"
else
  record 1 "이유가 적힌 예외는 통과" "ALLOWED 출력 없음 — 예외 목록이 죽었다"
fi

current=$(git status --porcelain)
if [ "$current" = "$SNAPSHOT" ]; then record 0 "원본 저장소 상태 불변" "before/after 동일"
else record 1 "원본 저장소 상태 불변" "변경 발생"; fi

printf 'CHECKED: %d\n' "$checked"
if [ "$fail" -eq 0 ]; then echo "VERDICT: PASS"; else echo "VERDICT: FAIL"; fi
exit "$fail"
