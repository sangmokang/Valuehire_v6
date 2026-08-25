# Valuehire v6 — Git/브랜치 전략 (SOT)

최종 갱신: 2026-08-08
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
- main 직접 push 금지는 현재 사람 규율이다. 2026-08-15 원격 조회에서 main은 `protected=false`였고,
  브랜치 보호·저장소 규칙 조회는 모두 현재 개인 계정의 비공개 저장소 요금제에서 403으로 거부됐다.
  따라서 CI는 실패 표시를 만들지만 합치기 자체를 기계적으로 거부하지 못한다. 로컬 pre-push도
  `git push --no-verify`로 우회할 수 있다. 강제하려면 GitHub Pro로 올리거나 저장소를 공개한 뒤
  `verify` 성공을 필수 상태 검사로 지정해야 한다.

## 비범위 / 한계

- CI가 각 원칙(P1~P22)을 어떻게 강제하는지의 전체 매핑표는 여기 옮기지 않았다 — 원본 goal 문서 §4 "CI가 강제할 것"에 있다.
- 위 원격 상태는 2026-08-15에 `gh api repos/sangmokang/Valuehire_v6/branches/main`과 보호·저장소
  규칙 조회로 확인했다. 계정 요금제나 저장소 공개 범위가 바뀌면 같은 명령으로 다시 확인해야 한다.
