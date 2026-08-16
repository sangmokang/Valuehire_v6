# P0-04A Generated Artifact Ignore Goal

Easy conclusion: prove Git ignores pnpm/admin local build and test artifact paths without creating any artifacts, and prove no forbidden artifact under those roots is currently tracked.

## Scope

- Parent AC: AC-01
- Micro: P0-04A-generated-artifact-ignore
- Dependency checkpoint: `7e7fe3937c43a3abbcb4687c51ad85fb66eaab13`
- Dependency audit SHA-256: `0e27da83c48391b9b7cc4b1d4daab55a6c2118707f4024ef9f00129ab61ae39e`
- Single observable result: `requiredIgnorePathCount=5`, `checkedIgnoredPathCount=5`, `trackedForbiddenArtifactCount=0`, `targetCount=5`

## File Facts

- `.gitignore:9` already ignores `node_modules/`.
- `.gitignore:12` already ignores `.next/`, which covers `apps/admin/.next/.artifact-canary`.
- `scripts/verify/check-admin-foundation.sh` owns the admin foundation selectors and is extended only with `artifact-ignore`.
- `docs/engineering/admin-weekly-dashboard-v6-canonical-dependencies-2026-08-17.md:43` lists `P0-04A-generated-artifact-ignore`.
- `docs/engineering/admin-weekly-dashboard-v6-canonical-dependencies-2026-08-17.md:44` requires `P0-04-root-private-workspace`.
- `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:192` is the referenced goal boundary line for this packet.

## Acceptance Contract

The single AC is that all five synthetic paths are ignored by Git and no currently tracked file exists under the forbidden artifact roots:

1. `node_modules/.artifact-canary`
2. `apps/admin/.next/.artifact-canary`
3. `apps/admin/test-results/.artifact-canary`
4. `apps/admin/playwright-report/.artifact-canary`
5. `apps/admin/coverage/.artifact-canary`

Non-scope: no artifact creation, no admin app creation, no package or lockfile changes, no dependency install, no CI edits, no SOT or registry edits, no source-file ignores, no prior selector refactors, and no admin lifecycle commands.

Cannot split: the ignore-engine check and tracked-artifact scan are one rollback unit because a rule-only pass could still hide already tracked generated output, while a tracked scan alone would not prove future local build/test output stays out of `git status`.

## Commands

- Canonical RED/GREEN: `bash scripts/verify/check-admin-foundation.sh artifact-ignore`
- Regression selectors: `bash scripts/verify/check-admin-foundation.sh node-version`, `bash scripts/verify/check-admin-foundation.sh pnpm-version`, `bash scripts/verify/check-admin-foundation.sh root-workspace`
- Broader local gates: `bash verify.sh`, `bash scripts/session-status.sh`, `bash scripts/acceptance-0-2.sh`, `git diff --check`, `bash -n scripts/verify/check-admin-foundation.sh`

## Required Mutations

Both mutation checks must run only in disposable copies:

- Remove the existing `node_modules/` ignore rule and rerun the canonical selector. Expected: RED for `node_modules/.artifact-canary`, `targetCount=5`, `checkedIgnoredPathCount<5`.
- Separately remove the existing `.next/` ignore rule and rerun the canonical selector. Expected: RED for `apps/admin/.next/.artifact-canary`, `targetCount=5`, `checkedIgnoredPathCount<5`.

## Production Path

pnpm/build/test output paths -> `.gitignore` -> `git check-ignore` / `git status` boundary -> `git ls-files` tracked-artifact scan -> direct `ADMIN_FOUNDATION_ARTIFACT_IGNORE` receipt.

## Stop Conditions

- Stop as `SUPERSEDED_BAD_RED` if the initial selector does not execute all five targets or fails for a reason other than missing ignore coverage.
- Stop complete only after the candidate receipt is exact and the allowed regression commands have fresh evidence.

## External Effects

`external_side_effect_count_expected=0`. Admin install, lint, typecheck, unit, build, start, CI, and actual artifact generation are `NOT_RUN`.
