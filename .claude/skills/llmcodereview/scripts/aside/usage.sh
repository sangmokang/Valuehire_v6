#!/bin/bash
# Cursor Models 포함 사용률(%) 출력. 읽기 실패 시 UNKNOWN
S=$(dirname "$0"); source $S/env.sh
osascript -e "tell application \"Aside\" to set URL of (tab id $CURSOR_TAB of window id $ASIDE_WIN) to \"https://cursor.com/dashboard/spending\""
for i in $(seq 1 12); do sleep 3
 echo 'var t=document.body.innerText; var m=t.match(/Cursor Models[^\n]*\n[^\n]*?(\d+)% used/); var od=/On-demand spending is currently disabled/.test(t); m ? (m[1]+" od_disabled="+od) : "WAIT"' > $S/_u.js
 r=$(bash $S/aside_js.sh $S/_u.js); [[ "$r" != WAIT ]] && { echo "$r"; exit 0; }; done; echo UNKNOWN