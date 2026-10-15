#!/bin/bash
# usage: rretry.sh <conv_url> <TAG> <out_raw> <gem_js 이름>  — aside repl 로 같은 대화에 코드블록 재출력 요청 → 완료 대기 → 수집
S=$(dirname "$0"); U="$1"; TAG="$2"; O="$3"; GJ="${4:-gem_js_main.sh}"; WIN=${GEM_WIN:-665806760}
[[ "$U" == https://gemini.google.com/app/* && -n "$TAG" && -n "$O" ]] || { echo BAD_ARGS; exit 9; }
MSG="방금 낸 결과 JSON 을 분석은 다시 하지 말고, 같은 내용을 \`\`\`json 코드블록 하나 안에 온전한 JSON 으로 다시 출력하세요. 코드블록 바로 위 줄에 <<<$TAG, 바로 아래 줄에 $TAG>>> 를 쓰세요. 다른 설명은 쓰지 마세요."
B64=$(printf '%s' "$MSG" | base64 | tr -d '\n')
cat > $S/_rr.js <<JS
const t2=(await listBrowserTabs()).find(t=>t.windowId===$WIN&&/gemini\.google\.com/.test(t.url||""));
const p2=await attachBrowserTab(t2.targetId);
await p2.goto('$U'); await sleep(8000);
for(let i=0;i<50;i++){ if(!(await p2.locator('button[aria-label*="중지"]').count())) break; await sleep(2000); }
const n0=await p2.locator('model-response').count();
const ed2=p2.locator('div[aria-label="Gemini 프롬프트 입력"]'); await ed2.click();
await p2.keyboard.insertText(Buffer.from('$B64','base64').toString('utf8')); await sleep(1500);
await p2.locator('button[aria-label="메시지 보내기"]').click();
for(let i=0;i<55;i++){ await sleep(2000); if((await p2.locator('model-response').count())>n0) break; }
console.log('N0 '+n0+' N1 '+(await p2.locator('model-response').count()));
JS
cd /tmp && ~/.local/bin/aside repl --account u2 "$(cat $S/_rr.js)" </dev/null 2>&1 | grep -vE "^\s+at " | tail -3
# 응답 완성까지 대기 후 수집(가려진 탭도 읽힘)
bash $S/$(echo $GJ | sed 's/gem_js/mpoll/;s/mpoll_main.sh/mpoll_main.sh/') "$U" "$TAG" "$O" 1800 >/dev/null 2>&1
echo "rretry_done pre=$(/usr/bin/grep -c @@PRE@@ "$O")"
