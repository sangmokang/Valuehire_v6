# Admin Weekly Dashboard v6 P0-04A Generated Artifact Ignore Goal

## Conclusion

This micro is complete only when the five contracted local output paths are hidden from normal git status and none of those exact paths are already tracked. No app code, CI, SOT, dependencies, or real generated output is in scope.

## Contract

- Parent AC: AC-01.
- Micro: P0-04A-generated-artifact-ignore.
- Single observable result: exactly five contracted pnpm/admin generated-artifact canary paths are ignored while zero tracked forbidden artifacts exist, as reported by `bash scripts/verify/check-admin-foundation.sh artifact-ignore`.
- Single failure reason: any required canary is not ignored or any forbidden canary artifact is tracked.
- Cannot split: ignoring these five paths and rejecting force-tracked copies is one boundary; splitting would allow a green ignore check while tracked artifacts still leak.
- External side effects expected: 0.

## Current Facts

- `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:81` names this micro.
- `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:86` limits changes to `.gitignore`, `scripts/verify/check-admin-foundation.sh`, and this goal file.
- `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:88` defines the RED command.
- `.gitignore:9` currently ignores `node_modules/`.
- `.gitignore:12` currently ignores `.next/`.
- `scripts/verify/check-admin-foundation.sh:6` currently accepts only the existing foundation selectors, so `artifact-ignore` must be added before the RED run can measure the contract.

## Acceptance Criteria

At candidate HEAD, this command must exit 0:

```bash
bash scripts/verify/check-admin-foundation.sh artifact-ignore
```

Expected receipt:

```text
ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=5 tracked=0 targetCount=5 reason=null
```

The five required synthetic paths are:

```text
node_modules/.artifact-canary
apps/admin/.next/.artifact-canary
apps/admin/test-results/.artifact-canary
apps/admin/playwright-report/.artifact-canary
apps/admin/coverage/.artifact-canary
```

## Non-Scope

- No `scripts/acceptance-admin-*.sh` changes.
- No `.github/workflows/verify.yml` changes.
- No `docs/sot/verification-commands.md` or `docs/sot/mechanism-registry.yaml` changes.
- No dependencies.
- No product/admin application files.
- No real generated artifacts committed.
- No external, network, or live calls.

## RED and GREEN

- RED command: `bash scripts/verify/check-admin-foundation.sh artifact-ignore`.
- Base RED expected after adding the selector but before `.gitignore` changes: `required=5 ignored=2 tracked=0 targetCount=5`, nonzero exit.
- GREEN expected after `.gitignore` changes: `required=5 ignored=5 tracked=0 targetCount=5`, exit 0.

## Mutation Plan

Use only disposable clones or worktrees:

- Remove `node_modules/` ignore and rerun the selector. Expected RED: `required=5 ignored=4 tracked=0 targetCount=5`.
- Remove `apps/admin/.next/` ignore and rerun the selector. Expected RED: `required=5 ignored=4 tracked=0 targetCount=5`.
- Force-track one forbidden canary path and rerun the selector. Expected RED: `required=5 ignored=5 tracked=1 targetCount=5 reason=tracked-forbidden-artifact`.

## Production Call Path

`check-admin-foundation.sh artifact-ignore` selector -> canonical path set -> `git check-ignore --no-index` ignore evaluator plus `git ls-files` tracked-artifact detector -> receipt/stdout and nonzero/zero exit -> direct shell test and disposable mutation checks.

## Stop Conditions

Stop without correction or amendment if the RED output is not `required=5 ignored=2 tracked=0 targetCount=5`, if any file outside the three allowed files is required, if a forbidden artifact must be committed, or if the contract cannot be satisfied with `.gitignore` plus the existing verifier.

## Adversarial Checks

- The selector must fail when an ignore rule is missing.
- The selector must fail when a forbidden canary is force-tracked even if the ignore rule exists.
- The selector must count all five required paths and must not pass with zero checked paths.

## Verification Log

Pending.
