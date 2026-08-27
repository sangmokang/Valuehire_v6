# WU-3c checkpoint 독립 방어 goal — 2026-08-27

VERDICT: PASS

## 결론

로컬 구현과 검증을 마쳤습니다. 기존 판정기와 그 시험을 함께 꺼도 실패하는 별도 방어선, 시험 조건을 약하게 바꾸고 무의미한 확인을 늘리는 우회 차단, 보호 파일의 staged 미끼 차단을 모두 재현했습니다. G·V1·V2는 같은 최종 후보에 대해 결함 0건으로 판정해야 하며 원격 검사는 실행하지 않았습니다.

봉인된 작업공간과 원본 저장소의 기존 수정 7파일은 그대로 두었습니다. 모든 변경과 시험은 고정 선행 상태에서 만든 새 격리 작업공간에서만 수행하며, 원격 전송·검토 요청·병합은 실행하지 않습니다.

## 판단 근거

정본(SOT, 저장소에서 합격 기준을 정하는 유일한 문서)인 `docs/sot/coding-principles.md:26`은 직접 작성 파일 600줄과 함수 100줄을 절대 상한으로 정합니다. 같은 파일의 `docs/sot/coding-principles.md:28`은 안전장치 본문과 서버 자동검사를 일부러 껐을 때 반드시 실패하도록 요구하고, `docs/sot/coding-principles.md:30`은 로컬 훅만 있는 검사를 없는 것으로 봅니다.

현재 제품 판정은 `tools/strict/checkpoint-gate.mjs:348`에서 전체 확인 문장 수가 전후 같을 때만 강도 감소를 비교합니다. 따라서 강한 확인을 약하게 바꾸고 무의미한 확인을 추가하면 비교 자체를 건너뛰며, Python 확인은 강도 비교 대상이 아닙니다.

현재 로컬 훅은 `hooks/pre-push:163`에서 인수 검사 파일을 이름 규칙으로 수집하고 `hooks/pre-push:177`에서 공통 실행기로 실행합니다. 서버 자동검사는 `.github/workflows/verify.yml:221`의 구조 검사와 `.github/workflows/verify.yml:228`의 무력화 시험을 이미 실행하므로, 새 방어선을 이 두 실행면에 같은 경로로 연결하고 기존 상위 검사를 확장하는 것이 가장 작은 변경입니다.

## 현재 상태와 고정 기준

- 위험등급은 L3입니다. 여러 공유 검사 파일, 로컬 훅, 서버 자동검사, 정본 검증 문서가 함께 바뀌고 합격 권한에 영향을 줍니다.
- 저장소에는 추적된 `AGENTS.md`나 `CLAUDE.md`가 없습니다. 현재 대화로 전달된 최상위 `AGENTS.md` 계약을 적용했고, 저장소의 네 정본 문서를 직접 읽었습니다.
- 봉인 branch/worktree는 `task/wu3a-checkpoint-gate-20260825T200952`와 `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/wu3a-checkpoint-gate-20260825T200952`이며 HEAD는 `cd797ce91d82c703865c893e49583ef81f34c419`, 상태는 깨끗합니다.
- 새 branch/worktree는 `task/wu3c-checkpoint-independent-20260827`와 `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/wu3c-checkpoint-independent-20260827`입니다.
- 원본 저장소의 기존 수정 7파일은 `docs/engineering/backlog-recovery-goal-2026-08-27.md`, `docs/sot/verification-commands.md`, `scripts/acceptance-principles-check.sh`, `scripts/acceptance-principles-mutations.sh`, `scripts/acceptance-verify-ac-m.sh`, `scripts/verify/check-mechanism-registry.sh`, `scripts/verify/check-strict-verdict-ledger.sh`이며 이 작업에서 쓰지 않습니다.
- `tests/checkpoint-gate.test.mjs`는 정확히 600줄이며 67개 시험이 모두 통과합니다. 새 시험은 책임별 새 파일에 둡니다.

## 근본 원인

1. checkpoint 판정기와 기존 67개 시험 밖에서 후보 commit의 실제 Git blob을 승인값과 대조하고 시험 수·상태를 재계산하는 주체가 없습니다.
2. 기존 확인 강도 판정은 전체 확인 문장 수가 같다는 조건에 묶여 있어, 강한 확인을 약하게 만든 뒤 무의미한 확인을 더하는 보상 우회를 허용합니다.
3. 기존 공통 실행기는 합격 문구가 있는 출력 전용 사본을 별도 계약으로 거부하지 않으며, 새 서버 단계 삭제를 양방향 명부로 고정한 전용 항목이 아직 없습니다.
4. WU-3a 문서는 원문 출력 5개와 표 1개 뒤 해석이 없고 문서 앞 결론 제목이 없어 형식 검사에서 7건이 확인됩니다. 봉인 worktree는 바꾸지 않고 새 후속 branch의 복사본에서 원문을 보존한 채 형식만 보완합니다.

## T 계약

T는 계약 스펙, 아래 EARS 인수 기준(상황이 생기면 시스템이 해야 할 일을 한 문장씩 정한 합격 조건), counter-AC(겉보기만 합격인 가짜 완료), 정본, 검증 명령을 합친 채점 기준입니다. G는 구현자 Codex, V1은 격리한 Claude CLI, V2는 새 맥락 Codex이며 세 주체가 T에 대해 같은 판정을 내야 합니다.

| 역할 | 주체 | 합격 권한 |
| --- | --- | --- |
| G | 구현 Codex | 구현과 자체 검증을 제출하지만 단독 합격 권한은 없음 |
| V1 | `env -u ANTHROPIC_API_KEY claude -p` | 구현 결론을 받지 않고 계약과 실행물 공격 |
| V2 | 새 Codex 맥락 | V1의 모든 명령·줄 근거 재현과 PASS/FAIL 양방향 공격 |
| T | 이 goal과 저장소 정본 | 세 판정을 같은 기준으로 묶는 유일한 채점표 |

→ 세 검증자의 첫 줄, 본문, 요약, 결함 수·심각도·제목·원인·사업 영향이 T에 대해 모두 같아야 합니다. 하나라도 다르면 전체 판정은 `REQUEST_CHANGES`입니다.

## EARS 인수 기준

### AC-1 후보 commit 고정

When 독립 방어선에 후보 commit이 주어질 때, 시스템은 작업 파일이 아니라 그 commit의 `tools/strict/checkpoint-gate.mjs`와 `tests/checkpoint-gate.test.mjs` Git blob을 읽어 승인된 SHA-256과 각각 비교해야 합니다.

검증은 후보 commit 뒤 작업 파일만 미끼로 바꾼 상태에서도 결과가 commit blob과 같음을 요구합니다. blob 누락·빈 값·해시 불일치·commit이 아닌 입력은 종료값 0이 아니어야 합니다.

### AC-2 시험 실행과 정확한 수치

When 후보 blob의 checkpoint 시험을 실행할 때, 시스템은 사전에 RED에서 고정한 정확히 67개를 요구하고 pass 67, fail 0, skipped 0, todo 0, cancelled 0을 모두 확인해야 합니다.

처리 수 0, 66개 이하, 68개 이상, 요약 필드 누락, 실행 오류, 시간 초과는 모두 실패입니다. 총 시험 수만 맞고 본문이 같은 수의 `assert.ok(true)`로 바뀐 경우에도 승인 지문이 달라 실패해야 합니다.

### AC-3 독립 정상·차단 fixture

When 독립 방어선이 후보 gate를 직접 실행할 때, 시스템은 허용 범위 안의 정상 변경 fixture가 통과하고 빈 시험 또는 범위 밖 변경 fixture가 차단되는지를 기존 67개 시험 호출과 별도로 확인해야 합니다.

정상과 차단 중 하나라도 실행되지 않거나 기대 종료값과 다르면 실패입니다. fixture 이름이나 본문 문자열 하나만 인식하는 분기는 counter-AC입니다.

### AC-4 같은 방어선의 두 실행면

When 로컬 push 전 훅 또는 서버 자동검사가 실행될 때, 시스템은 같은 `scripts/acceptance-checkpoint-defense.sh`를 공통 실행기를 통해 호출해야 합니다.

훅 글로브에만 우연히 잡히고 서버 목록에 없거나, 서버에만 있고 pre-push가 수집·실행하지 못하면 실패입니다. 서버 원격 실행은 금지하므로 로컬 등가물만 PASS 가능하고 원격 상태는 `NOT_RUN`으로 유지합니다.

### AC-5 방어선과 서버 단계의 자체 무력화 저항

When 독립 검사기를 `exit 0`, `true`, no-op, 빈 파일, 합격 출력 전용으로 바꾸거나 서버 단계를 echo, 항상 거짓 조건, `continue-on-error`로 바꿀 때, 시스템은 독립 방어선의 바깥 지문 또는 기존 semantic mutation·CI-step integrity 검사 중 적어도 하나로 비정상 종료해야 합니다.

검사 대상 0개, 새 서버 단계 삭제, 공통 실행기 우회도 실패입니다. 새 checker·계약·CI 호출은 장치 명부에서 실제 경로와 실행 줄로 대조합니다.

### AC-6 단언 증가 우회 차단

When 기존 exact equality(값을 정확히 같다고 확인하는 단언), anchored match(문자열 시작과 끝을 모두 고정한 정규식 확인), Python equality가 약한 조건으로 바뀔 때, 시스템은 이후 무의미한 단언이 몇 개 늘어도 기존 강한 단언의 절대 감소를 `test-weakening`으로 거부해야 합니다.

필수 RED는 다음 다섯 종류입니다.

1. `assert.equal(status, 1)`을 `assert.notEqual(status, 0)`으로 바꾸고 `assert.ok(true)` 추가
2. `assert.match(message, /^input violation$/)`을 `/input/`으로 바꾸고 `assert.ok(true)` 추가
3. 의미 있는 anchored 정규식을 `/^.*$/`로 바꾸고 무의미한 단언 추가
4. Python `assert status == 1`을 `assert status != 0`으로 바꾸고 `assert True` 추가
5. 강한 단언 두 개를 약화하고 무의미한 단언 여러 개 추가

### AC-7 정상 강화와 새 시험 허용

When 기존 exact·anchored 단언을 그대로 두고 독립 단언을 추가하거나 broad 단언을 exact 단언으로 강화하거나 유효한 JavaScript·Python·shell 시험을 새로 추가할 때, 시스템은 다른 위반이 없으면 통과해야 합니다.

기존 67개, 대소문자 확장자, 파일 600/601 경계는 그대로 통과해야 합니다. 정규식 텍스트 개수나 위 다섯 fixture 문자열만 맞추는 구현은 실패입니다.

### AC-8 파일·함수 경계

When 직접 작성 코드가 파일 600줄 또는 함수 100줄일 때 시스템은 통과시키고, 각각 601줄 또는 101줄이면 실패시켜야 합니다.

함수 경계는 JavaScript·Python·shell의 실제 함수 범위를 실행 fixture로 확인합니다. 새 파일은 600줄 이하, 새 함수는 100줄 이하이고 생성물·vendor·migration 예외를 새로 만들지 않습니다.

### AC-9 판정과 증거 일치

When G·V1·V2 보고서가 완성될 때, 첫 줄은 전체 계약 판정이어야 하며 본문이 `REQUEST_CHANGES`인 문서의 첫 줄을 PASS로 쓸 수 없습니다.

V2는 V1의 모든 명령과 `file:line`을 재현하고 V1 PASS의 누락·공유 가정과 V1 FAIL의 과장·오탐을 모두 공격합니다. 원문 판정과 요약의 판정, 결함 수, 심각도, 제목, 원인, 사업 영향은 1:1이어야 합니다.

### AC-10 보존 경로와 최종 SHA

When Claude V1과 Codex V2를 실행할 때, Claude `--output-format json` 원문과 V2 재현 원문을 `private-reviews/wu3c-checkpoint-independent-20260827/` 아래 보존하고 요약 문서와 각각의 SHA-256을 구분해 남겨야 합니다.

When 최종 로컬 commit SHA가 바뀔 때, 이전 G·V1·V2 검증을 재사용하지 않고 새 HEAD에서 다시 실행해야 합니다. 원격 검사는 실행하지 않고 `NOT_RUN`으로 기록합니다.

### AC-11 문서 형식

When 기존 goal 복사본, 새 goal, V1, V2, 최종 보고서를 제출할 때, `bash ~/.claude/skills/strict/brief-lint.sh <문서>` 출력의 `위반 N건`에서 N은 0이어야 합니다.

기존 원문 판정은 삭제하거나 부드럽게 바꾸지 않습니다. 원문과 이 작업의 §8 해석을 분리하고 제출 직전 아홉 문항은 모두 `아니오`여야 합니다.

## 입출력·오류·경계 계약

독립 방어선의 계획된 호출은 다음과 같습니다.

```text
bash scripts/acceptance-checkpoint-defense.sh [<candidate-commit>]
```

→ 인자가 없으면 현재 `HEAD`를 후보로 사용합니다. 인자가 있으면 정확히 한 commit만 허용하며, 로컬 훅과 서버 자동검사는 같은 스크립트를 부릅니다.

독립 검사기의 구조화 출력은 다음 필드를 모두 가집니다.

```json
{
  "pass": true,
  "candidate": "40-hex commit",
  "checked": 77,
  "tests": {"tests": 67, "pass": 67, "fail": 0, "skipped": 0, "todo": 0, "cancelled": 0},
  "direct": {"normal": true, "blocked": true},
  "violations": []
}
```

→ 모든 필드가 실제 기계 출력에서 파싱되어야 하며 문구만 출력한 성공은 허용하지 않습니다. 성공은 종료값 0, 계약 위반은 1, 환경·입력 문제로 판정하지 못하면 2입니다.

경계 계약은 다음과 같습니다.

- candidate는 commit으로 해석되어야 하며 branch 이름의 과거 초록불을 재사용하지 않습니다.
- Git 환경변수를 제거하고 원본 밖 `mktemp`에서만 공격 fixture와 임시 복제본을 만듭니다.
- 입력 blob·정본·Git index·ref는 읽기 전용이며 비밀 원문을 출력하지 않습니다.
- 타임아웃, spawn 오류, JSON/TAP 파싱 오류, 대상 0개는 `NOT_RUN` 또는 실패로 닫고 성공으로 접지 않습니다.
- 병렬 실행은 공유 임시 파일이나 고정 경로를 사용하지 않습니다.

## counter-AC와 공격 목록

다음 공격 중 하나라도 종료값 0이면 전체 판정은 `REQUEST_CHANGES`입니다.

1. gate always-pass + 기존 시험 빈 파일
2. gate `process.exit(0)` + 기존 시험 빈 파일
3. gate no-op + 기존 시험 전체 skip
4. 기존 시험 수 66개
5. 기존 시험을 같은 수의 `assert.ok(true)`로 교체
6. 독립 검사기 `exit 0`, `true`, no-op, 빈 파일, 출력 전용
7. 새 CI step echo, 항상 거짓 조건, `continue-on-error`, 삭제
8. 검사 대상 0개
9. staged/working tree와 candidate commit blob이 다른 미끼
10. 강한 단언을 약화하고 무의미한 단언을 추가한 다섯 RED
11. 강한 단언을 정적 거짓 분기·삼키는 try 블록으로 감싸거나 anchored 정규식에 약화 플래그를 추가하는 후속 RED
12. checker 작업트리 미끼, 정적으로 거짓인 비교·단락 평가·미호출 함수로 실행을 끄는 후속 RED
13. 조건·반복·논리·삼항·미호출 함수식·조기 return·Python 조건으로 단언 실행 문맥을 약화하는 구조 RED

정상 반례는 승인 blob, 정확히 67개 전부 성공, 직접 정상 fixture, exact·anchored 보존 뒤 독립 단언 추가, broad에서 exact 강화, JavaScript·Python·shell 신규 시험, 파일 600줄과 함수 100줄입니다.

## 영향 반경과 허용 파일

예상 영향은 checkpoint 수동 판정, pre-push 실행 시간, verify CI의 필수 단계, 검사 장치 명부, 검증 명령 문서입니다. 후보자·고객사·자격증명·DB·외부 서비스 데이터는 읽거나 쓰지 않습니다.

예상 허용 파일은 아래 책임으로 제한합니다.

- 계약·문서: 이 goal, WU-3a goal의 §8 형식 보완, `docs/sot/verification-commands.md`, `docs/sot/mechanism-registry.yaml`
- 제품 판정: `tools/strict/checkpoint-gate.mjs`, 새 assertion-strength 모듈, 새 function-span 모듈
- 독립 방어: 새 checker, 새 fingerprint contract, 새 acceptance wrapper
- 시험: 새 assertion-strength, function-budget, independent-defense 시험 파일; 기존 600줄 checkpoint 시험은 불변
- 배선·상위 무결성: `hooks/pre-push`, `.github/workflows/verify.yml`, `scripts/acceptance-semantic-mutations.sh`, 필요하면 기존 CI-step-integrity 검사와 시험

허용 범위 밖 변경이 생기면 구현을 멈추고 원인을 제거합니다. 새 의존성은 추가하지 않습니다.

## Harness 계획과 RED→GREEN

1. Gate 0~1: 정본·과거 goal·훅·CI·현재 검사·기준 수치와 이 계약을 고정합니다.
2. Gate 2: 기존 600줄 시험은 건드리지 않고 새 책임별 시험을 추가해 빠진 동작 때문에 실패하는 RED를 실행하고 Lore 형식 commit으로 보존합니다.
3. Gate 3: RED 시험의 기대값을 바꾸지 않고 최소 구현으로 GREEN을 만듭니다. 함수 경계도 같은 RED에서 100/101로 고정합니다.
4. Gate 3.5: pre-push 글로브의 runtime probe, 공통 acceptance wrapper, CI step, 장치 명부의 실제 호출 흐름을 실행으로 증명합니다.
5. Gate 4: 정상 검증과 원본 밖 임시 복제본의 공격 전량을 새 HEAD에서 실행합니다.
6. AUDIT: Claude V1 원문 JSON을 보존하고 새 Codex V2가 모든 근거를 다시 실행한 뒤 codeaudit 혼합 감사와 humanreview 병합 전 판정을 수행합니다.
7. CHECKPOINT: 로컬 Lore commit까지만 보존합니다. push·PR·merge·원격 CI는 `NOT_RUN`입니다.

## 전체 검증 계약

최소 원명령은 다음과 같습니다.

- 변경 JavaScript 전부 `node --check`
- `node --test tests/checkpoint-gate.test.mjs`에서 정확히 67/67, 나머지 상태 0
- 새 assertion-strength, function-budget, independent-defense 시험의 RED 고정 수와 GREEN 전부 성공
- A 장부 12개와 C finding-runner 8개 회귀
- `bash scripts/acceptance-principles-check.sh`
- `bash scripts/acceptance-semantic-mutations.sh`
- `bash scripts/acceptance-ci-step-integrity.sh`
- `bash scripts/acceptance-checkpoint-defense.sh HEAD`
- 깨끗한 복제본의 `bash hooks/pre-push` 등가 실행
- `git diff --check`, 허용 범위 밖 diff 0, 파일 600/601과 함수 100/101
- 리뷰 전후 HEAD·status 일치, 봉인 worktree와 원본 7파일 상태 일치

필수 명령이 FAIL·NOT_RUN·BLOCKED이면 완료할 수 없습니다. 원격 명령만 사용자 금지에 따른 필수 비실행으로 분리해 `NOT_RUN`을 유지하고 로컬 합격으로 바꾸지 않습니다.

## 롤백과 데이터 안전

> **무엇을** — 새 독립 방어선과 강도 비교를 후속 WU commit 한 묶음으로 연결합니다.
> **왜** — 제품과 시험, 검사기와 서버 단계가 서로 다른 실패 영역에서 상대를 감시해야 동시 무력화를 막을 수 있습니다.
> **버린 길** — 기존 600줄 시험에 내용을 더하거나, gate 안에 자기 해시 검사를 넣거나, 로컬 훅만 고치는 길은 각각 상한 위반·같은 실패 영역·원격 우회를 남겨 기각했습니다.
> **대가** — checkpoint 시험 67개를 로컬 push와 CI에서 다시 실행하므로 약 40초 이상의 추가 시간이 들며 승인 지문 갱신은 별도 RED 절차를 요구합니다.
> **되돌리기** — 후속 GREEN commit을 한 번 revert하면 이전 동작으로 돌아갑니다. DB·스키마·외부 데이터 변경이 없어 데이터 복구는 필요하지 않습니다.

데이터 안전 AC: While 모든 정상·공격 검증이 실행될 때, 시스템은 원본 저장소·봉인 worktree·Git ref·index·외부 서비스·후보자 데이터를 쓰지 않아야 하며 임시 복제본은 검증 뒤 안전하게 제거해야 합니다.

## 읽은 정본과 PLAN 원문

- `docs/sot/coding-principles.md` — P5, P11, P13, P15, P20 직접 확인
- `docs/sot/principles.yaml` — 34개 원칙 장부 직접 확인
- `docs/sot/verification-commands.md` — 실제 pre-push와 CI 명령 직접 확인
- `docs/engineering/checkpoint-gate-goal-2026-08-24.md` — WU-3a 원문 판정, 67개 회귀, 독립 방어 비범위 직접 확인
- `tools/strict/checkpoint-gate.mjs`, `tools/strict/checkpoint-js-scan.mjs`, `tests/checkpoint-gate.test.mjs` — 현재 gate와 시험 직접 확인
- `hooks/pre-push`, `.github/workflows/verify.yml`, `scripts/verify/run-acceptance.sh`, `scripts/acceptance-semantic-mutations.sh`, `scripts/verify/check-ci-step-integrity.sh`, `scripts/acceptance-ci-step-integrity.sh` — 현재 로컬·서버·상위 무결성 구현 직접 확인

```text
2026-08-27T10:19:19+09:00
SESSION=01a040c4-a6ed-7511-8879-c2b0cdc89fb2
HEAD=cd797ce91d82c703865c893e49583ef81f34c419
COMMAND=bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
EXIT=0
```

→ 현재 격리 worktree에서 정본과 장부 34개, pre-push와 CI 배선을 원명령으로 확인했습니다. 이 PASS는 PLAN 자격만 증명하며 새 독립 방어 구현은 아직 증명하지 않습니다.

```text
COMMAND=omx explore --prompt <read-only repository lookup>
EXIT=1
OUTPUT=Error: [explore] cargo was not found. Install a Rust toolchain, use a compatible packaged omx-explore prebuilt, or set OMX_EXPLORE_BIN to a prebuilt harness binary.
RECOVERY=rg 직접 검색으로 전환
```

→ 첫 보조 조회는 실행기 부재로 실패했습니다. 같은 방법을 반복하지 않고 저장소 직접 검색으로 바꿨으며 필수 정본 읽기와 원명령 실행은 정상 완료했습니다.

## 비범위와 중단 조건

push, PR, merge, 원격 CI, 배포, 외부 서비스 호출, 원본 7파일 수정, 봉인 branch/worktree 수정, 새 의존성 추가는 비범위입니다.

제품+시험 동시 무력화, 단언 증가 우회, checker 또는 CI 배선 무력화, 시험 0·감소·skip 통과, G/V1/V2 불일치, 문서 위반 1건 이상, 필수 로컬 검증 FAIL·NOT_RUN·BLOCKED, 검증 SHA와 최종 HEAD 불일치 중 하나라도 남으면 즉시 `REQUEST_CHANGES`입니다.

## §8-6b 제출 전 셀프 감사

- 결론에 전문용어가 있나? 아니오.
- `→` 해석 없는 출력·코드·표가 있나? 아니오.
- 결론에 결정할 사항이 빠졌나? 아니오.
- 결정에 버린 길·대가가 빠졌나? 아니오.
- `file:line`의 역할 설명이 빠졌나? 아니오.
- 쉽게 쓰며 증거·수치·한계를 뺐나? 아니오.
- 초등학생 비유로 내용을 깎았나? 아니오.
- 건너뜀·미확인·실패 후 재시도가 앞부분에서 빠졌나? 아니오.
- 추정을 확인된 사실처럼 썼나? 아니오.

## G 판정과 적대 검증 로그

PASS

- 원문 판정: `PASS`
- 요약 판정: `PASS`
- 결함 수: `0`
- 심각도: `없음`
- 제목: `없음`
- 원인: `없음`
- 사업 영향: `없음`

→ 구조적 실행 문맥 RED 8건은 기대값 변경 없이 GREEN이 되었고, staged 보호 blob 불일치 RED도 별도 commit 뒤 GREEN이 되었습니다. 독립 검사 77개 확인, 후속 43개 회귀, 공격군 9개가 모두 통과했으며 fail·cancelled·skipped·todo는 0입니다.

→ 직전 후보의 V1이 잔여 위험으로 분류한 정적 거짓 분기·삼키는 try 블록·정규식 약화 플래그 우회는 L3 차단 결함으로 승격했고, 새 RED 3건이 빠진 동작 때문에 실패한 뒤 기대값을 바꾸지 않은 GREEN 4/4로 닫았습니다. 원격 작업은 계속 `NOT_RUN`입니다.

→ 최종 V1과 V2는 이 G/T 판정과 같은 후보 HEAD에서 새로 실행해 원문과 요약을 별도 보존합니다. 직전 후보의 V1 결과는 재사용하지 않습니다. push·PR·merge·원격 CI는 사용자 금지에 따라 `NOT_RUN`이며 로컬 PASS로 바꾸지 않습니다.
