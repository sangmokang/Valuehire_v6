#!/usr/bin/env python3
"""Planner JSON 을 diff 인벤토리와 독립 대조한다. 종료값 0=PASS, 1=FAIL, 2=파싱 불가."""
import json, os, re, sys
from pathlib import Path

def extract(raw: str, tag: str):
    blocks = re.findall(rf"<<<{tag}\s*(.*?)\s*{tag}>>>", raw, re.S)
    for b in reversed(blocks):  # 마지막 블록이 모델 출력(첫 블록은 지시문 원문)
        b = b.strip().strip("`")
        try:
            return json.loads(b, strict=False)
        except json.JSONDecodeError:
            r = _repair(b)
            if r is not None:
                r["_repaired"] = True
                return r
    return None

def _repair(s):
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

def main(raw_path, inv_path, out_path):
    plan = extract(Path(raw_path).read_text(), "PLANNER_JSON")
    if plan is None:
        print("PARSE_FAIL"); return 2
    Path(out_path).write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    inv = {}
    for line in Path(inv_path).read_text().splitlines():
        f, a, d = line.split("\t"); inv[f] = (int(a), int(d))
    problems = []
    if plan.get("head_sha_checked", "").strip() != os.environ["LCR_SHA"]:
        problems.append(f"head_sha_checked={plan.get('head_sha_checked')!r}")
    ledger = plan.get("coverage_ledger", [])
    wu_ids = {w["id"] for w in plan.get("wus", [])}
    seen = {}
    for row in ledger:
        seen.setdefault(row["file"], []).append(row.get("primary_wu"))
    for f in inv:
        if f not in seen: problems.append(f"MISSING {f}")
        elif len(seen[f]) != 1: problems.append(f"DUP_PRIMARY {f} {seen[f]}")
        elif seen[f][0] not in wu_ids: problems.append(f"UNKNOWN_WU {f} {seen[f][0]}")
    for f in seen:
        if f not in inv: problems.append(f"EXTRA {f}")
    for row in ledger:
        if row["file"] in inv and (row.get("added"), row.get("deleted")) != inv[row["file"]]:
            problems.append(f"LINES {row['file']} plan={row.get('added')}/{row.get('deleted')} diff={inv[row['file']]}")
    wu_files = {f for w in plan.get("wus", []) for f in w.get("files", [])}
    for f in inv:
        if f not in wu_files: problems.append(f"NOT_IN_WU_FILES {f}")
    print(f"diff_files={len(inv)} ledger_unique={len(seen)} wus={len(wu_ids)}")
    for w in plan.get("wus", []):
        print(f"  {w['id']} {w.get('risk')} lines={w.get('changed_lines')} files={len(w.get('files',[]))} auditor={w.get('needs_auditor')} :: {w.get('title')}")
    if problems:
        print("FAIL"); [print("  -", p) for p in problems]; return 1
    print("PASS"); return 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
