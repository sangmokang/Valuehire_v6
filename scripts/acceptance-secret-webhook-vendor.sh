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
must_catch "${K_WH} 계열 .env 대입(불투명 토큰)" "${K_WH}_SECRET_VALUE=${TOK}"
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
  echo "PASS: 저장소 무오염 (파일 상태[무시 포함] · HEAD · 객체 수 3축 동일)"
fi

# ── 하한 (D3) — "0건만 아니면 통과"는 하한이 아니다 ──────────────────────────
# 2026-08-12 V1 D3: 이전 판은 `checked == 0` 만 막아서 **검사 3개를 지워도 성공**했다
# (CHECKED: 14 로 통과). bash 버전 차이·편집 실수로 검사가 조용히 사라지는 것이
# 이 저장소의 실제 사고 유형이다(같은 날 ${VAR^^} 로 3건이 사라졌다).
# 그래서 기대 개수를 코드에 못박고 **적으면 실패**한다(P20 · P2).
EXPECTED_CHECKS=29
# -lt(하한)가 아니라 -ne(정확값)로 조인다: 하한만 보면 새 검사 3개를 넣고 기존 3개를
# 지워도 초록이다. V1 판정서의 설계 결정("checked == 기대값 강제")과도 이쪽이 일치한다.
if [ "$checked" -ne "$EXPECTED_CHECKS" ]; then
  printf 'FAIL: 검사 항목 %d개 ≠ 계약값 %d개 (검사가 사라졌거나 무단 추가됐다 · P20)\n' "$checked" "$EXPECTED_CHECKS"
  printf 'CHECKED: %d\n' "$checked"
  exit 1
fi

printf 'CHECKED: %d\n' "$checked"
exit "$fail"
