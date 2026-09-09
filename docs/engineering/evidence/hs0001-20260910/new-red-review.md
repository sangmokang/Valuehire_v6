# HS-00.01 신규 결함 pytest RED 독립리뷰

## Verdict

- PASS for tests-only RED commit evidence.
- 검토 대상: `artifacts/hs-next-20260910/regression-draft.py`
- 대상 지문: `sha256=5e84ee466466147ca377b08928bfd04593184e519dc54677a6dd8fe1c31278bf`, `wc -l=177`
- 보존 증거: `artifacts/hs-next-20260910/new-red-review.json`
- 증거 JSON 지문: `sha256=c3dcbee8f4eab3b9cac3944bfe093fc62a14eefc10fbf391c13ddaf39cbc2577`

이 draft는 현재 제품/검사기 결함을 정확히 RED로 잠근다. 정상 대조군 1개는 PASS하고, E5a/E5b/E5f/E5d/E5e1 및 top-level BASH_ENV까지 6개 false-pass 반례는 현재 acceptance가 `exit 0`으로 잘못 통과시켜 pytest에서 FAIL한다. 실패 원인은 import, 수집, 문법 오류가 아니라 `assert result.returncode != 0`가 깨진 행동 RED다.

## Evidence

- `artifacts/hs-next-20260910/regression-draft-evidence-rev2.json`
  - `sha256=d39b6755f9be187960077f4a90b7ac8b5e050862943f1f8d26ee67284fd257f5`
  - rev2 자체 기록: ruff exit 0, strict mypy exit 0, pytest exit 1, `6 failed, 1 passed`.
- Fresh verifier run in `new-red-review.json`
  - HEAD: `06110d9355ae352da58e4ee7e4e2551962cda7d4`
  - MERGE_HEAD: `c6a94c713486c62b9effb1cef8adc2f137114e9f`
  - `humansearch/.venv/bin/ruff check artifacts/hs-next-20260910/regression-draft.py` -> exit 0, `All checks passed!`
  - `humansearch/.venv/bin/mypy --strict --python-executable humansearch/.venv/bin/python artifacts/hs-next-20260910/regression-draft.py` -> exit 0, `Success: no issues found in 1 source file`
  - `humansearch/.venv/bin/pytest --collect-only -q artifacts/hs-next-20260910/regression-draft.py` -> exit 0, 7 tests collected.
  - `humansearch/.venv/bin/pytest artifacts/hs-next-20260910/regression-draft.py -q --tb=short` -> exit 1, `.FFFFFF`, `6 failed, 1 passed`.
- Fingerprint stability during fresh verifier run
  - `fingerprints_changed_during_review` in JSON is `{}`.
  - Product/acceptance fingerprints stayed fixed during the run:
    - `scripts/acceptance-hs-kickoff.sh`: `705ceb9f82fdd899673e04d31c68fb73a38372a0f324674f6e5533b5120d147b`
    - `scripts/verify/list-workflow-steps.py`: `c8630fc4cce7071ee12365becbf9852aedfeff3dae79b9be22392d212f0b4505`
    - `.github/workflows/verify.yml`: `175d44e93b0eca518cdd74dd54b971e49b020e66bfd6b3935930ae20fac7ecc5`
    - `docs/engineering/humansearch-branch-disposition-2026-09-07.md`: `973d760992323165895841708a01b6a8ef7ee709e69f1df359c4cdb670ba6872`

## Contract Check

- 정상 대조군 PASS: `test_clean_hs_kickoff_fixture_passes` passes, so the draft is not an always-fail test.
- E5a step `shell`: `mutate_step_shell()` inserts a step-level `shell: bash -c "true" {0}` before the hs-kickoff run line. Current acceptance returns 0, so pytest fails at `assert result.returncode != 0`.
- E5b top `defaults.run.shell`: `mutate_default_shell()` inserts top-level defaults before `jobs:`. Current acceptance returns 0, so pytest fails.
- E5f step `BASH_ENV`: `mutate_step_bash_env()` adds step env with `BASH_ENV`. Current acceptance returns 0, so pytest fails.
- Top `BASH_ENV`: `mutate_top_bash_env()` adds top-level env with `BASH_ENV`. Current acceptance returns 0, so pytest fails.
- E5d `PR #131`: `mutate_pr_131()` changes the target text from `PR #13` to `PR #131`; current acceptance still counts it as `PR #13`, so pytest fails.
- E5e1 `VERDICT: PASSED`: `mutate_verdict_passed()` changes the verdict prefix to `VERDICT: PASSED`; current regex still accepts it, so pytest fails.

These are direct CLI failures against the current scripts, not static assertions over strings.

## Test Quality

- Git environment cleanup is present for every subprocess path in the draft:
  - `clean_env()` removes all `GIT_*`, `BASH_ENV`, and `ENV`.
  - `copy_fixture()` passes that env to `git init`, `git add`, and `git commit`.
  - `run_acceptance()` passes that env to the acceptance subprocess.
- Failure reason matching is present and scoped to real `FAIL:` lines:
  - `fail_lines()` keeps only lines starting with `FAIL: `.
  - `assert_rejected()` requires nonzero return, `CHECKED: 12`, and an expected failure fragment inside a `FAIL:` line.
- Current RED does not rely on wrong failure substrings. All six negative cases fail earlier because current acceptance returns `0`; therefore a future GREEN must both reject the mutation and emit a matching `FAIL:` line.

## Gaps

- The expected failure strings for top-level `defaults` and top-level `BASH_ENV` are intentionally broad: `워크플로를 정규 형식으로 읽지 못했다`. This is acceptable for the RED commit because current behavior is false PASS, but a later GREEN review should verify the precise top-level key reason if that precision matters.
- The test uses a synthetic verdict fixture. That is fine for this regression scope because these tests target workflow/selector/verdict-prefix false passes, not the independent-review semantic truth issue from the earlier report.

## Risks

- `scripts/verify/list-workflow-steps.py` is currently `AM` in git status from other work. This review treats current file contents and SHA `c8630fc...` as the proof target and does not revert or edit them.
- Pytest/ruff/mypy may touch local cache directories. The reviewed source and product/acceptance fingerprints did not change during my captured run.

## Stop Condition

This is sufficient as tests-only RED evidence before product fix. Do not claim product fix completion from this; after implementation, rerun the same pytest plus the normal hs-kickoff acceptance/mutation gates and require the six negative cases to become PASS for the right failure reasons.
