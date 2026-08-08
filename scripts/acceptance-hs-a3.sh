#!/usr/bin/env bash
# acceptance-hs-a3.sh — 세션 계열 자격증명이 비밀 스캔에 실제로 잡히는가 (AC-A3)
#
# 계약: docs/engineering/humansearch-v6-implementation-plan-2026-08-08.md §6 Phase A / AC-A3
#   EARS : If 세션 계열 자격증명이 추적 파일에 있으면, then 스캔이 실패해야 한다
#   출력 : exit 0 = PASS | exit 1 = FAIL | exit 2 = NOT_RUN
#   stdout: 항목마다 PASS:/FAIL:/NOT_RUN: 을 전부 출력하고, 마지막 줄에 `CHECKED: <검사 수>`
#   불변식: 0건 검사는 통과가 아니다 (P20)
#
# 개정 이력:
#   2026-08-08 초판 — 세션 키 7종을 "키: 값" 한 줄 형태로만 검사했다.
#   2026-08-09 개정 — **초판 테스트가 구현의 모양을 그대로 베낀 tautology 였다**(P5 위반).
#     내가 상상한 형식만 검사했고, CDP Network.getAllCookies / Playwright storageState 가
#     실제로 뱉는 직렬화(쿠키 이름이 값 자리에 오는 형태)는 한 건도 검사하지 않았다.
#     보안 재검증에서 그 형식 31종이 통과하는 것이 실측됐다. v6 는 CDP 경유가 전제이므로
#     그것이 **실제 산출 형식**이다. 아래 must_catch 는 그 실형식들로 다시 짰다.
#     동시에 오탐 대조군을 4개 추가했다 — 진짜를 놓치고 더미를 막으면 훅 우회 습관이 생긴다.
#
# 자기 매칭 방지: 카나리 문자열을 이 파일에 리터럴로 두면 스캐너가 이 스크립트를 잡는다.
#   조각으로 나눠 런타임에 합친다(scripts/acceptance-0-5.sh 의 카나리 조립과 같은 이유).
#   ※ 파일명 자기 면제는 쓰지 않는다(scripts/acceptance-0-6.sh:17 — E1 사고 재현 금지).
#   실제 비밀값을 쓰지 않는다. 값은 더미이며 어떤 파일로도 기록하지 않는다.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO"

PATTERNS=.secret-patterns.default
if [ ! -f "$PATTERNS" ] || [ ! -s "$PATTERNS" ]; then
  echo "NOT_RUN: $PATTERNS 없음/빈 파일 — 스캔 기준을 읽을 수 없다"
  echo "CHECKED: 0"
  exit 2
fi

# verify.sh 와 같은 정제 절차. 판정기가 두 벌이 되지 않게 같은 규칙을 쓴다.
CLEAN=$(mktemp) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -f "$CLEAN"' EXIT
tr -d '\r' < "$PATTERNS" | grep -vE '^[[:space:]]*(#|$)' > "$CLEAN"
if [ ! -s "$CLEAN" ]; then
  echo "NOT_RUN: 유효 패턴 0개 — 검사가 성립하지 않는다"
  echo "CHECKED: 0"
  exit 2
fi

fail=0
checked=0

# ── 카나리 조각 결합 (리터럴로 남기지 않는다) ────────────────────────────────
K_LI=$(printf 'li%s' '_at')
K_LIRM=$(printf 'li%s' '_rm')
K_JS=$(printf 'JSESSION%s' 'ID')
NAMEF=$(printf 'na%s' 'me')
H_SETCOOKIE=$(printf 'Set-%s' 'Cookie')
H_COOKIE=$(printf 'Coo%s' 'kie')
H_AUTH=$(printf 'Authoriz%s' 'ation')
JWT_HEAD=$(printf 'ey%s' 'J')
JWTSEG=$(printf 'a%.0s' 1 2 3 4 5 6 7 8 9 10 11 12)
# LinkedIn li_at 값 접두 + 40자 (실제 값 아님, 모양만)
VAL=$(printf 'AQ%s%s' 'ED' 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd')
AJAXV=$(printf 'aja%s:%s' 'x' '1234567890123456')
WSURL=$(printf 'ws://127.0.0.1:9338/dev%s/browser/ab-12' 'tools')

must_catch() {
  local desc="$1" line="$2" rc=0
  checked=$((checked + 1))
  printf '%s\n' "$line" | grep -qEif "$CLEAN"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    printf 'PASS: 탐지됨 — %s\n' "$desc"
  elif [ "$rc" -eq 1 ]; then
    printf 'FAIL: 통과됨(놓침) — %s\n' "$desc"
    fail=1
  else
    printf 'FAIL: 검사 실행 오류(grep exit=%s) — %s\n' "$rc" "$desc"
    fail=1
  fi
}

must_not_catch() {
  local desc="$1" line="$2" rc=0
  checked=$((checked + 1))
  printf '%s\n' "$line" | grep -qEif "$CLEAN"
  rc=$?
  if [ "$rc" -eq 1 ]; then
    printf 'PASS: 오탐 없음 — %s\n' "$desc"
  elif [ "$rc" -eq 0 ]; then
    printf 'FAIL: 오탐 — %s (평범한 코드가 막히면 훅 우회 습관이 생긴다)\n' "$desc"
    fail=1
  else
    printf 'FAIL: 검사 실행 오류(grep exit=%s) — %s\n' "$rc" "$desc"
    fail=1
  fi
}

# ── ① 실제 산출 형식 (CDP · Playwright) — 초판이 한 건도 검사하지 않은 것 ──────
must_catch "CDP getAllCookies 직렬화"   "{\"${NAMEF}\":\"${K_LI}\",\"value\":\"${VAL}\"}"
must_catch "Playwright storageState"    "  {\"${NAMEF}\": \"${K_LI}\", \"value\": \"${VAL}\", \"domain\": \".x.com\"}"
must_catch "CDP 디버거 WebSocket URL"   "  \"webSocketDebuggerUrl\": \"${WSURL}\""
# 값 모양을 알아볼 수 없는 CDP 직렬화. 값-모양 패턴이 못 잡으므로 **값-자리 패턴만이**
# 이것을 잡는다 — 그 패턴을 지우면 이 항목만 빨개진다(뮤테이션 격리용).
must_catch "CDP 직렬화(값 모양 미상)"   "{\"${NAMEF}\":\"${K_LI}\",\"value\":\"Zm9vYmFyYmF6cXV4\"}"

# ── ② 값 '모양' — 키 이름을 바꿔도 값은 못 바꾼다 ─────────────────────────────
must_catch "값 모양만(키 이름 변조)"     "  \"opaque_field\": \"${VAL}\""
must_catch "세션 값 모양(ajax 형식)"     "  \"whatever\": \"${AJAXV}\""

# ── ③ 키 = 값 형태 (초판이 검사하던 것 — 회귀 방지로 유지) ───────────────────
must_catch "세션 쿠키 키(따옴표 값)"     "  \"${K_LIRM}\": \"${VAL}\""
must_catch "세션 쿠키 키(무따옴표 YAML)" "${K_LI}: ${VAL}"
must_catch "세션 쿠키 키(.env 형태)"     "${K_JS}=${AJAXV}"
must_catch "${H_SETCOOKIE} 응답 헤더"    "${H_SETCOOKIE}: ${K_LI}=${VAL}; Path=/; HttpOnly"
must_catch "${H_COOKIE} 요청 헤더"       "  \"${H_COOKIE}\": \"${K_LI}=${VAL}\""
must_catch "Bearer 인증 헤더"            "  \"${H_AUTH}\": \"Bearer ${JWT_HEAD}${JWTSEG}.${JWT_HEAD}${JWTSEG}.${JWTSEG}\""

# ── ④ 오탐 대조군 — 평범한 코드·문서는 막히면 안 된다 ────────────────────────
must_not_catch "빌드 경로 값"        "  \"$(printf 'p%s' 'wd')\": \"/Users/runner/work/repo\""
must_not_catch "상태 상수"           "  '$(printf 'P%s' 'W')': 'PENDING_WRITE'"
must_not_catch "헤더 '이름' 설정"    "  \"sessionIdHeader\": \"x-request-session\""
must_not_catch "i18n 안내 문구"      "  \"$(printf 'p%s' 'w')\": \"비밀번호를 입력하세요\""
must_not_catch "산문 속 키 이름 언급" "비밀 스캔이 ${K_LI} 와 ${H_COOKIE} 를 놓친다고 실측했다"

if [ "$checked" -eq 0 ]; then
  echo "FAIL: 검사 항목 0개 — 0건 처리로 통과는 금지한다 (P20)"
  echo "CHECKED: 0"
  exit 1
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
