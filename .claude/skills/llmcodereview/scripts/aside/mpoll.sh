#!/bin/bash
# usage: gpoll2.sh <conv_url> <marker> <outfile> [maxsec]
# 종료값: 0 DONE / 2 TIMEOUT / 3 USAGE / 7 응답 실패(재시도 소진) / 8 TRUNCATED
S=$(dirname "$0"); source $S/env.sh; U="$1"; M="$2"; O="$3"; MAX=${4:-3600}; t0=$(date +%s)
dc=0; dead=0; retries=0
printf '%s' 'location.href' > $S/_gh.js
reopen(){ osascript -e "tell application \"Aside\" to set URL of (tab id $GEM_TAB of window id $ASIDE_WIN) to \"$U\""; sleep 15; }
while :; do
  [[ "$(bash $S/gem_js.sh $S/_gh.js)" == "$U"* ]] || reopen
  bash $S/gem_js.sh $S/mlast.js > "$O.tmp" 2>&1 && mv "$O.tmp" "$O"
  stop=$(head -1 "$O"); disc=0; /usr/bin/grep -q "연결이 해제" "$O" && disc=1
  if /usr/bin/grep -qiE "사용량 한도|한도에 도달|usage limit|reached your limit|플랜 업그레이드" "$O"; then echo USAGE_WARNING; exit 3; fi
  if [ "$stop" = STOP=false ] && /usr/bin/grep -q -- "$M>>>" "$O"; then echo DONE; exit 0; fi
  if [ "$stop" = STOP=false ] && /usr/bin/grep -q TRUNCATED "$O"; then echo TRUNCATED; exit 8; fi
  # ① 생성 중인데 화면 연결만 끊김: 3분(6회)마다 다시 열기
  if [ $disc = 1 ] && [ "$stop" = STOP=true ]; then dc=$((dc+1)); [ $dc -ge 6 ] && { echo "resync $(date +%T)"; reopen; dc=0; continue; }; else dc=0; fi
  # ② 생성이 멈췄는데 결과 없음(연결 해제·오류 문구): 2분(4회) 지속 시 같은 대화에서 재시도 버튼
  if [ "$stop" = STOP=false ] && { [ $disc = 1 ] || /usr/bin/grep -qE "문제가 발생|Something went wrong|오류가 발생" "$O"; }; then
    dead=$((dead+1))
    if [ $dead -ge 4 ]; then
      [ $retries -ge 2 ] && { echo AGENT_ERROR_RETRY_EXHAUSTED; exit 7; }
      reopen
      r=$(printf '%s' 'var b=[].slice.call(document.querySelectorAll("button")).filter(function(x){var t=((x.getAttribute("aria-label")||"")+" "+(x.innerText||"")).trim();return /다시 시도|재생성|Retry|Regenerate/.test(t)&&x.getBoundingClientRect().width>0});b.length?(b[b.length-1].click(),"RETRY_CLICKED"):"NO_RETRY_BTN"' > $S/_rt.js; bash $S/gem_js.sh $S/_rt.js)
      retries=$((retries+1)); dead=0; echo "retry#$retries $r $(date +%T)"
      [ "$r" = NO_RETRY_BTN ] && [ $retries -ge 2 ] && { echo AGENT_ERROR_NO_RETRY_BTN; exit 7; }
    fi
  else dead=0; fi
  [ $(( $(date +%s) - t0 )) -gt $MAX ] && { echo TIMEOUT; exit 2; }
  sleep 30
done
