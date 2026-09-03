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
# 세 축을 잡는다(2026-08-12 V1 D4): 파일 상태(무시 파일 포함) · HEAD · git 객체 수.
SNAP0=$(git status --porcelain --ignored 2>/dev/null)
HEAD0=$(git rev-parse HEAD 2>/dev/null)
# ⚠️ 워크트리에서는 --git-dir 이 .git/worktrees/<이름> 을 가리키고 그 아래엔 objects 가
# 없다. --git-common-dir 을 써야 실제 객체 저장소를 본다(2026-08-12 실측: --git-dir 기준
# 이면 개수가 항상 0이라 이 검사가 아무것도 못 잡았다).
OBJ0=$(find "$(git rev-parse --git-common-dir)/objects" -type f 2>/dev/null | wc -l | tr -d ' ')

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
# AC-SECRET-SHORT-1 용 조각 (2026-09-03). 리터럴로 두지 않는 이유는 위 60행과 같다.
K_TK=$(printf 'TOK%s' 'EN')                       # TOKEN
K_PW=$(printf 'PASSW%s' 'ORD')                    # PASSWORD (대조군 전용)
SHORTV=abc123xy                                   # 8자 — 6자 하한과 12자 하한 사이
LONGV=$(printf 'abcdef%s' '123456789')            # 15자 — 12자 하한을 넘는 값

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
# ⚠️ 이 카나리의 값에 Discord 웹훅 URL 을 쓰면 안 된다. 그러면 위 ① 의 웹훅 패턴이
# 값을 보고 잡아버려서, 키워드 패턴을 지워도 이 항목이 초록으로 남는다(2026-08-12
# 뮤테이션 M4 에서 실측 — 이중 커버로 판별력이 0이었다). 값은 중립 URL 이어야 한다.
# ⚠️ 값을 URL 에서 **불투명 토큰**으로 바꿨다(2026-08-12 V1 D2 반영).
# URL 값 형태는 `.env.example` 의 정상 한 줄과 실제 운영 웹훅 주소가 모양이 완전히 같아
# 구분이 불가능하다. 비밀 스캔에는 억제 경로가 없어 오탐 1건이 곧 작업 중단이므로,
# URL 값 판정은 벤더 규칙(discord/slack)에 맡기고 이 키워드 규칙은 불투명 토큰만 본다.
# 그 결정의 대가(3사 밖 벤더 웹훅 URL 미탐)는 아래 ⑥ 한계 대조군으로 명시한다.
# ⚠️ 키 이름에 SECRET/TOKEN 등 기존 키워드를 쓰면 안 된다 — 기존 (2) 규칙이 이름만
# 보고 잡아서, 신규 규칙을 지워도 이 항목이 초록으로 남는다(2026-08-12 V2 뮤테이션
# 실측: _SECRET_VALUE 이름일 때 신규 규칙 삭제에도 '탐지됨'. D5 와 같은 죽은 카나리).
must_catch "${K_WH} 계열 .env 대입(불투명 토큰)" "${K_WH}_SIGNING_VALUE=${TOK}"
must_catch "${K_CR} 계열 .env 대입" "export SERVICE_${K_CR}=${TOK}"
must_catch "${K_PK} 한 줄 형태"     "${K_PK}=MIIEvQIBADANBgkqhkiG9w0BAQEFAASC"
# 회귀 방지 — 이 한 건은 기존 패턴(.secret-patterns.default:11 의 TOKEN)이 **이미** 덮는다.
# 신규 패턴이 없어도 통과하므로 RED 단계에서도 초록이다. 나중에 기존 패턴을 건드렸을 때
# 조용히 사라지는 것을 막기 위한 앵커다(중복이라는 사실을 goal §1-8 에 적었다).
# ⚠️ 이 항목은 **기존 (1)(2) 규칙의 TOKEN** 을 시험한다. 신규 규칙에는 BOT_TOKEN 이 없다.
# 2026-08-12 V1 D5: 신규 규칙에 BOT_TOKEN 을 중복으로 두면 어느 한쪽이 지워져도 다른 쪽이
# 가려서 시험이 계속 초록이다 — 방어 심도가 아니라 '서로의 삭제를 가리는 죽은 중복'이다.
must_catch "${K_BT} (기존 TOKEN 규칙 회귀 앵커 · 신규 규칙에는 없음)" "${K_BT}=${TOK}"

# ── ②-b V1 이 뚫은 형식 (2026-08-12 D1) ──────────────────────────────────────
# 전부 공식 문서에 있는 실제 사용 형태다. 근거는 판정서 §2 참조.
V10=$(printf 'v%s' '10')
# 조각을 조합식(${VAR%%.*} 등)으로 쓰면 bash 3.2 에서 의도와 다르게 풀려 카나리가
# 엉뚱한 문자열이 된다(2026-08-12 실측: GovSlack 카나리가 평범한 slack.com 이 되어
# 기존 규칙에 걸리는 바람에 '탐지됨'으로 초록이 났다). 명시 변수로만 만든다.
SLACK_GOV_HOST=$(printf 'hooks.sl%s' 'ack-gov.com')
SLACK_HOST=$(printf 'hooks.sl%s' 'ack.com')
NOT_SLACK_HOST=$(printf 'not-hooks.sl%s' 'ack.com')
NOT_DC=$(printf 'not%s' "$DC")
must_catch "${DC} 버전 경로 /api/${V10}/ (공식 권장 형식)" \
  "https://${DC}.com/api/${V10}/${WH}/${SNOW}/${TOK}"
must_catch "${DC} 하위 도메인(canary)" \
  "https://canary.${DC}.com/api/${WH}/${SNOW}/${TOK}"
must_catch "Slack 공공기관용 GovSlack 도메인" \
  "https://${SLACK_GOV_HOST}/${SVC}/T01ABCDEFGH/B01ABCDEFGH/${TOK}"
must_catch "Slack ${SVC} 없는 형태(OAuth 응답 예시)" \
  "https://${SLACK_HOST}/T01ABCDEFGH/B01ABCDEFGH/${TOK}"
must_catch "벤더 키 39자 본문(길이 경계)" \
  "  cfg.value = \"${SKA}AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\""
must_catch "인라인 주석이 붙은 .env 값" \
  "${K_CR}=abcdef123456 # local placeholder"

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

# ── ④-b V1 이 지적한 오탐 (2026-08-12 D2) ────────────────────────────────────
# 비밀 스캔에는 억제 경로가 없다. 아래가 막히면 .env.example·문서·CI 설정을 추가하는
# 정상 작업이 그 자리에서 멈추고, 그것이 훅 우회 습관을 만든다.
must_not_catch ".env.example 의 예시 주소" \
  "${K_WH}_URL=https://example.com/hooks/not-a-secret"
must_not_catch "숫자만 있는 설정값(재시도 간격)" \
  "${K_WH}_RETRY_INTERVAL_MS=300000"
must_not_catch "접미사 위장 도메인(${NOT_DC}.com)" \
  "https://${NOT_DC}.com/api/${WH}/${SNOW}/${TOK}"
must_not_catch "접미사 위장 도메인(${NOT_SLACK_HOST})" \
  "https://${NOT_SLACK_HOST}/${SVC}/T01ABCDEFGH/B01ABCDEFGH/${TOK}"
# ④-c V2 재검증이 잡은 잔여 오탐 (2026-08-12): 글자로 된 짧은 설정값.
# 키워드 규칙이 "글자 1개 + 5자"만 요구해 keychain(8자)·PKCS12(6자) 같은
# 저장 방식·형식 이름이 비밀로 오인됐다. 값 하한을 12자로 올려 해소한다 —
# 12자 미만의 실제 비밀은 놓친다(대가, 위 143행 카나리 12자는 유지되는 하한).
must_not_catch "${K_CR} 저장 방식 이름(글자 설정값)" \
  "${K_CR}_PROVIDER=keychain"
must_not_catch "${K_PK} 형식 이름(짧은 글자+숫자 설정값)" \
  "${K_PK}_FORMAT=PKCS12"
# ④-d codeaudit(2026-08-12) 이 잡은 헛경보 — 벤더 규칙의 왼쪽 경계 누락/과대.
# 억제 경로가 없어 이 오탐 1건이 곧 작업 중단이므로 반드시 막는다.
# D5: sk-ant 규칙에 왼쪽 경계가 없어 평범한 식별자 안의 'sk-ant-' 조각을 잡았다.
must_not_catch "sk-ant 조각을 품은 평범한 식별자(왼쪽 경계)" \
  "module: mask-ant-colony-observation-notes-2026-final"
# D4: discord/slack 규칙의 경계 [^A-Za-z0-9-] 가 밑줄을 통과시켜 위장 도메인을 잡았다.
must_not_catch "밑줄 접두 위장 ${DC} 도메인" \
  "url=my_${DC}.com/api/${WH}/${SNOW}/${TOK}"
must_not_catch "밑줄 접두 위장 slack 도메인" \
  "url=team_${SLK}/${SVC}/T01ABCDEFGH/B01ABCDEFGH/${TOK}"

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

# ── ⑥ AC-SECRET-SHORT-1 — 환경변수 형식의 6~11자 구간 (2026-09-03) ───────────
#
# 계약: docs/engineering/secret-short-value-goal-2026-09-03.md §⑤
#   기존 12자 규칙(.secret-patterns.default 마지막 줄)은 그대로 두고, 허용-접미를
#   **열거한** 6자 하한 규칙을 한 줄 더한다. 접미사가 열거 밖이면 판정하지 않는다 —
#   `_PROVIDER`·`_FORMAT` 은 비밀이 아니라 비밀의 메타데이터를 담는 이름이기 때문이다.
#
# ⚠️ 대조군 먼저. MISSED 판정은 "규칙이 배제했다"와 "판정기가 죽었다"를 구분하지 못한다.
# 아래 대조군이 CAUGHT 가 아니면 뒤따르는 MISSED 3건은 증거가 아니다(goal §⑤ CA-3).
must_catch "대조군(자가검증) — ${K_PW} 짧은 값은 기존 규칙이 이미 잡는다" \
  "${K_PW}=${SHORTV}"

# 6벡터는 정규식 단위가 아니라 **verify.sh 전체 스캐너**에 격리 파일로 넣는다.
# 정규식이 맞아도 스캐너가 그 줄을 안 쓰면 아무 의미가 없다(⑤ 와 같은 이유).
e2e "짧은 값 — ${K_CR} (접미 없음)"          "${K_CR}=${SHORTV}"            1
e2e "짧은 값 — ${K_WH}_URL (열거된 접미)"    "${K_WH}_URL=${SHORTV}"        1
e2e "짧은 값 — ${K_PK} (접미 없음)"          "${K_PK}=${SHORTV}"            1
# ⚠️ 이 한 건은 **기존 (2) 규칙의 TOKEN** 이 이미 덮는다. 신규 줄을 지워도 초록이므로
# 신규 규칙의 검출력 증거로 세지 않는다(goal §⑤ 판별력 열 ❌ · 회귀 앵커 전용).
e2e "회귀 앵커 — ${K_CR}_${K_TK} (기존 ${K_TK} 규칙 소관)" \
                                             "${K_CR}_${K_TK}=${SHORTV}"    1
e2e "오탐 방지 — ${K_CR}_PROVIDER (열거 밖 접미)" "${K_CR}_PROVIDER=keychain" 0
e2e "오탐 방지 — ${K_PK}_FORMAT (열거 밖 접미)"   "${K_PK}_FORMAT=PKCS12"     0

# ── ⑥-b old∖new 회귀 — 2026-09-03 기준선이 잡던 것을 지금도 잡는가 ───────────
#
# 기준선은 **동결 사본**이다(scripts/verify/fixtures/secret-patterns/). '현재 파일에서
# 신규 줄을 뺀 것'을 기준선으로 삼으면, 줄을 더하기만 한 변경에서는 검출력이 구조적으로
# 줄 수 없어 항상 0이 나오는 동어반복이 된다. 동결 사본이어야 "기존 12자 줄을 신규 줄로
# 교체" 같은 실제 회귀가 여기서 빨간불이 된다(goal §⑤ CA-2).
BASELINE=scripts/verify/fixtures/secret-patterns/baseline-2026-09-03.default
# 기준선 무결성은 **해시로 못박는다** (2026-09-03 V1 적대검증 D3).
#   V1 반례: fixture 를 `.` 한 줄로 바꿔도 코퍼스 전건이 '기준선 탐지'로 남아
#   old_caught 하한을 통과하고 회귀 0이 나온다. 즉 기준선 자체가 공격면이었다.
#   이 상수를 바꾸는 것은 곧 "탐지 기준선을 의도적으로 옮긴다"는 선언이며,
#   그때는 suppressions.yaml 에 근거를 남기는 것이 계약이다.
BASELINE_SHA256=24fa49aa45af2253f1f508b49d988086bf511dd7c13d6b5b5be1a38265e04000
OLDCLEAN=$(mktemp) || { echo "FAIL: mktemp 실패 — 회귀 대조 불가"; echo "CHECKED: ${checked}"; exit 2; }
trap 'rm -f "$CLEAN" "$OLDCLEAN"' EXIT
checked=$((checked + 1))
if [ ! -f "$BASELINE" ] || [ ! -s "$BASELINE" ]; then
  echo "FAIL: 회귀 기준선이 없다/비었다 — $BASELINE (fail-closed)"
  fail=1
else
  got=$(shasum -a 256 "$BASELINE" 2>/dev/null | awk '{print $1}')
  if [ -z "$got" ]; then
    echo "FAIL: 기준선 해시를 계산하지 못했다 (shasum 부재 · fail-closed)"
    fail=1
  elif [ "$got" != "$BASELINE_SHA256" ]; then
    printf 'FAIL: 기준선이 변조됐다 — 기대 %s / 실제 %s\n' "$BASELINE_SHA256" "$got"
    fail=1
  else
    printf 'PASS: 회귀 기준선 무결 (sha256 %s…)\n' "$(printf '%s' "$got" | cut -c1-12)"
  fi
  tr -d '\r' < "$BASELINE" | grep -vE '^[[:space:]]*(#|$)' > "$OLDCLEAN"
fi

# 회귀 코퍼스 — 2026-09-03 기준선이 CAUGHT 하던 표본. 값은 전부 더미이며 파일에 쓰지 않는다.
CORPUS_1="${K_CR}_PROVIDER=${LONGV}"
CORPUS_2="${K_PK}_FORMAT=${LONGV}"
CORPUS_3="${K_WH}_RETRY_LABEL=${LONGV}"
CORPUS_4="${K_WH}_SIGNING_VALUE=${TOK}"
CORPUS_5="export SERVICE_${K_CR}=${TOK}"
CORPUS_6="${K_PK}=MIIEvQIBADANBgkqhkiG9w0BAQEFAASC"
CORPUS_7="${K_BT}=${TOK}"
CORPUS_8="https://${DC}.com/api/${WH}/${SNOW}/${TOK}"
CORPUS_9="https://${SLK}/${SVC}/T01ABCDEFGH/B01ABCDEFGH/${TOK}"
CORPUS_10="  cfg.value = \"${SKA}api03-${LONGK}\""
CORPUS_11="${K_CR}=abcdef123456 # local placeholder"
CORPUS_12="${K_PW}=${SHORTV}"
# 2026-09-03 V1 적대검증 D3·D4 반영 — 코퍼스가 키워드 계열만 덮어서, 코퍼스 밖 규칙
# (AWS·GitHub·JWT·쿠키…)을 완화하거나 지워도 회귀 0이 나왔다. V1 이 든 반례가
# 정확히 `AKIA[0-9A-Z]{16}` -> `{99}` 였다. 규칙 계열마다 표본을 하나씩 박아 둔다.
# 카나리는 전부 조립한다 — 리터럴로 두면 이 파일 자신이 스캔에 걸린다(위 60행과 같은 이유).
AWSP=$(printf 'AK%s' 'IA')
GHP=$(printf 'gh%s_' 'p')
AIZ=$(printf 'AI%s' 'za')
XOX=$(printf 'xo%s-' 'xb')
SKG=$(printf 'sk%s' '-')
JWTP=$(printf 'ey%s' 'J')
LIAT=$(printf 'li%sat' '_')
AQ=$(printf 'AQ%s' 'ED')
PEM=$(printf -- '-----BE%s RSA PRIVATE KEY-----' 'GIN')
CORPUS_13="${AWSP}IOSFODNN7EXAMPLE"
CORPUS_14="${GHP}0123456789abcdefghijklmnopqrstuvwxyz01"
CORPUS_15="${AIZ}SyD0123456789abcdefghijklmnopqrstuvw"
CORPUS_16="${XOX}0123456789-abcdefghij"
CORPUS_17="${SKG}0123456789abcdefghijklmno"
CORPUS_18="${JWTP}hbGciOiJIUzI1NiJ9.${JWTP}zdWIiOiIxIn0.c2ln"
CORPUS_19="  {\"name\": \"${LIAT}\", \"domain\": \".example.com\"}"
CORPUS_20="${AQ}AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
CORPUS_21="$PEM"
# ⚠️ 이 둘은 조립하지 않으면 **이 파일 자신이** 스캔에 걸린다(2026-09-03 실측:
# verify.sh 가 이 스크립트를 매치해 exit 1). 자격증명 URL 과 Authorization 헤더는
# 카나리 문자열이 곧 완성된 매치라 변수로 끊어야 한다.
URLC=$(printf 'user:hunter2%s@' 'pass')
AUTHH=$(printf 'Authoriza%s' 'tion')
BEAR=$(printf 'Bear%s' 'er')
CORPUS_22="  fetch('https://${URLC}internal.example.com/x')"
CORPUS_23="  ${AUTHH}: ${BEAR} abcdefghijklmnop.qrst"
# ⚠️ 실제 응답 헤더 형식이어야 한다. `headers['Set-Cookie'] = '...'` 같은 코드 대입은
# 규칙 (8)의 `SET-COOKIE[[:space:]]*:` 를 만족하지 않아 첫 판에서 이 표본만 미탐이었다
# (2026-09-03 실측: 코퍼스 23/24). 규칙이 아니라 표본이 틀렸던 경우다.
SETC=$(printf 'Set-Coo%s' 'kie')
CORPUS_24="${SETC}: sid=abc123def456; Path=/"
CORPUS_N=24

old_caught=0
regressed=0
i=1
while [ "$i" -le "$CORPUS_N" ]; do
  eval "line=\$CORPUS_$i"
  o=0; printf '%s\n' "$line" | grep -qEif "$OLDCLEAN" || o=$?
  n=0; printf '%s\n' "$line" | grep -qEif "$CLEAN"    || n=$?
  if [ "$o" -gt 1 ] || [ "$n" -gt 1 ]; then
    printf 'FAIL: 회귀 대조 실행 오류 (기준선 exit=%s · 현행 exit=%s) — 코퍼스 %d\n' "$o" "$n" "$i"
    fail=1
  else
    [ "$o" -eq 0 ] && old_caught=$((old_caught + 1))
    if [ "$o" -eq 0 ] && [ "$n" -ne 0 ]; then
      printf 'FAIL: 회귀 — 기준선은 잡던 것을 지금은 놓친다 (코퍼스 %d)\n' "$i"
      regressed=$((regressed + 1))
    fi
  fi
  i=$((i + 1))
done

# 대조군: 기준선이 코퍼스를 하나도 못 잡으면 위 "회귀 0건"은 판정기가 죽은 결과일 뿐이다.
checked=$((checked + 1))
if [ "$old_caught" -ne "$CORPUS_N" ]; then
  printf 'FAIL: 기준선이 코퍼스 %d건 중 %d건만 탐지 — 기준선이 죽었다면 회귀 0건은 증거가 아니다\n' \
    "$CORPUS_N" "$old_caught"
  fail=1
else
  printf 'PASS: 회귀 기준선 살아있음 — 코퍼스 %d/%d 탐지 (%s)\n' "$old_caught" "$CORPUS_N" "$BASELINE"
fi

# ── ⑥-c 설정 센티널 오탐 코퍼스 (2026-09-03 V1 적대검증 D2 반례의 영구 편입) ──
#
# V1 이 `WEBHOOK_VALUE=disabled` 로 뚫었고, 실측해 보니 범위가 더 넓었다 —
# 이름 열거와 길이만으로 가르면 `disabled`·`keychain`·`changeme` 같은 평범한 설정
# 센티널이 전부 비밀로 잡힌다. 비밀 스캔에는 줄 단위 억제 경로가 없어 이 한 줄이 곧
# 전 브랜치 작업 중단이므로, 값에 숫자를 요구하는 것으로 닫고 그 반례를 여기 박아 둔다.
FP_1="${K_WH}_VALUE=disabled"
FP_2="${K_WH}_URL=disabled"
FP_3="${K_WH}_ENDPOINT=disabled"
FP_4="${K_CR}=disabled"
FP_5="${K_CR}=keychain"
FP_6="${K_WH}_URL=changeme"
FP_7="${K_CR}=placeholder"
FP_8="${K_PK}=default"
FP_N=8

fp_hit=0
i=1
while [ "$i" -le "$FP_N" ]; do
  eval "line=\$FP_$i"
  rc=0; printf '%s\n' "$line" | grep -qEif "$CLEAN" || rc=$?
  if [ "$rc" -gt 1 ]; then
    printf 'FAIL: 센티널 대조 실행 오류 (grep exit=%s) — FP %d\n' "$rc" "$i"; fail=1
  elif [ "$rc" -eq 0 ]; then
    printf 'FAIL: 오탐 — 평범한 설정 센티널이 비밀로 잡힌다 (FP %d)\n' "$i"
    fp_hit=$((fp_hit + 1))
  fi
  i=$((i + 1))
done

checked=$((checked + 1))
if [ "$fp_hit" -ne 0 ]; then
  printf 'FAIL: 설정 센티널 오탐 %d건 (계약값 0) — 오탐 1건이 곧 전 브랜치 작업 중단이다\n' "$fp_hit"
  fail=1
else
  printf 'PASS: 설정 센티널 %d종 오탐 0건 (2026-09-03 V1 반례 회귀)\n' "$FP_N"
fi

checked=$((checked + 1))
printf 'OLD_CAUGHT_AND_NEW_MISSED_COUNT=%d\n' "$regressed"
if [ "$regressed" -ne 0 ]; then
  printf 'FAIL: 변경 전 CAUGHT → 변경 후 MISSED 가 %d건 (계약값 0)\n' "$regressed"
  fail=1
else
  printf 'PASS: 변경 전 CAUGHT 였다가 변경 후 MISSED 가 된 항목 0건\n'
fi

# ── 종료 상태 대조 (D4) ──────────────────────────────────────────────────────
# 2026-08-12 V1 D4: `git status --porcelain` 만 두 시점 비교하면 **무시된 파일**(gitignore)과
# **잠깐 생겼다 지운 변경**을 못 본다. 검사기가 로컬 산출물이나 비밀 파일을 남겨도 "무오염"이
# 된다. 세 축으로 넓힌다 — ① --ignored 로 무시 파일까지 ② HEAD 이동 여부 ③ 객체 파일 수.
# ③ 이 '잠깐 생겼다 지운' 경로를 잡는다: git 은 객체를 쓰면 지워도 파일이 남기 때문이다.
SNAP1=$(git status --porcelain --ignored 2>/dev/null)
HEAD1=$(git rev-parse HEAD 2>/dev/null)
OBJ1=$(find "$(git rev-parse --git-common-dir)/objects" -type f 2>/dev/null | wc -l | tr -d ' ')
checked=$((checked + 1))
if [ "$SNAP0" != "$SNAP1" ]; then
  echo "FAIL: 이 검사가 작업트리를 오염시켰다 — 시작/종료 상태가 다르다 (무시 파일 포함 · 판정 무효)"
  printf '%s\n' "$SNAP1" | sed 's/^/       /'
  fail=1
elif [ "$HEAD0" != "$HEAD1" ]; then
  echo "FAIL: 이 검사가 HEAD 를 옮겼다 ($HEAD0 -> $HEAD1) — 판정 무효"
  fail=1
elif [ "$OBJ0" != "$OBJ1" ]; then
  echo "FAIL: 이 검사가 git 객체를 남겼다 (${OBJ0} -> ${OBJ1}) — 되돌린 척한 오염 (판정 무효)"
  fail=1
else
  echo "PASS: 3축 종료 상태 동일 (파일 상태[무시 포함] · HEAD · 객체 수 — 중간에 바꿨다 되돌린 변경·같은 개수 객체 교체는 못 본다, REV2-D1)"
fi

# ── 하한 (D3) — "0건만 아니면 통과"는 하한이 아니다 ──────────────────────────
# 2026-08-12 V1 D3: 이전 판은 `checked == 0` 만 막아서 **검사 3개를 지워도 성공**했다
# (CHECKED: 14 로 통과). bash 버전 차이·편집 실수로 검사가 조용히 사라지는 것이
# 이 저장소의 실제 사고 유형이다(같은 날 ${VAR^^} 로 3건이 사라졌다).
# 그래서 기대 개수를 코드에 못박고 **적으면 실패**한다(P20 · P2).
# 2026-09-03 AC-SECRET-SHORT-1 로 9건 추가(32 -> 41): 대조군 1 + 격리 e2e 6 + 회귀 2.
# 같은 날 V1 적대검증 반례 편입으로 2건 추가(41 -> 43): 기준선 해시 대조 1 + 센티널 오탐 1.
# ⚠️ AC 6벡터의 표본과 기대값은 RED 커밋(ae84381) 이후 한 글자도 바뀌지 않았다.
# 늘어난 것은 전부 적대검증이 찾아낸 반례를 **더한** 것이지 기준을 낮춘 것이 아니다.
EXPECTED_CHECKS=43
# -lt(하한)가 아니라 -ne(정확값)로 조인다: 하한만 보면 새 검사 3개를 넣고 기존 3개를
# 지워도 초록이다. V1 판정서의 설계 결정("checked == 기대값 강제")과도 이쪽이 일치한다.
if [ "$checked" -ne "$EXPECTED_CHECKS" ]; then
  printf 'FAIL: 검사 항목 %d개 ≠ 계약값 %d개 (검사가 사라졌거나 무단 추가됐다 · P20)\n' "$checked" "$EXPECTED_CHECKS"
  printf 'CHECKED: %d\n' "$checked"
  exit 1
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
