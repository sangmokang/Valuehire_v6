#!/bin/bash
# usage: glaunch.sh <prompt.txt> <short_instruction>  -> prints CONV <url>
S=$(dirname "$0"); source $S/env.sh; W=$ASIDE_WIN; T=${GPT_TAB:?}; PROJ="$GPT_PROJECT_URL"
js(){ printf '%s' "$1" > $S/_q.js; bash $S/gpt_js.sh $S/_q.js; }
osascript -e "tell application \"Aside\" to set URL of (tab id $T of window id $W) to \"$PROJ\""
for i in $(seq 1 20); do sleep 2; r=$(js 'var b=[].slice.call(document.querySelectorAll("button[aria-label=\"파일 등 추가\"]")).filter(function(e){return e.getBoundingClientRect().width>0})[0]; (b&&location.pathname.indexOf("/project")>0)?"READY":"WAIT"'); [ "$r" = READY ] && break; done
[ "$r" = READY ] || { echo BLOCKED_CHATGPT_UI; exit 4; }
ED='var el=[].slice.call(document.querySelectorAll("[contenteditable=true]")).filter(function(e){return e.getBoundingClientRect().width>0})[0];'
chip(){ js "$ED"'el.innerHTML.indexOf("app-mention-name=")>=0&&el.innerHTML.indexOf("github")>=0?"CHIP_OK":"NO_CHIP"'; }
pick='var c=[].slice.call(document.querySelectorAll("button")).filter(function(e){var t=(e.innerText||e.textContent||"").trim();return t.indexOf("GitHub")==0&&/Triage/.test(t)});'
# 가려진 탭은 팝업을 그리지 않는다 → 대상 탭을 잠깐 활성 탭으로, 끝나면 원래 탭 복원(앱 전환·마우스 없음)
PREV_IDX=$(osascript -e "tell application \"Aside\" to get active tab index of window id $W")
focus_tab(){ osascript -e "tell application \"Aside\"
set w to window id $W
set n to 0
repeat with t in tabs of w
set n to n + 1
if id of t is $T then set active tab index of w to n
end repeat
end tell"; sleep 1.5; }
restore_tab(){ [ -n "$PREV_IDX" ] && osascript -e "tell application \"Aside\" to set active tab index of window id $W to $PREV_IDX" 2>/dev/null; }
trap restore_tab EXIT
focus_tab
# 1) 기본: @GitHub 입력 -> 항목 선택 (화면 비점유)
sleep 3  # 준비 직후 입력창이 한 번 더 다시 그려진다
for i in 1 2 3; do
  js "$ED"'el.innerHTML="<p><br></p>";el.focus();document.execCommand("insertText",false,"@GitHub");"t"' >/dev/null; sleep 2
  js "$pick"'c.length?(c[0].click(),"C"):"N"' >/dev/null; sleep 1.5
  [ "$(chip)" = CHIP_OK ] && break
  sleep 2
done
# 2) 대체: 실제 클릭 (전면 앱·로딩·결과 확인, 3회)
if [ "$(chip)" != CHIP_OK ]; then
  FRONT=$(osascript -e 'tell application "System Events" to get name of first process whose frontmost is true')
  for i in 1 2 3; do
    until [ "$(js 'document.readyState')" = complete ]; do sleep 1; done
    osascript -e "tell application \"Aside\"
activate
set w to window id $W
set n to 0
repeat with t in tabs of w
set n to n + 1
if id of t is $T then set active tab index of w to n
end repeat
set index of w to 1
end tell"; sleep 1.5
    [ "$(osascript -e 'tell application "System Events" to get name of first process whose frontmost is true')" = Aside ] || { echo "front_not_aside try=$i"; continue; }
    pos=$(js 'var b=[].slice.call(document.querySelectorAll("button[aria-label="파일 등 추가"]")).filter(function(e){return e.getBoundingClientRect().width>0})[0];var r=b.getBoundingClientRect();(window.screenX+Math.round(r.left+r.width/2))+","+(window.screenY+window.outerHeight-window.innerHeight+Math.round(r.top+r.height/2))')
    cliclick c:$pos; sleep 2
    [ "$(js "$pick"'c.length?"OPEN":"CLOSED"')" = OPEN ] || { echo "menu_closed try=$i"; continue; }
    js "$pick"'c[0].click();"C"' >/dev/null; sleep 1.5
    [ "$(chip)" = CHIP_OK ] && break
  done
  osascript -e "tell application "$FRONT" to activate" 2>/dev/null
fi
restore_tab; c=$(chip); echo "$c"; [ "$c" = CHIP_OK ] || { echo BLOCKED_CHATGPT_UI_NO_CHIP; exit 4; }
B=$(base64 < "$1" | tr -d '\n'); IB=$(printf '%s' "$2" | base64 | tr -d '\n')
cat > $S/_p.js <<JS
(function(){var t=decodeURIComponent(escape(atob("$B")));var ins=decodeURIComponent(escape(atob("$IB")));var el=[].slice.call(document.querySelectorAll('[contenteditable=true]')).filter(function(e){return e.getBoundingClientRect().width>0})[0];el.focus();var s=window.getSelection();s.selectAllChildren(el);s.collapseToEnd();var dt=new DataTransfer();dt.setData('text/plain',t);el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));s.selectAllChildren(el);s.collapseToEnd();document.execCommand("insertText",false," "+ins);return "in="+t.length;})()
JS
bash $S/gpt_js.sh $S/_p.js; sleep 4
att=$(js 'document.querySelector("button[aria-label=\"붙여넣은 텍스트 첨부 제거\"]")?"ATT_OK":"NO_ATT"'); echo "$att"
[ "$att" = ATT_OK ] || { echo BLOCKED_CHATGPT_UI_NO_ATTACH; exit 4; }
for i in $(seq 1 15); do r=$(js 'var b=document.querySelector("button[aria-label=\"보내기\"]");b&&!b.disabled?(b.click(),"SENT"):"NO_SEND"'); [ "$r" = SENT ] && break; sleep 2; done; echo "$r"
for i in $(seq 1 15); do sleep 2; u=$(js 'location.href'); [[ "$u" == *"/c/"* ]] && { echo "CONV $u"; exit 0; }; done
echo NO_CONV_URL; exit 5
