#!/usr/bin/env bash
# acceptance-hs-1308-nosend.sh — HS-13.08: InMail 초안 모듈에 발송 API 가 0건인가
#
# 계약: docs/engineering/humansearch-hs13-position-brief-goal-2026-09-10.md
#   §7 D8(러너 경계 — 코드는 발송 API 를 갖지 않는다), §8(후보에게 직접 발송 요청 → 거부),
#   §9 HS-13.08("발송 API 부재(정적: send·smtplib·requests import 0)")
#   출력 : 항목마다 PASS:/FAIL: 전부 출력, 마지막 줄 `CHECKED: <검사 수>`
#   exit : 0 = PASS | 1 = FAIL | 2 = NOT_RUN
#   불변식: CHECKED 는 정확히 EXPECTED_CHECKED 여야 한다(P20 — 검사가 사라져도 초록이면 가짜다)
#
# 무엇을 판정하나 (humansearch/src/humansearch/brief/*.py 전체 대상):
#   1  smtplib import 0건 (import smtplib / from smtplib)
#   2  requests·urllib.request import 0건 (import requests / from requests / urllib.request)
#   3  발송 함수 정의·호출 0건 (def send( / .send( / send_message()
set -uo pipefail

unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY \
      GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_PREFIX GIT_QUARANTINE_PATH

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "NOT_RUN: git 저장소가 아니다"; echo "CHECKED: 0"; exit 2; }
cd "$REPO" || { echo "NOT_RUN: 저장소 루트로 이동 실패"; echo "CHECKED: 0"; exit 2; }

BRIEF_DIR="${HS_1308_BRIEF_DIR:-humansearch/src/humansearch/brief}"
EXPECTED_CHECKED=3

if [ ! -d "$BRIEF_DIR" ]; then
  echo "NOT_RUN: 대상 디렉터리 없음 — $BRIEF_DIR"
  echo "CHECKED: 0"
  exit 2
fi

# grep 은 ugrep 으로 가려져 있을 수 있다 — 절대경로로 고정한다(2026-08-25 실측).
G=/usr/bin/grep

fail=0
checked=0

pass() { checked=$((checked + 1)); printf 'PASS: %s\n' "$1"; }
failed() { checked=$((checked + 1)); printf 'FAIL: %s\n' "$1"; fail=1; }

FILE_COUNT=$(find "$BRIEF_DIR" -type f -name '*.py' | wc -l | tr -d ' ')
if [ "$FILE_COUNT" -eq 0 ]; then
  echo "NOT_RUN: $BRIEF_DIR 아래 .py 파일이 없다"
  echo "CHECKED: 0"
  exit 2
fi

# 1) smtplib import 0건
if hits=$(find "$BRIEF_DIR" -type f -name '*.py' -exec $G -Eln '^\s*(import\s+smtplib|from\s+smtplib\b)' {} +); then
  failed "smtplib import 가 있다: $hits"
else
  pass "smtplib import 0건"
fi

# 2) requests·urllib.request import 0건
if hits=$(find "$BRIEF_DIR" -type f -name '*.py' -exec $G -Eln '^\s*(import\s+requests|from\s+requests\b|import\s+urllib\.request|from\s+urllib\.request\b)' {} +); then
  failed "requests/urllib.request import 가 있다: $hits"
else
  pass "requests/urllib.request import 0건"
fi

# 3) 발송 함수 정의·호출 0건 (def send( / .send( / send_message()
if hits=$(find "$BRIEF_DIR" -type f -name '*.py' -exec $G -Eln '(^\s*def\s+send\(|\.send\(|send_message\()' {} +); then
  failed "발송 함수 정의·호출이 있다: $hits"
else
  pass "발송 함수 정의·호출(def send(·.send(·send_message() ) 0건"
fi

echo "CHECKED: $checked"
if [ "$checked" -ne "$EXPECTED_CHECKED" ]; then
  echo "FAIL: CHECKED $checked ≠ 기대 $EXPECTED_CHECKED — 검사가 사라지거나 늘었다"
  exit 1
fi
exit "$fail"
