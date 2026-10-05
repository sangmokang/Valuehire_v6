#!/bin/bash
# usage: rlaunch.sh <prompt.txt>  -> CONV <url>   (Aside 정식 통로: aside repl, Playwright 진짜 입력. 창이 가려져도 동작 목표)
S=$(dirname "$0"); P="$1"; WIN=${GEM_WIN:-665807174}
B64=$(base64 < "$P" | tr -d '\n')
want=$(python3 -c "t=open('$P').read();print(len(t)-t.count(chr(10)))")
cat > $S/_r.js <<JS
const t1=(await listBrowserTabs()).find(t=>t.windowId===$WIN&&/gemini\.google\.com/.test(t.url||""));
if(!t1){console.log('NO_TAB');} else {
const p1=await attachBrowserTab(t1.targetId);
await p1.goto('https://gemini.google.com/app');
const ed1=p1.locator('div[aria-label="Gemini 프롬프트 입력"]');
await ed1.waitFor({timeout:30000}); await sleep(3000);
console.log('vis', await p1.evaluate(()=>document.visibilityState));
const txt1=Buffer.from('$B64','base64').toString('utf8');
await ed1.click(); await p1.keyboard.insertText(txt1); await sleep(3000);
const len1=await ed1.evaluate(e=>e.textContent.length);
console.log('len '+len1+' want $want');
if(String(len1)!=='$want'){console.log('MISMATCH');} else {
  await p1.locator('button[aria-label="메시지 보내기"]').click();
  for(let i=0;i<40;i++){ await sleep(2000); if(/\/app\/[a-z0-9]+/.test(p1.url())) break; }
  console.log('CONV '+p1.url());
}}
JS
cd /tmp && ~/.local/bin/aside repl --account u2 "$(cat $S/_r.js)" </dev/null 2>&1 | grep -vE "^\s+at " | tail -12
