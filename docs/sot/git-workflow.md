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
- 로컬 커밋 위치 정책: HEAD가 `refs/heads/main`이면 모든 checkout에서 직접 커밋을
  거부한다(이슈 #84의 A). 기본 worktree의 HEAD가 `refs/heads/task/*`이면 개발
  커밋을 별도 위치 사유로 거부한다(이번 요청의 B). 정상 허용 범위는 분리된
  `worktrees/<name>/`의 `task/<name>` 브랜치이며 기존 비밀·약화 훅도 통과해야 한다.
  기본 worktree는 Git의 `--git-dir`과 `--git-common-dir` 실제 경로가 같은 checkout이다.
  이 로컬 위치 정책은 다른 브랜치·detached HEAD의 일반 커밋에 대한 보호를
  주장하지 않는다. 표준 훅은 `git commit --no-verify`로 건너뛸 수 있다.
- PR = 인수 기준 1개. **squash merge**, 머지 후 브랜치 삭제
- 릴리스 = `main` 의 어노테이트 태그 `v6.YYYY.MM.DD-N` → CI가 artifact 빌드 → digest 산출 → `releases/<digest>/` 설치
- **자동 병합 금지.** 오너가 diff를 실제로 읽는 것이 P11(코드 예산)의 존재 이유

## 시행 지점

- 워크트리 생성: `git worktree add worktrees/<name> -b task/<name>` (이 저장소엔 아직 `make task`가 없다 — `docs/sot/verification-commands.md` 참고)
- `main` 보호(직접 push 금지)는 아직 GitHub 브랜치 보호 규칙으로 기계 강제되어 있는지 실행으로 재확인 필요 — 이 문서 갱신 시점 기준 미확인.
- 로컬 `hooks/pre-commit`은 빠른 커밋 시점 가드레일이다. CI는 개발자의 기본
  worktree 위치를 관찰할 수 없다. 최종 main 보호는 GitHub branch protection,
  PR 및 최종 SHA의 CI 검증이 담당한다. 실제 원격 보호 설정은 이 작업에서 미확인.

## 비범위 / 한계

- CI가 각 원칙(P1~P22)을 어떻게 강제하는지의 전체 매핑표는 여기 옮기지 않았다 — 원본 goal 문서 §4 "CI가 강제할 것"에 있다.
- `main` 브랜치 보호 규칙의 실제 GitHub 설정 여부는 이 문서 작성 시점에 실행 확인하지 않았다(범위 밖) — 필요 시 `gh api repos/:owner/:repo/branches/main/protection`로 확인한다.
