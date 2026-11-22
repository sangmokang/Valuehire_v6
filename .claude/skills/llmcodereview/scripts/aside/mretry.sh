#!/bin/bash
# usage: mretry.sh <conv_url> <TAG> <out_raw>  — 같은 대화에 '코드블록으로 재출력' 요청 후 수집
S=$(dirname "$0"); U="$1"; TAG="$2"; O="$3"
[[ "$U" == https://gemini.google.com/app/* && -n "$TAG" && -n "$O" ]] || { echo "BAD_ARGS"; exit 9; }
js(){ printf '%s' "$1" > $S/_rq.js; bash $S/gem_js.sh $S/_rq.js; }
osascript -e "tell application \"Aside\" to set URL of (tab id 665807175 of window id 665807174) to \"$U\""; sleep 12
# 생성이 끝날 때까지 대기
for i in $(seq 1 300); do st=$(js 'String(!!document.querySelector("button[aria-label*=\"중지\"]"))'); [ "$st" = false ] && break; sleep 10; done
n0=$(js 'String(document.querySelectorAll("model-response").length)')
MSG="방금 낸 결과 JSON 을 분석은 다시 하지 말고, 같은 내용을 \`\`\`json 코드블록 하나 안에 온전한 JSON 으로 다시 출력하세요. 코드블록 바로 위 줄에 <<<$TAG, 바로 아래 줄에 $TAG>>> 를 쓰세요. 다른 설명은 쓰지 마세요."
B=$(printf '%s' "$MSG" | base64 | tr -d '\n')
js "var el=document.querySelector('div[aria-label=\"Gemini 프롬프트 입력\"]');el.focus();document.execCommand('insertText',false,decodeURIComponent(escape(atob('$B'))));String(el.textContent.length)" >/dev/null; sleep 2
for wv in $(seq 1 120); do v=$(js 'document.visibilityState'); [ "$v" = visible ] && break; [ $wv = 1 ] && echo "waiting_visible"; sleep 5; done; [ "$v" = visible ] || { echo BLOCKED_GEMINI_WINDOW_HIDDEN; exit 4; }
js 'var b=[].slice.call(document.querySelectorAll("button")).filter(function(x){return /메시지 보내기/.test(x.getAttribute("aria-label")||"")})[0];b.click();"S"' >/dev/null
for i in $(seq 1 120); do sleep 6; st=$(js 'String(!!document.querySelector("button[aria-label*=\"중지\"]"))+"|"+document.querySelectorAll("model-response").length'); [ "$st" = "false|$((n0+1))" ] && break; done
bash $S/gem_js.sh $S/mlast.js > "$O"; echo "retry_done $st pre=$(/usr/bin/grep -c @@PRE@@ "$O")"
