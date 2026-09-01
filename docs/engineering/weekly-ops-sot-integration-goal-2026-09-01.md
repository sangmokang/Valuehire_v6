# Weekly Ops 요구사항 SOT 통합 목표 — 2026-09-01

## 결론

Weekly 업무 규칙을 다음 세션이 한 곳에서 찾을 수 있는 영구 정본으로 통합한다. 현재 Golden
v1은 문서 계약만 있고 실행 엔진이 없으므로, 정본 통합 뒤에도 실제 Golden 발행은 계속 막는다.

> **무엇을** — Weekly 전용 SOT, Skill 참조, legacy 상태, 자동 검사를 한 변경으로 묶는다.
> **왜** — 요구가 여러 파일에 흩어져 있고 현재 검사 설명도 실제 mutation 수와 갈라졌기 때문이다.
> **버린 길** — 기존 Golden v1 문서만 정본이라고 선언하는 방법은 실행되지 않는 계약을 완성품처럼 보이게 하므로 사용하지 않는다.
> **대가** — 문서뿐 아니라 Skill·계약·검사 배선도 함께 바뀌며, Golden v2 엔진 전까지 발행은 NOT_RUN이다.
> **되돌리기** — 새 SOT와 참조·검사 변경을 함께 revert하면 이전 탐색 구조로 돌아가며 운영 데이터에는 영향이 없다.

## 현재 상태와 근본 원인

- `docs/sot/INDEX.md`에는 Weekly 전용 SOT가 없다.
- `docs/sot/verification-commands.md`에는 Weekly 검사 한 줄만 있고 `mutation 25종`으로 적혀 있다.
- 2026-09-01 fresh 실행에서 Weekly 단위시험은 62건, mutation 호출은 26종,
  전체 acceptance는 `CHECKED: 50`이었다.
- `.agents/skills/weekly-ops/SKILL.md`는 Golden 요청에서 v1 reference와 JSON을 읽지만 Weekly
  업무 SOT는 읽지 않는다.
- `contracts/weekly-ops/notion-golden-sample-v1.json`은 hook 이름을 담고 있으나 실제 Golden
  callable 실행기와 연결되지 않는다.

근본 원인은 업무 불변조건, 기계 수식, 실행 상태, 검증 명령이 서로 다른 생명주기의 파일에
섞였는데 이를 연결하고 불일치를 차단하는 장치가 없다는 것이다.

## 위험등급과 범위

- 위험등급: Strict L3. SOT와 공용 Skill, 계약, CI 연결 인수 검사를 함께 변경한다.
- 쓰기 범위: 저장소 문서·Skill·legacy contract 상태·로컬 검사·테스트·로컬 checkpoint.
- 외부 쓰기: Notion, Gmail, ClickUp, admin web, 운영 DB, push, PR, merge 모두 금지.
- 비범위: Golden v2 계산 엔진, 실제 4주 데이터 수집, 실제 Notion 발행.

## T 계약

### AC-1 — 영구 Weekly 정본

When 다음 세션이 `docs/sot/INDEX.md`를 읽으면, 시스템은 `weekly-ops-contract.md`를 Weekly 업무
정본으로 발견하고 그 문서에서 요구·현재 구현 상태·비범위를 구분할 수 있어야 한다.

- counter-AC: 파일은 생겼지만 INDEX와 Skill 어디에서도 참조하지 않는다.

### AC-2 — 사용자 권한 경계

When Weekly 문서를 렌더링하면, 시스템은 최근 인입을 시간순 사실로 표시하고 P0/P1 또는
`즉시 실행`, `해야 한다` 같은 경영 명령을 만들지 않아야 한다.

- counter-AC: 시장 접근성 점수를 LLM이 경영진 우선순위로 번역한다.

### AC-3 — 4주와 집계 단위

When 4주 KPI를 정의하면, 시스템은 보고 주차와 직전 완료 주간을 분리하고 live client
positions, new tasks, reactivations, active/interview/pre-interview pipeline, 채널별 verified sends를
서로 다른 단위로 정의해야 한다.

- counter-AC: 현재 포지션 수를 과거 네 주에 복사하거나 재활성을 신규 Task로 센다.

### AC-4 — 실제 고객 포지션과 Scraped 경계

While 근거가 회사 채용 페이지뿐이면, 시스템은 포지션을 `SCRAPED_STAGING`으로 유지하고
고객 요청 근거 없이 `CLIENT_REQUESTED|CLIENT_SHARED`로 승격하지 않아야 한다.

- counter-AC: 회사 채용 페이지에 있다는 이유만으로 ClickUp 직무 상태에 활성 의뢰로 넣는다.

### AC-5 — Candidate Task identity

When 후보자 Task를 중복 제거하면, 시스템은
`(candidate_key_hmac, position_id, hiring_cycle_id)`를 identity로 사용하고 신규·재활성·단계 이동을
별도로 계산해야 한다.

- counter-AC: ClickUp task ID 또는 이름 유사도만으로 같은 채용 cycle이라고 판단한다.

### AC-6 — LinkedIn 시장 접근성

When 시장 접근성을 계산하면, 시스템은 frozen query와 ordered hash, 첫 20개 HMAC-unique
표본의 predicate 판정을 요구하고 pool과 precision을 곱하는 versioned 수식만 사용해야 한다.

- counter-AC: 0/20 적합인데 전체 검색 결과가 많다는 이유로 EASY가 된다.

### AC-7 — Legacy 상태

While Golden v2 callable과 runtime 검사가 없으면, 시스템은 Golden v1을
`CONTRACT_ONLY_NOT_EXECUTABLE`, `publication_allowed=false`로 표시하고 발행을 NOT_RUN해야 한다.

- counter-AC: JSON hook 문자열이 존재한다는 이유로 Golden 발행 준비가 됐다고 보고한다.

### AC-8 — 자동 검사와 의미 변조

When Weekly acceptance를 실행하면, 시스템은 SOT·INDEX·Skill·Golden references·legacy status를
검사하고 필수 heading, 수식, pipeline stage, 링크 또는 발행 금지를 변조한 사본을 실패시켜야 한다.

- counter-AC: 검사기가 파일 존재와 `PASS` 문자열만 확인한다.

### AC-9 — 안정적인 검증 설명

When 단위시험이나 mutation 수가 바뀌면, `verification-commands.md`는 쉽게 낡는 고정 숫자 대신
0건 거부, mutation 생존 0건, CHECKED 양수라는 성공 계약을 유지해야 한다.

- counter-AC: 검사 수가 하나 늘었는데 SOT에는 계속 `mutation 25종`이라고 남는다.

### AC-10 — 데이터 안전과 외부 효과

While 이 통합 작업을 수행하면, 시스템은 실제 후보자 정보나 외부 업무 시스템을 읽거나 쓰지
않아야 하며 원본 worktree 밖의 사용자 데이터를 변경하지 않아야 한다.

- counter-AC: SOT 검증을 명분으로 Aside나 Notion에 접속하거나 후보자 이름을 fixture에 넣는다.

## 입출력·오류·경계 계약

검사 입력은 repository root와 아래 regular file이다.

- `docs/sot/weekly-ops-contract.md`
- `docs/sot/INDEX.md`
- `docs/sot/verification-commands.md`
- `.agents/skills/weekly-ops/SKILL.md`
- `.agents/skills/weekly-ops/references/prompt-contract.md`
- `.agents/skills/weekly-ops/references/notion-golden-sample.md`
- `contracts/weekly-ops/notion-golden-sample-v1.json`

검사 출력은 `PASS|FAIL|NOT_RUN`, 이름 있는 오류 코드, `CHECKED` 양수다. 파일 누락·빈 파일·symlink,
JSON 파싱 실패, 필수 의미 누락은 FAIL이고 repository root 자체를 읽지 못하면 NOT_RUN이다.

## RED→GREEN과 공격 계획

1. 먼저 checker의 fail-open stub과 독립 fixture 시험을 추가한다.
2. 필수 heading·수식·stage·참조·legacy 발행 금지를 제거한 fixture가 모두 RED인지 확인한다.
3. SOT와 checker를 구현해 같은 원명령을 GREEN으로 만든다.
4. checker의 오류 반환을 `return []`로 변조한 사본을 기존 단위시험이 죽이는지 확인한다.
5. 전체 Weekly acceptance와 원칙 검사, 비밀 검사, diff 검사를 실행한다.

## 롤백·영향 반경·데이터 안전

- 영향 반경: Weekly 문서 탐색, Golden 요청의 fail-closed 상태, 로컬/CI Weekly acceptance.
- 일반 Weekly v1 계산·렌더링 로직은 변경하지 않는다.
- 새 SOT와 참조·checker·legacy 상태를 한꺼번에 revert한다.
- 운영 DB schema와 외부 페이지는 변경하지 않는다.
- 실제 후보자 이름·메일·프로필 URL을 저장소에 넣지 않는다.

## 시작 검증 장부

- 시각: `2026-09-01T14:18:05+09:00`
- HEAD: `251c3419446f04c5d3c00dfc0a839923e1c3540d`
- branch: `task/weekly-ops-skill`
- worktree: clean
- session shell PID: `26499`
- `docs/sot/coding-principles.md`: 직접 전체 로드 PASS
- `docs/sot/principles.yaml`: 직접 전체 로드 PASS
- `bash scripts/acceptance-principles-check.sh`: exit 0

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 원칙 정본 두 파일과 로컬·CI 연결은 확인됐다. 이 결과는 Weekly 요구사항 SOT가 이미 존재한다는
증거가 아니므로 본 작업의 RED는 별도로 만들어야 한다.

## 적대 검증 로그

구현 뒤 Claude V1 원문과 fresh Codex V2 재현 결과를 같은 변경 SHA와 artifact hash에 묶어 기록한다.
V1을 실행하지 못하면 PASS로 대체하지 않고 NOT_RUN 또는 BLOCKED로 남긴다.
