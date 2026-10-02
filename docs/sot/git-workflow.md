# Valuehire v6 — Git/브랜치 전략 (SOT)

최종 갱신: 2026-09-22
근거: `docs/engineering/v6-coding-principles-goal-2026-08-06.md` §4

## 현재 규칙

### 결론: 저장소는 하나, 동시 작업은 브랜치와 워크트리로 나눈다

GitHub 원격 저장소는 `Valuehire_v6` 하나다. Codex, Claude, Grok을 동시에 써도 저장소를 모델마다 복제하지 않는다.
`origin/main` 은 기준선이다. 동시에 돌아가는 세션은 각자 브랜치 하나와 워크트리 하나를 가진다.

```text
GitHub 원격 저장소
origin/main
    │
    ├─ task/<작업>  +  worktrees/<작업>/
    ├─ task/<작업>  +  worktrees/<작업>/
    └─ task/<작업>  +  worktrees/<작업>/
```

예:

```text
main                         Valuehire_v6/                 (기준선, 여기서 수정하지 않음)
├─ task/codex-search         worktrees/codex-search/
├─ task/claude-admin         worktrees/claude-admin/
└─ task/grok-invoice         worktrees/grok-invoice/
```

**GitFlow REJECT.** develop/release/hotfix 분기는 여러 팀의 병렬 릴리스 트레인을 조율하는 장치다.
1인에게는 조율 대상이 없어 순수 오버헤드이며, 더 나쁜 것은 **장수 브랜치 + LLM 생성 코드 = 대형 충돌**이고
**LLM은 충돌을 "코드를 새로 지어내서" 해결한다. v4의 자동로그인 6벌이 그 산물이다.**

**worktree는 브랜치 전략이 아니라 작업 공간 격리 메커니즘**이며 trunk-based와 결합된다.
동시 세션 1개 = 작업 1개 = worktree 1개 = 브랜치 1개 = 인수 기준 1개.
브랜치 이름에 `codex` / `claude` / `grok` 을 넣어 어느 세션이 고쳤는지 남길 수 있다.
그 이름은 이번 작업의 표식이다. 모델마다 오래 사는 전용 브랜치를 두지 않는다.

### 같은 `main` 폴더에서 동시에 고치지 않는다

Codex, Claude, Grok이 전부 같은 `main` 작업 폴더에서 파일을 고치면 변경이 한 인덱스에 섞인다.
한 세션이 다른 세션의 미커밋 변경을 덮거나, 그 변경을 자기 작업으로 읽고 커밋할 수 있다.
병렬로 돌릴 때의 순서는 이것이다.

1. `main` 은 기준선으로만 유지한다. 기본 체크아웃 `Valuehire_v6/` 에서는 기능 수정을 하지 않는다.
2. 각 작업은 `task/<name>` 브랜치를 만든다.
3. 각 세션은 `worktrees/<name>/` 에서만 파일을 고친다.
4. 작업이 끝나면 그 워크트리에서 commit 한다.
5. 검증한 것만 PR 로 `main` 에 squash merge 한다. 머지 후 브랜치와 워크트리를 지운다.

### 규약

- `main` 보호. 직접 push 금지. **오너 본인도 예외 없음**
- 작업 브랜치 `task/<name>`, 위치 `worktrees/<name>/`, **수명 24~48시간 상한**. 초과 = 인수 기준이 너무 크다는 신호(v4: 워크트리 77개·미병합 브랜치 113개가 방치된 실측 사례)
- PR = 인수 기준 1개. **squash merge**, 머지 후 브랜치 삭제
- 릴리스 = `main` 의 어노테이트 태그 `v6.YYYY.MM.DD-N` → CI가 artifact 빌드 → digest 산출 → `releases/<digest>/` 설치
- **자동 병합 금지.** 오너가 diff를 실제로 읽는 것이 P11(코드 예산)의 존재 이유

## 시행 지점

- 워크트리 생성: `git worktree add worktrees/<name> -b task/<name>` (이 저장소엔 아직 `make task`가 없다 — `docs/sot/verification-commands.md` 참고)
- 생성 뒤 그 세션의 작업 디렉터리는 `worktrees/<name>/` 이다. 기본 체크아웃으로 돌아와 이어서 고치지 않는다.
- `main` 보호(직접 push 금지)는 아직 GitHub 브랜치 보호 규칙으로 기계 강제되어 있는지 실행으로 재확인 필요 — 이 문서 갱신 시점 기준 미확인.
- 체크아웃이 세션마다 따로인 실행 환경(클라우드 에이전트 VM)은 이미 작업방이 나뉘어 있다. 그 안에서도 `main` 에 직접 커밋하지 않고 수명이 짧은 작업 브랜치를 쓴다. VM 안에 `worktrees/` 를 또 만들지 않는다.

## 비범위 / 한계

- CI가 각 원칙(P1~P22)을 어떻게 강제하는지의 전체 매핑표는 여기 옮기지 않았다 — 원본 goal 문서 §4 "CI가 강제할 것"에 있다.
- `main` 브랜치 보호 규칙의 실제 GitHub 설정 여부는 이 문서 작성 시점에 실행 확인하지 않았다(범위 밖) — 필요 시 `gh api repos/:owner/:repo/branches/main/protection`로 확인한다.
- 같은 폴더에서 동시에 고치는 일은 이 규약과 워크트리 분리로 막는다. pre-commit 은 "어느 LLM의 미커밋 변경인지"를 구분하지 않는다.
