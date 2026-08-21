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

# ⚠️ git 훅은 GIT_DIR·GIT_INDEX_FILE 등을 자식 프로세스로 export 한다. 그 상태에서는
# 임시 저장소로 `cd` 해도 git 명령이 **실제 저장소**에 붙는다 — 2026-08-09 실측:
# `git push` 중 이 검사가 돌면서 실제 워크트리 인덱스에 테스트 파일 12개가 스테이지되고
# README.md 가 덮어써졌다(push 는 fail-closed 로 막혀 원격에는 안 갔다).
# 검증기가 검증 대상을 오염시키면 그 판정은 무효다. 여기서 상속을 끊는다.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO"

# 자기 오염 감지 — 이 검사가 끝난 뒤 저장소 상태가 시작과 달라지면 판정 자체가 무효다.
SNAP0=$(git status --porcelain)

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
# 선언된 쿠키 이름 7종 중 위 3종만 카나리로 덮여 있었다. 나머지 4종은 패턴에서 지워도
# 검사가 전부 초록이었다(2026-08-12 V1 적대검증 D5 · V2 재현 확인:
# `perl -pi -e 's/\|BCOOKIE\|BSCOOKIE//g'` 후에도 CHECKED: 21 / exit 0).
# 이름별 앵커를 붙여 어느 하나가 사라져도 그 항목만 빨개지게 한다.
K_LIDC=$(printf 'LI%s' 'DC')
K_PHP=$(printf 'PHPSESS%s' 'ID')
K_BC=$(printf 'BCOO%s' 'KIE')
K_BSC=$(printf 'BSCOO%s' 'KIE')
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
must_catch "무따옴표 Cookie 헤더(Copy as cURL)" "curl -H '${H_COOKIE}: sess_x=Zm9vYmFyYmF6cXV4'"
must_catch "Bearer 인증 헤더"            "  \"${H_AUTH}\": \"Bearer ${JWT_HEAD}${JWTSEG}.${JWT_HEAD}${JWTSEG}.${JWTSEG}\""

# ── ③-b 이름별 회귀 앵커 — 선언한 쿠키 이름 하나가 사라지면 그 항목만 빨개진다 ────
#
# 값은 **모양이 없는** 문자열이어야 한다. AQED…·ajax:… 를 쓰면 값-모양 패턴이 대신
# 잡아버려 이름이 지워져도 초록이 남는다(= 이 앵커가 아무것도 앵커하지 못한다).
# 값에 `=` 를 넣어도 안 된다 — Cookie 헤더 패턴이 대신 잡는다. 둘 다 D5 와 같은 실수다.
OPAQUE=Zm9vYmFyYmF6cXV4
must_catch "쿠키 이름 앵커 — ${K_LIDC}"  "  \"${K_LIDC}\": \"${OPAQUE}\""
must_catch "쿠키 이름 앵커 — ${K_PHP}"   "  \"${K_PHP}\": \"${OPAQUE}\""
must_catch "쿠키 이름 앵커 — ${K_BC}"    "  \"${K_BC}\": \"${OPAQUE}\""
must_catch "쿠키 이름 앵커 — ${K_BSC}"   "  \"${K_BSC}\": \"${OPAQUE}\""

# ── ④ 오탐 대조군 — 평범한 코드·문서는 막히면 안 된다 ────────────────────────
must_not_catch "빌드 경로 값"        "  \"$(printf 'p%s' 'wd')\": \"/Users/runner/work/repo\""  # selfcontained-ok: 오탐 대조군용 표본 문자열이며 실제 파일 접근이 아니다
must_not_catch "상태 상수"           "  '$(printf 'P%s' 'W')': 'PENDING_WRITE'"
must_not_catch "헤더 '이름' 설정"    "  \"sessionIdHeader\": \"x-request-session\""
must_not_catch "i18n 안내 문구"      "  \"$(printf 'p%s' 'w')\": \"비밀번호를 입력하세요\""
must_not_catch "산문 속 키 이름 언급" "비밀 스캔이 ${K_LI} 와 ${H_COOKIE} 를 놓친다고 실측했다"

# ── ⑤ 종단: 스캐너가 실제로 이 패턴을 쓰는가 (판정기 2벌 방지) ───────────────
#
# ①~④ 는 "정규식이 맞는가"만 증명한다. verify.sh 가 그 패턴을 실제로 그렇게 쓰는지는
# 별개 문제다 — 예컨대 verify.sh 에서 `grep -i` 하나만 빠지면 신규 패턴이 전부 대문자라
# 실제 소문자 쿠키를 놓치는데, 위 검사는 자기 파이프라인으로 판정하므로 **전부 초록인 채**
# 스캐너만 뚫린다(2026-08-09 품질 재검증 실증). 규칙을 복사하는 것이 곧 판정기 2벌이다
# (hooks/pre-commit:54-61 에 같은 사고가 기록돼 있다). 그래서 verify.sh 를 실제로 태운다.
e2e() {
  local desc="$1" content="$2" want_rc="$3"
  local tmp rc=0
  checked=$((checked + 1))
  tmp=$(mktemp -d) || { printf 'FAIL: 임시 저장소 생성 실패 — %s (fail-closed)\n' "$desc"; fail=1; return; }
  if [ -z "$tmp" ] || [ ! -d "$tmp" ]; then
    printf 'FAIL: 임시 저장소 경로가 비었다 — %s (fail-closed)\n' "$desc"; fail=1; return
  fi
  git init -q "$tmp"
  cp verify.sh "$PATTERNS" "$tmp/"
  (
    cd "$tmp" || exit 9
    printf '%s\n' "$content" > payload.json
    git add payload.json >/dev/null 2>&1
    SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh
  ) >/dev/null 2>&1
  rc=$?
  rm -rf "$tmp"
  if [ "$rc" -eq "$want_rc" ]; then
    printf 'PASS: 스캐너 종단 — %s (verify.sh exit=%s)\n' "$desc" "$rc"
  else
    printf 'FAIL: 스캐너 종단 — %s (기대 exit=%s, 실제 %s)\n' "$desc" "$want_rc" "$rc"
    fail=1
  fi
}

# 카나리는 **소문자 키 + 모양 없는 값**이어야 판별력이 있다.
# 값이 AQED… 처럼 대문자 모양이면 `grep -i` 가 빠져도 대문자 패턴이 그대로 잡아버려
# 이 종단 검사가 -i 손실을 못 잡는다(2026-08-09 실측 — 첫 카나리가 그랬다).
e2e "세션 쿠키 파일을 verify.sh 가 차단" "${K_LI}: Zm9vYmFyYmF6cXV4cXV1eA" 1
e2e "정상 파일은 verify.sh 가 통과"      "{\"position\":\"AX Sales\",\"pages\":20}"        0

if [ "$checked" -eq 0 ]; then
  echo "FAIL: 검사 항목 0개 — 0건 처리로 통과는 금지한다 (P20)"
  echo "CHECKED: 0"
  exit 1
fi

# ⚠️ 이름을 증명 범위에 맞춘다(2026-08-12 V1 적대검증 D3 · V2 재현 확인).
# `git status --porcelain` 은 **추적/미추적 파일 상태만** 본다. git 설정(`git config`),
# 참조(refs), 내부 객체(.git/objects), 과거 기록, 무시된 파일은 보지 못하고, 중간에
# 오염시켰다가 되돌린 사실도 원리상 볼 수 없다. V2 재현: 검사 도중 `git config` 를 바꾸고
# 객체 1개를 저장해도(객체 파일 45→46) 이 비교는 "동일"로 나왔다.
# 따라서 "저장소 무오염"이라 부르면 과장이다 — 실제로 증명한 범위만 이름에 담는다.
SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  checked=$((checked + 1))
  echo "FAIL: 이 검사가 작업트리를 오염시켰다 — 시작/종료 파일 상태가 다르다 (판정 무효)"
  printf '%s\n' "$SNAP1" | sed 's/^/       /'
  fail=1
else
  checked=$((checked + 1))
  echo "PASS: 작업트리 무오염 (git status 기준 — git 설정·내부 객체·참조는 범위 밖)"
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
