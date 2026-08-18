# Valuehire v6 — Git/브랜치 전략 (SOT)

최종 갱신: 2026-08-18
근거: `docs/engineering/v6-coding-principles-goal-2026-08-06.md` §4

## 현재 규칙

### 결론: Trunk-based + 수명 짧은 worktree 브랜치 + 태그 릴리스

**GitFlow REJECT.** develop/release/hotfix 분기는 여러 팀의 병렬 릴리스 트레인을 조율하는 장치다.
1인에게는 조율 대상이 없어 순수 오버헤드이며, 더 나쁜 것은 **장수 브랜치 + LLM 생성 코드 = 대형 충돌**이고
**LLM은 충돌을 "코드를 새로 지어내서" 해결한다. v4의 자동로그인 6벌이 그 산물이다.**

**worktree는 브랜치 전략이 아니라 작업 공간 격리 메커니즘**이며 trunk-based와 결합된다.
작업 1개 = worktree 1개 = 브랜치 1개 = 인수 기준 1개.

### 규약

- `main` 직접 push 금지. **오너 본인도 예외 없음.** 다만 2026-08-18 GitHub API 실측은 `protected:false`이므로 현재는 운영 정책이고 서버의 기계 강제가 아니다. `review-gate`·`verify` 필수 검사 전환 전에는 “보호됨”이라고 보고하지 않는다.
- 작업 브랜치 `task/<name>`, 위치 `worktrees/<name>/`, **수명 24~48시간 상한**. 초과 = 인수 기준이 너무 크다는 신호(v4: 워크트리 77개·미병합 브랜치 113개가 방치된 실측 사례)
- PR = 인수 기준 1개. **squash merge**, 머지 후 브랜치 삭제
- 릴리스 = `main` 의 어노테이트 태그 `v6.YYYY.MM.DD-N` → CI가 artifact 빌드 → digest 산출 → `releases/<digest>/` 설치
- **자동 병합 금지.** 오너가 diff를 실제로 읽는 것이 P11(코드 예산)의 존재 이유

## 시행 지점

- 워크트리 생성: `git worktree add worktrees/<name> -b task/<name>` (이 저장소엔 아직 `make task`가 없다 — `docs/sot/verification-commands.md` 참고)
- `main` 보호는 2026-08-18 `gh api repos/sangmokang/Valuehire_v6/branches/main`으로 재확인했고 `protected:false`, 필수 검사 목록 0개였습니다. 서버 기능을 켜기 전까지 직접 push 금지는 운영 정책입니다.

## 비범위 / 한계

- CI가 각 원칙(P1~P22)을 어떻게 강제하는지의 전체 매핑표는 여기 옮기지 않았다 — 원본 goal 문서 §4 "CI가 강제할 것"에 있다.
- GitHub 요금제·권한 때문에 보호 설정 API가 거절될 수 있습니다. 보호 활성화 작업은 쓰기 전 실제 API 가용성을 다시 확인하고, 불가능하면 advisory 한계를 유지합니다.
