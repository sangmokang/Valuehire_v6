# Valuehire v6 — Git/브랜치 전략 (SOT)

최종 갱신: 2026-08-21
근거: `docs/engineering/v6-coding-principles-goal-2026-08-06.md` §4,
`docs/engineering/work-unit-methodology-goal-2026-08-21.md`

## 현재 규칙

### 결론: Trunk-based + 수명 짧은 worktree 브랜치 + 태그 릴리스

**GitFlow REJECT.** develop/release/hotfix 분기는 여러 팀의 병렬 릴리스 트레인을 조율하는 장치다.
1인에게는 조율 대상이 없어 순수 오버헤드이며, 더 나쁜 것은 **장수 브랜치 + LLM 생성 코드 = 대형 충돌**이고
**LLM은 충돌을 "코드를 새로 지어내서" 해결한다. v4의 자동로그인 6벌이 그 산물이다.**

**worktree는 브랜치 전략이 아니라 작업 공간 격리 메커니즘**이며 trunk-based와 결합된다.

### Work Unit 정책의 정본

Work Unit의 개수·수명·완료 조건·검토 강도·최종 관문·롤백 경계는 `docs/sot/work-unit-policy.yaml` 한 벌이 기계 정본이다. 사람이 읽는 `docs/sot/work-unit-policy.md`는 그 YAML에서 생성하며 직접 편집하지 않는다.

이 문서는 trunk-based와 worktree의 역할만 설명한다. Work Unit 규칙을 자연어로 다시 적어 두 벌로 만들지 않는다. 정책값·순서·생성 문서의 일치는 `scripts/acceptance-work-unit-policy*.sh`가 판정한다.

### 규약

- `main` 보호. 직접 push 금지. **오너 본인도 예외 없음**
- 작업 브랜치 `task/<name>`, 위치 `worktrees/<name>/`. 수명 상한과 PR 분리 기준은 Work Unit 정책 정본을 따른다.
- PR = 사용자 결과 1개. **squash merge**, 머지 후 브랜치 삭제
- squash 뒤 롤백 경계는 Work Unit 정책 정본을 따른다.
- 릴리스 = `main` 의 어노테이트 태그 `v6.YYYY.MM.DD-N` → CI가 artifact 빌드 → digest 산출 → `releases/<digest>/` 설치
- **자동 병합 금지.** 오너가 diff를 실제로 읽는 것이 P11(코드 예산)의 존재 이유

## 시행 지점

- 워크트리 생성: `git worktree add worktrees/<name> -b task/<name>` (이 저장소엔 아직 `make task`가 없다 — `docs/sot/verification-commands.md` 참고)
- `main` 보호(직접 push 금지)는 아직 GitHub 브랜치 보호 규칙으로 기계 강제되어 있는지 실행으로 재확인 필요 — 이 문서 갱신 시점 기준 미확인.

## 비범위 / 한계

- CI가 각 원칙(P1~P22)을 어떻게 강제하는지의 전체 매핑표는 여기 옮기지 않았다 — 원본 goal 문서 §4 "CI가 강제할 것"에 있다.
- `main` 브랜치 보호 규칙의 실제 GitHub 설정 여부는 이 문서 작성 시점에 실행 확인하지 않았다(범위 밖) — 필요 시 `gh api repos/:owner/:repo/branches/main/protection`로 확인한다.
