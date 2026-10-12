#!/usr/bin/env python3
"""ChatGPT 응답의 bundle_files_seen 을 첨부 원문 줄 수와 대조. usage: check_seen.py <prompt.txt> <result.json>"""
import json, re, sys
want = {m.group(1): int(m.group(2)) for m in re.finditer(r"===== END FILE: (.+?) \(last line (\d+)\) =====", open(sys.argv[1]).read())}
r = json.load(open(sys.argv[2]))
got = {x["file"]: x.get("last_line_seen") for x in r.get("bundle_files_seen", [])}
bad = [f"{f} want={n} got={got.get(f)}" for f, n in want.items() if got.get(f) != n]
bad += [f"{f} nonpositive_last_line={n}" for f, n in want.items() if n <= 0]
bad += [f"EXTRA_SEEN {f}" for f in got if f not in want]
if not want:
    bad.append("NO_BUNDLE_FILES")
seen_ok = sum(1 for f, n in want.items() if got.get(f) == n and n > 0)
print(f"bundle files={len(want)} seen_ok={seen_ok}")
if bad:
    print("SEEN_GAP"); [print("  -", b) for b in bad]; sys.exit(1)
print("SEEN_OK")
