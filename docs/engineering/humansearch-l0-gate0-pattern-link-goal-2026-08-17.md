# HumanSearch L0 시작 검사 연결 수리 목표 (2026-08-17)

## 1층 — 결론

새 작업 공간을 만들면 시작 검사에 필요한 로컬 규칙이 따라오지 않아 구현을 시작할 수 없습니다.
이미 있는 안전한 연결 기능을 실행 순서에 넣고, 연결이 실제로 맞는지 다시 확인한 뒤에만 검사를
시작하도록 수리합니다.

사장님이 지금 결정하실 것은 없습니다. 실제 채용 사이트, 로그인, 후보자 정보, 세 변경 요청의 합치기,
제품 분류기 구현은 이번 수리에서 하지 않습니다.

## 2층 — 판단 근거

검사 규칙에는 저장소에 함께 넣을 수 없는 실제 값이 포함되므로 새 작업 공간에 복사하거나 변경 기록에
넣으면 안 됩니다. 저장소에는 이미 기본 작업 공간의 로컬 규칙을 새 작업 공간에서 가리키게 하는 기능이
있습니다. 문제는 HumanSearch 실행 지시서가 새 작업 공간을 만든 뒤 이 기능을 실행하지 않고 곧바로
시작 검사를 부른다는 점입니다.

검사를 약하게 만들어 로컬 규칙 없이도 통과시키는 길은 버립니다. 실제 값을 복사하는 길도 유출 위험과
중복 관리 때문에 버립니다. 기존 연결 기능을 호출하고, 연결 대상이 기본 작업 공간의 파일과 정확히
같은지, 변경 기록에 포함되지 않는지, 빈 파일이 아닌지를 다시 읽어 확인하는 길을 택합니다.

이 판단이 틀리면 두 방향으로 깨집니다. 연결 확인이 느슨하면 다른 파일을 검사 규칙으로 오인할 수 있고,
지시가 과도하면 정상적인 새 작업 공간도 계속 시작하지 못합니다. 따라서 기존 연결 기능은 재사용하되
실패를 통과시키지 않는 확인 절차를 바로 뒤에 둡니다.

### 결정 카드

**무엇을** — 새 작업 공간을 만든 뒤 기존 로컬 규칙 연결기를 실행하고, 연결 대상·내용 존재·변경 기록
제외를 확인한 다음 시작 검사를 실행합니다.
**왜** — 연결 기능은 이미 구현돼 있지만 HumanSearch 지시서의 실제 실행 순서에서 호출되지 않아 시작
검사가 실행 불가로 끝나기 때문입니다.
**버린 길** — 검사를 약하게 만드는 길과 실제 규칙을 복사하는 길을 버렸습니다. 전자는 검출력을
낮추고, 후자는 민감한 값을 불필요하게 복제합니다.
**대가** — 새 작업 공간을 시작할 때 연결 확인 단계가 추가되고, 기본 작업 공간에 로컬 규칙이 없으면
계속 중단됩니다. 이는 검사 결과를 꾸며 통과시키지 않기 위해 감수하는 제한입니다.
**되돌리기** — 이번 지시서 변경만 되돌리면 됩니다. 연결은 변경 기록 밖의 로컬 파일 하나이므로 잘못된
연결은 해당 작업 공간에서 제거하고 기존 지시서 상태로 돌아갈 수 있습니다.

## 3층 — 계약과 증거

### 1. 현재 상태

- `docs/engineering/goal-prompts/codex-humansearch-l0-surface-classifier-v2-2026-08-16.md:241-284`는
  새 작업 공간 생성·재개 뒤 `scripts/session-status.sh`를 바로 실행합니다. 이 구간에는
  `scripts/install-hooks.sh` 호출이 없습니다.
- `scripts/install-hooks.sh:22-34`는 기본 작업 공간의 `.secret-patterns`를 새 작업 공간에 상징 연결하고,
  파일이 이미 있으면 덮어쓰지 않습니다.
- `scripts/acceptance-0-2.sh:12-14`는 `.secret-patterns`가 없거나 비어 있으면 실행 불가 성적 2로
  중단합니다.
- `docs/sot/hook-contracts.md`와 `docs/sot/verification-commands.md`는 시작 검사를 실패 건수 0으로
  통과해야 하는 실제 관문으로 정합니다.

### 2. 근본 원인

저장소의 연결 기능과 HumanSearch 실행 지시서가 따로 존재하며, 지시서의 새 작업 공간 생성 경로가 연결
기능을 호출하지 않습니다. “기능이 있다”는 사실을 “실제 실행 경로에 연결됐다”로 잘못 본 것이
근본 원인입니다.

### 3. 단일 인수 기준

**AC-L0-G0-LINK.** HumanSearch 실행 지시서가 새 작업 공간을 생성하거나 기존 작업 공간을 재개하면,
기본 작업 공간의 로컬 비밀 검사 규칙을 기존 설치기로 연결하고 다음 네 조건을 모두 직접 확인한 뒤에만
시작 검사를 실행해야 합니다.

1. 연결 원본은 기본 작업 공간의 `.secret-patterns`와 정확히 같습니다.
2. 연결된 파일은 존재하고 비어 있지 않습니다.
3. `.secret-patterns`는 Git 변경 기록에 포함되지 않습니다.
4. `bash scripts/session-status.sh`의 실패 수는 정확히 0입니다.

다음 중 하나라도 가능하면 가짜 합격입니다.

- 설치기를 호출하지 않고 시작 검사부터 실행합니다.
- `.secret-patterns.default`만으로 로컬 전용 검사를 통과한 것으로 셉니다.
- 실제 규칙 파일을 복사하거나 Git에 추가합니다.
- 연결 대상이 다른데 파일이 존재한다는 이유만으로 통과합니다.
- 시작 검사 결과가 실행 불가이거나 실패 1건 이상인데 다음 단계로 갑니다.

### 4. RED 증거

```text
$ bash scripts/acceptance-0-2.sh
FAIL: .secret-patterns 없음/빈 파일 — AC 판정 불가
ACCEPTANCE_EXIT=2

$ 지시서의 새 작업 공간 생성부터 시작 검사까지 설치기 호출 순서를 검사
INSTALL_LINE=MISSING
STATUS_LINE=39
PROMPT_ORDER_EXIT=1
```

→ 첫 명령은 로컬 규칙이 연결되지 않아 검사를 실행할 수 없다는 성적 2를 냈습니다. 두 번째 검사는
시작 검사보다 앞선 설치기 호출이 지시서에 없음을 확인해 성적 1을 냈습니다. 둘 다 현재 상태가
불합격이라는 증거입니다.

### 5. Harness 게이트 진행

- Gate 0: 현재 RED를 재현했습니다. 이 선행 수리 외 제품 작업은 시작하지 않습니다.
- Gate 1: 이 문서의 단일 인수 기준 `AC-L0-G0-LINK`로 고정했습니다.
- Gate 2: 기존 `task/docs-snapshot` 작업 공간과 PR #15를 재사용합니다. 이는 PR #15 실행 지시서에
  발견된 검토 결함을 같은 요청에서 고치는 작업이며 새 제품 인수 기준을 섞지 않습니다.
- Gate 3: 지시서 순서 검사와 실제 `acceptance-0-2.sh` 실패를 RED로 남겼습니다.
- Gate 4: 수리 뒤 같은 검사, 전체 시작 검사, 문서 검사, 비밀 검사, 변경 공백 검사를 실행합니다.
- Gate 5: 검증이 모두 합격하면 일반 push로 PR #15를 갱신하고 원격 제목·본문·검사 결과를 다시 읽습니다.
- Gate 6: PR #13·#14·#15 합치기, 제품 구현, 실제 사이트 접근은 하지 않습니다.

### 6. 적대검증 항목

1. 설치기 호출 문장만 추가하고 실제 연결 대상 확인을 빼먹지 않았는가.
2. 연결 대상 비교가 상대 경로·다른 작업 공간·이미 존재하는 잘못된 파일에 속지 않는가.
3. 로컬 규칙을 복사하거나 Git에 추가하는 유출 경로가 생기지 않았는가.
4. 시작 검사 실행 불가를 실패 0건으로 오인할 수 있는가.
5. 새 작업 공간 생성 경로와 기존 작업 공간 재개 경로가 모두 같은 준비 절차를 타는가.
6. PR #13·#14·#15가 아직 합쳐지지 않은 상태에서 제품 코드가 바뀌었는가.
7. Claude 판정의 모든 명령·줄 근거를 Codex가 직접 재현할 수 있는가.

### 7. SOT 체크리스트

- [x] `docs/sot/INDEX.md` — 기능별 계약과 날짜가 있는 실행 증거의 위치를 확인했습니다.
- [x] `docs/sot/coding-principles.md` — P3 실행 불가 은폐 금지, P6 실행 환경, P12 실제 연결,
  P13 검사 약화 금지, P15 우회 금지를 확인했습니다.
- [x] `docs/sot/git-workflow.md` — main 직접 수정 금지와 기존 작업 요청의 검토 결함을 같은 가지에서
  고치는 경계를 확인했습니다.
- [x] `docs/sot/hook-contracts.md` — 설치기와 시작 검사의 입출력 계약을 확인했습니다.
- [x] `docs/sot/verification-commands.md` — 이 저장소의 실제 Gate 0 명령을 확인했습니다.
- [x] `docs/sot/humansearch-l0-surface-contract.md` — 제품 분류 계약은 이번 수리에서 바꾸지 않습니다.
- [x] 사용자 제공 `AGENTS.md` — 증거 우선, Lore 커밋, 자동 합치기 금지를 적용합니다.

### 8. 비범위

- `humansearch/src`와 `humansearch/tests` 제품 코드
- PR #13·#14·#15의 합치기 또는 자동 합치기
- 실제 포털, 브라우저, 로그인, 세션, 자격증명 내용, 후보자 개인정보
- 회수 가능한 Git 객체 삭제, 강제 갱신, 배포, 메일 발송
- 후속 L2/L3/runner/C1 구현

### 9. 검증 로그

지시서 변경 뒤 실제 설치기를 현재 작업 공간에서 실행하고 연결 상태를 다시 읽었습니다.

```text
$ bash scripts/install-hooks.sh
core.hooksPath = hooks
설치된 훅:
  hooks/pre-commit
  hooks/pre-push
EXPECTED=/Users/kangsangmo/Desktop/Valuehire_v6/.secret-patterns
LINKED=/Users/kangsangmo/Desktop/Valuehire_v6/.secret-patterns
EXPECTED_NONEMPTY=yes
LINK_NONEMPTY=yes
TRACKED_COUNT=0
IGNORED_RC=0
```

→ 기본 작업 공간의 로컬 규칙을 가리키는 상징 연결이 정확히 만들어졌고 원본과 연결 파일은 비어 있지
않습니다. 이 파일은 Git 추적 0건이고 무시 규칙 성적 0이므로 변경 기록에 들어가지 않습니다. 실제 규칙
내용은 읽거나 출력하지 않았습니다.

지시서 안의 실행 순서를 줄 번호로 대조했습니다.

```text
INSTALL_LINE=279
STATUS_LINE=315
PROMPT_ORDER_EXIT=0
```

→ 설치기 호출은 시작 검사 호출보다 36줄 앞에 있고 순서 검사 성적은 0입니다. 새 작업과 재개 작업은
공통 대상 경로를 정한 뒤 이 한 절을 모두 통과해야 다음 단계로 갑니다.

현재 PR #15 가지의 기존 검사와 별도 수리 PR #21의 검사 파일을 같은 작업 공간에서 차례로 실행했습니다.

```text
$ bash scripts/acceptance-0-2.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
FAIL: unreachable 객체 35건 잔존 (reflog expire/gc --prune=now 미완)
CURRENT_BRANCH_ACCEPTANCE_EXIT=1

$ bash /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/humansearch-g0-unreachable-secret-scan/scripts/acceptance-0-2.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
PASS: 0-2 — 히스토리·객체·reflog·docs 리터럴 0건, 스캐너 뮤테이션 검출 확인
REPAIR_PR_ACCEPTANCE_EXIT=0
```

→ 연결 누락은 해결됐지만 PR #15가 아직 기반으로 삼는 기존 검사는 비밀과 무관한 복구 기록 35개를
개수만으로 막아 성적 1입니다. 수리 PR #21의 같은 검사 파일을 사용하면 실제 비밀 내용 검사는 유지한 채
성적 0입니다. 따라서 #21을 먼저 오너가 합친 뒤 #15를 합치는 순서가 강제되며, 그전에는 제품 구현을
시작하지 않습니다.

수리 PR: https://github.com/sangmokang/Valuehire_v6/pull/21

### 10. 적대 검증 로그

Claude 1차 판정의 명령 전문과 본문, Codex 2차 재현 명령·출력·일치 여부를 이 절에 덧붙입니다.
