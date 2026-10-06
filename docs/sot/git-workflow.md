# Valuehire v6 — Git/브랜치 전략 (SOT)

최종 갱신: 2026-10-07
근거: `docs/engineering/v6-coding-principles-goal-2026-08-06.md` §4

## 현재 규칙

### 결론: Trunk-based + 수명 짧은 worktree 브랜치 + 태그 릴리스

**GitFlow REJECT.** develop/release/hotfix 분기는 여러 팀의 병렬 릴리스 트레인을 조율하는 장치다.
1인에게는 조율 대상이 없어 순수 오버헤드이며, 더 나쁜 것은 **장수 브랜치 + LLM 생성 코드 = 대형 충돌**이고
**LLM은 충돌을 "코드를 새로 지어내서" 해결한다. v4의 자동로그인 6벌이 그 산물이다.**

**worktree는 브랜치 전략이 아니라 작업 공간 격리 메커니즘**이며 trunk-based와 결합된다.
작업 1개 = worktree 1개 = 브랜치 1개 = 인수 기준 1개.

### 규약

- `main` 보호. 직접 push 금지. **오너 본인도 예외 없음**
- 작업 브랜치 `task/<name>`, 위치 `worktrees/<name>/`, **수명 24~48시간 상한**. 초과 = 인수 기준이 너무 크다는 신호(v4: 워크트리 77개·미병합 브랜치 113개가 방치된 실측 사례)
- PR = 인수 기준 1개. **squash merge**, 머지 후 브랜치 삭제
- 릴리스 = `main` 의 어노테이트 태그 `v6.YYYY.MM.DD-N` → CI가 artifact 빌드 → digest 산출 → `releases/<digest>/` 설치
- **자동 병합 금지.** 오너가 diff를 실제로 읽는 것이 P11(코드 예산)의 존재 이유

## 시행 지점

- 워크트리 생성: `git worktree add worktrees/<name> -b task/<name>` (이 저장소엔 아직 `make task`가 없다 — `docs/sot/verification-commands.md` 참고)
- `main` 보호는 GitHub ruleset `main-pr-verify-gate`(id 23568184)가 강제한다(2026-10-07 적용·실측). 규칙: ① PR 필수(승인 0명 — 1인 저장소에서 작성자는 자기 PR 을 승인할 수 없으므로 1명 이상이면 교착) ② 필수 검사 `verify`(GitHub Actions 발행분만 인정, integration_id 15368) 통과 ③ main 최신 기준 갱신 필수(strict). 우회 권한자 없음.
- 실측 근거와 이전 규칙(`acceptance` 배포 요구 — 배포 경로가 없어 정직한 PR 은 영구 차단, API 로 만든 가짜 배포로는 통과)의 폐기 사유: `docs/engineering/merge-governance-goal-2026-10-07.md`.
- 확인 명령: `gh api repos/:owner/:repo/rules/branches/main` (기대: `pull_request` 와 `required_status_checks[verify]` 두 규칙).
- PR 관제: `bash scripts/pr-triage.sh` (🔴 즉시 확인 / 🟢 병합 가능 / 🟡 사람 결정·대기). `.github/workflows/pr-triage.yml` 이 기본 브랜치에 들어간 뒤부터 매일 09:00 KST 에 `pr-triage` 라벨 이슈에 댓글로 남긴다(첫 예약 실행 확인 전까지는 수동 실행만 확인된 상태). 리뷰에서 재현된 결함이 있는 PR 에는 `needs-fix` 라벨을 단다(작성자는 자기 PR 에 변경 요청을 걸 수 없다).

## 비범위 / 한계

- CI가 각 원칙(P1~P22)을 어떻게 강제하는지의 전체 매핑표는 여기 옮기지 않았다 — 원본 goal 문서 §4 "CI가 강제할 것"에 있다.
- 이 저장소는 고전 branch protection 을 쓰지 않는다(`branches/main/protection` 은 404 가 정상). 보호는 위 ruleset 하나다.
- PR 이 자기 `verify.yml` 을 약화하면 그 PR 의 `verify` 도 약화된 채 초록일 수 있다 — 필수 검사는 PR 쪽 워크플로 파일로 돈다. 이 경우의 방어선은 사람의 diff 검토다(자동 병합 금지 규약).
