#!/usr/bin/env bash
# acceptance-ci-step-integrity.sh — 워크플로 스텝을 끄면 반드시 빨개지는가.
#
# scripts/verify/check-ci-step-integrity.sh 를 격리 사본으로 공격한다.
# 차단 — 조건부·오류무시·빈 job·출력만 하는 스텝 8종을 주입하면 전부 불합격
# 통과 — 손대지 않은 실제 워크플로와 이유가 적힌 예외는 그대로 합격
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

# ── 통과 쪽: 손대지 않은 실제 워크플로 ───────────────────────────────────────
expect_rc "실제 워크플로 → 통과" "$WF" 0

# ── 차단 쪽: 무력화 주입 ─────────────────────────────────────────────────────
mutate() {
  local name="$1" ruby_code="$2"
  local path="$TMP/$name.yml"
  cp "$WF" "$path"
  ruby -e "$ruby_code" "$path"
  printf '%s' "$path"
}

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

p=$(mutate empty-steps 'p=ARGV[0]; require "psych"; d=Psych.safe_load(File.read(p), aliases: true); d["jobs"]["verify"]["steps"]=[]; File.write(p,Psych.dump(d))')
expect_rc "job 의 스텝 전량 삭제 → 불합격" "$p" 1

# 실행 제어도 검사 대상이다. 각 변형은 실제 YAML 사본에 적용한다.
mutate_control() {
  local name="$1" ruby_code="$2"
  mutate "$name" 'require "psych"; p=ARGV[0]; d=Psych.safe_load(File.read(p), aliases: true); '"$ruby_code"'; File.write(p, Psych.dump(d))'
}

p=$(mutate_control no-concurrency 'd.delete("concurrency")')
expect_rc "동시 실행 제어 삭제 → 불합격" "$p" 1
p=$(mutate_control shared-main 'd["concurrency"]["group"]="verify-${{ github.event_name }}-${{ github.ref }}"')
expect_rc "main 대기 실행이 같은 그룹을 공유 → 불합격" "$p" 1
p=$(mutate_control no-event 'd["concurrency"]["group"].sub!("${{ github.event_name }}", "event")')
expect_rc "push/PR 그룹 분리 제거 → 불합격" "$p" 1
p=$(mutate_control no-ref 'd["concurrency"]["group"].sub!("${{ github.ref }}", "ref")')
expect_rc "브랜치 그룹 분리 제거 → 불합격" "$p" 1
p=$(mutate_control cancel-main 'd["concurrency"]["cancel-in-progress"]=true')
expect_rc "main 실행 취소 허용 → 불합격" "$p" 1
p=$(mutate_control keep-feature 'd["concurrency"]["cancel-in-progress"]=false')
expect_rc "작업 브랜치 중복 취소 제거 → 불합격" "$p" 1
p=$(mutate_control max-queue 'd["concurrency"]["queue"]="max"')
expect_rc "조건부 취소와 호환되지 않는 queue 설정 → 불합격" "$p" 1
p=$(mutate_control no-timeout 'd["jobs"]["verify"].delete("timeout-minutes")')
expect_rc "시간 상한 삭제 → 불합격" "$p" 1
p=$(mutate_control long-timeout 'd["jobs"]["verify"]["timeout-minutes"]=360')
expect_rc "시간 상한 6시간으로 회귀 → 불합격" "$p" 1
p=$(mutate_control job-concurrency 'd["jobs"]["verify"]["concurrency"]="shared-main"')
expect_rc "job 수준에서 main 공유 그룹 재도입 → 불합격" "$p" 1

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
