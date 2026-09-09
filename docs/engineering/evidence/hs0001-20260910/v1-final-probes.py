#!/usr/bin/env python3
"""V1 final adversarial probes against the candidate reader/acceptance, run directly (no pytest)
in isolated git-init copies. Records diff, command, rc, full output. Also runs check-ci-step-integrity.sh where relevant."""
import datetime, difflib, hashlib, json, os, pathlib, shutil, subprocess, tempfile
ORIG = pathlib.Path(os.environ["V1_REPO"]).resolve()
FIX = [".github/workflows/verify.yml","docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md",
 "docs/engineering/goal-prompts/humansearch-journey-kickoff-2026-09-07.md",
 "docs/engineering/history/resume-evidence-supabase-archive-goal-2026-08-17.md",
 "docs/engineering/history/resume-evidence-supabase-implementation-prompt-2026-08-17.md",
 "docs/engineering/hs-observe-url-crash-goal-2026-08-25.md","docs/engineering/humansearch-branch-disposition-2026-09-07.md",
 "docs/engineering/verdicts/hs-observe-url-crash.verdict.json","docs/sot/verification-commands.md",
 "humansearch/src/humansearch/observe.py","scripts/acceptance-hs-kickoff.sh","scripts/verify/list-workflow-steps.py",
 "scripts/verify/run-acceptance.sh","scripts/verify/check-ci-step-integrity.sh","scripts/acceptance-ci-step-integrity.sh"]
WF = ".github/workflows/verify.yml"
VERDICT = "docs/engineering/humansearch-kickoff-ledger-verdict-0000-00-00.md"
RUN = "        run: bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-kickoff.sh"
def env(): return {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in {"BASH_ENV", "ENV"}}
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def rep(root, rel, old, new, count=1):
    p = root / rel; t = p.read_text(encoding="utf-8"); assert t.count(old) == count, (rel, old, t.count(old)); p.write_text(t.replace(old, new), encoding="utf-8")
def ins(root, rel, marker, prefix): rep(root, rel, marker, prefix + marker)

def p01(r):  # earlier acceptance step writes BASH_ENV into GITHUB_ENV for later steps
    (r / "scripts/v1-bait-env.sh").write_text("exit 0\n")
    rep(r, WF, "        run: bash verify.sh\n", '        run: bash verify.sh && echo "BASH_ENV=$GITHUB_WORKSPACE/scripts/v1-bait-env.sh" >> "$GITHUB_ENV"\n')
def p02(r): ins(r, WF, "      - name: 인수 검사 hs-kickoff (HumanSearch 착수 정리 · WU-0A)\n", "      - shell: cat\n") ; rep(r, WF, "      - shell: cat\n      - name: 인수 검사 hs-kickoff (", "      - shell: cat\n        name: 인수 검사 hs-kickoff (")
def p03(r): rep(r, WF, "\non:\n", '\n"on":\n')
def p04(r):
    (r / "docs/engineering/humansearch-kickoff-ledger-verdict-2026-09-10.md").write_text("VERDICT: FAIL\n\nreal-looking newer review\n")
def p05(r): ins(r, WF, "    steps:\n", "    env:\n      BASH_ENV: scripts/v1-bait-env.sh\n")
def p06(r): ins(r, WF, "jobs:\n", "# harmless comment\ndefaults:\n  run:\n    shell: cat\n\n")
def p07(r): ins(r, WF, RUN, "        working-directory: /tmp\n")
def p08(r): ins(r, WF, "    steps:\n", "    timeout-minutes: ${{ 30 }}\n")
def p09(r): ins(r, WF, "    steps:\n", "    container: ubuntu:24.04\n")
def p10(r): rep(r, WF, "    runs-on: ubuntu-latest\n", "    runs-on: windows-latest\n")
def p11(r): ins(r, WF, RUN, "        timeout-minutes: 0\n")
def p12(r): rep(r, WF, "      - name: 인수 검사 hs-kickoff (HumanSearch 착수 정리 · WU-0A)\n", "      - name: 인수 검사 hs-kickoff (HumanSearch 착수 정리 · WU-0A)\n        if: false\n")
def p13(r):  # GITHUB_PATH hijack of `bash` from an earlier step
    rep(r, WF, "        run: bash verify.sh\n", '        run: bash verify.sh && mkdir -p /tmp/fakebin && printf "#!/bin/sh\\nexit 0\\n" > /tmp/fakebin/bash && chmod +x /tmp/fakebin/bash && echo /tmp/fakebin >> "$GITHUB_PATH"\n')
PROBES = [
 ("p01_earlier_step_writes_BASH_ENV_to_GITHUB_ENV", p01, "expect: is it caught?"),
 ("p02_shell_key_on_dash_line", p02, "expect rejected 약화"),
 ("p03_quoted_on_key_legit_yaml", p03, "over-block check"),
 ("p04_two_verdict_files_fail_and_pass", p04, "which file is reported"),
 ("p05_job_level_env_BASH_ENV", p05, "expect rejected job-level key"),
 ("p06_top_defaults_after_comment", p06, "expect rejected top key"),
 ("p07_step_working_directory", p07, "expect rejected 약화"),
 ("p08_job_timeout_expression", p08, "expect rejected non-integer"),
 ("p09_job_container", p09, "expect rejected job-level key"),
 ("p10_runs_on_windows", p10, "environment change via runs-on value"),
 ("p11_step_timeout_zero", p11, "invalid step timeout value"),
 ("p12_if_false_regression", p12, "expect rejected 약화 (existing)"),
 ("p13_earlier_step_hijacks_bash_via_GITHUB_PATH", p13, "expect: is it caught?"),
]
base = pathlib.Path(tempfile.mkdtemp(prefix="v1final-probe-"))
ev = {"started": datetime.datetime.now(datetime.timezone.utc).isoformat(), "base": str(base), "orig_sha_before": {f: sha(ORIG/f) for f in ("scripts/acceptance-hs-kickoff.sh","scripts/verify/list-workflow-steps.py",WF)}, "probes": []}
for name, edit, note in PROBES:
    root = base / name / "repo"
    for rel in FIX:
        (root/rel).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ORIG/rel, root/rel)
    (root/VERDICT).write_text("VERDICT: PASS\n\nsynthetic fixture verdict\n")
    before = (root/WF).read_text()
    edit(root)
    after = (root/WF).read_text()
    diff = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), "a/"+WF, "b/"+WF))
    subprocess.run(["git","init","-q"], cwd=root, env=env(), check=True); subprocess.run(["git","add","."], cwd=root, env=env(), check=True)
    subprocess.run(["git","-c","user.name=v1","-c","user.email=v1@example.invalid","commit","-qm","probe"], cwd=root, env=env(), check=True)
    cmd = ["bash","scripts/verify/run-acceptance.sh","scripts/acceptance-hs-kickoff.sh"]
    p = subprocess.run(cmd, cwd=root, env=env(), text=True, capture_output=True)
    cmd2 = ["bash","scripts/verify/check-ci-step-integrity.sh", WF]
    p2 = subprocess.run(cmd2, cwd=root, env=env(), text=True, capture_output=True)
    fails = [l for l in (p.stdout+p.stderr).splitlines() if l.startswith("FAIL: ") or l.startswith("PASS: 판정")]
    rec = {"name": name, "note": note, "mutation_diff": diff, "acceptance_cmd": cmd, "acceptance_rc": p.returncode, "acceptance_stdout": p.stdout, "acceptance_stderr": p.stderr,
           "ci_integrity_cmd": cmd2, "ci_integrity_rc": p2.returncode, "ci_integrity_stdout": p2.stdout, "ci_integrity_stderr": p2.stderr}
    ev["probes"].append(rec)
    print(f"{name}: acceptance rc={p.returncode} ci-integrity rc={p2.returncode} :: {' | '.join(fails)[:300]}")
ev["orig_sha_after"] = {f: sha(ORIG/f) for f in ev["orig_sha_before"]}
ev["ended"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(ORIG/"artifacts/hs-next-20260910/v1-final-probes-evidence.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1)+"\n")
shutil.rmtree(base)
print("orig unchanged:", ev["orig_sha_before"] == ev["orig_sha_after"])
