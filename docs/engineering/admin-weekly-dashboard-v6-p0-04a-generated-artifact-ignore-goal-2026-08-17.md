# P0-04A Generated Artifact Ignore Goal

## 쉬운 말 결론

이 micro의 단일 관찰 결과는 "admin 작업 중 생길 수 있는 다섯 개 로컬 산출물 canary 경로가 git에 들어가지 않도록 모두 무시되고, 이미 추적된 금지 canary도 0개로 남는다"입니다. 실패 이유도 하나입니다: 다섯 경로 중 하나라도 무시되지 않거나, 무시되는 경로라도 강제로 추적되면 이 micro는 실패합니다. rollback unit은 root `.gitignore`, `scripts/verify/check-admin-foundation.sh`, 이 goal 문서뿐입니다.

## Parent And Micro

- Parent AC: `AC-01`, clean checkout에서 고정 Node/pnpm으로 admin install, ESLint, typecheck, test, build, start가 되는 기반입니다. 원문 AC-01은 `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:1160`에 있습니다.
- Micro: `P0-04A-generated-artifact-ignore`, dependency install 전에 생성물로 worktree가 오염되지 않게 하는 선행 원자 작업입니다. Controller는 AC-01이 Phase 0 `P0-02~P0-12`와 `P0-04A`를 포함한다고 매핑합니다: `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:200`. Controller는 P0-04A가 dependency install 전 선행 작업이라고도 고정합니다: `docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md:215`.
- Phase row: Phase 0 row는 parent AC, micro id, rollback unit, dependencies, allowed files, RED/GREEN command를 고정합니다: `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:80`, `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:81`, `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:84`, `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:85`, `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:86`, `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:88`, `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:89`.

## Current Facts

- Root ignore rules currently include general generated artifact rules for `node_modules/` and `.next/`: `.gitignore:8`, `.gitignore:9`, `.gitignore:12`.
- P0-04A-specific ignore rules currently include `/node_modules/`, `/apps/admin/.next/`, `/apps/admin/test-results/`, `/apps/admin/playwright-report/`, and `/apps/admin/coverage/`: `.gitignore:15`, `.gitignore:16`, `.gitignore:17`, `.gitignore:18`, `.gitignore:19`, `.gitignore:20`.
- The verifier accepts `artifact-ignore` as a supported selector: `scripts/verify/check-admin-foundation.sh:4`, `scripts/verify/check-admin-foundation.sh:6`.
- The verifier's exact five production inputs are `node_modules/.artifact-canary`, `apps/admin/.next/.artifact-canary`, `apps/admin/test-results/.artifact-canary`, `apps/admin/playwright-report/.artifact-canary`, and `apps/admin/coverage/.artifact-canary`: `scripts/verify/check-admin-foundation.sh:106`, `scripts/verify/check-admin-foundation.sh:107`, `scripts/verify/check-admin-foundation.sh:108`, `scripts/verify/check-admin-foundation.sh:109`, `scripts/verify/check-admin-foundation.sh:110`, `scripts/verify/check-admin-foundation.sh:111`, `scripts/verify/check-admin-foundation.sh:112`, `scripts/verify/check-admin-foundation.sh:113`.
- The verifier counts required inputs, ignored inputs, tracked inputs, missing-ignore paths, and tracked paths before deciding: `scripts/verify/check-admin-foundation.sh:114`, `scripts/verify/check-admin-foundation.sh:115`, `scripts/verify/check-admin-foundation.sh:116`, `scripts/verify/check-admin-foundation.sh:117`, `scripts/verify/check-admin-foundation.sh:118`.
- For each input, the production path first runs `git check-ignore --no-index --quiet -- "$required_path"` and increments `ignored_count`, then runs `git ls-files --error-unmatch -- "$required_path"` and increments `tracked_count`: `scripts/verify/check-admin-foundation.sh:120`, `scripts/verify/check-admin-foundation.sh:121`, `scripts/verify/check-admin-foundation.sh:122`, `scripts/verify/check-admin-foundation.sh:127`, `scripts/verify/check-admin-foundation.sh:128`.
- If any canary is tracked, the selector exits 1 with `reason=tracked-forbidden-artifact`: `scripts/verify/check-admin-foundation.sh:133`, `scripts/verify/check-admin-foundation.sh:135`, `scripts/verify/check-admin-foundation.sh:136`.
- If any required input is not ignored, the selector exits 1 with `reason=missing-artifact-ignore`: `scripts/verify/check-admin-foundation.sh:139`, `scripts/verify/check-admin-foundation.sh:141`, `scripts/verify/check-admin-foundation.sh:142`.
- If all five are ignored and none are tracked, the selector exits 0 with `reason=null`: `scripts/verify/check-admin-foundation.sh:145`, `scripts/verify/check-admin-foundation.sh:146`, `scripts/verify/check-admin-foundation.sh:147`.

## Single Acceptance Condition

Run exactly:

```bash
bash scripts/verify/check-admin-foundation.sh artifact-ignore
```

It must exit 0 and emit exactly this receipt line:

```text
ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=5 tracked=0 targetCount=5 reason=null
```

No other acceptance condition is part of this micro.

## Explicit Non-Scope

This micro does not prove parent AC-01 completion, dependency install, `pnpm` runtime behavior, admin app existence, ESLint execution, typecheck execution, tests, Next build, admin start, generated artifact creation, data-exposure registration, acceptance script changes, CI wiring, SOT updates, registry updates, package changes, lockfile changes, external network access, live calls, deployment, or operational write paths.

## Cannot Split Further

The ignore rules and direct selector are one invariant. Splitting them would allow either an unverified ignore file or a verifier that is disconnected from the actual generated artifact paths. The smallest useful behavior is the complete path from the five exact canary inputs, through `git check-ignore --no-index`, through tracked enumeration, to one receipt and exit code.

## RED And GREEN Receipts

- RED commit: `bd12c2e9f1e4067a0fccad302c8d0017ff2c462a`.
- RED command:

```bash
bash scripts/verify/check-admin-foundation.sh artifact-ignore
```

- RED receipt and exit: `ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=2 tracked=0 targetCount=5 reason=missing-artifact-ignore`, exit 1.
- GREEN command:

```bash
bash scripts/verify/check-admin-foundation.sh artifact-ignore
```

- GREEN receipt and exit: `ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=5 tracked=0 targetCount=5 reason=null`, exit 0.

## Mutation Receipts

All mutation checks are disposable only and must not leave source writes in the candidate.

- Remove `node_modules` ignore coverage: receipt `ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=4 tracked=0 targetCount=5 reason=missing-artifact-ignore`, exit 1.
- Remove `.next` ignore coverage: receipt `ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=4 tracked=0 targetCount=5 reason=missing-artifact-ignore`, exit 1.
- Force-track a canary: receipt `ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=5 tracked=1 targetCount=5 reason=tracked-forbidden-artifact`, exit 1.

## Production Call Path

Selector: `artifact-ignore` enters the artifact block at `scripts/verify/check-admin-foundation.sh:106`.

Exact five inputs:

1. `node_modules/.artifact-canary`
2. `apps/admin/.next/.artifact-canary`
3. `apps/admin/test-results/.artifact-canary`
4. `apps/admin/playwright-report/.artifact-canary`
5. `apps/admin/coverage/.artifact-canary`

Direct tests:

1. `git check-ignore --no-index --quiet -- "$required_path"` for each input.
2. `git ls-files --error-unmatch -- "$required_path"` for each input.
3. Receipt `ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=5 tracked=0 targetCount=5 reason=null`.
4. Exit 0.

The current candidate file:line anchors for this path are `scripts/verify/check-admin-foundation.sh:106`, `scripts/verify/check-admin-foundation.sh:120`, `scripts/verify/check-admin-foundation.sh:121`, `scripts/verify/check-admin-foundation.sh:127`, `scripts/verify/check-admin-foundation.sh:135`, `scripts/verify/check-admin-foundation.sh:141`, `scripts/verify/check-admin-foundation.sh:146`.

## Stop Conditions

Stop and do not claim micro success if any of these occurs:

- `targetCount=0` or any other zero-target shortcut appears.
- A disposable mutation returns GREEN.
- The selector path is disconnected from the root `.gitignore` rules or from the exact five production inputs.
- Scope expands beyond root `.gitignore`, `scripts/verify/check-admin-foundation.sh`, and this goal document for the original micro, or beyond this goal document for the R16 rework.
- Any exposure scan, external access, live call, deployment, or operational write is attempted.
- A baseline selector for `node-version`, `pnpm-version`, or `root-workspace` regresses.
- The diff contains acceptance, CI, SOT, registry, app, package, dependency, lockfile, runtime, or generated artifact changes.

## External Effects

- Expected external effects: 0.
- Actual external effects: 0.

## Parent Status And NOT_RUN

Parent AC-01 remains `PARTIAL` / `NOT PASS`. Phase 0 remains partial. The repository remains partial. `pnpm install`, `pnpm` workspace execution, admin runtime, artifact generation, CI, deployment, and live access remain `NOT_RUN`.
