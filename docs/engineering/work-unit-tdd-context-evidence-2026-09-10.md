# Work Unit TDD·맥락 계약 실행 증거 — 2026-09-10

## 결론

WU-1은 불완전한 작업 기록을 실제 입력으로 거부하고, 정상 기록 한 건만 받아들이는 상태입니다. 다음 작업 단위는 아직 시작하지 않았습니다.

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
