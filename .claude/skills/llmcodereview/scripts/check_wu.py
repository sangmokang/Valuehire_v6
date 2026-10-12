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
    if not wu.get("files"):
        gaps.append("WU_FILES_EMPTY")
    got = {x["file"]: x.get("changed_lines_read") for x in r.get("files_reviewed", [])}
    for f in wu["files"]:
        if f not in got:
            gaps.append(f"NOT_REVIEWED {f}")
        elif got[f] is None or int(got[f]) < inv[f]:
            gaps.append(f"PARTIAL {f} read={got[f]} changed={inv[f]}")
elif tag == "INTEG_JSON":
    expected = [b["id"] for b in json.load(open(plan_p)).get("cross_wu_boundaries", [])]
    boundaries = r.get("boundaries", [])
    actual = [b.get("id") for b in boundaries]
    if not expected:
        gaps.append("NO_BOUNDARIES")
    if len(actual) != len(set(actual)):
        gaps.append("DUP_BOUNDARY")
    for boundary_id in expected:
        if boundary_id not in actual:
            gaps.append(f"MISSING_BOUNDARY {boundary_id}")
    for boundary_id in actual:
        if boundary_id not in expected:
            gaps.append(f"EXTRA_BOUNDARY {boundary_id}")
    for b in boundaries:
        status = str(b.get("status", "")).strip()
        if status == "NOT_CHECKED":
            gaps.append(f"BOUNDARY_NOT_CHECKED {b.get('id', '?')}")
        elif status not in {"VERIFIED", "ISSUE"}:
            gaps.append(f"BOUNDARY_BAD_STATUS {b.get('id', '?')} {status!r}")
        if not str(b.get("evidence", "")).strip():
            gaps.append(f"BOUNDARY_NO_EVIDENCE {b.get('id', '?')}")
elif tag == "AUDIT_JSON":
    reviewer_path = Path(out).with_name(f"{wid}.json")
    if not reviewer_path.is_file():
        gaps.append("REVIEWER_RESULT_MISSING")
    else:
        reviewer = json.loads(reviewer_path.read_text())
        if str(reviewer.get("head_sha_checked", "")).strip() != SHA:
            gaps.append("REVIEWER_SHA_MISMATCH")
        reviewer_ids = [f.get("id") for f in reviewer.get("findings", [])]
        actual = [f.get("id") for f in r.get("reclassified", [])]
        if len(actual) != len(set(actual)):
            gaps.append("DUP_RECLASSIFIED")
        for finding_id in reviewer_ids:
            if finding_id not in actual:
                gaps.append(f"MISSING_RECLASSIFIED {finding_id}")
        for finding_id in actual:
            if finding_id not in reviewer_ids:
                gaps.append(f"EXTRA_RECLASSIFIED {finding_id}")
        for item in r.get("reclassified", []):
            if item.get("status") not in {"CONFIRMED", "REFUTED", "CONDITIONAL", "NEEDS_MORE_EVIDENCE"} or not str(item.get("reason", "")).strip():
                gaps.append(f"BAD_RECLASSIFICATION {item.get('id')}")
    attempts = r.get("attempts", [])
    if len(attempts) < 3 or any(not str(a.get("attack", "")).strip() or not str(a.get("result", "")).strip() for a in attempts):
        gaps.append("AUDIT_ATTEMPTS_INCOMPLETE")
sev = {}
for f in r.get("findings", []) + r.get("new_findings", []):
    required = ("id", "severity", "evidence", "file_func", "condition", "impact", "counter_evidence", "minimal_fix", "verify")
    if not isinstance(f, dict) or any(not str(f.get(k, "")).strip() for k in required) or f.get("severity") not in {"S0", "S1", "S2", "S3"} or f.get("evidence") not in {"REPRODUCED", "NOT_TESTED", "NOT_REPRODUCIBLE", "UNRESOLVED"}:
        gaps.append(f"FINDING_INVALID {f.get('id', '?') if isinstance(f, dict) else '?'}")
        continue
    sev[f.get("severity", "?")] = sev.get(f.get("severity", "?"), 0) + 1
print(f"{wid} verdict={r.get('verdict')} findings={sev} tests_exec={len(r.get('tests_executed', []))} conf={r.get('confidence')}")
for f in r.get("findings", []) + r.get("new_findings", []):
    if not isinstance(f, dict):
        continue
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
