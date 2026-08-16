# Admin Weekly Dashboard v6 P0-04 Root Private Workspace Goal - 2026-08-17

## Easy conclusion

This micro only proves the repository root publication and workspace discovery boundary. The accepted result is a root `package.json` with parsed `private: true` and a root `pnpm-workspace.yaml` that declares exactly one package pattern, `apps/*`, plus a direct foundation selector that reports `checkedPrivateFields=1`, `workspacePatternCount=1`, and `targetCount=2`.

## Parent AC and micro-AC

- Parent AC: AC-01 - a clean checkout can run the admin foundation on fixed Node/pnpm and later install, lint, typecheck, test, build, and start without a sibling repository.
- Micro-AC: P0-04-root-private-workspace - root package is non-publishable and pnpm workspace discovery includes admin apps through exactly `apps/*`.

## Current facts

- SOT priority is injected/session AGENTS, then `docs/sot/*`, then the goal contract, Phase goals, implementation, and tests: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:82`.
- The root package must declare only a private workspace boundary: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:175`.
- Phase 0 may not be widened into dependency or later product work: `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:177`.
- AC-01 maps to Phase 0 P0-02 through P0-12 plus P0-04A, so this micro cannot complete the parent AC alone: `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:200`.
- The Phase 0 row for P0-04 allows only `package.json`, `pnpm-workspace.yaml`, `scripts/verify/check-admin-foundation.sh`, and this goal file: `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:70`.
- The canonical RED and GREEN command for this micro is `bash scripts/verify/check-admin-foundation.sh root-workspace`: `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:72`.
- P0-03 dependency evidence is checkpoint commit `ac26ece99e614d64dd69a4aae1c8ceb3617bf589`, with raw audit SHA-256 `dc2706c089bbfb8a7c308f5e56c16fca97cb7e9cb0c5f8b01c03c67beb2b6109`.

## Single acceptance condition

Run `bash scripts/verify/check-admin-foundation.sh root-workspace` at candidate HEAD. It must exit 0, parse the root `package.json` field `private` as boolean `true`, compare `pnpm-workspace.yaml` byte-for-byte to exactly `packages:\n  - apps/*\n`, emit `checkedPrivateFields=1`, emit `workspacePatternCount=1`, and emit `targetCount=2`.

## Non-scope

No apps/admin package or directory, dependencies, devDependencies, scripts, name, engines, lockfile, install, CI/SOT/registry registration, `.node-version`, prior audit evidence, fallback, refactor, or unrelated acceptance repair is in scope. The P0-03 LOW ambient-status note is not fixed here.

## Cannot-split reason

The production boundary is one invariant: the root package must be non-publishable and pnpm must discover the admin package namespace. Splitting `private` from the workspace pattern would allow either publishing from root or making admin packages undiscoverable while a half-check passed.

## Exact RED and GREEN commands

- RED before `private: true` and `pnpm-workspace.yaml` exist: `bash scripts/verify/check-admin-foundation.sh root-workspace`
- GREEN after the minimal production files are present: `bash scripts/verify/check-admin-foundation.sh root-workspace`

## Mutations

In disposable copies only:

- Change `package.json` `private` to `false` and rerun `bash scripts/verify/check-admin-foundation.sh root-workspace`. The command must exit nonzero for `private-not-true` while reporting `checkedPrivateFields=1` and `targetCount=2`.
- Remove the `apps/*` workspace pattern from `pnpm-workspace.yaml` and rerun `bash scripts/verify/check-admin-foundation.sh root-workspace`. The command must exit nonzero for `workspace-pattern-mismatch` while reporting `checkedPrivateFields=1`, `workspacePatternCount=0`, and `targetCount=2`.

## Production call path

Root `package.json` parsed `private` flag plus root `pnpm-workspace.yaml` package pattern -> pnpm workspace discovery/configuration boundary -> direct foundation selector/check. This micro proves the file and selector path; actual pnpm workspace discovery under pnpm `11.22.0` is `NOT_RUN`.

## Stop condition

Stop after a clean candidate commit containing only `package.json` and `pnpm-workspace.yaml` on top of a RED commit containing only this goal document and `scripts/verify/check-admin-foundation.sh`, with targeted GREEN, P0-02/P0-03 selector reruns, broader verification results recorded, two mutation RED checks proven in disposable copies, trace recorded in the final report, and parent status reported as `PARTIAL_PARENT_AC`.

## Expected external effects

0. No network service, dependency install, deployment, PR, merge, email, calendar, ClickUp, or production write is expected or allowed.
