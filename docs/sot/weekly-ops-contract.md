# Valuehire v6 — Weekly Ops 업무 정본

최종 갱신: 2026-09-01

## 결론

이 문서는 Weekly 브리핑과 Notion Golden Sample이 무엇을 세고, 무엇을 세지 않으며, 누가 판단할
수 있는지를 정하는 영구 정본이다. 현재 일반 Weekly v1 경로는 존재하지만 Golden v1은 실행기가
없는 문서 계약이므로 실제 Golden 발행은 준비되지 않았다.

> **무엇을** — Weekly 업무 불변조건은 이 문서, 타입·enum·수식은 versioned machine contract, 사건 기록은 날짜가 붙은 goal에 둔다.
> **왜** — 규칙과 구현 상태를 섞으면 문서에 hook 이름이 있다는 이유만으로 발행 가능한 것처럼 보이기 때문이다.
> **버린 길** — 기존 Golden 참고 문서를 그대로 영구 정본으로 승격하는 방법은 과거 결함과 표현까지 규칙으로 굳히므로 사용하지 않는다.
> **대가** — Golden v2 실행기와 검사가 생기기 전에는 일부 요청이 NOT_RUN으로 끝난다.
> **되돌리기** — 이 문서와 Skill·검사 참조를 함께 revert한다. 운영 데이터와 외부 페이지에는 변화가 없다.

## 권한과 정본 우선순위

충돌할 때는 다음 순서로 판단한다.

1. 사용자가 현재 요청에서 명시한 대상·행동·금지사항
2. 저장소 최상위 `AGENTS.md` 또는 세션에 주입된 동일 계약
3. 이 `docs/sot/weekly-ops-contract.md`
4. `contracts/weekly-ops/`의 versioned machine contract
5. `.agents/skills/weekly-ops/SKILL.md`와 references
6. `docs/engineering/*weekly*goal*.md`의 날짜별 사건·검증 기록

위 순위는 이미 허용된 범위 안에서 대상·행동·표현이 충돌할 때만 적용한다. 어떤 우선순위 층도
publication·execution·privacy·credential·legal gate를 완화할 수 없다. 완화 지시나 계약이 들어오면
그 부분은 적용하지 않고 `BLOCKED` 또는 `NOT_RUN`으로 남긴다.

이 문서는 업무 의미와 불변조건의 정본이다. Versioned machine contract는 이 문서가 이름과 version만
위임하고 값을 반복하지 않은 타입·enum·수식·JSON schema의 실행 정본이다. 두 표면이 같은 숫자 weight,
enum 또는 schema 값을 모두 명시하면 반드시 동일해야 한다. 값 충돌은 machine contract의 우선권이
아니라 drift이며 위 순서대로 이 문서가 우선한다. `docs/engineering/`은 당시 판단과 증거를 보존하는
기록이지 현재 규칙을 덮어쓰는 정본이 아니다.

Machine contract는 `publication_allowed`, Golden runtime state, `DO_NOT_EXECUTE`, `NOT_RUN`,
readback·privacy gate 같은 안전·실행 가능성을 완화할 수 없다. 허용 집합을 넓히거나 배제를 줄이거나
identity·origin·intent mapping·evidence·status·count eligibility를 바꾸면 값 유형이
숫자·enum·schema여도 drift로 실패한다.

LLM은 사실을 요약하고 허용된 evidence enum을 제안할 수 있다. LLM이 포지션 실행 여부, 경영
우선순위, 점수, 상태, 중복 identity를 결정할 수 없다.
일반 Weekly v1의 `client_priorities`, `score_version`, `score_points`는 Golden projection 입력에서
제외한다. 고객이 직접 밝힌 priority는 관측 evidence일 뿐 Golden의 실행 우선순위 점수가 아니다.

## 현재 구현 상태

| 표면 | 현재 상태 | 허용 범위 |
|---|---|---|
| 일반 Weekly v1 | 실행기와 단위시험 존재 | 기존 evidence bundle의 일반 브리핑 계산 |
| Notion Golden v1 | `CONTRACT_ONLY_NOT_EXECUTABLE` | 계약 회수·감사만 가능 |
| Notion Golden v2 | 미구현 | contract·callable·runtime·mutation이 모두 생기기 전 사용 금지 |
| Golden 외부 발행 | `NOT_RUN` | 실제 publisher와 write-ahead·readback이 모두 검증될 때까지 금지 |

→ 문서 계약의 존재는 제품 기능의 존재가 아니다. Golden v1의
`publication_allowed=false`가 해제되거나 v1 hook 문자열만 호출 가능한 것으로 취급되면 정본 위반이다.

Golden 요청은 다음 tracked regular file이 모두 존재할 때만 실행 준비를 다시 판정한다.

- `contracts/weekly-ops/notion-golden-sample-v2.json`
- `.agents/skills/weekly-ops/scripts/golden_v2_registry.py`
- `.agents/skills/weekly-ops/scripts/golden_v2_cli.py`
- `.agents/skills/weekly-ops/scripts/golden_v2_publisher.py`
- `tests/weekly_ops/test_golden_v2_runtime.py`
- `scripts/acceptance-weekly-golden-v2.sh`

Manifest는 위 callable·CLI·publisher의 module path와 SHA-256, readback schema version을 exact 값으로
가져야 한다. `bash scripts/verify/run-acceptance.sh scripts/acceptance-weekly-golden-v2.sh`가 exit 0,
`PASS`, 양수 `CHECKED`를 모두 내고 해당 hash들이 run evidence에 묶여야 readiness를 재판정한다.
Caller의 "v2가 있다"는 문장이나 임의 path 주장은 이 gate를 충족하지 못한다. 하나라도 없거나
불일치하면 `DO_NOT_EXECUTE`, `NOT_RUN`이다. 일반 Weekly v1의 `render_brief()`를 Golden renderer라고
이름만 바꿔 사용하는 것도 금지한다.

## 보고 주차와 4주 데이터

보고 달력 version은 `valuehire-report-calendar-v1`이다.

- `report_week_label`: 회의 시각이 속한 ISO week-year/week를 `FY{yy}W{ww}`로 표시한다.
- 4주 KPI row의 `week_label`은 위 report slot label이고, `metric_iso_week`는 해당 row의
  `metric_window_start`가 속한 ISO week다. FY26W36 row의 닫힌 데이터는 FY26W35일 수 있으며 두 값을
  서로 대입하거나 같은 뜻의 `iso_week`로 축약하지 않는다.
- `metric_window_end_exclusive`: `meeting_at`이 속한 ISO week의 현지 Monday 00:00이다.
- `metric_window_start`: `metric_window_end_exclusive - 7 days`다. 따라서 window는 회의 전에 완전히
  닫히고 `window_end_exclusive <= meeting_at`이다. Monday 00:00 회의도 방금 시작한 주가 아니라 직전
  7일을 센다.
- 모든 timestamp는 지정 timezone이 있는 ISO-8601이어야 한다.
- window는 7일 half-open interval `[start, end)`이다.
- DB run 자체가 `window_end_exclusive = window_start + 7 days`와 KST meeting ISO week의 Monday
  00:00 정렬을 강제한다. 하위 receipt가 잘못된 run window를 정본으로 삼을 수 없다.
- 4주 표는 정확히 네 개의 연속 window를 사용한다.
- 현재 report의 닫힌 metric window는 raw event로 계산한다. 회의가 속한 진행 중 calendar week를 세지 않는다.
- 과거 주는 같은 형식의 raw history 또는 immutable VERIFIED snapshot만 사용한다.
- 과거 run의 immutable VERIFIED metric snapshot을 사용할 때는 그 hash·cutoff·evidence URI를 묶은
  새 current-run source snapshot을 먼저 캡처한다. Metric cell은 이 current-run snapshot ID만 참조하고
  과거 run의 snapshot ID는 lineage metadata일 뿐 직접 FK/evidence가 아니다.
- 과거 VERIFIED non-zero 값은 위 current-run lineage capture로 보존할 수 있다. 과거 VERIFIED zero는
  과거 zero-result receipt를 복사해 VERIFIED로 승격하지 않는다. 동일 과거 window의 provider raw
  history를 현재 run에서 다시 완전 조회하고 `PASS` source snapshot과 새 `weekly-zero-result-v1`
  receipt를 만들었을 때만 VERIFIED zero다. 재조회하지 못하면 값은 null, status는 `PARTIAL`이다.
- 현재 상태를 과거 네 주에 복사하지 않는다.
- raw 계산과 snapshot이 함께 있으면 value, cutoff, evidence hash가 모두 같아야 한다. 하나라도 다르면
  어느 쪽도 우선하지 않고 영향 셀은 `value=null,status=PARTIAL`, run은 `BLOCKED`로 기록한다. 해당
  metric의 trend와 publication `READY`를 금지하고 reconciliation evidence가 생긴 뒤 새 run으로 계산한다.
- Outreach reconciliation의 provider receipt identity는 run을 넘어 `(channel, provider_receipt_ref)`로
  유일하다. 새 run은 같은 receipt를 복제하지 않고, target run의 window와 meeting cutoff 안에 있는
  기존 immutable PASS-backed send fact와 새로 발견한 send fact를 함께 재집계한다. 따라서 새 run의
  focus와 outreach 수치는 `send.run_id = current_run_id`로 제한하지 않는다.
- 미확인 주차는 0이 아니라 `—`, `PARTIAL`, `NOT_RUN`으로 표시한다.
- trend는 네 점 중 최소 세 점이 VERIFIED일 때만 표시한다.

FY26W36 예시는 보고 라벨과 집계 창의 차이를 설명하는 고정 사례다.

- report week: `FY26W36`
- metric window: `[2026-08-24T00:00:00+09:00, 2026-08-31T00:00:00+09:00)`

각 metric cell은 최소 다음을 가진다.

- non-negative integer 또는 null인 `value`
- `VERIFIED|PARTIAL|NOT_RUN` status
- `as_of`
- `source_snapshot_id`
- `evidence_refs`
- VERIFIED zero일 때 `weekly-zero-result-v1` receipt

VERIFIED cell의 source snapshot status는 반드시 `PASS`다. `PARTIAL|FAIL|NOT_RUN|STALE` source는
숫자 0을 포함한 어떤 VERIFIED 값의 근거도 될 수 없다.

VERIFIED 값은 0과 non-zero 모두 DB event ledger에서 재계산한 값과 같아야 한다. Position state는
immutable `canonical_position_state_events`, Task와 Pipeline은 candidate task/event ledger, outreach는
provider receipt로 확정된 SENT ledger에서 target window와 meeting cutoff 기준으로 계산한다.

VERIFIED zero의 receipt collection은 metric의 flow/state 의미에 따라 고정한다.

- `live_client_position_count` → `position_state`
- `channel_outreach` → `outreach_events`
- `new_task_count|reactivated_task_count` → `pipeline_events`
- `active_pipeline_count|interview_pipeline_count|pre_interview_pipeline_count` → `pipeline_state`

Flow receipt로 state zero를 증명할 수 없다. `positions` collection은 일반 v1 입력의 빈 목록 증명에는
남아 있지만 Golden KPI `live_client_position_count`의 zero receipt로는 사용할 수 없다.

Receipt는 metric과 같은 run·source snapshot이어야 하고 `provider_receipt_ref`가 해당 metric cell의
`evidence_refs`에 포함돼야 한다. PARTIAL과 NOT_RUN cell의 `value`는 반드시 null이다.

## DB와 source snapshot

Weekly 숫자의 근간은 DB의 immutable run identity/window, legal status transition, source snapshot,
canonical identity, event ledger다.
ClickUp, Notion, Gmail, 채용 페이지, 관리자 화면은 DB를 대신하는 정본이 아니라 source 또는 같은
report snapshot에서 파생되는 projection이다.

숫자나 상태를 만들기 전에 최소 다음을 DB 또는 검증 가능한 입력 bundle에 기록한다.

- `weekly_run`과 report calendar version
- source system, opaque source pointer, fetched/event timestamp, status, content hash
- canonical position과 source lineage
- customer intent와 evidence ref
- candidate task와 hiring cycle
- pipeline event와 stable event fingerprint
- channel outreach receipt
- metric snapshot과 formula version
- publication intent와 readback receipt

`run_id`가 있는 증거 행은 같은 run의 source snapshot만 참조한다. 다른 run의 source snapshot row를
현재 run의 zero-result, outreach, market 또는 metric evidence로 직접 재사용하지 않는다. 위에서 정한
current-run historical-metric capture만 과거 VERIFIED metric content의 입력 계보로 허용하며, 과거의
zero-result·outreach·market receipt를 현재 증거로 승격하지 않는다.

고객 이메일은 개별 message의 업무 본문만 사용하고 인용·서명·첨부·후보자 이력서·자동 알림·당사
발신 추천을 고객 신규 의뢰로 세지 않는다. 허용 intent는 `REQUESTED`, `POSITION_SHARED`,
`REQUIREMENT_CHANGED`, `PIPELINE_FEEDBACK`, `REFERENCE_ONLY`, `NONE`이다. Raw body와 개인 주소는 보호된 source에
남기고 보고·Git·review bundle에는 opaque evidence ref만 전달한다.

Intent→origin mapping은 `REQUESTED→CLIENT_REQUESTED`, `POSITION_SHARED→CLIENT_SHARED`다.
`REQUIREMENT_CHANGED|PIPELINE_FEEDBACK`는 이미 `CLIENT_REQUESTED|CLIENT_SHARED`인 position에만 연결하며
origin 승격 근거가 아니다. `REFERENCE_ONLY|NONE`도 origin을 승격하지 않는다.

DB 또는 source readback이 없는 값은 추정하지 않는다. 운영 migration target이 확인되지 않은
상태에서는 schema 계약과 ephemeral validation까지만 허용하고 production DB에 쓰지 않는다.

ClickUp 고객 포지션 목록, JobKorea·Saramin 운영 화면, private Notion parent의 정확한 URL은
`contracts/weekly-ops/runtime-contract-v1.json`에 보존한다. 브라우저에 탭이 열렸다는 사실은 URL의
존재 증거일 뿐 인증·readback·주간 집계 완료 증거가 아니다.

## 실제 고객 포지션과 Scraped 경계

Weekly의 live client position은 고객 요청 또는 고객 공유 근거가 연결된 canonical position이다.

허용 origin:

- `CLIENT_REQUESTED`
- `CLIENT_SHARED`
- `INTERNAL_CREATED`
- `SCRAPED_STAGING`

Live client position count에는 `CLIENT_REQUESTED|CLIENT_SHARED`이면서 cutoff 시점에 active인
position만 포함한다. `SCRAPED_STAGING`, `INTERNAL_CREATED`, canonical lifecycle `CLOSED`, ClickUp의
외부 terminal status `closedpositions|complete`는 제외한다.

회사 채용 페이지에서 관측한 공고는 항상 중간 거점인 `SCRAPED_STAGING`으로 들어간다. 동일
회사·직무가 ClickUp에 있다는 사실만으로 고객 의뢰가 되지 않는다. 고객 Gmail의
`REQUESTED|POSITION_SHARED` evidence와 canonical position이 연결돼야 고객 origin으로 승격할 수 있다.
`포지션 변동 사항`에는 Scraped staging 관측을 별도 표식으로 보여줄 수 있지만 live 고객 포지션 수,
최근 고객 인입, 시장 접근성 또는 coverage risk 계산에는 포함하지 않는다.

스푼랩스, 코드잇, 여기어때, 뤼튼테크놀로지스, 패스트뷰의 채용 페이지는 정해진 cadence로
관측할 수 있지만 scraping 실패를 채용 0건으로 바꾸지 않는다. URL·selector·cadence는 이 문서가
아니라 versioned machine contract에 둔다.
여기어때는 보고 label이고 공식 채용 URL의 법인 운영자 `GC Company`는 별도 `legal_operator`로 기록한다.
다섯 source 모두 talent pool/general opening을 active requisition에서 제외한다.
브라우저 network adapter가 official page와 다른 host를 호출하면 versioned allowlist가 있어야 한다.
Allowlist가 비어 있거나 관측 host가 목록 밖이면 `NOT_RUN`이며 새 host를 추론해 따라가지 않는다.

최근 인입 포지션은 `observed_at desc, position_id asc`의 사실 목록이다. 이 목록에는 P0/P1이나
행동 명령을 붙이지 않는다.

## Task identity와 중복 제거

Canonical position identity는 canonical position ID와 고객 요청 evidence lineage로 결정한다.
외부 ClickUp task ID는 lineage이지 canonical identity가 아니다.

Candidate Task identity:

`(candidate_key_hmac, position_id, hiring_cycle_id)`

규칙:

- candidate display name을 identity로 사용하지 않는다.
- 같은 cycle의 최초 VERIFIED `CREATED`만 new task다.
- 최초 `CREATED`는 `from_stage=null`이고 active stage로만 진입한다.
- active stage 사이 이동의 event type은 `STAGE_CHANGED`이고, active에서 terminal stage로 이동하는
  event type은 destination stage가 `JOINED`·`REJECTED`·`WITHDRAWN`·`CLOSED` 중 무엇이든
  `CLOSED`다. Event type `CLOSED`와 destination stage `CLOSED`는 서로 다른 필드다.
- 위 네 terminal stage 어디에서든 active stage로 돌아가는 event type은 `REACTIVATED`만 허용한다.
- 늦게 들어온 event도 앞·뒤 event의 stage chain과 일치해야 하며 task별 직렬화로 동시 삽입을 막는다.
- CLOSED 뒤 같은 cycle의 `REACTIVATED`는 reactivation이다.
- reactivation은 new task가 아니다.
- stage movement는 provider event ref 또는 stable event fingerprint로 dedupe한다.
- current state는 cutoff 이하 최신 VERIFIED event로 계산한다.
- 동률은 `(event_at, recorded_at, pipeline_event_id)` tuple의 lexicographic maximum을 최신으로 결정한다.
- mutable task row의 `current_stage`를 event history보다 우선하지 않는다.
- `hiring_cycle_id`가 없거나 상충하면 영향받는 count는 null/PARTIAL이다.
- 원자료는 삭제하지 않는다. duplicate source link를 비활성화하고 versioned decision을 남긴다.
- 유사한 회사명·직무명만으로 자동 병합하지 않는다.

지난주 표는 최소 다음을 분리한다.

- 신규 Task
- 재활성 Task
- 이동된 기존 후보자
- 현재 Pipeline

## Pipeline 정의

Active Pipeline stages:

- `RECOMMENDATION_PENDING`
- `CLIENT_REVIEW`
- `ASSIGNMENT`
- `INTERVIEW_1`
- `INTERVIEW_2`
- `FINAL_INTERVIEW`
- `OFFER`
- `FINAL_ACCEPTED`

Interview Pipeline stages:

- `ASSIGNMENT`
- `INTERVIEW_1`
- `INTERVIEW_2`
- `FINAL_INTERVIEW`
- `OFFER`
- `FINAL_ACCEPTED`

Pre-interview Pipeline, 즉 `면접 직전 Pipeline` stages:

- `RECOMMENDATION_PENDING`
- `CLIENT_REVIEW`

Current Pipeline에서 제외하는 stages:

- `JOINED`
- `REJECTED`
- `WITHDRAWN`
- `CLOSED`

같은 Candidate Task identity는 한 section에서 한 번만 나타난다. `활성 Pipeline`은 active stage
전체이고, `면접 Pipeline`과 `면접 직전 Pipeline`은 그 부분집합이다. `면접 Pipeline`은 4주 KPI의
집계 지표이며 별도 상세 section이 아니다. `활성 Pipeline` section은 여덟 active stage 전체를
stage별로 보여주고, `면접 직전 Pipeline` section은 그중 `RECOMMENDATION_PENDING|CLIENT_REVIEW`만
의도적으로 다시 필터링한 운영 view다. 따라서 같은 Candidate Task가 두 section에 나타날 수 있지만
각 section 안에서는 한 번만 나타나며 두 section의 row 수를 합산하지 않는다. 최종합격 목록 일부를
전체 활성 Pipeline이라고 부르지 않는다.

## 후보자 소싱

사람인, 잡코리아, LinkedIn Recruiter를 한 합계로 먼저 합치지 않는다. 보고서에는 각각 4주
연속 데이터를 둔다.

- `Saramin`
- `JobKorea`
- `LinkedIn Recruiter`

주간 발송으로 세려면 provider sent-history readback, stable receipt/message/request ID, sent time,
approved consultant actor가 모두 있어야 한다.

Consultant roster와 channel별 provider actor/seat mapping은 append-only evidence다. 기존 consultant나
provider account row의 UPDATE·DELETE·TRUNCATE는 금지하고 roster 변경은 새 source snapshot과 계약
version으로 남긴다.

다음은 발송이 아니다.

- 열린 후보 탭
- 검색 결과
- 읽음 상태
- 초안
- 내부 포지션 공유 메일
- 로컬 클릭 기록
- provider 누적 합계

사람인의 `-1건`은 credit usage 표기이고 음수 발송량이 아니다. 잡코리아 누적 159 같은 전체
합계는 closed window의 개별 행이 없으면 주간 수치로 사용하지 않는다. 읽지 못한 채널은 0이 아니라
coverage gap이다.

LinkedIn은 사용자가 열어 둔 기존 인증 Aside tab 안에서만 읽는다. 고정 operator URL을 추정하지
않으며 현재 인증 surface의 URL ref를 캡처·검증한 뒤에만 sent-history evidence로 사용할 수 있다.

컨설턴트 몰입도는 verified send만 consultant×canonical position으로 집계한다. `consultant-focus-v2`
machine contract가 산출한 `YELLOW_ELIGIBLE`은 잔디밭의 YELLOW 자격 evidence일 뿐 다른 색 상태를
계산하거나 덮어쓰지 않는다. 미확인 채널의 컨설턴트를 0건으로 비교하지 않는다.

## LinkedIn 시장 접근성

시장 접근성은 “LinkedIn에서 해당 조건의 후보를 실제로 얼마나 찾기 쉬운가”를 측정한다. 회사나
직무 이름의 인상으로 추정하지 않는다.

Ranked 결과의 필수 입력:

- authenticated source snapshot ID
- `captured_at`
- frozen sort order
- ordered result snapshot hash
- frozen geography, titles, skills, seniority/years, languages
- versioned must-have predicates
- `result_count_lower_bound`와 `count_is_exact`
- 캡처 순서의 첫 20개 row
- 20개의 HMAC-unique candidate key
- predicate별 `TRUE|FALSE|UNKNOWN`

다섯 frozen filter dimension은 각각 비어 있지 않은 non-blank string 배열이어야 한다. 빈 배열,
JSON null, 공백 문자열 또는 다른 JSON type이 하나라도 있으면 ranked market input이 아니다.
Market source snapshot의 source system은 `linkedin_rps`이고 그 `raw_hash`는
`ordered_result_snapshot_hash`와 정확히 같아야 한다.
`result_count_lower_bound`와 `count_is_exact`는 같은 run·PASS source snapshot·ordered hash에 결속된
immutable provider result receipt에서 읽어 DB가 다시 대조한다. Market row의 caller 값은 근거가 아니다.

각 evaluation row의 필드는 정확히 `candidate_key_hmac`, `rank`, `predicate_results`이고 `rank`는
캡처 순서와 같은 1..20이다. Predicate key 집합은 frozen `must_have_predicates`와 정확히 같아야 한다.

모든 must-have predicate가 TRUE일 때만 qualified match다. 각 값은 JSON null이 아닌
`TRUE|FALSE|UNKNOWN` 중 하나다. FALSE 또는 UNKNOWN이 하나라도 있으면 match가 아니고 UNKNOWN은
coverage gap에도 기록한다. Aggregate match count는 입력값으로 신뢰하지 않고 20개 evaluation에서
다시 계산한다. `result_count_lower_bound`는 검증한 20명보다 작을 수 없다. Unique 표본이 20보다
작으면 `UNRANKED`다.

Pool points는 `result_count_lower_bound`를 versioned 구간값에 매핑한다. 구간은 `0=0`, `1..9=10`,
`10..24=20`, `25..49=30`, `50..99=40`, `100 이상=50`이다. Precision points는 `0 이상 0.20 미만=0`,
`0.20 이상 0.40 미만=15`, `0.40 이상 0.60 미만=30`, `0.60 이상 0.80 미만=40`,
`0.80 이상=50`을 사용한다.

```text
precision_rate = qualified_sample_matches / evaluated_sample_size
market_accessibility = (pool_points * precision_points * 100) // 2500
```

`evaluated_sample_size`는 qualified subset의 크기가 아니라 고정된 HMAC-unique 평가 표본 수이며
정상 산출에서는 정확히 20이다.
`pool_points` 입력은 `result_count_lower_bound`, `precision_points` 입력은 위 `precision_rate`다.
Market formula version은 `market-accessibility-v2`, coverage-risk formula version은
`sourcing-coverage-risk-v1`이다. Coverage risk 비대상 lifecycle은 score null, band `UNRANKED`, reason
`INELIGIBLE_LIFECYCLE`로 필드는 유지한다.
비대상 lifecycle row의 lineage guard는 position과 PASS LinkedIn snapshot을 검증하되 ACTIVE 전용
`position_age_days`와 `active_candidate_count` 재계산 일치 조건을 적용하지 않는다.
Market row에는 두 version을 각각 `market_formula_version`, `coverage_risk_formula_version`으로 기록한다.

→ 두 요소를 곱하므로 0/20 qualified이면 전체 검색 결과가 많아도 `HARD 0`이다. 언어별 반올림
차이를 없애기 위해 정수 연산을 사용한다.

Market bands:

- `EASY=70..100`
- `MEDIUM=40..69`
- `HARD=0..39`

Weight와 band는 제품 계약 T이지 시장의 절대 진리가 아니다. 변경하려면 formula version과 독립
기대값 테스트를 함께 바꿔야 하며 LLM이 임의 조정할 수 없다.

## 소싱 커버리지 위험지수

Coverage risk는 경영 명령이 아니라 최근성, active candidate gap, 시장 scarcity를 보여주는
참고값이다.

- recency: 0..2일=40, 3..7일=30, 8..14일=15, 15일 이상=0
- active candidates: 0명=30, 1명=20, 2명=10, 3명 이상=0
- scarcity: HARD=30, MEDIUM=15, EASY=0

```text
coverage_risk = recency_points + pipeline_gap_points + scarcity_points
```

→ 높은 수치는 커버리지 위험이 크다는 뜻일 뿐 그 포지션을 실행하라는 지시가 아니다.

Coverage bands: `A=70..100 B=40..69 C=0..39`.

Market result가 UNRANKED이면 coverage risk도 UNRANKED다. `age_days`는 observed date와 cutoff의
현지 날짜 차이로 계산한다. 미래 observed date, naive datetime, 음수 candidate count는 BLOCKED다.
Observed date는 cutoff 이전의 PASS `REQUESTED|POSITION_SHARED|REQUIREMENT_CHANGED` customer intent 중
가장 최근 시각이다. Active candidate count는 cutoff 이전 PASS pipeline event를 Candidate Task별
`(event_at, recorded_at, pipeline_event_id)` 내림차순으로 하나만 선택한 뒤 여덟 active stage만 센다.
두 입력값은 DB가 재계산하며 caller가 제공한 값과 다르면 `MARKET_COVERAGE_RISK_DERIVATION_INVALID`다.

## Notion Golden Sample 형식

첫 화면은 짧은 dashboard이고 상세 목록은 collapsed toggle이다.

1. `4주 KPI`
2. `최근 인입 포지션`
3. `시장 접근성 / 소싱 커버리지 위험지수`
4. `포지션 변동 사항`
5. `후보자 소싱`
6. `지난주 신규 Task`
7. `지난주 재활성 Task`
8. `지난주 이동 후보자`
9. `활성 Pipeline`
10. `면접 직전 Pipeline`
11. `데이터 커버리지`

Structured render model에서 1~5는 `collapsed=false`, 6~11은 `collapsed=true`다.
각 section은 versioned Golden machine contract의 `section_schemas`에 정의된 row shape와 필수 필드를
따른다. `후보자 소싱`은 `channel_coverage`, `consultant_focus`, `excluded_rows` 세 collection을 담는다.
필수 collection이나 row field가 없으면 해당 section은 PARTIAL/BLOCKED이며 임의 보완하지 않는다.
`마감 후 경보`는 12번째 section을 만들지 않고 `데이터 커버리지`의 `post_cutoff_alerts` collection으로
투영한다. 같은 section의 `requirement_status`와 합산하지 않는다.

금지 표현:

- `P0/P1`
- `즉시 실행`
- `우선 실행`
- `우선 착수`
- `해야 한다`
- `이번 주 고객 액션`
- `운영 변경`
- `소싱 실행`
- LLM 자기언급
- 출처 없는 권고·성과 코멘트

최근 인입은 시간순 사실 목록이다. 시장 접근성과 coverage risk 외에 별도의 “LLM 추천
우선순위”를 만들지 않는다. `운영 변경` 대신 `포지션 변동 사항`, `소싱 실행` 대신 `후보자 소싱`을
사용한다.

## 외부 발행과 개인정보

Preflight와 render mode는 publication hook를 호출하지 않는다.

- `publication_verdict=NOT_RUN`
- `publication_reason=MODE_FORBIDS_PUBLICATION`
- `external_writes_performed=[]`

외부 호출 전에는 exact target, private visibility, write-ahead intent, idempotency key, current schema
readback이 필요하다. 하나라도 없으면 외부 호출 전에 NOT_RUN이다. External object ID는 외부 쓰기
결과로 받은 뒤 readback receipt에 기록한다. Reload content hash와 persisted receipt까지 확인돼야
발행 성공이다.
여러 target을 쓰는 경우 receipt envelope는 target name과 target ID를 포함하며 target별 intent,
idempotency key, readback을 독립적으로 검증한다.
Report snapshot은 run별 1부터 끊김 없이 증가하는 immutable revision이다. 전체 revision 중 가장 높은
현재 revision만 발행 후보가 될 수 있고, 그 snapshot과 weekly run이 모두 `READY`여야 한다. Publication
intent와 receipt를 기록할 때마다 같은 run을 잠근 뒤 이 current 조건을 다시 확인한다. 따라서 이전
READY revision은 뒤에 PARTIAL/BLOCKED/READY revision이 생기거나 run이 READY에서 벗어나는 즉시 발행할
수 없다. `database|clickup|notion|admin_web|email` target별 intent는 current report snapshot에 하나만
허용한다. Weekly run의 `PUBLISHED` 전이는 다섯 target 모두의 `READBACK_VERIFIED` intent와 verified
receipt가 같은 current report snapshot에 연결된 뒤에만 허용한다.
External object ID 중복 금지는 `(readback_report_snapshot_id, target_name, external_object_id)` 범위다.
같은 안정적 외부 object를 다음 주 report snapshot에서 다시 readback하는 것은 허용한다.

HTTP 성공은 발행 성공이 아니다. External object ID를 받은 뒤 readback이 실패하면
`UNKNOWN_REQUIRES_RECONCILIATION`이며 자동 재발행하지 않는다. 먼저 idempotency key로 기존 object를
재조회한다.

Candidate display name은 canonical input, Git, email, admin web, logs, hashes, receipts, exceptions,
review artifacts에 넣지 않는다. Machine contract 식별자는 정확히 `canonical_input|git|email|admin_web|
logs|hashes|receipts|exceptions|review_bundle`이다. 실행 가능한 Golden v2 계약 아래 사용자가 명시적으로
승인한 private Notion detail에서만 publish 직전에 보호된 resolver로 해석할 수 있다. 테스트는
synthetic ID만 사용한다.

## 검증과 완료 조건

Weekly SOT 통합은 다음 호출 경로가 모두 연결돼야 한다.

```text
docs/sot/INDEX.md
→ docs/sot/weekly-ops-contract.md
→ .agents/skills/weekly-ops/SKILL.md
→ prompt/notion Golden references
→ versioned machine contract
→ scripts/acceptance-weekly-ops-skill.sh
→ CI verify workflow
```

→ 파일을 추가하는 것만으로는 통합이 아니다. 다음 세션의 Skill 진입점과 기존 CI가 같은 정본을
읽고 누락·변조를 실패시켜야 한다.

검사 성공 계약:

- required file 0건 금지
- unit test 0건 금지
- mutation 생존 0건
- `CHECKED` 양수
- child subprocess 실행 없이 `PASS + CHECKED` 문자열만 출력한 결과는 합격 근거가 아님
- SOT heading·formula·stage·link·legacy publication block 의미 변조 차단
- Golden v1 감사 계약과 reference·DB DDL이 3-key identity, 정확 20개 표본, 곱셈식,
  11-section layout을 이 정본과 동일하게 표현
- 일반 Weekly v1 회귀 없음
- 원본 worktree 밖 변경 없음

발행 후보의 적대검증은 같은 redacted evidence hash와 동일 계약 T를 사용한다. Claude V1이 먼저
요구·구현·검사기를 공격하고 fresh Codex V2가 각 주장을 재현·반박한다. 두 엔진 중 하나가
NOT_RUN이거나 필수 결함이 확인되면 발행 PASS를 금지한다. 모델의 PASS 문장은 실행 증거가 아니다.

Golden publication 완료는 이 SOT 통합의 완료 조건이 아니다. Golden v2 callable과 실제 source,
publisher, readback이 없는 한 ship verdict는 NOT_READY다.

## 롤백과 영향 반경

이 문서 변경의 영향 반경은 Weekly 요구 탐색, Golden fail-closed 상태, Skill과 CI 검사다. 일반
Weekly v1의 계산과 Markdown 출력은 이 통합에서 바꾸지 않는다.

롤백은 다음을 한 commit 단위로 되돌린다.

- 이 SOT
- INDEX와 verification 설명
- Skill·reference 링크
- Golden v1 runtime status
- SOT checker와 acceptance 연결

롤백 실패나 부분 revert가 생기면 `RECOVERY_REQUIRED`로 남기고 검사와 SOT 중 하나만 제거한 상태를
정상으로 취급하지 않는다. 운영 DB, Notion, Gmail, ClickUp, admin web에는 쓰지 않는다.
