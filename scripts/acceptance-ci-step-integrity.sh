#!/usr/bin/env bash
# acceptance-ci-step-integrity.sh — 워크플로 스텝을 끄면 반드시 빨개지는가.
#
# scripts/verify/check-ci-step-integrity.sh 를 격리 사본으로 공격한다.
# 차단 — 조건부·오류무시·빈 job·출력만 하는 스텝 8종을 주입하면 전부 불합격
# 통과 — 손대지 않은 실제 워크플로와 이유가 적힌 예외는 그대로 합격
#
# verify.yml과 audit.yml 둘 다 대상으로 삼는다. 2026-09-07 V1 적대검증(audit-workflow
# PR #68)에서 이 검사가 verify.yml만 봐서 audit.yml에 continue-on-error 같은 걸
# 몰래 넣어도 아무 자동 검사도 못 잡는다는 반례가 나왔다 — 그 반례를 여기 편입한다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || exit 2
CHECKER="$REPO/scripts/verify/check-ci-step-integrity.sh"
if [ ! -f "$CHECKER" ]; then
  echo "FAIL: 검사기가 없다 (fail-closed)"; echo "CHECKED: 0"; exit 2
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

# label: 로그 접두어 / wf: 워크플로 경로 / job: jobs.<key> / anchor: 존재하는 "- name:" 줄
# run_line: 존재하는 "run:" 줄(echo/bash -n 치환 대상)
run_battery() {
  local label="$1" wf="$2" job="$3" anchor="$4" run_line="$5"

  if [ ! -f "$wf" ]; then
    checked=$((checked + 1))
    echo "FAIL: [$label] 워크플로가 없다 (fail-closed) — $wf"; fail=1
    return
  fi

  expect_rc "[$label] 실제 워크플로 → 통과" "$wf" 0

  local p
  p="$TMP/${label}-step-if-false.yml"
  cp "$wf" "$p"; ruby -e 'p=ARGV[0]; a=ARGV[1]; s=File.read(p).sub(a, a+"\n        if: ${{ false }}"); File.write(p,s)' "$p" "$anchor"
  expect_rc "[$label] 스텝에 if: \${{ false }} 주입 → 불합격" "$p" 1

  p="$TMP/${label}-step-if-never.yml"
  cp "$wf" "$p"; ruby -e 'p=ARGV[0]; a=ARGV[1]; s=File.read(p).sub(a, a+"\n        if: github.event_name == \x27never\x27"); File.write(p,s)' "$p" "$anchor"
  expect_rc "[$label] 스텝에 항상-거짓 조건 주입 → 불합격" "$p" 1

  p="$TMP/${label}-step-if-always.yml"
  cp "$wf" "$p"; ruby -e 'p=ARGV[0]; a=ARGV[1]; s=File.read(p).sub(a, a+"\n        if:" + " always()"); File.write(p,s)' "$p" "$anchor"
  expect_rc "[$label] 스텝에 항상-참 조건(always) 주입 → 불합격" "$p" 1

  p="$TMP/${label}-step-continue.yml"
  cp "$wf" "$p"; ruby -e 'p=ARGV[0]; a=ARGV[1]; s=File.read(p).sub(a, a+"\n        continue-on-error:" + " true"); File.write(p,s)' "$p" "$anchor"
  expect_rc "[$label] 스텝에 continue-on-error 주입 → 불합격" "$p" 1

  p="$TMP/${label}-job-if.yml"
  cp "$wf" "$p"; ruby -e 'p=ARGV[0]; s=File.read(p).sub("    runs-on: ubuntu-latest", "    if: ${{ false }}\n    runs-on: ubuntu-latest"); File.write(p,s)' "$p"
  expect_rc "[$label] job 에 if 주입 → 불합격" "$p" 1

  p="$TMP/${label}-echo-only.yml"
  cp "$wf" "$p"; ruby -e 'p=ARGV[0]; r=ARGV[1]; body=r.sub(/^ *run: */,""); s=File.read(p).sub(r, "        run: echo " + body); File.write(p,s)' "$p" "$run_line"
  expect_rc "[$label] 실행 대신 echo → 불합격" "$p" 1

  p="$TMP/${label}-syntax-only.yml"
  cp "$wf" "$p"; ruby -e 'p=ARGV[0]; r=ARGV[1]; body=r.sub(/^ *run: */,""); s=File.read(p).sub(r, "        run: bash -n " + body.sub(/^bash /,"")); File.write(p,s)' "$p" "$run_line"
  expect_rc "[$label] 실행 대신 bash -n → 불합격" "$p" 1

  p="$TMP/${label}-empty-steps.yml"
  cp "$wf" "$p"; ruby -e 'p=ARGV[0]; job=ARGV[1]; require "psych"; d=Psych.safe_load(File.read(p), aliases: true); d["jobs"][job]["steps"]=[]; File.write(p,Psych.dump(d))' "$p" "$job"
  expect_rc "[$label] job 의 스텝 전량 삭제 → 불합격" "$p" 1
}

run_battery "verify" "$REPO/.github/workflows/verify.yml" "verify" \
  "      - name: 인수 검사 hs-a4" \
  "        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-a4.sh"

run_battery "audit" "$REPO/.github/workflows/audit.yml" "audit" \
  "      - name: 서드파티 액션 SHA 고정 드리프트 검사" \
  "        run: bash scripts/check-action-sha-drift.sh"

# ── fail-closed: 읽지 못하는 상황을 통과로 세지 않는다 (검사기 1벌로 충분) ───
expect_rc "워크플로 파일 없음 → NOT_RUN" "$TMP/does-not-exist.yml" 2

printf 'jobs: [broken\n' > "$TMP/broken.yml"
expect_rc "파싱 불가 워크플로 → NOT_RUN" "$TMP/broken.yml" 2

printf 'name: x\njobs: {}\n' > "$TMP/nojobs.yml"
expect_rc "job 0개 → NOT_RUN" "$TMP/nojobs.yml" 2

# ── 예외 목록이 살아 있는가(과잉 차단 방지, verify.yml 전용 — 0-5 조건 예외) ──
if bash "$CHECKER" "$REPO/.github/workflows/verify.yml" 2>&1 | grep -q '^ALLOWED: 인수 검사 0-5'; then
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
