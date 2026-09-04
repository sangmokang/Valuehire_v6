# Weekly Ops 요구사항 SOT 통합 목표 — 2026-09-01

## 결론

Weekly 업무 규칙을 다음 세션이 한 곳에서 찾을 수 있는 영구 정본으로 통합한다. 현재 Golden
v1은 문서 계약만 있고 실행 엔진이 없으므로, 정본 통합 뒤에도 실제 Golden 발행은 계속 막는다.

> **무엇을** — Weekly 전용 SOT, Skill 참조, legacy 상태, 자동 검사를 한 변경으로 묶는다.
> **왜** — 요구가 여러 파일에 흩어져 있고 현재 검사 설명도 실제 mutation 수와 갈라졌기 때문이다.
> **버린 길** — 기존 Golden v1 문서만 정본이라고 선언하는 방법은 실행되지 않는 계약을 완성품처럼 보이게 하므로 사용하지 않는다.
> **대가** — 문서뿐 아니라 Skill·계약·검사 배선도 함께 바뀌며, Golden v2 엔진 전까지 발행은 NOT_RUN이다.
> **되돌리기** — 새 SOT와 참조·검사 변경을 함께 revert하면 이전 탐색 구조로 돌아가며 운영 데이터에는 영향이 없다.

## 착수 당시 상태와 근본 원인

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

## 통합 후 현재 상태

- `docs/sot/weekly-ops-contract.md`가 Weekly 요구사항의 영구 업무 정본이며 `docs/sot/INDEX.md`,
  공용 Weekly Skill, Golden reference, runtime/DB contract와 검사기에 연결됐다.
- 정본은 보고 주차와 4주 창, 실제 고객 포지션과 Scraped staging, Gmail intent, 후보자 Task identity,
  신규·재활성·단계 이동, 활성·면접·면접 직전 Pipeline, Saramin·JobKorea·LinkedIn 채널 분리,
  컨설턴트별 활동 집중도, LinkedIn 20명 시장 표본, 시장 접근성·coverage risk, 개인정보와 발행 권한을
  각각 독립된 계약으로 정의한다.
- 경영진 브리핑은 관측 사실과 수식 결과만 표시한다. P0/P1, 즉시 실행, 해야 한다 같은 경영 명령을
  LLM이 생성하지 못하고 최근 인입은 `observed_at` 내림차순 사실 목록으로만 렌더링한다.
- legacy Golden v1은 계속 `CONTRACT_ONLY_NOT_EXECUTABLE`, `publication_allowed=false`다. callable registry,
  private Notion publisher, readback 구현이 없는 동안 Golden 발행은 `NOT_RUN`이며 일반 v1 renderer로
  우회할 수 없다.
- 최신 PostgreSQL 임시 클러스터 truth table은 49개 반례·정상 경로를 모두 통과했다. 운영 DB migration,
  Notion, Gmail, ClickUp, admin web, push, PR, merge는 실행하지 않았다.

### 2026-09-02 로컬 검증 증거

- Weekly SOT 단위계약: 35 tests, PASS
- Weekly SOT 의미검사: `CHECKED: 89`, PASS
- Weekly full acceptance: `CHECKED: 60`, mutation 생존 0건
- Strict 원칙 정본·장부·배선: `34/34`, PASS
- Strict 원칙 mutation·500/501 경계: `CHECKED: 41`, PASS
- acceptance 무력화 mutation: `CHECKED: 10`, PASS
- mechanism registry 적대검사: `CHECKED: 31`, PASS
- Weekly 전체 단위시험: 116 tests, PASS
- PostgreSQL fresh DDL 적용과 runtime truth table: `CHECKED: 49`, PASS
- `verify.sh`, `git diff --check`, Python compile, Bash syntax: PASS

이 증거는 로컬 계약·검사 통과를 뜻하며 Golden v2 실행 엔진 또는 외부 발행 완료를 뜻하지 않는다.

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

### 최종 독립 감사 입력 계약 — 2026-09-02

- 직전 최종 로컬 GREEN: Weekly 전체 단위시험 116건,
  full acceptance `CHECKED: 60`, SOT checker `CHECKED: 89`.
- Strict 기반 검사: 원칙 `34/34`, 원칙 mutation `CHECKED: 41`, acceptance 의미 mutation
  `CHECKED: 10`, mechanism registry `CHECKED: 31`, `verify.sh` PASS.
- PostgreSQL fresh ephemeral DDL 및 runtime truth table: `CHECKED: 49`, PASS.
- 최종 V1/V2는 같은 tracked diff hash와 전체 diff를 입력으로 받는다. 다음 일곱 항목을 이전 결함의
  회귀 표적으로 다시 공격한다: briefing 권한 문구, renderer 실행 연결, state/flow zero evidence,
  caller-supplied KPI, 7일·Monday weekly-run 정렬, report week와 metric ISO week 분리,
  provider receipt에 묶인 LinkedIn result count.
- 최종 독립 감사 원문·출력은 개인정보와 외부 쓰기 없이 `.omx/artifacts/`에 저장한다.
  이 section은 감사 입력을 고정하는 장부이며 결과를 미리 PASS로 선언하지 않는다.
- 외부 쓰기: NONE. Golden v1은 `CONTRACT_ONLY_NOT_EXECUTABLE`, publication은 `NOT_RUN`이다.

### 2026-09-02 fresh PRE-V2 FAIL과 보정

- fresh Codex PRE-V2는 `FAIL / REQUEST_CHANGES`였다. DB digest를 함께 갱신하면 live-client origin,
  Gmail intent 승격, 5개 발행 대상 제약을 약화해도 기존 검사가 통과했고, 새 DB lineage 시험 파일이
  Git 미추적 상태였으며, publication receipt의 target identity와 두 candidate-name alias가 빠져 있었다.
- 일반 Weekly v1 renderer를 Golden v2 문체로 바꾼 변경은 “일반 v1 출력 불변” 계약을 위반하므로 원래
  heading·점수·action wording으로 복구했다. Golden v2 경영지시 금지는 briefing projection에만 적용한다.
- 보정 뒤 digest를 공격자가 같이 갱신해도 다음 의미 변조를 고유 오류로 차단한다: Scraped live-position
  승격, `REFERENCE_ONLY` intent 승격, 발행 대상 5→4 축소, normalized fact·zero-result·LinkedIn result
  receipt evidence-membership 제거.
- runtime은 정확한 5개 publication target만 허용하고 receipt에 `target_name`과 `target_id`를 남기며,
  candidate/applicant name key는 case·underscore·hyphen·space를 제거한 token으로 정규화해 canonical
  input에서 차단한다.
- RED 뒤 최신 GREEN은 Weekly 116 tests, SOT `CHECKED: 89`, full acceptance `CHECKED: 60`, PostgreSQL
  truth table `CHECKED: 49`다. 새 DB lineage 시험 파일은 Git index에 추가했다.
- 이전 수동 Claude prompt와 artifact hash는 폐기했다. 최종 Claude V1은 새 tracked diff hash로 사용자가
  직접 실행해야 하며, 그 원문을 받은 뒤 같은 hash에 대한 fresh Codex V2가 PASS하기 전에는 Strict 완료,
  commit, push를 선언하지 않는다.

### RED 장부

- RED checkpoint: `3b389fdee994a76fe3b38d73d845126c5f8276cd`
- 최초 checker는 `audit_bundle()`가 무조건 빈 오류 목록을 반환하는 fail-open stub이었다.
- 최초 독립 fixture는 heading·수식·Pipeline stage·SOT link·legacy publication block 변조를
  실패시켰다. 이후 첫 fresh Codex 감사 반례를 회귀로 추가해 다음 RED를 다시 확인했다.
  - 의미가 뒤집힌 문장 뒤에 정상 문자열을 decoy로 추가
  - 3-key identity를 2-key로 축소
  - 곱셈식을 덧셈식으로 교체
  - Pre-interview stage 집합 교체
  - runtime URL suffix 변조
  - Golden reference·DB DDL 밖에 정상 문자열을 주석으로 추가
  - JSON은 유효하지만 nested object shape를 list로 변조

### 첫 V1/V2 결과와 보정

- Claude V1: `NOT_RUN` — CLI가 `Error: No messages returned from query`로 종료했다. PASS로
  대체하지 않았다.
- fresh Codex V2 artifact hash:
  `78a8b003024904547c5af2963a283e211b0ff7e4872de356d45dccebe56a88ef`
- V2 verdict: `FAIL`.
- 재현된 핵심 결함:
  - checker가 전역 문자열만 찾아 의미 반전+decoy를 통과
  - SOT의 3-key identity와 Golden JSON/reference/DB DDL의 2-key가 충돌
  - SOT의 곱셈식과 Golden JSON/reference의 덧셈식이 충돌해 0/20도 EASY가 될 수 있음
  - Notion URL을 prefix로만 검사
- 보정:
  - section-scoped SOT·Skill·reference 검사와 exact JSON/DDL 구조 검사
  - candidate identity를 `(candidate_key_hmac, position_id, hiring_cycle_id)`로 통일
  - 정확한 첫 20 HMAC-unique 표본과 정수 곱셈식, `0/20 → HARD 0` 고정
  - 11-section Golden layout, 채널별 4주, coverage risk 명칭 고정
  - JobKorea·Saramin·ClickUp·Notion URL exact equality 검사

### GREEN 검증 장부

- Weekly SOT 단위 계약: 16건 PASS
- Weekly 전체 단위시험: 78건 PASS
- Weekly full acceptance: `CHECKED: 55` PASS
- SOT checker: `CHECKED: 63` PASS
- Strict 원칙: `CHECKED: 34` PASS
- semantic mutation: `CHECKED: 10` PASS
- mechanism registry AC-M: `CHECKED: 31` PASS
- `verify.sh`: tracked secret scan PASS
- `git diff --check`, shell syntax, Python compile: PASS
- 외부 쓰기: 없음. Notion, Gmail, ClickUp, admin web, 운영 DB를 읽거나 쓰지 않았고 push·PR·merge도 하지 않았다.

→ 이 장부의 GREEN은 로컬 구현·검사 결과다. 최종 Claude V1과 fresh Codex V2가 같은 최종
artifact hash에서 모두 PASS하기 전에는 Strict 완료 checkpoint를 만들지 않는다.

### 두 번째 V1/V2 결과와 보정

- Claude V1 재시도: `NOT_RUN` — 최종 artifact를 대상으로 실행했으나 3분 이상 아무 결과를
  반환하지 않아 해당 Claude 프로세스만 종료했다. PASS로 대체하지 않았다.
- fresh Codex V2 artifact hash:
  `a2d964f0d7f83924a3f5ae3a3f0f9f4a87d708d747d6c5a3bd1bcfa15ebc166b`
- V2 verdict: `FAIL`.
- 재현된 핵심 결함:
  - mutation 격리본에 DB 계약이 없어 무관한 import 실패도 mutation kill로 합격
  - 금지→필수, 4주 출처 반전, Golden reference의 경영 명령 반전을 checker가 통과
  - Golden collapsed layout과 알 수 없는 실행 필드 추가를 legacy JSON 검사가 통과
  - DB의 시장 수식과 표본 20개 제약 변조를 checker가 통과
  - DB가 20개 JSON 길이만 보아 HMAC 고유성·순번·predicate key/value·qualified 재계산을 보장하지 않음
  - 공용 briefing style이 Golden에서 금지한 고객 액션·선행 소싱 문구를 지시
- 보정:
  - mutation마다 완전한 격리본을 만들고, 변이 전 단위시험 수집·성공 baseline을 먼저 증명
  - 의미 반전·layout·unknown key·DB 수식/표본·SQL comment decoy 회귀 추가
  - LinkedIn evaluation을 exact 3-field, rank 1..20, HMAC 20개 고유, frozen predicate key,
    `TRUE|FALSE|UNKNOWN`, qualified count 재계산 계약으로 강화
  - pool/precision point도 DB가 원시 입력에서 다시 계산하도록 제약
  - briefing style을 시간순 관측 사실과 데이터 커버리지 중심으로 교체
- 보정 후 두 번째 V2 반례 7종은 모두 `KILLED`로 재현됐다.
- PostgreSQL 임시 로컬 DB에 DDL 적용 PASS. 정상 20개 표본=true, 중복 HMAC 표본=false,
  UNKNOWN 1개가 있는 표본의 qualified count=19를 확인했다. 운영 DB에는 적용하지 않았다.

### 최종 로컬 GREEN 장부

- Weekly SOT 단위 계약: 23건 PASS
- Weekly 전체 단위시험: 85건 PASS
- Weekly full acceptance 당시 script revision: `CHECKED: 56` PASS
- SOT checker: `CHECKED: 63` PASS
- 두 번째 V2 반례 재현: 7/7 `KILLED`
- Strict 원칙: `CHECKED: 34` PASS
- semantic mutation: `CHECKED: 10` PASS
- mechanism registry AC-M: `CHECKED: 31` PASS
- `verify.sh`, `git diff --check`, shell syntax, JSON parse, Python compile: PASS
- PostgreSQL ephemeral DDL apply와 표본 함수 진리표: PASS
- 외부 쓰기: 없음. Notion, Gmail, ClickUp, admin web, 운영 DB를 읽거나 쓰지 않았고
  stage·commit·push·PR·merge도 하지 않았다.

→ 이 GREEN도 최종 Claude V1과 fresh Codex V2가 같은 최종 artifact hash에서 모두 PASS하기
전에는 Strict 완료 checkpoint 근거가 아니다.

### 세 번째 V2 결과와 보정

- final-candidate artifact hash:
  `f18ac7c131cdcf2c921c93b0b2721c841dfa04cc3416741a72a3a4e5d1b2ae74`
- Claude V1: `NOT_RUN` — OMX advisor의 role prompt 전달 오류 뒤 무응답 재시도가 3분 이상
  결과를 반환하지 않아 종료했다. PASS로 대체하지 않았다.
- fresh Codex V2 verdict: `FAIL`.
- 재현된 핵심 결함:
  - Markdown HTML comment 안의 정상 문구로 4주·Pipeline·Scraped 규칙 변조를 숨길 수 있음
  - SQL string/dollar-quoted literal 안의 정상 수식으로 실행 제약 우회를 숨길 수 있음
  - legacy JSON은 top-level만 exact여서 nested 실행 필드와 fail-closed 반전을 허용함
  - malformed nested object가 이름 있는 FAIL 대신 `AttributeError`를 일으킴
  - mutation test의 import·syntax 실패도 test 수만 양수면 kill로 오인할 수 있음
  - legacy JSON에 reactivation/pre-interview metric, DB enum에 pre-interview metric이 빠짐
- 보정:
  - HTML comment 제거 후 section 의미를 검사하고 identity·Scraped·경영 명령·발행 우회 반례를 고정
  - 함수 body와 SQL literal을 구분해 실행 SQL만 검사하고 JSON/DDL canonical digest를 함께 고정
  - legacy JSON의 recursive exact key shape와 canonical value digest, malformed shape FAIL을 추가
  - import/module/syntax 실패는 mutation infrastructure failure로 분리
  - `reactivated_task_count`, `pre_interview_pipeline_count`를 JSON·DB·reference의 독립 지표로 추가

### 세 번째 보정 후 로컬 GREEN 장부

- Weekly SOT 신규 반례: 6건 RED 재현 뒤 GREEN
- Weekly 전체 단위시험: 91건 PASS
- Weekly full acceptance 당시 script revision: `CHECKED: 56` PASS
- SOT checker: `CHECKED: 63` PASS
- Strict 원칙: `CHECKED: 34` PASS
- semantic mutation: `CHECKED: 10` PASS
- mechanism registry AC-M: `CHECKED: 31` PASS
- `verify.sh`, `git diff --check`, shell syntax, JSON parse, Python compile: PASS
- 파일 hard limit: `sot_gate.py` 600줄, acceptance 600줄, 함수 100줄 이하 PASS
- PostgreSQL ephemeral DDL apply PASS. pre-interview metric constraint 1건, 20개 표본 valid=true,
  UNKNOWN 1개 표본 qualified count=19를 확인했다.
- 외부 쓰기: 없음. Notion, Gmail, ClickUp, admin web, 운영 DB를 읽거나 쓰지 않았고
  stage·commit·push·PR·merge도 하지 않았다.

→ 같은 최종 artifact hash에서 Claude V1과 fresh Codex V2가 모두 PASS하기 전에는 Strict 완료가
아니다. Claude V1이 계속 `NOT_RUN`이면 변경은 로컬 미커밋 상태로 남긴다.

### 네 번째 V1 분할 탐색과 보정

- `f4510a2fc34b12b550432dfbfda5ca7c58f0c84fd42696adf69abe7226deea23` 전체 diff를 한 번에
  검토한 Claude와 fresh Codex는 장시간 무출력으로 종료돼 둘 다 `NOT_RUN`이다. PASS로 대체하지
  않았다.
- Claude 최소 연결 진단 `CLAUDE_OK`는 성공했다. 이후 같은 아티팩트를 1만~2만 자 계약 조각으로
  나누자 실제 판정이 반환됐다. 이 분할 결과는 결함 탐색 증거이며, 해시가 바뀐 뒤의 최종 V1
  판정은 아니다.
- Claude가 제안한 반례 중 다음은 로컬에서 재현돼 RED로 고정했다.
  - 외부 object ID를 외부 호출 전 필수값으로 읽을 수 있는 순환 발행 문장
  - market pool points의 원시 입력 필드 미명시
  - weekly run/source snapshot/event ledger의 UPDATE·DELETE 허용
  - mutable task current stage와 최신 event state의 불일치 허용
  - publication receipt가 다른 report snapshot/hash를 가리켜도 삽입 가능
  - 빈 문자열 zero-result receipt 허용
  - 1만 자리 JSON 정수에서 `ValueError`로 checker crash
  - runtime `require_readback=false` 의미 변조 통과
  - Golden reference에 first-20 표본 부정문을 추가해도 통과
  - mutation test의 `IndentationError|TabError|_FailedTest`를 정상 kill로 오분류
- 단순 재귀 JSON 배열은 이미 `LEGACY_CONTRACT_INVALID`로 통제돼 재현되지 않았다. Legacy nested
  boolean 반전은 canonical digest와 exact value 검사가 함께 차단해 결함으로 세지 않았다.
- 보정:
  - pre-write 조건과 post-write receipt를 분리하고 pool input을 `result_count_lower_bound`로 고정
  - append-only trigger, event-derived current-state view, recorded-at tie-break 추가
  - report snapshot/hash composite FK와 receipt lineage trigger 추가
  - pathological JSON 예외, runtime publication guard exact check, Golden reference digest pin 추가
  - mutation infrastructure 오류 분류에 `IndentationError|TabError|unittest.loader._FailedTest` 추가
- PostgreSQL ephemeral 실증:
  - DDL 전체 apply PASS
  - weekly run·pipeline event·publication receipt UPDATE 차단 PASS
  - 동일 event time에서 `recorded_at` 최신 상태 선택 PASS
  - 빈 zero receipt와 다른 report/hash receipt 차단 PASS
  - 정상 publication receipt 삽입 PASS
  - 임시 DB와 디렉터리 정리 완료, 운영 DB 접근 없음

→ 위 보정 당시 Weekly 단위시험 95건과 그 script revision의 full acceptance `CHECKED: 56`이 PASS했다. 그러나 최종
artifact hash에서 V1/V2를 다시 수행하기 전에는 Strict 완료나 checkpoint 근거가 아니다.

### 다섯 번째 V1 분할 탐색과 보정

- `feffd94d2c327a19225566b8e2d8d6f347cfdf02e888ec8346f1ff7f2b7b0980`에서 Claude V1을
  SOT·JSON·SQL·checker·mutation harness로 분할 실행했다. SQL, checker, harness 조각은 FAIL을
  반환했으며 최종 V1 PASS로 간주하지 않았다.
- 로컬에서 재현된 결함:
  - verified-zero receipt 원장의 사후 수정 허용
  - 발송 attempt의 identity와 terminal receipt 사후 수정 허용
  - publication intent의 report snapshot/hash 계보 사후 변경 허용
  - mutation baseline 실패 후에도 mutation loop 계속 실행
- 재현되지 않은 지적:
  - SOT required token HTML-comment decoy는 `audit_bundle` 입구의 `_visible_markdown`로 이미 차단됨
  - 비정상 `recent_client_positions` 타입은 crash하지 않고 `LEGACY_STRUCTURE_INVALID`로 차단됨
  - 깨끗한 baseline 복제본의 단일 mutation으로 인한 임의 test failure는 mutation kill의 표준
    판정이며, 무관한 사전 실패는 baseline gate가 차단함
- 보정:
  - zero-result assertion은 append-only trigger로 고정
  - proposal attempt는 identity 불변, `PENDING -> SENT|FAILED`만 허용, terminal 상태는 불변으로 고정
  - publication intent는 lineage 불변과 단방향 상태 전이를 trigger로 강제
  - mutation baseline 실패 시 즉시 종료
- PostgreSQL ephemeral 실증에서 위 세 원장의 변조 차단, proposal 정상 종결, publication 정상
  상태 전이와 receipt 삽입을 확인했다. 운영 DB에는 적용하지 않았다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

## 2026-09-02 후속 RED→GREEN — 제안 영수증과 신규 Task 계보

### 1층 결론

진행 중이다. 이전 continuation은 fresh Codex V2가 기존 38개 PostgreSQL 진리표의 두 사각지대를
독립 재현했으므로 `progress`다. 이번 변경에서 세 사각지대는 실제 DB·runtime 거부 규칙과 해시 독립
의미 검사로 보정됐고, 새 PostgreSQL 진리표 44개와 Weekly 단위시험 106개가 통과했다.

아직 Strict 완료가 아니다. 최종 변경 지문에서 Claude V1과 fresh Codex V2를 다시 실행하지 않았고,
Claude V1의 과거 무출력 시간초과는 현재 `NOT_RUN` 상태다. Notion·Gmail·ClickUp·운영 DB·admin web에는
아무것도 쓰지 않았고 push·PR·merge도 수행하지 않았다.

### 2층 판단 근거

- 시각: `2026-09-02T07:38:00+09:00`
- 작업 폴더: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/weekly-ops-skill`
- HEAD: `3b389fdee994a76fe3b38d73d845126c5f8276cd`
- 이 기록 직전 tracked diff SHA-256: `1b05e84b846afbc95fdb2cfe156f578316607f71eaa205bb741b38b3484b233e`
- 최종 독립 검토 hash는 이 기록을 포함한 tracked diff를 다시 계산해 V1/V2 입력 봉투에 고정한다.
  문서 안에 자기 자신의 최종 hash를 넣는 자기참조 방식은 사용하지 않는다.
- 위험등급: L3 — DB 계약, SOT 강제 검사, 3개 이상 파일을 함께 변경한다.

RED 1 — `proposal_send_attempts.provider_receipt_ref`는 빈 값과 중복만 막았고, 같은 source snapshot의
불변 증거 목록에 실제 존재하는지는 확인하지 않았다. 기존 PostgreSQL 진리표는 `send-receipt-1`을
임의로 써도 정상 처리했으므로 실제 portal sent-history receipt 계보를 증명하지 못했다.

RED 2 — `new_task_count`는 첫 VERIFIED `CREATED` event가 아니라
`candidate_position_tasks.first_created_at` 행만 셌다. fresh Codex V2가 해당 분기를 `select 0`으로
바꾸고 DB digest까지 맞추자 `_db_errors()`가 빈 목록을 반환했다. 즉 이전 검사는 파일 지문에는
민감했지만 계산 의미 변조에는 무력했다.

RED 3 — 일반 Weekly runtime은 `CLIENT_REQUESTED + NONE`과 `CLIENT_SHARED + REQUESTED`를 오류 없이
받아 data verdict를 PASS로 만들었다. SOT의 `REQUESTED→CLIENT_REQUESTED`,
`POSITION_SHARED→CLIENT_SHARED`, 기존 고객 포지션 전용 변경 신호 규칙이 실제 입력 gate에 연결되지
않은 상태였다.

GREEN — source snapshot 자체에 비어 있지 않고 중복 없는 `evidence_refs`를 불변 저장하고, SENT 전이는
`source.evidence_refs ? provider_receipt_ref`가 참일 때만 허용한다. 최초 CREATED는 Task의 source와
`first_created_at`을 정확히 공유해야 하며, `new_task_count`는 해당 CREATED event만 집계한다. Runtime은
origin별 허용 intent 집합을 직접 검사하고 허용되지 않은 조합을 `POSITION_ORIGIN_INTENT_MISMATCH`로
차단한다.

의미 검사 — 새 `tests/weekly_ops/test_weekly_db_lineage_contract.py`는 DB digest 상수를 mutant digest로
바꾼 뒤에도 영수증 membership 제거, 신규 Task 분기 `select 0`, CREATED source/time 비교 제거를 각각
고유 오류로 적발한다. 따라서 digest 불일치 하나만으로 합격하는 검사가 아니다.

> **무엇을** — provider receipt를 source snapshot의 불변 evidence 집합에 귀속하고 신규 Task를 첫 CREATED event에서만 센다.
> **왜** — 문자열 존재나 Task 행 존재만으로는 실제 발송·신규 생성 사실을 증명하지 못한다.
> **버린 길** — 별도 appendable evidence table은 사후에 조작 receipt를 추가할 수 있어 기각했다. Task의 `first_created_at` 직접 집계도 event 누락을 숨겨 기각했다.
> **대가** — source snapshot 입력에 `evidence_refs`가 필수가 되고 기존 DDL 소비자는 migration 설계가 필요하다. 이번 변경은 계약뿐이며 운영 DB에는 적용하지 않았다.
> **되돌리기** — DDL·`sot_gate.py`·lineage 단위시험을 같은 변경으로 되돌린다. 운영 데이터 변경이 없으므로 데이터 롤백은 없다.

### 3층 증거 원문

```text
$ cat docs/sot/coding-principles.md
$ cat docs/sot/principles.yaml
$ bash scripts/acceptance-principles-check.sh
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 34
```

→ 현재 저장소의 코딩 원칙 정본과 기계 장부를 직접 읽었고, 원칙 검사 34개가 모두 통과했다.

```text
$ python3 -m unittest tests/weekly_ops/test_weekly_db_lineage_contract.py
FFFFF
Ran 5 tests in 0.034s
FAILED (failures=5)
```

→ 빠진 동작 때문에 다섯 검사가 먼저 실패했다. 문법/import 오류가 아니라 요구한 DB 계보와 의미
검사 코드가 아직 없어서 발생한 RED다.

```text
$ python3 -m unittest tests/weekly_ops/test_weekly_db_lineage_contract.py
.....
Ran 5 tests in 0.249s
OK
```

→ 최소 변경 뒤 같은 다섯 검사가 GREEN이 됐다.

```text
$ python3 -m unittest discover -s tests/weekly_ops
..........................................................................................................
Ran 106 tests in 27.213s
OK
```

→ Weekly 전체 단위시험 106개가 통과했고 검사 대상은 0개가 아니다.

```text
$ psql -X ... -f contracts/weekly-ops/db-contract-v1.sql \
  -f .omx/artifacts/weekly-ops-db-truth-table.sql
...
fabricated_provider_receipt_rejected              | EXPECTED_REJECTION | P0001:PROPOSAL_SEND_ATTEMPT_SENT_EVIDENCE_INVALID
created_event_source_lineage_mismatch_rejected    | EXPECTED_REJECTION | P0001:PIPELINE_INITIAL_EVENT_INVALID
created_event_timestamp_lineage_mismatch_rejected | EXPECTED_REJECTION | P0001:PIPELINE_INITIAL_EVENT_INVALID
task_row_without_created_event_not_counted        | EXPECTED_REJECTION | P0001:WEEKLY_METRIC_DERIVATION_INVALID
new_task_count_derived_from_first_created_event   | ACCEPTED           | new_task_count=1
result  | count
--------+------
CHECKED | 44
```

→ fresh 임시 PostgreSQL에 DDL을 처음부터 적용했다. 새 반례 네 종류는 거부되고 정상 신규 Task 집계는
1로 수락됐다. 임시 DB는 종료·삭제했으며 운영 DB에는 연결하지 않았다.

```text
$ bash scripts/acceptance-weekly-ops-skill.sh --full
...
PASS: mutation position origin-intent mapping bypass is killed by tests
PASS: mutation Weekly SOT checker fail-open is killed by tests
CHECKED: 60
```

→ Weekly 인수 게이트 60개가 통과했고, origin-intent gate와 fail-open을 포함한 우회 변조가 모두
적발됐다. 새 DB
의미 변조 세 종류는 이 명령이 실행하는 106개 단위시험 안에서 별도로 주입됐다.

```text
$ python3 .agents/skills/weekly-ops/scripts/sot_gate.py --repo .
PASS: Weekly Ops SOT semantics and execution links
CHECKED: 89
```

→ SOT와 실행 표면의 의미·배선 검사 89개가 통과했다. 최종 V1/V2 전까지 이 결과만으로 완료를
선언하지 않는다.

```text
$ python3 -m py_compile ...
$ bash -n scripts/acceptance-weekly-ops-skill.sh
$ python3 -m json.tool contracts/weekly-ops/runtime-contract-v1.json
$ python3 -m json.tool contracts/weekly-ops/notion-golden-sample-v1.json
$ git diff --check
exit 0

$ wc -l .agents/skills/weekly-ops/scripts/sot_gate.py \
  .agents/skills/weekly-ops/scripts/weekly_gate.py \
  scripts/acceptance-weekly-ops-skill.sh
600 .agents/skills/weekly-ops/scripts/sot_gate.py
595 .agents/skills/weekly-ops/scripts/weekly_gate.py
599 scripts/acceptance-weekly-ops-skill.sh
FUNCTION_LIMIT_PASS

$ bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked
```

→ 문법·JSON·diff whitespace, 직접 변경 코드의 600줄/100줄 상한, tracked secret pattern 검사가
모두 통과했다. 선택 진단인 전체 Git history 노출 검사는 오래 걸려 중단했으며 필수 gate PASS로
기록하지 않는다.

### 최종 해시 전 V1 SQL 공격 보정과 Strict 원칙 재로드

- 검토 대상 diff hash `3dd7f20b2720f9d9c9acd1837b817e6c33450180135ac12664d614863b5b3a9e`의 Claude V1
  SQL 검토는 빈 발송 영수증, 빈 Pipeline 근거, 인증되지 않은 채널의 `COVERED` 기록, 오래된 READY
  report snapshot 발행 가능성을 material finding으로 판정해 FAIL이었다.
- 채택한 보정:
  - `SENT` provider receipt와 Pipeline evidence는 공백 문자열도 DB가 거부한다.
  - 채널 coverage `COVERED`는 `AUTHENTICATED`와 함께일 때만 허용한다.
  - report snapshot은 run별 연속 immutable revision이며 가장 높은 전체 revision과 run이 모두 READY인
    경우만 current다. Snapshot insert, publication intent, receipt가 같은 weekly run row lock을 사용해
    오래된 revision의 동시 발행을 차단한다.
- 기각한 제안: external ClickUp task ID를 unique identity로 만드는 방식은 외부 ID가 lineage라는 SOT와
  충돌하고 실제 재채용 cycle을 합치므로 적용하지 않았다.
- Strict 원칙 직접 로드: 2026-09-01T13:28:52Z에 `docs/sot/coding-principles.md`와
  `docs/sot/principles.yaml`을 현재 worktree에서 읽고 `bash scripts/acceptance-principles-check.sh`를
  재실행했다. 2026-09-01T13:29:13Z 종료값 0, `CHECKED: 34`, 정본·장부·pre-push·CI 배선 PASS였다.
  첫 포장 실행은 zsh 예약 변수 `status` 충돌로 종료값 기록이 실패했으므로 합격 증거에서 제외했다.
- PostgreSQL 실증: 기본 local socket에는 서버가 없어 첫 시도는 `NOT_RUN`이었다. `/tmp` 아래 독립
  cluster와 별도 port로 원명령을 복구 실행해 DDL apply, `CHALLENGE+COVERED`, 빈 SENT receipt, 빈
  Pipeline evidence, stale report intent, stale report receipt 거부를 확인했다. READY revision 1 뒤 READY
  revision 2를 생성하고 current revision 2에 다섯 target receipt를 연결한 경우에만 run이 PUBLISHED가
  됐다. 출력은 `final_status=PUBLISHED`, `current_revision=2`, `verified_targets=5`였고 운영 DB 접근은
  없었다. 임시 cluster는 정지 후 `/Users/kangsangmo/.Trash/weekly-ops-pg.Vd8hVS`로 이동해 복구 가능한
  상태로 정리했다.
- 같은 해시의 Claude V1 A2(JSON-only)는 12건을 FAIL로 제기했다. Origin 전체 enum, 일반 Weekly v1
  점수 필드, legacy hook 문자열, stage/formula/표본 선언, 계정 allowlist를 단일 JSON만으로 fail-open으로
  해석한 항목은 DB·checker·일반 v1 보존 범위를 포함한 재공격 전까지 `UNRESOLVED`로 두고 바로 고치지
  않았다.
- Claude V1 A3(Skill/reference)는 다음 모순을 재현해 FAIL이었다.
  - Golden v1 `NOT_RUN` 선언 뒤 Phase 2·6과 legacy STOP/acceptance가 private Notion 쓰기·후보자 이름
    resolver·write 후 readback을 다시 허용하는 문구
  - prompt의 후보자 이름 절대 금지와 Skill의 조건부 private Notion 허용 간 충돌
  - 세 outreach capability가 모두 PASS일 때만 세 채널 diagnostics를 요구해 부분 실패 run에서 채널별
    blocker 기록이 사라질 수 있는 조건절
- 보정: legacy v1은 resolver·write·readback을 모두 하지 않고 future executable v2만 private resolver를
  허용한다. 세 고정 채널은 capability 상태와 무관하게 매 run diagnostic 한 건씩을 내고 non-PASS는
  blocker+NOT_RUN으로 남긴다. CI Weekly acceptance는 기본 인자의 암묵성도 제거해 `--full`을 workflow와
  mechanism registry에 명시했다. Verification 표의 과거 blob step 번호와 snapshot 날짜도 현재 값으로
  바로잡았다.
- A3의 "CI가 --full 없이 약화된다"는 원명령에서 재현되지 않았다. Acceptance script는 인자 없음도
  `${1:---full}`로 full mode가 된다. 다만 정본·workflow의 표현을 일치시키는 방어적 명시화는 채택했다.
- Claude V1 SQL B1/B2 재공격은 두 결함을 추가로 재현해 FAIL이었다.
  - `weekly_metric_snapshots`의 PARTIAL row가 숫자 값을 가질 수 있고 VERIFIED 0이 같은 run/source의
    `weekly-zero-result-v1` receipt 없이 저장될 수 있었다.
  - 빈 `predicate_results={}`가 key 집합 비교와 `bool_and`의 SQL NULL을 통과해 20/20 qualified,
    EASY 100으로 계산될 수 있었다.
- 보정:
  - PARTIAL/NOT_RUN metric value를 null로 고정하고, metric별 zero collection을
    `positions|outreach_events|pipeline_events`로 결정론적으로 매핑했다. VERIFIED 0은 같은 run/source,
    같은 receipt ref가 metric evidence에 포함될 때만 insert된다.
  - market validator의 predicate/evaluation aggregate를 `IS TRUE`로 닫고 HMAC/rank JSON type, nonblank
    predicate, exact key set을 강제했다. qualified count도 frozen must-have 각각의 명시적 TRUE만 센다.
  - 세 outreach capability 중 하나가 non-PASS여도 세 채널 diagnostic을 모두 요구하도록 runtime gate를
    `require_all_channels=True`로 고정했다.
- PostgreSQL ephemeral GREEN: 20개 빈 map과 19개 빈 map+1개 정상 map 거부, 정상 20개 표본과 qualified
  5명 재계산, PARTIAL 숫자 거부, receipt 없는 VERIFIED 0 거부, source/receipt 불일치 거부, 같은
  run/source의 positions·pipeline_events zero receipt 정상 수용을 확인했다. 운영 DB에는 적용하지 않았다.
- B1의 canonical position 관련 cross-run 지적은 해당 행이 run-scoped 행이 아니고 canonical position이
  global identity라는 현재 계약과 충돌해 기각했다. Publication revision/receipt 공격은 앞선 PostgreSQL
  실증에서 모두 차단된 상태를 유지했다.
- 후보 diff `bfc6b27dedc52652da484cf23f79353cfdeeee3a3159b03de603a40157ff9fec`의
  Claude V1 A1/A3는 material finding을 남겨 FAIL이었다.
  - SOT가 exact numeric/schema 충돌에서 machine contract 우선과 SOT 보존을 동시에 말해 45점/60점
    weight 반례를 결정론적으로 판정하지 못했다.
  - 과거 VERIFIED metric snapshot 사용과 same-run snapshot FK 규칙 사이의 import lineage가 없었다.
  - Monday 회의에서 `직전 Monday`가 방금 지난 00:00인지 마지막 완료 주의 시작인지 모호했다.
  - legacy Golden reference의 `private_display_map`이 v1 PII resolver 금지와 충돌했다.
  - future v2 존재 조건이 exact artifact/실행 predicate에 묶이지 않았고 verification 표의 Weekly step
    이름·wrapper 명령이 실제 workflow와 달랐다.
- 보정:
  - 동일 값을 양쪽이 명시하면 반드시 같고 충돌은 machine-contract 우선이 아니라 drift라고 단일화했다.
  - 과거 metric은 과거 snapshot hash/cutoff/evidence URI를 묶은 새 current-run snapshot을 캡처한 뒤 그
    ID만 참조하도록 했다. 과거 receipt의 현재 증거 승격은 계속 금지한다.
  - metric window end를 meeting ISO week의 Monday 00:00, start를 end-7 days로 exact 정의했다.
  - legacy v1 입력에서 display-name map을 제거하고 future v2 readiness를 여섯 exact tracked path,
    wrapped acceptance exit 0/PASS/positive CHECKED, run-bound hash로 고정했다. Caller 주장은 증거가 아니다.
  - verification 표의 step 5 이름과 wrapper 포함 명령을 `verify.yml` 원문과 일치시켰다.
- A2 JSON 슬라이스는 material finding 0으로 PASS였다. 그 review의 JSON-only silence 항목은 DB/checker
  슬라이스가 끝날 때까지 cross-layer `UNRESOLVED`로 유지한다.

> **무엇을** — 단일 READY 행 대신 현재 revision을 기계적으로 판별하고 발행 각 단계에서 다시 확인한다.
> **왜** — run이 BLOCKED를 거쳐 새 READY가 되면 이전 READY 행을 불변으로 보존하면서도 발행 후보에서
> 즉시 제외해야 하기 때문이다.
> **버린 길** — run당 READY 한 행 unique는 불변 snapshot을 갱신할 수 없고, 과거 READY 삭제·수정은
> 감사 이력을 훼손하므로 기각했다.
> **대가** — report revision이 연속이어야 하고 발행 쓰기마다 run row lock 비용이 든다.
> **되돌리기** — 이 SOT·DDL·checker·test 묶음의 로컬 checkpoint commit 한 건을 revert한다. 부분
> revert는 `RECOVERY_REQUIRED`이며 운영 DB에는 적용하지 않는다.

→ 보정 뒤 새 artifact hash에서 PostgreSQL 반례, 전체 gate, Claude V1 세 조각, fresh Codex V2를 모두
재실행하기 전에는 Strict 완료나 checkpoint 근거가 아니다.

### 스물세 번째 V1 career alias·intent enum 보정

- 최종 후보 Slice A V1은 여기어때 label과 GC Company 공식 도메인의 관계가 명시되지 않고, SOT의
  허용 intent 목록에서 `NONE`이 누락된 모순을 찾아 FAIL이었다.
- 보정:
  - career source의 보고 company는 `여기어때`, 공식 URL 법인 운영자는 `GC Company`로 분리
  - `NONE`을 허용 intent enum에 포함하되 origin 승격은 계속 금지
  - runtime checker가 여기어때↔GC Company alias를 exact mapping으로 검증

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 스물두 번째 V1 Skill·cleanup·report state 보정

- acceptance/test/misc V1은 Skill의 Required reads 밖 fail-open 문구가 검사되지 않고, unsafe temp path
  cleanup이 exit status를 실패로 바꾸지 않는 반례를 찾아 FAIL이었다.
- 보정:
  - Golden v1 publish-without-readback override를 visible Skill 전체에서 검사
  - unsafe temp path trap은 삭제를 건너뛰고 exit 1로 검증 실패를 확정
  - immutable report snapshot에서 도달 불가능한 PUBLISHED enum을 제거하고 run PUBLISHED만 상태로 유지

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 스물한 번째 V1 SOT 전체 digest 보정

- checker 2/2 V1은 `VERDICT: PASS`와 함께 의미 검사 목록 밖의 SOT 문장 약화를 잡지 못하는 medium
  finding을 남겼다. Strict에서는 finding이 있는 PASS를 최종 PASS로 인정하지 않았다.
- 보정: repository full bundle에서는 `docs/sot/weekly-ops-contract.md` 원문 전체 SHA-256을 고정하고,
  목록 밖 문장 한 글자 변경도 `SOT_CONTRACT_DIGEST_DRIFT`로 실패하는 mutation을 추가했다.
- SQL raw block 추출의 일관성 부채는 DB 전체 digest가 방어하고 실제 bypass가 아니므로 기록만 유지했다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 스무 번째 V1 checker 전반부 보정

- `dae27eb832c6b4ef25689b2cac1c8718869b609d3968b4e13f95ddb39f90d7ec`의 checker 1/2 V1은
  runtime 배열 타입 파손의 예외 종료, 동일 section의 상충 규칙 중복, source key 중복 덮어쓰기를
  찾아 FAIL이었다.
- 보정:
  - `career_sources`를 순회 전에 list로 검증하고 정해진 5개 회사만 고유하게 허용
  - outreach channel도 3개 고정 key를 정확히 한 번씩만 허용
  - identity·market formula·pipeline stage block은 section 안에서 정확히 한 번만 허용
  - Markdown은 NFKC 정규화 후 zero-width format character를 제거하고 의미 검사
- 기각:
  - duplicate heading은 `audit_bundle`이 모든 REQUIRED heading의 출현 횟수를 정확히 1로 검사해 이미 차단
  - legacy nested value는 checker 후반부의 formula/version/band/shape 검사가 별도로 검증

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열아홉 번째 V1 SQL market·publication 계보 보정

- `d22eca43b6b7cbd111421ab7de0517e1f76546e7df4de5c5aa961a47d44e0afd`의 SQL 3/3 V1은
  JSON null predicate가 qualified로 계산되고, READY snapshot·verified receipt 없이 publication이
  완료될 수 있는 반례를 찾아 FAIL이었다.
- 보정:
  - predicate JSON null 거부와 qualified의 `IS DISTINCT FROM TRUE` 계산
  - 20명 표본보다 작은 result lower bound 거부
  - run별 publishable snapshot 1개, READY snapshot 전용 intent, target별 intent 1개
  - receipt를 확인한 intent만 READBACK_VERIFIED, 정확한 5개 target receipt 뒤에만 run PUBLISHED 허용
- Golden v1은 계속 `CONTRACT_ONLY_NOT_EXECUTABLE`, publication `NOT_RUN`이며 위 보정은 실행 허용이
  아니라 향후 publisher의 완료 계보를 fail-closed로 제한한다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열일곱 번째 V1 SQL roster·zero·send 보정

- `b49f9f1003d9388ac09ea9714b8f12b32552d29791012b8e4b35dcfcd200e605`에서 SOT와 JSON은
  Claude V1 PASS였지만 SQL 1/3이 네 결함으로 FAIL이었다.
- 보정:
  - consultant focus에 consultant FK와 검증된 channel-mix 합계 함수를 추가
  - zero-result assertion PK를 source snapshot까지 확장해 같은 run/collection의 다중 source 증거 허용
  - FAILED send는 sent_at/provider receipt를 가질 수 없도록 SENT형 필드와 상호 배타화
  - source/customer/send/dedupe evidence 문자열의 빈 값 차단

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열여덟 번째 V1 SQL pipeline·metric evidence 보정

- `d96cd29ecfcd63d6bd956ed3a9eccbabb2ae8643c13a31c2634faaff20ad5930`의 SQL 2/3 V1은
  VERIFIED metric이 빈 JSON evidence를 허용하고 동일 stage의 `STAGE_CHANGED`가 movement로 남는
  반례를 찾아 FAIL이었다.
- 보정:
  - metric evidence는 비어 있지 않은 고유 opaque string 배열만 허용
  - `STAGE_CHANGED`는 이전 stage와 다른 destination만 허용하며 backfill의 다음 event도 같은 규칙 적용
- 기각:
  - `(event_at, recorded_at, pipeline_event_id)` 동률 결정은 SOT가 명시한 결정론이며 실제 시간 추론이 아님
  - external task ID는 lineage이고 canonical candidate task identity는 3-key이므로 외부 ID unique 승격 금지

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열여섯 번째 V1 machine-contract 예외 일반화

- `9084586c627d3574396942f37a0c3de6c9fb053e994327aae57bfeaca907b410`의 SOT V1은
  enum 예외가 origin/intent/count eligibility를 완화할 여지를 material defect로 판정해 FAIL이었다.
- 개별 보호 필드 열거만으로는 누락이 반복되므로 예외를 단조로운 표현 정합으로 일반화했다.
  Machine contract는 SOT의 허용 집합 확대, 배제 축소, identity/origin/intent/evidence/status/count
  eligibility 변경을 할 수 없으며 그런 충돌에서는 값 유형과 무관하게 SOT가 우선한다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열다섯 번째 V1 권한·intent 승격 보정

- `9c3b301bd40c84b4aef77c4c42afc1e6130cad4429049fd30b507fed74e242b1`의 SOT V1은
  machine-contract 예외의 안전 필드 범위와 Gmail intent→origin mapping 누락으로 FAIL이었다.
- 보정:
  - `publication_allowed`, runtime state, DO_NOT_EXECUTE/NOT_RUN, readback/privacy gate는 machine-contract
    값 우선 예외로 완화할 수 없도록 봉인
  - `REQUESTED→CLIENT_REQUESTED`, `POSITION_SHARED→CLIENT_SHARED`를 명시
  - REQUIREMENT_CHANGED/PIPELINE_FEEDBACK는 기존 client position 전용, REFERENCE_ONLY/NONE은 승격 금지

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열네 번째 V1 formula·navigation 비대칭 보정

- `70fc658aee6ced91c45cd0db2f3e5ddea7d87aefdbfac740dbccc4b0dd7bed42`에서 SOT는 V1 PASS,
  JSON은 FAIL이었다.
- Golden v1이 의도적으로 `CONTRACT_ONLY_NOT_EXECUTABLE`인 점을 결함으로 본 F1은 요구와 정반대여서
  기각했다. Publication 경로는 향후 v2 migration용 계약일 뿐 v1 실행 허용이 아니다.
- 채택한 보정:
  - market row의 formula version을 `market_formula_version`과 `coverage_risk_formula_version`으로 분리
  - JobKorea operator URL에서 `sent_history > position_offer_history`로 가는 navigation 경계 고정
  - 다섯 career source 모두 talent pool/general opening 제외 규칙 적용

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열세 번째 V1 Golden section 완전성 보정

- `8fd922feca60668fca2e70df80209d104bbdf3dc48bd4e86fbad9e79233545fd`에서 SOT는 V1 PASS,
  runtime/Golden JSON은 section/formula 결함 3건으로 FAIL이었다.
- 보정:
  - `마감 후 경보`를 12번째 section이 아닌 `데이터 커버리지.post_cutoff_alerts` collection으로 고정
  - coverage-risk 비대상 lifecycle은 score null, band `UNRANKED`, reason `INELIGIBLE_LIFECYCLE`
  - market/coverage formula version을 각각 `market-accessibility-v2`, `sourcing-coverage-risk-v1`로 고정

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열두 번째 V1 충돌·동률 결정론 보정

- `6c2aaee9f3add9db73a1decba6dd8dbffc7aeb11844e1d8fc086e1a2f640431d`의 SOT 재검토는
  raw 재계산과 snapshot 불일치의 fail-closed 상태가 없음을 material defect로 판정해 FAIL이었다.
- 보정: value/cutoff/evidence hash 중 하나라도 다르면 어느 쪽도 우선하지 않고 영향 셀을
  `null/PARTIAL`, run을 `BLOCKED`로 두며 trend와 publication READY를 금지한다. Reconciliation 뒤에는
  기존 run을 덮지 않고 새 run으로 계산한다.
- event 동률은 `(event_at, recorded_at, pipeline_event_id)` tuple의 lexicographic maximum으로 고정했다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열한 번째 V1 SOT projection 용어 보정

- `3105dae934f7ecdb129468a2855b42a79cc5eeaa8b6e21e769fe8ed1a384d17a`의 SOT 재검토는
  render projection과 외부 enum 용어 3건을 지적해 FAIL이었다.
- 보정:
  - 활성 Pipeline은 8개 active stage 전체, 면접 직전 Pipeline은 그중 2개 stage의 의도적 filtered view로
    정의하고 section 간 중복 row는 합산하지 않도록 명시
  - 잔디밭 근거를 `consultant-focus-v2`의 `YELLOW_ELIGIBLE` evidence로 한정하고 다른 색 계산·덮어쓰기 금지
  - canonical lifecycle `CLOSED`와 ClickUp 외부 terminal status `closedpositions|complete`를 분리

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 열 번째 V1 JSON 계약 완전성 보정

- `63d8b6ba638c5ec4e1d4a72af5270e57c0bfc990afc2151818c3ccf8c23f73d9`에서 SOT는 Claude V1
  PASS였지만 runtime/Golden JSON 조각은 FAIL이므로 전체 V1은 FAIL이다.
- 채택한 보정:
  - 일반 Weekly v1 priority score를 Golden projection에서 제외하고 고객 priority는 관측 evidence로만 제한
  - `INTERNAL_CREATED`를 live/recent client position에서 명시적으로 제외
  - 11개 Golden section 전부에 row/collection schema 추가, 후보자 소싱 세 collection의 section 매핑 고정
  - 시장 점수의 pool/precision 입력 필드와 20명 미달 `UNRANKED`를 명시
  - active candidate 3명 이상을 하나의 0점 coverage-gap bucket으로 고정
  - LinkedIn을 기존 인증 Aside tab으로 제한하고 Codeit cross-domain adapter는 빈 allowlist에서 `NOT_RUN`
  - publication receipt envelope에 target name/ID를 요구
- 해시 자체를 Claude가 재계산할 수 없다는 지적은 검토 입력 봉투의 한계이며 제품 결함으로 채택하지 않았다.
  최종 동일해시는 호출 직전 로컬 hash gate와 fresh Codex V2에서 별도로 검증한다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 아홉 번째 V1 문서 결정론 보정

- `26b0181dadd89546888fb53840c326c25c8bcabb77725b1caa406ed7cb8973cc`에서 Claude V1은
  SOT 내부 의미 충돌 4건을 지적해 FAIL로 판정했다.
- 보정:
  - `interview_pipeline_count`는 4주 KPI이고 별도 상세 section이 아니라는 11-section render 경계를 명시
  - 20명 고정 평가 표본의 분모를 `qualified_sample_size`에서 `evaluated_sample_size`로 개명
  - machine contract 우선 예외를 SOT 3순위와 contract 4순위 사이의 값 충돌로만 제한하고 사용자·AGENTS
    1~2순위는 덮어쓰지 못하게 고정
  - event type `CLOSED`와 destination stage `CLOSED`를 별도 필드로 명시하고 네 terminal stage 모두의
    재활성 event type은 `REACTIVATED`로 고정
- JSON·DDL·reference·검사기·단위시험을 같은 용어로 함께 갱신했다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 여덟 번째 V1 run 상태기계 보정

- `85120675f2cfd4607f387e30cd2405c2975102de74896c353439e51e73a81f2f`에서 SOT와 JSON은
  Claude V1 PASS였지만 SQL 앞부분은 FAIL이므로 전체 V1은 FAIL이다.
- 재현된 결함: `weekly_runs.status`는 다섯 상태를 선언했지만 generic immutable trigger가 모든
  UPDATE를 막아 `DISCOVERED` 이후 상태가 도달 불가능했다.
- 보정: run identity·calendar window·idempotency·lock·created_at은 불변으로 두고 status만 명시된
  전이를 허용했다. DELETE, identity 변경, PUBLISHED 회귀는 계속 차단한다.
- PostgreSQL ephemeral GREEN: `DISCOVERED→PARTIAL→BLOCKED→READY→PUBLISHED`, identity 변경 차단,
  PUBLISHED 회귀 차단을 확인했다. 운영 DB에는 적용하지 않았다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 일곱 번째 V1 권한 계층 보정

- `e81edb99b4ef2d7e7ddf9f5046cde87927f8d97fc4a950d68562a54a5eb2d161`의 첫 SOT 조각은
  `VERDICT: PASS`를 출력했지만 동시에 material finding을 남겼으므로 Strict에서는 FAIL로 처리했다.
- 재현된 결함: 일반 충돌 순위에서는 SOT가 machine contract보다 위였지만 숫자 weight·enum·JSON
  schema의 정본은 machine contract라고 별도로 적어 도메인별 예외가 암묵적이었다.
- 보정: 숫자 weight·enum·JSON schema 값 자체가 충돌할 때는 versioned machine contract를
  우선한다는 예외를 명시하고, 문장 삭제가 `SOT_AUTHORITY_MEANING_DRIFT`로 실패하는 테스트를 추가했다.

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

### 여섯 번째 V1 SQL 반례와 보정

- `988632673ad8eca7d440ee9feb21e551d1ae0ad8ac722869a929cac326fb6650`에서 SOT 4개 완결 조각과
  runtime/Golden JSON은 Claude V1 PASS를 반환했다. SQL 앞부분은 FAIL이므로 이 해시의 전체 V1은
  FAIL이다.
- PostgreSQL에서 재현된 결함:
  - `run_b`의 verified-zero와 weekly metric이 `run_a`의 source snapshot을 evidence로 참조할 수 있음
  - 최초 `CREATED`가 terminal stage로 들어가고, `STAGE_CHANGED`가 terminal에서 active로 되살아날 수 있음
- 재현했지만 결함으로 채택하지 않은 지적:
  - 같은 external task ID가 다른 `hiring_cycle_id`에 나타나는 것은 외부 ID를 identity가 아닌 lineage로
    취급한다는 확정 계약과 일치한다. 외부 ID unique를 추가하면 실제 재채용 cycle을 합칠 수 있어 기각했다.
- 보정:
  - source snapshot에 `(run_id, snapshot_id)` composite key를 추가하고 run-scoped evidence table의 FK를
    같은 run으로 묶었다.
  - pipeline insert guard가 task row lock 아래 앞·뒤 event를 모두 검사한다. 최초 CREATED는 active만,
    active 간 이동은 STAGE_CHANGED, terminal 진입은 CLOSED, terminal 복귀는 REACTIVATED만 허용한다.
- PostgreSQL ephemeral GREEN:
  - cross-run zero/metric evidence 차단
  - terminal CREATED와 terminal→active STAGE_CHANGED 차단
  - CREATED→STAGE_CHANGED→CLOSED→REACTIVATED 정상 전이와 current state 확인
  - 임시 DB 정리, 운영 DB 접근 없음

→ 새 artifact hash에서 전체 gate와 Claude V1/fresh Codex V2를 다시 수행하기 전에는 Strict 완료나
checkpoint 근거가 아니다.

## 2026-09-04 REQUEST_CHANGES 해소 run — PII 3층 우회 보정

### fresh 재검증 (착수 증거)

- HEAD `3b389fdee994a76fe3b38d73d845126c5f8276cd`, 미커밋 22파일, 착수 시 tracked diff
  SHA-256 `806d22f8ee3fc92bb3d75bb29ea222577416542fc09afb4b3d68556760718e67`.
- ① 키 우회 재현: PII 후보 키 14종(email, phone, ssn, jumin, kakao_id, resume_url,
  profile_url, linkedin_url, name_ko, 이름, 연락처, 전화번호, 주소, 생년월일)을 position에
  주입해도 오류 0건 — 열거식 `FORBIDDEN_KEYS`가 전부 놓쳤다.
- ② 값 우회 재현: LinkedIn/GitHub 프로필 URL 값, 전각 ＠ 이메일, 전각 숫자 전화,
  주민등록번호(900101-1234567), 문자열화 JSON 내 name 값, 국제전화(+1 415 …) 7종 전부
  `FORBIDDEN_SENSITIVE_VALUE` 미검출.
- ③ 렌더링 후 무방비 재현: `render_brief` 출력에 합성 이메일·전화를 주입해도 verdict
  PARTIAL 유지, errors 0건, PII가 `brief_markdown`에 그대로 남았다.
- 부채: SOT-30 §4.5 R4가 참조하는 `docs/sot/31-strict-recurrence-ledger.md`는 이 저장소에
  실존하지 않는다(팬텀 참조). 원장 인용 불가 — 부채 행은 이 goal에 기록하고 원장 신설은
  별도 작업으로 넘긴다.

### 입력 영역 표 (WU-1, 결정성 규율 ①)

입력 = `weekly-ops-input-v1` 발행 번들 JSON 전체(명시 인자). 암묵 입력 없음(시계·DB·설정
미사용, 순수 함수 게이트). 각 오브젝트는 아래 정확 키 허용목록으로 닫힌다.

| 오브젝트 | 허용 키(정확 집합) |
|---|---|
| bundle 최상위 | schema_version, run, capabilities, source_snapshots, operating_snapshot, dedupe_decisions, positions, career_page_summaries, consultant_roster, outreach_channel_diagnostics, outreach_events, zero_result_assertions, publication_targets |
| run | meeting_at, window_start, window_end_exclusive, late_alert_end |
| capabilities[] | name, status, required |
| source_snapshots[] | snapshot_id, source_system, source_uri_ref, fetched_at, status, content_hash, evidence_refs |
| positions[] | canonical_id, company, title, category, origin, intent, event_at, deadline_days, late_stage, client_priority, lifecycle, difficulty, evidence_refs, action |
| positions[].difficulty | scarcity, seniority, constraints, funnel_friction |
| dedupe_decisions[] | decision_id, kept_canonical_id, removed_source_refs, reason, rule_version |
| career_page_summaries[] | company, official_url, status, active_requisitions, talent_pools, freshness_at, limitation, source_snapshot_id |
| consultant_roster[] | consultant_id, consultant_display, provider_accounts{jobkorea, saramin, linkedin_rps} |
| outreach_channel_diagnostics[] | channel, access_state, surface_kind, surface_ref, stable_receipt_available, covered_provider_actor_refs, source_snapshot_id, blocker_reason |
| outreach_events[] | event_id, consultant_id, consultant_display, position_id, channel, status, sent_at, candidate_key_hmac, provider_actor_ref, provider_receipt_ref, source_snapshot_id, provider_seat_ref, provider_project_ref |
| zero_result_assertions[] | collection, rule_version, source_snapshot_id, provider_receipt_ref, observed_count |
| publication_targets[] | name, target_id, required, status + READBACK 8필드(write_ahead_intent_id, idempotency_key, schema_readback_ref, external_object_id, receipt_id, receipt_persisted_ref, report_snapshot_id, content_hash) |
| operating_snapshot | 기존 `operating_gate` 정확 키 집합과 동일(source_snapshot_id, meeting_date, generated_at, timezone, provenance, count_semantics, closed_week{10}, current{4, funnel 6}, targets{9}) |
| **그 외 전부** | **FORBIDDEN_UNKNOWN_FIELD 명시적 거부(fail-closed catch-all)** |

스칼라 자리(허용 키의 값)에 dict/list가 오는 것도 미지 구조로 거부한다. 필수 여부·타입
검증은 기존 validator가 담당하고, 이 표는 "허용되지 않은 키·구조의 존재"만 차단한다.

### 결정 목록 (WU-1·2·3, 결정성 규율 ②)

- 미허용 키 오류는 bare 코드 `FORBIDDEN_UNKNOWN_FIELD`로만 출력한다 — 키 이름 자체가
  PII일 수 있어 출력에 에코하지 않는다(fail-closed).
- `{`로 시작하고 JSON object로 파싱되는 문자열 값은 무조건 차단한다(이 계약에 정당
  사용례 없음). `[` 시작은 차단하지 않는다 — `count_semantics` 값이 `[week_start, …`로
  시작하는 정당 사례가 있어 패턴 검사로만 폴백한다.
- 주민등록번호 패턴이 64-hex 해시 내부의 우연한 13숫자 연쇄와 일치할 확률은 입력당
  약 1e-4 수준 — 잔여 위험으로 수용하고 오탐 발생 시 원장으로 승격한다.
- candidate_display_name: `docs/sot/weekly-ops-contract.md`의 "canonical input·Git·email·
  admin_web·logs·hashes·receipts·exceptions·review_bundle 금지, 실행 가능한 Golden v2
  계약 아래 사용자 승인 private Notion detail에서만 보호된 resolver로 해석" 계약과
  이 게이트의 차단 범위(canonical input)는 충돌하지 않는다 — 게이트는 resolver 경로가
  아니라 canonical input만 본다 (WU-1 절차 ④ 확인).
- substring 매칭 금지 준수: 키는 정확 허용목록, 값은 인용부호+콜론 경계가 있는 토큰
  패턴과 도메인 경계가 있는 URL 패턴만 사용한다. `metric_name`·`target_name` 등 정당
  키가 `name` substring으로 오탐되지 않음을 표본 12종으로 고정한다.
- 렌더링 후 재검사 실패 시 산출물은 payload를 비운 BLOCKED 결과로 대체한다
  (`FORBIDDEN_SENSITIVE_OUTPUT`) — blockers 문자열도 입력 유래 값이므로 함께 비운다.

### 표↔테스트 대응 (③)과 R9 편입 위치

- WU-1: `tests/weekly_ops/test_weekly_gate_adversarial.py` — PII 후보 키 14종 주입 차단,
  미열거 신규 키 차단(최상위·position·outreach event·publication target), 정당 키 오탐 0건
  표본(position_id, hiring_cycle_id, candidate_key_hmac, list_url, official_url, operator_url,
  notion_parent_url, search_url_ref, metric_name, risk_name, target_name,
  display_name_similarity).
- WU-2: `tests/weekly_ops/test_weekly_gate_pii_values.py`(신규) — Codex 반례 6종 회귀
  (candidate_alias·candidateDisplayNameV2 키, 프로필 URL 값, 전각 ＠, 비한국 전화,
  주민번호, 문자열화 JSON) + 정당 값(official_url, allowlist 이메일 target_id) 오탐 0건.
- WU-3: 같은 신규 파일 — renderer 주입 시 `FORBIDDEN_SENSITIVE_OUTPUT` + payload 소거,
  acceptance mutation(renderer 합성 PII 주입, 최종 재검사 우회, 입력 스키마 fail-open) 3종.
- 자유문 `action`의 임의 한국어 실명(합성 이름) 반례는 정규식으로 원천 차단 불가 —
  아래 결정 카드로 사용자 결정 대기, 이 goal에 부채 행으로 기록(R9 대체 경로).

### RED에서 추가 발견한 반례 (2026-09-04)

- `positions[].evidence_refs`에 dict를 섞으면 `validate_positions`의 set membership 검사
  (`weekly_gate.py`)가 unhashable TypeError로 crash한다 — 이름 있는 FAIL이 아니라 예외
  종료. `test_structures_hidden_under_scalar_slots_fail_closed`가 회귀로 고정하며, 보정은
  ref 타입 가드 + 스키마의 미지 구조 거부 두 겹이다.

### WU-3 구현 중 결정 (2026-09-04)

- 오염된 publication target(`target_id`가 dict)은 이전에는 receipts로 그대로 에코됐다.
  최종 재검사 도입 후에는 산출물 전체가 소거된 BLOCKED 결과로 대체된다 — 기존 테스트
  `test_non_string_publication_target_fails_closed_without_exception`의 기대를 "오류 코드
  유지 + publication_report/receipts 소거"로 갱신했다(검증 강화, 약화 아님).
- 최종 재검사 실패 시 stdout 산출물도 `find_sensitive_text`로 한 번 더 검사해 markdown/
  html/json 어느 형식으로도 PII가 프로세스 밖으로 나가지 않는다.

### 결정 카드 — 자유문 action 필드의 실명 잔여 위험 (사용자 결정 대기)

1. 문제: `positions[].action` 자유문에 임의 한국어 실명이 들어오면 패턴으로 차단 불가.
2. 선택지 A: action을 구조화 템플릿(고정 동사구 enum + 대상 참조)으로 제한 — 잔여 위험
   제거, 표현력 손실.
3. 선택지 B: 자유문 유지 + 잔여 위험 수용(이메일·전화·주민번호·URL 패턴은 차단됨) +
   운영 리뷰에서 육안 확인.
4. 영향: A는 renderer·계약·기존 테스트 문구 변경 필요, B는 변경 0.
5. 결정 전까지 필드는 그대로 유지한다(임의 제거 금지) — 기본 동작은 B와 동일.

### 2026-09-04 fresh Codex V2 1차 결과와 보정

- V2 artifact: `.omx/artifacts/codex-v2-pii-3layer-20260904.md` (검토 대상 HEAD
  `d822c145e399ab2d78832cb21dcffda055533014`, branch diff
  `2ed74eb5c324014e107e03f9091173c388083d4b173da4d561d958e7e1e5fa57`) — verdict `FAIL`.
- 1차 실행은 cyber 정책 필터로 빈 출력(무효 처리), 컴플라이언스 리뷰 표현으로 재실행해
  판정 본문을 확보했다. Codex 샌드박스에서 임시 디렉터리 필요 테스트 1건은
  sandbox-limited로 분리 보고됐다.
- 채택·보정(같은 PR 회귀 편입, R9): 따옴표 로컬파트 이메일, 슬래시 구분 전화·주민번호,
  괄호 국제전화, 포트 붙은 github URL, 중간 삽입 camelCase/한국어 키 문자열화 JSON,
  `+1 234 567건` 증감 표기 오탐(국제전화 패턴 3그룹 강제), allowlist 이메일이 main JSON
  출력 재검사에서 오차단되던 결함(정확 값 마스킹 후 검사), tuple/set 컨테이너의 스키마
  걷기 통과, main 종단(e2e) 테스트 부재.
- 기각(의도된 과차단 — 발행 게이트에서 과차단은 안전 방향): github 저장소 URL·
  linkedin company URL 차단 유지(`/company/` 예외는 경로 조작으로 우회 가능),
  `설정 예시: {"name": …}` 문자열 차단 유지, 유사날짜 사업 ID(990231-…) 차단 유지.
- V2의 "정당 키 12종 표본은 denylist 비매칭만 증명" 지적에 대한 해석 확정:
  hiring_cycle_id 등 9종은 DB/Golden 계층 키로 v1 입력 허용목록에 의도적으로 없다.
  "오탐 0건"은 PII 분류기·값 검사 수준의 계약이며, 스키마 밖 거부는 오탐이 아니라
  fail-closed 계약 이행이다. v1 입력·출력에 실재하는 position_id·candidate_key_hmac·
  official_url·target_name은 수용 테스트로 증명한다.
- 보정 후 fresh GREEN: 단위 139 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 64` exit 0(mutation 31종 생존 0), verify.sh PASS.

### 2026-09-04 fresh Codex V2 2차 결과와 보정

- V2 2차 artifact: `.omx/artifacts/codex-v2-pii-3layer-round2-20260904.md`
  (검토 대상 HEAD `12cfcd45759d3a8af1ec7c256f1f42e517b71ea9`) — verdict `FAIL`.
  1차 반례 7종은 전부 닫힌 것으로 독립 재현·확인됐다.
- 채택·보정(R9 회귀 편입): allowlist 이메일 substring 마스킹이
  `sangmokang@valueconnect.kr.evil.com` 을 통과시키던 우회(경계 lookaround re.sub로 교체),
  공백 든 따옴표 이메일, 한글 IDN 이메일(유니코드 이메일 패턴), 괄호 지역번호
  `(02) 123-4567`, 주민번호 성별 자리 1-8 확장·공백-하이픈 구분, main 최종 문자열 검사의
  격리 반례(render_html 주입 e2e 테스트) + 전용 acceptance mutation
  (stdout-rescan-bypass) 신설.
- 기각(의도된 과차단 유지): `+1 234 567 890건` 4그룹 증감 표기 — 실제 국제전화와
  구조적으로 동일해 구분 불가. 진짜 전화 뒤에 한글 조사가 오는 경우를 예외로 두면
  우회 구멍이 되므로 차단 유지(콤마 표기 시 통과). 날짜코드+7자리 수 병기 유사 사례도
  같은 방향의 잔여 과차단으로 수용.
- 보정 후 fresh GREEN: 단위 142 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 65` exit 0(mutation 32종 생존 0), verify.sh PASS, clean.

### 2026-09-04 fresh Codex V2 3차 결과와 보정

- V2 3차 artifact: `.omx/artifacts/codex-v2-pii-3layer-round3-20260904.md`
  (검토 대상 HEAD `150606762772a3deb336a6f837a5756feb4ffa60`) — verdict `FAIL`.
  2차 반례는 5/5 값·2/2 주입 전부 닫힘으로 독립 재현·확인, 정당 fixture 18/18 통과 확인.
- 채택·보정(R9 회귀 편입): 따옴표+IDN 이메일(`"홍 길동"@예시.한국`), punycode TLD
  이메일, 공백-하이픈 지역번호 `(02) 123 - 4567`, 내선 확장 전화 `010-1234-5678x123`,
  그리고 allowlist 이메일 마스킹의 문맥 무시(HTML 주입도 마스킹) 결함 — 마스킹을
  json 형식(구조적 target_id 예외의 직렬화 표면)에만 제한. HTML/Markdown에 allowlist
  이메일이 등장하면 이제 차단된다.
- 잔여 위험 기록 확장: 전화 패턴이 16진수 해시 안의 8자리 이상 연속 숫자와 우연히
  일치할 확률(해시당 수 % 수준, 원 코드 시절부터 존재)은 RRN-in-hex와 같은 계열의
  수용 위험으로 두고, 운영 관측 항목(BLOCKED 오탐 모니터링)으로 승격 대상.
- 보정 후 fresh GREEN: 단위 144 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 65` exit 0(mutation 32종 생존 0), verify.sh PASS, clean.

### 2026-09-04 fresh Codex V2 4차 결과와 보정

- V2 4차 artifact: `.omx/artifacts/codex-v2-pii-3layer-round4-20260904.md`
  (검토 대상 HEAD `cc193d5c82912282c6db9eb250eae124dd25d3ab`) — verdict `FAIL`.
  3차 반례는 5/5 차단으로 독립 재현·확인.
- 채택·보정(R9 회귀 편입): 이메일 발행 대상의 수신자 allowlist가 구조적으로 강제되지
  않던 결함 — `publication_state`가 name=email이면 target_id의
  `ALLOWED_EMAIL_TARGETS` 정확 일치를 요구하고 위반 시 `EMAIL_TARGET_NOT_ALLOWLISTED`
  (fixtures의 email target_id도 허용 주소로 교체). 도메인-리터럴 이메일
  (`user@[192.0.2.1]`) 패턴, 검사 전 공백 연쇄 정규화(다중 공백 구분 전화),
  FQDN 끝점 프로필 URL(`linkedin.com./in/...`).
- 보정 후 fresh GREEN: 단위 146 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 65` exit 0(mutation 32종 생존 0), verify.sh PASS, clean.

### 2026-09-04 fresh Codex V2 5차 결과와 보정

- V2 5차 artifact: `.omx/artifacts/codex-v2-pii-3layer-round5-20260904.md`
  (검토 대상 HEAD `1617beca0119fe6ec0398a0d79ea467651d67115`) — verdict `FAIL`.
  4차 반례 3/3 차단·allowlist 강제 2/2 재현·정당 fixture 통과 확인.
- 채택·보정(R9 회귀 편입): IPv6 도메인 리터럴 이메일(`user@[IPv6:2001:db8::1]`),
  RFC atext 특수문자 로컬파트(`user!@example.com`), 가변 그룹 국제전화
  (`+33 1 42 68 53 00` — 1~4자리 그룹 4~6개 대안 추가, 기존 3그룹 규칙과 병행,
  `+1 234 567건` 오탐 가드 테스트는 그대로 GREEN).
- 보정 후 fresh GREEN: 단위 147 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 65` exit 0(mutation 32종 생존 0), verify.sh PASS, clean.

### 2026-09-04 fresh Codex V2 6차 결과와 보정

- V2 6차 artifact: `.omx/artifacts/codex-v2-pii-3layer-round6-20260904.md`
  (검토 대상 HEAD `4f5146e6088697565d8defbcda5873776336c8f7`) — verdict `FAIL`.
  4·5차 반례 6/6 차단·allowlist 강제 2/2 재현 확인.
- 채택·보정(R9 회귀 편입): 따옴표 로컬파트 안의 `@`(`"john@doe"@example.com` —
  qcontent 허용), 한 자리 지역번호 국제전화(`+82 2 1234 5678`, `+81 3 1234 5678` —
  1~2자리 지역 그룹 + 3~4자리 그룹 2개 대안). `+1 234 567건` 오탐 가드 GREEN 유지.
- 보정 후 fresh GREEN: 단위 148 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 65` exit 0(mutation 32종 생존 0), verify.sh PASS, clean.

### 2026-09-04 fresh Codex V2 7차 결과와 보정

- V2 7차 artifact: `.omx/artifacts/codex-v2-pii-3layer-round7-20260904.md`
  (검토 대상 HEAD `15d04ed7a74044e50b20f472c5ea44332ea876a0`) — verdict `FAIL`.
  4~6차 반례 11건 차단 재현 확인.
- 채택·보정(R9 회귀 편입): 구조화 이름 JSON(`{"firstName":…,"lastName":…}` —
  임베디드 키 토큰에 first/last/given/family/middle/sur/nick name·성 추가),
  프로필 URL 정책을 호스트 열거에서 **승인 호스트 allowlist(fail-closed)**로 반전 —
  http(s) URL은 승인 9개 호스트 밖이면 전부 차단(behance·gitlab 포함 미지 호스트 일괄).
  스킴 없는 표기는 확장된 프로필 호스트 목록이 2차 방어.
- 결정: 신규 정당 호스트는 `APPROVED_URL_HOSTS` 갱신이 필요(키 allowlist와 같은
  의도된 마찰). 스킴 없는 미지 호스트 표기(`example.com/x`)는 잔여 위험으로 기록.
- 보정 후 fresh GREEN: 단위 149 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 65` exit 0(mutation 32종 생존 0), verify.sh PASS, clean.

### 2026-09-04 fresh Codex V2 8차 결과와 보정

- V2 8차 artifact: `.omx/artifacts/codex-v2-pii-3layer-round8-20260904.md`
  (검토 대상 HEAD `313ef0f79d983db56884769e9615f342d54faf78`) — verdict `FAIL`.
  4~7차 반례 15/15 값·2/2 수신자 차단 재현 확인.
- 채택·보정(R9 회귀 편입): 문장 마침표가 붙은 이메일(`…@example.com.` — 종결 경계를
  단어문자/도메인 연속만 배제하도록 수정), 괄호 국가번호(`(+33) …`)와 `00` 국제 접두
  전화, `contactName` 등 contact 계열 구조화 키 토큰.
- 보정 후 fresh GREEN: 단위 150 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 65` exit 0(mutation 32종 생존 0), verify.sh PASS, clean.

### 2026-09-04 fresh Codex V2 9차 결과와 보정

- V2 9차 artifact: `.omx/artifacts/codex-v2-pii-3layer-round9-20260904.md` (검토 대상 HEAD
  `9f99627367df22975f344d2dd89283cecf81f5c5`, diff hash
  `cedeb788327b023b62c35253d6c53cbe62304ba83bf598ebaccaa33b070dd7d5`) — verdict `FAIL`.
  1~8차 반례 표본(라운드당 대표 1건 이상, 총 15건)은 전부 독립 재현으로 CLOSED 유지 확인.
- 신규 반례: 국가번호(+/00) 없는 북미식(NANP) 국내 전화번호 형식
  `(415) 555-2671` / `415-555-2671` / `415.555.2671`이 `contract_gate.py`의
  `PHONE_PATTERN`(한국식 전용)과 `INTL_PHONE_PATTERN`(+/00 요구)을 모두 통과해
  입력 게이트와 최종 렌더링 재검사 양쪽에서 JSON/Markdown/HTML로 그대로 발행됐다
  (`weekly_gate.py` main 종단 재현, exit 0, 값 포함 확인).
  file:line — `contract_gate.py:52`(한국 전용), `contract_gate.py:83`(국가번호 필수).
- 채택·보정(R9 회귀 편입): `NANP_PHONE_PATTERN`(`\(?[2-9]\d{2}\)?[-. ][2-9]\d{2}[-. ]\d{4}`,
  경계 lookaround 포함)을 `find_sensitive_text` 판정에 추가.
  `test_codex_v2_round9_false_negative_formats_are_blocked` 3종 회귀 추가, RED 확인 뒤
  최소 구현으로 GREEN 전환. 기존 정당 값(날짜·업무 수치·해시 등)과 자릿수 경계가
  겹치지 않음을 `test_legitimate_values_have_zero_false_positives`,
  `test_business_delta_notation_is_not_an_intl_phone` 재통과로 확인.
- RED 커밋 `3634a10`, GREEN 커밋 `5bf1896`(fresh HEAD
  `5bf18966d5a6b9fe53e0827e0d77a14d86784a5c`).
- 보정 후 fresh GREEN: 단위 151 tests OK, sot_gate `CHECKED: 89` exit 0, acceptance
  `CHECKED: 65` exit 0(mutation 32종 생존 0), verify.sh PASS, clean. 새 tracked diff hash
  `3e7a608956472b9681279308f4e805ce382f33809640f3b2318bff2b6a87a112`.

### 2026-09-05 codeaudit 자기 검증 — 9차 보정의 불완전성과 사장님 수용 결정

- `/codeaudit`+`/humanreview` 관점으로 9차 GREEN 커밋(`5bf1896`)을 읽기 전용으로
  재검증한 결과, `NANP_PHONE_PATTERN`(`contract_gate.py:52`)이 그룹 사이 구분자를
  전부 **필수**로 요구해 다음 두 형식이 여전히 입력·출력 게이트를 통과해 발행됨을
  실행으로 확인했다: 괄호 뒤 공백 없는 `(415)555-2671`, 구분자가 전혀 없는
  `4155552671`. `evaluate()` 종단 재현: `verdict=PASS`, `brief_markdown`에 값 포함.
  기존 한국식 `PHONE_PATTERN`은 구분자가 전부 선택(`?`)이라 `01012345678`(구분자
  없음)도 잡는 것과 설계가 불일치했다(대조 재현 완료).
- 사장님 결정(2026-09-05, 실시간 지시): 이 구멍은 지금 고치지 않는다("이건
  넘어가"). 결정 카드 목록의 "의도된 과차단/잔여 위험" 항목과 같은 성격의
  **명시적 owner 수용 잔여 위험**으로 취급하고, 임의로 만료일을 붙이거나 기본
  유예로 처리하지 않는다 — 실시간 owner 승인이 근거다.
- 남은 부채: `docs/sot/31-strict-recurrence-ledger.md`가 아직 없어(결정 대기 #2)
  이 항목을 정식 원장 행으로 옮기지 못했다. 원장이 생기면 이 절을 그 행으로
  이관한다. 그 전까지는 이 goal 문서가 유일한 기록이며, 향후 fresh Codex V2가
  같은 구멍을 다시 지적하면 "신규 결함"이 아니라 "이미 owner가 수용한 잔여
  위험"으로 분류하고 재수정 루프를 돌리지 않는다.
- 코드 변경 없음(읽기 전용 감사) — HEAD·diff hash는 8a6516d 라운드와 동일하게
  유지된다.

### 2026-09-05 humanreview/codeaudit 재개 — 이전 위험 수용 폐기 및 검사기 자기포함

- 최신 사용자 지시는 `$humanreview $codeaudit`로 문제를 검증한 뒤 **문제를 해결**하라는
  것이다. 따라서 바로 위 절의 compact NANP 형식 위험 수용은 현재 실행 범위에서는
  폐기한다. 개인정보 발행 차단은 strict 불변조건이므로 유예 가능한 운영 부채로
  남기지 않는다.
- RED: `(415)555-2671`, `4155552671`을 기존 round9 회귀 검사에 추가하자 같은 두 값이
  모두 `PASS`로 재현됐다. 잘못된 작업 디렉터리에서 최초 실행한 import 실패는 기능
  증거에서 제외하고, `tests/weekly_ops`에서 다시 실행해 2 failures를 확인했다.
- GREEN: `NANP_PHONE_PATTERN`의 괄호 뒤·숫자 그룹 사이 구분자를 선택으로 바꾸고,
  영숫자 경계는 유지했다. round9 privacy, 정당 값 오탐, 업무 증감 표기 회귀가 함께
  통과했다. RED 커밋 `3d3f045`, GREEN 커밋 `1a39d95`.
- 추가 공격 감사에서 `scripts/acceptance-weekly-ops-skill.sh`가 628줄이면서도 기존
  600줄 파일 상한 검사의 대상에서 자기 자신을 제외한다는 false-PASS를 발견했다.
  전용 검사 `test_weekly_code_budget.py`를 먼저 추가해 628줄로 실패시킨 뒤, 빈 줄 정리와
  기존 표현 결합만으로 shell을 599줄로 줄이고 tracked required-file 목록에 새 검사를
  연결했다. RED 커밋 `750663a`, GREEN 커밋 `3dab69d`.
- fresh 단위시험: 152 tests, exit 0, `OK`.
- fresh Weekly full acceptance: `CHECKED: 66`, exit 0. 필수 파일·Golden 계약·SOT 연결·
  코드 예산·단위시험·32개 mutation이 모두 통과했다.
- fresh 임시 PostgreSQL 진실표: 운영 DB와 분리한 임시 클러스터에서 DDL을 처음부터
  적용해 `CHECKED: 49`, exit 0. 임시 클러스터는 종료·삭제했다.
- fresh 보조 게이트: principles `CHECKED: 34`, Weekly SOT `CHECKED: 89`, secret scan
  PASS, `git diff --check` PASS.
- 남은 병합 차단: upstream `251c341..3dab69d`의 tracked diff는 6,038 insertions +
  321 deletions = 6,359줄이다. `coding-principles.md` P11의 PR 3,000줄 절대 상한을
  초과하므로 현재 브랜치를 단일 PR로 병합할 수 없다. 사용자 승인 없는 히스토리
  재작성·push·PR 생성은 수행하지 않는다.
- Golden v2 실행 엔진과 외부 Notion/Gmail/ClickUp/admin-web 게시 상태는 여전히
  `NOT_RUN`이다. 현재 검증은 Weekly SOT/계약/게이트 구현의 일관성을 증명하며,
  Golden Sample 게시 완료를 의미하지 않는다.
