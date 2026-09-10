# Work Unit TDD·맥락 계약 실행 증거 — 2026-09-10

## 결론

WU-1~WU-5는 각각 스키마, RED/GREEN 이력, 현재 Git 맥락, NOT_APPLICABLE, 검사기·CI mutation을 실제 입력으로 검증합니다. 완료된 각 WU는 같은 시험의 GREEN과 작은 반례를 통과했습니다.

## WU-1 RED 원문

시각 `2026-09-10T16:04:12+09:00`, 선행 계약 `e80d1809da31b0c0c649d302dfc7c7633f53f26e`, RED 커밋 `14604d568301492f3c73e5cceac8c2b49768e714`.

```text
FAIL: normal manifest — expected exit=0 diagnostic=^VERDICT: PASS$ actual=2
VERDICT: NOT_RUN
REASON: work unit manifest validation not implemented
CHECKED: 0
FAIL: missing AC — expected exit=1 diagnostic=AC_REQUIRED: actual=2
VERDICT: NOT_RUN
REASON: work unit manifest validation not implemented
CHECKED: 0
FAIL: missing counter-AC — expected exit=1 diagnostic=COUNTER_AC_REQUIRED: actual=2
VERDICT: NOT_RUN
REASON: work unit manifest validation not implemented
CHECKED: 0
FAIL: duplicate ID — expected exit=1 diagnostic=ID_DUPLICATE: actual=2
VERDICT: NOT_RUN
REASON: work unit manifest validation not implemented
CHECKED: 0
WU_TESTS: 4
CHECKED: 4
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
EXIT=1
```

→ 정상 입력을 판정하는 동작이 아직 없어서 시험 4건이 실패했습니다. 문법·불러오기 오류나 시험 0건이 아니므로 유효한 RED입니다.

## WU-1 GREEN·회귀·작은 공격 원문

시각 `2026-09-10T16:07:38+09:00`, GREEN 커밋 `18e7535e7e9799d03a14c6b31582e857ae94ddf9`.

```text
PASS: normal manifest — exit=0
PASS: missing AC — exit=1
PASS: missing counter-AC — exit=1
PASS: duplicate ID — exit=1
WU_TESTS: 4
CHECKED: 4
VERDICT: PASS
SCHEMA_EXIT=0
TEST_LOCK_EXIT=0
VERDICT: FAIL
WORK_UNITS_REQUIRED: at least one
CHECKED: 2
ZERO_UNITS_ATTACK_EXIT=1
```

→ 같은 시험 4건이 모두 통과했고 RED 뒤 시험 파일 diff는 0건이었습니다. 추가로 WU 0건 입력을 넣자 종료값 1로 거부했으므로, 파일만 존재하는 가짜 합격도 막았습니다.

## WU-2 RED 원문

시각 `2026-09-10T16:11:16+09:00`, RED 커밋 `f72c029b96d9ef4a59b63fafe5c9913ae3f867ee`.

```text
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
FAIL: syntax-only RED rejected
VERDICT: PASS
CHECKED: 11
FAIL: test expectation drift rejected
VERDICT: PASS
CHECKED: 11
WU_TESTS: 4
CHECKED: 4
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
EXIT=1
```

→ 시험 4건은 실행됐고, 문법 오류만 난 RED와 시험 기대값을 바꾼 가짜 GREEN을 기존 구조 검사기가 통과시켜 유효한 RED가 됐습니다.

### 첫 GREEN 실패와 승인된 시험 입력 보정

첫 구현 실행은 fixture가 만든 `feature_test.rb` 대신 존재하지 않는 `example_test.rb`를 호출해 정상 이력도 실패했습니다. 기대 판정은 유지하고 시험 입력 경로만 고친 별도 커밋 `95110bd48da5794ffb9160a8e961d28762c692ab`에 `Test-Expectation-Approval: WU-2 fixture path repair only`를 기록했습니다.

```text
FAIL: authentic RED then GREEN
VERDICT: FAIL
RED_FAILURE_INVALID: exit=1 command=ruby test/example_test.rb
FIRST_GREEN_INVALID: exit=1 command=ruby test/example_test.rb
RED_TEST_COUNT_MISMATCH: expected=1 actual=0
TEST_FILE_MISSING: test/example_test.rb
CHECKED: 20
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
FAIL: test expectation drift rejected
VERDICT: FAIL
RED_FAILURE_INVALID: exit=1 command=ruby test/example_test.rb
FIRST_GREEN_INVALID: exit=1 command=ruby test/example_test.rb
RED_TEST_COUNT_MISMATCH: expected=1 actual=0
TEST_FILE_MISSING: test/example_test.rb
CHECKED: 20
WU_TESTS: 4
CHECKED: 4
VERDICT: FAIL
SCHEMA_EXIT=0
TDD_EXIT=1
```

→ 구현의 결함이 아니라 시험 fixture 경로 결함이었습니다. 이를 숨기지 않고 test-only 커밋으로 분리한 뒤, 구현이 없는 그 커밋에서 RED 종료값 1을 다시 확인했습니다.

## WU-2 GREEN·회귀·작은 공격 원문

시각 `2026-09-10T16:18:18+09:00`, GREEN 커밋 `f2c609942ebf90040cae91ae10ccafe6eb286bec`.

```text
PASS: normal manifest — exit=0
PASS: missing AC — exit=1
PASS: missing counter-AC — exit=1
PASS: duplicate ID — exit=1
WU_TESTS: 4
CHECKED: 4
VERDICT: PASS
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
WU_TESTS: 4
CHECKED: 4
VERDICT: PASS
SCHEMA_EXIT=0
TDD_EXIT=0
TEST_LOCK_EXIT=0
```

→ 정상 이력은 RED와 GREEN을 실제 커밋에서 다시 실행해 통과했고, 0건·문법 오류·시험 변경은 모두 거부했습니다. 승인 보정 뒤 시험 파일은 GREEN까지 바이트 변경 0건입니다.

```text
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
FAIL: syntax-only RED rejected
VERDICT: FAIL
RED_TEST_COUNT_MISMATCH: expected=1 actual=0
TEST_FILE_CHANGED_AFTER_RED: test/feature_test.rb
CHECKED: 21
PASS: test expectation drift rejected
WU_TESTS: 4
CHECKED: 4
VERDICT: FAIL
BROKEN_RED_GUARD_EXIT=1
```

→ 임시 작업공간에서 RED 원인 거부 줄을 항상 거짓으로 바꾸자 상위 시험이 종료값 1을 냈습니다. 검사 한 줄 고장을 실제로 감지한 좋은 증거입니다.

## WU-3 RED 원문

시각 `2026-09-10T16:26:21+09:00`, 선행 Type 계약 `c28b3a29d4be3509d1d097ec99ce70d9eab676b8`, RED 커밋 `bc5c4d0`.

```text
FAIL: current exact context
VERDICT: FAIL
CONTEXT_SCHEMA_INVALID: work_units[0]
CHECKED: 11
FAIL: filename-only declaration rejected
FAIL: context hash mismatch rejected
FAIL: stale HEAD rejected
FAIL: other worktree rejected
FAIL: whole repository scope rejected
FAIL: undeclared observed read rejected
WU_TESTS: 7
CHECKED: 7
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
CONTEXT_EXIT=1
SCHEMA_EXIT=1
```

→ 관측 읽기 목록이라는 새 Type 필드와 의미 검증이 아직 없어 정상 사례를 포함한 7건이 모두 실패했습니다. Ruby 문법 검사는 통과했고 시험 7건이 실행됐으므로 문법 오류나 0건 RED가 아닙니다.

## WU-3 GREEN·회귀·작은 공격 원문

시각 `2026-09-10T16:28:46+09:00`, GREEN 커밋 `2c25879`.

```text
PASS: current exact context
PASS: filename-only declaration rejected
PASS: context hash mismatch rejected
PASS: stale HEAD rejected
PASS: other worktree rejected
PASS: whole repository scope rejected
PASS: undeclared observed read rejected
WU_TESTS: 7
CHECKED: 7
VERDICT: PASS
PASS: normal manifest — exit=0
PASS: missing AC — exit=1
PASS: missing counter-AC — exit=1
PASS: duplicate ID — exit=1
WU_TESTS: 4
CHECKED: 4
VERDICT: PASS
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
WU_TESTS: 4
CHECKED: 4
VERDICT: PASS
CONTEXT_EXIT=0
SCHEMA_EXIT=0
TDD_EXIT=0
```

→ 정상 맥락 한 건은 통과하고 filename-only, hash 불일치, 오래된 HEAD, 다른 worktree, 전체 저장소 범위, 미선언 읽기는 모두 종료값 1로 거부됐습니다. WU-3 RED 뒤 context 시험 파일 diff도 0건입니다.

## WU-4 RED 원문

시각 `2026-09-10T16:32:16+09:00`, RED 커밋 `3c418f5`.

```text
FAIL: documented alternative validation
VERDICT: FAIL
COMMIT_INVALID: work_units[0].red_commit
COMMIT_INVALID: work_units[0].green_commit
RED_COMMAND_REQUIRED: work_units[0]
RED_FAILURE_KIND_REQUIRED: work_units[0]
TEST_FILES_REQUIRED: work_units[0]
CHECKED: 11
FAIL: missing reason rejected
FAIL: zero alternative commands rejected
FAIL: unsupported change kind rejected
FAIL: RED_GREEN with waiver rejected
WU_TESTS: 5
CHECKED: 5
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
NOT_APPLICABLE_EXIT=1
```

→ 기존 형식은 RED/GREEN 값만 허용해 올바른 문서 변경도 표현할 수 없었고, 사유·대체 명령·허용 종류를 판정하는 동작도 없었습니다. 시험 5건과 `missing_behavior`가 출력된 유효한 RED입니다.

## WU-4 GREEN·회귀·작은 공격 원문

시각 `2026-09-10T16:34:07+09:00`, GREEN 커밋 `597e5a1`.

```text
PASS: documented alternative validation
PASS: missing reason rejected
PASS: zero alternative commands rejected
PASS: unsupported change kind rejected
PASS: RED_GREEN with waiver rejected
WU_TESTS: 5
CHECKED: 5
VERDICT: PASS
PASS: current exact context
PASS: filename-only declaration rejected
PASS: context hash mismatch rejected
PASS: stale HEAD rejected
PASS: other worktree rejected
PASS: whole repository scope rejected
PASS: undeclared observed read rejected
WU_TESTS: 7
CHECKED: 7
VERDICT: PASS
PASS: normal manifest — exit=0
PASS: missing AC — exit=1
PASS: missing counter-AC — exit=1
PASS: duplicate ID — exit=1
WU_TESTS: 4
CHECKED: 4
VERDICT: PASS
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
WU_TESTS: 4
CHECKED: 4
VERDICT: PASS
NOT_APPLICABLE_EXIT=0
CONTEXT_EXIT=0
SCHEMA_EXIT=0
TDD_EXIT=0
```

→ 문서 변경은 실제 `test -s README.md` 대체 명령을 실행해 통과했습니다. 빈 사유, 명령 0개, 허용 밖 변경 종류, RED_GREEN과 면제 혼합은 닫힌 실패이며 WU-4 RED 뒤 시험 파일 diff는 0건입니다.

## WU-5 RED 원문

시각 `2026-09-10T16:39:03+09:00`, RED 커밋 `672283c`.

```text
PASS: 정상 WU gate — all modes exit=0
PASS: 검사기 무력화 차단: exit-zero — exit=1
PASS: 검사기 무력화 차단: noop — exit=1
PASS: 검사기 무력화 차단: echo-only — exit=1
PASS: 검사기 무력화 차단: always-false — exit=1
FAIL: WU CI 배선 — one or more executable commands missing
FAIL: WU CI 항상-거짓 조건 차단 — target step missing
PASS: 원본 worktree 상태 불변 — before/after identical
WU_TESTS: 8
CHECKED: 8
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
MUTATION_EXIT=1
```

→ 검사기 네 변이는 이미 상위 schema gate가 잡았지만, 서버가 WU gate를 호출하지 않아 두 배선 사례가 실패했습니다. 따라서 구현 누락은 CI 연결이며 시험 8건이 실행된 유효한 RED입니다.

### WU-5 시험 런타임 보정과 RED 재현

저장소 Ruby가 `filter_map`을 제공한다고 가정한 시험 결함을 별도 test-only 승인 커밋 `c78f930`에서 `map + compact`로 고쳤습니다. 그 커밋만 분리 체크아웃해 GREEN 파일 없이 다시 실행한 결과입니다.

```text
PASS: 정상 WU gate — all modes exit=0
PASS: 검사기 무력화 차단: exit-zero — exit=1
PASS: 검사기 무력화 차단: noop — exit=1
PASS: 검사기 무력화 차단: echo-only — exit=1
PASS: 검사기 무력화 차단: always-false — exit=1
FAIL: WU CI 배선 — one or more executable commands missing
FAIL: WU CI 항상-거짓 조건 차단 — target step missing
PASS: 원본 worktree 상태 불변 — before/after identical
WU_TESTS: 8
CHECKED: 8
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
CORRECTED_RED_EXIT=1
```

## WU-5 GREEN·회귀·mutation 원문

시각 `2026-09-10T16:45:21+09:00`, GREEN 커밋 `faa8b6f`, 누락 manifest 회귀 확장 `2b64699`.

```text
PASS: 정상 WU gate — all modes exit=0
PASS: 검사기 무력화 차단: exit-zero — exit=1
PASS: 검사기 무력화 차단: noop — exit=1
PASS: 검사기 무력화 차단: echo-only — exit=1
PASS: 검사기 무력화 차단: always-false — exit=1
PASS: WU CI 배선 — contract and mutation commands present
PASS: WU CI 항상-거짓 조건 차단 — exit=1
PASS: 원본 worktree 상태 불변 — before/after identical
WU_TESTS: 8
CHECKED: 8
VERDICT: PASS
MUTATION_EXIT=0
CI_TOTAL=30 CI_NAMED=29
DOC_STEP_ROWS=29
CI_INTEGRITY: PASS 24/24
AC_M: PASS 31/31
PRINCIPLES: PASS 34/34
```

→ CI는 WU 계약과 mutation 스크립트를 각각 무조건 실행하고, mechanism 명부와 명령 정본도 같은 실행 줄을 가리킵니다. 별도 회귀에서 manifest 파일 자체가 없으면 `MANIFEST_MISSING`, 종료값 1이었고 전체 네 모드는 21/21 PASS였습니다.

## WU-2R 감사 보정: DB/API/Type 선행 근거

완료 뒤 자체 감사에서 `contract_commit < RED` 순서만 확인하고 authority 근거 파일이 그 contract commit에 존재하는지는 보지 않는 구멍을 찾았습니다. 계약 커밋 `3c1ad8c` 뒤 RED `aa87570`에서 `late-contract.txt`를 RED commit에 처음 추가한 다음 DB/API/Type 근거로 선언했습니다.

```text
2026-09-10T16:56:45+09:00
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
FAIL: contract declared only after boundary rejected
VERDICT: PASS
CHECKED: 20
WU_TESTS: 5
CHECKED: 5
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
TDD_REMEDIATION_RED_EXIT=1
```

→ 기존 checker는 RED 뒤 생긴 계약 파일을 통과시켜 반례가 정확히 재현됐습니다. GREEN `1bdb504`는 DB/API/Type 경로를 1개 이상 요구하고 contract commit의 Git blob을 직접 확인합니다.

```text
2026-09-10T16:57:55+09:00
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
PASS: contract declared only after boundary rejected
WU_TESTS: 5
CHECKED: 5
VERDICT: PASS
TDD_REMEDIATION_GREEN_EXIT=0
SCHEMA_EXIT=0
CONTEXT_EXIT=0
NOT_APPLICABLE_EXIT=0
```

→ 늦게 만든 계약 파일은 `AUTHORITY_PATH_NOT_AT_CONTRACT`로 거부됐고, 기존 schema·context·NOT_APPLICABLE 회귀도 모두 종료값 0입니다. RED 뒤 시험 diff는 0건입니다.

## WU-2R2 감사 보정: 첫 GREEN 뒤 시험 불변

독립 감사에서 RED와 첫 GREEN 사이만 비교하므로 그 뒤의 무승인 기대값 변경을 놓치는 구멍을 찾았습니다. RED `14dad68`은 GREEN 뒤 시험 파일을 바꾼 합성 이력을 만들어 기존 checker가 통과하는지 공격했습니다.

```text
2026-09-10T17:09:25+09:00
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
PASS: contract declared only after boundary rejected
FAIL: post-GREEN test expectation drift rejected — checker unexpectedly passed
WU_TESTS: 6
CHECKED: 6
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
TDD_POST_GREEN_RED_EXIT=1
```

GREEN `0cd7731`은 RED 시점 blob을 첫 GREEN이 아닌 현재 저장소 HEAD blob과 비교합니다.

```text
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
PASS: contract declared only after boundary rejected
PASS: post-GREEN test expectation drift rejected
WU_TESTS: 6
CHECKED: 6
VERDICT: PASS
TDD_POST_GREEN_GREEN_EXIT=0
ALL_MODES_EXIT=0
WU_TESTS: 23
CHECKED: 23
VERDICT: PASS
```

→ 첫 GREEN 뒤에 시험을 바꾸어도 별도 승인 커밋이 없으면 `TEST_FILE_CHANGED_AFTER_RED`로 거부됩니다.

## WU-5R 감사 보정: 실제 저장소 WU manifest

독립 감사에서 fixture만 검사하고 이 저장소의 실제 WU manifest가 0개여도 CI가 통과하는 구멍을 찾았습니다. 계약 `9a79acb` 뒤 RED `b4a542b`에서 저장소 manifest·CI 실행 누락을 직접 조사했습니다.

```text
2026-09-10T17:18:47+0900
FAIL: repository WU manifest 0 — docs/engineering/work-units/*.yaml
FAIL: repository WU acceptance is not wired in CI
WU_TESTS: 2
CHECKED: 2
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
REPOSITORY_WU_RED_EXIT=1
RED_FAILURE_KIND_CHECK_EXIT=0
```

GREEN `90df3a0`은 `docs/engineering/work-units/work-unit-tdd-context.yaml`에 WU-1~WU-5의 실제 계약·RED·GREEN·맥락 증거를 보존하고 CI가 이를 재실행합니다. 완료 후 HEAD에서 다시 실행한 원문입니다.

```text
PASS: repository WU manifests discovered — 1
PASS: repository WU acceptance is wired in CI
PASS: repository WU manifest — docs/engineering/work-units/work-unit-tdd-context.yaml
WU_TESTS: 3
CHECKED: 3
VERDICT: PASS
REPOSITORY_WU_FINAL_EXIT=0
```

적대 회귀 `229bc59`는 manifest 삭제, 미추적 manifest 대체, CI 실행 줄 무력화를 분리 worktree에서 공격합니다.

```text
PASS: normal repository WU gate — exit=0
PASS: missing repository manifests rejected — exit=1
PASS: untracked manifest substitute rejected — exit=1
PASS: disabled repository CI wiring rejected — exit=1
PASS: original worktree state unchanged
WU_TESTS: 5
CHECKED: 5
VERDICT: PASS
```

→ fixture 정상 통과만으로는 완료할 수 없으며, Git에 추적된 실제 manifest와 무조건 CI 호출이 둘 다 필요합니다.

## WU-2R3 감사 보정: 최종 blob 원복으로 숨긴 가짜 GREEN

계약 `4949acb` 뒤 RED `3c7017c`은 GREEN 커밋에서 기대값을 바꿔 구현 없이 통과시킨 뒤, 나중 HEAD에서 시험을 원복하고 구현을 넣는 이력을 만들었습니다.

```text
2026-09-10T17:47:50+0900
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
PASS: contract declared only after boundary rejected
PASS: test drift after first GREEN rejected
FAIL: fake GREEN followed by restored expectation rejected
WU_TESTS: 7
CHECKED: 7
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
RESTORED_DRIFT_RED_EXIT=1
```

GREEN `77ee839`은 최종 blob만 비교하지 않고 `red_commit..HEAD`에서 선언한 시험 파일을 건드린 모든 커밋을 조사합니다. manifest에 승인 SHA가 없거나 해당 커밋에 `Test-Expectation-Approval: <WU-ID>` trailer가 없으면 실패합니다.

```text
2026-09-10T17:49:39+0900
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
PASS: contract declared only after boundary rejected
PASS: test drift after first GREEN rejected
PASS: fake GREEN followed by restored expectation rejected
WU_TESTS: 7
CHECKED: 7
VERDICT: PASS
RESTORED_DRIFT_GREEN_EXIT=0
```

## WU-5R2 감사 보정: 완료 명령 실제 실행

계약 `1757cc6` 뒤 RED `a9fd860`은 정상 명령과 함께 `false`, `true`, 0건 PASS 출력을 manifest에 넣었습니다. 기존 checker는 문자열 형태만 보고 네 가지 부적합 명령을 모두 통과시켰습니다.

```text
2026-09-10T17:54:58+0900
PASS: executed completion commands
FAIL: failing regression command rejected
FAIL: failing adversarial command rejected
FAIL: no-op completion command rejected
FAIL: zero-check completion output rejected
WU_TESTS: 5
CHECKED: 5
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
COMPLETION_COMMAND_RED_EXIT=1
```

GREEN `fd6e6e0`은 현재 저장소 HEAD에서 regression·adversarial 명령을 실행하고, 종료값 0·`VERDICT: PASS`·양수 `WU_TESTS` 또는 `CHECKED`를 모두 요구합니다. checker의 제어 환경변수는 자식 명령에 전파하지 않습니다.

```text
2026-09-10T17:56:15+0900
PASS: executed completion commands
PASS: failing regression command rejected
PASS: failing adversarial command rejected
PASS: no-op completion command rejected
PASS: zero-check completion output rejected
WU_TESTS: 5
CHECKED: 5
VERDICT: PASS
COMPLETION_COMMAND_GREEN_EXIT=0

WU_TESTS: 29
CHECKED: 29
VERDICT: PASS
ALL_AFTER_COMPLETION_EXIT=0

PASS: repository WU manifests discovered — 1
PASS: repository WU acceptance is wired in CI
PASS: repository WU manifest — docs/engineering/work-units/work-unit-tdd-context.yaml
WU_TESTS: 3
CHECKED: 3
VERDICT: PASS
REPOSITORY_WITH_COMPLETION_EXIT=0
```

후속 적대 회귀 `fb1a7ac`은 `bash -c` 안에서 양수 카운트와 PASS 문구만 echo하는 위조를 추가로 차단했습니다.

```text
PASS: executed completion commands
PASS: failing regression command rejected
PASS: failing adversarial command rejected
PASS: no-op completion command rejected
PASS: zero-check completion output rejected
PASS: echo-only positive-count forgery rejected
WU_TESTS: 6
CHECKED: 6
VERDICT: PASS
COMPLETION_ANTI_FORGE_EXIT=0
```

## WU-5R3 감사 보정: 승인되지 않은 위조 검사기 차단

독립 공격 리뷰는 `bash -c`만 막아도 저장소 안의 임의 스크립트가 `VERDICT: PASS`와 양수 `CHECKED`를 출력해 완료 증거를 위조할 수 있음을 확인했습니다. SOT 계약 `b42126c` 뒤 RED `b7ffb7f`은 기존 6개 사례를 보존한 채 승인되지 않은 위조 스크립트 한 건만 실패시켰습니다.

```text
PASS: executed completion commands
PASS: failing regression command rejected
PASS: failing adversarial command rejected
PASS: no-op completion command rejected
PASS: zero-check completion output rejected
PASS: echo-only positive-count forgery rejected
FAIL: unapproved forged-count script rejected
VERDICT: PASS
CHECKED: 13
WU_TESTS: 7
CHECKED: 7
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
RED_EXIT:1
```

GREEN `0c7376b`은 `docs/sot/work-unit-policy.yaml`의 `completion.approved_commands`와 정확히 일치하는 명령만 실행합니다. 임의 명령은 출력이나 종료값을 보기 전에 `*_COMMAND_NOT_APPROVED`로 거부합니다.

```text
PASS: executed completion commands
PASS: failing regression command rejected
PASS: failing adversarial command rejected
PASS: no-op completion command rejected
PASS: zero-check completion output rejected
PASS: echo-only positive-count forgery rejected
PASS: unapproved forged-count script rejected
WU_TESTS: 7
CHECKED: 7
VERDICT: PASS
GREEN_EXIT:0

WU_TESTS: 31
CHECKED: 31
VERDICT: PASS
ALL_CONTRACT_EXIT=0

PASS: repository WU manifests discovered — 1
PASS: required repository WU ID set matches manifests
PASS: repository WU acceptance is wired in CI
PASS: repository WU manifest — docs/engineering/work-units/work-unit-tdd-context.yaml
WU_TESTS: 4
CHECKED: 4
VERDICT: PASS
REPOSITORY_WU_EXIT=0

WU_TESTS: 8
CHECKED: 8
VERDICT: PASS
CONTRACT_MUTATIONS_EXIT=0

WU_TESTS: 6
CHECKED: 6
VERDICT: PASS
REPOSITORY_MUTATIONS_EXIT=0

PASS: 무력화 차단: exit-zero — 33/33 전부 불합격 처리
PASS: 무력화 차단: true-only — 33/33 전부 불합격 처리
PASS: 무력화 차단: noop — 33/33 전부 불합격 처리
PASS: 무력화 차단: empty — 33/33 전부 불합격 처리
PASS: 무력화 차단: echo-only — 33/33 전부 불합격 처리
CHECKED: 16
VERDICT: PASS
SEMANTIC_MUTATIONS_EXIT=0
```

CI integrity 24/24, mechanism registry 25개, AC-M 31건, 원칙 34/34, `verify.sh`, `git diff --check`도 종료값 0입니다. 검증 중 셸 스크립트를 `ruby`로 잘못 호출한 1회는 `LoadError`로 종료값 1이었고, 같은 파일을 올바른 `bash` 명령으로 즉시 재실행해 25/25를 확인했습니다.

## WU-2R4 감사 보정: marker-only GREEN과 GREEN 자체 승인 차단

계약 `2182378` 뒤 RED `e7b73c5`는 기존 7개 TDD 사례를 유지하면서 marker 출력만 바뀐 RED/GREEN과 GREEN 커밋 자체가 기대값 변경을 승인하는 두 반례를 추가했습니다.

```text
PASS: authentic RED then GREEN
PASS: zero RED commands rejected
PASS: syntax-only RED rejected
PASS: test expectation drift rejected
PASS: contract declared only after boundary rejected
PASS: test drift after first GREEN rejected
PASS: fake GREEN followed by restored expectation rejected
FAIL: marker-only RED and GREEN rejected
FAIL: GREEN cannot self-approve expectation changes
WU_TESTS: 9
CHECKED: 9
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
A7_RED_EXIT:1
```

GREEN `fd0714d`은 RED 명령의 실행 파일이 첫 GREEN까지 byte-identical인지 확인하고, 첫 GREEN에 시험·RED 실행 파일 밖의 변경을 요구하며, GREEN SHA를 기대값 승인 SHA로 재사용하지 못하게 합니다.

```text
PASS: marker-only RED and GREEN rejected
PASS: GREEN cannot self-approve expectation changes
WU_TESTS: 9
CHECKED: 9
VERDICT: PASS
A7_GREEN_EXIT:0

VERDICT: PASS
CHECKED: 115
A7_REPOSITORY_TDD_EXIT:0
```

## WU-3R 감사 보정: historical worktree와 과다 맥락 차단

계약 `2182378` 뒤 RED `fb63b15`는 기존 7개 context 사례를 보존하고, historical worktree 위조와 추적 파일 전체에서 한 개만 뺀 context 두 건을 추가했습니다.

```text
PASS: current exact context
PASS: filename-only declaration rejected
PASS: context hash mismatch rejected
PASS: stale HEAD rejected
PASS: other worktree rejected
PASS: whole repository scope rejected
PASS: undeclared observed read rejected
FAIL: all-but-one repository context rejected
FAIL: historical worktree forgery rejected
WU_TESTS: 9
CHECKED: 9
WU_FAILURE_KIND: missing_behavior
VERDICT: FAIL
A8_RED_EXIT:1
```

GREEN `a424e56`은 historical worktree 문자열이 hash로 고정된 계약 맥락 파일에 실제로 기록됐는지 확인하고, 20개 초과 또는 전체에서 1개 이하만 생략한 read set을 과다 범위로 거부합니다.

```text
PASS: all-but-one repository context rejected
PASS: historical worktree forgery rejected
WU_TESTS: 9
CHECKED: 9
VERDICT: PASS
A8_GREEN_EXIT:0

VERDICT: PASS
CHECKED: 117
A8_REPOSITORY_CONTEXT_EXIT:0
```
