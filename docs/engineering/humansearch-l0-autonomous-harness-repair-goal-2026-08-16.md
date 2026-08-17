# HumanSearch L0 자율 하네스 교정 goal (2026-08-16)

## 1층 — 결론

이전 실행 지시서는 쓰지 않는다. 첫 단계와 뒤 단계를 섞어 상태 수를 잘못 늘렸고, 앞 작업이 끝나지
않았는데도 새 코드를 시작하게 만들었기 때문이다.

이번에는 첫 단계가 답해야 할 다섯 결과를 기준 문서로 고정하고, 잘못된 옛 지시는 폐기 표시하며,
앞 작업이 준비되지 않으면 아무것도 바꾸지 않는 새 실행 지시서를 만든다. 실제 채용 사이트, 로그인,
후보자 정보, 제품 코드는 건드리지 않는다.

사장님이 지금 추가로 정하실 것은 없다. 새 지시서는 준비 확인, 실패 시험, 최소 수정, 이중 검증,
서버 검사 순서를 모두 통과한 뒤에도 다음 실제 사이트 작업 앞에서 스스로 멈춘다.

## 2층 — 판단 근거

### 1. 현재 상태와 fresh evidence

- `origin/main=682f00e`다.
- `task/humansearch-g3-portal-constants=918f0b6`과 `task/file-size-gate=b4fd4a8`은 둘 다
  `git merge-base --is-ancestor <branch> origin/main`이 exit 1이었다. 즉 PR #13과 #14는 열려 있지만
  `main`에는 아직 없다.
- `task/docs-snapshot=68fded1`은 원격에 올라가 있고 PR #15가 OPEN/CLEAN이다.
- `bash scripts/session-status.sh`는 문서 worktree에서 `HEAD: 68fded1 (ahead 1 / behind 0)`,
  `ORIGIN: 682f00e`를 출력했다. 이 출력의 ORIGIN은 `origin/main` 비교값이며 문서 브랜치의
  upstream 상태가 아니다.
- 클린룸 계획 `humansearch-v6-clean-room-rebuild-goal-2026-08-12.md:373-380`은 L0에
  `UNKNOWN/HUMAN_AUTH/AUTHENTICATED/CHALLENGE/DRIFTED` 다섯 결과를 요구한다.
- 같은 계획 `:240-250`은 전체 실행 흐름에 `RECHECK/RUNNING/STOP/AUTH_CONFLICT`도 표현하고,
  `:392-398`은 이 중 재확인과 충돌 처리를 L2/L3로 미룬다.
- 같은 계획은 현재 다른 worktree의 미추적 파일이라 어떤 Git ref에서도 읽을 수 없다. 기존 프롬프트의
  `worktrees/...` 참조는 다른 실행 환경에서 깨진다.
- `git diff-tree --check 68fded1`은
  `docs/engineering/premerge-a3-a4-v1-verdict-2026-08-09.md:117`의 trailing whitespace를 잡았다.
- 기존 7-state 프롬프트는 선행 병합 확인 없음, 임의 role 여섯 개, 임의 우선순위, RED/GREEN 커밋
  혼합, Claude V1 부재, CI 증거 부재, Lore 커밋 위반을 포함한다.

### 2. 근본 원인

첫째, 계획 문서의 **화면 분류 계층**과 **전체 run 생명주기**를 같은 enum으로 읽었다. 그 결과
L0의 다섯 결과에 후속 계층의 `RECHECK`와 `AUTH_CONFLICT`를 섞고 `AUTHENTICATED`를 전체 실행의
terminal처럼 잘못 적었다.

둘째, 계획 문서를 Git에 추적하지 않은 채 절대적인 worktree 경로처럼 소비했다. 그래서 프롬프트만
복사한 실행자는 정본을 열 수 없다.

셋째, “오래 자율 실행”을 “무조건 계속 실행”으로 잘못 번역했다. 안전한 자율성은 각 단계의 입력,
증거, 실패 종료, 재개 규칙이 기계적으로 닫혀 있어야 한다. 특히 선행 PR 미병합, SOT 충돌, 라이브
접근 필요는 자동 우회 대상이 아니라 fail-closed 중단 조건이다.

## 3층 — 계약·검증 증거

### 3. 계약 결정

L0는 시간에 따른 run 상태기계가 아니라 **현재 화면 관측의 순수 분류기**다.

- 입력 role은 계획에 실제로 존재하는 `authenticated_surface`, `human_auth_surface`,
  `challenge_surface` 세 개뿐이다.
- 출력은 `UNKNOWN`, `HUMAN_AUTH`, `AUTHENTICATED`, `CHALLENGE`, `DRIFTED` 다섯 개다.
- role 0개는 `UNKNOWN`이다.
- role 1개는 대응하는 정상 결과다.
- 상호 배타적인 role 2개 이상은 우선순위로 하나를 고르지 않고 `DRIFTED`다.
- `DRIFTED`는 입력 role이 아니라 모순되거나 계약 밖인 관측의 결과다.
- `RECHECK`, `AUTH_CONFLICT`, `RUNNING`, `STOP`은 L0 enum에 넣지 않는다. L2/L3와 runner가
  L0 결과를 소비해 처리한다.
- 따라서 L0에서 `AUTHENTICATED`는 성공적인 관측 결과일 뿐 전체 run의 terminal이 아니다.

이 해석은 가능한 세 role의 멱집합 8개를 전수 검사할 수 있고, 빈 화면과 모순 화면이
`AUTHENTICATED`로 새지 않는다. 임의 우선순위와 임의 role 이름도 제거한다.

## 4. 단일 인수 기준과 counter-AC

**AC-L0-HANDOFF.** When 오너가 장기 부재 중 새 Codex 세션에 v2 프롬프트를 제공하면, then 실행자는
저장소 안의 추적 가능한 L0 계약만 읽고 선행 병합을 확인한 뒤, 제품 코드 변경을 한 worktree/branch/PR로
격리하고, RED와 GREEN을 분리하고, 저장소 게이트와 두 모델의 적대검증과 CI를 모두 증명하며,
라이브 단계 전에 멈춰야 한다.

다음 중 하나라도 가능하면 실패다.

- 선행 PR이 `origin/main`에 없는데 구현을 시작한다.
- `worktrees/...` 경로, 줄 번호만 있는 비추적 문서, 현재 셸의 기억에 의존한다.
- L0에 7개 상태나 임의 role/우선순위를 다시 넣는다.
- 빈 role 또는 상충 role을 `AUTHENTICATED`로 분류한다.
- 테스트와 구현을 같은 커밋에 넣거나 GREEN에서 RED 기대값을 바꾼다.
- `--no-verify`, 자동 merge, 실제 포털, 로그인, 캡처, 개인정보를 건드린다.
- Claude 의견을 로컬 재현 없이 결함 또는 합격증으로 센다.
- PR CI가 끝나지 않았는데 완료라고 쓴다.
- 중단 후 재실행할 때 이미 만든 branch/worktree/PR을 중복 생성한다.

## 5. Harness 게이트

- Gate 0: `bash scripts/session-status.sh`; Git clean; `origin/main` fetch; PR #13/#14/#15가 `MERGED`인지
  확인하고 각 squash merge commit이 fresh `origin/main`의 조상인지 검사한다. 하나라도 exit 1이면
  제품 변경 0으로 중단한다.
- Gate 0.5: `docs/sot/INDEX.md`, `coding-principles.md`, `hook-contracts.md`, `git-workflow.md`,
  `verification-commands.md`, 새 L0 계약, 저장소 지시 파일을 읽고 충돌 순서를 기록한다.
- Gate 1: 구현 세션이 별도 날짜 goal 문서를 먼저 만들고 AC, counter-AC, 명령, 기대 출력을 적는다.
- Gate 2: 한 AC = `worktrees/humansearch-l0-surface-classifier` =
  `task/humansearch-l0-surface-classifier` = PR 한 개다.
- Gate 3 RED: 테스트·필요한 test dependency·lockfile만 커밋하고, 대상 기능 부재로 실패함을 증명한다.
- Gate 3 GREEN: 테스트 기대값을 바꾸지 않고 최소 구현과 export만 커밋한다.
- Gate 4: targeted pytest, ruff, mypy, 관련 acceptance, `bash verify.sh`, mutation을 실행한다.
- Gate 4.5: `env -u ANTHROPIC_API_KEY claude -p` V1의 전체 명령·출력을 goal에 남기고,
  Codex V2가 각 finding을 직접 재현하거나 반박한다. 불일치는 완료 금지다.
- Gate 5: clean tree에서 일반 push, 기존 PR 재사용 또는 새 PR 생성, CI terminal green 확인이다.
- Gate 6: merge·배포·live·C1은 하지 않는다. 오너가 검토할 PR과 다음 owner-gated 프롬프트만 남긴다.

## 6. 적대검증 정조준

1. 5-state 계약과 전체 run 다이어그램이 다시 합쳐지지 않았는가.
2. 세 role의 8개 조합 중 한 조합이라도 명세·시험에서 빠졌는가.
3. `frozenset`의 타입 표기만 믿고 런타임의 미지원 role을 조용히 허용하는가.
4. Hypothesis가 실제 의존성·lockfile에 추가되고 수집되는가. 시드 고정 반복문을 property test라고
   속이지 않는가.
5. RED가 문법·import 환경 오류가 아니라 기능 부재로 실패하는가.
6. GREEN 커밋이 테스트 기대값을 바꾸거나 skip/xfail을 심는가.
7. mutation에서 변경을 복구하고 clean/readback까지 확인하는가.
8. Claude V1이 문서만 읽고 승인하거나 Codex V2가 재현 없이 동의하는가.
9. push 후 PR head SHA와 로컬 SHA, CI 대상 SHA가 같은가.
10. 재개 시 existing branch/worktree/PR을 읽지 않고 중복 side effect를 만드는가.
11. PR #13/#14가 닫혔다는 사실만으로 merge를 추정하는가. ancestry가 유일한 통과 증거다.
12. L0 다음 C1을 “다음 단계”라는 이유로 자동 실행하는가.

## 7. SOT 체크리스트

- [x] `docs/sot/INDEX.md`: 제품·다음 세션이 답으로 참조할 계약은 SOT로 둘 수 있다.
- [x] `docs/sot/git-workflow.md`: main 직접 push와 자동 merge 금지; AC=worktree=branch=PR.
- [x] `docs/sot/verification-commands.md`: 실제 Gate 0/4/5 명령과 CI/pre-push 차이를 사용한다.
- [x] `docs/sot/coding-principles.md`: P2/P3/P5/P13/P15/P16/P20/P22 및 V-1~V-5를 반영한다.
- [x] `docs/sot/hook-contracts.md`: 미추적 파일이 있는 push 금지, pre-push 우회 금지, CI 최종 판정.
- [x] 사용자 제공 `AGENTS.md` 본문(현재 worktree의 파일이 아니라 세션 주입 계약): Lore commit,
  direct execution, evidence-first, no automatic merge.
- [x] 새 L0 계약과 INDEX 링크를 추가하고 staged diff로 재확인했다.
- [x] 기존 프롬프트 두 개를 실행 불가 tombstone으로 바꾸고 v2 연결을 재확인했다.
- [x] Claude V1 원문과 Codex V2 전 finding 재현을 별도 tracked 문서로 남겼다.

## 8. 비범위

- HumanSearch Python 제품 코드와 dependency/lockfile 변경
- PR #13/#14/#15의 merge 또는 main 직접 push
- 실제 채용 포털 접속, 브라우저 제어, 로그인, 세션, 캡처, 후보자 개인정보
- C1 이후 라이브 계약, 점수 계산, 후보 등록, 발송
- v5 코드 회수·복사·실행
- 브랜치 보호 설정이나 배포 환경 변경

## 9. 검증 로그

실행 결과와 해석은 작업 중 append한다. 도구를 실행하지 못했으면 `NOT_RUN`으로 남기며 PASS로
대체하지 않는다.

- `brief-lint.sh`는 이 goal, 새 L0 SOT, v2 구현 프롬프트에서 각각 위반 0건이었다.
- `git diff --cached --check`는 exit 0, 출력 0줄이었다.
- 회수 전·후 클린룸 계획의 SHA-256은 둘 다
  `04c03a11bf0b88ad3f84efbf37a3b237d735d471941f8fe5c23f39ce57273faf`였다.
- PR #13, #14, #15는 V2 재현 시점에 모두 `OPEN`, `mergeCommit=null`이었다. 이 때문에 새 구현
  프롬프트를 지금 실행해도 제품 변경 0으로 `BLOCKED`가 된다.
- 실제 채용 포털, browser, login, credential, 후보자 개인정보, 등록, 발송, merge, deploy는 모두
  `NOT_RUN`이다.
- `bash scripts/session-status.sh`는 HEAD와 ORIGIN을 출력한 뒤 원격 단계에서 2분 넘게 새 출력이 없어
  중단했고 exit 130이었다. 이를 PASS로 세지 않았다. `git rev-parse`와 `gh pr view` 개별 명령으로
  같은 핵심 상태를 재확인했다.
- `bash verify.sh`는 `PASS: no secret-pattern match in any tracked file, .env not tracked`와 exit 0이었다.
- `bash scripts/check-docs-sot.sh`는 필수 SOT와 hook 참조를 전부 확인하고 exit 0이었다.
- `bash scripts/verify/check-mechanism-registry.sh`는 명부의 세 검사기를 모두 확인하고 `CHECKED: 3`,
  exit 0이었다.
- `bash scripts/acceptance-verify-ac-m.sh`는 정상·변조 fixture 25개와 저장소 무오염을 확인하고
  `CHECKED: 25`, exit 0이었다.

## 10. 적대검증 로그

Claude V1의 정확한 명령·입력·출력 전문은
`docs/engineering/humansearch-l0-autonomous-harness-claude-v1-2026-08-16.md`에 보존했다. 첫 full V1은
`VERDICT: PASS`였고 낮은 위험 관찰 세 건을 냈다.

Codex V2의 finding별 재현 명령·출력·조치는
`docs/engineering/humansearch-l0-autonomous-harness-codex-v2-2026-08-16.md`에 보존했다. 세 건을 모두
재현했고, 현재 attempt의 RED SHA 선택과 owner-gated prompt 재개 문법을 더 정확하게 고쳤으며,
세션 주입 `AGENTS.md`의 출처도 명시했다. 기각해 숨긴 finding은 0건이다.

교정 뒤 Claude V1 전체를 한 번 더 실행했고 최종 `VERDICT: PASS`였다. 정확한 명령·입력·출력은
`docs/engineering/humansearch-l0-autonomous-harness-claude-v1-final-2026-08-16.md`에 보존했다. 최종
검증은 계약 모순, 검증 우회, 무한 반복, 권한 확장, 복원 불가, 문서 주장과 실측 불일치를 모두
0건으로 판정했다. 낮은 위험 관찰 세 건은 실행 안전에 영향이 없으며 미확인 원격 배송은 이 문서
commit 뒤 Gate 5에서 확인한다.
