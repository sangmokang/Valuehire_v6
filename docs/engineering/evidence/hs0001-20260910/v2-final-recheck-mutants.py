#!/usr/bin/env python3
"""V2 final recheck from V1 final: product-side fault injection in isolated mkdtemp copies. Tests untouched.
Each mutant: fresh copy, mutation diff recorded, new pytest (8) run with the original venv's
python, full output + rc + target sha256 before/after preserved in v2-final-recheck-mutants-evidence.json."""
import datetime, difflib, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile

ORIG = pathlib.Path(os.environ["V1_REPO"]).resolve()
PY = ORIG / "humansearch/.venv/bin/python"
COPY_FILES = [
    ".github/workflows/verify.yml",
    "docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md",
    "docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md",
    "docs/engineering/history/resume-evidence-supabase-archive-goal-2026-08-17.md",
    "docs/engineering/history/resume-evidence-supabase-implementation-prompt-2026-08-17.md",
    "docs/engineering/hs-observe-url-crash-goal-2026-08-25.md",
    "docs/engineering/humansearch-branch-disposition-2026-09-07.md",
    "docs/engineering/verdicts/hs-observe-url-crash.verdict.json",
    "docs/sot/verification-commands.md",
    "humansearch/src/humansearch/observe.py",
    "scripts/acceptance-hs-kickoff.sh",
    "scripts/verify/list-workflow-steps.py",
    "scripts/verify/run-acceptance.sh",
    "humansearch/tests/test_hs_0001.py",
    "humansearch/tests/test_hs_0001_main_compat.py",
    "humansearch/pyproject.toml",
]
READER = "scripts/verify/list-workflow-steps.py"
ACC = "scripts/acceptance-hs-kickoff.sh"
NEG = ["step shell no-op is rejected", "top defaults run shell is rejected", "step BASH_ENV is rejected",
       "top BASH_ENV is rejected", "PR 131 does not satisfy PR 13", "VERDICT PASSED suffix is rejected"]
CLEAN = "test_clean_hs_kickoff_fixture_passes"
COMPAT = "test_hs_kickoff_accepts_latest_main_ci_concurrency_and_job_timeout"

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def env():
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in {"BASH_ENV", "ENV"}}

def replace(root, rel, old, new, count=1):
    p = root / rel; t = p.read_text(encoding="utf-8")
    assert t.count(old) == count, (rel, old, t.count(old))
    p.write_text(t.replace(old, new), encoding="utf-8")

def from_head(root, rel):
    blob = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ORIG, capture_output=True, check=True).stdout
    (root / rel).write_bytes(blob)

MUTANTS = [
    ("m01_reader_allow_all_step_keys", READER, lambda r: replace(r, READER, "        elif key not in RUN_KEYS:", "        elif False:"),
     {"step shell no-op is rejected", "step BASH_ENV is rejected"}),
    ("m02_reader_allow_all_top_keys", READER, lambda r: replace(r, READER, "            if key not in TOP_KEYS:", "            if False:"),
     {"top defaults run shell is rejected", "top BASH_ENV is rejected"}),
    ("m03_reader_allow_shell_key", READER, lambda r: replace(r, READER, 'RUN_KEYS = ("name", "run", "id", "timeout-minutes")', 'RUN_KEYS = ("name", "run", "id", "timeout-minutes", "shell")'),
     {"step shell no-op is rejected"}),
    ("m04_reader_always_reject_top", READER, lambda r: replace(r, READER, 'TOP_KEYS = ("name", "on", "permissions", "jobs", "concurrency")', "TOP_KEYS = ()"),
     {CLEAN, COMPAT}),
    ("m05_reader_drop_job_timeout_allow", READER, lambda r: replace(r, READER, '        if key not in ("runs-on", "steps", "timeout-minutes"):', '        if key not in ("runs-on", "steps"):'),
     {COMPAT}),
    ("m06_acceptance_verdict_regex_unanchored", ACC, lambda r: replace(r, ACC, "'^VERDICT: (PASS|FAIL)$'", "'^VERDICT: (PASS|FAIL)'"),
     {"VERDICT PASSED suffix is rejected"}),
    ("m07_acceptance_target_substring", ACC, lambda r: replace(r, ACC, """'NF && $1 ~ ("(^|[^[:alnum:]_./-])" t "($|[^[:alnum:]_./-])")'""", "'NF && index($1, t) > 0'", count=2),
     {"PR 131 does not satisfy PR 13"}),
    ("m08_acceptance_always_allow", ACC, lambda r: replace(r, ACC, 'failc() { echo "FAIL: $1"; checked=$((checked+1)); fail=1; }', 'failc() { echo "PASS: $1"; checked=$((checked+1)); }'),
     set(NEG)),
    ("m09_acceptance_always_reject", ACC, lambda r: replace(r, ACC, 'pass() { echo "PASS: $1"; checked=$((checked+1)); }', 'pass() { echo "FAIL: $1"; checked=$((checked+1)); fail=1; }'),
     {CLEAN, COMPAT}),
    ("m10_product_from_HEAD_16e5d64_red_preservation", READER, lambda r: (from_head(r, READER), from_head(r, ACC)),
     set(NEG) | {COMPAT}),
]

base = pathlib.Path(tempfile.mkdtemp(prefix="v2final-mut-"))
evidence = {"started": datetime.datetime.now(datetime.timezone.utc).isoformat(), "orig": str(ORIG), "base": str(base),
            "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ORIG, text=True, capture_output=True).stdout.strip(),
            "orig_sha_before": {f: sha(ORIG / f) for f in (READER, ACC)}, "mutants": []}
summary = []
for name, target, edit, expect_fail in MUTANTS:
    root = base / name;
    for rel in COPY_FILES:
        (root / rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ORIG / rel, root / rel)
    before = {f: (root / f).read_text(encoding="utf-8") for f in (READER, ACC)}
    edit(root)
    diff = ""
    for f in (READER, ACC):
        after = (root / f).read_text(encoding="utf-8")
        if after != before[f]:
            diff += "".join(difflib.unified_diff(before[f].splitlines(True), after.splitlines(True), f"a/{f}", f"b/{f}"))
    cmd = [str(PY), "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rA", "tests/test_hs_0001.py", "tests/test_hs_0001_main_compat.py"]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    p = subprocess.run(cmd, cwd=root / "humansearch", env=env(), text=True, capture_output=True)
    ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
    failed = set()
    for line in p.stdout.splitlines():
        if line.startswith("FAILED "):
            nodeid = line.split(" ", 1)[1].split(" - ")[0]
            failed.add(nodeid.split("[", 1)[1].rstrip("]") if "[" in nodeid else nodeid.split("::")[-1])
    ok = (p.returncode != 0) and (failed == expect_fail)
    rec = {"name": name, "target": target, "mutation_diff": diff, "target_sha256_after": {f: sha(root / f) for f in (READER, ACC)},
           "command": cmd, "cwd": str(root / "humansearch"), "started": started, "ended": ended, "exit_code": p.returncode,
           "stdout": p.stdout, "stderr": p.stderr, "expected_failing_tests": sorted(expect_fail), "actual_failing_tests": sorted(failed),
           "verdict": "CAUGHT" if ok else "SURVIVED_OR_WRONG_REASON"}
    evidence["mutants"].append(rec)
    summary.append(f"{rec['verdict']:24} {name}: rc={p.returncode} failed={sorted(failed)}")
    print(summary[-1], flush=True)
evidence["orig_sha_after"] = {f: sha(ORIG / f) for f in (READER, ACC)}
evidence["ended"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
pathlib.Path(ORIG / "artifacts/hs-next-20260910/v2-final-recheck-mutants-evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
shutil.rmtree(base)
print("orig unchanged:", evidence["orig_sha_before"] == evidence["orig_sha_after"])
