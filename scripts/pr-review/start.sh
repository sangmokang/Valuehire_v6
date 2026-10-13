#!/usr/bin/env bash
# pr-review/start.sh — herdr 에 pr-review 작업공간을 만들고 그 첫 창에서 loop.sh 를 띄운다 (#133)
#
# 사용: bash scripts/pr-review/start.sh [간격초]   기본 3600(매시간). 하루 한 번은 86400.
#       bash scripts/pr-review/start.sh --stop      작업공간을 닫아 반복을 멈춘다
# 스크립트·지시문은 상태 디렉터리 bin/ 으로 복사해 실행한다. 리뷰 중 체크아웃되는 PR 브랜치의 코드나
# 나중에 지워질 수 있는 워크트리 경로를 반복 실행기가 부르지 않게 하기 위해서다.
# 스크립트를 고친 뒤에는 --stop 후 다시 start 해야 반영된다.
set -euo pipefail

STATE=${PR_REVIEW_STATE:-$HOME/.valuehire-pr-review}
HERE=$(cd "$(dirname "$0")" && pwd)
LABEL=pr-review

[ "${HERDR_ENV:-}" = 1 ] || { echo "herdr 창 안에서 실행해야 한다(HERDR_ENV=1)" >&2; exit 2; }
for c in git gh jq herdr codex claude; do command -v "$c" >/dev/null || { echo "필요한 명령 없음: ${c}" >&2; exit 2; }; done

existing=$(herdr workspace list | jq -r --arg l "$LABEL" '.result.workspaces[]? | select(.label == $l) | .workspace_id')
if [ "${1:-}" = "--stop" ]; then
  for w in $existing; do herdr workspace close "$w" > /dev/null; echo "멈춤: 작업공간 ${w}"; done
  exit 0
fi
if [ -n "$existing" ]; then
  echo "이미 돌고 있다: 작업공간 ${existing}. 다시 띄우려면 --stop 후 start" >&2; exit 1
fi

INTERVAL=${1:-3600}
mkdir -p "$STATE/bin"
cp "$HERE/run.sh" "$HERE/loop.sh" "$HERE/prompt-claude.md" "$HERE/prompt-codex.md" "$STATE/bin/"

ws=$(herdr workspace create --cwd "$STATE" --label "$LABEL" --no-focus)
pane=$(printf '%s' "$ws" | jq -r '.result.root_pane.pane_id')
herdr pane run "$pane" "bash $STATE/bin/loop.sh $INTERVAL 2>&1 | tee -a $STATE/loop.log" > /dev/null
echo "시작: herdr 작업공간 '$LABEL' · ${INTERVAL}초마다 · 로그 $STATE/loop.log · 장부 $STATE/ledger.jsonl"
