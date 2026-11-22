#!/bin/bash
# usage: launch.sh <prompt.txt>  -> prints session URL. 저장소/모델이 기대값이 아니면 BLOCKED_CURSOR_UI
S=$(dirname "$0"); source $S/env.sh
osascript -e "tell application \"Aside\" to set URL of (tab id $CURSOR_TAB of window id $ASIDE_WIN) to \"https://cursor.com/agents\""
for i in $(seq 1 20); do sleep 2
  echo 'var r=document.querySelector("button[aria-label=\"sangmokang/Valuehire_v6\"]"); var m=[].slice.call(document.querySelectorAll("button")).filter(function(b){return /^Grok [0-9]/.test(b.innerText.trim())}); (location.pathname=="/agents" && r && m.length && document.querySelector("div[contenteditable=true]")) ? "READY model="+m[0].innerText.trim() : "WAIT"' > $S/_rdy.js
  st=$(bash $S/aside_js.sh $S/_rdy.js); [[ "$st" == READY* ]] && break; done
echo "$st"; [[ "$st" == READY* ]] || { echo BLOCKED_CURSOR_UI; exit 4; }
bash $S/insert_prompt.sh "$1"; sleep 2
bash $S/aside_js.sh $S/send.js
for i in $(seq 1 15); do sleep 2; u=$(bash $S/aside_js.sh $S/h.js); [[ "$u" == *"/agents/bc-"* ]] && { echo "SESSION $u"; exit 0; }; done
echo "NO_SESSION_URL $u"; exit 5
