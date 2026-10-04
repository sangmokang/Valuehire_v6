#!/bin/bash
# usage: driver.sh WU04 WU03 ...   (각 WU: 사용률확인 → 리뷰 → 검사 → [감사]) 실패 시 즉시 정지
S=$(dirname "$0"); source $S/env.sh; R=$LCR_ROOT; T=$(cd $S/.. && pwd)
log(){ python3 -c "import json,sys,datetime;d=json.loads(sys.argv[1]);d.update(ts=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),pr=int(__import__('os').environ['LCR_PR']),head_sha=__import__('os').environ['LCR_SHA']);open('$R/ledger.jsonl','a').write(json.dumps(d,ensure_ascii=False)+'\n')" "$1"; }
run(){ run1 "$@"; rc=$?; if [ $rc -eq 7 ]; then log "{\"event\":\"${1}_RETRY\",\"wu\":\"$2\"}"; mv "$5" "$5.err1" 2>/dev/null; run1 "$@"; rc=$?; fi; [ $rc -eq 0 ] || { echo STOP_POLL_$rc; exit 5; }; }
run1(){ # kind wid promptfile marker rawfile
  u=$(bash $S/usage.sh); echo "[$2 $1] usage=$u"
  pct=${u%% *}; [[ "$pct" =~ ^[0-9]+$ ]] || { log "{\"event\":\"BLOCKED_CURSOR_UI\",\"wu\":\"$2\",\"why\":\"usage unreadable\"}"; echo STOP_USAGE_UNKNOWN; exit 3; }
  [[ "$u" == *od_disabled=true* ]] || { log "{\"event\":\"BLOCKED_INCLUDED_USAGE\",\"why\":\"on-demand not disabled\"}"; echo STOP_OD; exit 3; }
  [ "$pct" -ge 90 ] && { log "{\"event\":\"BLOCKED_INCLUDED_USAGE\",\"wu\":\"$2\",\"pct\":$pct}"; echo STOP_PCT; exit 3; }
  out=$(bash $S/launch.sh "$3"); echo "$out"; sess=$(echo "$out" | /usr/bin/grep -o 'https://cursor.com/agents/bc-[a-z0-9-]*')
  [ -n "$sess" ] || { log "{\"event\":\"BLOCKED_CURSOR_UI\",\"wu\":\"$2\",\"kind\":\"$1\"}"; echo STOP_LAUNCH; exit 4; }
  log "{\"event\":\"${1}_STARTED\",\"wu\":\"$2\",\"cursor_session\":\"$sess\",\"usage_pct_before\":$pct}"
  bash $S/poll2.sh "$sess" "$4" "$5" 3000; rc=$?
  [ $rc -eq 0 ] || { log "{\"event\":\"${1}_POLL_FAIL\",\"wu\":\"$2\",\"rc\":$rc,\"cursor_session\":\"$sess\"}"; return $rc; }
}
for W in "$@"; do
  if [ "$W" = INTEG ]; then bash $S/integ.sh; run INTEG INTEG $P/integ-prompt.txt INTEG_JSON $P/integ-raw.txt; python3 $T/check_wu.py $P/integ-raw.txt $P/planner.json $P/inventory.tsv INTEG $P/integ.json INTEG_JSON; log "{\"event\":\"INTEG_DONE\",\"check_rc\":$?}"; continue; fi
  if [ "$(/usr/bin/grep -c "<<<WU_JSON" $P/$W-raw.txt 2>/dev/null)" -ge 2 ] 2>/dev/null; then echo "[$W] review exists, skip"; else run WU $W $P/$W-prompt.txt WU_JSON $P/$W-raw.txt; fi
  python3 $T/check_wu.py $P/$W-raw.txt $P/planner.json $P/inventory.tsv $W $P/$W.json; c=$?
  log "{\"event\":\"WU_DONE\",\"wu\":\"$W\",\"check_rc\":$c}"
  [ $c -eq 2 ] && { echo STOP_PARSE; exit 6; }
  need=$(python3 -c "import json;r=json.load(open('$P/$W.json'));print(1 if '$W' in ('WU04','WU05') or any(f.get('severity') in ('S0','S1') for f in r.get('findings',[])) or r.get('confidence')=='low' else 0)")
  if [ "$need" = 1 ]; then
    python3 $T/make_wu_prompt.py audit $P/planner.json $W $P/$W.json > $P/$W-audit-prompt.txt
    run AUDIT $W $P/$W-audit-prompt.txt AUDIT_JSON $P/$W-audit-raw.txt
    python3 $T/check_wu.py $P/$W-audit-raw.txt $P/planner.json $P/inventory.tsv $W $P/$W-audit.json AUDIT_JSON; c=$?
    log "{\"event\":\"AUDIT_DONE\",\"wu\":\"$W\",\"check_rc\":$c}"; [ $c -eq 2 ] && { echo STOP_PARSE_AUDIT; exit 6; }
  fi
done
echo ALL_DONE
