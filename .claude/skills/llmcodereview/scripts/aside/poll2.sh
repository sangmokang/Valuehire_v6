#!/bin/bash
# usage: poll2.sh <session_url> <marker> <outfile> [maxsec]
S=$(dirname "$0"); source $S/env.sh; U="$1"; M="$2"; O="$3"; MAX=${4:-2400}; t0=$(date +%s)
echo 'document.body.innerText' > $S/_all.js
while :; do
  cur=$(bash $S/aside_js.sh $S/h.js)
  if [[ "$cur" != "$U"* ]]; then osascript -e "tell application \"Aside\" to set URL of (tab id $CURSOR_TAB of window id $ASIDE_WIN) to \"$U\""; sleep 10; fi
  bash $S/aside_js.sh $S/_all.js > "$O.tmp" 2>&1 && mv "$O.tmp" "$O"
  n=$(/usr/bin/grep -c -- "<<<$M" "$O")
  if /usr/bin/grep -qiE "included usage|on-demand spending|upgrade to|out of usage|usage limit|pay-as-you-go|purchase credits" "$O"; then echo "USAGE_WARNING n=$n"; exit 3; fi
  if /usr/bin/grep -q -- "Agent encountered an error" "$O"; then echo "AGENT_ERROR n=$n"; exit 7; fi
  if [ "$n" -ge 2 ] && /usr/bin/grep -q -- "Worked for" "$O"; then echo "DONE n=$n"; exit 0; fi
  [ $(( $(date +%s) - t0 )) -gt $MAX ] && { echo "TIMEOUT n=$n"; tail -c 1500 "$O"; exit 2; }
  sleep 30
done
