#!/usr/bin/env bash
# pr-review/install.sh — run.sh 를 launchd 로 주기 실행하게 등록한다 (#133)
#
# 사용: bash scripts/pr-review/install.sh [간격초]   기본 3600(매시간). 하루 한 번은 86400.
#       bash scripts/pr-review/install.sh --uninstall
# run.sh·prompt.md 는 상태 디렉터리 bin/ 으로 복사해 실행한다. 리뷰 중 체크아웃되는 PR 브랜치의
# 코드나, 나중에 지워질 수 있는 워크트리 경로를 launchd 가 실행하지 않게 하기 위해서다.
# 스크립트를 고친 뒤에는 이 설치를 다시 돌려야 반영된다.
set -euo pipefail

LABEL=kr.valueconnect.pr-review
STATE=${PR_REVIEW_STATE:-$HOME/.valuehire-pr-review}
PLIST=$HOME/Library/LaunchAgents/$LABEL.plist
HERE=$(cd "$(dirname "$0")" && pwd)
DOMAIN=gui/$(id -u)

launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null && echo "기존 등록 해제"
if [ "${1:-}" = "--uninstall" ]; then rm -f "$PLIST"; echo "제거 완료"; exit 0; fi

INTERVAL=${1:-3600}
case "$INTERVAL" in ''|*[!0-9]*) echo "간격은 초 단위 숫자: $INTERVAL" >&2; exit 2 ;; esac

for c in git gh jq codex; do command -v "$c" >/dev/null || { echo "필요한 명령 없음: $c" >&2; exit 2; }; done
mkdir -p "$STATE/bin" "$HOME/Library/LaunchAgents"
cp "$HERE/run.sh" "$HERE/prompt.md" "$STATE/bin/"

# launchd 는 로그인 셸의 PATH 를 모른다. 지금 찾은 명령들의 위치를 그대로 넘긴다.
P=""
for c in git gh jq codex node; do
  d=$(dirname "$(command -v "$c")"); case ":$P:" in *":$d:"*) ;; *) P=${P:+$P:}$d ;; esac
done
P=$P:/usr/bin:/bin

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$STATE/bin/run.sh</string></array>
  <key>StartInterval</key><integer>$INTERVAL</integer>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>$P</string>
    <key>PR_REVIEW_STATE</key><string>$STATE</string>
  </dict>
  <key>StandardOutPath</key><string>$STATE/launchd.log</string>
  <key>StandardErrorPath</key><string>$STATE/launchd.log</string>
</dict></plist>
EOF
plutil -lint "$PLIST" >/dev/null
launchctl bootstrap "$DOMAIN" "$PLIST"
echo "등록 완료: $LABEL · ${INTERVAL}초마다 · 로그 $STATE/launchd.log · 장부 $STATE/ledger.jsonl"
