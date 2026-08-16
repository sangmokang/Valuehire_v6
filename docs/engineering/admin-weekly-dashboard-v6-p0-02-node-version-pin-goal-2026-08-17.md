# Admin Weekly Dashboard v6 P0-02 Node Version Pin Goal — 2026-08-17

## Easy conclusion

This micro only proves the repository root Node version pin. The accepted result is a root `.node-version` file containing exactly one line, `24.19.0`, plus a direct foundation selector that reports `checkedVersionFiles=1` and `targetCount=1`.

## Parent AC and micro-AC

- Parent AC: AC-01 — a clean checkout can run the admin foundation on fixed Node/pnpm and later install, lint, typecheck, test, build, and start without a sibling repository.
- Micro-AC: P0-02-node-version-pin — `.node-version` is exactly `24.19.0` on one line.

## Current facts

- SOT priority is injected/session AGENTS, then `docs/sot/*`, then the goal contract, Phase goals, implementation, and tests: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:82`.
- Phase 0 may not be widened into product work or later dependency work: `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:177`.
- The Phase 0 row for P0-02 allows only `.node-version`, `scripts/verify/check-admin-foundation.sh`, and this goal file: `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:32`.
- The canonical RED and GREEN command for this micro is `bash scripts/verify/check-admin-foundation.sh node-version`: `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:40`.
- The fixed Node version is `24.19.0`, and Node is pinned through root `.node-version`: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:196`.
- AC-01 maps to Phase 0 P0-02 through P0-12 plus P0-04A, so this micro cannot complete the parent AC alone: `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:200`.

## Single acceptance condition

Run `bash scripts/verify/check-admin-foundation.sh node-version` at candidate HEAD. It must exit 0, emit `checkedVersionFiles=1`, emit `targetCount=1`, and the root `.node-version` must compare byte-for-byte equal to `24.19.0` followed by one newline.

## Non-scope

No package.json, pnpm, workspace declaration, lockfile, apps/admin, dependencies, CI/SOT/registry registration, v4/v5 migration, runtime consumption proof, fallback, refactor, or unrelated acceptance repair is in scope.

## Cannot-split reason

The production artifact and the direct shell contract are one invariant: the root Node pin exists and is exact. Splitting the file from the direct check would allow an unguarded version pin or a dead check.

## Exact RED and GREEN commands

- RED before `.node-version` exists: `bash scripts/verify/check-admin-foundation.sh node-version`
- GREEN after `.node-version` is added: `bash scripts/verify/check-admin-foundation.sh node-version`

## Mutation

In a disposable clone/worktree only, change `.node-version` to `24.19.1` and rerun `bash scripts/verify/check-admin-foundation.sh node-version`. The command must exit nonzero for `node-version-mismatch` while still reporting `checkedVersionFiles=1` and `targetCount=1`.

## Production call path

Root `.node-version` -> local/CI runtime bootstrap configuration contract -> direct foundation selector/check. This micro proves the file and selector path; actual runtime manager consumption is not yet proven here.

## Stop condition

Stop after a clean candidate commit containing only `.node-version` on top of a RED commit containing only this goal document and `scripts/verify/check-admin-foundation.sh`, with targeted GREEN, broader verification results recorded, mutation RED proven in a disposable copy, and parent status reported as `PARTIAL_PARENT_AC`.

## Expected external effects

0. No network service, deployment, PR, merge, email, calendar, ClickUp, or production write is expected or allowed.
