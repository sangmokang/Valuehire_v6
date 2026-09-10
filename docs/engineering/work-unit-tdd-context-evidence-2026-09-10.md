# Work Unit TDD·맥락 계약 실행 증거 — 2026-09-10

## 결론

WU-1~WU-3은 각각 스키마, RED/GREEN 이력, 현재 Git 맥락을 실제 입력으로 검증합니다. 완료된 각 WU는 같은 시험의 GREEN과 작은 반례를 통과했고, WU-4·WU-5는 아직 시작하지 않았습니다.

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
