# verification-trust-core 최소화 goal — 2026-09-18

## 결론

일반 개발은 독립 인간 검토가 없다는 이유만으로 멈추지 않는다. 자동 테스트, 새 맥락의 LLM 교차검토, 독립 인간 검토는 각각 실제 실행 결과를 기록하며 하나의 종합 PASS로 합치지 않는다.

이 변경은 제품·데이터·인증·DB 스키마를 바꾸지 않는 내부 검증 체계 축소다. 배송 상태는 `NOT_APPLICABLE`이고, commit·push·PR·GitHub 설정·배포는 범위 밖이다.

## 판단 근거

기존 미커밋 trust-core 작업은 로컬 검증이 모두 통과해도 protected PR, required reviewer, acceptance environment가 현재 후보를 검증하기 전에는 전체를 `NOT_RUN / CONTRACT_ONLY / BLOCKED`로 유지했다. 이는 1인 개발 + LLM 중심 환경에서 일반 개발 완료와 원격 거버넌스를 섞었다.

새 기준은 필수 자동 테스트 실패만 완료를 막고, 인간 검토는 데이터 삭제·인증/권한·대규모 DB 마이그레이션처럼 고위험 작업에서 goal이 명시한 경우에만 필수다.

## 범위와 기준

- candidate base: `origin/main`
- 포함: `f12ea335a0fd323bb3eec3ca0e300ae1ca9b0717`
- 제외: `605973f70483be22aeda5a03b62e311c50f7d736`, `fdb9a2027313a88818d739aaf07381dd77253755`
- 금지: `humansearch/src/humansearch/runner_boundary.py`, `scratchpad-sot-exception-status.md`, `wrtn-finance-data-search/**`, RPS 관련 파일
- Git/외부 금지: commit, push, branch/PR/review/merge, collaborator/repository/environment/deployment 변경

## 현재 상태와 근본 원인

확인한 호출 경로:

1. `.github/workflows/verify.yml`의 `environment: acceptance`가 일반 CI를 외부 승인에 결합했다.
2. `scripts/strict-current.sh`가 `scripts/verify/run-strict-current-evidence.rb`를 호출했다.
3. 생산자가 G/V1/V2/T 결과를 만든 뒤 `scripts/verify/check-strict-verdict-ledger.sh --current`를 호출했다.
4. current 모드는 역할이 모두 PASS여도 protected acceptance 경계 전에는 `NOT_RUN / CONTRACT_ONLY`를 반환했다.
5. `docs/sot/verification-commands.md`와 이 goal의 이전 판은 별도 reviewer 부재를 전체 `BLOCKED`로 설명했다.

근본 원인은 자동 테스트·LLM 검토·인간 검토를 분리하지 않고 원격 보호 경계를 일반 로컬 완료 조건으로 사용한 것이다.

## 유지 / 단순화 / 삭제

### 유지

- 기존 acceptance 실행과 실패 전파
- 실행하지 않은 검증을 `NOT_RUN`으로 기록하는 원칙
- 새 맥락 LLM 적대검토와 재현 가능한 finding만 수정하는 흐름
- 고위험 변경에서 별도 인간 검토를 필수로 지정할 수 있는 가능성

### 단순화

- `coding-principles.md`: 세 검증 채널을 분리하고 선택 인간 검토의 `NOT_RUN` 비차단을 명시
- `principles.yaml`: P3 기계 기대값을 같은 상태 계약으로 정렬
- `strict-workflow.md`: 기본 흐름을 구현 → 자동 테스트 → LLM 검토 → 수정 → 회귀 → 기록으로 정리
- 기존 `acceptance-principles-check.sh`와 mutation suite: 위 계약의 존재와 삭제 반례만 검사

### 삭제

- `docs/sot/acceptance-integrity-contract.json`
- `docs/sot/work-unit-policy.yaml`
- `scripts/strict-current.sh`
- `scripts/verify/check-acceptance-integrity.rb`
- `scripts/verify/run-strict-current-evidence.rb`
- `scripts/verify/test-strict-current-evidence.sh`
- 관련 fixture와 current ledger mode·CI/environment·registry·pre-push 배선
- collaborator, required reviewer, admin bypass, environment policy를 일반 개발의 선행조건으로 설명하던 문구

## 계약

입력:

- 자동 테스트 상태: `PASS | FAIL | NOT_RUN`
- LLM 교차검토 상태: `PASS | FAIL | NOT_RUN`
- 독립 인간 검토 상태: `PASS | FAIL | NOT_RUN`
- 위험 분류: 일반 또는 goal에 명시된 고위험

출력:

- 세 상태를 각각 그대로 보고한다.
- 일반 작업의 인간 검토 `NOT_RUN`은 자동 테스트나 LLM 상태를 바꾸지 않는다.
- 필수 자동 테스트 `FAIL` 또는 `NOT_RUN`은 완료 보고를 금지한다.
- 고위험 goal이 인간 검토를 필수로 지정한 경우에만 인간 검토 `NOT_RUN`이 완료를 막는다.

오류·경계:

- 실행하지 않은 검증은 PASS로 승격하지 않는다.
- LLM 검토를 인간 검토로 재표기하지 않는다.
- 외부 GitHub 설정 상태는 로컬 개발 판정에 합산하지 않는다.
- 이번 변경은 데이터·인증·권한·DB 마이그레이션을 수행하지 않는다.

## EARS 인수 기준과 counter-AC

1. **When** 검증 결과를 기록할 때, 시스템은 자동 테스트·LLM 교차검토·독립 인간 검토를 각각 `PASS / FAIL / NOT_RUN`으로 기록해야 한다.
   - 검증: 정본 첫 문장만 반전한 격리 사본이 원칙 검사 exit 1과 `VERDICT: FAIL`을 반환한다.
   - counter-AC: 세 채널 중 하나를 생략하거나 서로 다른 상태 어휘를 사용해도 통과한다.
2. **When** 검증 채널이 실행되지 않았거나 여러 채널의 결과가 다를 때, 시스템은 미실행을 PASS로 표시하거나 세 채널을 하나의 종합 PASS로 합치지 않아야 한다.
   - 검증: 정본 둘째 문장만 반전한 격리 사본이 원칙 검사 exit 1과 `VERDICT: FAIL`을 반환한다.
   - counter-AC: 정본 밖 주석·decoy에 원문을 남기면 훼손된 정본 절도 통과한다.
3. **When** 필수 자동 테스트가 `FAIL` 또는 `NOT_RUN`일 때, 시스템은 인간 또는 LLM 결과와 무관하게 완료로 보고하지 않아야 한다.
   - 검증: 정본 셋째 문장만 반전한 격리 사본이 원칙 검사 exit 1과 `VERDICT: FAIL`을 반환한다.
   - counter-AC: LLM PASS가 자동 테스트 FAIL을 덮거나 차단 문장만 삭제해도 통과한다.
4. **When** 일반 작업의 인간 검토가 실행되지 않았을 때, 시스템은 인간 검토를 `NOT_RUN`으로 남기되 그것만으로 차단하지 않아야 하며, **If** 데이터 삭제·인증/권한·대규모 DB 마이그레이션을 goal이 고위험으로 지정하면 독립 인간 검토를 필수 채널로 둘 수 있어야 한다.
   - 검증: 정본 넷째 문장만 반전한 격리 사본이 원칙 검사 exit 1과 `VERDICT: FAIL`을 반환한다.
   - counter-AC: 모든 작업에 인간 검토를 강제하거나 어떤 작업에도 강제할 수 없게 한다.
5. **When** acceptance 하위 명령이 exit 0을 반환해도 실제 `FAIL:` 또는 `VERDICT: FAIL|NOT_RUN`을 출력하거나 `VERDICT:`를 둘 이상 출력하면, 기존 runner는 이를 실패시켜야 한다.
   - 검증: 기존 semantic mutation suite의 부분 실패 probe와 정상 acceptance 양성 대조군.
   - counter-AC: 앞선 `PASS:` 한 줄이 후속 실패 판정을 가린다.

## Harness와 롤백

- RED: 네 invariant를 각각 하나씩 반전한 사본과 부분 실패 출력 probe가 모두 기존 검사에서 exit 0으로 통과함
- GREEN: 정본 절의 네 완전한 문장을 각각 한 조건으로 검사하고, 단독 mutation 네 건과 부분 실패 출력 probe가 모두 exit 1로 차단됨
- 회귀: principles, semantic mutation, AC-M, docs SOT, `verify.sh`, shell syntax, `git diff --check`
- 적대검토: 새 맥락 LLM이 범위·호출 경로·가짜 PASS·필수 자동 테스트·고위험 예외를 공격
- timeout: 저장소에는 CI job의 30분 상한과 개별 Python `subprocess` timeout만 있고 로컬 shell acceptance의 프로세스 그룹 정리 관례는 없다. 새 watchdog 계층 없이 TERM/INT 뒤 자식 정리를 보장할 수 없으므로 이번 핵심 변경에서는 runner timeout을 추가하지 않고 후속 위험으로 기록한다.
- 롤백: 변경 파일을 작업 시작 시 바이트로 되돌리고 삭제한 미추적 trust-core 파일을 복원한다. Git 기록과 외부 설정은 건드리지 않는다.
- 영향 반경: 검증 정본과 로컬/CI acceptance 배선만. 제품 코드·운영 데이터 영향 없음.
- 데이터 안전 AC: 금지 경로와 외부 시스템을 읽거나 쓰지 않는다.

## 검증 장부

| 시각(KST) | 명령 | 종료값 | 상태 | 해석 |
| --- | --- | ---: | --- | --- |
| 2026-09-17 20:28 | `bash scripts/acceptance-principles-check.sh` | 0 | PASS | 변경 전 원칙 장부·배선 35개가 통과했으나 새 세 상태 계약은 검사하지 않았음 |
| 2026-09-17 20:32 | `bash scripts/acceptance-principles-mutations.sh` | 미확정 | NOT_RUN | 새 RED 단언 두 건이 실패한 출력은 확인했지만 장시간 실행의 최종 종료값을 회수하지 못해 PASS/FAIL로 승격하지 않음 |
| 2026-09-17 20:35 | `bash scripts/acceptance-principles-check.sh` | 0 | PASS | 세 상태 분리·일반 인간 검토 비차단·고위험 예외 계약 포함, 34개 검사 |
| 2026-09-17 20:36 | `bash scripts/acceptance-principles-mutations.sh` | 0 | PASS | 비차단 계약 삭제 반례가 exit 1로 잡혔고 당시 전체 43개 검사 통과 |
| 2026-09-17 20:37 | `bash scripts/acceptance-semantic-mutations.sh` | 0 | PASS | 29개 acceptance의 5종 무력화와 Invoice 반례, 전체 16개 검사 통과 |
| 2026-09-17 20:37 | `bash scripts/acceptance-verify-ac-m.sh` | 0 | PASS | 명부·CI 배선·0건·오형식 반례 31개 통과 |
| 2026-09-17 20:37 | `bash scripts/verify/check-mechanism-registry.sh` | 0 | PASS | 기존 메커니즘 20개와 원칙 검사 원명령 통과 |
| 2026-09-17 20:37 | `bash scripts/acceptance-ci-step-integrity.sh` | 0 | PASS | 실제 workflow와 비활성화·오류무시 반례 24개 통과 |
| 2026-09-17 20:37 | `bash scripts/check-docs-sot.sh` | 1 | FAIL | `coding-principles.md` 21,292바이트로 20,000바이트 상한 초과 |
| 2026-09-17 20:38 | `bash scripts/check-docs-sot.sh` | 0 | PASS | 관련 P3/P13 중복 서술을 축약해 19,868바이트, 같은 원명령 재실행 통과 |
| 2026-09-17 20:37 | `bash verify.sh` | 0 | PASS | 추적 파일 비밀 패턴 없음 |
| 2026-09-17 20:38 | `bash scripts/verify/check-pre-push-runtime.sh hooks/pre-push` | 0 | PASS | 격리 probe 발견·실행·실패 전파 확인 |
| 2026-09-17 20:38 | `bash scripts/verify/check-strict-verdict-ledger.sh` | 0 | PASS | 기존 G/V1/V2/T 역사 장부 4역할 검증 통과; 이번 세 상태의 종합 판정으로 사용하지 않음 |
| 2026-09-17 20:38 | `bash -n ... && git diff --check` | 0 | PASS | 변경한 셸 2개 문법과 diff 공백 검사 통과 |
| 2026-09-17 20:38 | `bash hooks/pre-push` | 1 | FAIL | commit 금지 범위의 미커밋 작업트리를 P15가 의도대로 차단; 우회하거나 PASS로 재표기하지 않음 |
| 2026-09-17 20:46 | 임시 복제본에서 P3 `mechanism_expected` 계약 삭제 후 원칙 검사 | 0 | FAIL | V1 HIGH finding 재현: 원장 상태 계약 삭제를 기존 검사기가 놓침 |
| 2026-09-17 20:47 | `bash scripts/acceptance-principles-check.sh` | 0 | PASS | P3 원장에도 세 채널·상태·비차단·고위험 예외가 있는지 검사, 34개 원칙 배선 통과 |
| 2026-09-17 20:47 | `bash scripts/acceptance-principles-mutations.sh` | 0 | PASS | P3 원장 계약 삭제 반례가 exit 1로 잡혔고 전체 44개 검사 통과 |
| 2026-09-17 20:47 | `bash scripts/check-docs-sot.sh` | 0 | PASS | SOT 존재·크기·훅 계약 참조 통과 |
| 2026-09-17 20:47 | `bash verify.sh` | 0 | PASS | 추적 파일 비밀 패턴 없음 |
| 2026-09-17 20:47 | `bash -n ... && git diff --check` | 0 | PASS | 수정 후 셸 문법과 diff 공백 검사 통과 |
| 2026-09-17 20:50 | V2 임시 변조 재현·원명령 재실행 | 0 | PASS | P3 계약 삭제는 exit 1, principles 34개와 mutation 44개 및 wrapper·docs·pre-push runtime 검증 통과 |
| 2026-09-17 20:52 | 최종 principles·mutation·semantic·AC-M·registry·CI integrity·docs·secret·pre-push runtime·ledger·syntax/diff 묶음 | 0 | PASS | 11개 원명령 모두 종료값 0; semantic 장시간 세션도 최종 `CHECKED: 16`, `VERDICT: PASS` 회수 |

현재 채널 상태:

- 자동 테스트: `PASS` — 범위 내 필수 대상·회귀·문서·셸 검사가 모두 PASS다. 원본 pre-push의 dirty 차단은 push 적격성 검사이며, commit 금지로 발생한 기대된 음성 결과를 자동 테스트 FAIL로 합산하지 않는다.
- LLM 교차검토: `PASS` — V1 finding 두 건을 재현·수정했고, 새 맥락 V2가 수정과 활성 호출 경로를 독립 재검증해 PASS 판정했다.
- 독립 인간 검토: `NOT_RUN` — 일반 개발 비차단이며 이번 변경은 고위험 분류가 아니다.

## 적대 검증 로그

### V1 — `/root/v1_trust_review`

- 판정: `FAIL`
- HIGH: `principles.yaml`의 P3 상태 계약을 제거해도 기존 `acceptance-principles-check.sh`가 exit 0을 반환했다.
- LOW: `verification-commands.md`가 mutation 반례 수를 41로 고정해 실제 43과 어긋났다.
- 재현: 임시 저장소에서 P3 `mechanism_expected`를 이전 문구로 바꾼 뒤 원칙 검사 exit 0을 확인했다. 문서 28행의 41과 실제 suite 출력 43도 대조했다.
- 수정: 기존 검사기에 P3 원장 fragment 검증과 삭제 mutation을 추가하고, 문서에서는 변동 가능한 고정 개수를 삭제했다.

### V2 — `/root/v2_trust_verification`

- 판정: `PASS`
- V1 HIGH 재검증: 같은 P3 변조가 exit 1과 `P3_VERIFICATION_STATUS_CONTRACT_MISSING` 5건을 반환했다.
- V1 LOW 재검증: 활성 SOT·스크립트에서 41/43 고정 수치가 사라졌다.
- 독립 실행: principles 검사 34개, mutation 44개, acceptance wrapper 2개, docs SOT, pre-push runtime, 셸 문법, diff 공백 검사가 모두 exit 0이었다.
- 범위 확인: 활성 CI/pre-push 호출 경로에 reviewer/environment 부재를 일반 작업의 실패로 승격하는 배선이 없고, 금지 경로와 RPS는 검토하지 않았다.

## 2026-09-18 최소화·부분 실패 전파 재검증

### 검증 장부 추가

| 시각(KST) | 명령 | 종료값 | 상태 | 해석 |
| --- | --- | ---: | --- | --- |
| 10:31 | `bash scripts/acceptance-principles-check.sh` | 0 | PASS | 변경 전 작업트리의 6개 source fragment + 5개 P3 fragment 검사 기준선 |
| 10:33 | 네 invariant 단독 반전 격리 probe | 각 0 | FAIL | 네 반전 모두 기존 검사에서 `VERDICT: PASS`로 살아남아 RED 확보 |
| 10:34 | 부분 실패 출력 격리 probe 4종 | 각 0 | FAIL | 실제 `FAIL:`, `VERDICT: FAIL`, `VERDICT: NOT_RUN`, 중복 PASS verdict가 기존 runner를 통과해 RED 확보 |
| 10:36 | `bash scripts/acceptance-principles-check.sh` 첫 GREEN | 1 | FAIL | 새 절 파서의 `#` 정규식 문법 오류 재현; 리터럴로 수정 |
| 10:36 | 같은 원칙 검사 + `bash scripts/acceptance-principles-mutations.sh` | 0 / 0 | PASS | 정상 34개와 mutation 45건; 네 단독 반례가 각각 오류 1건·exit 1·`VERDICT: FAIL` |
| 10:38 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-semantic-mutations.sh` | 0 | PASS | 정상 acceptance 양성 대조군 유지, 부분 실패 probe 4/4 차단, 전체 17건 |
| 10:39 | AC-M·registry·CI integrity·pre-push runtime·docs SOT·secret·shell·diff | 모두 0 | PASS | 기존 CI/pre-push 배선과 검증 명령 회귀 통과 |
| 10:45 | native 새 맥락 LLM 공격 검토 | 0 | PASS | invariant·runner·과잉 차단·배선·timeout 잔여 위험을 읽기 전용 재현, 작업트리 before/after 동일 |
| 10:47 | V2 같은 절 내부 5번째 decoy bullet 공격 | 0 | FAIL | V1 누락 재현: 반전 bullet과 원문 decoy bullet이 함께 있으면 검사 통과 |
| 10:48 | 절 bullet 수 4개 구조 조건 추가 후 같은 공격 | 1 | PASS | `VERIFICATION_CONTRACT_LINE_COUNT: expected=4 actual=5`, `VERDICT: FAIL`로 차단 |
| 10:48 | 수정 후 원칙 검사 + mutation suite | 0 / 0 | PASS | 네 독립 반례와 정상 대조군 재통과, source-tree before/after 동일 |
| 10:49 | `omx ask claude ...` | 130 | NOT_RUN | 7분 이상 모델 출력이 없어 SIGINT; 최소 진단도 `No messages returned`라 외부 Claude 판정을 PASS로 승격하지 않음 |
| 10:51 | 최종 wrapper 원칙·mutation + shell syntax + `git diff --check` | 모두 0 | PASS | 최종 관련 회귀와 정적 검사 통과, HEAD 불변 |
| 11:00 | 최종 native 새 맥락 LLM 재검토 + timeout 변경 provenance 대조 | 0 | PASS | 네 invariant·부분 실패·legacy 양성·decoy를 재확인했고, CI timeout은 현재 diff가 아님을 확인해 최초 지적을 철회 |

### 적대 검증 결과

- 새 맥락 LLM 검토: `PASS`. native 독립 검토가 요구 공격을 실행했고 재현 가능한 결함 0건으로 보고했다.
- V2 재공격: `PASS`. V1이 놓친 같은 절 내부 decoy를 재현해 구조 조건을 추가했고 동일 공격과 관련 회귀를 다시 통과시켰다.
- 외부 Claude 추가 검토: `NOT_RUN`. 실행 예정이나 프로세스 시작을 PASS로 세지 않았고 원문은 `.omx/artifacts/claude-strict-adversarial-review-20260918-104939.md`에 보존했다.
- 최종 native LLM 재검토: `PASS`. timeout 지적은 `.github/workflows/verify.yml`의 현재 diff가 비어 있어 이번 변경의 결함이 아닌 것으로 재검증했고, 로컬 runner hang은 미해결 잔여 위험으로 유지했다.
- 독립 인간 검토: `NOT_RUN`. 이번 변경은 데이터 삭제·인증/권한·대규모 DB 마이그레이션을 수행하지 않아 goal에서 필수 채널로 지정하지 않았다.
