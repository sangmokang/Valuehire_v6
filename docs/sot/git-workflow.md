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
Issue 또는 goal 문서 1개 = worktree 1개 = 브랜치 1개 = PR 1개다. PR 하나에는 Work Unit 1~5개만 둘 수 있다.

### Work Unit — PR보다 작은 증명 경계

**Work Unit은 하나의 주장만 만들고, 그 주장을 반증하는 시험까지 통과한 뒤 완료 커밋으로 닫는 최소 작업 단위다.** 파일 수나 줄 수가 아니라 실행으로 참·거짓을 가릴 수 있는 불변조건으로 나눈다.

각 Work Unit은 다음 여섯 항목을 가진다.

1. `WU-01` 같은 식별값과 하나의 주장
2. EARS 문법의 실행 가능한 인수 기준과 정확한 기대값
3. 가짜 합격을 뜻하는 counter-AC와 작은 반증 1~3개
4. 변경 범위와 선행 Work Unit
5. 위험등급과 필요한 검토 강도
6. 표적 검증을 통과해 증명이 닫힌 완료 커밋

`WU-01 = verify.yml 수정`, `WU-02 = hook 수정`처럼 파일로 나누지 않는다. `WU-01 = hs-a4 실행줄을 echo로 무력화하면 실패한다`처럼 증명하려는 사실 하나로 나누고, 필요하면 그 사실을 구현하는 여러 파일을 같은 Work Unit이 소유한다.

### RED 계약과 완료 커밋

P5의 시험 불변 계약이 Work Unit보다 우선한다. 필요한 시험이 아직 없다면 여러 Work Unit의 RED(= 기능이 없어서 시험이 실패하는 상태) 계약을 먼저 별도 커밋하고, 이후 각 Work Unit 완료 커밋은 그 시험의 기대값·skip·의존성을 바꾸지 않는다. 새 반례가 발견되면 그 반례가 실패하는 별도 RED 커밋을 먼저 만든 뒤 수정한다.

따라서 Work Unit 하나가 항상 Git 커밋 하나라는 뜻은 아니다. RED 계약 커밋은 시험을 잠그는 공통 기준선이고, 각 Work Unit의 **완료 커밋**은 “이 주장 하나의 구현·표적 검증·작은 적대검증(= 속여서 통과시키는 시도)이 끝났다”는 검토 경계다. 서로 다른 Work Unit 구현을 한 완료 커밋에 섞지 않는다.

### 목표·Work Unit·PR 관계

- Issue 또는 goal 문서 하나가 PR의 목표와 Work Unit 전체 목록을 정의한다. 목표 문서를 둘 이상 참조해야 하면 PR을 나눈다.
- worktree·브랜치·PR은 그 Issue 또는 goal 문서 하나를 소유한다.
- PR 안에는 Work Unit 1~5개만 순서대로 둘 수 있다. 여섯 번째 Work Unit이 필요하면 새 Issue 또는 goal 문서와 PR로 나눈다. 각 Work Unit은 실행 가능한 인수 기준 정확히 하나에 대응하므로 개수는 goal의 Work Unit 장부 행으로 센다.
- Work Unit마다 새 Agent·새 세션을 띄우는 것은 선택이다. 같은 세션에서도 한 Work Unit만 구현하고 표적 검증을 끝낸 뒤 다음 Work Unit으로 넘어갈 수 있다.
- 가능한 경우 구현자가 아닌 새 맥락이 반증을 맡는다. 단 외부 모델·유료 서비스·별도 오케스트레이터가 없어도 기본 절차는 중단되지 않는다.

### 규약

- `main` 보호. 직접 push 금지. **오너 본인도 예외 없음**
- 작업 브랜치 `task/<name>`, 위치 `worktrees/<name>/`, **수명 24~48시간 상한**. 초과 = 목표나 Work Unit 분해가 너무 크다는 신호(v4: 워크트리 77개·미병합 브랜치 113개가 방치된 실측 사례)
- PR = 사용자 결과 1개. **squash merge**, 머지 후 브랜치 삭제
- Work Unit 완료 커밋은 squash 전 검토·원인 격리 경계다. squash 뒤 `main`의 롤백 경계는 PR 전체 커밋이며, 특정 Work Unit만 되돌릴 때는 해당 변경을 역적용하는 새 커밋을 만든다.
- 릴리스 = `main` 의 어노테이트 태그 `v6.YYYY.MM.DD-N` → CI가 artifact 빌드 → digest 산출 → `releases/<digest>/` 설치
- **자동 병합 금지.** 오너가 diff를 실제로 읽는 것이 P11(코드 예산)의 존재 이유

## 시행 지점

- 워크트리 생성: `git worktree add worktrees/<name> -b task/<name>` (이 저장소엔 아직 `make task`가 없다 — `docs/sot/verification-commands.md` 참고)
- `main` 보호(직접 push 금지)는 아직 GitHub 브랜치 보호 규칙으로 기계 강제되어 있는지 실행으로 재확인 필요 — 이 문서 갱신 시점 기준 미확인.

## 비범위 / 한계

- CI가 각 원칙(P1~P22)을 어떻게 강제하는지의 전체 매핑표는 여기 옮기지 않았다 — 원본 goal 문서 §4 "CI가 강제할 것"에 있다.
- `main` 브랜치 보호 규칙의 실제 GitHub 설정 여부는 이 문서 작성 시점에 실행 확인하지 않았다(범위 밖) — 필요 시 `gh api repos/:owner/:repo/branches/main/protection`로 확인한다.
