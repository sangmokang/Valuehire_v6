# 관리자 주간 대시보드 Phase D 운영 데이터 결정 계약 목표 — 2026-08-17

## 결론

이번 단계에서는 실계정과 운영 데이터에 손대지 않고, 기존 Supabase 표를 어떤 기준으로 읽을지 먼저 코드와 시험으로 고정합니다. 새 원본 저장소를 만들지 않고 Gmail 수집 장부·사건 표·ClickUp 후보 표를 최대한 재사용합니다.

사장님이 이번 변경에서 직접 보실 것은 다섯 가지입니다. Gmail 메일 원문은 영구 복사하지 않고 주간 합계만 장기 보관하는지, 후보자 이름·학교·회사는 자동 병합이 아니라 검토 제안에만 쓰는지, 작업을 시작했다가 덜 끝낸 경우를 실패로 표시하는지, sangmokang이 실제 캘린더 하나로 확인될 때만 쓰는지, 읽기 주기를 15분으로 두되 주간 보고 기준은 그대로인지입니다.

실제 Gmail·ClickUp·캘린더 계정 읽기, Supabase 쓰기, 일정 등록, 배포는 이번 단계에서 하지 않습니다. 그래서 Phase D가 통과해도 운영 수치가 생겼다고 보고하지 않습니다.

## 판단 근거

- v4에는 이미 Gmail 사건·실행 장부·동기화 위치와 ClickUp 후보 식별자를 담는 표가 있습니다. 같은 목적의 새 표를 만들면 두 체계가 갈라집니다.
- Google의 현재 정책은 Google 사용자 데이터의 영구 복사본을 만드는 것을 금지하고 삭제 요청을 존중하도록 요구합니다. 따라서 Gmail 원문 영구 보관은 사장님 의도와 무관하게 이번 구현에서 채택할 수 없습니다. 공식 근거: https://developers.google.com/workspace/workspace-api-user-data-developer-policy
- `sangmokang`은 사람이 알아보기 좋은 별칭일 수 있지만 Google Calendar가 API 호출에 요구하는 실제 캘린더 고유값이라고 확인된 것은 아닙니다. 목록에서 정확히 하나가 확인되지 않으면 수집하지 않는 편이 잘못된 일정 집계를 막습니다. 공식 근거: https://developers.google.com/calendar/api/v3/reference/calendarList/list
- ClickUp은 기본 요금제에서도 토큰당 분당 100회 제한이 있으므로 15분 주기는 충분히 보수적입니다. 다만 페이지가 많아 제한에 걸리면 해당 실행을 성공으로 처리하지 않습니다. 공식 근거: https://developer.clickup.com/docs/rate-limits
- Supabase는 반복 작업을 초 단위부터 예약할 수 있지만 이번 단계에서는 운영 일정을 등록하지 않습니다. 공식 근거: https://supabase.com/docs/guides/cron

## 사장님이 반드시 볼 부분

### 1. Gmail 보관 범위

- **판단이 필요한 이유:** 메일 원문은 후보자·고객사 개인정보를 포함할 수 있고 Google 정책상 영구 복사할 수 없습니다.
- **정확한 변경 위치:** 새 운영 원본 계약의 `retention.gmail`과 이를 검사하는 시험입니다. 이 위치는 저장 가능한 항목과 금지 항목을 정합니다.
- **승인 기준:** 제목·본문·주소·첨부 원문은 영구 저장하지 않고, 개인을 다시 알아볼 수 없게 만든 주간 합계만 장기 보관하면 승인입니다.
- **틀렸을 때 영향:** 잘못 승인하면 삭제 요청을 지키기 어렵고, 사고 시 노출 범위가 메일 전체로 커집니다.

### 2. 후보자 중복 판단

- **판단이 필요한 이유:** 같은 이름이 있을 수 있고 학교·회사는 바뀌므로 세 항목만으로 자동 병합하면 다른 사람 기록이 합쳐질 수 있습니다.
- **정확한 변경 위치:** 새 후보자 연결 정책 함수와 시험입니다. 이 위치는 이름·학교·회사를 비교한 뒤 어떤 검토 결과를 내는지 정합니다.
- **승인 기준:** 이름이 같고 학교·회사도 모두 같아도 자동 병합하지 않고 “연결 검토”만 만들면 승인입니다.
- **틀렸을 때 영향:** 다른 후보자의 이력·연락 정보·추천 기록이 한 사람으로 섞일 수 있습니다.

### 3. 실패와 미실행 구분

- **판단이 필요한 이유:** 일부 페이지만 읽고 숫자를 보여주면 실제보다 작은 수치를 성공처럼 볼 수 있습니다.
- **정확한 변경 위치:** 새 수집 결과 판정 함수와 시험입니다. 이 위치는 시도 여부와 전체 완료 여부를 보고 세 상태를 정합니다.
- **승인 기준:** 애초에 정책·권한·설정이 없어 시작하지 않은 것은 `NOT_RUN`, 시작한 뒤 일부라도 못 끝낸 것은 `FAIL`, 전체 페이지를 끝낸 경우만 `PASS`면 승인입니다.
- **틀렸을 때 영향:** 불완전한 숫자를 믿고 영업·채용 운영 결정을 내릴 수 있습니다.

### 4. 캘린더 선택

- **판단이 필요한 이유:** 별칭이 중복되거나 실제 고유값과 다르면 엉뚱한 일정을 기준으로 집계할 수 있습니다.
- **정확한 변경 위치:** 새 캘린더 별칭 해석 함수와 시험입니다. 이 위치는 `sangmokang`을 실제 목록 항목 하나에 연결합니다.
- **승인 기준:** 고유값 또는 표시 이름이 정확히 하나만 일치할 때만 실제 고유값을 사용하고, 없거나 둘 이상이면 `NOT_RUN`이면 승인입니다.
- **틀렸을 때 영향:** 주간 회의 기준일과 집계 기간이 틀어집니다.

### 5. 읽기 주기

- **판단이 필요한 이유:** 더 자주 읽으면 새 활동을 빨리 반영하지만 외부 서비스 제한과 장애 횟수도 늘어납니다.
- **정확한 변경 위치:** 새 운영 원본 계약의 `refresh.interval_minutes`입니다. 이 위치가 향후 읽기 작업의 기본 간격을 정합니다.
- **승인 기준:** 기본 15분, 한 번에 하나만 실행, 이전 실행이 끝나지 않았으면 겹쳐 돌지 않고 건너뛰면 승인입니다.
- **틀렸을 때 영향:** 중복 실행과 제한 초과로 수집 실패가 늘 수 있습니다.

## 결정 카드

### Gmail 원문 보관

- **무엇을** — Gmail 원문 영구 복사는 금지하고 개인을 다시 알아볼 수 없게 만든 주간 합계만 장기 보관합니다.
- **왜** — Google 정책과 삭제 요구를 지키고 개인정보 사고 범위를 줄여야 합니다.
- **버린 길** — 메일 원문·첨부를 Supabase에 영구 보관하는 길은 정책 위반과 사고 범위 확대 때문에 버립니다.
- **대가** — 오래된 메일을 Valuehire 안에서 원문 그대로 다시 검색할 수 없습니다.
- **되돌리기** — 법률·정책 검토로 별도 보관이 허용돼도 새 승인과 별도 보안 설계가 필요하며, 이 PR만 되돌려 자동 허용하지 않습니다.

### 후보자 중복 판단

- **무엇을** — 이름·학교·회사는 연결 검토 제안에만 쓰고 자동 병합은 하지 않습니다.
- **왜** — 세 항목은 동명이인과 이직·학력 표기 차이를 완전히 구분하지 못합니다.
- **버린 길** — 세 항목 일치 즉시 한 후보자로 합치는 길은 개인정보 오병합 위험 때문에 버립니다.
- **대가** — 사람이 검토해야 하므로 처리 속도가 느려집니다.
- **되돌리기** — 나중에 검증된 고유 식별자 계약이 생기면 별도 단계에서 자동 연결 기준을 추가합니다.

### 수집 판정

- **무엇을** — 시작 전 막힘은 `NOT_RUN`, 시작 후 불완전은 `FAIL`, 전량 완료만 `PASS`로 정합니다.
- **왜** — 일부 수치를 성공으로 보여주는 일을 막아야 합니다.
- **버린 길** — 일부 성공 상태를 새로 추가하는 길은 현재 화면의 세 상태 계약과 충돌해 버립니다.
- **대가** — 일부 수집된 데이터가 있어도 그 실행의 숫자는 화면에 표시하지 않습니다.
- **되돌리기** — 별도의 부분 성공 계약과 화면 표현을 설계한 새 버전에서만 네 번째 상태를 도입합니다.

### 캘린더 선택

- **무엇을** — sangmokang이 실제 목록에서 정확히 하나로 확인될 때만 그 고유값을 사용합니다.
- **왜** — 별칭만 믿고 첫 항목을 고르면 엉뚱한 일정이 기준이 될 수 있습니다.
- **버린 길** — 별칭을 실제 고유값으로 하드코딩하는 길과 첫 일치 항목을 고르는 길은 모호해서 버립니다.
- **대가** — 첫 연결 때 목록 확인 절차가 한 번 필요합니다.
- **되돌리기** — 확인된 실제 고유값을 안전한 런타임 설정에 저장하면 별칭 검색 없이 직접 사용할 수 있습니다.

### 읽기 주기

- **무엇을** — 기본 15분 간격으로 읽되 이전 실행과 겹치면 새 실행을 건너뜁니다.
- **왜** — 주간 보고를 기다리지 않고 새 활동을 반영하면서도 외부 서비스 제한 안에 머물 수 있습니다.
- **버린 길** — 매분 읽기는 불필요한 호출과 장애를 늘리고, 하루 한 번은 사장님이 원한 빠른 반영에 못 미쳐 버립니다.
- **대가** — 최악의 경우 새 활동 반영이 약 15분 늦습니다.
- **되돌리기** — 계약 값 하나를 바꾸고 실제 호출량 시험을 다시 통과시키면 간격을 늘리거나 줄일 수 있습니다.

## 현재 상태

1. v6 metric 계약은 Gmail과 ClickUp 외부효과를 `DISABLED`로 두며, 보관 정책이 없을 때 추천·포지션 메일을 미집계로 표시합니다(`contracts/admin-weekly-dashboard/metric-contract-v1.json:3-8`, `:18-20`).
2. v6 집계기는 출처 상태가 없으면 `NOT_RUN/source_state_missing`, 출처가 실패·미실행이면 값 대신 해당 상태를 그대로 냅니다(`humansearch/src/humansearch/admin_weekly_dashboard/snapshot.py:79-105`).
3. v4 `gmail_derived_events`는 사건 종류·상태·발생시각을 이미 갖고 있고 보고는 가린 증거만 쓰도록 적혀 있습니다(`/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260726000000_gmail_clickup_ingestion_ledger.sql:119-165`).
4. 같은 migration의 `gmail_ingestion_runs`는 전체 페이지 완료 여부와 실행 상태를 이미 갖습니다(`/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260726000000_gmail_clickup_ingestion_ledger.sql:233-253`).
5. v4 `gmail_sync_state`는 마지막 성공 시각과 오류를 보관합니다(`/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260603120000_gmail_messages.sql:31-44`).
6. v4 `pipeline_candidates`에는 ClickUp 고유 작업값과 마지막 동기화 시각이 이미 있습니다(`/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260517010000_candidates_clickup_parity_columns.sql:59-79`, `:140-156`).
7. 기존 `weekly_brief_snapshot`은 월요일 회의 전 주를 기준으로 하며(`/Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations/20260725090000_weekly_brief_snapshot.sql:1-18`), Phase B의 일요일~토요일 계약과 달라 그대로 재사용할 수 없습니다.

## 근본 원인

Phase B와 C는 정확한 주간 집계와 안전한 화면을 먼저 만들었지만, 실제 원본을 읽기 전에 확정해야 하는 보관·캘린더·중복·실패·주기 정책이 비어 있었습니다. 그래서 연결을 서두르면 기존 표를 재사용하더라도 개인정보를 과도하게 저장하거나 불완전한 숫자를 성공으로 표시할 수 있습니다.

## 인수 기준

### AC-D1 — 기존 표 재사용 운영 결정 계약

- **EARS 단언:** When 운영 원본 계약을 읽고 수집 결과·후보자 비교·캘린더 목록을 판정하면, 시스템은 기존 Supabase 표를 정본으로 가리키고, 15분 단일 실행, Gmail 원문 영구 복사 금지, 후보자 자동 병합 금지, 전체 완료 전 `FAIL`, 캘린더 하나 확인 전 `NOT_RUN`을 일관되게 반환해야 합니다.
- **검증 명령:** `cd humansearch && uv run --no-sync pytest -q tests/test_admin_source_policy.py`, `cd humansearch && PYTHONPATH=src uv run --no-sync python -m humansearch.admin_weekly_dashboard.source_policy_cli --contract ../contracts/admin-weekly-dashboard/source-contract-v1.json`, 저장소 Python 게이트 전체를 실행합니다.
- **counter-AC:** 새 원본 표를 만들거나, Gmail 본문 영구 저장을 허용하거나, 이름·학교·회사 일치로 자동 병합하거나, 일부 페이지만 읽고 `PASS`를 반환하거나, `sangmokang`을 목록 확인 없이 실제 고유값으로 쓰면 가짜 합격입니다.

## Harness 게이트 진행 계획

1. 이 목표와 입출력 계약을 먼저 커밋합니다.
2. 운영 원본 계약·판정 함수가 없는 상태에서 실패하는 시험을 먼저 작성하고 커밋합니다.
3. 시험을 통과시키는 최소 JSON 계약과 순수 Python 판정 모듈만 구현합니다.
4. 독립 시험, 전체 Python 검사, 저장소 비밀·개인정보 검사를 실행합니다.
5. Claude 1차와 Codex 2차 적대 검증을 수행하고 판정 전문을 이 문서에 보존합니다.
6. 한국어 PR을 만들고 실제 원격 본문을 다시 읽습니다. 자동 병합·배포는 하지 않습니다.

## 적대 검증 항목

- “기존 표 재사용”이라는 말만 있고 실제 표·필드가 계약에 박혀 있지 않은가.
- Gmail 원문 또는 다시 개인을 알아볼 수 있는 값을 영구 보관하도록 새는가.
- 후보자 비교가 자동 병합으로 이어지는 숨은 경로가 있는가.
- 일부 성공이 `PASS`나 0으로 표시되는가.
- 캘린더 별칭 중복을 첫 번째 항목 선택으로 조용히 통과시키는가.
- 15분 실행이 겹쳐 같은 구간을 중복 수집할 수 있는가.

## SOT 체크리스트

- `docs/sot/INDEX.md`
- `docs/sot/coding-principles.md`
- `docs/sot/verification-commands.md`
- `docs/sot/git-workflow.md`
- `docs/sot/hook-contracts.md`
- 동작 변경은 아직 운영 SOT에 반영할 단계가 아닙니다. Phase D는 연결 전 계약이며 live 실행을 만들지 않습니다.

## 비범위

- Gmail·ClickUp·Google Calendar 실계정 읽기
- Supabase migration 적용·데이터 쓰기·삭제
- Gmail 원문·첨부·주소의 새 영구 저장
- 후보자 행 자동 병합·수정
- Supabase 반복 작업 등록
- 관리자 인증·배포·PR #16 병합
- 기존 v4 `weekly_brief_snapshot` 함수 수정

## 롤백 절차

Phase D 커밋을 되돌리면 새 운영 원본 계약·판정 모듈·시험·이 목표 문서만 사라집니다. Phase B/C 코드와 기존 v4 Supabase 표는 수정하지 않으므로 데이터 롤백은 없습니다.

## 영향 반경

- 잘못된 계약은 다음 실계정 연결 단계의 보관·집계·중복 판단을 잘못 이끕니다.
- 이번 단계 자체는 네트워크 연결과 데이터 쓰기가 없어 운영 수치·후보자 기록·메일함을 바꾸지 않습니다.
- Gmail·후보자 정보는 개인정보 경로이므로 이 변경은 L3로 검증합니다.

## 계약 스펙

```json
{
  "refresh": {
    "interval_minutes": 15,
    "overlap_policy": "SKIP_AS_NOT_RUN"
  },
  "calendar": {
    "requested_alias": "sangmokang",
    "resolution": "EXACTLY_ONE_ID_OR_SUMMARY_MATCH"
  },
  "retention": {
    "gmail_raw_permanent_copy": "FORBIDDEN",
    "weekly_anonymized_aggregates": "INDEFINITE",
    "deletion_request": "REQUIRED"
  },
  "candidate_identity": {
    "evidence": ["name", "school", "company"],
    "auto_merge": false,
    "three_exact": "REVIEW_REQUIRED"
  },
  "collection_verdict": {
    "not_attempted_for_missing_prerequisite": "NOT_RUN",
    "attempted_but_incomplete": "FAIL",
    "all_pages_completed": "PASS"
  }
}
```

→ 이 계약은 더 자주 읽되 겹치지 않게 하고, 원문 영구 복사와 자동 후보 병합을 막으며, 불완전한 수치를 성공으로 보이지 않게 합니다.

## 적대 검증 로그

### 사전 독립 코드·보안 검토

- 코드 검토자는 실제 module CLI가 `tool.uv.package = false` 때문에 `PYTHONPATH=src` 없이 실행되지 않는 고아 경로와 계약 `version`을 검사하지 않는 결함을 지적했습니다. subprocess 시험과 v1 exact version 검증을 추가한 뒤 재검토 `PASS`를 받았습니다.
- 보안 검토자는 `public.*`면 어떤 표든 허용되어 `public.gmail_messages`로 바꿔치기할 수 있는 결함을 재현했습니다. 승인된 기존 표·필드·처리방식 전체를 exact allowlist로 고정하고 raw Gmail table mutation이 `ValueError`로 막힘을 재검증해 `PASS`를 받았습니다.

### Claude 1차 적대 검증 — `NOT_RUN`

실행한 명령 전문:

```text
env -u ANTHROPIC_API_KEY claude -p --tools 'Read,Grep,Glob' --permission-mode dontAsk --no-session-persistence --output-format text '당신은 Codex가 구현한 Valuehire_v6 Phase D의 독립 1차 적대 검증자다. 읽기 전용으로 /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/admin-dashboard-phase-d 를 검토하라. 코드나 GitHub를 수정하거나 live Gmail, ClickUp, Calendar, Supabase, 배포 환경에 접근하지 마라.

검토 기준 문서: docs/engineering/admin-weekly-dashboard-phase-d-source-policy-goal-2026-08-17.md
반드시 읽을 구현: contracts/admin-weekly-dashboard/source-contract-v1.json, humansearch/src/humansearch/admin_weekly_dashboard/source_policy.py, source_policy_cli.py, contracts.py, __init__.py, humansearch/tests/test_admin_source_policy.py, scripts/acceptance-hs-gates-mutations.sh, scripts/acceptance-hs-gates-antiforge.sh.
기존 표 근거가 필요하면 /Users/kangsangmo/Desktop/Valuehire_v4/supabase/migrations 안의 관련 SQL도 읽어라.

정조준 질문:
1. 기존 Supabase 표를 최대한 재사용한다는 말이 실제 exact table/field 계약인가, 아니면 raw Gmail/PII 표로 바꿔치기 가능한가?
2. Gmail 원문 영구보관 금지와 삭제 요구, 익명 주간 집계만 장기보관이라는 경계가 코드/공개 CLI에서 새는가?
3. 이름·학교·회사 exact 비교가 자동 병합이나 동명이인 오병합으로 이어질 경로가 있는가?
4. sangmokang 별칭이 실제 CalendarList에서 정확히 하나일 때만 PASS인가?
5. NOT_RUN은 미시도/전제 부족/겹침, FAIL은 시도 후 불완전, PASS는 pagination 전량 완료로만 나오는가? reason 조합으로 의미를 위조할 수 있는가?
6. source_policy_cli가 실제 실행 가능한 경로인가, 시험에서만 import되는 고아인가?
7. mutation/antiforge 샌드박스가 FileNotFound 같은 엉뚱한 이유로 통과하지 않는가?
8. 이번 Phase D가 live 연결·쓰기·스케줄러·배포를 하지 않았는데 완료로 과장했는가?
9. Claude가 놓칠 법한 타입·Unicode 정규화·빈 값·중복 Calendar ID·계약 버전·추가 키·외부효과 경계를 공격하라.

이미 확보한 주장(그대로 믿지 말고 코드로 확인): targeted 22 tests PASS, full HumanSearch 62 tests PASS, mutations 6/6, antiforge 3/3, verify secret scan PASS, data exposure tracked 106/history 515 violation 0. acceptance-0-2는 worktree에 .secret-patterns가 없어 NOT_RUN, session-status는 RED 1/19. live 외부 연결은 전부 NOT_RUN이다.

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 "결론". 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 "판단 근거": 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·표를 붙였으면 바로 아래에 "→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가" 1~3줄을 달아라.
- 첫 줄에 VERDICT: PASS 또는 VERDICT: FAIL 한 줄을 두어라. 그 한 줄은 결론의 일부가 아니라 기계가 읽는 표식이므로 결론 제목 앞에 온다.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨을 붙이고, 그 옆에 그대로 두면 사업/운영에 무슨 일이 생기는지 한 문장으로 덧붙여라(라벨을 지우지 마라).
- 설계 결정을 지적할 때는 "무엇을 / 왜 / 버린 대안 / 대가 / 되돌리는 법" 5줄로 적어라.
- 이번에 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 판정 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라(확인 못 한 것은 ※).
- 한국어 존칭체. 초등학생용 비유는 쓰지 마라 — 성인 의사결정자 수준으로 써라.'

[출력 형식 — 반드시 지킬 것]
읽는 사람은 기술 배경이 없는 사업 책임자다. 판정 내용은 절대 축소하지 말고, 표현만 풀어 써라.
1) 문서 맨 앞에 "결론". 결정할 사항 1개당 1~2문장, 전체 분량 상한 없음. 전문용어는 풀어 쓰더라도 결론에서는 쓰지 마라.
2) 그다음 "판단 근거": 왜 그렇게 봤는지, 갈림길에서 왜 이 해석을 골랐는지, 버린 해석은 왜 버렸는지, 이 판정이 틀리면 무엇이 깨지는지.
3) 그다음부터 기술 상세·명령·출력·file:line 전문. 증거는 하나도 생략하지 마라.
- 전문용어는 첫 등장 문장 안에서 괄호로 풀어 써라. 뒤에 몰아 쓴 용어집은 무효다.
- 터미널 출력·코드 블록·표를 붙였으면 바로 아래에 "→ 뭘 시켰나 / 뭐가 나왔나 / 좋은 소식인가 나쁜 소식인가" 1~3줄을 달아라.
- 첫 줄에 VERDICT: PASS 또는 VERDICT: FAIL 한 줄을 두어라.
- file:line 을 인용하면 그 줄이 무슨 일을 하는 줄인지 한 마디 덧붙여라.
- 결함마다 심각도 라벨과 사업 영향을 적어라.
- 설계 결정을 지적할 때는 무엇을/왜/버린 대안/대가/되돌리는 법 5줄로 적어라.
- 건너뛴 것·확인하지 못한 것·중간에 실패해서 다시 한 것을 앞부분에 명시해라.
- 추정과 확인된 사실을 구분 표시해라.
- 한국어 존칭체로 적어라.
```

→ Claude에게 Phase D의 개인정보·중복·상태·배선·격리 게이트를 읽기 전용으로 공격하라고 보낸 실제 명령과 strict 출력 규칙 전문입니다.

실행 결과 전문:

```text
(stdout 0바이트)
(stderr 0바이트)
120초 동안 출력 없음. Ctrl-C 전송 뒤 "Execution error"가 한 번 표시됐고, 최종 프로세스 결과는 exit 0 / output 0바이트였습니다.
```

→ `VERDICT:`와 판정 본문이 없으므로 strict §5의 1차 검증으로 인정하지 않습니다. Claude 1차는 `NOT_RUN/빈 출력`이며 전체 strict 합격이라고 주장하지 않습니다.

### Codex 2차 독립 재공격 — 최초 `FAIL`

실행 표면 전문:

```text
spawn_agent(agent_type="verifier", task_name="phase_d_strict_v2")
Claude가 120초 빈 출력으로 NOT_RUN인 사실을 전달하고, fresh Codex 세션에 goal·계약·구현·시험·격리 게이트·v4 migration을 읽혀 exact allowlist, raw Gmail/PII, 후보 자동 병합, Calendar 중복 ID, 상태 사유 위조, CLI 고아, wrong-reason pass, live 과장을 read-only로 재현하도록 지시했습니다.
```

→ Claude가 유효한 본문을 내지 못한 뒤, 별도 Codex 검증 세션에 같은 목표를 독립 재공격하게 한 호출입니다.

판정 본문:

```text
VERDICT: FAIL

## 결론

Phase D는 큰 방향은 맞습니다. 기존 Supabase 표를 새로 만들지 않고 재사용하고, Gmail 원문 영구 보관·후보 자동 병합·운영 쓰기·라이브 연결은 막혀 있습니다.

하지만 blocker 2개가 남았습니다. 캘린더 목록에 같은 고유값이 중복으로 들어오면 “목록 항목 하나만 확인”이라는 계약과 달리 성공 처리됩니다. 또 수집을 실제로 시도하고 덜 끝낸 경우에도 사유를 “사전조건 부족”처럼 넣을 수 있어, 장애 원인을 속인 상태가 됩니다.

### [중간] 같은 캘린더 고유값이 중복된 경우에도 PASS가 됩니다

- 위치: humansearch/src/humansearch/admin_weekly_dashboard/source_policy.py:304
- 그 줄 역할: 일치한 캘린더를 calendar_id 기준으로 합쳐 중복 항목을 제거합니다.
- 사업 영향: 실제 목록이 이상하거나 중복 응답이 들어왔을 때 “목록 항목 하나만 확인”하지 못했는데도 일정 집계를 시작할 수 있습니다.

재현 출력:
same_id_summary_match PASS None cal-1
same_id_conflicting_summary PASS None sangmokang

### [중간] 시도 후 불완전한 실행에 NOT_RUN 계열 사유를 붙일 수 있습니다

- 위치: humansearch/src/humansearch/admin_weekly_dashboard/source_policy.py:350
- 그 줄 역할: 수집을 시도했지만 끝내지 못한 경우 FAIL을 반환합니다.
- 사업 영향: 실제 장애가 있었는데도 원인을 “사전조건 부족”처럼 기록해, 운영자가 권한 문제인지 수집 장애인지 잘못 판단할 수 있습니다.

재현 출력:
FAIL precondition_missing

## Claude ↔ Codex 대조

Claude 1차는 NOT_RUN/빈 출력이어서 재현할 Claude 결함이 없었습니다. Codex는 기존 표 재사용·Gmail 원문 금지·후보 자동 병합 금지·CLI·격리 게이트를 PASS로 확인했지만, duplicate Calendar ID와 FAIL/NOT_RUN 사유 위조를 FAIL로 판정했습니다.

## NOT_RUN / 남은 gap

- 실제 Gmail·ClickUp·Google Calendar·Supabase 계정에는 접근하지 않았습니다.
- goal 문서의 적대 검증 로그는 아직 실행 전으로 남아 있어 최종 PR 전 갱신이 필요합니다.
```

→ Codex 2차는 Claude 판정이 없다는 점을 숨기지 않고 독립 공격했으며, 중간 결함 2개를 실제 입력으로 재현했습니다.

### 2차 결함 수정

1. Calendar 매칭 결과를 `calendar_id` 딕셔너리로 접지 않고 실제 매칭 항목 리스트 수로 판정해, 같은 ID가 두 번 와도 `NOT_RUN/calendar_alias_ambiguous`가 되게 했습니다.
2. 실패 이유를 `NOT_RUN 전용`, `FAIL 전용`, 양쪽 허용(`permission_denied`)으로 분류하고 시도 여부와 모순되는 이유를 `ValueError`로 거부했습니다.
3. `SourceFailureReason`이 추가될 때 어느 분류에도 들어가지 않으면 실패하는 exhaustive invariant 시험을 추가했습니다.

수정 뒤 직접 재현:

```text
duplicate_calendar NOT_RUN calendar_alias_ambiguous None
reason_mismatch ValueError an attempted collection cannot use a NOT_RUN-only reason
```

→ 최초 두 결함의 같은 입력이 더 이상 PASS나 모순된 원인을 만들지 못합니다.

### Codex 2차 재검증 — 최종 `PASS`

재검증 요청 전문:

```text
두 FAIL 지적을 수정했습니다. resolve_calendar_alias는 dict dedupe를 제거해 실제 매칭 항목 수를 세고, collection_state는 NOT_RUN-only/FAIL-only reason을 시도 상태에 맞게 강제합니다. 회귀시험과 직접 재현을 다시 읽고 두 결함 해소 여부와 새 blocker를 VERDICT PASS|FAIL로 보고하세요. 코드 수정은 금지합니다.
```

→ 최초 Codex 검증에서 나온 두 결함을 고친 뒤, 같은 검증자에게 동일 입력의 재현과 새 blocker 탐색을 다시 요청했습니다.

판정 본문:

```text
VERDICT: PASS

## 결론
두 FAIL 지적은 해소됐습니다. 중복 캘린더 항목은 이제 성공하지 않고 NOT_RUN/calendar_alias_ambiguous가 되며, 시도한 수집에 precondition_missing 같은 미실행 전용 사유를 붙이면 ValueError로 막힙니다.

새 blocker는 못 찾았습니다.

## 판단 근거
- source_policy.py:327 — 캘린더 매칭 결과를 딕셔너리로 합치지 않고 실제 매칭 항목 리스트로 셉니다.
- source_policy.py:341 — 매칭 항목이 2개 이상이면 중복 고유값이어도 모호함으로 처리합니다.
- source_policy.py:369 — 전달받은 사유를 먼저 허용 목록 enum으로 정규화합니다.
- source_policy.py:374-377 — 시도한 수집에는 NOT_RUN 전용 사유를 허용하지 않습니다.
- source_policy.py:384-390 — 시도하지 않은 수집에는 실행 실패 전용 사유와 계획 상태에 맞지 않는 사유를 허용하지 않습니다.
- test_admin_source_policy.py:192-213 — 사유 상태 불일치 회귀시험이 추가됐습니다.
- test_admin_source_policy.py:289-300 — 같은 캘린더 고유값 중복 시험이 추가됐습니다.

## 실행 증거
targeted 27 passed
ruff: All checks passed!
mypy: Success: no issues found in 9 source files
duplicate_calendar NOT_RUN calendar_alias_ambiguous None
reason_mismatch ValueError an attempted collection cannot use a NOT_RUN-only reason
HumanSearch 전체 67 tests PASS
mutations 6/6 PASS
antiforge 3/3 PASS

## Gaps
- 실제 Gmail·ClickUp·Google Calendar·Supabase live 접근은 하지 않았습니다.
- 검증 당시 두 파일은 커밋 전이었습니다.

## Risks
- reason 분류는 수동 두 묶음이므로 새 SourceFailureReason 추가 때 시험과 함께 갱신해야 합니다.
```

→ 재검증 뒤 blocker는 0개입니다. 이후 수동 분류 누락 위험을 막는 exhaustive invariant 시험을 하나 더 추가했고 최종 전용 시험은 28개, 전체 시험은 68개로 다시 통과했습니다.

### Claude ↔ Codex 최종 교차표

| 항목 | Claude 1차 | Codex 2차 최초 | 수정 뒤 Codex 재검증 |
| --- | --- | --- | --- |
| 판정 본문 | `NOT_RUN` / 빈 출력 | `FAIL` | `PASS` |
| 기존 Supabase exact 표·필드 | 확인 못 함 | PASS | PASS |
| Gmail 원문 영구보관 금지 | 확인 못 함 | PASS | PASS |
| 후보 자동 병합 금지 | 확인 못 함 | PASS | PASS |
| Calendar 0/1/N·중복 ID | 확인 못 함 | 중복 ID `FAIL` | `PASS` |
| FAIL/NOT_RUN 사유 정합성 | 확인 못 함 | `FAIL` | `PASS` |
| 실제 CLI 배선 | 확인 못 함 | PASS | PASS |
| mutation/antiforge wrong-reason | 확인 못 함 | PASS | PASS |
| live 연결·쓰기·배포 | `NOT_RUN` | `NOT_RUN` | `NOT_RUN` |

→ Claude는 판정을 내지 못했고, Codex가 최초 두 결함을 잡은 뒤 같은 입력으로 수정 완료를 재확인했다는 교차 결과입니다. live 연결은 어느 검증에서도 실행하지 않았습니다.

### 최종 로컬 증거

```text
bash scripts/acceptance-hs-gates.sh
PASS: ruff clean in 16 python files
PASS: mypy strict clean in 16 source files
PASS: pytest collected 68 and passed
PASS: runtime import proof .../humansearch/src/humansearch/__init__.py
COLLECTED: 68

bash scripts/acceptance-hs-gates-mutations.sh
PASS: gates mutations blocked 6/6

bash scripts/acceptance-hs-gates-antiforge.sh
PASS: gates antiforge 3/3 (evidence forgery + CI disable blocked)

bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked

bash scripts/scan-data-exposure.sh all
PASS: 추적 파일 106개 검사, 위반 0건
PASS: 기록 전량 blob 515개 검사, 크기·경로 위반 0건
PASS: csv/tsv/sql 0개 검사(추적 106개 중), 개인정보 적재 0건

bash scripts/check-docs-sot.sh
OK: docs/sot 재구성 AC 전부 충족

bash scripts/session-status.sh
RED: 1/19 (acceptance-0-7.sh 제외 — CI 담당)

bash scripts/acceptance-0-2.sh
FAIL: .secret-patterns 없음/빈 파일 — AC 판정 불가
```

→ 기능·타입·위조·비밀·개인정보·문서 검사는 통과했습니다. 로컬 전용 `acceptance-0-2`는 worktree에 비추적 `.secret-patterns`가 없어 실행 전제를 충족하지 못했고, 이 한 건 때문에 세션 시작 장부가 RED 1/19입니다. live 외부 접근과 Claude 1차는 계속 `NOT_RUN`입니다.
