# 다음 세션 프롬프트 — PR 적체 정리 2단계 (2026-10-07 작성)

`/clear` 후 아래를 그대로 붙여 넣는다. 이전 대화 기억 없이 실행 가능해야 한다.

---

/strict

# 역할
`Valuehire_v6`(GitHub sangmokang/Valuehire_v6, 공개 저장소) PR 적체 정리 2단계 실행자. 새 시스템을 만들지 않는다. main 직접 push 금지. 병합은 사장님 승인 후에만.

# 0. 시작 전 사실 재확인(이전 결론을 믿지 말 것)
```
git fetch origin --prune
gh api repos/sangmokang/Valuehire_v6/rules/branches/main          # 기대: pull_request + required_status_checks[verify]
gh api repos/sangmokang/Valuehire_v6/rulesets/23568184 --jq '{name,bypass_actors,rules}'
gh pr view <merge-governance PR 번호> --json state,mergeStateStatus,statusCheckRollup
bash scripts/pr-triage.sh        # 병합 전이면 브랜치 task/merge-governance-20261007 에서
git show origin/main:suppressions.yaml | grep expiry   # 10-13 만료 확인
```
기대와 다르면 그 차이부터 보고하고 멈춘다.

# 1. 지난 세션 상태 (2026-10-07 01:50 KST 기준)
- 브랜치 `task/merge-governance-20261007` (워크트리 `worktrees/merge-governance`), origin/main 55240f7 위 커밋: 8f3d5a9(RED) 48bc61a(RED) f2652b9(GREEN) 8eeb71f(배선) e09df7a(근거 문서) + 이후 V1 반영 커밋. PR 번호는 `gh pr list --head task/merge-governance-20261007` 로 확인.
- **해결한 병합 규칙 문제**: main ruleset 23568184 를 `required_deployments[acceptance]`(배포 경로 0 → 정직한 PR 영구 차단, API 가짜 배포로 통과) → `main-pr-verify-gate` = PR 필수(승인 0) + `verify`(Actions, integration 15368) 필수 + strict. 2026-10-06T16:39Z GitHub 에 이미 적용됨. 되돌리기: `gh api -X PUT repos/sangmokang/Valuehire_v6/rulesets/23568184 --input docs/engineering/evidence/merge-governance-20261007/ruleset-main-before.json`.
- 실험 근거: `docs/engineering/evidence/merge-governance-20261007/probe-matrix.md` (A·B 재현, POS/NEG/STRICT 기대대로). 임시 자원 정리 완료.
- 근거·분류 전문: `docs/engineering/merge-governance-goal-2026-10-07.md`.

# 2. PR 분류 (55개)
- MERGE_READY: #122 (herdr — S2 후속 2건, Windows 실측 미확인)
- FIX_REQUIRED: #123(S1 재현, needs-fix 라벨) #74 #75 #77 #78(10-13 억제 만료 체인, #74·#75 충돌) #109 #110 #83 #44 #45 #104 #105
- SUPERSEDED_OR_DUPLICATE: #120(#121 과 트리 동일) #118(#121 의 조상)
- STALE_NEEDS_DECISION: 갱신만 하면 판정 가능 #116 #115 #112 #102 #107 #103 / HS 계열 #85 #86 #88 #91 #92 #87 #89 #90 #93 #94 #96 #97 #100 #95 / 오래된 충돌 #14 #15 #37 #43 #48 #68 / 옛 초록 #47 #54 #61 #63 #65 #66 #67 #79 / 초안 #106 #114 #117 / 폐기 결정·대체 확인 #121(Grok API 경로 폐기 결정) #119(10-02 스냅샷) #108(핵심 파일은 f12ea33 로 main 에, 판정 문서 등 고유분 잔존)

# 3. 실행한 검증과 결과
- `acceptance-principles-check.sh` PASS 34 · `acceptance-pr-triage.sh` PASS(26판정/CHECKED 25) · 뮤테이션 10/10 KILLED · `check-mechanism-registry.sh` PASS 21 · `verify.sh` PASS · `pr-triage.sh` 실 조회 rc 0
- V1(Codex, session 01a1121d…): FAIL 5건 → 전부 재현·반영(RED 03776f0 → GREEN, CHECKED 35). 뮤테이션 18종 15 KILLED, 생존 3 은 조합 변이·중복 조항으로 등가 판별

# 4. 미실행 검증
- `pr-triage.yml` 예약 실행·이슈 생성·댓글 알림(기본 브랜치 병합 후에만 가능) → 병합 후 `gh workflow run pr-triage` 1회, `gh run watch`, 이슈 댓글 확인
- V2(새 맥락 재현) 미실행이면 여기서 실행
- R-2(10-02 이전 규칙 미평가 원인), R-3(push/PR 두 verify 결과 충돌 시 GitHub 판정) 미확인

# 5. 다음 작업 우선순위 (이 순서로)
1. **10-13 억제 만료 대응** — 만료되면 모든 PR 의 `verify` 가 실패한다. 선택지 카드를 만들어 사장님께 1개만 묻는다: (a) `suppressions.yaml` 기한 재연장 1줄 PR (b) #74→#75→#77→#78 체인을 main 기준으로 재정렬해 2건 해제(충돌 해소 필요) — gate-scope-gaps 1건은 어느 쪽이든 남는다.
2. merge-governance PR 의 CI 초록 확인 → 사장님 병합 승인 요청 → 병합 후 `pr-triage.yml` 실측.
3. "갱신만 하면 판정 가능" 6건(#116 #115 #112 #102 #107 #103)을 사장님 승인 후 `gh pr update-branch` → CI 결과로 MERGE_READY/FIX_REQUIRED 재판정. 갱신 전 그 브랜치를 쓰는 다른 세션이 없는지 확인(`git worktree list`, `lsof` cwd).
4. SUPERSEDED 2건(#118 #120)과 폐기 결정 3건(#121 #119 #108) 닫기 여부를 사장님께 한 번에 묻는다(닫기는 승인 후, 댓글에 대체 근거 링크).
5. #123 수정(needs-fix 해제 조건: D1 재현 입력이 FAIL 로 바뀜) — 별도 워크트리.
6. HS 계열 14건·오래된 충돌 6건은 사장님 결정 카드 1장으로(되살릴 것/닫을 것).

# 6. 금지
기존 PR 내용 수정·대량 신규 PR·검사 삭제/skip·게이트 우회·가짜 상태 생성·main 직접 push·후보 개인정보 커밋·사장님 승인 없는 병합/PR 닫기.
