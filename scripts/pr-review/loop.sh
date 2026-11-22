#!/usr/bin/env bash
# pr-review/loop.sh — run.sh 를 주기적으로 돈다. herdr 의 pr-review 작업공간 첫 창에서 start.sh 가 띄운다 (#133)
# 사용: bash loop.sh [간격초]   기본 3600(매시간). 하루 한 번은 86400. 멈추려면 이 창에서 Ctrl+C.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
INTERVAL=${1:-3600}
case "$INTERVAL" in ''|*[!0-9]*) echo "간격은 초 단위 숫자: ${INTERVAL}" >&2; exit 2 ;; esac
[ "${HERDR_ENV:-}" = 1 ] || { echo "herdr 창 안에서 실행해야 한다" >&2; exit 2; }
while :; do
  bash "$HERE/run.sh"
  echo "$(date '+%F %T') 대기 — 다음 회차는 ${INTERVAL}초 뒤"
  sleep "$INTERVAL"
done
