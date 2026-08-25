# WU-3b checkpoint 함수 예산 goal — 2026-08-25

VERDICT: RED

## 결론

checkpoint-gate의 복구 원본은 P11 파일 hard 600만 판정하고 함수 hard 100 LOC를 판정하지 않는다. 원본 B 네 파일 복구와 계약 확장을 섞지 않고, 별도 branch와 worktree에서 함수 100/101 경계를 RED→GREEN으로 추가한다.

## 신원과 소유 경계

- session: `VHREC-20260825T200157+0900-01a03893`
- base: `72c3d8ebc052b3ec4241c1c21422fdc6151c5ef7`
- branch: `task/wu3b-checkpoint-function-budget-20260825T212515`
- worktree: `worktrees/wu3b-checkpoint-function-budget-20260825T212515`
- 소유 파일:
  - `docs/engineering/checkpoint-function-budget-goal-2026-08-25.md`
  - `tests/checkpoint-function-budget.test.mjs`
  - `tools/strict/checkpoint-gate.mjs`
  - `tools/strict/checkpoint-function-scan.mjs`
- 변경 금지: `tests/checkpoint-gate.test.mjs`와 `tools/strict/checkpoint-js-scan.mjs`

## T 계약

- `T(input)`: staged index의 직접 작성 코드 파일, P11 문구, 명시된 scope.
- `T(output)`: 파일 hard 한도와 함수 hard 한도를 각각 판정한 기존 checkpoint JSON과 exit 0/1.
- `T(constraints)`: 새 의존성 없음, 파일 600 LOC 이하, 함수 100 LOC 이하, 실제 index blob만 검사, 생성물·fixture·migration 예외 유지.
- `T(error)`: 지원 언어의 구문을 안전하게 판정하지 못하거나 현재 저장소에 없는 코드 언어가 들어오면 조용히 PASS하지 않고 `size-limit` violation으로 fail-closed.
- `T(stop)`: RED commit과 GREEN commit에서 같은 테스트를 재현하고 exact GREEN SHA의 G/V1/V2/T가 일치할 때 종료.

## EARS AC

- AC1: When JavaScript 계열 함수가 정확히 100 LOC이면 통과하고 101 LOC이면 `size-limit`으로 실패해야 한다.
- AC2: When Python `def`/`async def`가 정확히 100 LOC이면 통과하고 101 LOC이면 실패해야 한다.
- AC3: When shell 함수가 정확히 100 LOC이면 통과하고 101 LOC이면 실패해야 한다.
- AC4: When 현재 저장소 코드 언어 집합 밖의 직접 작성 코드 확장자가 staged되면 parser 부재를 PASS로 숨기지 말고 fail-closed해야 한다.
- AC5: When 함수 한도를 판정해도 기존 파일 600/601, scope, secrets, test weakening 판정은 동일하게 유지돼야 한다.
- AC6: When RED 이후 구현을 추가해도 counter-test 파일은 바뀌지 않아야 한다.
- AC7: When 완료를 판정하면 base 대비 변경은 이 WU 소유 네 파일뿐이어야 한다.

## counter-AC

- 함수 101줄인데 파일 전체가 600줄 이하라 PASS한다.
- Python nested 함수의 dedent를 잘못 읽어 바깥 함수 길이를 축소한다.
- JS 문자열·정규식·주석 안의 중괄호를 함수 종료로 센다.
- shell 인용문 안의 중괄호를 함수 종료로 센다.
- 지원하지 않는 `.go` 변경을 함수 0개로 오인해 PASS한다.
- 테스트를 구현 뒤에 바꾸거나 기존 600줄 테스트를 축약한다.

## 오류·롤백 계약

- parser 오류: 파일 경로와 언어만 포함한 `size-limit` violation, 비밀·원문 미출력.
- hash 또는 scope 불일치: 양쪽 보존, `RECOVERY_REQUIRED`.
- RED 미재현: 구현 금지, `BLOCKED`.
- 롤백: 이 WU branch/ref를 보존한 채 후속 commit을 되돌릴 수 있다. B 원본 branch는 변경하지 않는다.

## 검증 명령

```text
node --test tests/checkpoint-function-budget.test.mjs
node --test tests/checkpoint-gate.test.mjs
node --check tools/strict/checkpoint-gate.mjs
node --check tools/strict/checkpoint-function-scan.mjs
bash scripts/acceptance-principles-check.sh
bash verify.sh
bash scripts/check-docs-sot.sh
git diff --check
git show --check HEAD
```

## 판정 장부

- RED: `2026-08-25T21:27:24+09:00`, `node --test tests/checkpoint-function-budget.test.mjs`, exit 1, tests 7, pass 3, fail 4.
- RED 원문: `/tmp/vhrec-wu3b-red.tMakr9/node-test-red.log`, SHA-256 `00a8fe65f61eb11a09e071ab72cf7903417bfa99fa854dac211188a1ca24e037`.
- RED 해석: 100줄 정상 경계는 통과했고, 미구현인 101줄 JS/Python/shell 차단과 unsupported 언어 fail-closed 네 동작이 실패했다.
- 최초 RED commit `33bafa51825ac5fa9e82b2f84430001e6dbf635e`은 `git show --check`가 테스트 EOF 빈 줄을 보고해 canonical RED에서 제외한다. 단언을 바꾸지 않고 빈 줄 1개만 제거한 테스트 SHA-256 `00d957a7b1e1835b0d4a74d6db34fac036255734dea251f5fe795f01b3ad54be`로 재실행한 결과도 tests 7, pass 3, fail 4, exit 1이다.
- 교정 RED 원문: `/tmp/vhrec-wu3b-red-corrected.ul6jLn/node-test-red-corrected.log`, SHA-256 `2f1b59618e87591fc02a9b6600c66bd9e78db428ccedc0c40382bae5429937ab`.
- GREEN: `NOT_RUN`
- G: `NOT_RUN`
- V1: `NOT_RUN`
- V2: `NOT_RUN`
- T: `NOT_RUN`
