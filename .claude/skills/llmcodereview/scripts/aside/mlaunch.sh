#!/bin/bash
# usage: mlaunch.sh <prompt.txt> -> prints CONV <url>  (Gemini, insertText, 길이 정확 일치 확인)
S=$(dirname "$0"); W=665807174; T=665807175
js(){ printf '%s' "$1" > $S/_mq.js; bash $S/gem_js.sh $S/_mq.js; }
osascript -e "tell application \"Aside\" to set URL of (tab id $T of window id $W) to \"https://gemini.google.com/app\""
for i in $(seq 1 20); do sleep 2; r=$(js 'var el=document.querySelector("div[aria-label=\"Gemini 프롬프트 입력\"]");(el&&location.pathname=="/app")?"READY":"WAIT"'); [ "$r" = READY ] && break; done
[ "$r" = READY ] || { echo BLOCKED_GEMINI_UI; exit 4; }
sleep 3
B=$(base64 < "$1" | tr -d '\n')
cat > $S/_mins.js <<JS
(function(){var t=decodeURIComponent(escape(atob("$B")));var el=document.querySelector('div[aria-label="Gemini 프롬프트 입력"]');el.focus();document.execCommand("insertText",false,t);return String(el.textContent.length);})()
JS
got=$(bash $S/gem_js.sh $S/_mins.js); want=$(python3 -c "t=open('$1').read();print(len(t)-t.count(chr(10)))")
echo "len got=$got want=$want"; [ "$got" = "$want" ] || { echo BLOCKED_GEMINI_INPUT_MISMATCH; exit 4; }
sleep 3; got2=$(js 'String(document.querySelector("div[aria-label=\"Gemini 프롬프트 입력\"]").textContent.length)'); vis=$(js 'document.visibilityState'); echo "recheck=$got2 vis=$vis"
[ "$got2" = "$want" ] || { echo BLOCKED_GEMINI_HIDDEN_INPUT_DROPPED; exit 4; }
for wv in $(seq 1 120); do v=$(js 'document.visibilityState'); [ "$v" = visible ] && break; [ $wv = 1 ] && echo "waiting_visible"; sleep 5; done; [ "$v" = visible ] || { echo BLOCKED_GEMINI_WINDOW_HIDDEN; exit 4; }
for i in $(seq 1 15); do r=$(js 'var b=[].slice.call(document.querySelectorAll("button")).filter(function(x){return /메시지 보내기/.test(x.getAttribute("aria-label")||"")})[0];b&&b.getAttribute("aria-disabled")!="true"&&!b.disabled?(b.click(),"SENT"):"NO_SEND"'); [ "$r" = SENT ] && break; sleep 2; done; echo "$r"
for i in $(seq 1 30); do sleep 2; u=$(js 'location.href'); [[ "$u" == *"/app/"* ]] && { echo "CONV $u"; exit 0; }; done
echo NO_CONV_URL; exit 5
