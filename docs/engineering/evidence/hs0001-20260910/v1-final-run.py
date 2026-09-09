#!/usr/bin/env python3
"""V1 final independent verifier runner. Records command, UTC time, exit code, full stdout/stderr
as JSON text fields (trailing whitespace preserved). Usage: v1-final-run.py <label> <cwd> -- <cmd...>"""
import json, os, subprocess, sys, datetime, hashlib, pathlib
label, cwd = sys.argv[1], sys.argv[2]
assert sys.argv[3] == "--"
cmd = sys.argv[4:]
env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in {"BASH_ENV", "ENV"}}
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
p = subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)
ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
rec = {"label": label, "command": cmd, "cwd": cwd, "started": started, "ended": ended,
       "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr,
       "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=os.environ.get("V1_REPO", cwd), text=True, capture_output=True).stdout.strip()}
out = pathlib.Path(os.environ.get("V1_OUT", "artifacts/hs-next-20260910")) / f"v1-final-{label}.json"
out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"[{label}] exit={p.returncode} started={started} -> {out}")
print(p.stdout[-3000:])
if p.stderr: print("STDERR:", p.stderr[-2000:])
sys.exit(0)
