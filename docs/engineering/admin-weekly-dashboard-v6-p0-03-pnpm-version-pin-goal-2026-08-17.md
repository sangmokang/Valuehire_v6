# Admin Weekly Dashboard v6 P0-03 pnpm Version Pin Goal

## Contract

P0-03 is an AC-01 partial micro. The single observable result is that the root `package.json` parses as JSON and contains `packageManager` exactly equal to `pnpm@11.22.0`.

## Allowed Scope

- `package.json`
- `scripts/verify/check-admin-foundation.sh`
- `docs/engineering/admin-weekly-dashboard-v6-p0-03-pnpm-version-pin-goal-2026-08-17.md`

Forbidden scope includes private files, workspace metadata, package names, scripts, dependencies, engines, lockfiles, apps, CI, SOT, `.node-version`, and refactors.

## Canonical Verification

```bash
bash scripts/verify/check-admin-foundation.sh pnpm-version
```

Expected GREEN receipt:

```text
ADMIN_FOUNDATION_PNPM_VERSION checkedPackageManagerFields=1 targetCount=1 expected=pnpm@11.22.0 reason=null
```

Missing `package.json` must fail with `checkedPackageManagerFields=0 targetCount=0`. Missing `packageManager`, malformed JSON, non-string `packageManager`, or any other value must fail closed.

## Mutation

In a disposable clone, changing `packageManager` to `pnpm@11.22.1` must produce RED with `checkedPackageManagerFields=1 targetCount=1`.

## Production Path

The production configuration path is `package.json` `packageManager` -> Corepack/pnpm selector. This micro verifies the direct selector only. Corepack execution, admin install, admin lint, admin typecheck, admin unit tests, admin build, admin start, and CI are `NOT_RUN`.

## Dependency Checkpoint

- dependency PASS checkpoint: `dbb55566b9f656800892b7373678444641989432`
- raw P0-02 audit sha256: `fb4daed9a6606f0a1a950b3f7b021c2268f9e91cc12831f779f381c4d5115afe`
