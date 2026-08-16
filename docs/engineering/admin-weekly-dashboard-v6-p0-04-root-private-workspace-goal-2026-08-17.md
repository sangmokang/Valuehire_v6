# Admin Weekly Dashboard v6 P0-04 Root Private Workspace Goal

## Contract

P0-04 is an AC-01 partial micro. The observable result is that the root `package.json` parses as JSON, contains `private` exactly equal to `true`, and `pnpm-workspace.yaml` declares exactly one workspace package pattern: `apps/*`.

## Allowed Scope

- `package.json`
- `pnpm-workspace.yaml`
- `scripts/verify/check-admin-foundation.sh`
- `docs/engineering/admin-weekly-dashboard-v6-p0-04-root-private-workspace-goal-2026-08-17.md`

Forbidden scope includes app files, dependencies, scripts, package names, engines, lockfiles, CI, SOT, `.node-version`, prior selector refactors, and workspace execution.

## Canonical Verification

```bash
bash scripts/verify/check-admin-foundation.sh root-workspace
```

Expected GREEN receipt:

```text
ADMIN_FOUNDATION_ROOT_WORKSPACE checkedPrivateFields=1 workspacePatterns=1 targetCount=2 expectedPrivate=true expectedWorkspacePattern=apps/* reason=null
```

The verifier must evaluate both components before verdicts so receipts report actual discovered counts. `targetCount` is computed from `checkedPrivateFields + workspacePatterns`.

## Mutations

In disposable clones:

- Changing root `package.json` `private` to `false` must produce RED with `checkedPrivateFields=1 workspacePatterns=1 targetCount=2`.
- Removing the `apps/*` pattern from `pnpm-workspace.yaml` must produce RED with `checkedPrivateFields=1 workspacePatterns=0 targetCount=1`.

## Production Path

The production configuration path is root `package.json` `private` plus root `pnpm-workspace.yaml` package discovery. Direct config checks are in scope. pnpm workspace execution is `NOT_RUN`.

## Dependency Checkpoint

- dependency PASS checkpoint: `55b71bb7ee8bf0b2877f040e57e92382fd45b6af`
- raw P0-03 audit sha256: `360dc78c3b9ca92892048cfb1913ab10f3e145d75bd710d63c23c97b4e0af161`
