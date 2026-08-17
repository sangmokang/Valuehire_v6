CODEAUDIT SPEC v2

1. verdict
auditor ID: p0_04a_codeaudit_a5. Verdict: PASS_MICRO_ONLY. P0=0, P1=0, core-P2=0. Parent AC-01/Phase 0/repo shipping remain PARTIAL/NOT_RUN. Source worktree stayed clean and unchanged: HEAD `0f93d1f1f9e61be84dd75b5e56e38e6795d7dd37`, status only branch line.

2. requirement/claim matrix
R1 구현 확인: five canary paths ignored, zero tracked; new selector exit 0 receipt `required=5 ignored=5 tracked=0 targetCount=5`.
R2-R3 구현 확인: canonical command and exact five paths at `scripts/verify/check-admin-foundation.sh:106-113`.
R4 구현 확인: candidate exit 0 with `5/5/0/5`; zero-target mutation failed closed with exit 1, not success.
R5 구현 확인: call path uses `git check-ignore --no-index` at line 121 and `git ls-files --error-unmatch` at line 127; force-track mutation failed `tracked=1`.
R6 구현 확인: RED `bd12c2e...` exit 1, receipt `required=5 ignored=2 tracked=0 targetCount=5 reason=missing-artifact-ignore`.
R7 구현 확인: node coverage removal exit 1 `5/4/0/5`; `.next` full coverage removal exit 1 `5/4/0/5`; force-track exit 1 `5/5/1/5`.
R8 구현 확인: ordinary source/config paths checked not ignored; `.gitignore:17-20` only targets admin generated dirs, no broad admin source ignore found.
R9-R10 구현 확인: base..new changed exactly `.gitignore`, `scripts/verify/check-admin-foundation.sh`, goal doc; prev..new changed exactly goal doc.
R11 구현 확인: base<=RED<=previous<=new ancestry all exit 0; RED/previous/new each parsed as seven contiguous Lore trailers in exact order.
R12 구현 확인: `bash -n` exit 0; node/pnpm/root/artifact selectors exit 0; `bash verify.sh` exit 0; data scan exit 0; source baseline preserved `RED: 1/19`.
R13 구현 확인: connected call path traced below.
R14 구현 확인: external effects 0; no Gmail/Calendar/ClickUp/Discord/email/production/network command executed.
R15 구현 확인: only PASS_MICRO_ONLY eligible; parent/Phase/repo/runtime/build/CI/live connectors remain NOT_RUN.
R16 구현 확인: goal doc covers conclusion, parent/micro, current facts, one acceptance condition, non-scope, cannot-split, RED/GREEN receipts, mutation receipts, production call path, stop conditions, external effects 0, rollback unit, parent/Phase/repo PARTIAL. Anchor validation: 48/48 unique file:line anchors existed and matched candidate content.

3. key-flow
Selector input is read at `scripts/verify/check-admin-foundation.sh:4`; `artifact-ignore` is admitted at line 6 and enters the block at line 106. The five canary inputs are line 108-112. For each input, line 121 checks ignore status, line 127 checks whether it is tracked, lines 133-136 fail tracked artifacts, lines 139-142 fail missing ignores, and lines 145-147 emit the PASS receipt and exit 0.

4. missed-better-answer
No blocking missed answer. Non-blocking clarity note: because `.gitignore` already has general `.next/` at line 12 and the candidate adds `/apps/admin/.next/` at line 17, the mutation wording “remove `.next` ignore coverage” is safer than “remove one `.next` line.” Removing only line 17 stays green; removing all `.next` coverage gives the required `5/4/0/5` failure.

5. adversarial rebuttal
Strongest counterargument: the new `/apps/admin/.next/` rule is redundant, so a line-delete mutation can pass and falsely suggest weak coverage. Rebuttal: R7 is satisfied when the coverage, not just the redundant added line, is removed; the goal doc also states existing `.next/` and P0-04A-specific `.next` rules separately. This does not inflate parent scope or hide a failing primary path.

6. evidence ledger
Hash: original request sha256 matched `b00f70061...`; private/contact values were not quoted.
History/files: ancestry exits 0/0/0; failed-audit commit `b45afa...` is not ancestor of new, exit 1; diff-check exit 0.
Receipts: RED exit 1 `5/2/0/5`; GREEN exit 0 `5/5/0/5`.
Selectors: node-version, pnpm-version, root-workspace, artifact-ignore all exit 0.
Mutations: node coverage removal exit 1 `5/4/0/5`; `.next` full coverage removal exit 1 `5/4/0/5`; force-track exit 1 `5/5/1/5 reason=tracked-forbidden-artifact`.
Baseline: disposable clone `session-status` showed `RED: 2/19` due clone-only `acceptance-0-5` origin/main mismatch plus known `acceptance-0-2`; source showed `RED: 1/19`, and source `acceptance-0-2` exit 2 from absent/empty `.secret-patterns`.

7. repetition result
NOT_RUN. The packet did not require historical repeated-question counting, and I did not search user conversation archives.

8. validation limits
NOT_RUN: admin runtime/build/test, artifact generation, install, CI, deployment, live connectors, network, credentials, PR/push/merge. One invalid anchor-check attempt was discarded because zsh `path` variable shadowing broke command lookup; the rerun with a different variable validated 48/48 anchors.

9. prioritized next action
No required code change for P0-04A. Keep final claim limited to PASS_MICRO_ONLY and do not claim AC-01, Phase 0, repository green, runtime readiness, artifact generation, CI, or external/live success.
