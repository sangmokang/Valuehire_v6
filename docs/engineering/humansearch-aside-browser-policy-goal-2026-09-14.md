# HumanSearch HS-05.01 Aside 브라우저 정책 계약 goal — 2026-09-14

## 1층 — 결론

최신 결정은 HumanSearch 실제 채널을 Chrome이 아니라 Aside로 고정한다. 이 작업은 실제 브라우저를 조작하지 않고, 문서 정본과 기계 계약이 그 결정을 빠뜨리면 실패하게 만드는 범위다.

실제 포털 접속, RPS 프로젝트 생성, LinkedIn 상세 저장, 채널 순서 개정은 이 작업의 완료 증거가 아니다. 이 작업의 배송 상태는 문서·검사 변경이므로 `NOT_APPLICABLE`이다.

## 2층 — 판단 근거

기존 `docs/sot/humansearch-browser-contract.md`는 사람인·잡코리아 전용 프로필과 LinkedIn 실프로필의 차이를 설명하지만, 2026-09-14 사용자가 정한 Aside 전용 자동화와 Chrome 비간섭을 정본으로 고정하지 못한다. 그래서 후속 구현자가 과거 Chrome/CDP 제한이나 사람 입력 감지 규칙을 이유로 이미 결정된 작업을 다시 묻거나 Chrome 작업을 건드릴 수 있다.

**무엇을** — Aside 전용 브라우저 정책을 SOT와 별도 기계 계약에 추가한다.

**왜** — 사람의 Chrome 업무와 자동화 대상 Aside 작업을 분리하고, 입력·사용권·중단·재개 판단을 대상 앱·프로필·탭에 귀속해야 하기 때문이다.

**버린 길** — 기존 SOT 문구만 일부 고쳐 둔다. 검사가 없으면 다음 작업에서 같은 문구가 빠져도 초록불이 될 수 있어 버린다.

**대가** — CI 단계와 검사 명부가 1개 늘어난다. 문서 계약 작업이라 실제 Aside 조작 성공은 증명하지 않는다.

**되돌리기** — 새 acceptance 스크립트, browser-policy 계약 파일, SOT 문단, CI/SOT 배선 줄을 같은 PR에서 제거하면 이전 D0 계약으로 돌아간다.

## 3층 — 계약

### 입력

- 사용자 최신 지시: `/Users/kangsangmo/Desktop/hs-next-prompt-v5-20260914.md`
- 적용 정본: `docs/sot/humansearch-browser-contract.md`
- 신규 기계 계약: `contracts/humansearch/browser-policy.yaml`

### 출력

- SOT는 다음을 명시해야 한다.
  - 실제 자동화 채널은 Aside다.
  - Chrome 창·탭·포트·프로필·확장·설정과 일반 입력은 건드리지 않는다.
  - 사람인·잡코리아는 Aside 전용 프로필, RPS는 Aside 안의 사장님 실제 LinkedIn Recruiter 프로필을 쓴다.
  - 사람 입력 신호는 대상 앱·프로필·탭에 귀속하며 Chrome 입력을 Aside 중단 신호로 쓰지 않는다.
  - 새 관측과 새 사용권 뒤에는 자동 재개할 수 있지만, 명시적 STOP은 새 사용자 해제 없이는 자동 해제하지 않는다.
  - 현재 확인된 AppleScript 실행 가능성과 CDP 인증 필요는 라이브 권한 충족 증거가 아니다.
- `contracts/humansearch/browser-policy.yaml`은 위 결정을 기계가 찾을 수 있는 값으로 가진다.

### EARS AC와 counter-AC

1. When 최신 Aside 정책 검사를 실행하면, 시스템은 SOT와 browser-policy 계약에서 Aside 전용·Chrome 비간섭·채널별 프로필·입력 귀속·재개/STOP 경계를 확인해야 한다.
   - 검증 명령: `bash scripts/acceptance-hs-browser-policy.sh`
   - 기대값: `VERDICT: PASS`, `CHECKED` 1 이상, 종료값 0.
   - counter-AC: SOT에 산문만 있고 기계 계약 파일이 없는데 통과한다.
2. If 문서가 “사람 입력 뒤 자동 재개하지 않는다”만 유지하면, 시스템은 최신 새 관측·새 사용권 재개 결정을 누락으로 실패해야 한다.
   - 검증 명령: `bash scripts/acceptance-hs-browser-policy.sh`
   - 기대값: 해당 문구가 남으면 종료값 1.
   - counter-AC: STOP과 일반 사람 입력을 구분하지 않고 모두 영구 중단으로 처리한다.
3. While 사용자가 Chrome에서 업무를 계속하면, 시스템은 Chrome 입력을 Aside 사용자 개입으로 해석하지 않는 계약을 보존해야 한다.
   - 검증 명령: `bash scripts/acceptance-hs-browser-policy.sh`
   - 기대값: 대상 앱·프로필·탭 귀속 문구와 Chrome 비간섭 문구가 둘 다 있어야 통과.
   - counter-AC: “별도 브라우저 사용”만 적고 Chrome 작업·입력 간섭 금지를 빠뜨린다.

### 정조준 시험 계획

RED 단계는 `scripts/acceptance-hs-browser-policy.sh`를 추가한 뒤 현재 SOT에서 실패해야 한다. GREEN 단계는 SOT, `contracts/humansearch/browser-policy.yaml`, CI/SOT 배선을 최소 수정해 같은 명령을 통과시킨다.

### 읽은 SOT와 비범위

- 읽은 SOT: `docs/sot/strict-workflow.md`, `docs/sot/coding-principles.md`, `docs/sot/principles.yaml`, `docs/sot/git-workflow.md`, `docs/sot/verification-commands.md`, `docs/sot/humansearch-browser-contract.md`, `docs/sot/humansearch-l0-surface-contract.md`.
- 비범위: 실제 Aside 조작, RPS 프로젝트 쓰기, LinkedIn 상세 저장, 잡코리아/사람인 라이브 검색, push, PR 생성, merge.

## 검증 장부

- Strict 원칙 직접 로드: `bash scripts/acceptance-principles-check.sh` → `VERDICT: PASS`, `CHECKED: 34`.
- RED: `bash scripts/acceptance-hs-browser-policy.sh` → `VERDICT: FAIL`, `CHECKED: 22`. 이유는 `contracts/humansearch/browser-policy.yaml` 부재, Aside 전용·Chrome 비간섭·채널별 프로필·입력 귀속·재개/STOP 문구 누락, 오래된 `자동 재개하지 않는다.` 문구다.
- GREEN:
  - `bash scripts/acceptance-hs-browser-policy.sh` → `VERDICT: PASS`, `CHECKED: 22`.
  - `bash scripts/verify/run-acceptance.sh scripts/acceptance-hs-browser-policy.sh` → `OK(run-acceptance)`, 판정 23건, `CHECKED 22`.
  - `bash scripts/acceptance-verify-ac-m.sh` → `CHECKED: 31`, mechanism registry 21개와 검사기 보고 21개 일치.
  - `bash verify.sh` → `PASS: no secret-pattern match in any tracked file, .env not tracked`.
  - `bash scripts/acceptance-principles-check.sh` → `VERDICT: PASS`, `CHECKED: 34`.
  - `bash scripts/acceptance-ci-step-integrity.sh` → `VERDICT: PASS`, `CHECKED: 24`.
  - `bash scripts/acceptance-semantic-mutations.sh` → `VERDICT: PASS`, `CHECKED: 16`.
  - `bash -n scripts/acceptance-hs-browser-policy.sh && git diff --check` → 종료값 0.
- 외부 결함주입 RED: `automation_app: Aside`를 주석으로 남기고 실제 값을 `Chrome`으로 바꾼 격리 사본이 기존 grep 검사에서 통과했다. 중복키, 불리언 문자열, 주석만 남긴 no-op 계약도 같은 계열 반례로 고정한다.
