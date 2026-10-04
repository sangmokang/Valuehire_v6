#!/usr/bin/env python3
"""WU 결과 JSON 추출 + 파일 커버리지 대조. usage: check_wu.py <raw> <planner.json> <inventory.tsv> <WUxx> <out.json> [TAG]
종료값 0=PASS(커버리지 충족), 1=GAP, 2=PARSE_FAIL"""
import json, os, re, sys
from pathlib import Path

def _repair(s):
    """화면 렌더링이 지운 역슬래시 복구: 오류 위치 직전 따옴표를 이스케이프(최대 40회)."""
    for _ in range(40):
        try:
            return json.loads(s, strict=False)
        except json.JSONDecodeError as e:
            if "delimiter" not in e.msg:
                return None
            q = s.rfind('"', 0, e.pos)
            if q <= 0 or s[q - 1] == "\\":
                return None
            s = s[:q] + "\\" + s[q:]
    return None

def extract(raw, tag):
    for b in reversed(re.findall(rf"<<<{tag}\s*(.*?)\s*{tag}>>>", raw, re.S)):
        b = b.strip().strip("`")
        try:
            return json.loads(b, strict=False)
        except json.JSONDecodeError:
            r = _repair(b)
            if r is not None:
                r["_repaired"] = True
                return r
    return None

raw, plan_p, inv_p, wid, out = sys.argv[1:6]
tag = sys.argv[6] if len(sys.argv) > 6 else "WU_JSON"
r = extract(Path(raw).read_text(), tag)
if r is None:
    print("PARSE_FAIL"); sys.exit(2)
Path(out).write_text(json.dumps(r, ensure_ascii=False, indent=1))
SHA = os.environ["LCR_SHA"]
gaps = []
if str(r.get("head_sha_checked", "")).strip() != SHA:
    gaps.append(f"SHA {r.get('head_sha_checked')!r}")
if tag == "WU_JSON":
    inv = {l.split("\t")[0]: int(l.split("\t")[1]) + int(l.split("\t")[2]) for l in Path(inv_p).read_text().splitlines()}
    wu = next(w for w in json.load(open(plan_p))["wus"] if w["id"] == wid)
    got = {x["file"]: x.get("changed_lines_read") for x in r.get("files_reviewed", [])}
    for f in wu["files"]:
        if f not in got:
            gaps.append(f"NOT_REVIEWED {f}")
        elif got[f] is None or int(got[f]) < inv[f]:
            gaps.append(f"PARTIAL {f} read={got[f]} changed={inv[f]}")
sev = {}
for f in r.get("findings", []) + r.get("new_findings", []):
    sev[f.get("severity", "?")] = sev.get(f.get("severity", "?"), 0) + 1
print(f"{wid} verdict={r.get('verdict')} findings={sev} tests_exec={len(r.get('tests_executed', []))} conf={r.get('confidence')}")
for f in r.get("findings", []) + r.get("new_findings", []):
    print(f"  [{f.get('severity')}/{f.get('evidence')}] {f.get('id')} {f.get('file_func','')[:90]} :: {str(f.get('condition',''))[:120]}")
for x in r.get("reclassified", []):
    print(f"  RECLASS {x.get('id')} -> {x.get('status')} :: {str(x.get('reason',''))[:140]}")
for b in r.get("boundaries", []):
    print(f"  {b.get('id')} {b.get('status')} :: {str(b.get('note',''))[:120]}")
for t in r.get("tests_executed", []):
    if not isinstance(t, dict): t = {"cmd": str(t)}
    print(f"  TEST exit={t.get('exit')} {str(t.get('cmd',''))[:90]} -> {str(t.get('summary',''))[:60]}")
if gaps:
    print("GAP"); [print("  -", g) for g in gaps]; sys.exit(1)
print("COVERAGE_OK"); sys.exit(0)
