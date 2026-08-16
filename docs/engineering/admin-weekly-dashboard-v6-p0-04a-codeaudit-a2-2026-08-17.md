CODEAUDIT SPEC v2

1. verdict

FAIL / REQUEST_CHANGES. 후보 `2325103e5b7f8553c30b8f591f5760befb5b4b76`는 `.gitignore` 기능 자체는 재현상 맞지만, P0-04A 합격 조건은 못 맞춥니다. 이유는 두 가지입니다: 허용 파일 밖의 새 `scripts/acceptance-admin-*.sh`를 추가했고, 정본 명령인 `bash scripts/verify/check-admin-foundation.sh artifact-ignore`는 여전히 `unsupported-selector`로 실패합니다.

P0/P1/core P2: P0=0, P1=2, core P2=0.  
Effects: source worktree write 0, external/network/live call 0, disposable clone mutation only.  
NOT_RUN: lifecycle verification, artifact generation, pnpm install/runtime, external systems, global conversation-history search.

2. requirement/claim matrix

| ID | requirement/claim | verdict | evidence | gap/refutation | severity |
|---|---|---|---|---|---|
| R1 | exact allowed files only: `.gitignore`, `scripts/verify/check-admin-foundation.sh`, P0-04A goal doc | FAIL | `docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md:86` defines allowed files; diff base..candidate adds `scripts/acceptance-admin-weekly-dashboard-v6-p0-04a-generated-artifact-ignore.sh` | `scripts/verify/check-admin-foundation.sh` unchanged | P1/HIGH |
| R2 | canonical verifier command is `bash scripts/verify/check-admin-foundation.sh artifact-ignore` | FAIL | phase plan `:88-89`; actual run: `FAIL: unsupported admin foundation selector: artifact-ignore`, rc=2; selector allow-list at `scripts/verify/check-admin-foundation.sh:5` excludes `artifact-ignore` | standalone renamed verifier is not equivalent | P1/HIGH |
| R3 | no split of new admin acceptance bundle | FAIL | `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:175-180` says new admin checks update acceptance script, CI, verification table, mechanism registry together; `:184` requires admin foundation to compare acceptance set vs CI set | candidate adds standalone acceptance script without CI/SOT/registry/admin mutation bundle | P1/HIGH |
| R4 | candidate artifact ignore behavior 5/5/0/5 | PASS_BEHAVIOR_ONLY | disposable run: `receipt required=5 checkedIgnored=5 trackedForbidden=0 target=5`, rc=0 | behavior cannot override scope/canonical-command failure | none |
| R5 | two ignore-removal RED receipts | PASS_BEHAVIOR_ONLY | `drop-node-modules` and `drop-next`: `required=5 checkedIgnored=4 trackedForbidden=0 target=5 reason=ignore-coverage` | mutation harness returns rc=0 because it asserts expected RED receipt | none |
| R6 | force-tracked canary detects 5/5/1/5 correct reason | PASS_BEHAVIOR_ONLY | `tracked-canary`: `required=5 checkedIgnored=5 trackedForbidden=1 target=5 reason=tracked-forbidden-artifact` | temp clone only | none |
| R7 | normal source remains visible | PASS | `git check-ignore --no-index` rc=1 for `package.json`, `pnpm-lock.yaml`, `apps/admin/package.json`, `apps/admin/src/index.ts`; `.gitignore:13-15` anchors only admin artifact dirs | no broad admin source ignore found | none |
| R8 | prior P0-02/P0-03/P0-04 regressions preserved | PASS | `node-version`, `pnpm-version`, `root-workspace` all rc=0 | pnpm runtime still NOT_RUN | none |
| R9 | exposure/baseline | PASS | `scan-data-exposure.sh all`: tracked 115 files 0 violations; history 491 blobs 0 violations; csv/tsv/sql 0 files, PII 0 | admin artifact generation NOT_RUN | none |
| R10 | trailers/effects | PASS_LIMITED | RED/intermediate/candidate all have Lore trailers; no network/write API found; `git status --short` clean after source audit | writer summary is not evidence | none |

3. key-flow

The intended flow is: Phase plan -> `scripts/verify/check-admin-foundation.sh artifact-ignore` -> `.gitignore` boundary -> receipt. That flow is broken at the verifier entrypoint: `scripts/verify/check-admin-foundation.sh:5` only accepts `node-version`, `pnpm-version`, and `root-workspace`.

The actual implemented flow is a new standalone script at `scripts/acceptance-admin-weekly-dashboard-v6-p0-04a-generated-artifact-ignore.sh:1`. It checks five canary paths at `:6-12`, counts ignored paths with `git check-ignore --no-index` at `:37-48`, counts tracked forbidden artifacts at `:50-61`, and runs mutation modes at `:163-180`. That proves useful behavior, but it is not the SOT call path.

4. missed-better-answer

The correct writer answer should have said: “`.gitignore` behavior passes under a standalone experimental verifier, but P0-04A is not passable until the logic is wired into `scripts/verify/check-admin-foundation.sh artifact-ignore`, with no new `acceptance-admin-*` script in this micro.” If adding an admin acceptance script was truly desired, the writer needed the indivisible bundle in `replacement-goal:175-184`, not a renamed one-off verifier.

5. adversarial rebuttal

Strongest defense: commit `2325103e...` itself is `.gitignore`-only, and the RED/intermediate commits supplied the verifier before the candidate.

Rebuttal: PASS was defined over the exact allowed-file candidate/audit surface from P0-04 PASS, not merely the final single commit diff. `git diff --name-status f91b59c7..2325103e` contains the forbidden new acceptance script, and the canonical command remains unsupported. A staged RED verifier cannot be a standalone admin acceptance script when the SOT requires `check-admin-foundation.sh artifact-ignore` for this micro.

6. evidence ledger

Hashes: base/P0-04 PASS `f91b59c7cd8e0c423f83225336ce61d46bb72597`; audit metadata SHA `25b5fd8a23ae6c8d47f9ed66e8734a15873b58b5f733032b1e304a9c7103e87f` confirmed at `docs/engineering/admin-weekly-dashboard-v6-p0-04-codeaudit-a3-metadata-2026-08-17.md:12`; RED `d97d89a599307362858276dc3002b881be361765`; intermediate `c8141265df6b1da96152fbbebdd948eb89287694`; candidate `2325103e5b7f8553c30b8f591f5760befb5b4b76`.

Raw outputs:
```text
git diff --name-status f91b59c7..HEAD
M .gitignore
A docs/engineering/admin-weekly-dashboard-v6-p0-04a-generated-artifact-ignore-goal-2026-08-17.md
A scripts/acceptance-admin-weekly-dashboard-v6-p0-04a-generated-artifact-ignore.sh

CANONICAL_COMMAND
FAIL: unsupported admin foundation selector: artifact-ignore
... reason=unsupported-selector
CANONICAL_COMMAND_RC=2

CANDIDATE_232
receipt required=5 checkedIgnored=5 trackedForbidden=0 target=5
PASS: P0-04A generated artifact ignore coverage
```
→ 좋은 소식은 `.gitignore` 동작입니다. 나쁜 소식은 합격 기준인 파일 범위와 정본 명령이 깨졌다는 점입니다.

Diagnostics: `lsp_diagnostics` attempted on all three modified files; diagnosticCount 0, but command says `tsc skipped: no tsconfig found`. `ast-grep` unavailable; grep fallback found no secret/network/fallback blocker. `bash -n` passed for changed shell scripts.

7. repetition result

현재 제공된 task payload와 repo-local evidence만 검색했습니다. 전역 Codex 대화 보관함은 검색하지 않았습니다. 이 범위에서 같은 P0-04A a2 audit 요청 반복 횟수는 확정 불가입니다.

8. validation limits

NOT_RUN: lifecycle verification, real artifact generation, pnpm install/build/test/runtime, external services, full CI execution, global conversation-history search. Disposable clone path was `/var/folders/.../tmp.KQ7OVlmwtC/repo`; source worktree `git status --short` stayed clean.

9. prioritized next action

REQUEST_CHANGES: remove the standalone `scripts/acceptance-admin-weekly-dashboard-v6-p0-04a-generated-artifact-ignore.sh`; implement `artifact-ignore` inside `scripts/verify/check-admin-foundation.sh`; keep the diff to the exact three allowed files; rerun canonical RED/GREEN/mutations using `bash scripts/verify/check-admin-foundation.sh artifact-ignore`.
