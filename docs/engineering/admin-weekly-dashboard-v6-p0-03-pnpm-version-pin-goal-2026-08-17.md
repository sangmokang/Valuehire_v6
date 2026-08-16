# Admin Weekly Dashboard v6 P0-03 pnpm Version Pin Goal - 2026-08-17

## Easy conclusion

This micro only proves the repository root pnpm package manager pin. The accepted result is a root `package.json` with `packageManager` exactly equal to `pnpm@11.22.0`, plus a direct foundation selector that reports `checkedPackageManagerFields=1` and `targetCount=1`.

## Parent AC and micro-AC

- Parent AC: AC-01 - a clean checkout can run the admin foundation on fixed Node/pnpm and later install, lint, typecheck, test, build, and start without a sibling repository.
- Micro-AC: P0-03-pnpm-version-pin - root `package.json` has `packageManager` exactly equal to `pnpm@11.22.0`.

## Current facts

- SOT priority is injected/session AGENTS, then `docs/sot/*`, then the goal contract, Phase goals, implementation, and tests: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:82`.
- Phase 0 may not be widened into product work or later dependency work: `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:177`.
- AC-01 maps to Phase 0 P0-02 through P0-12 plus P0-04A, so this micro cannot complete the parent AC alone: `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:200`.
- The Phase 0 row for P0-03 allows only `package.json`, `scripts/verify/check-admin-foundation.sh`, and this goal file: `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:54`.
- The canonical RED and GREEN command for this micro is `bash scripts/verify/check-admin-foundation.sh pnpm-version`: `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:56`.
- The fixed pnpm version is `11.22.0`, and pnpm is pinned through root `packageManager`: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:196` and `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:220`.
- P0-02 dependency evidence is checkpoint commit `36b13a2c3d81e56d2e1e29fa71b72e9cf43d90ca`, with raw audit SHA-256 `fb4daed9a6606f0a1a950b3f7b021c2268f9e91cc12831f779f381c4d5115afe`.

## Single acceptance condition

Run `bash scripts/verify/check-admin-foundation.sh pnpm-version` at candidate HEAD. It must exit 0, emit `checkedPackageManagerFields=1`, emit `targetCount=1`, and parse the root `package.json` JSON field `packageManager` as exactly `pnpm@11.22.0`.

## Non-scope

No workspace declaration, `private` field, apps/admin, lockfile, dependencies, devDependencies, scripts, CI/SOT/registry registration, `.node-version`, v4/v5 migration, Corepack execution proof, pnpm execution proof, fallback, refactor, or unrelated acceptance repair is in scope.

## Cannot-split reason

The production artifact and the direct shell contract are one invariant: the root package manager pin exists and is exact. Splitting the file from the direct JSON-field check would allow an unguarded pnpm pin or a dead check.

## Exact RED and GREEN commands

- RED before root `package.json` exists: `bash scripts/verify/check-admin-foundation.sh pnpm-version`
- GREEN after minimal root `package.json` is added: `bash scripts/verify/check-admin-foundation.sh pnpm-version`

## Mutation

In a disposable clone/worktree only, change `packageManager` to `pnpm@11.22.1` and rerun `bash scripts/verify/check-admin-foundation.sh pnpm-version`. The command must exit nonzero for `package-manager-mismatch` while still reporting `checkedPackageManagerFields=1` and `targetCount=1`.

## Production call path

Root `package.json` `packageManager` -> Corepack/pnpm invocation contract -> direct foundation selector/check. This micro proves the file and selector path; actual Corepack provisioning or pnpm `11.22.0` execution is not proven here.

## Stop condition

Stop after a clean candidate commit containing only `package.json` on top of a RED commit containing only this goal document and `scripts/verify/check-admin-foundation.sh`, with targeted GREEN, broader verification results recorded, mutation RED proven in a disposable copy, and parent status reported as `PARTIAL_PARENT_AC`.

## Expected external effects

0. No network service, dependency install, deployment, PR, merge, email, calendar, ClickUp, or production write is expected or allowed.
