# WU-3a checkpoint 판정기 goal — 2026-08-24

VERDICT: CHECKPOINT_PENDING

## 2026-08-26 명시적 run 선택 계약

현재 B 판정기는 검사 대상을 명시하지 않고 모든 run 장부의 `updated_at`을 비교한다. 따라서 더 최신인 무관 run 하나가 추가되면 같은 호출의 범위 판정이 달라질 수 있다. 이번 L3 변경은 필수 `--run-id`가 가리키는 정규 파일 하나만 읽고, 범위 출처를 그 장부 또는 `--scope` 중 정확히 하나로 제한한다. A의 `id/ac/status/commit` WU 스키마와 C 구현은 바꾸지 않는다.

### 현재 상태와 근본 원인

- `tools/strict/checkpoint-gate.mjs:13-31`의 인자 판독에는 `--run-id`가 없다.
- `tools/strict/checkpoint-gate.mjs:124-187`은 `.strict/run-ledger/*.json` 전체를 읽고 `updated_at` 최대값을 선택한다.
- `tools/strict/checkpoint-gate.mjs:189-216`은 장부가 없거나 범위가 없으면 `--scope`로 조용히 대체한다.
- 근본 원인은 범위의 권위자를 호출자가 정하지 않고, 파일 시각과 fallback 규칙이 추론한다는 점이다.

### CLI 입출력·오류·경계 계약

```text
node tools/strict/checkpoint-gate.mjs \
  --base <commit-ish> \
  --run-id <r-13자리-4자리> \
  [--scope <glob> ...] \
  [--json]
```
→ `--base`와 `--run-id`는 필수다. `--run-id`는 `^r-\d{13}-\d{4}$`와 일치해야 하며, `.strict/run-ledger/<run_id>.json` 한 파일만 선택한다.

- 지정 파일 부재, 심볼릭 링크, 빈 파일, JSON 파싱 실패, 내부 `run_id` 불일치는 다른 검사 전에 `input` 위반과 종료값 1을 낸다.
- `wus`에서 상태가 `open`, `red`, `green`이고 `scope`, `scopes`, `files`, `paths`에 문자열 또는 문자열 배열을 가진 항목이 정확히 하나면 그 범위만 쓴다.
- 범위 선언 WU가 둘 이상이면 안전하게 종료값 1을 낸다.
- 장부 범위가 있으면 `--scope` 동시 입력은 `input` 위반이다.
- 장부 범위가 없으면 `--scope`를 하나 이상 요구한다. 이는 A의 현재 WU 스키마와 호환되는 유일한 fallback이다.
- 장부 없이 `--scope`만 제공하는 구형 호출과 스테이지 변경 0개인 호출도 유효한 `--run-id` 없이는 통과하지 않는다.
- 기존 JSON 객체, 검사별 `check`, 성공 종료값 0, 실패 종료값 1 계약은 유지한다.

### EARS 인수 기준

1. **AC-1** — When 유효한 `--run-id`가 주어질 때, 시스템은 지정한 run 장부 하나만 읽고 다른 장부의 `updated_at`이나 내용에 영향을 받지 않아야 한다.
2. **AC-2** — When 지정 run에 범위 선언이 있을 때, 시스템은 장부 범위만 사용하고 `--scope` 동시 입력을 거부해야 한다.
3. **AC-3** — When 지정 run에 범위 선언이 없을 때, 시스템은 `--scope`를 요구하고 누락 시 종료값 1이어야 한다.
4. **AC-4** — When `run_id`가 누락·형식 오류·파일 부재·비정규 파일·JSON 오류·내용 불일치일 때, 시스템은 다른 검사 실행 전에 종료값 1과 `input` 위반을 출력해야 한다.
5. **데이터 안전 AC** — While 판정기가 run 장부와 Git 인덱스를 검사할 때, 시스템은 장부·작업 파일·인덱스·ref를 쓰거나 비밀 원문을 출력하지 않아야 한다.

검증 원명령은 `node --check tools/strict/checkpoint-gate.mjs`와 `node --test tests/checkpoint-gate.test.mjs`다. 기대값은 구문 검사 종료값 0, B 테스트 `fail 0`, `skipped 0`이다.

### Counter-AC와 RED 원장 계획

- 더 최신인 무관 run을 추가했을 때 지정 run의 결과가 바뀌면 실패다.
- `--run-id` 없는 구형 호출, 장부 범위와 `--scope` 동시 입력, 빈·잘못된 JSON·심볼릭 링크 장부가 통과하면 실패다.
- 최신 선택 테스트의 기대값만 뒤집고 제품 코드에서 전체 장부 열거와 `updated_at` 비교가 남으면 실패다.
- RED는 기존 구현에 새 계약 시험만 적용해 누락된 동작 때문에 실패시킨다. RED commit 뒤 테스트 파일은 GREEN 구현 commit에서 변경하지 않는다.
- GREEN 뒤 제품 변이, 빈 테스트, `test.skip`, `exit 0`/no-op 변이를 임시 복제본에 주입하고 모두 원 검증이 실패하는지 확인한다.
- P11 hard 600의 정상 경계와 601줄 고장 경계를 모두 실행한다. 검사 대상 0개는 합격으로 세지 않는다.

### 영향 반경·비범위·롤백

- 영향 반경은 수동 B CLI의 입력 자격과 범위 선택이다. 기존 비밀·테스트 약화·파일 크기 판정 로직과 JSON 출력 형식은 유지한다.
- 수정 허용 파일은 이 goal, `tests/checkpoint-gate.test.mjs`, `tools/strict/checkpoint-gate.mjs`뿐이다. A의 `tools/strict/ledger.mjs`, WU 스키마, C 파일, 훅, CI, main, 원격은 비범위다.
- 판정기는 읽기 전용이다. 병렬 호출 사이에 공유 임시 상태를 만들지 않는다.
- 롤백은 이번 GREEN commit을 되돌리는 한 번의 로컬 Git 명령이다. 장부 데이터 마이그레이션이 없으므로 데이터 복구는 필요하지 않다.

### 결정 카드

> **무엇을** — 호출자가 준 `run_id`를 검증하고 대응하는 정규 JSON 파일 하나만 읽는다.
> **왜** — 파일 시각은 작업 대상의 신원이 아니며 무관 run 생성만으로 판정이 바뀐다.
> **버린 길** — 전체 장부에서 최신 파일 선택과 장부 오류 시 `--scope` 대체는 대상 추측과 조용한 실패를 남겨 기각했다. A 장부 스키마 확장은 별도 계약 변경이라 이번 B 수정에서 분리했다.
> **대가** — 기존 호출자는 모두 `--run-id`를 추가해야 하며, 장부가 범위를 담지 않는 동안 `--scope`도 함께 명시해야 한다.
> **되돌리기** — GREEN commit을 로컬에서 revert하면 이전 CLI 계약으로 돌아간다. 장부나 데이터는 수정하지 않는다.

### 2026-08-26 Strict SOT 직접 로드 장부

```text
2026-08-26T17:13:37,045367000+09:00
SESSION=strict-b-checkpoint-20260826T1713+0900
HEAD=72c3d8ebc052b3ec4241c1c21422fdc6151c5ef7
COMMAND=bash scripts/acceptance-principles-check.sh
EXIT=0
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```
→ 현재 저장소의 정본과 기계 장부를 직접 읽은 뒤 원명령을 실행했다. 34개 계약 연결과 pre-push/CI 배선이 모두 확인되어 PLAN 자격은 PASS다.

### 2026-08-26 RED 원장

```text
2026-08-26T17:20:05,169609000+09:00
SESSION=strict-b-checkpoint-20260826T1719-r2+0900
HEAD=72c3d8ebc052b3ec4241c1c21422fdc6151c5ef7
TEST_SHA256=2aa6fe212e2fdc07d5200b9f2a2076e48cf818019ab347a4771682f16665ade0
COMMAND=node --test tests/checkpoint-gate.test.mjs
EXIT=1
OUTPUT_SHA256=077b78733b9bc1274b253d82001e3bda78112286b4add1c7e988a7aed2ca37d4
tests=49 pass=7 fail=42 skipped=0 todo=0
```
→ 기존 구현에 새 계약 시험을 적용했다. 문법이나 import가 아니라 `--run-id`를 모르는 기존 동작과 구형 무지정 호출의 통과 때문에 42건이 실패했다. 이 600줄 시험 파일을 RED commit 뒤 고정한다.

## 2026-08-25 무손실 복구 상태

검증된 기준 `c59bad7b160c473cda5545e76e6fa6bcc711a7ea`에서 전용 branch `task/wu3a-checkpoint-gate-20260825T200952`와 전용 worktree를 만들었다. RED commit에는 goal과 테스트만 있고, 현재 GREEN 후보에는 rescue에서 hash-readback한 구현 파일 두 개가 추가됐다.

- session: `VHREC-20260825T200157+0900-01a03893`
- fresh RED command: `node --test tests/checkpoint-gate.test.mjs`
- fresh RED time: `2026-08-25T20:48:22+09:00` ~ `2026-08-25T20:53:58+09:00`
- fresh RED result: exit 1, tests 45, pass 0, fail 45
- raw output: `/tmp/vhrec-b-red.rveyOb/node-test-red.log`
- raw output SHA-256: `7f4c0176c3073577ce8e7700da66817e6470cfa0ecd5b6ef102a3edd9b8bb382`
- failure reason: `tools/strict/checkpoint-gate.mjs` 부재로 요구 CLI 동작을 실행할 수 없음
- RED commit: `11593107fefcffb1b77d4d76370dd1e6a1452a5e`
- clean RED replay: exit 1, tests 45, pass 0, fail 45, output SHA-256 `9e5850bc59f6038c7d088d6b857142fb93ee027ac9e48be589964603a93058da`
- fresh precommit GREEN time: `2026-08-25T21:17:29+09:00` ~ `2026-08-25T21:18:04+09:00`
- fresh precommit GREEN: node check 2개 exit 0, tests 45, pass 45, fail 0
- fresh GREEN output SHA-256: `05eecd7e2a3aa11ca5195c1d59c2032c6c9403506a6bd2c16205096176a47983`

복구 소유 범위는 다음 네 파일로 고정한다.

1. `docs/engineering/checkpoint-gate-goal-2026-08-24.md`
2. `tests/checkpoint-gate.test.mjs`
3. `tools/strict/checkpoint-gate.mjs`
4. `tools/strict/checkpoint-js-scan.mjs`

canonical post-writer rescue hash는 goal `37de8d4342349baa85ae837651d5679180200425dca80a121c10b7324fd9c9f1`, test `72b9d42b521c04d242740d33683bbb11f2a2c2e10f302c10dec1d4652c589267`, gate `e93da3cf4a4623c8b1da0f8adafd3f7d166b7133a351c9fb286042c73da07ca9`, scanner `01c0f9603f67c292464c6c8d814b4d9d6f9fb9820c58aa3842d19c07c02c4c43`이다. 테스트는 정확히 600줄이며 RED 이후 한 줄도 수정하지 않는다. 최초 pre-writer goal hash `58eb…`는 외부 writer 종료 뒤 inventory를 폐기·재시작했으므로 정본이 아니다.

현재 상태는 `PRECOMMIT_GREEN`; exact GREEN commit의 G, V1, V2, T는 `NOT_RUN`이다. 아래 2026-08-24 착수·mutation 이력은 계약 배경일 뿐 새 commit 검증에 재사용하지 않는다.

## 계약 결론

요구 동작 부재 RED와 구현 복원 GREEN을 분리했다. exact GREEN commit에서 G와 독립 V1/V2가 끝나기 전까지 최종 PASS는 보류한다. 제품 CLI는 커밋을 실행하지 않고 준비된 변경이 네 안전조건을 모두 만족하는지만 판단한다.

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
- 이 복구 원본은 P11의 파일 hard 한도만 판정하고 함수 hard 100 LOC는 판정하지 않는다. 사용자 복구 계약의 함수 100/101 경계는 현재 네 파일 원본 계약을 몰래 확장하지 않고 별도 RED→GREEN Work Unit에서 고정한다.
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

- 제품 CLI의 커밋 실행·자동 커밋, 장부 갱신, 훅·CI 배선. 복구용 RED/GREEN checkpoint commit은 제품 동작과 분리한다.
- `ledger.mjs` import 또는 병렬 A 소스 의존.
- `docs/sot/INDEX.md` 및 다른 정본 변경.
- 기존 pre-commit의 비밀 외 검사 재구현.

## 2026-08-25 복구 RED→GREEN 증거

```text
RED_HEAD: 11593107fefcffb1b77d4d76370dd1e6a1452a5e
RED_COMMAND: node --test tests/checkpoint-gate.test.mjs
RED_RESULT: exit 1 / tests 45 / pass 0 / fail 45
RED_OUTPUT_SHA256: 9e5850bc59f6038c7d088d6b857142fb93ee027ac9e48be589964603a93058da

GREEN_CANDIDATE_BASE: 11593107fefcffb1b77d4d76370dd1e6a1452a5e
GREEN_COMMAND: node --check tools/strict/checkpoint-gate.mjs
GREEN_GATE_CHECK_EXIT: 0
GREEN_COMMAND: node --check tools/strict/checkpoint-js-scan.mjs
GREEN_SCANNER_CHECK_EXIT: 0
GREEN_COMMAND: node --test tests/checkpoint-gate.test.mjs
GREEN_RESULT: exit 0 / tests 45 / pass 45 / fail 0
GREEN_OUTPUT_SHA256: 05eecd7e2a3aa11ca5195c1d59c2032c6c9403506a6bd2c16205096176a47983
```

→ RED와 GREEN은 같은 600줄 테스트와 같은 테스트 SHA-256 `72b9d42b521c04d242740d33683bbb11f2a2c2e10f302c10dec1d4652c589267`을 사용했다. GREEN 구현은 rescue·post-writer snapshot·대상 worktree에서 각각 readback한 exact bytes다.

세 실행 산출물의 복원 hash:

```text
e93da3cf4a4623c8b1da0f8adafd3f7d166b7133a351c9fb286042c73da07ca9  tools/strict/checkpoint-gate.mjs
01c0f9603f67c292464c6c8d814b4d9d6f9fb9820c58aa3842d19c07c02c4c43  tools/strict/checkpoint-js-scan.mjs
72b9d42b521c04d242740d33683bbb11f2a2c2e10f302c10dec1d4652c589267  tests/checkpoint-gate.test.mjs
```

goal을 포함한 네 파일의 최종 commit hash readback과 G/V1/V2 원문은 자기참조로 commit SHA를 바꾸지 않도록 외부 복구 evidence manifest와 control worktree에 귀속한다.

## 현재 T 판정

`RED_CONFIRMED`, `PRECOMMIT_GREEN`; exact GREEN commit의 G, V1, V2, T는 `NOT_RUN`이다. P11 함수 hard 100의 100/101 경계는 별도 Work Unit 전까지 `BLOCKED`이며 이 복구 commit을 전체 T PASS로 보고하지 않는다. 과거 `3094eef`·45/45·검증자 문구는 모두 제거했으며 자동 훅 배선·장부 갱신은 WU-3b 범위다.
