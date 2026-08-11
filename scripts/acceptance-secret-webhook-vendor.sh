#!/usr/bin/env bash
# acceptance-secret-webhook-vendor.sh — 웹훅 URL·벤더 API 키가 비밀 스캔에 잡히는가 (AC-S1)
#
# 계약: docs/engineering/secret-webhook-vendor-goal-2026-08-12.md §③ AC-S1
#   EARS : If 추적 파일에 Discord/Slack 웹훅 URL, sk-ant- 형식 벤더 키, 또는
#          WEBHOOK|CREDENTIAL|BOT_TOKEN|PRIVATE_KEY 계열 .env 대입문이 있으면,
#          then 비밀 스캔이 실패해야 한다. 평범한 코드는 막히지 않아야 한다.
#   출력 : exit 0 = PASS | exit 1 = FAIL | exit 2 = NOT_RUN
#   stdout: 항목마다 PASS:/FAIL:/NOT_RUN: 을 전부 출력하고, 마지막 줄에 `CHECKED: <검사 수>`
#   불변식: 0건 검사는 통과가 아니다 (P20)
#
# 왜 필요한가(2026-08-12 실측): 기존 패턴 10개는 "비밀은 이름표가 붙은 값"이라는 전제 위에
#   있다. 웹훅은 비밀이 **URL 경로에** 실려 이름표가 없고, 벤더 키는 접두사에 하이픈이 들어
#   기존 문자 클래스를 만족하지 못한다. 8종 중 7종이 그냥 통과했다.
#
# 자기 매칭 방지: 카나리 문자열을 이 파일에 리터럴로 두면 스캐너가 이 스크립트를 잡는다.
#   조각으로 나눠 런타임에 합친다(scripts/acceptance-hs-a3.sh:59-72 와 같은 이유).
#   ※ 파일명 자기 면제는 쓰지 않는다(scripts/acceptance-0-6.sh:17 — E1 사고 재현 금지).
#   실제 비밀값을 쓰지 않는다. 값은 더미이며 어떤 파일로도 기록하지 않는다.
set -uo pipefail

# ⚠️ git 훅은 GIT_DIR·GIT_INDEX_FILE 등을 자식 프로세스로 export 한다. 그 상태에서는
# 임시 저장소로 `cd` 해도 git 명령이 **실제 저장소**에 붙는다(2026-08-09 실측 사고).
# 검증기가 검증 대상을 오염시키면 그 판정은 무효다. 여기서 상속을 끊는다.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

# 자기 오염 감지 — 이 검사가 끝난 뒤 저장소 상태가 시작과 달라지면 판정 자체가 무효다.
SNAP0=$(git status --porcelain)

PATTERNS=.secret-patterns.default
if [ ! -f "$PATTERNS" ] || [ ! -s "$PATTERNS" ]; then
  echo "NOT_RUN: $PATTERNS 없음/빈 파일 — 스캔 기준을 읽을 수 없다"
  echo "CHECKED: 0"
  exit 2
fi

# verify.sh 와 같은 정제 절차(verify.sh:40). 판정기가 두 벌이 되지 않게 같은 규칙을 쓴다.
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
# ⚠️ 이 저장소가 도는 맥의 기본 bash 는 3.2 다(2026-08-12 실측). `${VAR^^}`·`${VAR,,}` 같은
# 대소문자 변환 확장은 bash 4 문법이라 3.2 에서 `bad substitution` 으로 죽고, 그 줄의 검사가
# **조용히 사라진다**(첫 RED 실행에서 검사 3건이 그렇게 유실됐다 — CHECKED 가 17이 아니라 14였다).
# 그래서 변환은 전부 tr 로 미리 만들어 둔다.
DC=$(printf 'disc%s' 'ord')                       # discord
WH=$(printf 'webh%s' 'ooks')                      # webhooks
SLD=$(printf 'sl%s' 'ack.com')                    # slack.com
SLK="hooks.$SLD"                                  # hooks.slack.com
SVC=$(printf 'ser%s' 'vices')                     # services
SKA=$(printf 'sk-%s-' 'ant')                      # sk-ant-
K_WH=$(printf 'WEBH%s' 'OOK')                     # WEBHOOK
K_CR=$(printf 'CREDEN%s' 'TIAL')                  # CREDENTIAL
K_BT=$(printf 'BOT_T%s' 'OKEN')                   # BOT_TOKEN
K_PK=$(printf 'PRIVATE_%s' 'KEY')                 # PRIVATE_KEY
SNOW=1234567890123456789                          # Discord 스노플레이크(18자리) 모양
TOK=AbCdEfGhIjKlMnOpQrStUvWxYz0123456789          # 36자 더미 토큰 모양
LONGK=AbCdEfGhIjKlMnOpQrStUvWxYz0123456789ABCDEF  # 42자 더미 키 본문
# bash 3.2 호환 대소문자 변환
K_WH_L=$(printf '%s' "$K_WH" | tr 'A-Z' 'a-z')    # webhook
K_WH_C=$(printf 'W%s' "$(printf '%s' "${K_WH#W}" | tr 'A-Z' 'a-z')")  # Webhook
DC_U=$(printf '%s' "$DC" | tr 'a-z' 'A-Z')        # DISCORD
WH_U=$(printf '%s' "$WH" | tr 'a-z' 'A-Z')        # WEBHOOKS
TOK_U=$(printf '%s' "$TOK" | tr 'a-z' 'A-Z')      # 대문자 표기 토큰

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

# ── ① 경로에 비밀이 실린 형태 — 이름표가 없어 기존 패턴이 구조적으로 못 잡는다 ──
must_catch "${DC} 웹훅 URL" \
  "  const url = \"https://${DC}.com/api/${WH}/${SNOW}/${TOK}\";"
must_catch "${DC}app.com 변종(구 도메인)" \
  "https://${DC}app.com/api/${WH}/${SNOW}/${TOK}"
must_catch "Slack 웹훅 URL" \
  "  webhook: 'https://${SLK}/${SVC}/T01ABCDEFGH/B01ABCDEFGH/${TOK}'"

# ── ② 벤더 API 키 — 접두사에 하이픈이 있어 기존 sk-[A-Za-z0-9]{20,} 를 빠져나간다 ──
# ⚠️ 변수 이름을 `api_key` 로 쓰면 안 된다. 기존 패턴(.secret-patterns.default:9)의 키워드
# 목록에 API_KEY 가 있어 **키 형식과 무관하게** 그 이름만으로 잡힌다. 첫 RED 실행에서 이
# 항목이 초록으로 나온 원인이 그것이었다 — 신규 패턴이 아니라 기존 패턴을 시험하고 있었다.
# 판별력을 가지려면 이름이 중립이어야 한다(tautology 회피 · counter-AC 1).
must_catch "Anthropic 벤더 키(하이픈 접두 · 중립 변수명)" \
  "  cfg.value = \"${SKA}api03-${LONGK}\""

# ── ③ .env 대입문 키워드 확장 ────────────────────────────────────────────────
must_catch "${K_WH} 계열 .env 대입" "${K_WH}_URL=https://${DC}.com/api/${WH}/${SNOW}/${TOK}"
must_catch "${K_CR} 계열 .env 대입" "export SERVICE_${K_CR}=${TOK}"
must_catch "${K_PK} 한 줄 형태"     "${K_PK}=MIIEvQIBADANBgkqhkiG9w0BAQEFAASC"
# 회귀 방지 — 이 한 건은 기존 패턴(.secret-patterns.default:11 의 TOKEN)이 **이미** 덮는다.
# 신규 패턴이 없어도 통과하므로 RED 단계에서도 초록이다. 나중에 기존 패턴을 건드렸을 때
# 조용히 사라지는 것을 막기 위한 앵커다(중복이라는 사실을 goal §1-8 에 적었다).
must_catch "${K_BT} (기존 패턴이 이미 덮음 · 회귀 앵커)" "${K_BT}=${TOK}"

# ── ④ 오탐 대조군 — 평범한 코드·문서는 막히면 안 된다 ────────────────────────
# 비밀 스캔에는 억제 경로가 없다. 오탐 1건 = 작업 중단이므로 탐지보다 이쪽이 더 아프다.
must_not_catch "일반 ${DC} 채널 URL(비밀 아님)" \
  "  <a href=\"https://${DC}.com/channels/${SNOW}/987654321\">공지</a>"
must_not_catch "코드 대입(값이 아니라 호출)" \
  "  const ${K_WH_L}Url = get${K_WH_C}Url();"
must_not_catch "환경변수 참조(값이 없다)" \
  "${K_WH}_URL=\${${DC_U}_${K_WH}}"
must_not_catch "산문 속 키 형식 언급" \
  "${SKA} 로 시작하는 키는 기존 sk- 패턴에 안 걸린다고 실측했다"
must_not_catch "일반 Slack 워크스페이스 URL" \
  "  see https://myteam.${SLD}/archives/C01ABCDEFGH"

# ── ⑤ 종단: 스캐너가 실제로 이 패턴을 쓰는가 (판정기 2벌 방지) ───────────────
#
# ①~④ 는 "정규식이 맞는가"만 증명한다. verify.sh 가 그 패턴을 실제로 그렇게 쓰는지는
# 별개 문제다. 규칙을 복사하는 것이 곧 판정기 2벌이므로 verify.sh 를 실제로 태운다.
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
    printf '%s\n' "$content" > payload.txt
    git add payload.txt >/dev/null 2>&1
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

# 여기서도 변수 이름은 중립이어야 한다(위 ② 와 같은 이유 — 이름만으로 잡히면 판별력 0).
e2e "벤더 키 파일을 verify.sh 가 차단" \
    "cfg.value = \"${SKA}api03-${LONGK}\"" 1
# 신규 패턴은 전부 소문자로 적힌다. verify.sh 에서 `grep -i`(verify.sh:63,72) 가 빠지면
# 대문자 표기의 같은 비밀을 놓치는데, 위 소문자 카나리로는 그 손실을 감지하지 못한다.
e2e "대문자 표기 웹훅도 차단(-i 손실 감지)" \
    "u=HTTPS://${DC_U}.COM/API/${WH_U}/${SNOW}/${TOK_U}" 1
e2e "정상 파일은 verify.sh 가 통과" \
    "{\"position\":\"AX Sales\",\"pages\":20}" 0

if [ "$checked" -eq 0 ]; then
  echo "FAIL: 검사 항목 0개 — 0건 처리로 통과는 금지한다 (P20)"
  echo "CHECKED: 0"
  exit 1
fi

SNAP1=$(git status --porcelain)
if [ "$SNAP0" != "$SNAP1" ]; then
  checked=$((checked + 1))
  echo "FAIL: 이 검사가 저장소를 오염시켰다 — 시작/종료 상태가 다르다 (판정 무효)"
  printf '%s\n' "$SNAP1" | sed 's/^/       /'
  fail=1
else
  checked=$((checked + 1))
  echo "PASS: 저장소 무오염 (시작/종료 상태 동일)"
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
