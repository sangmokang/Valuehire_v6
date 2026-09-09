## Verdict
- PASS

Scope: requested bounded V2 verification for PR37 policy canonicalization/hardening at current HEAD `594b595632dc7e9cdbaf2e0b104b35872c28a300`. I did not run the full pre-push suite or remote CI because root was running those separately.

## Evidence
- Current verified HEAD: `594b595632dc7e9cdbaf2e0b104b35872c28a300`.
- Full pre-push was reported by root as complete at `594b595` with 29 PASS and exit 0; V2 did not rerun it.
- Original failing baseline artifact: `v2-current-independent-reproduction.md/json` captured HEAD `74e183032352017b8ea8d205a58091b131d177b7`.
- Baseline extra counterexample artifact: `v2-baseline-extra-counterexamples.md/json` captured the missing 74e1830 failure-count mutant and supplied V1 whitelist fake runs.
- Fixed snapshot artifact: `v2-fixed-7dec.md/json` captured committed snapshot beginning at stream HEAD `0db449f81900b77302e4b8cd37abe8d2275f7158`. Work-unit policy code was later unchanged through `594b595`.
- Final docs/range artifact: `v2-final-report-evidence.md/json` captured current HEAD `594b595632dc7e9cdbaf2e0b104b35872c28a300`.
- Corrected evidence-doc path artifact: `v2-final-evidence-docs-corrected.md/json`, exit 0 for dated V1/evidence/pr-body files.

## Baseline vs Fixed
| Check | 74e1830 result | Fixed/current result | Verdict |
|---|---:|---:|---|
| Normal policy checker/acceptance/contract/mutation/meta | exit 0 | exit 0 | PASS |
| YAML merge key `<<` with `claims_per_unit: 2` shadowed by explicit `1` | exit 0, `VERDICT: PASS`, `POLICY_CHECKED: 22` | exit 1, `POLICY_SCHEMA_INVALID: merge key...`, `POLICY_CHECKED: 0` | fixed |
| Policy module SyntaxError | exit 1 Ruby stacktrace, no `NOT_RUN` | exit 2, `VERDICT: NOT_RUN`, `policy runtime unavailable (SyntaxError)` | fixed |
| Stronger positive gate that rejects fake `PASS22` | meta test exit 1 | meta test exit 0 | fixed |
| `aliases: true` mutant | contract test exit 0 | contract test exit 1 | fixed |
| Failure-count constant forgery | contract test exit 0 after replacing failure-path `POLICY_CHECKED: #{checked}` with constant `22` | contract test exit 1 | fixed |
| V1 whitelist fake checker | supplied `v1-whitelist-fake-checker.rb` contract test exit 0 on 74e1830 | contract test exit 1 and gates meta exit 1 | fixed |
| Ruby unavailable D7 | old e967 runner attempt invalid; discarded | direct acceptance exit 2; run-acceptance wrapper exit 2 | fixed |
| Ruby guard deletion mutant | old e967 runner attempt invalid; discarded | contract test exit 1, showing old `exit=127`/`VERDICT: FAIL` would be caught | covered |

## Code/Contract Anchors
- `scripts/verify/work_unit_policy.rb:59-62` performs AST duplicate/merge-key precheck before `Psych.safe_load(... aliases: false)`.
- `scripts/verify/check-work-unit-policy.rb:9-13` rescues `SyntaxError` as `NOT_RUN` exit 2.
- `scripts/verify/work-unit-policy-contract-test.rb:58-60` adds valid-schema alias and inline/shadowed merge fixtures.
- `scripts/verify/work-unit-policy-contract-test.rb:75-96` emits/replays `WORK_UNIT_PROPERTY_SEED`; replay passed with seed `178932400608507206198734046811340924089`.
- `scripts/verify/work-unit-policy-contract-test.rb:136-147` checks failure `POLICY_CHECKED` values instead of accepting a constant 22.
- `scripts/verify/work-unit-policy-contract-test.rb:174-190` checks no-Ruby direct and wrapper behavior.
- `scripts/verify/work-unit-policy-gates-test.rb:68-72` records fake `PASS22` positive-gate behavior without requiring the positive gate to be foolable.
- `scripts/verify/work-unit-policy-gates-test.rb:80-92` adds meta mutants for forged failure count, aliases enabled, and float equality.

## Docs/Main Integration
- `git diff --name-status 7dec976..HEAD` shows docs-only changes after the policy-code validation commit.
- `git diff --name-status 7dec976..HEAD -- <work-unit policy/code paths>` returned empty output, so the verified work-unit code path was unchanged through final HEAD.
- `wc -c docs/sot/coding-principles.md` returned `19974`, below the 20000-byte SOT limit.
- `bash scripts/check-docs-sot.sh` exit 0.
- Mechanical slice compare of the P1-P24 table in `docs/sot/coding-principles.md` against `7dec976` returned `PASS: coding principles P1-P24 table bytes unchanged`.
- Corrected dated evidence files exist: `pr37-resolution-evidence-2026-09-10.md`, `pr37-resolution-v1-verdict-2026-09-10.md`, `pr37-resolution-v1-recheck-verdict-2026-09-10.md`, `pr37-resolution-v1-delta-verdict-2026-09-10.md`, and `pr37-resolution-pr-body-2026-09-10.md`.

## Gaps
- V2 did not rerun full `hooks/pre-push` or remote GitHub CI. Root reported full pre-push complete at `594b595` with 29 PASS and exit 0.
- Baseline extra check was intentionally limited to two missing reproductions: failure-count constant forgery and supplied V1 whitelist fake. No normal suite or meta suite was rerun for that addendum.
- I did not expand into RuntimeError/NoMethodError or invalid property seed handling because those are outside the stated T contract and root explicitly asked not to expand into new areas.
- Early `v2-fixed-e967` no-Ruby/guard results using `bash -lc` are invalid proof and superseded by `v2-fixed-7dec` direct `Open3` execution.

## Risks
- V1 D1 should not be phrased as “same-authority fake prevention is impossible/solved” in absolute terms. The verified claim is narrower: the supplied whitelist fake and the count/alias/float mutants are now caught by the current contract/meta tests.
- Merge readiness still depends on remote CI evidence for the final delivery commit, not on V2's bounded local artifact checks or any earlier SHA.
