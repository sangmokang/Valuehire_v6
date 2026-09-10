# HS-00.03 initial RED independent review

Verdict: PASS

Reviewed SHA: `396cd2b7e92f755d65c34cf103d07b8741259cfc`
Parent SHA: `39cc8df54b0095ec85931a547c7dac68188feddc`
Review mode: isolated detached worktree at exact RED SHA; the shared GREEN worktree was not tested or edited.

## Commit shape

The RED commit changed exactly two test files:

- `M humansearch/tests/test_hs_0001.py`
- `A humansearch/tests/test_hs_0003.py`

`git diff --check HEAD^ HEAD` passed.

## Runtime-file absence

The isolated RED worktree did not contain the runtime implementation/data files:

- `scripts/verify/check-hs-kickoff-identities.py`
- `scripts/verify/hs-kickoff-confusables-17.0.0.json`

This verified that the optional runtime-copy fixture path does not create import, collection, fixture, or absent-runtime harness errors when those files are missing.

## Strengthened controls

The passing normal control preserved spoofed-boundary and multilingual cases:

- `ＰR #131`
- `hｓ-kickoff-other`
- Korean: `정상 한글`
- Japanese: `山田太郎`
- Arabic: `محمد`
- Latin: `Überprüfung`

The final RED test set also included the same-count mapping-content tamper case:

- Test id: `same-count-content`
- Mutation: changes the first confusable mapping entry to `"10FFFF"` while preserving the declared mapping count.
- RED behavior: current acceptance still returns success, so the test fails behaviorally where it expects `ERROR: Unicode 매핑 데이터`.

## Verification commands and results

Command:

```text
cd humansearch && uv run --no-sync pytest -q tests/test_hs_0003.py
```

Result:

```text
14 failed, 1 passed in 9.34s
```

Failure classification: behavioral RED. The failures are assertions that current acceptance returns `0` and `OK(run-acceptance)` where spoof or Unicode mapping-data rejection is expected. There were no import, collection, fixture, or harness failures.

Command:

```text
uv run --no-sync ruff check tests/test_hs_0003.py tests/test_hs_0001.py
```

Result:

```text
All checks passed!
```

Temporary detached worktree cleanup completed after review.
