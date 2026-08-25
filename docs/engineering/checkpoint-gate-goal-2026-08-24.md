# WU-3a checkpoint 판정기 goal — 2026-08-24

VERDICT: RED

## 2026-08-25 무손실 복구 상태

검증된 기준 `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`에서 전용 branch `task/wu3a-checkpoint-gate-20260825T200952`와 전용 worktree를 만들었다. 이 RED 상태에는 goal과 테스트만 있고 구현 파일 두 개는 없다.

- session: `VHREC-20260825T200157+0900-01a03893`
- fresh RED command: `node --test tests/checkpoint-gate.test.mjs`
- fresh RED time: `2026-08-25T20:48:22+09:00` ~ `2026-08-25T20:53:58+09:00`
- fresh RED result: exit 1, tests 45, pass 0, fail 45
- raw output: `/tmp/vhrec-b-red.rveyOb/node-test-red.log`
- raw output SHA-256: `7f4c0176c3073577ce8e7700da66817e6470cfa0ecd5b6ef102a3edd9b8bb382`
- failure reason: `tools/strict/checkpoint-gate.mjs` 부재로 요구 CLI 동작을 실행할 수 없음

복구 소유 범위는 다음 네 파일로 고정한다.

1. `docs/engineering/checkpoint-gate-goal-2026-08-24.md`
2. `tests/checkpoint-gate.test.mjs`
3. `tools/strict/checkpoint-gate.mjs`
4. `tools/strict/checkpoint-js-scan.mjs`

canonical post-writer rescue hash는 goal `37de8d4342349baa85ae837651d5679180200425dca80a121c10b7324fd9c9f1`, test `72b9d42b521c04d242740d33683bbb11f2a2c2e10f302c10dec1d4652c589267`, gate `e93da3cf4a4623c8b1da0f8adafd3f7d166b7133a351c9fb286042c73da07ca9`, scanner `01c0f9603f67c292464c6c8d814b4d9d6f9fb9820c58aa3842d19c07c02c4c43`이다. 테스트는 정확히 600줄이며 RED 이후 한 줄도 수정하지 않는다. 최초 pre-writer goal hash `58eb…`는 외부 writer 종료 뒤 inventory를 폐기·재시작했으므로 정본이 아니다.

현재 상태는 `RED_CONFIRMED`; GREEN, G, V1, V2, T는 `NOT_RUN`이다. 아래 2026-08-24 실행 로그와 HEAD·45/45·V1/V2 문구는 복구 전 과거 기록이며 새 commit 검증에 재사용하지 않는다.

## 계약 결론

기존 판정은 감사에서 뒤집혔고, 핵심 오탐 수정과 로컬 재검증을 완료했다. 독립 V1/V2 결과가 도착하기 전까지 최종 PASS는 보류한다. 이 작업은 커밋을 실행하지 않고, 준비된 변경이 네 안전조건을 모두 만족하는지만 판단한다.

현재 범위는 새 검사기·시험·기록 문서뿐이며 저장소 규칙·장부·훅·커밋은 건드리지 않는다.

세 실행 산출물과 goal을 합친 네 소유 파일만 복구하며 범위 밖 변경은 포함하지 않는다.

## 판단 근거

- 정본인 `docs/sot/coding-principles.md:26`의 P11은 직접 작성 코드 파일을 soft 300 / hard 600줄로 정한다. 판정기는 숫자 600을 복사하지 않고 매 실행마다 이 문장에서 hard 값을 읽으며, 조항이 없을 때만 500을 쓴다.
- rescue 원본 줄수는 gate 502, scanner 597, tests 600으로 모두 P11 hard 600 이하이다.
- 기존 훅인 `hooks/pre-commit:56`은 비밀 판정을 `verify.sh` 한 벌에 위임하고, `hooks/pre-commit:73`의 정확한 호출은 `SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh`다. 새 판정기는 이 호출을 재사용하고, `verify.sh` 자체가 없을 때만 보수적 내장 패턴으로 스테이지 blob을 검사한다. 복구 worktree의 실제 검증은 존재하는 `.secret-patterns` symlink를 사용하며 `.secret-patterns.default`만으로 초록을 만들지 않는다.
- 병렬 A 장부는 착수 시 없었으나 구현 중 `task/wu1-strict-ledger-20260824`에 `.strict/run-ledger/<run_id>.json` 파일 인터페이스가 생성됐다. 현재 고정 `wus` 스키마는 `id/ac/status/commit`만 있고 파일 범위 필드는 아직 없으므로, 범위 선언이 없는 현재 장부는 사용자가 반복 지정한 `--scope <glob>`를 파일 범위 계약으로 삼는다. 향후 장부 WU가 `scope/scopes/files/paths`를 제공하면 그 파일 선언을 우선하며, `ledger.mjs`는 import하지 않는다.
- 기준 커밋과 스테이지를 비교해야 작업트리 덮어쓰기나 삭제를 놓치지 않는다. 모든 내용 판정은 작업트리 파일이 아니라 Git 인덱스 blob을 읽는다.

### 결정 카드

> **무엇을** — 네 검사를 한 CLI에서 독립 실행하고 위반 목록의 합집합으로 전체 AND 판정을 계산한다.
> **왜** — 한 검사 실패가 뒤 검사를 생략하면 사용자가 한 번에 전체 수리 범위를 알 수 없고, 부분 합격을 전체 합격으로 오인할 수 있다.
> **버린 길** — `hooks/pre-commit` 전체 호출은 비밀 검사 외 정책까지 섞여 검사별 독립 판정과 JSON 계약을 깨므로 기각했다. `ledger.mjs` import도 병렬 A 구현에 런타임 결합되므로 기각했다.
> **대가** — 장부 스키마 오류나 기존 비밀 스캐너 실행 오류도 안전하게 불합격 처리되어, 환경 결함이 있을 때 커밋 가능 판정이 보수적이다.
> **되돌리기** — 신규 goal·테스트·`tools/strict/checkpoint-gate.mjs`·`tools/strict/checkpoint-js-scan.mjs`를 삭제하면 원상복구된다. 기존 훅·정본·장부에는 변경이 없다.

## 위험등급과 영향 경계

- 위험등급: L3. 이유는 보안 검사 호출, 커밋 직전 공유 판정 도구, 네 파일 변경이다.
- 영향 반경: 수동으로 `node tools/strict/checkpoint-gate.mjs ...`를 실행한 프로세스의 stdout/stderr와 종료값뿐이다. 훅·CI·커밋에는 연결하지 않는다.
- 데이터 안전: 판정기는 Git 인덱스와 정본을 읽기만 하며 파일, 장부, ref, index를 쓰지 않는다. 비밀값은 출력하지 않고 파일 경로와 검사기 실패만 보고한다.
- 롤백: 신규 파일 삭제. 기존 파일 수정이 없으므로 데이터 복구나 마이그레이션은 없다.

## 계약 스펙

### CLI 입력

```text
node tools/strict/checkpoint-gate.mjs --base <commit-ish> [--scope <glob> ...] [--json]
```
→ CLI는 기준 커밋과 선택적 범위를 받아 구조화된 판정을 출력하는 입력면이다.

- `--base`는 필수이며 실제 commit으로 해석되어야 한다.
- 장부는 `.strict/run-ledger/*.json`을 파일 인터페이스로만 읽는다. 하나의 현재 WU가 선언한 `scope`/`scopes`/`files`/`paths` 문자열 또는 문자열 배열을 사용한다.
- 장부가 없거나 현재 A 스키마처럼 WU에 파일 범위 선언이 없을 때 `--scope`가 하나 이상 필요하다. 장부 JSON이 파싱 불가하거나 범위 선언을 가진 현재 WU가 여러 개이면 fail-closed한다.
- 글로브는 이름 규칙으로 파일을 모으는 방식이며 `*`, `**`, `?`를 지원한다.

### CLI 출력과 오류

```json
{"pass":false,"violations":[{"check":"scope","file":"path","detail":"reason"}]}
```
→ 실패 시 위반 종류·파일·상세를 한 JSON 객체로 반환한다.

- `--json`: stdout에 위 객체 한 개만 출력한다.
- 성공: 종료값 0, `pass: true`, 빈 `violations`.
- 위반·입력 오류·검사기 실행 오류: 종료값 1, `pass: false`, 하나 이상의 violation.
- 각 violation의 `check`는 `scope`, `secrets`, `test-weakening`, `size-limit`, 또는 실행 전 입력 문제를 뜻하는 `input`이다.
- 비밀 매칭 원문은 절대 출력하지 않는다.

### 경계

- 스테이지 변경 0개는 명시된 네 위반이 없으므로 통과한다. 이 WU는 “커밋할 내용 존재”라는 다섯 번째 정책을 추가하지 않는다.
- rename은 기존 경로와 새 경로를 함께 비교하되 테스트 파일 rename을 삭제로 오인하지 않는다.
- 테스트 파일 삭제는 assertion 수와 무관하게 반드시 불합격이다.
- 코드 파일은 정본 hard 값과 같은 줄이면 통과하고 한 줄 초과면 실패한다.
- 생성물·vendor·dist/build·coverage·migration·fixture 경로는 정본의 직접 작성 코드 예외로 크기 검사에서 제외한다.
- 병렬 실행에 공유 임시 상태를 만들지 않는다. 하위 비밀 스캐너의 stdout/stderr는 캡처하고 JSON 출력을 오염시키지 않는다.

## EARS 인수 기준과 counter-AC

### AC-1

When 유효한 `--base`와 스테이지된 변경이 주어질 때, 시스템은 범위·비밀·테스트 약화·파일 크기의 네 검사를 각각 독립 판정하고 하나라도 위반하면 종료값 1과 해당 `{check,file,detail}`을, 모두 정상이면 종료값 0을 반환해야 한다.

검증 명령:

```text
node --test tests/checkpoint-gate.test.mjs
```
→ 이 명령은 실제 CLI를 임시 저장소에서 실행하는 회귀 검증이다.

기대값: 전체 테스트 통과, 실패 0건.

counter-AC: 기준 커밋에 있던 테스트 파일을 스테이지에서 삭제했는데 종료값 0이면 전체 WU는 FAIL이다. 추가 공격은 skip/only/todo 각각의 증가, assertion 감소, hard 경계/경계+1, 기존 비밀 스캐너 호출 실패, 장부 부재 시 scope 누락이다.

## Harness 게이트 계획

1. Gate 0~1: 정본·장부·기존 훅·과거 브랜치를 읽고 이 계약을 고정한다.
2. Gate 2: 구현 파일이 없는 상태에서 테스트가 모듈 부재 때문에가 아니라 요구 동작 부재로 실패하도록 임시 최소 스텁을 사용하지 않고, 대상 CLI 부재 RED를 기록한다.
3. Gate 3: `checkpoint-gate.mjs`와 P11 한도 안에서 분리한 `checkpoint-js-scan.mjs`를 최소 구현한다. 테스트는 각 새 반례를 먼저 RED로 고정한 뒤 GREEN으로 만든다.
4. R2: skip/only/todo, assertion 삭제, 테스트 삭제, hard+1을 실제로 주입한다. 정상쌍도 실행한다.
5. R4: 실제 진입점은 CLI 직접 호출이다. 훅 배선은 명시적 비범위다.
6. Gate 4: 목표 테스트, 구문 검사, 원칙 검사, 기존 비밀 검사, 파일 줄수, 허용 경로 diff를 실행한다.
7. V1: 구현 결론을 주지 않은 증거 묶음을 Claude CLI에 전달해 독립 공격한다.
8. V2: V1의 모든 재현 가능한 주장을 새 Codex 검증 맥락에서 다시 실행하고 누락·오탐을 양방향 공격한다.

## 읽은 정본과 2026-08-24 착수 증거 — 현재 SHA 재사용 금지

- `docs/sot/coding-principles.md` — 직접 읽음, P11 hard 600 확인.
- `docs/sot/principles.yaml` — 직접 읽음, P1~P24·§1-B·V-1~V-5 34개 항목 확인.
- `docs/sot/hook-contracts.md` — 기존 pre-commit 비밀 위임과 종료값 계약 확인.
- `hooks/pre-commit`·`verify.sh` — index 스캔 호출과 fail-closed 동작 확인.
- `docs/engineering/work-unit-process-adoption-2026-08-21.md` — WU당 선언 범위와 독립 반증 취지 확인.

```text
2026-08-24T07:33:25+09:00
SESSION: 01a030bf-f7dc-7123-abfc-31ffc84e3107
HEAD: c59bad7b160c473cda5545e76e6fa6bcc711a7ea
COMMAND: bash scripts/acceptance-principles-check.sh
EXIT: 0
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 이 블록은 2026-08-24 착수 이력이다. 새 task commit의 검증 증거가 아니며 현재 실행으로 교체하기 전에는 PASS로 세지 않는다.

## 2026-08-24 RED→GREEN·mutation 원장 — 과거 이력

- 최초 대상 CLI 부재 상태에서 요구 동작 테스트가 실패한 뒤 구현을 시작했다.
- 감사에서 세미콜론 없는 assertion 다음의 무관한 구조분해 대입이 assertion 감소로 오인되는 정상 fixture를 `before.assertions=1 / after.assertions=0`으로 RED 재현했다. 구조분해 여는 괄호부터 대응하는 닫는 괄호까지를 확인하도록 범위를 제한해 `1 -> 1` GREEN으로 만들었다.
- 구조분해로 assertion을 no-op 객체에 재할당하는 공격 fixture는 계속 `assertions decreased 2 -> 0`으로 exit 1을 반환한다.
- 무관한 일반 객체 `const paging = { skip: 1 }`를 테스트 약화로 오인하는 V2 반례는 관련 단일 테스트에서 `expected 0 / actual 1`로 RED를 재현하고, 테스트 호출의 인라인 옵션 객체에서만 truthy `skip/only/todo` 키를 세도록 좁혀 GREEN으로 만들었다.
- 진짜 `assert` import를 로컬 no-op 객체로 가리는 V1 반례는 `expected violation exit 1 / actual 0`으로 RED를 재현하고, 비신뢰 `assert`/`expect` 재바인딩·메서드 덮어쓰기를 assertion으로 세지 않도록 고쳐 GREEN으로 만들었다.
- `({ assert } = ...)`와 `[assert] = [...]` 구조분해 재할당 V1 반례도 같은 방식으로 RED를 재현하고 구조분해 LHS 종료 뒤 `=`를 재바인딩으로 분류해 GREEN으로 만들었다.
- mutation: 인라인 테스트 옵션 문맥 가드를 제거하면 무관 `paging.skip` 정상 fixture가 RED가 됐고, assertion shadow 수집을 빈 집합으로 바꾸면 no-op shadow fixture가 RED가 됐다. 두 mutation은 즉시 원복했으며 원복 후 단일 테스트와 전체 스위트를 다시 통과했다.

## 비범위

- 커밋 실행, 자동 커밋, 장부 갱신, 훅·CI 배선.
- `ledger.mjs` import 또는 병렬 A 소스 의존.
- `docs/sot/INDEX.md` 및 다른 정본 변경.
- 기존 pre-commit의 비밀 외 검사 재구현.

## 2026-08-24 적대 검증 로그 — 현재 SHA에 무효

### 과거 G — 최종 로컬 증거가 아님

```text
HEAD: 3094eefa646b102074dfb6401777afe450223e6c
COMMAND: node --test tests/checkpoint-gate.test.mjs
RESULT: tests 45 / pass 45 / fail 0 / skipped 0 / todo 0

COMMAND: node --check tools/strict/checkpoint-gate.mjs
EXIT: 0
COMMAND: node --check tools/strict/checkpoint-js-scan.mjs
EXIT: 0
COMMAND: bash scripts/acceptance-principles-check.sh
EXIT: 0
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34

COMMAND: git diff --check
EXIT: 0
COMMAND: node tools/strict/checkpoint-gate.mjs --base HEAD --json --scope tools/strict/checkpoint* --scope tests/checkpoint-gate.test.mjs --scope docs/engineering/checkpoint-gate-goal-2026-08-24.md
EXIT: 0
OUTPUT: {"pass":true,"violations":[]}
COMMAND: git diff --cached --name-only
OUTPUT: <empty>
```
→ `3094eef` dirty rescue 시점의 기록이다. 새 task commit의 G/V1/V2/T로 재사용하지 않는다.

수정 후보 해시:

```text
e93da3cf4a4623c8b1da0f8adafd3f7d166b7133a351c9fb286042c73da07ca9  tools/strict/checkpoint-gate.mjs
01c0f9603f67c292464c6c8d814b4d9d6f9fb9820c58aa3842d19c07c02c4c43  tools/strict/checkpoint-js-scan.mjs
72b9d42b521c04d242740d33683bbb11f2a2c2e10f302c10dec1d4652c589267  tests/checkpoint-gate.test.mjs
```
→ 세 실행 산출물의 rescue 원본 식별값이다. goal을 포함한 네 파일의 최종 hash는 commit 뒤 외부 복구 manifest에서 readback한다.

### 과거 V1 — 현재 SHA 재검증 필요

- 실행기 정체 1회는 후보 무변경 상태에서 중단하고 `--safe-mode --no-session-persistence --permission-mode bypassPermissions --tools Bash,Read,Grep,Glob`로 재실행했다.
- V1은 먼저 일반 객체 `skip` 오탐, 직접 no-op assertion shadow, 구조분해 assertion 재할당을 각각 FAIL로 보고했다. 모든 재현을 RED fixture로 고정하고 수정했다.
- 이전 세션 결과는 수정 전 후보에 대한 기록이므로 폐기했다. 새 후보에 대한 실제 Claude CLI는 도구 세션이 장시간 `tool_use` 상태로 종료되어 결과를 받지 못했다. V1 결과를 새 세션으로 확보하기 전에는 PASS를 선언하지 않는다.

### 과거 V2 — 현재 SHA 재검증 필요

- 검증자: 새 `/root/checkpoint_v2_postfix`; 후보 편집 권한 없이 새 문맥에서 실행 중이다.
- 새 후보에 대한 결론과 증거를 수신한 뒤 기록한다.
- 초기 V2의 기존 base secret 지적은 사용자 착수 계약이 요구한 기존 pre-commit 전체-index 호출의 정확한 재사용이므로 결함이 아니다. 최종 V2는 이 명시 계약을 반영해 동의했다.

## 복구 RED T 판정

`RED_CONFIRMED`: 구현 부재 상태에서 원명령이 45개 요구 동작을 수집하고 45개 모두 실패했다. GREEN, G, V1, V2, T는 아직 `NOT_RUN`이며 과거 45/45와 검증자 문구는 결론 근거가 아니다. 자동 훅 배선·장부 갱신은 WU-3b 범위다.
