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

require_file "$SOT" "브라우저 SOT"
require_file "$POLICY" "browser-policy 계약"
require_file "$GOAL" "goal"

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
