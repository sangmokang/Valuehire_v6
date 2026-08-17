# 고객사 × 포지션 맵 ("잔디밭") — 확정 스펙 2026-08-17

> 작성: Claude (Fable 5), 사장님 인터뷰 3회(구현 위치·시간 축·노랑 정의·설계 승인) 반영.
> 선행 문서: `admin-dashboard-engagement-heatmap-spec-adversarial-review-2026-08-16.md`(적대적 검증),
> `admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md`(주차 계약).
> 구현 대상 저장소: **Valuehire_v4** (admin.valuehire.cc 실제 배포체). 이 문서는 v6 docs에 정본으로 둔다.

## 1층 — 결론

`/admin/position-map` 화면을 v4 admin에 신설한다. 가로축 고객사, 세로축 포지션인 잔디밭 매트릭스로,
셀 색은 그 포지션의 최고 도달 단계(녹색>파랑>노랑>주황>투명), 셀 외곽선 겹 수는 배치 실행 횟수를 나타낸다.
셀 클릭 시 하단에 근거 원자료 리스팅이 나온다.

모든 숫자는 v4 Supabase의 SQL에서만 흘러나온다. 프론트는 재계산하지 않는다.
ClickUp 싱크는 **기존 `tools/clickup-sync/mirror-boards.mjs` 재사용**으로 충족한다(신설 아님).
유일한 신설 원장은 `proposal_send_events`(후보 개인별 제안 발송 이력) 하나다 — 사장님이
"노랑 = 포털 등록"이 아니라 "노랑 = 개인별 발송"을 선택했기 때문이다.

어제(8/16) 적대적 검증이 지적한 3대 붕괴 전제는 이 스펙에서 다음과 같이 해소된다.

| 8/16 지적 | 이 스펙의 해소 |
|---|---|
| 대상 스키마가 저장소에 없음 | 구현 대상을 v4로 확정. `pipeline_position_cards`·`pipeline_candidates`·`position_batch_*`·`sourcing_*` 전부 v4 마이그레이션에 실존 확인(§3 근거) |
| 로그인 필요 외부 사이트 무인 접근 미정의 | **외부 사이트를 읽지 않는다.** 모든 근거는 이미 내부 SQL에 적재된 원장뿐. 발송 이력도 발송 도구가 발송 시점에 내부 원장에 쓴다(스크레이핑 아님) |
| payload_hash 멱등성 자기모순 | 화면 텍스트 해시를 쓰지 않는다. 멱등키는 안정 식별자 조합 `(channel, candidate_source_key, position_ref)` 하나로 고정(§6) |

## 2층 — 판단 근거 (결정 카드)

### 결정 1 — 구현 위치는 v4 (사장님 확정)
- **무엇을**: admin.valuehire.cc의 실제 배포체인 v4에 화면·뷰·원장을 추가한다.
- **왜**: 필요한 SQL 원천이 전부 v4 Supabase에 있고, v6 `apps/admin`은 아직 존재하지 않는다.
- **v6 전면교체 goal과의 관계**: goal의 "v4 금지"는 v6 신규 코드의 실행 경계다. v4 자체에 화면을 더하는 것은 경계 위반이 아니다. 단, 이 스펙의 SQL 뷰·판정 계약은 v6 이관이 가능하도록 이 문서에 이식 가능한 형태로 고정한다.

### 결정 2 — ClickUp 싱크는 기존 미러 재사용 (사장님 지시 "클릭업 싱크 일단 맞추자"의 실현)
- `tools/clickup-sync/mirror-boards.mjs`: FY26_Candidates(901814621142) → `pipeline_candidates`, FY26_Clients(901814621569) → `pipeline_position_cards`. 기본 dry-run, `--apply`에서만 쓰기, 페이지네이션·429 재시도 내장.
- 신설하지 않는 이유: 이미 검증된(vitest 커버) 미러가 있는데 새로 만들면 두 개의 진실이 생긴다.
- 정례화: cron으로 `--apply --since-hours 2`를 주기 실행. 미러 최종 성공 시각을 화면에 상시 표기하고, 24시간 초과 시 STALE 경고를 띄운다. 미러 실패는 0이 아니라 `NOT_RUN`이다.

### 결정 3 — 시간 축은 "누적 상태 + 주차 선택" (사장님 확정)
- 기본 화면은 현재까지의 누적 최고 단계·누적 배치 수. 상단 주차 셀렉터로 과거 주차 선택 시, 그 주차 종료 시각(as-of) 이전 이벤트만으로 같은 판정을 재평가한다(되감기).
- 주차 경계는 8/16 goal 문서의 확정 계약을 그대로 쓴다: **일요일 00:00 KST ~ 다음 일요일 00:00 KST 직전**(반열린 구간, 일~토). 월요일 시작 창은 금지(8/16 goal 결정 카드 3).

### 결정 4 — 노랑은 개인별 발송 원장 기준 (사장님 확정)
- 포지션 단위 "포털 JD 등록 성공"(position_batch_steps)은 노랑의 근거가 아니다.
- 사람인·잡코리아·LinkedIn RPS 발송 도구가 **발송 확인 후** `proposal_send_events`에 1행을 쓴다. 노랑 = 그 포지션으로 발송 1건 이상.
- 대가: 발송 스킬들(saramin/jobkorea/linkedin-rps 계열)에 계측을 심는 선행 작업이 필요하고, 계측 이전의 과거 발송은 노랑으로 보이지 않는다. 과거분은 백필 대상으로 §9에 남긴다.

### 결정 5 — 색은 SQL이 판정하고 프론트는 렌더만 한다
- 판정은 마이그레이션으로 고정된 SQL 함수 하나(`admin_position_map_cells(as_of)`)에만 존재한다.
- LLM·프론트·수기 입력은 숫자와 색을 만들지 못한다(coding-principles: 수치는 코드 계산).

## 3층 — 계약 전문

### §3 데이터 소스 (전부 v4에 실존 확인, 2026-08-17 읽기 전용 조사)

| 용도 | 테이블/파일 | 근거 |
|---|---|---|
| 포지션·고객사 축 | `pipeline_position_cards` (company_name, position_title, stage, raw_clickup_payload) | `supabase/migrations/20260516180000_pipeline_boards.sql` |
| 후보 단계 | `pipeline_candidates` (stage) + `pipeline_stage_history` (from/to_stage, changed_at) | `20260507000000_pipeline.sql`, parity: `20260517010000` |
| ClickUp 미러 | `tools/clickup-sync/mirror-boards.mjs` + `lib/active-sync.mjs` (task 이름 파싱 "회사, 포지션 - 후보") | 동 파일 헤더 |
| 배치 실행 | `position_batch_runs` (run_id, triggered_at, status) + `position_batch_steps` (position_id, step, status, UNIQUE(position_id, step, run_id)) | `20260525120000_position_batch_state.sql`, step enum 16종: `20260720000004` |
| AI 서치 | `sourcing_runs`/`sourcing_results` (position_id, channel, candidate_name, created_at) + `ai_search_runs`/`ai_search_run_steps` | `20260516120002`, `20260601000000` |
| 발송 이력 | **신설** `proposal_send_events` (§6) | — |

### §4 셀 색 판정 계약

포지션 셀 1개 = `pipeline_position_cards` 1행. as-of 시각 `T`(누적 보기면 `now()`, 주차 보기면 그 주차의 `event_end_exclusive`) 이전 이벤트만 센다. 우선순위 위에서부터, 첫 일치가 색이다.

```text
GREEN  : 그 포지션에 연결된 후보 중, stage 도달 이력이 INTERVIEW_PLUS 집합에
         든 후보가 1명 이상 (도달 시각 <= T)
BLUE   : 위가 아니고, RECOMMEND_PLUS 집합 도달 후보 1명 이상
YELLOW : 위가 아니고, proposal_send_events 에 그 포지션 발송 1건 이상 (sent_at <= T)
ORANGE : 위가 아니고, AI 서치 흔적 1건 이상 —
         sourcing_results(run 경유, created_at <= T)
         또는 position_batch_steps(step='ai_search', status='success', created_at <= T)
TRANSPARENT : 그 외 (아무것도 안 한 포지션)
```

stage 집합은 FY26_Candidates 실제 상태명(8/16 읽기 전용 스냅샷)으로 고정하고 `contracts` JSON에 둔다.
실행 시 ClickUp 실제 상태명과 대조해 다르면 집계를 멈추고 `NOT_RUN`을 표기한다(조용히 계속 금지).

```json
{
  "INTERVIEW_PLUS": ["1차 면접/coffee chat", "2차면접", "3차면접", "면접후탈락",
                     "최종합격", "셀프드롭(최종합격후)", "입사", "입사후퇴사"],
  "RECOMMEND_PLUS": ["고객사추천", "코딩테스트사전과제", "서류탈락",
                     "코딩테스트 사전과제 탈락", "셀프드롭(서류, 면접)"]
}
```

- 판정은 `pipeline_stage_history`의 도달 이력(to_stage, changed_at)을 우선 사용한다. 이력이 없는 후보는 현재 `stage`로 판정하되 도달 시각을 알 수 없으므로 **누적 보기에서만** 반영하고 주차 되감기에서는 제외한다(시각 없는 사건으로 과거를 꾸미지 않는다 — 8/16 goal 원칙).
- `셀프드롭(서류, 면접)`은 서류/면접 어느 쪽 드롭인지 상태명으로 구분 불가 → 보수적으로 RECOMMEND_PLUS에 둔다(면접 도달을 과대 표시하지 않는다).
- `추천`(내부 추천, 고객사 전달 전)과 `제안(추천대기)`·`ai sourcing`은 파랑이 아니다. 파랑의 뜻은 "고객사에 실제로 추천됨"이다.

### §5 후보 ↔ 포지션 연결 계약

- 연결 키: `(company_name, position_title)` 정규화 일치. 정규화 = NFKC → trim → 연속 공백 1칸 → casefold. 그 이상(오탈자 유사도, LLM 추론)은 하지 않는다.
- 정규화 일치 실패 후보는 **버리지 않는다**. 맵 우측 "미연결" 패널에 건수와 목록을 표시해 사람이 ClickUp 표기를 고치게 한다. 미연결이 숨어서 셀이 투명해 보이는 것을 막는다.
- 서로 다른 채널의 후보를 공통 식별자 없이 동일인으로 합치지 않는다(8/16 검증 원칙 유지). 채널 내 식별자(`candidate_source_key`)만 신뢰한다.

### §6 신설 원장 — `proposal_send_events`

```sql
create table proposal_send_events (
  id                        uuid primary key default gen_random_uuid(),
  channel                   text not null
                              check (channel in ('saramin','jobkorea','linkedin_rps','email')),
  position_clickup_task_id  text,          -- 알 수 있으면 최우선 연결 키
  company_name              text not null, -- 없을 때의 연결 키 (§5 정규화)
  position_title            text not null,
  candidate_source_key      text not null, -- 채널 내 후보 식별자(프로필 URL/ID)
  candidate_display_name    text,
  sent_at                   timestamptz not null,  -- 실제 발송 시각. 수집 시각 아님
  sent_by                   text not null,         -- 실행 주체(스킬 이름 또는 사람)
  batch_run_id              text,                  -- position_batch_runs.run_id (있으면)
  evidence_uri              text,                  -- 발송 확인 캡처/로그 경로
  created_at                timestamptz not null default now(),
  unique (channel, candidate_source_key, position_clickup_task_id)
);
```

- **멱등**: 같은 채널·같은 후보·같은 포지션 재발송 시도는 UNIQUE로 1행이다. 화면 텍스트 해시는 어디에도 쓰지 않는다(8/16 지적 3 해소).
- **쓰기 시점**: 발송 도구가 발송 성공을 **확인한 뒤에만** insert한다. "보냈다는 요청"만으로 쓰지 않는다(readback 원칙). insert 실패 시 발송 도구는 실패를 보고하고 조용히 넘어가지 않는다.
- **계측 대상**: saramin-talent-sourcing, jobkorea-talent-sourcing, linkedin-rps 발송 경로. 계측 전 과거 발송의 백필은 별도 후속 작업(§9).
- RLS: 기존 `sourcing_*`와 동일 — service_role 쓰기, authenticated 읽기.

### §7 배치 횟수(외곽선)와 요약 지표

```text
batch_count(position, T)
  = count(distinct s.run_id)
    from position_batch_steps s join position_batch_runs r using (run_id)
    where s.position_id = position.raw_clickup_payload->>'id'  -- ClickUp task id (§11 대조 확인)
      and s.status = 'success'          -- 성공 스텝이 1개도 없는 run은 세지 않는다
      and r.triggered_at <= T
```

- 외곽선: 0회 = 없음, 1회 = 1선, 2회 = 2선, 3회 이상 = 3선 + 셀 모서리에 숫자.
- 요약 지표(맵 상단, 전부 같은 SQL 함수에서 파생):
  - 총 포지션(셀) 수 / 색 분포(투명·주황·노랑·파랑·녹색 각 건수)
  - 이번 주 수행 포지션 수 = 해당 주차 창 안에 이벤트(발송·서치·배치·단계 전이)가 1건 이상 발생한 포지션 수
  - 밀도 = 비투명 셀 / 전체 셀
  - 주차별 흐름: 최근 8주의 위 지표 시계열(작은 스파크라인)

### §8 화면 계약 — `/admin/position-map`

- 위치: v4 `app/(admin)/admin/position-map/page.tsx`. `AdminSubNav set="weekly"`에 탭 추가. 기존 `/admin/dashboard`(weekly-brief iframe)는 건드리지 않는다.
- 레이아웃: 가로축 = 고객사(포지션 많은 순 정렬), 각 고객사 컬럼 아래 그 고객사의 포지션 셀을 세로로 쌓는다. 포지션은 특정 고객사에 속하므로 전역 포지션 행 축은 만들지 않는다(대부분 빈 격자가 되는 것을 피함).
- 범위: 기본은 `stage`가 closed/complete 계열이 아닌 포지션. "종료 포함" 토글 제공.
- 셀 클릭 → 하단 상세 리스팅(원자료 그대로, 최신순):
  - AI 서치: `26.8.17 / 테크핀레이팅스, AI Engineer — 링크드인 24개` 형식. `sourcing_results`를 날짜×채널로 group by한 건수.
  - 발송: `26.8.15 / 사람인 발송 — 홍OO님 (sent_by)` — `proposal_send_events` 행.
  - 추천·면접: `26.08.13 고객사추천 — 김가가님` — `pipeline_stage_history` 전이 행. 후보 상세(학교·출신)는 `pipeline_candidates`에 있는 필드만 표시하고 추측 보강하지 않는다.
- 데이터 상태 배지(맵 상단 상시): 미러 최종 성공 시각, 24h 초과 시 STALE, 소스 조회 실패 시 그 소스만 `NOT_RUN — 이유`. **0으로 대체 표시 금지.**
- 주차 셀렉터: 일~토 창(§2 결정 3). 선택 시 URL 쿼리에 주차를 남겨 공유 가능하게 한다.

### §9 구현 단계 (v4에서, harness 게이트 준수)

각 단계는 독립 worktree + `task/<name>` 브랜치, RED 시험 먼저, `verify` 통과 후 PR.

1. **P1 — 원장·판정 SQL**: `proposal_send_events` 마이그레이션 + `admin_position_map_cells(as_of timestamptz)` SQL 함수 + 시드 fixture로 색 우선순위·되감기·멱등 시험.
2. **P2 — 발송 도구 계측**: 3개 발송 경로에 insert 계측. RED = "발송 성공 mock 후 원장 1행" / "발송 실패 시 0행" / "재실행 시 여전히 1행".
3. **P3 — 화면**: `/admin/position-map` + 상세 리스팅 + 상태 배지. 색 재계산 금지(API가 준 색만 렌더) 시험 포함.
4. **P4 — 미러 정례화**: mirror-boards cron + STALE 표시.
5. **후속(이번 범위 아님)**: 과거 발송 백필, v6 `apps/admin` 이관, 채널 간 동일인 연결 계약.

### §10 기계 인수 기준

1. 색 우선순위: 같은 포지션에 면접 이력+발송+AI서치가 다 있으면 녹색 하나만 나온다.
2. 되감기: T를 발송 전 주로 두면 그 셀은 노랑이 아니다(발송 사건이 미래이므로).
3. 멱등: 같은 (channel, candidate_source_key, position) insert 2회 → 1행, 노랑 판정 불변.
4. 시각 없는 사건: stage_history 없는 후보는 주차 보기에서 제외되고, 누적 보기에서만 반영된다.
5. 미연결: 정규화 불일치 후보는 사라지지 않고 미연결 패널 건수에 나타난다.
6. 상태명 계약: ClickUp 상태명 하나를 바꾼 fixture에서 집계가 `NOT_RUN`이 되고 0이 표시되지 않는다.
7. 배치 수: 성공 스텝 0개인 run은 외곽선에 안 세어지고, 3회 이상은 3선+숫자다.
8. 0건 검사 금지: 판정 시험은 실제 처리 행 수를 출력하고 0건이면 실패한다.
9. 프론트 무판정: 화면 코드에 색 판정 CASE·stage 문자열 비교가 존재하지 않는다(grep 검사).

### §11 미확정 (이름·기한 명시)

| 항목 | 내용 | 오너 | 기한 |
|---|---|---|---|
| position_id 형식 대조 | `position_batch_steps.position_id`와 `pipeline_position_cards`의 ClickUp task id 대응을 P1 착수 시 실데이터 5건으로 실측 확인 | 구현자 | P1 시작 시 |
| 발송 백필 범위 | 계측 이전 과거 발송을 얼마나 소급할지 | 사장님 | P2 완료 후 |
| PII 보관 | `candidate_display_name`·`candidate_source_key` 보관기간 — 기존 `sourcing_results.candidate_name` 정책과 함께 일괄 결정 | 사장님 | P1 머지 전 |
