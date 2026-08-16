# Admin Weekly Dashboard v6 P0-04A Generated Artifact Ignore Goal

## Contract

- Evaluate exactly these generated artifact canary paths without creating them in the production verifier path:
  - `node_modules/.artifact-canary`
  - `apps/admin/.next/.artifact-canary`
  - `apps/admin/test-results/.artifact-canary`
  - `apps/admin/playwright-report/.artifact-canary`
  - `apps/admin/coverage/.artifact-canary`
- Use Git's ignore engine with `git check-ignore --no-index` so tracked paths cannot inflate ignore coverage.
- Independently fail first on tracked forbidden canaries with reason `tracked-forbidden-artifact`.
- Fail second on incomplete ignore coverage with reason `ignore-coverage`.
- Preserve normal source paths as unignored.

## Expected Evidence

- Base RED: `required=5 checkedIgnored=2 trackedForbidden=0 target=5`.
- Candidate PASS: `required=5 checkedIgnored=5 trackedForbidden=0 target=5`.
- Disposable mutation RED, removing `node_modules/`: `required=5 checkedIgnored=4 trackedForbidden=0 target=5`.
- Disposable mutation RED, removing `.next/`: `required=5 checkedIgnored=4 trackedForbidden=0 target=5`.
- Disposable mutation RED, force-adding a tracked canary: `required=5 checkedIgnored=5 trackedForbidden=1 target=5 reason=tracked-forbidden-artifact`.

## Non-Goals

- No artifact generation in the production verifier path.
- No lifecycle verification changes.
- No broad source ignore rules.
