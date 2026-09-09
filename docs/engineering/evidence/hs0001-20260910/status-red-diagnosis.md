# Status RED Diagnosis — HS00.01

VERDICT: CURRENT_31_PASS / ORIGINAL_RED2_NAMES_NOT_PROVABLE

## Symptom
`scripts/session-status.sh` reported `RED: 2/31` for commit `16e5d649dbd257e6d01318c1a8fb0fbe8e731596`. The script discovers checks at `scripts/session-status.sh:46` through `scripts/session-status.sh:49`, suppresses each check at `scripts/session-status.sh:63`, and prints only the aggregate at `scripts/session-status.sh:66`.

## Root Cause
The exact two failing check names are not recoverable from the final session-status run because per-check output was intentionally discarded. The best-supported cause is an overlapping evidence-recovery window, not a stable HS source failure: raw `v1-cli.log` caused a secret-pattern failure at `2026-09-09T20:52:21Z`, then the same index scan passed at `2026-09-09T20:55:18Z`, and worktree/index scans passed after recovery at `2026-09-09T20:56:16Z`.

A second reproducible failure mode is concurrent writes during checks that compare `git status` before and after running. `acceptance-semantic-mutations.sh:271` through `scripts/acceptance-semantic-mutations.sh:276` and `acceptance-verify-ac-m.sh:350` through `scripts/acceptance-verify-ac-m.sh:359` fail if any other agent writes files mid-check. During this diagnosis, those two checks failed while concurrent V1/V2 evidence files appeared, then both passed on an immediate clean rerun captured outside the repository.

## Current 31-Check Result
Current table result: `31/31 PASS`. Non-PASS rows: `0`.

| # | Check | Current | Evidence |
|---:|---|---|---|
| 1 | `./scripts/acceptance-0-2-unreachable-content.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 2 | `./scripts/acceptance-0-2.sh` | PASS | docs/engineering/evidence/hs0001-20260910/commands.json:gate0-recovery |
| 3 | `./scripts/acceptance-0-5.sh` | PASS | docs/engineering/evidence/hs0001-20260910/commands.json:gate0-recovery |
| 4 | `./scripts/acceptance-0-6.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 5 | `./scripts/acceptance-ci-step-integrity.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 6 | `./scripts/acceptance-guard-global-skill-files.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 7 | `./scripts/acceptance-hs-a3.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 8 | `./scripts/acceptance-hs-a4.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 9 | `./scripts/acceptance-hs-cleanroom-absolute-contexts.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 10 | `./scripts/acceptance-hs-cleanroom-absolute-paths.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 11 | `./scripts/acceptance-hs-cleanroom-colon-paths.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 12 | `./scripts/acceptance-hs-cleanroom-file-urls.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 13 | `./scripts/acceptance-hs-cleanroom-hook-env-mutations.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 14 | `./scripts/acceptance-hs-cleanroom-hook-env.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 15 | `./scripts/acceptance-hs-cleanroom-mutations.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 16 | `./scripts/acceptance-hs-cleanroom.sh` | PASS | status-red-diagnosis.json:fresh_runs |
| 17 | `./scripts/acceptance-hs-gates-antiforge.sh` | PASS | artifacts/hs-next-20260910/hs0001-final-g2.json/log |
| 18 | `./scripts/acceptance-hs-gates-mutations.sh` | PASS | artifacts/hs-next-20260910/hs0001-final-g2.json/log |
| 19 | `./scripts/acceptance-hs-gates.sh` | PASS | artifacts/hs-next-20260910/hs0001-final-g2.json/log |
| 20 | `./scripts/acceptance-hs-kickoff-mutations.sh` | PASS | artifacts/hs-next-20260910/v1-final-mutations37.json |
| 21 | `./scripts/acceptance-hs-kickoff.sh` | PASS | artifacts/hs-next-20260910/v1-final-acceptance12.json |
| 22 | `./scripts/acceptance-invoice.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 23 | `./scripts/acceptance-principles-check.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 24 | `./scripts/acceptance-principles-mutations.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 25 | `./scripts/acceptance-secret-webhook-vendor.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 26 | `./scripts/acceptance-semantic-mutations.sh` | PASS | status-red-diagnosis.json:fresh_runs.state_sensitive_clean_reruns |
| 27 | `./scripts/acceptance-silent-failure-lint-mutations.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 28 | `./scripts/acceptance-silent-failure-lint.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 29 | `./scripts/acceptance-verified-sha.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |
| 30 | `./scripts/acceptance-verify-ac-m.sh` | PASS | status-red-diagnosis.json:fresh_runs.state_sensitive_clean_reruns |
| 31 | `./verify.sh` | PASS | status-red-diagnosis.json:fresh_runs.baseline_reruns |

## Historical Failures Preserved

- `hs0001-final-session-status`: aggregate `RED: 2/31`, no per-check output.
- `hs0001-staged-secret-scan`: `VERIFY_SCAN_SOURCE=index bash verify.sh` failed on `docs/engineering/evidence/hs0001-20260910/v1-cli.log`.
- `hs0001-staged-secret-recheck`: same index scan passed after remediation.
- `hs0001-evidence-recovery`: `git diff --cached --check && bash verify.sh && VERIFY_SCAN_SOURCE=index bash verify.sh` passed after recovery.

## Minimal Next Action

Do not change product/source for this RED2 alone. If an exact future RED name is required, run `scripts/session-status.sh` only after agents stop writing, or change it to preserve per-check rc and output. The current diagnosis artifact keeps full raw command records in `status-red-diagnosis.json`.
