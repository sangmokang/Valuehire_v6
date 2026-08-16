# P0-04A Generated Artifact Ignore Goal

## Scope

This micro proves only the repository ignore boundary for local generated artifacts created by dependency install, admin build, and admin test tooling.

Allowed files:

- `.gitignore`
- `scripts/verify/check-admin-foundation.sh`
- `docs/engineering/admin-weekly-dashboard-v6-p0-04a-generated-artifact-ignore-goal-2026-08-17.md`

Forbidden scope includes acceptance scripts, CI, SOT, registry, app files, package files, lockfiles, dependency changes, live calls, and actually generating build or test artifacts.

## Observable Result

The canonical selector is:

```bash
bash scripts/verify/check-admin-foundation.sh artifact-ignore
```

Candidate success requires exactly five required generated artifact canary paths, all ignored by `git check-ignore --no-index`, with zero tracked forbidden canaries reported by `git ls-files`.

Required canary paths:

- `node_modules/.artifact-canary`
- `apps/admin/.next/.artifact-canary`
- `apps/admin/test-results/.artifact-canary`
- `apps/admin/playwright-report/.artifact-canary`
- `apps/admin/coverage/.artifact-canary`

The GREEN receipt must report:

```text
ADMIN_FOUNDATION_ARTIFACT_IGNORE required=5 ignored=5 tracked=0 targetCount=5 reason=null
```

## Failure Contract

The selector must fail when any required generated artifact path is not ignored, while preserving `required=5` and `targetCount=5`. It must also fail when any forbidden canary is force-tracked, even if the path is ignored, with `reason=tracked-forbidden-artifact`.

This micro does not prove clean install, admin build, admin test execution, CI registration, or parent AC-01 completion.
