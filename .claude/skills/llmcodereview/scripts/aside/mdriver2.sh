#!/bin/bash
# usage: mdriver.sh WU05 WU04 ... INTEG  (Gemini, Grok 과 같은 분할·지시문)
S=$(dirname "$0"); R=/Users/kangsangmo/Desktop/Valuehire_v6/private-reviews/cursor-pr-review; P=$R/pr109; M=$P/gemini
log(){ python3 -c "import json,sys,datetime;d=json.loads(sys.argv[1]);d.update(ts=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),pr=109,engine='gemini',head_sha='6ce1e6aeffb92e035081a1743780591408a2cd0e');open('$R/ledger.jsonl','a').write(json.dumps(d,ensure_ascii=False)+'\n')" "$1"; }
run(){ # kind wid prompt marker raw
  for att in 1 2; do
    out=$(bash $S/rlaunch.sh "$3"); echo "$out"; conv=$(echo "$out" | /usr/bin/grep -o 'https://gemini.google.com/app/[a-z0-9]*')
    [ -n "$conv" ] || { log "{\"event\":\"BLOCKED_GEMINI_UI\",\"wu\":\"$2\"}"; echo STOP_LAUNCH; exit 4; }
    log "{\"event\":\"${1}_STARTED\",\"wu\":\"$2\",\"conv\":\"$conv\",\"attempt\":$att}"
    bash $S/${MPOLL:-mpoll.sh} "$conv" "$4" "$5" 3600; rc=$?
    [ $rc -eq 0 ] && return 0
    log "{\"event\":\"${1}_POLL_FAIL\",\"wu\":\"$2\",\"rc\":$rc}"
    [ $rc -eq 7 ] || [ $rc -eq 8 ] || { echo STOP_POLL_$rc; exit 5; }
    mv "$5" "$5.err$att"
  done; echo STOP_RETRY_EXHAUSTED; exit 5
}
check(){ # raw wid out tag key
  python3 $R/tools/check_wu.py "$1" $P/planner.json $P/inventory.tsv $2 "$3" $4; c=$?
  if [ $c -eq 2 ]; then python3 $R/tools/recover_codeblock.py "$1" $4 $5 "$1.recovered" && { python3 $R/tools/check_wu.py "$1.recovered" $P/planner.json $P/inventory.tsv $2 "$3" $4; c=$?; log "{\"event\":\"RECOVERED_FROM_CODEBLOCK\",\"wu\":\"$2\"}"; }; fi
  return $c
}
for W in "$@"; do
  if [ "$W" = INTEG ]; then
    python3 - <<PY
import json,os
M="$M";out={}
for w in [f"WU0{i}" for i in range(1,10)]:
    p=f"{M}/{w}.json"
    if not os.path.exists(p): out[w]={"verdict":"MISSING"}; continue
    r=json.load(open(p));a=f"{M}/{w}-audit.json"
    out[w]={"verdict":r.get("verdict"),"core_flow":str(r.get("core_flow",""))[:600],"findings":[{k:f.get(k) for k in ("id","severity","evidence","file_func","condition","minimal_fix")} for f in r.get("findings",[])]}
    if os.path.exists(a):
        x=json.load(open(a));out[w]["audit"]={"verdict":x.get("verdict"),"new_findings":[{k:f.get(k) for k in ("id","severity","evidence","file_func","condition")} for f in x.get("new_findings",[])]}
json.dump(out,open(f"{M}/wu-summary.json","w"),ensure_ascii=False,indent=1)
PY
    python3 $R/tools/gpt_bundle.py integ $M/wu-summary.json $M/integ-prompt.txt
    python3 - "$M/integ-prompt.txt" <<'PY'
import re,sys;p=sys.argv[1];t=open(p).read()
t=re.sub(r"- GitHub 플러그인으로 .*?첨부만으로 진행하세요\.\n","- 이 대화에서는 GitHub·저장소에 접근할 수 없습니다. 아래 첨부 원문만으로 판단하고, 첨부 밖 내용은 '첨부 밖 — 확인 불가'로 적으세요.\n",t,flags=re.S).replace("(필요하면 GitHub 조회)","")
open(p,"w").write(t)
PY
    run INTEG INTEG $M/integ-prompt.txt INTEG_JSON $M/integ-raw.txt
    check $M/integ-raw.txt INTEG $M/integ.json INTEG_JSON boundaries; c=$?
    python3 $R/tools/check_seen.py $M/integ-prompt.txt $M/integ.json; s=$?
    log "{\"event\":\"INTEG_DONE\",\"check_rc\":$c,\"seen_rc\":$s}"; continue
  fi
  if /usr/bin/grep -q "WU_JSON>>>" $M/$W-raw.txt 2>/dev/null; then echo "[$W] exists, skip"; else run WU $W $M/$W-prompt.txt WU_JSON $M/$W-raw.txt; fi
  check $M/$W-raw.txt $W $M/$W.json WU_JSON verdict; c=$?
  [ $c -eq 2 ] && { log "{\"event\":\"WU_PARSE_FAIL\",\"wu\":\"$W\"}"; echo "PARSE_FAIL $W (continue)"; continue; }
  python3 $R/tools/check_seen.py $M/$W-prompt.txt $M/$W.json; s=$?
  log "{\"event\":\"WU_DONE\",\"wu\":\"$W\",\"check_rc\":$c,\"seen_rc\":$s}"
done; echo ALL_DONE
