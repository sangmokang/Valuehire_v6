# WU-3a checkpoint 판정기 goal — 2026-08-24

## 결론

기존 합격 판단은 감사에서 뒤집혔다. 현재 변경의 계산과 고장 주입 시험은 통과했지만, 서로 다른 두 검증자가 새 사본에 동의하기 전까지 완료로 보지 않는다. 이 작업에서는 커밋하지 않는다.

현재 범위는 새 검사기·시험·기록 문서뿐이며 저장소 규칙·장부·훅·커밋은 건드리지 않는다.

이 단계는 검사 도구가 정상이라는 전제 아래 준비된 내용만 판단한다. 같은 작업 공간의 도구가 자기 자신을 완전히 믿을 수 있다고 주장하지 않으며, 도구가 바뀌지 않았다는 독립 보증은 다음 작업에서 연결해야 한다. 따라서 지금은 판단 계산만 검증 중이고 실제 커밋 준비 확인은 아직 실행하지 않은 상태로 분리한다.

## 판단 근거

- 정본인 `docs/sot/coding-principles.md:26`의 P11은 직접 작성 코드 파일을 soft 300 / hard 600줄로 정한다. 판정기는 숫자 600을 복사하지 않고 매 실행마다 이 문장에서 hard 값을 읽으며, 조항이 없을 때만 500을 쓴다.
- 현재 직접 작성 코드 줄수는 gate 510, scanner 572, 기존+대문자 회귀 tests 600, mutation tests 183으로 모두 P11 hard 600 이하이다.
- 기존 훅인 `hooks/pre-commit:56`은 비밀 판정을 `verify.sh` 한 벌에 위임하고, `hooks/pre-commit:73`의 정확한 호출은 `SECRET_PATTERNS_FILE= VERIFY_SCAN_SOURCE=index bash verify.sh`다. 새 판정기는 이 호출을 그대로 재사용하고, 파일이 없을 때만 보수적 내장 패턴으로 스테이지 blob을 검사한다. 이 호출은 변경 파일만이 아니라 Git index 전체를 스캔하는 pre-commit 계약이므로, 기준 커밋부터 있던 비밀도 무관한 staged 변경에서 `secrets/file=""`로 차단한다. 이를 staged-only 검사라고 부르지 않는다.
- 병렬 A 장부는 착수 시 없었으나 구현 중 `task/wu1-strict-ledger-20260824`에 `.strict/run-ledger/<run_id>.json` 파일 인터페이스가 생성됐다. 현재 고정 `wus` 스키마는 `id/ac/status/commit`만 있고 파일 범위 필드는 아직 없으므로, 범위 선언이 없는 현재 장부는 사용자가 반복 지정한 `--scope <glob>`를 파일 범위 계약으로 삼는다. 향후 장부 WU가 `scope/scopes/files/paths`를 제공하면 그 파일 선언을 우선하며, `ledger.mjs`는 import하지 않는다.
- 기준 커밋과 스테이지를 비교해야 작업트리 덮어쓰기나 삭제를 놓치지 않는다. staged 코드·테스트와 P11 정본은 Git index blob을 읽는다. 기존 `verify.sh`가 읽는 비밀 패턴 파일은 아직 worktree 입력이므로 WU-3b가 승인 해시/읽기 전용 산출물과 HEAD/index/worktree 일치를 함께 보호해야 한다.

### 결정 카드

> **무엇을** — 네 검사를 한 CLI에서 독립 실행하고 위반 목록의 합집합으로 전체 AND 판정을 계산한다.
> **왜** — 한 검사 실패가 뒤 검사를 생략하면 사용자가 한 번에 전체 수리 범위를 알 수 없고, 부분 합격을 전체 합격으로 오인할 수 있다.
> **버린 길** — `hooks/pre-commit` 전체 호출은 비밀 검사 외 정책까지 섞여 검사별 독립 판정과 JSON 계약을 깨므로 기각했다. `ledger.mjs` import도 병렬 A 구현에 런타임 결합되므로 기각했다.
> **대가** — 장부 스키마 오류나 기존 비밀 스캐너 실행 오류도 안전하게 불합격 처리되어, 환경 결함이 있을 때 커밋 가능 판정이 보수적이다.
> **되돌리기** — 신규 goal·테스트·`tools/strict/checkpoint-gate.mjs`·`tools/strict/checkpoint-js-scan.mjs`를 삭제하면 원상복구된다. 기존 훅·정본·장부에는 변경이 없다.

### 신뢰 경계 결정 카드

> **무엇을** — WU-3a는 신뢰된 `verify.sh`·scanner·gate와 정책 입력을 전제로 index 내용을 계산하는 순수 판정기로 한정하고, 독립 mutation runner가 각 도구의 고장 사본을 차단하는지 별도로 검증한다.
> **왜** — 같은 작업트리의 gate가 자기 파일과 의존 파일의 진위를 자기 기준으로 증명하면 공격자가 기준과 실행물을 함께 바꿀 수 있어 순환 신뢰가 된다.
> **버린 길** — gate 안에 HEAD/index/worktree 해시 비교를 넣는 길은 신뢰 기준점까지 같은 변경 권한 아래 있어 완전한 자기 보호가 아니며, 이번 금지 범위인 훅·CI 배선 없이는 checkpoint 권한도 얻지 못하므로 기각했다.
> **대가** — WU-3a 로직이 통과해도 독립 기준점이 실행되기 전에는 checkpoint readiness가 `NOT_RUN`이고 실제 커밋 차단 권한이 없다.
> **되돌리기** — mutation 회귀 파일과 이 경계 기록을 삭제하면 기존 순수 판정기 상태로 돌아가지만 P13 무력화 저항 증거도 함께 사라진다.

## 위험등급과 영향 경계

- 위험등급: L3. 이유는 보안 검사 호출, 커밋 직전 공유 판정 도구, 3파일 이상 변경이다.
- 영향 반경: 수동으로 `node tools/strict/checkpoint-gate.mjs ...` 또는 독립 mutation 테스트를 실행한 프로세스의 stdout/stderr와 종료값뿐이다. 훅·CI·커밋에는 연결하지 않는다.
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
- 다만 스테이지 변경 0개의 PASS는 후보 패키지 검증 증거가 아니다. 후보 검증은 격리 저장소에서 후보 파일을 실제 stage하고 `CHECKED` 대상을 별도로 기록해야 한다.
- rename은 기존 경로와 새 경로를 함께 비교하되 테스트 파일 rename을 삭제로 오인하지 않는다.
- 테스트 파일 삭제는 assertion 수와 무관하게 반드시 불합격이다.
- JavaScript assertion 판정은 신뢰 모듈에서 온 binding의 직접 호출 수를 비교하는 정적 약화 지표다. 회귀에 고정한 비신뢰 import, 직접·구조분해·rest·파라미터 재바인딩, binding 인자 전달, 직접 메서드 덮어쓰기, 정적 전역 dot/computed write는 fail-closed한다. 임의 별칭, 동적 key, 대입 연산자 전 종류, TypeScript 의미, 분기 도달성·assertion 의미·테스트 실행 결과의 완전 탐지는 보장하지 않는다. P13의 이번 mutation 계약은 아래 다섯 도구 무력화가 독립 validator에서 차단되는지에 한정하며 이 정적 지표를 의미 분석기로 과장하지 않는다.
- 마지막 파일 확장자는 판정 전에 소문자로 정규화한다. `tests/unit.JS`와 `tests/unit.TSX`는 테스트 약화·크기 검사에 포함되며 위반 JSON의 파일명은 입력 대소문자를 보존한다. 중위 `.TEST.`나 `TEST_` 이름까지 대소문자 무시로 넓히는 것은 이번 T 계약 밖의 알려진 한계다.
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

### AC-2 — P13 독립 mutation 저항

When 독립 mutation 검증이 실행될 때, 시스템은 정상 `verify.sh`·scanner·gate 사본에서 종료값 0을 반환하고, `verify.sh → exit 0`, `scanner → always zero`, `gate → exit 0`, `gate → 고정 PASS`, `gate → 빈 출력` 사본 각각에서 종료값 1을 반환해야 한다.

검증 명령:

```text
node --test tests/checkpoint-gate-mutation.test.mjs
```
→ 상위 테스트는 임시 저장소의 독립 검증 명령이 정상 사본에서 0, 다섯 고장 사본에서 각각 1인지 실행해 검사한다.

기대값: 테스트 6 / 통과 6 / 실패 0. 내부 독립 명령은 정상 0, 고장 5종 각각 1.

counter-AC: gate 단독 PASS를 mutation 저항 증거로 사용하거나, mutation 사본을 실제 실행하지 않고 문자열 존재만 확인하거나, 고장 사본과 validator를 함께 약화해 종료값 0을 만들면 전체 WU는 FAIL이다.

### trusted-tooling precondition과 WU-3b 인수 기준

- WU-3a precondition: 실행되는 `verify.sh`, `checkpoint-js-scan.mjs`, `checkpoint-gate.mjs`, mutation validator와 이들이 읽는 P11 정본·기본/로컬 비밀 패턴의 내용이 독립 기준점이 승인한 해시와 일치해야 한다.
- WU-3b는 변경 대상과 다른 신뢰 영역에서 후보 해시를 고정하고, 그 해시의 mutation validator를 gate보다 먼저 실행하며, 정상 0·고장 5종 각 1·검사 대상 0개 아님을 확인한 뒤에만 gate 결과를 checkpoint 입력으로 받아야 한다.
- WU-3b는 도구뿐 아니라 P11 정본과 `.secret-patterns.default`·`.secret-patterns` 정책 입력도 worktree 파일 그대로 신뢰하지 않고 승인 SHA/index blob 또는 읽기 전용 배포 산출물에서 실행해야 하며, 이 전체 보호 집합의 HEAD/index/worktree 불일치·해시 불일치·runner 무출력은 fail-closed해야 한다.
- 이번 작업은 훅·CI·정본 배선 변경이 금지되어 이 precondition을 실제 checkpoint 경로에 연결하지 않는다. 그러므로 WU-3b 실행 전 readiness는 `NOT_RUN`이다.

## Harness 게이트 계획

1. Gate 0~1: 정본·장부·기존 훅·과거 브랜치를 읽고 이 계약을 고정한다.
2. Gate 2: 구현 파일이 없는 상태에서 테스트가 모듈 부재 때문에가 아니라 요구 동작 부재로 실패하도록 임시 최소 스텁을 사용하지 않고, 대상 CLI 부재 RED를 기록한다.
3. Gate 3: `checkpoint-gate.mjs`와 P11 한도 안에서 분리한 `checkpoint-js-scan.mjs`를 최소 구현한다. 테스트는 각 새 반례를 먼저 RED로 고정한 뒤 GREEN으로 만든다.
4. R2: skip/only/todo, assertion 삭제, 테스트 삭제, hard+1을 실제로 주입한다. 정상쌍과 `verify.sh`·scanner·gate 무력화 5종도 실행한다.
5. R4: 실제 진입점은 CLI 직접 호출이다. 훅 배선은 명시적 비범위다.
6. Gate 4: 목표 테스트, 구문 검사, 원칙 검사, 기존 비밀 검사, 파일 줄수, 허용 경로 diff를 실행한다.
7. V1: 구현 결론을 주지 않은 증거 묶음을 Claude CLI에 전달해 독립 공격한다.
8. V2: V1의 모든 재현 가능한 주장을 새 Codex 검증 맥락에서 다시 실행하고 누락·오탐을 양방향 공격한다.

## 읽은 정본과 착수 증거

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

→ 원칙 정본과 기계 장부가 모두 직접 로드됐고, 필수 pre-push·CI 배선도 실제 검사에서 통과했다. 착수 전제 ①은 hard 600 파싱으로, ②는 기존 `verify.sh` 호출 재사용 계약으로 충족한다.

### 2026-08-25 신뢰 경계 재착수 장부

```text
TIME: 2026-08-25T12:41:16Z
SESSION: strict-wu3a-20260825T124116Z-20586
HEAD: 3094eefa646b102074dfb6401777afe450223e6c
COMMAND: sed -n '1,240p' docs/sot/coding-principles.md
EXIT: 0
COMMAND: sed -n '1,280p' docs/sot/principles.yaml; sed -n '281,$p' docs/sot/principles.yaml
EXIT: 0
PRINCIPLES_YAML_LINES: 345
COMMAND: bash scripts/acceptance-principles-check.sh
EXIT: 0
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 현재 HEAD에서 원칙 정본 240줄과 기계 장부 345줄 전체를 직접 읽었고, 원칙 검사 종료값 0과 34/34 배선을 확인했다. 과거 기록을 현재 증거로 재사용하지 않았다.

### Finding 재분류

| Finding | 상태 | 현재 계약 |
|---|---|---|
| F1 `verify.sh → exit 0`에서 staged secret 통과 | REPRODUCED | gate 자기 보호가 아니라 독립 mutation runner가 고장 사본의 전체 검증을 종료값 1로 만든다. 실제 신뢰 배선은 WU-3b다. |
| F2 scanner always-zero에서 assertion 삭제 통과 | REPRODUCED | 독립 mutation runner가 고장 scanner 사본의 전체 검증을 종료값 1로 만든다. 실제 신뢰 배선은 WU-3b다. |
| F3 staged 0개 gate PASS | REPRODUCED | 순수 판정 결과로는 허용하지만 후보 검증 증거로 금지한다. 격리 저장소에서 후보를 실제 stage해 별도 실행한다. |
| F4 기존 base/index secret이 무관 변경을 `file=""`로 차단 | REPRODUCED | pre-commit 전체-index 재사용 계약의 의도된 보수적 차단이며 staged-only라고 주장하지 않는다. |
| F5 객체 구조분해 fixture 중복 | REPRODUCED | 두 번째 fixture를 실제 배열 공격 `[assert] = [noop]`로 교체했다. |

→ 다섯 Finding은 모두 독립 실행 또는 코드 fixture로 재현했다. F1/F2는 WU-3a 로직 내부 자기검증으로 과장하지 않고, 별도 runner의 차단 증거와 WU-3b 신뢰 기준점 책임으로 나눴다.

## RED→GREEN·mutation 원장

- 최초 대상 CLI 부재 상태에서 요구 동작 테스트가 실패한 뒤 구현을 시작했다.
- 감사에서 세미콜론 없는 assertion 다음의 무관한 구조분해 대입이 assertion 감소로 오인되는 정상 fixture를 `before.assertions=1 / after.assertions=0`으로 RED 재현했다. 구조분해 여는 괄호부터 대응하는 닫는 괄호까지를 확인하도록 범위를 제한해 `1 -> 1` GREEN으로 만들었다.
- 구조분해로 assertion을 no-op 객체에 재할당하는 공격 fixture는 계속 `assertions decreased 2 -> 0`으로 exit 1을 반환한다.
- 무관한 일반 객체 `const paging = { skip: 1 }`를 테스트 약화로 오인하는 V2 반례는 관련 단일 테스트에서 `expected 0 / actual 1`로 RED를 재현하고, 테스트 호출의 인라인 옵션 객체에서만 truthy `skip/only/todo` 키를 세도록 좁혀 GREEN으로 만들었다.
- 진짜 `assert` import를 로컬 no-op 객체로 가리는 V1 반례는 `expected violation exit 1 / actual 0`으로 RED를 재현하고, 비신뢰 `assert`/`expect` 재바인딩·메서드 덮어쓰기를 assertion으로 세지 않도록 고쳐 GREEN으로 만들었다.
- `({ assert } = ...)`와 `[assert] = [...]` 구조분해 재할당 V1 반례도 같은 방식으로 RED를 재현하고 구조분해 LHS 종료 뒤 `=`를 재바인딩으로 분류해 GREEN으로 만들었다.
- mutation: 인라인 테스트 옵션 문맥 가드를 제거하면 무관 `paging.skip` 정상 fixture가 RED가 됐고, assertion shadow 수집을 빈 집합으로 바꾸면 no-op shadow fixture가 RED가 됐다. 두 mutation은 즉시 원복했으며 원복 후 단일 테스트와 전체 스위트를 다시 통과했다.
- 2026-08-25 RED: `node --test tests/checkpoint-gate-mutation.test.mjs`는 파일 부재로 종료값 1이었다.
- GREEN: 별도 mutation runner를 추가한 뒤 정상 사본은 내부 검증 종료값 0, `verify-exit-zero`, `scanner-always-zero`, `gate-exit-zero`, `gate-fixed-pass`, `gate-empty`는 각각 종료값 1이었다. 상위 스위트는 테스트 6 / 통과 6 / 실패 0이다.
- 배열 공격 fixture `[assert] = [noop]`는 `test-weakening` 위반으로 gate 종료값 1을 유지하며, 객체 공격과 다른 실행 경로를 검사한다.
- 2026-08-25 V2 RED: 신뢰된 gate·scanner를 바꾸지 않고 테스트의 `assert` import만 로컬 no-op 모듈로 교체하자 assertion 수가 2→2로 잘못 유지되어 gate 종료값 0이었다. 로컬 assertion import를 비신뢰 shadow로 분류하고 같은 fixture를 회귀로 고정한 뒤 gate 종료값 1, 전체 gate 46/46으로 GREEN을 확인했다.
- 후속 V2 RED: 신뢰된 `node:assert/strict`를 default alias·namespace alias·named import로 사용하면 assertion 수가 2→0으로 오인되어 정상 변경을 exit 1로 막았다. 신뢰 모듈에서 유래한 로컬 import/require binding을 수집하도록 바꾸고 default·namespace·named import와 require·destructured require 정상쌍을 추가해 전체 gate 51/51 GREEN을 확인했다.
- 후속 Claude V1 RED: 신뢰 import를 유지한 채 no-op 객체를 `function run(assert)` 또는 `(assert) =>` 파라미터로 전달하면 assertion 수가 2→2로 잘못 유지되어 gate 종료값 0이었다. 함수·화살표·메서드·catch 파라미터의 assertion binding을 비신뢰 shadow로 분류하고 네 실행 fixture를 고정해 전체 gate 55/55 GREEN을 확인했다.
- 다음 Claude V1 RED: `Object.assign(assert, ...)`와 `Reflect.set(assert, ...)`로 메서드를 no-op으로 덮으면 assertion 수가 2→2로 유지되어 gate 종료값 0이었다. 신뢰 선언·직접 assertion 호출과 회귀로 승인한 정상 사용 외 binding 사용을 보수적으로 제외하도록 바꿔 두 실행 fixture와 전체 gate 57/57 GREEN을 확인했다. 이 규칙은 위 경계에 열거한 정적 징후를 보장하며 임의 JavaScript/TypeScript 의미의 완전 탐지를 주장하지 않는다.
- 후속 Claude V1 RED: rest가 `.` 세 개로 토큰화되어 `const {...assert}`가 property access로 오인됐고 gate 종료값 0이었다. `...` 토큰을 먼저 인식하고 object/array/rest-parameter binding과 `globalThis.expect` write를 비신뢰로 분류해 네 실행 fixture와 전체 gate 61/61 GREEN을 확인했다.
- 후속 Codex V2 RED: `globalThis["ex" + "pect"] = no-op` 정적 computed-key write가 단일 문자열 key 검사만 우회해 gate 종료값 0이었다. 기존 static-expression 계산 결과를 global binding write에도 재사용하고 실행 fixture를 고정해 전체 gate 62/62 GREEN을 확인했다.
- 2026-08-26 RED: `src/oversized.JS`·`.TSX` 601 LOC와 `tests/unit.JS`·`.TSX` assertion 2→1이 각각 gate 종료값 0이었다. 마지막 확장자를 공통 함수에서 소문자화하고 세 판정 함수가 먼저 호출하도록 바꾼 뒤 네 회귀와 대응 staged 정상 fixture를 추가해 전체 gate 66/66 GREEN으로 만들었다.
- 첫 대문자 후보 tree `1d5ae79b5838df285d7fc1480209c112e894724d`의 Claude V1과 새 Codex V2는 assertion 정상 fixture가 기준 내용 복원으로 staged 0이 되는 결함, P11을 worktree에서 읽는 정본 미끼, 오래된 goal 수치를 모두 재현해 WU-3a FAIL에 일치했다. 정상 fixture를 assertion 2→3의 실제 staged 변경으로 바꾸고 P11을 index blob에서 읽도록 수정했으므로 이 실패 판정은 수정 전 hash에만 유효하다.

## 비범위

- 커밋 실행, 자동 커밋, 장부 갱신, 훅·CI 배선, 독립 신뢰 기준점의 운영 배치.
- `ledger.mjs` import 또는 병렬 A 소스 의존.
- `docs/sot/INDEX.md` 및 다른 정본 변경.
- 기존 pre-commit의 비밀 외 검사 재구현.

## 적대 검증 로그

### G — 현재 로컬 증거

```text
TIME: 2026-08-25T13:35:53Z
HEAD: 3094eefa646b102074dfb6401777afe450223e6c
COMMAND: node --test tests/checkpoint-gate.test.mjs
EXIT: 0
RESULT: tests 62 / pass 62 / fail 0 / skipped 0 / todo 0

COMMAND: node --test tests/checkpoint-gate-mutation.test.mjs
EXIT: 0
RESULT: tests 6 / pass 6 / fail 0 / skipped 0 / todo 0
INTERNAL: original exit 0; verify-exit-zero, scanner-always-zero,
          gate-exit-zero, gate-fixed-pass, gate-empty each exit 1

COMMAND: node --check tools/strict/checkpoint-gate.mjs
EXIT: 0
COMMAND: node --check tools/strict/checkpoint-js-scan.mjs
EXIT: 0
```

→ 배열 공격, 로컬 no-op assertion import, 파라미터·rest shadow와 정적 computed global write, assertion binding 전달 공격, 신뢰 assertion alias 정상쌍을 포함한 gate 62개와 독립 mutation 6개가 모두 통과했다. 상위 mutation 테스트의 합격은 고장 사본 자체가 합격했다는 뜻이 아니라, 내부 독립 검증이 정상 사본만 0이고 고장 사본은 각각 1인 것을 확인했다는 뜻이다.

### 격리 저장소의 실제 staged 후보 증거

```text
TIME: 2026-08-25T12:52:43Z
ISOLATED_REPO: /tmp/wu3a-stage-audit-20260825-92037/repo
BASE: 3094eefa646b102074dfb6401777afe450223e6c
ORIGINAL_FOUR_STAGED_COUNT: 4
ORIGINAL_FOUR_GATE_OUTPUT: {"pass":true,"violations":[]}
ORIGINAL_FOUR_GATE_EXIT: 0
FULL_FIVE_STAGED_COUNT: 5
FULL_FIVE_GATE_OUTPUT: {"pass":true,"violations":[]}
FULL_FIVE_GATE_EXIT: 0
```

→ 원래 후보 4개를 실제 stage한 상태와 새 mutation 파일까지 포함한 5개 상태를 각각 검사했다. 둘 다 staged 파일 수가 0이 아니며 gate 종료값 0, 위반 0건이었다. 원본 저장소 index는 사용하지 않았고 임시 clone은 실행 뒤 삭제했다.

### V1 — 실제 Claude CLI (`NOT_RUN`)

아래 시도와 판정 이후 computed global binding 수정으로 후보 해시가 바뀌었으므로, 해당 V1과 뒤의 V2 기록은 현재 후보 판정으로 재사용하지 않는다.

```text
IDENTITY: /Users/kangsangmo/.local/bin/claude
VERSION: 2.1.241 (Claude Code)
ENVIRONMENT: env -u ANTHROPIC_API_KEY

ATTEMPT 1: exec session 89894, 원본 읽기 + 임시 저장소 실증 요청
RESULT: 3분 이상 message 0건, 중단 뒤 exit 130
OUTPUT: Error: No messages returned from query

ATTEMPT 2: claude-cli-2.1.241-wu3a-20260825T130308Z
SNAPSHOT: /tmp/wu3a-v1-20260825-62221/repo
STAGED_COUNT: 5
RESULT: 3분 이상 message 0건, 중단 뒤 exit 130
OUTPUT: Error: No messages returned from query

ATTEMPT 3: exec session 38685, 도구 없는 최소 OK 응답 확인
RESULT: 40초간 message 0건
OUTPUT: Error: No messages returned from query

ATTEMPT 4: exec session 54596, 최신 당시의 후보 5개를 stage한 격리 clone
RESULT: exit 0, Claude 검증 본문 수신, VERDICT FAIL
REPRODUCED: function/arrow parameter shadow에서 gate exit 0
DISPOSITION: RED 회귀 뒤 수정했으므로 이 판정은 수정 전 후보에만 유효

ATTEMPT 5: exec session 78566, 다음 후보 5개를 stage한 격리 clone
RESULT: exit 0, Claude 검증 본문 수신, VERDICT FAIL
REPRODUCED: Object.assign/Reflect.set assertion method overwrite에서 gate exit 0
DISPOSITION: RED 회귀 뒤 폐쇄 규칙으로 수정했으므로 이 판정은 수정 전 후보에만 유효

ATTEMPT 6: exec session 37434, 폐쇄 규칙 후보 5개를 stage한 격리 clone
RESULT: exit 0, Claude 검증 본문 수신, VERDICT FAIL
REPRODUCED: object rest assertion binding에서 gate exit 0
DISPOSITION: RED 회귀 뒤 rest 토큰과 전역 binding write를 수정했으므로 이 판정은 수정 전 후보에만 유효
```

→ 네 번째부터 여섯 번째 실제 Claude CLI 실행의 결함을 각각 원본에서 재현하고 수정했다. 수정으로 해시가 바뀌었으므로 현재 후보의 V1 상태는 다시 `NOT_RUN`이며 Codex 결과로 대체하지 않는다.

### V2 — 새 문맥 Codex verifier

검증자: `/root/wu3a_v2_fresh`. 대상 실행 묶음 SHA256 `57ae721df2f39049cc01c9b60740afd1e080c2007bd463f05b0e8b91409f1533`.

```text
INITIAL VERDICT: FAIL
NEW COUNTEREXAMPLE:
  mutation validator의 JSON parse·violation 기대·mutant 기대 exit를 함께 약화하면
  mutation suite tests 6 / pass 6 / fail 0
  checkpoint gate {"pass":true,"violations":[]} / exit 0

READ-ONLY EVIDENCE:
  HEAD 3094eefa646b102074dfb6401777afe450223e6c
  gate tests 45/45 / exit 0
  mutation tests 6/6 / exit 0
  original four staged count 4 / gate exit 0
  full five staged count 5 / gate exit 0
  original index staged count 0

REATTACK VERDICT: NOT_RUN
CORRECTION: initial FAIL은 범위 오분류였다.
WU-3a logic: PASS
checkpoint readiness: NOT_RUN
overall T: NOT_RUN
```

→ V2의 첫 공격은 validator와 판정 기대를 같은 권한으로 함께 바꾸면 초록이 된다는 사실을 재현했다. 그러나 T는 validator 자체의 승인 해시와 실행 배선을 WU-3b 독립 기준점 책임으로 이미 분리했다. V2는 자기 판정을 다시 공격해 이 반례를 WU-3a 로직 결함이 아니라 WU-3b가 필요한 이유로 재분류했다. 지정된 단일 mutation 5종은 원본 validator에서 모두 내부 종료값 1이고 정상 사본만 0임을 재확인했다.

## 최종 T 판정

이 goal을 후보 다섯 파일의 hash에 포함한 뒤 실행되는 최종 Claude V1·새 Codex V2 원문은 hash 순환을 피하려고 별도 증거 파일에 보존한다. 별도 증거가 이 절의 과거 상태보다 최신 판정이며, 두 검증자가 같은 후보 hash와 T에 일치하기 전에는 WU-3a 로직 PASS를 선언하지 않는다. WU-3b 독립 신뢰 기준점과 실제 checkpoint 배선은 이번 범위 밖이므로 checkpoint readiness와 overall T는 계속 `NOT_RUN`이다.
