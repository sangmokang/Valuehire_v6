#!/usr/bin/env bash
# acceptance-hs-1305-pii.sh — 후보자 PII 가 저장소 텍스트 파일에 한 건이라도 들어왔는가
#
# 계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §9 HS-13.05 · §11
#   출력 : 항목마다 PASS:/FAIL: 전부 출력, 마지막 줄 `CHECKED: <검사 수>`
#   exit : 0 = PASS | 1 = FAIL | 2 = NOT_RUN
#   불변식: CHECKED 는 정확히 EXPECTED_CHECKED 여야 한다 — 검사가 사라져도 초록이면 가짜다(P20)
#
# 검사 대상: `git grep -I`(바이너리 제외) 로 고른 **추적 텍스트 파일 전체**.
#   `humansearch/src/`·`contracts/`·`docs/`·`scripts/`·`tests/` 를 전부 포함한다.
#   HS_1305_EXTRA_FILE 이 있으면 그 파일 1개를 대상에 **추가**한다(자기 변이 전용 —
#   저장소 밖 임시 파일을 먹여 "이 검사가 실제로 잡는가"를 증명한다).
#
# 무엇을 판정하나:
#   1  LinkedIn 프로필 slug 가 `example-` 로 시작하지 않는 URL 0건
#      (계약 설명 문서인 goal 문서·docs/sot/ 도 예외 없이 같이 본다 — 현재 0건이다)
#   2  이메일 중 허용 형태(ALLOWED_EMAIL) 밖 0건. 파일 통째 면제는
#      scripts/verify/pii-allowlist.txt 에 적힌 것만, 그것도 이 검사(②)에만 적용된다
#   3  전화 패턴(0X-XXXX-XXXX) 0건
#   4  한국 휴대폰 붙여쓰기(010 + 8자리) 0건
#
# 무엇을 판정하지 못하나 (과장 금지):
#   **사람 이름은 정규식으로 잡을 수 없다.** 이름은 리뷰어 육안과, 후보 데이터가
#   저장소 파일로 들어갈 경로 자체를 만들지 않는 구조(D7: 패킷은 git 밖 0600)로 막는다.
#   여기서 0건은 "이름이 없다"가 아니라 "URL·이메일·전화가 없다"는 뜻이다.
#
# 허용 이메일에 RFC 2606/6761 예약 도메인(example.com/org/net/invalid/test)을 넣은 이유:
#   저장소의 기존 fixture 주소가 전부 그 도메인이고(사람에게 도달 불가), 파일 통째
#   면제로 풀면 humansearch/tests·scripts 를 통째로 눈멀게 해야 한다. 주소 규칙은
#   파일을 눈멀게 하지 않는다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

# grep 은 ugrep 으로 가려져 있을 수 있다 — 절대경로로 고정한다(2026-08-25 실측).
G=/usr/bin/grep
[ -x "$G" ] || { echo "NOT_RUN: $G 가 없다"; echo "CHECKED: 0"; exit 2; }

ALLOWLIST=${HS_1305_ALLOWLIST:-scripts/verify/pii-allowlist.txt}
EXPECTED_CHECKED=4

# BSD grep(macOS)과 GNU grep(CI) 둘 다에서 같게 도는 형태만 쓴다 — `\b` 는 BSD 에서
# 보장되지 않으므로 경계를 문자 클래스로 직접 적는다.
LINKEDIN_PAT='linkedin\.com/in/[A-Za-z0-9%_-]+'
EMAIL_PAT='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z][A-Za-z]+'
ALLOWED_EMAIL=':holder@|@example\.(com|org|net|invalid|test)$|@valueconnect\.kr$|:noreply@anthropic\.com$'
PHONE_PAT='(^|[^0-9A-Za-z-])0[0-9]{1,2}-[0-9]{3,4}-[0-9]{4}([^0-9-]|$)'
MOBILE_PAT='010[0-9]{8}'
# 전화 검사의 유일한 예외: 저장소에 이미 있는 자리표시 번호 `010-1234-5678`.
# 이것은 scripts/acceptance-hs-a4.sh 의 **음성 fixture** 다 — scan-data-exposure.sh 의
# PII 모드가 후보자 CSV 를 실제로 막는지 증명하려고 일부러 심어 둔 줄이다. 지우면
# 그 게이트가 무장 해제되고, 파일 통째 면제는 scripts/ 라서 금지다. 그래서 번호
# 하나만 문자열로 뺀다. 한계: 실제 번호가 정확히 이 자리표시와 같으면 통과한다
# (연속 숫자 견본 번호라 실제 가입 번호로 존재하지 않는다).
ALLOWED_PHONE='010-1234-5678'

LIST=$(mktemp) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -f "$LIST"' EXIT

# 추적 텍스트 파일 전체(바이너리 제외). NUL 구분으로 받아 공백 있는 경로도 안전하게.
if ! git grep -I -l -z -e '' -- . > "$LIST" 2>/dev/null; then
  echo "NOT_RUN: 추적 텍스트 파일 목록을 만들지 못했다"
  echo "CHECKED: 0"
  exit 2
fi
if [ -n "${HS_1305_EXTRA_FILE:-}" ]; then
  if [ ! -f "$HS_1305_EXTRA_FILE" ]; then
    echo "NOT_RUN: HS_1305_EXTRA_FILE 가 파일이 아니다 — $HS_1305_EXTRA_FILE"
    echo "CHECKED: 0"
    exit 2
  fi
  printf '%s\0' "$HS_1305_EXTRA_FILE" >> "$LIST"
fi

targets=()
while IFS= read -r -d '' entry; do
  targets+=("$entry")
done < "$LIST"
file_count=${#targets[@]}
if [ "$file_count" -lt 1 ]; then
  echo "NOT_RUN: 검사 대상 파일이 0개 — 빈 목록은 '전부 통과'가 되므로 판정하지 않는다"
  echo "CHECKED: 0"
  exit 2
fi

fail=0
checked=0
pass() { checked=$((checked + 1)); printf 'PASS: %s\n' "$1"; }
failed() { checked=$((checked + 1)); printf 'FAIL: %s\n' "$1"; fail=1; }

# 대상 전체에서 패턴을 찾아 `경로:줄:일치` 로 낸다. 한 건도 없으면 빈 문자열.
# grep 종료값은 0(일치)·1(불일치)만 정상이고 2 이상은 읽기 실패다. 그 경우
# "일치 0건"으로 접지 않고 SCAN_ERROR 를 흘려 보내 해당 검사를 FAIL 시킨다
# (2026-09-09 정본: 입출력 준비 실패가 "결과 없음"으로 접히면 조용한 거짓 초록이 된다).
scan() {
  local out rc
  out=$("$G" -HonE "$1" "${targets[@]}")
  rc=$?
  if [ "$rc" -gt 1 ]; then
    printf 'SCAN_ERROR: grep 종료값 %s — 대상을 다 읽지 못했다(판정 불가)\n' "$rc"
    return 0
  fi
  printf '%s' "$out"
}

# 파일 통째 면제 목록(② 전용). 규칙 위반 항목은 보조 검사에서 잡는다.
allow_files=""
if [ -f "$ALLOWLIST" ]; then
  allow_files=$("$G" -vE '^[[:space:]]*(#|$)' "$ALLOWLIST")
fi

drop_allowlisted() {
  local input="$1" line path
  if [ -z "$allow_files" ]; then
    printf '%s' "$input"
    return 0
  fi
  printf '%s\n' "$input" | while IFS= read -r line; do
    [ -n "$line" ] || continue
    path=${line%%:*}
    if printf '%s\n' "$allow_files" | "$G" -Fxq -- "$path"; then
      continue
    fi
    printf '%s\n' "$line"
  done
}

report() {
  local label="$1" hits="$2" note="$3"
  if [ -z "$hits" ]; then
    pass "$label 0건 (${file_count}개 파일)$note"
  else
    failed "$label 이 저장소에 있다 — 후보 PII 는 git 에 0건이어야 한다(D7·P21)"
    printf '%s\n' "$hits" | sed 's/^/    /'
  fi
}

# 1) LinkedIn 프로필 slug — `example-` 접두만 허용
linkedin_hits=$(scan "$LINKEDIN_PAT" | "$G" -v 'linkedin\.com/in/example-')
report "실 LinkedIn 프로필 URL(slug 가 example- 아님)" "$linkedin_hits" ""

# 2) 이메일 — 허용 형태 밖 0건 (파일 면제는 allowlist 에 적힌 것만)
email_raw=$(scan "$EMAIL_PAT" | "$G" -vE "$ALLOWED_EMAIL")
email_hits=$(drop_allowlisted "$email_raw")
allow_count=$(printf '%s' "$allow_files" | "$G" -c .)
report "허용 밖 이메일" "$email_hits" " · 면제 파일 ${allow_count:-0}개"

# 3) 전화 패턴 (자리표시 번호 1개만 제외 — 위 ALLOWED_PHONE 주석의 이유)
phone_hits=$(scan "$PHONE_PAT" | "$G" -vF -- "$ALLOWED_PHONE")
report "전화 패턴(0X-XXXX-XXXX)" "$phone_hits" " · 자리표시 ${ALLOWED_PHONE} 제외"

# 4) 한국 휴대폰 붙여쓰기
mobile_hits=$(scan "$MOBILE_PAT")
report "휴대폰 패턴(010+8자리)" "$mobile_hits" ""

# 보조 진단 — 면제 목록이 게이트의 목적을 지우는 자리를 가리키면 안 된다.
# CHECKED 에는 넣지 않는다(WU 카드가 `CHECKED: 4` 를 계약값으로 못박았다).
if [ -n "$allow_files" ]; then
  bad=$(printf '%s\n' "$allow_files" | "$G" -E '^(humansearch/|contracts/|scripts/)')
  if [ -n "$bad" ]; then
    printf 'FAIL: (보조·CHECKED 제외) 면제 목록에 넣을 수 없는 경로가 있다\n'
    printf '%s\n' "$bad" | sed 's/^/    /'
    fail=1
  else
    printf 'PASS: (보조·CHECKED 제외) 면제 목록 %s개가 전부 허용 경로다\n' "$allow_count"
  fi
else
  printf 'PASS: (보조·CHECKED 제외) 면제 목록이 비어 있다 — 통째로 눈감은 파일 0개\n'
fi

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED — 검사가 사라지거나 늘었다"
  exit 1
fi
exit "$fail"
