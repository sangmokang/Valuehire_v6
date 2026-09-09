# HumanSearch 미병합 6건 처분표 — 2026-09-09

기준: `main` = `01495b3`(= origin/main, 2026-09-09 재확인). 실측 명령은 각 행의 근거 열에 있다.
결론 어휘는 `병합요청 | 재작성 | 폐기` 세 가지뿐이다. 이 표는 **추천**이며 병합·폐기 실행은 사장님 몫이다.
검사: `scripts/acceptance-hs-kickoff.sh` 가 이 표에서 6행의 `결론=` `근거=` 를 기계로 센다.

## 1층 — 결론

6건 중 **병합요청 0, 재작성 3, 폐기 3.** 병합 버튼을 바로 누를 수 있는 것은 없다 — 열린 PR 셋은 전부 `main` 과 충돌하거나 CI 가 빨갛다. 폐기 3건은 내용이 이미 `main` 에 들어가 있어 잃는 것이 없다.

## 2층 — 처분표

| # | 대상 | 결론 | 근거 | 다음 행동 |
|---|---|---|---|---|
| 1 | PR #13 `task/humansearch-g3-portal-constants` (G3, 로컬 57·origin 56커밋) | 결론=재작성 | 근거=브랜치 tip `2d5280d`; `gh pr view 13` → `CONFLICTING DIRTY`; `gh pr checks 13` → verify pass(2026-08 head 기준). 브랜치가 main 대비 29커밋 뒤짐(`git rev-list --count task/humansearch-g3-portal-constants..main`=29) | main 위로 rebase → CI 재실행 → 병합요청. WU-5(Discord) 선행 조건이므로 우선 |
| 2 | PR #54 `task/hs-cdp-handshake-proof` (5커밋) | 결론=재작성 | 근거=브랜치 tip `0b34d93`; `gh pr view 54` → `MERGEABLE UNSTABLE`; `gh run view 33030699472 --log-failed` → 실패 스텝 "억제 만료 스캔 (suppressions.yaml)"(2026-08-27). 코드 결함이 아니라 억제 만료 | main 최신으로 rebase 후 CI 재실행. 초록이면 병합요청 |
| 3 | PR #15 `task/docs-snapshot` (문서 22파일 5,382줄) | 결론=폐기 | 근거=브랜치 tip `a7a0453`; 회수 완료본 `docs/engineering/goal-prompts/humansearch-L0-kickoff-2026-08-16.md`; `gh pr view 15` → `CONFLICTING DIRTY`; `git diff --name-only main...origin/task/docs-snapshot` 22건 중 15건은 이미 main 에 존재(L0 계약은 PR #26, 클린룸 계획은 PR #41 로 회수됨). Active Tab Bridge 계획은 D0(PR #34)가 기각 | PR 닫기. **미회수 문서 7건**은 별도 docs PR 로 회수: `goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md`, `humansearch-l0-autonomous-harness-claude-v1-2026-08-16.md`, `…-claude-v1-final-2026-08-16.md`, `…-codex-v2-2026-08-16.md`, `…-repair-goal-2026-08-16.md`, `humansearch-l0-gate0-pattern-link-goal-2026-08-17.md`, `humansearch-l0-v2-verification-repair-goal-2026-08-16.md` |
| 4 | 브랜치 `task/hs-d1-permit` (2커밋, PR 없음) | 결론=재작성 | 근거=`git log --oneline main..task/hs-d1-permit` → `c9470a8` "실제 화면 읽기가 소비된 승인 없이는 시작되지 못하게 한다", `c5138f2` RED. `humansearch/tests/test_observe_permit.py` 374줄 | WU-2(`hs-d1-neutral`)가 이 2커밋을 cherry-pick 으로 흡수. 브랜치는 WU-2 PR 병합 뒤 삭제 |
| 5 | 브랜치 `task/hs-l1-malformed-url-fix` (3커밋, PR 없음) | 결론=폐기 | 근거=`git diff main task/hs-l1-malformed-url-fix -- humansearch/src/humansearch/observe.py` → main 쪽이 더 넓은 실패 갈래(`RecursionError`, `InvalidURL`, IDNA, 고립 서로게이트)를 이미 처리. 브랜치는 그 이전 판본. PR #42(`eadab45`)가 대체 | 브랜치 삭제 |
| 6 | 브랜치 `task/hs-observe-url-crash` (54커밋, 워크트리 없음) | 결론=폐기 | 근거=`git diff --name-only main...task/hs-observe-url-crash` 19파일 전부 main 에 존재(`git cat-file -e main:<path>` 19/19) — PR #42 squash 병합과 `docs/engineering/evidence/hs-observe-url-crash/*`, `docs/engineering/hs-observe-url-crash-goal-2026-08-25.md`, `docs/engineering/verdicts/hs-observe-url-crash.verdict.json` 회수 완료 | 브랜치 삭제 |

## 3층 — 함께 기록하는 것(처분 대상 아님)

- `worktrees/resume-evidence-supabase-prompt` 의 untracked 3건: 설계서 2건은 이 PR 에서 `docs/engineering/history/` 로 보존(v4 전제 역사 기록 머리말). `scripts/experiments/profile-archiver-long-page-benchmark.mjs` 는 v4 경로(`Valuehire_v4/tools/profile-archiver`)를 참조하므로 **커밋하지 않는다**(G1). 필요하면 사장님 로컬 보관.
- `main` 작업트리의 untracked `docs/engineering/admin-weekly-dashboard-phase-e-position-cards-goal-2026-09-01.md` 는 관리자 대시보드 트랙(PR #66 계열) 소유 — 이 PR 은 건드리지 않는다.
- 등록이 끊긴 잔재 디렉터리 `worktrees/hs-l1/`, `worktrees/humansearch-g2-gates/`(`git worktree list` 에 없음, `humansearch/`·`.omc/` 만 남음) — 삭제 후보. 이 PR 범위 밖.
