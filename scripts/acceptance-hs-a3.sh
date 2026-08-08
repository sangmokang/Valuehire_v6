#!/usr/bin/env bash
# acceptance-hs-a3.sh — 세션 계열 자격증명이 비밀 스캔에 실제로 잡히는가 (AC-A3)
#
# 계약: docs/engineering/humansearch-v6-implementation-plan-2026-08-08.md §6 Phase A / AC-A3
#   EARS : If 세션 계열 자격증명 패턴이 추적 파일에 있으면, then 스캔이 실패해야 한다
#   출력 : exit 0 = PASS | exit 1 = FAIL | exit 2 = NOT_RUN
#   stdout: 항목마다 PASS:/FAIL:/NOT_RUN: 을 전부 출력하고, 마지막 줄에 `CHECKED: <검사 수>`
#   불변식: 0건 검사는 통과가 아니다 (P20). CHECKED 가 0이면 스스로 FAIL 한다
#
# 왜 이 검사가 필요한가 (2026-08-08 실측):
#   `.secret-patterns.default` 는 키 이름에 PASSWORD|SECRET|TOKEN|APIKEY|ACCESS_KEY 가
#   있어야 매칭한다. 그래서 li_at · JSESSIONID · Set-Cookie · Authorization: Bearer ·
#   JWT · pw 가 **전부 통과**했다. LinkedIn Recruiter 의 세션 쿠키 하나면 2FA 를 이미
#   통과한 상태의 자격증명이라 비밀번호보다 강하다. 구현 계획은 receipts/*.json 을
#   커밋 대상으로 규정하므로, 이 구멍이 열린 채로 Phase 1 에 들어가면 안 된다.
#
# 자기 매칭 방지 (scripts/acceptance-0-5.sh 의 "카나리는 조립해서 만든다"와 같은 이유):
#   카나리 키 이름을 이 파일에 리터럴로 두면 스캐너가 이 스크립트 자신을 잡아
#   verify.sh 가 상시 FAIL 한다. 그래서 키 이름을 조각으로 나눠 런타임에 합친다.
#   ※ 파일명 자기 면제는 쓰지 않는다 (scripts/acceptance-0-6.sh:17 — E1 사고 재현 금지).
#
# 실제 비밀값을 쓰지 않는다: 값은 전부 'A' 반복이며 어떤 파일로도 기록하지 않는다.
set -uo pipefail

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO"

PATTERNS=.secret-patterns.default
if [ ! -f "$PATTERNS" ] || [ ! -s "$PATTERNS" ]; then
  echo "NOT_RUN: $PATTERNS 없음/빈 파일 — 스캔 기준을 읽을 수 없다"
  echo "CHECKED: 0"
  exit 2
fi

# verify.sh 와 같은 정제 절차(CRLF 제거 + 주석/빈 줄 제거). 판정기가 두 벌이 되지 않게 같은 규칙을 쓴다.
CLEAN=$(mktemp)
trap 'rm -f "$CLEAN"' EXIT
tr -d '\r' < "$PATTERNS" | grep -vE '^[[:space:]]*(#|$)' > "$CLEAN"
if [ ! -s "$CLEAN" ]; then
  echo "NOT_RUN: 유효 패턴 0개 — 검사가 성립하지 않는다"
  echo "CHECKED: 0"
  exit 2
fi

fail=0
checked=0

# 값 24자. 실제 비밀이 아니라 '모양'만 맞춘 더미다.
VAL=$(printf 'A%.0s' 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24)
JWTSEG=$(printf 'a%.0s' 1 2 3 4 5 6 7 8 9 10 11 12)

# 키 이름은 조각 결합으로 만든다 (이 파일에 리터럴로 남기지 않는다).
K_LI=$(printf 'li%s' '_at')
K_JS=$(printf 'JSESSION%s' 'ID')
K_SID=$(printf 'session%s' '_id')
K_PW=$(printf 'p%s' 'w')
H_SETCOOKIE=$(printf 'Set-%s' 'Cookie')
H_COOKIE=$(printf 'Coo%s' 'kie')
H_AUTH=$(printf 'Authoriz%s' 'ation')
JWT_HEAD=$(printf 'ey%s' 'J')

# must_catch <설명> <검사할 한 줄>
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

# must_not_catch <설명> <검사할 한 줄>  — 오탐 방지. 키 '이름'만 언급한 산문은 잡히면 안 된다.
must_not_catch() {
  local desc="$1" line="$2" rc=0
  checked=$((checked + 1))
  printf '%s\n' "$line" | grep -qEif "$CLEAN"
  rc=$?
  if [ "$rc" -eq 1 ]; then
    printf 'PASS: 오탐 없음 — %s\n' "$desc"
  elif [ "$rc" -eq 0 ]; then
    printf 'FAIL: 오탐 — %s (문서에서 키 이름만 언급해도 스캔이 막힌다)\n' "$desc"
    fail=1
  else
    printf 'FAIL: 검사 실행 오류(grep exit=%s) — %s\n' "$rc" "$desc"
    fail=1
  fi
}

must_catch "LinkedIn 세션 쿠키(JSON)"      "  \"${K_LI}\": \"${VAL}\""
must_catch "세션 ID(.env 형태)"            "${K_JS}=${VAL}"
must_catch "세션 ID(JSON)"                 "  \"${K_SID}\": \"${VAL}\""
must_catch "짧은 비밀번호 키"              "  \"${K_PW}\": \"${VAL}\""
must_catch "${H_SETCOOKIE} 응답 헤더"      "${H_SETCOOKIE}: ${K_LI}=${VAL}; Path=/"
must_catch "${H_COOKIE} 요청 헤더"         "  \"${H_COOKIE}\": \"${K_LI}=${VAL}\""
must_catch "Bearer 인증 헤더"              "  \"${H_AUTH}\": \"Bearer ${JWT_HEAD}${JWTSEG}.${JWT_HEAD}${JWTSEG}.${JWTSEG}\""

# 대조군: 계획 문서가 키 이름을 산문으로 언급하는 형태. 잡히면 문서를 못 쓰게 된다.
must_not_catch "산문 속 키 이름 언급" "비밀 스캔이 ${K_LI} 와 ${H_COOKIE} 를 놓친다고 실측했다"

if [ "$checked" -eq 0 ]; then
  echo "FAIL: 검사 항목 0개 — 0건 처리로 통과는 금지한다 (P20)"
  echo "CHECKED: 0"
  exit 1
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
