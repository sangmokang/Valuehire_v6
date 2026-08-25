# WU-3b checkpoint 함수 예산 goal — 2026-08-25

VERDICT: LOCAL_GREEN_CHECKPOINT

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
  - `tools/strict/checkpoint-js-scan.mjs`
  - `tools/strict/checkpoint-js-lexer.mjs`
- 변경 금지: `tests/checkpoint-gate.test.mjs`

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
- AC5a: When 기존 scanner 자체가 새 함수 한도에 걸리면 예외로 숨기지 않고 lexer를 helper 모듈로 분리하며 기존 45개 동작을 유지해야 한다.
- AC6: When RED 이후 구현을 추가해도 counter-test 파일은 바뀌지 않아야 한다.
- AC7: When 완료를 판정하면 base 대비 변경은 이 WU 소유 여섯 파일뿐이어야 한다.
- AC8: When `.c`, `.h`, `.cpp`, `.cc`, `.hpp`, `.m`, `.vue`, `.svelte`, `.lua`, `.pl`, `.sql`, `.scala`가 staged되면 파일·함수 예산을 모두 우회하지 않아야 한다.

## counter-AC

- 함수 101줄인데 파일 전체가 600줄 이하라 PASS한다.
- Python nested 함수의 dedent를 잘못 읽어 바깥 함수 길이를 축소한다.
- JS 문자열·정규식·주석 안의 중괄호를 함수 종료로 센다.
- shell 인용문 안의 중괄호를 함수 종료로 센다.
- 지원하지 않는 `.go` 변경을 함수 0개로 오인해 PASS한다.
- 알려진 비-JS/Python/shell 코드 확장자를 size 검사 대상에서 제외해 601줄 파일도 PASS한다.
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
- 첫 GREEN 시도는 Python trailing newline을 함수 줄로 더해 `5/7`이었고, dedent 뒤 EOF 계산을 수정해 `7/7`이 됐다. 이어서 기존 45개 중 scanner 소스를 stage하는 1개가 269줄 `tokenizeJavaScript`를 차단해 `44/45`였다. P11 예외 대신 lexer class helper로 분리해 각 method를 hard 100 이하로 만든다.
- GREEN candidate: function boundary 7/7, original checkpoint regression 45/45, node check 4개 exit 0.
- GREEN outputs: function tests SHA-256 `273077671aa3140d1989e12a2257a4f72ecb23ad45de0dc01c1454e52c11e298`; original tests SHA-256 `207d915ee48c8291d14dfb39084998bebd8d703b87ea33e31a92f816d092d4c9`.
- hard function readback: gate max 44, function scanner max 94, JS scanner max 77, JS lexer max 61, counter-test max 16 LOC.
- adversarial spans: JS regex/string brace 4 LOC, shell quoted brace 3 LOC, Python outer/inner dedent 4/2 LOC, 모두 PASS.
- V1 `a9573ec8-ac7b-4274-b93b-37da3bafd5a6` finding `V1-F003`: 12개 코드 확장자가 1200줄 파일과 101줄 함수를 모두 exit 0으로 통과함. counter-test RED를 구현 전에 추가한다.
- V1-F003 counter RED: `2026-08-25T22:47:09+09:00`, exact HEAD `c0a7a7051dc62b7eb99d5b1ae3f6c976612d096c`, `node --test tests/checkpoint-function-budget.test.mjs`, exit 1, tests 31, pass 7, fail 24.
- V1-F003 RED 원문: `/tmp/vhrec-wu3b-v1f003-red.SFy8KI/full.log`, SHA-256 `fad0c50c3b8932a2ae7d298a43e18c7942be826abad8580f7fd7dc2a3de34ad0`, session `VHREC-20260825T200157+0900-01a03893`.
- V1-F003 RED 해석: 기존 7개 함수 경계 검사는 전부 통과했고, 새 12개 확장자 각각의 unsupported fail-closed와 601줄 hard limit 두 단언만 실패했다.
- V1-F003 GREEN candidate: `2026-08-25T22:55:00+09:00`, exact RED HEAD `3e1fffad1436968219348de64bbfb33a9f949cbf` plus unstaged one-line implementation, function suite 31/31 and original suite 45/45, both exit 0.
- V1-F003 GREEN 원문: `/tmp/vhrec-wu3b-v1f003-green-target.ndIDlQ/full.log` SHA-256 `bce3da8c74de84ca49cf783aec8499db75d27ebb1bf401ac4d7ce2564a8840e8`; `/tmp/vhrec-wu3b-v1f003-green-regression.3h1PjI/full.log` SHA-256 `75beb429d0fb6c9095146603ddfe5ef108252cb6c22233e5773d37b0c836b9a9`.
- RED counter-test SHA-256 readback: `d8fe061c53d9238a83f376540eef996ec905ca69f35a0b9544effb1286c0f215`; GREEN 구현 뒤에도 동일하다.
- pre-commit G: syntax 4개, principles 34/34, `verify.sh`, docs SOT, `git diff --check` 모두 exit 0; 원문 `/tmp/vhrec-wu3b-v1f003-precommit-g.XrbXLt`.
- size readback: 새 counter-test 177줄, 원본 B test 정확히 600줄, gate 531줄, function scanner 239줄, JS scanner 238줄, lexer 366줄.
- G: `NOT_RUN`
- V1: `NOT_RUN`
- V2: `NOT_RUN`
- T: `NOT_RUN`
