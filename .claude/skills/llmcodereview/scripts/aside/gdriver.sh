#!/bin/bash
# usage: gdriver.sh WU05 WU04 ... INTEG   (ChatGPT, Grok 과 같은 분할·지시문·감사 기준)
S=$(dirname "$0"); source $S/env.sh; R=$LCR_ROOT; T=$(cd $S/.. && pwd); G=$P/gpt
log(){ python3 -c "import json,sys,datetime;d=json.loads(sys.argv[1]);d.update(ts=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),pr=int(__import__('os').environ['LCR_PR']),engine='chatgpt',head_sha=__import__('os').environ['LCR_SHA']);open('$R/ledger.jsonl','a').write(json.dumps(d,ensure_ascii=False)+'\n')" "$1"; }
INS="첨부한 텍스트 파일의 지시를 그대로 수행하세요. 먼저 첨부 끝에 '[첨부 끝 — 파일 N개' 줄과 [누락 검사] 규칙이 보이는지 확인하고, 안 보이면 TRUNCATED 라고만 답하고 멈추세요."
run(){ # kind wid prompt marker raw
  for att in 1 2; do
    out=$(bash $S/glaunch.sh "$3" "$INS"); echo "$out"; conv=$(echo "$out" | /usr/bin/grep -o 'https://chatgpt.com/[^ ]*/c/[a-z0-9-]*')
    [ -n "$conv" ] || { log "{\"event\":\"BLOCKED_CHATGPT_UI\",\"wu\":\"$2\",\"kind\":\"$1\"}"; echo STOP_LAUNCH; exit 4; }
    log "{\"event\":\"${1}_STARTED\",\"wu\":\"$2\",\"conv\":\"$conv\",\"attempt\":$att}"
    bash $S/gpoll2.sh "$conv" "$4" "$5" 3600; rc=$?
    [ $rc -eq 0 ] && return 0
    log "{\"event\":\"${1}_POLL_FAIL\",\"wu\":\"$2\",\"rc\":$rc,\"conv\":\"$conv\"}"
    [ $rc -eq 7 ] || [ $rc -eq 8 ] || { echo STOP_POLL_$rc; exit 5; }
    mv "$5" "$5.err$att"
  done; echo STOP_RETRY_EXHAUSTED; exit 5
}
for W in "$@"; do
  if [ "$W" = INTEG ]; then
    python3 - <<PY
import json,os
P="$P";G="$G";out={}
for w in [f"WU0{i}" for i in range(1,10)]:
    r=json.load(open(f"{G}/{w}.json"));a=f"{G}/{w}-audit.json"
    out[w]={"verdict":r.get("verdict"),"core_flow":str(r.get("core_flow",""))[:600],"findings":[{k:f.get(k) for k in ("id","severity","evidence","file_func","condition","minimal_fix")} for f in r.get("findings",[])]}
    if os.path.exists(a):
        x=json.load(open(a));out[w]["audit"]={"verdict":x.get("verdict"),"new_findings":[{k:f.get(k) for k in ("id","severity","evidence","file_func","condition")} for f in x.get("new_findings",[])]}
json.dump(out,open(f"{G}/wu-summary.json","w"),ensure_ascii=False,indent=1)
PY
    python3 $T/gpt_bundle.py integ $G/wu-summary.json $G/integ-prompt.txt
    run INTEG INTEG $G/integ-prompt.txt INTEG_JSON $G/integ-raw.txt
    python3 $T/check_wu.py $G/integ-raw.txt $P/planner.json $P/inventory.tsv INTEG $G/integ.json INTEG_JSON; c=$?
    python3 $T/check_seen.py $G/integ-prompt.txt $G/integ.json; s=$?
    log "{\"event\":\"INTEG_DONE\",\"check_rc\":$c,\"seen_rc\":$s}"; continue
  fi
  if /usr/bin/grep -q "WU_JSON>>>" $G/$W-raw.txt 2>/dev/null; then echo "[$W] review exists, skip"; else run WU $W $G/$W-prompt.txt WU_JSON $G/$W-raw.txt; fi
  python3 $T/check_wu.py $G/$W-raw.txt $P/planner.json $P/inventory.tsv $W $G/$W.json; c=$?
  [ $c -eq 2 ] && { log "{\"event\":\"WU_PARSE_FAIL\",\"wu\":\"$W\"}"; echo STOP_PARSE; exit 6; }
  python3 $T/check_seen.py $G/$W-prompt.txt $G/$W.json; s=$?
  log "{\"event\":\"WU_DONE\",\"wu\":\"$W\",\"check_rc\":$c,\"seen_rc\":$s}"
  need=$(python3 -c "import json;r=json.load(open('$G/$W.json'));print(1 if '$W' in ('WU04','WU05') or any(f.get('severity') in ('S0','S1') for f in r.get('findings',[])) or r.get('confidence')=='low' else 0)")
  if [ "$need" = 1 ]; then
    python3 $T/gpt_bundle.py audit $W $G/$W.json $G/$W-audit-prompt.txt
    run AUDIT $W $G/$W-audit-prompt.txt AUDIT_JSON $G/$W-audit-raw.txt
    python3 $T/check_wu.py $G/$W-audit-raw.txt $P/planner.json $P/inventory.tsv $W $G/$W-audit.json AUDIT_JSON; c=$?
    python3 $T/check_seen.py $G/$W-audit-prompt.txt $G/$W-audit.json; s=$?
    log "{\"event\":\"AUDIT_DONE\",\"wu\":\"$W\",\"check_rc\":$c,\"seen_rc\":$s}"
  fi
done; echo ALL_DONE
