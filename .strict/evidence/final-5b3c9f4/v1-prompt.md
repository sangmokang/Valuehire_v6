You are Claude V1, an independent read-only adversarial verifier. Do not edit, stage, commit, push, create/modify a PR, merge, deploy, or contact external services. Do not trust prior PASS/FAIL conclusions. Inspect the repository and execute only local read-only or temporary-fixture commands.

Repository: /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/wu3b-delivery-chain-20260827
Candidate: 5b3c9f4fb3798a23616078e39335f3258a644389
Base: 472c276f8c18584719319f1665c73bed61257c1a
Branch: task/wu3b-delivery-chain-20260827
Issue contract: docs/engineering/valuehire-delivery-chain-issue-2026-08-27.md
Goal contract: docs/engineering/valuehire-delivery-chain-goal-2026-08-27.md
Run ledger: .strict/run-ledger/strict-wu3b-20260827-472c276.json
Raw local command evidence (conclusions deliberately omitted): /tmp/valuehire-strict-wu3b-evidence/final-5b3c9f4

Attack all of these independently against this exact candidate:
1. fake GREEN, including multiple/conflicting final markers and PASS followed by FAIL;
2. unstaged run-ledger broadening, deletion, decoy copy, reordering, timestamp rollback, duplicate WU, mismatched WU/commit;
3. unstaged secret pattern weakening, missing/mismatched approval SHA, missing indexed scanner, scanner zero-without-verdict;
4. stale candidate, branch, worktree, nonexistent/unrelated merge commit, local evidence presented as GitHub statusCheckRollup;
5. zero targets, empty output, partial output, concurrent/repeated runs;
6. hard 600/601 and uppercase .JS/.TSX size/test weakening;
7. all five no-op mutations in tests/checkpoint-gate-mutation.test.mjs;
8. actual pre-commit, clean-clone pre-push, and CI wiring versus tests that merely exist;
9. regressions in existing acceptance scripts and whether checkpoint core tests are in the delivery/CI path;
10. WU history: RED test immutability, WU-3b-2c and WU-3b-6a invalidation, commit trailers, and claimed RED/GREEN pairs;
11. pre-merge readiness/overall T and separation of PR, CI, merge, deploy, and live verify;
12. direct-authored hard limit and any contradiction among issue, goal, SOT, code, tests, and PR draft.

Reproduce every finding with exact command, cwd, exit code, and decisive output. Cite current file:line for every code/document claim. Distinguish implementation logic from unavailable external PR/CI/merge/deploy evidence. Treat any FAIL, NOT_RUN, or BLOCKED required completion item as forbidding an overall delivery PASS. Report whether the local WU-3b logic contract itself is PASS or FAIL separately from overall delivery.

End with exactly one non-empty final marker line: FINAL: PASS or FINAL: FAIL. Do not place another FINAL marker anywhere else.
