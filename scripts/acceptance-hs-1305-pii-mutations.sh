#!/usr/bin/env bash
# acceptance-hs-1305-pii-mutations.sh — PII 게이트가 실제 형태의 PII 를 잡는가 (자기 변이 2종)
#
# 계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md §9 HS-13.05 · P13⑥
#   변이 ⓐ 실 LinkedIn 프로필 URL 이 든 파일 1개 → 검사가 exit 1
#   변이 ⓑ 실 이메일(개인 메일 도메인)이 든 파일 1개 → 검사가 exit 1
#   대조군(보조·CHECKED 제외): 추가 파일 없이 그대로 → 검사가 exit 0
#     (항상-거부 검사기를 잡는다. 이게 없으면 두 변이는 `exit 1` 한 줄로도 통과한다)
#   출력: PASS:/FAIL: + `CHECKED: 2`, exit 0/1/2
#
# 왜 mktemp **사본 저장소**가 아니라 환경변수인가:
#   저장소를 통째로 복사하면 판정 대상이 옛 사본이 되어 "검사가 대상을 안 보는" 함정에
#   빠진다(2026-09-09 정본). 여기서는 진짜 저장소를 그대로 보되 검사 대상 목록에
#   임시 파일 1개만 더한다 — 무엇이 판정을 뒤집었는지가 파일 하나로 고정된다.
#
# 쓰기 규칙: 저장소에 아무 파일도 만들지 않는다. 변이 파일은 mktemp 디렉터리에만 쓴다.
#
# ⚠️ 이 스크립트 자신도 PII 게이트의 검사 대상이다. 그래서 변이 문자열을 소스에
#    그대로 적지 않고 조각을 이어 붙인다 — 그대로 적으면 게이트가 이 파일을 잡는다.
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2
}
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

CHECKER=scripts/acceptance-hs-1305-pii.sh
EXPECTED_CHECKED=2
G=/usr/bin/grep

[ -f "$CHECKER" ] || { echo "NOT_RUN: 검사기 없음 — $CHECKER"; echo "CHECKED: 0"; exit 2; }
[ -x "$G" ] || { echo "NOT_RUN: $G 가 없다"; echo "CHECKED: 0"; exit 2; }

TMP=$(mktemp -d) || { echo "NOT_RUN: mktemp 실패"; echo "CHECKED: 0"; exit 2; }
trap 'rm -rf "$TMP"' EXIT

# 변이 문자열 조립 — 소스에는 조각만 남는다.
HOST="linked""in.com"
REAL_URL="https://www.${HOST}/in/real-person-123"
MAIL_DOMAIN="gm""ail.com"
REAL_MAIL="someone@${MAIL_DOMAIN}"

fail=0
checked=0

expect_rc() {
  local desc="$1" extra="$2" want="$3" rc=0
  checked=$((checked + 1))
  HS_1305_EXTRA_FILE="$extra" bash "$CHECKER" >/dev/null 2>&1
  rc=$?
  if [ "$rc" -eq "$want" ]; then
    printf 'PASS: %s (exit=%s)\n' "$desc" "$rc"
  else
    printf 'FAIL: %s (기대 exit=%s, 실제 %s)\n' "$desc" "$want" "$rc"
    fail=1
  fi
}

# 대조군 — 추가 파일 없이는 통과해야 한다(보조·CHECKED 제외).
bash "$CHECKER" >/dev/null 2>&1
base_rc=$?
if [ "$base_rc" -eq 0 ]; then
  printf 'PASS: (보조·CHECKED 제외) 대조군 — 추가 파일 없이 통과 (exit=0)\n'
else
  printf 'FAIL: (보조·CHECKED 제외) 대조군이 실패했다 (exit=%s) — 변이 결과를 믿을 수 없다\n' "$base_rc"
  fail=1
fi

# ⓐ 실 LinkedIn 프로필 URL
printf '후보 프로필: %s\n' "$REAL_URL" > "$TMP/url.txt"
if ! "$G" -qE 'linkedin\.com/in/real-person-123' "$TMP/url.txt"; then
  echo "NOT_RUN: 변이ⓐ 파일 생성 실패"; echo "CHECKED: $checked"; exit 2
fi
expect_rc "변이ⓐ 실 LinkedIn 프로필 URL 1건 → 불합격" "$TMP/url.txt" 1

# ⓑ 실 이메일
printf 'Email Contact: %s\n' "$REAL_MAIL" > "$TMP/mail.txt"
if ! "$G" -qE 'someone@gm[a]il\.com' "$TMP/mail.txt"; then
  echo "NOT_RUN: 변이ⓑ 파일 생성 실패"; echo "CHECKED: $checked"; exit 2
fi
expect_rc "변이ⓑ 실 이메일 1건 → 불합격" "$TMP/mail.txt" 1

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED"
  exit 1
fi
exit "$fail"
