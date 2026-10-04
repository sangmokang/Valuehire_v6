#!/bin/bash
S=$(dirname "$0"); source $S/env.sh; R=$LCR_ROOT; T=$(cd $S/.. && pwd)
python3 - <<PY
import json,glob,os
P="$P"; out={}
for w in [f"WU0{i}" for i in range(1,10)]:
    r=json.load(open(f"{P}/{w}.json")); a=f"{P}/{w}-audit.json"
    out[w]={"verdict":r.get("verdict"),"core_flow":str(r.get("core_flow",""))[:600],
      "findings":[{k:f.get(k) for k in ("id","severity","evidence","file_func","condition","minimal_fix")} for f in r.get("findings",[])]}
    if os.path.exists(a):
        x=json.load(open(a)); out[w]["audit"]={"verdict":x.get("verdict"),"new_findings":[{k:f.get(k) for k in ("id","severity","evidence","file_func","condition")} for f in x.get("new_findings",[])]}
json.dump(out,open(f"{P}/wu-summary.json","w"),ensure_ascii=False,indent=1)
PY
python3 $T/make_wu_prompt.py integ $P/planner.json $P/wu-summary.json > $P/integ-prompt.txt
wc -c $P/integ-prompt.txt
