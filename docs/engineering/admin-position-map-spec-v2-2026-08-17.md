# 고객사 × 포지션 맵 (“잔디밭”) 스펙 v2 — 2026-08-17

## 결론 — 사장님 브리핑

이 화면은 바로 만들면 안 됩니다. 먼저 들어오는 후보 상태와 포지션 연결을 고쳐, “무엇을 했는지”와 “언제 상태가 바뀌었는지”가 빠짐없이 남게 한 뒤에 화면을 만듭니다.

과거 주차를 되돌려 보는 기능은 이 수리를 배포한 뒤의 기간부터만 정확합니다. 그 이전 주차에는 숫자를 꾸며 내지 않고 **“이력 계측 전”**이라고 표시합니다.

운영 확인 네 가지는 현재 실행 환경의 연결 차단으로 끝내지 못했습니다. 실제 작업 횟수 연결이 맞는지 확인되기 전에는 외곽선을 0으로 보여 주지 않고 **“계산 중단”**으로 보여 줍니다.

후보 추천 여부는 고객사에 실제로 전달된 상태만 파란색으로 셉니다. 내부 추천·추천 대기와 섞이지 않도록 원래 상태명을 함께 보관합니다.

후보에게 제안을 보내는 과정은 보내기 전에 먼저 예약 기록을 남기고, 실제 발송 확인 뒤 성공으로 확정합니다. 중간에 프로그램이 꺼져도 같은 사람에게 자동으로 다시 보내지 않습니다.

이번 확인 단계에서는 운영 자료 읽기를 시도하고 이 설계 문서만 작성했습니다. 연결 차단으로 실제 자료는 읽지 못했으며, 코드·화면·자동 실행·자료 변경·외부 발송은 하지 않았습니다.

지금 사장님이 결정하실 것은 없습니다. 개인정보 보관 기간, 과거 발송을 어디까지 되살릴지, 실제 운영 반영 승인은 각 구현 단계의 정해진 멈춤점에서 받습니다.

## 판단 근거

### 결정 1 — 화면보다 미러 데이터 계약을 먼저 복구합니다

- **무엇을**: 구현 단계 맨 앞에 P0 “미러 데이터 계약 복구”를 두고 원래 상태명, 상태 변경 이력, 동기화 성공·실패를 함께 남깁니다.
- **왜**: 현재 미러는 여러 원래 상태를 하나의 상태로 합치고, 상태 현재값만 바꾸며, 이 화면이 읽을 동기화 장부에는 기록하지 않습니다.
- **버린 대안**: 현재값을 가지고 과거 주차를 추정하는 길은 과거에 없던 사실을 만드는 일이어서 버렸습니다.
- **대가**: P0 배포 전 주차는 되감아 볼 수 없고 “이력 계측 전”으로 남습니다.
- **되돌리는 법**: P0는 기존 현재값을 지우지 않는 추가 계약으로 만들고, 문제가 생기면 새 미러 쓰기를 멈춘 뒤 기존 읽기 화면으로 돌아갑니다.

### 결정 2 — 색은 저장된 영문 키와 보존된 원래 상태명으로만 판정합니다

- **무엇을**: 녹색은 저장된 영문 단계 키로, 파란색은 보존된 원래 상태명 **“고객사추천”**과 그 전이 이력으로 판정합니다.
- **왜**: 현재 저장값은 영문인데 v1은 한글을 비교했고, 현재 미러의 **recommended** 하나에는 고객사추천·내부 추천·추천 대기가 섞이기 때문입니다.
- **버린 대안**: **recommended**를 전부 파란색으로 세는 방법은 실제 고객사 전달을 과장하므로 버렸습니다.
- **대가**: P0에서 원래 상태를 다시 읽어 보존하기 전에는 일부 파란색을 확정할 수 없습니다.
- **되돌리는 법**: 판정 계약 JSON의 버전을 되돌릴 수 있지만, 모르는 키가 나타난 상태에서 자동으로 이전 계약을 쓰지는 않고 **NOT_RUN**으로 멈춥니다.

### 결정 3 — 후보와 포지션은 강한 연결부터 세 단계로 잇습니다

- **무엇을**: 포지션 카드 ID 직접 연결, 명시적인 포지션 쪽 ClickUp 작업 ID, 기존 **reconcileKey**(회사명과 직무명을 저장소의 기존 규칙으로 맞추는 함수) 순으로 연결합니다.
- **왜**: 현재 ClickUp 미러 코드는 후보의 직접 연결값을 null로 저장합니다. 운영 빈값 비율은 M3가 NOT_RUN이라 아직 수치로 확정하지 못했습니다.
- **버린 대안**: 후보 ClickUp 카드 자체 ID를 포지션 카드 ID처럼 쓰는 것과 새 유사도·인공지능 연결기를 만드는 것은 오연결 위험 때문에 버렸습니다.
- **대가**: 세 방법으로도 못 잇는 후보는 지도 셀에 들어가지 않고 별도 미연결 패널에 남습니다.
- **되돌리는 법**: 각 연결 행에 사용한 우선순위와 근거를 기록하므로 잘못된 낮은 순위 연결만 무효화하고 다시 계산할 수 있습니다.

### 결정 4 — 발송 기록은 예약과 확정의 두 단계로 만듭니다

- **무엇을**: 외부 발송 전에 **pending**(발송 예약) 행을 먼저 확정 저장하고, 외부 확인 후 같은 시도의 상태를 **sent** 또는 **failed**로 바꿉니다. 재시도와 사람이 의도한 재발송은 새 시도 행입니다.
- **왜**: 현재 Gmail 발송 도구는 외부 발송 후에만 성공을 확인하므로, 그 직후 프로그램이 꺼지면 내부에는 아무 기록이 없는 위험 구간이 생깁니다.
- **버린 대안**: 외부 발송 뒤 한 번만 기록하는 방법과, 남은 pending을 자동 재발송하는 방법은 중복 발송을 만들 수 있어 버렸습니다.
- **대가**: pending이 남으면 자동화는 멈추고 외부 읽기 확인 또는 사람 검토가 필요합니다.
- **되돌리는 법**: 발송 도구의 계측 호출을 끌 수 있지만, 이미 기록된 시도 행은 감사 증거이므로 삭제하지 않습니다.

### 결정 5 — 주간 계산과 무인 반복은 실패를 숫자 0으로 숨기지 않습니다

- **무엇을**: 일요일 00:00 KST부터 다음 일요일 00:00 KST 직전까지의 반열린 구간(시작은 포함하고 끝은 제외하는 시간 범위)을 쓰고, 출처·조회 시각·실패 상태를 결과에 함께 둡니다.
- **왜**: 기존 주간 스냅샷이 출처와 시간 범위를 남기는 패턴을 이미 갖고 있고, 이 화면만 다른 시간 규칙을 쓰면 같은 주의 숫자가 달라지기 때문입니다.
- **버린 대안**: 기존 함수의 월요일 시작 경계를 그대로 복사하는 길은 사장님이 확정한 일~토 주차와 충돌해 버렸습니다.
- **대가**: 한 출처가 실패하거나 알 수 없는 상태가 나타나면 해당 집계는 숫자 대신 **NOT_RUN**이 됩니다.
- **되돌리는 법**: 화면은 계산 결과만 렌더하므로 서버 계약 버전을 되돌리면 되고, 실패를 0으로 바꾸는 폴백은 두지 않습니다.

## 계약 전문

### 3-1. 범위, 정본, 현재 제한

구현 대상은 Valuehire_v4의 **/admin/position-map**이며, 문서 정본은 Valuehire_v6의 이 파일입니다. v1의 구현 위치, 기존 ClickUp 미러 재사용, 누적 보기와 주차 선택, 화면 배치 계약을 계승합니다.

이번 문서의 운영 실측 정본은 **docs/engineering/admin-position-map-phase0-measurement-2026-08-17.md**입니다. 네 측정은 현재 네트워크 차단으로 모두 **NOT_RUN**, 즉 **MEASURED: 0/4**입니다. 아래 계약은 저장소에서 확인한 사실과 고정값을 반영하되, M1·M2·M3·M4 성공 전 데이터 의존 분기를 확정하지 않습니다.

**높음 — 사업 영향:** 배치 외곽선은 M2가 전체 연결 일치를 증명하거나 불일치 교정을 끝낼 때까지 전부 **NOT_RUN**으로 둡니다. 표본 일부만 맞는 결과를 전체 성공처럼 표시하는 것은 금지합니다.

**치명 — 사업 영향:** P0 배포 전에는 원래 상태 전이 이력이 없으므로 과거 주차의 파랑·녹색을 재구성하지 않습니다. 해당 기간은 **PRE_INSTRUMENTATION / 이력 계측 전** 상태를 반환합니다.

### 3-2. 실물 코드 근거

| 계약 판단 | file:line 근거 | 그 줄이 하는 일 | 사업 해석 |
|---|---|---|---|
| 기존 미러 재사용 | **tools/clickup-sync/mirror-boards.mjs:2-8** | 후보·포지션 ClickUp 보드 대상과 기본 dry-run, apply 쓰기 모드를 선언합니다. | 새 미러를 만들 필요는 없지만 기존 미러의 쓰기 계약은 고쳐야 합니다. |
| 현재 미러의 이력 누락 | **tools/clickup-sync/mirror-boards.mjs:121-129** | 후보 현재 stage와 동기화 시각만 UPDATE합니다. | 과거 상태 변경이 사라져 주차 되감기가 불가능합니다. |
| 현재 원본 상태 보존의 불완전성 | **tools/clickup-sync/lib/board-mirror.mjs:86-109** | INSERT 때 memo.raw_status를 넣지만 jd_id는 null이며, 기존 행 UPDATE 계획에는 raw_status 갱신이 없습니다. | 처음 상태만 남고 다음 상태 변경의 원본이 낡을 수 있습니다. |
| 파랑 의미 붕괴 | **tools/clickup-sync/lib/board-mirror.mjs:13-32** | 고객사추천·추천·제안 상태를 모두 recommended로 합칩니다. | recommended만 보고 고객사 전달을 증명할 수 없습니다. |
| 기준 영문 매핑 | **supabase/migrations/20260517020000_candidates_board_clickup_parity.sql:101-120** | 한글 ClickUp 상태를 DB 영문 키로 바꿉니다. | 색 판정은 한글 현재값이 아니라 이 영문 저장값을 기준으로 해야 합니다. |
| 기존 변경 이력 형식 | **app/api/pipeline/candidates/[id]/route.ts:43-49** | candidate_id, from_stage, to_stage, changed_by를 이력에 넣습니다. | P0도 이 네 필드를 유지하되 현재값과 이력을 한 거래로 묶어야 합니다. |
| 기존 API의 거래 결함 | **app/api/pipeline/candidates/[id]/route.ts:36-50** | 현재값 UPDATE 뒤 이력 INSERT를 별도로 실행하고 이력 오류를 확인하지 않습니다. | P0는 이 구현을 복사하지 않고 둘 중 하나라도 실패하면 둘 다 취소해야 합니다. |
| 동기화 상태 장부 | **supabase/migrations/20260526010000_phase1_data_lake_schema.sql:46-57** | 마지막 시도·성공·오류·원본 요약 필드를 정의합니다. | 새 장부를 만들지 않고 이 장부를 확장해 STALE과 실패를 판정합니다. |
| 다른 러너의 성공·실패 기록 선례 | **tools/clickup-sync/lib/active-sync.mjs:146-179** | 성공과 오류를 clickup_sync_state에 각각 UPSERT합니다. | mirror-boards도 같은 장부에 기록하도록 연결해야 합니다. |
| 직접 포지션 연결 선례 | **app/api/pipeline/position-cards/[id]/ai-search/route.ts:733-736** | 조회에서 jd_id를 포지션 카드 id로 제한합니다. | 1순위 연결은 이미 실물 코드가 사용합니다. |
| AI Search 직접 적재 | **app/api/pipeline/position-cards/[id]/ai-search/route.ts:1111-1122** | 저장 행에 jd_id=card.id, stage=ai_search, source=ai_search:채널을 넣습니다. | 주황색은 이 직접 적재 경로를 반드시 포함해야 합니다. |
| AI 실행 원장의 연결 한계 | **supabase/migrations/20260601000000_ai_search_jobs_queue.sql:24-37** | 실행 상태와 시간은 있지만 포지션 연결 컬럼은 없습니다. | ai_search_runs는 주황 근거에서 제외합니다. |
| 소싱 결과의 포지션 연결 | **supabase/migrations/20260516120002_sourcing_results.sql:14-33** | sourcing_results가 run_id와 position_id를 갖고 인덱스를 둡니다. | run을 경유한 소싱 결과는 주황 근거로 쓸 수 있습니다. |
| 기존 이름 정규화기 | **tools/position-sync-audit/lib/reconcile.mjs:43-51** | 회사 별칭과 소문자·공백 정리를 거친 회사명|직무명 키를 만듭니다. | 새 정규화기를 만들지 않고 3순위에서 재사용합니다. |
| 현재 Gmail 발송 경계 | **tools/position-batch/send-offer-email.mjs:103-111** | Gmail 전송 뒤 메시지 ID와 SENT 라벨을 읽어 성공을 확인합니다. | 이 호출 전에 pending을 저장하고 읽기 확인 뒤 sent를 확정해야 합니다. |
| 배치 키의 약한 형식 | **supabase/migrations/20260525120000_position_batch_state.sql:22-38** | position_id가 제약 없는 text이고 run·step 단위 유일성만 있습니다. | M2가 NOT_RUN인 현재에는 실제 연결 여부를 스키마만으로 확정할 수 없습니다. |
| 주간 준거 | **supabase/migrations/20260725090000_weekly_brief_snapshot.sql:12-18,24-72,94-100** | KST 반열린 범위로 각 출처를 세고 출처·범위 설명을 결과에 둡니다. | 패턴은 재사용하되 월요일 경계는 일요일로 바꿉니다. |
| 화면 배선 시험 | **tests/adminMenuIa.test.ts:56-91** | SubNav 라우트 목록과 각 페이지 배선을 고정합니다. | 새 화면과 weekly 세트 배선을 시험 목록에 추가해야 합니다. |

→ 뭘 시켰나: 입력물에 적힌 파일 이름이 아니라 실제 적재·수정·발송 줄을 따라가 계약 근거를 만들었습니다.  
→ 뭐가 나왔나: 미러 현재값만 수정, 상태 축약, 직접 AI Search 적재, 이력의 비원자성, Gmail 읽기 확인 경계가 확인됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: 재사용할 기반은 있지만 P0 없이 화면부터 만들면 감사 결함이 그대로 재발합니다.

### 3-3. 미러 데이터 계약

P0 이후 후보 미러 한 건은 다음 세 결과를 **모두** 남겨야 성공입니다.

1. **pipeline_candidates 현재값**: 영문 stage와 별도 **source_stage_raw**(ClickUp 원래 상태명)를 최신 값으로 보존합니다.
2. **pipeline_stage_history 전이**: candidate_id, from_stage, to_stage, changed_by 기존 형식을 유지하고, **from_source_stage_raw, to_source_stage_raw, changed_at**을 함께 남깁니다.
3. **clickup_sync_state 실행 결과**: FY26_Candidates와 FY26_Clients 목록별 마지막 시도, 마지막 성공, 마지막 오류, 처리·실패 건수, 계약 버전을 남깁니다.

현재값 UPDATE와 전이 INSERT는 하나의 데이터베이스 거래(둘 다 성공하거나 둘 다 취소되는 단위)로 실행합니다. 전이 INSERT가 실패했는데 현재값만 바뀌는 결과는 금지합니다. 전체 미러 실행에 한 건이라도 실패하면 **last_success_at**을 갱신하지 않고 **last_error**와 실패 건수를 기록합니다.

P0 배포 시각은 **position_map_instrumented_at**으로 고정 기록합니다. 선택 주차의 끝이 이 시각 이하이면 색 결과 대신 **PRE_INSTRUMENTATION**을 반환하며, 화면에는 “이력 계측 전 — 이 주차의 과거 상태는 재구성하지 않습니다”를 표시합니다.

### 3-4. 상태 매핑과 색 판정 계약

다음 JSON은 판정 계약 v2의 확정 가능한 부분입니다. **clickupStatusToDbStage**는 백필 마이그레이션 CASE에서 가져왔고, 운영 저장값 목록은 M4가 NOT_RUN이라 문지기 값으로 남겼습니다. M4 성공 출력 없이는 observedDbStages를 배열로 바꾸거나 구현을 시작할 수 없습니다.

~~~json
{
  "contractVersion": "position-map-stage-v2",
  "clickupStatusToDbStage": {
    "서류탈락": "document_fail",
    "면접후탈락": "interview_fail",
    "고객사추천": "recommended",
    "포지션중단": "position_stop",
    "추천하려다fail": "recommend_fail",
    "셀프드롭(서류, 면접)": "self_drop_early",
    "셀프드롭(최종합격후)": "self_drop_late",
    "1차 면접/coffee chat": "interview_1",
    "입사": "joined",
    "코딩테스트 사전과제 탈락": "code_test_fail",
    "2차면접": "interview_2",
    "3차면접": "interview_3",
    "최종합격": "final_pass",
    "코딩테스트사전과제": "code_test",
    "입사후퇴사": "resigned"
  },
  "observedDbStages": ["ai_search", "code_test", "code_test_fail", "coding_test", "document", "document_fail", "document_review", "final_pass", "interview_1", "interview_2", "interview_3", "interview_fail", "joined", "pool", "position_stop", "recommend_fail", "recommended", "reference_check", "resigned", "self_drop", "self_drop_early", "self_drop_late", "sourced", "talent_pool"],
  "neutralDbStages": ["ai_search", "document", "document_review", "pool", "position_stop", "recommend_fail", "sourced", "talent_pool"],
  "ambiguousDbStages": ["self_drop", "coding_test", "reference_check"],
  "greenDbStages": [
    "interview_1",
    "interview_2",
    "interview_3",
    "interview_fail",
    "final_pass",
    "self_drop_late",
    "joined",
    "resigned"
  ],
  "blueRequiredRawStatus": "고객사추천",
  "blueDbStage": "recommended",
  "blueImpliedDbStages": ["document_fail", "code_test", "code_test_fail", "self_drop_early"],
  "unknownStagePolicy": "NOT_RUN"
}
~~~

→ 뭘 시켰나: 마이그레이션으로 확인된 한글 원본 상태와 영문 저장 키를 고정하고, 운영에서만 알 수 있는 값은 M4 문지기로 분리했습니다.  
→ 뭐가 나왔나: 백필 CASE의 15개 대응이 확인됐고, **V1(Claude) 재실행 M4로 운영 distinct 24종이 확정**되어 observedDbStages·중립·모호 분류가 채워졌습니다(실측 정본: 측정 보고 부록).  
→ 좋은 소식인가 나쁜 소식인가: 계약 매핑 밖 값 9종과 이상값(coding_test 1행, self_drop 35행)이 실재했으므로, 미지값 문지기가 없었다면 조용히 투명 처리될 뻔했습니다. 모호 3종(self_drop·coding_test·reference_check)은 P0에서 원본 상태로 분류하기 전까지 해당 셀 집계가 NOT_RUN입니다.

**V1 정정 (2026-08-18, Claude 적대 검증):** 위 관측·분류 배열과 blueImpliedDbStages는 검증자(V1)가 M4 실측 출력으로 확정해 채워 넣었다. blueImpliedDbStages는 v1 §4의 승인 의미(서류탈락·코딩테스트 계열·셀프드롭(서류,면접)은 고객사 전달 이후에만 도달하는 단계 — 사장님 인터뷰 반영분)를 복원한 것으로, v2 초판이 근거 설명 없이 이 집합을 떨어뜨렸던 것을 적대 검증이 잡았다(상세: 적대 검증 로그 신규 발견 1).

셀 1개는 포지션 카드 1행입니다. 같은 셀에 여러 근거가 있으면 아래 첫 일치 하나만 반환합니다.

~~~text
GATE
  알 수 없는 stage, source 조회 실패, 연결 계약 실패, 필요한 출처 미실행이 하나라도 있으면
  아래 색 판정을 실행하지 않고 즉시 NOT_RUN

GREEN
  P0 이후 기록된 후보 전이의 to_stage가 greenDbStages에 들어 있고 changed_at < 조회 끝 시각

BLUE
  GREEN이 아니며, 다음 중 하나 (기준 시각 < 조회 끝 시각)
  1) P0 이후 기록된 전이의 to_stage='recommended'이고 to_source_stage_raw='고객사추천'
  2) (V1 정정) 전이 to_stage 또는 누적 보기의 현재 stage가 blueImpliedDbStages에 포함
     — 고객사 전달 이후에만 도달 가능한 단계라는 v1 승인 의미의 복원

YELLOW
  위 둘이 아니며, 해당 포지션의 proposal_send_attempts에
  status='sent'이고 sent_at < 조회 끝 시각인 행이 1개 이상

ORANGE
  위 셋이 아니며, 아래 셋 중 하나가 조회 끝 시각 전에 존재
  1) sourcing_results를 sourcing_runs에 run_id로 연결한 포지션 결과
  2) position_batch_steps(step='ai_search', status='success')
  3) pipeline_candidates(source LIKE 'ai_search:%')

TRANSPARENT
  위 근거가 모두 정상 조회됐고 한 건도 없을 때만

~~~

→ 뭘 시켰나: 한 셀에 여러 근거가 있을 때 색 우선순위와 계산 중단 조건을 한곳에 고정했습니다.  
→ 뭐가 나왔나: GREEN→BLUE→YELLOW→ORANGE→TRANSPARENT 순서이며, 불명확한 값은 NOT_RUN입니다.  
→ 좋은 소식인가 나쁜 소식인가: 프론트가 색을 다시 해석할 여지를 없앴습니다.

누적 보기는 P0가 최신 ClickUp 원래 상태를 다시 읽어 현재값을 복구한 뒤 현재값과 P0 이후 이력을 함께 씁니다. 주차 보기는 P0 이후 전이만 씁니다. **ai_search_runs**는 포지션 연결 컬럼이 없으므로 주황 근거에서 제외하며, 연결 컬럼 신설도 이번 범위가 아닙니다.

### 3-5. 후보 ↔ 포지션 연결 계약

각 후보 연결은 아래 순서에서 처음 성공한 하나를 사용하고, **link_method, link_evidence, linked_at, contract_version**을 결과 근거에 남깁니다.

1. **DIRECT_JD_ID**: pipeline_candidates.jd_id = pipeline_position_cards.id::text.
2. **POSITION_CLICKUP_TASK_ID**: 후보 원본에서 명시적으로 추출·보존한 **position_clickup_task_id** = pipeline_position_cards.raw_clickup_payload->>'id'. 후보 카드 자신의 clickup_task_id는 포지션 키로 사용하지 않습니다.
3. **RECONCILE_KEY**: 후보 원본의 회사·직무와 포지션 카드의 회사·직무를 기존 **tools/position-sync-audit/lib/reconcile.mjs**의 reconcileKey로 비교합니다.

세 단계가 모두 실패하거나 한 후보가 같은 우선순위에서 여러 포지션에 걸리면 자동 선택하지 않습니다. **UNLINKED** 또는 **AMBIGUOUS**로 미연결 패널에 건수와 가린 목록을 노출합니다. 새 유사도·LLM 추론·후보 실명만으로의 연결은 금지합니다.

M3는 NOT_RUN이라 DIRECT_JD_ID의 운영 성공률은 수치로 확정하지 않습니다. 다만 **tools/clickup-sync/lib/board-mirror.mjs:86-89**가 ClickUp 후보 INSERT의 jd_id를 null로 두므로, 2·3순위를 계약에서 생략할 수 없습니다. 이 코드 사실은 이름 연결을 자동 승인한다는 근거가 아닙니다.

### 3-6. 배치 횟수 계약

M2는 NOT_RUN이므로 v1의 원본 ID 직접 조인은 현재 채택하지 않습니다. P0 첫 관문에서 측정 보고서의 M2 SELECT를 실행하고 다음 둘 중 하나만 선택합니다.

1. 전체 distinct position_id가 raw_clickup_payload->>'id'와 모두 일치하면 v1 §7 조인을 채택합니다.
2. 불일치가 하나라도 있으면 **position_batch_steps.position_card_id**를 포지션 카드 외래키로 추가하고, 미래 실행은 배치 입력을 만들 때 이 값을 필수로 기록합니다.
3. 불일치 키는 결정적 별칭 표 또는 원본 실행 입력 증거로만 교정합니다. 이름 유사도나 수기 추측은 금지합니다.
4. 교정하지 못한 키는 **position_batch_step_link_issues** 감사 목록에 원본 키·사유·확인 상태를 남깁니다.
5. M2 미실행 또는 미해결 1개라도 있으면 지도 전체의 batch_count와 외곽선은 **NOT_RUN**입니다.

M2 통과 또는 교정 완료 뒤 배치 횟수는 조회 끝 시각 이전의 성공 step이 하나 이상인 서로 다른 run_id 수입니다. 외곽선은 0회 없음, 1회 1선, 2회 2선, 3회 이상 3선과 실제 숫자입니다.

### 3-7. 발송 원장 계약

M1은 NOT_RUN이므로 운영 PostgreSQL 주버전을 확정하지 않습니다. M1 재실행 결과가 15 이상이면 빈값을 같은 값으로 취급하는 **UNIQUE NULLS NOT DISTINCT**를 사용하고, 15 미만이면 같은 열을 **COALESCE 식 유일 인덱스**(빈값을 고정 표식으로 바꿔 비교하는 중복 방지 인덱스)로 만듭니다. 아래 SQL은 15 이상일 때만 선택할 발췌이며, 이번 Phase 0에서 마이그레이션을 만들거나 적용하지 않습니다.

| 필드 | 계약 |
|---|---|
| id | 시도 행 UUID |
| send_intent_id | 같은 최초 발송 또는 retry 묶음에서 유지되는 UUID. 사람이 승인한 resend만 새 값 |
| resend_sequence | 최초 발송은 0. 사람이 승인한 재발송마다 같은 채널·후보·포지션 범위 안에서 1씩 증가 |
| attempt_no | 의도 안의 1부터 시작하는 시도 번호 |
| attempt_kind | initial, retry, resend 중 하나 |
| channel | saramin, jobkorea, linkedin_rps, email 중 하나 |
| candidate_source_key | 채널 어댑터가 원 출처의 안정 ID를 계약 버전에 따라 정본화한 비어 있지 않은 후보 식별자 |
| candidate_key_contract_version | 후보 식별자의 공백·대소문자·형식 규칙 버전 |
| position_card_id | **필수 canonical 포지션 카드 UUID. 이 값이 없으면 발송 원장 행을 만들지 않음** |
| position_clickup_task_id | 선택 증거용 포지션 ClickUp ID. 멱등 범위를 결정하지 않으며 모르면 null |
| status | pending, sent, failed 중 하나 |
| provider_request_key | 외부 조회에 쓸 안정 키. 화면 본문 해시 금지 |
| provider_message_id | 외부 읽기 확인에서 받은 ID |
| failure_reason | failed 사유 |
| requested_at / sent_at / finalized_at | 요청·확정 시각 |
| authorized_by / resend_reason | resend일 때 필수인 사람 의도 증거 |
| evidence_uri | 발송 확인 증거 위치 |
| created_at / updated_at | 내부 기록 시각 |

→ 뭘 시켰나: 한 번의 발송 시도를 재현하는 데 필요한 필드를 상태·연결·외부 확인·사람 승인으로 나눴습니다.  
→ 뭐가 나왔나: 후보 실명 없이도 pending부터 sent·failed까지 감사할 수 있는 계약입니다.  
→ 좋은 소식인가 나쁜 소식인가: 개인정보 복제를 줄이면서 재시도와 재발송을 구분할 수 있습니다.

**position_card_id가 반드시 있어야 합니다.** position_clickup_task_id는 연결 증거용 보조키일 뿐 멱등 범위를 결정하지 않습니다. P0 연결이 끝나지 않아 canonical position_card_id를 만들 수 없으면 pending도 만들지 않고 UNLINKED로 멈춥니다. 이 규칙은 같은 실제 포지션이 `(position_card_id, null)`과 `(null, position_clickup_task_id)`처럼 서로 다른 표현으로 들어와 활성 범위 인덱스를 우회하는 것을 막습니다.

필수 유일성은 다음 세 층입니다. 첫 번째는 한 의도 안의 시도 행 ID를 보호합니다. 두 번째는 **send_intent_id와 attempt_no를 일부러 빼고**, 서로 다른 실행 주체가 새 send_intent_id를 만들어도 같은 실제 발송 범위·재발송 차수의 pending·sent가 겹치지 않게 합니다. 세 번째는 resend_sequence와 무관하게 같은 실제 범위에 미확정 pending이 둘 생기지 않게 합니다.

~~~sql
alter table public.proposal_send_attempts
  alter column send_intent_id set not null,
  alter column resend_sequence set not null,
  alter column attempt_no set not null,
  alter column attempt_kind set not null,
  alter column channel set not null,
  alter column candidate_source_key set not null,
  alter column candidate_key_contract_version set not null,
  alter column position_card_id set not null,
  alter column status set not null,
  alter column provider_request_key set not null,
  alter column requested_at set not null,
  add constraint proposal_send_attempts_intent_attempt_uq
    unique (send_intent_id, attempt_no),
  add constraint proposal_send_attempts_position_required_ck
    check (position_card_id is not null),
  add constraint proposal_send_attempts_sequence_ck
    check (resend_sequence >= 0 and attempt_no >= 1),
  add constraint proposal_send_attempts_status_ck
    check (status in ('pending', 'sent', 'failed')),
  add constraint proposal_send_attempts_channel_ck
    check (channel in ('saramin', 'jobkorea', 'linkedin_rps', 'email')),
  add constraint proposal_send_attempts_candidate_key_ck
    check (
      candidate_source_key = btrim(candidate_source_key)
      and candidate_source_key <> ''
    ),
  add constraint proposal_send_attempts_kind_ck
    check (attempt_kind in ('initial', 'retry', 'resend')),
  add constraint proposal_send_attempts_attempt_shape_ck
    check (
      (attempt_kind = 'initial' and resend_sequence = 0 and attempt_no = 1)
      or (attempt_kind = 'retry' and attempt_no > 1)
      or (attempt_kind = 'resend' and resend_sequence >= 1 and attempt_no = 1)
    ),
  add constraint proposal_send_attempts_resend_auth_ck
    check (
      attempt_kind <> 'resend'
      or (authorized_by is not null and nullif(btrim(resend_reason), '') is not null)
    ),
  add constraint proposal_send_attempts_terminal_evidence_ck
    check (
      (status = 'pending' and finalized_at is null)
      or (
        status = 'sent'
        and sent_at is not null
        and finalized_at is not null
        and nullif(btrim(provider_message_id), '') is not null
      )
      or (
        status = 'failed'
        and finalized_at is not null
        and nullif(btrim(failure_reason), '') is not null
      )
    );

create unique index proposal_send_attempts_active_scope_uq
on public.proposal_send_attempts (
  channel,
  candidate_source_key,
  position_card_id,
  resend_sequence
)
nulls not distinct
where status in ('pending', 'sent');

create unique index proposal_send_attempts_one_pending_scope_uq
on public.proposal_send_attempts (
  channel,
  candidate_source_key,
  position_card_id
)
nulls not distinct
where status = 'pending';
~~~

→ 뭘 시켰나: 같은 의도·같은 시도 번호를 막는 행 식별 규칙과, 의도 ID가 달라도 같은 채널·후보·canonical 포지션·재발송 차수의 활성 발송을 막는 업무 규칙을 분리했습니다.  
→ 뭐가 나왔나: 이 블록은 PostgreSQL 15 이상 분기입니다. M1이 15 미만이면 NULLS NOT DISTINCT를 사용하지 않고 같은 유일성 열의 nullable 값에 COALESCE 고정 표식을 적용해야 하며, 두 분기 모두 같은 중복 시험을 통과해야 합니다.  
→ 좋은 소식인가 나쁜 소식인가: 서로 다른 send_intent_id·보조키 표현·resend_sequence로 미확정 발송을 우회할 수 없고, failed 뒤 retry와 이전 pending을 확정한 뒤 사람이 승인한 다음 resend_sequence는 허용됩니다.

M1이 PostgreSQL 15 미만으로 나오면 위 두 부분 유일 인덱스 대신 아래 COALESCE 식 유일 인덱스를 사용합니다. 핵심 열은 별도 NOT NULL 제약도 유지하며, 아래 식은 NULL이 다시 허용되는 스키마 변경이 생겨도 같은 업무 범위 중복을 막는 방어선입니다.

~~~sql
create unique index proposal_send_attempts_active_scope_uq
on public.proposal_send_attempts (
  coalesce(channel, '<NULL>'),
  coalesce(candidate_source_key, '<NULL>'),
  coalesce(position_card_id::text, '<NULL>'),
  coalesce(resend_sequence, -1)
)
where status in ('pending', 'sent');

create unique index proposal_send_attempts_one_pending_scope_uq
on public.proposal_send_attempts (
  coalesce(channel, '<NULL>'),
  coalesce(candidate_source_key, '<NULL>'),
  coalesce(position_card_id::text, '<NULL>')
)
where status = 'pending';
~~~

→ 뭘 시켰나: PostgreSQL 15 미만에서도 빈값을 서로 다른 값처럼 통과시키지 않는 대체 인덱스 전문을 고정했습니다.  
→ 뭐가 나왔나: M1 주버전 결과에 따라 둘 중 한 분기만 선택하며, 같은 발송 범위에 pending·sent가 겹치지 않는 계약은 같습니다.  
→ 좋은 소식인가 나쁜 소식인가: M1이 아직 NOT_RUN이어도 구현자가 임의 문법을 고를 수는 없지만, 실제 버전 확인 전에는 어느 분기도 적용하면 안 됩니다.

후보 식별자는 자유 입력 문자열이 아닙니다. 채널별 어댑터가 제공자 원문의 안정 ID만 받아 앞뒤 공백을 제거하고, 제공자 계약이 대소문자를 구분하지 않는다고 명시한 채널만 소문자로 맞춥니다. 대소문자 의미가 불명확하거나 사람이 조립한 값은 추측해 고치지 않고 발송을 중단합니다. 어댑터 규칙과 candidate_key_contract_version은 함께 배포하며, 유일 인덱스에는 정본화가 끝난 candidate_source_key만 들어갑니다.

채널별 **candidate_key_contract_state** 행은 active_version과 READY/MIGRATING/FAILED 상태를 가집니다. 발송 경계 함수와 버전 교정은 같은 채널 잠금을 잡고, 함수는 READY이면서 요청 버전=active_version일 때만 pending을 만듭니다. 버전 교정은 기존 키 전부 재계산, 충돌 0건, active_version 교체를 한 거래로 끝내며 실패하면 전부 이전 READY 상태로 되돌아갑니다. candidate_key_contract_version은 감사를 위한 값이지 유일 인덱스 차원이 아닙니다. 인덱스에 버전을 넣으면 같은 후보의 이전·새 버전 행을 오히려 서로 다른 키로 허용하므로 금지합니다.

원장 테이블의 직접 INSERT·UPDATE 권한은 발송 주체에서 제거하고 단일 보안 경계 함수만 호출하게 합니다. 그 함수는 채널·후보키를 먼저 검증하고 새 행을 pending으로만 만들며, 기존 pending은 sent 또는 failed로만 확정합니다. sent·failed를 pending으로 되돌리거나 terminal 행의 scope·intent·attempt 값을 바꾸는 UPDATE는 거부합니다. retry와 resend는 아래 규칙에 따른 새 행 INSERT만 허용합니다.

발송 순서는 고정입니다.

1. 후보와 포지션 연결을 먼저 확정해 canonical position_card_id를 얻습니다. 이 값이 null이면 보조 ClickUp ID가 있어도 발송하지 않습니다.
2. 같은 실제 범위를 transaction-scoped advisory lock 또는 동등한 직렬화 경계로 먼저 잠급니다. 같은 차수의 sent면 성공 재사용, 어떤 차수든 pending이면 retry와 resend 모두 금지합니다.
3. 활성 행이 없으면 최초 발송은 resend_sequence=0, attempt_no=1로 **pending** 행을 INSERT하고 커밋합니다. failed만 남아 있는 retry는 같은 send_intent_id·resend_sequence와 증가한 attempt_no로 pending을 INSERT합니다. 같은 실제 범위의 다른 send_intent_id가 경합해도 인덱스가 한 행만 허용합니다.
4. 외부 발송을 한 번 호출합니다.
5. 외부 읽기 확인으로 메시지 ID와 성공 상태를 확인합니다.
6. 확인되면 같은 시도 행을 sent로 확정합니다. 외부 실패가 확정되면 failed와 사유를 씁니다.
7. 외부 성공 여부가 불명확하거나 프로세스가 꺼져 pending이 남으면 재실행은 발송하지 않고 외부 읽기 확인·사람 검토로 갑니다.
8. retry는 같은 send_intent_id의 직전 행을 잠가 **동일한 resend_sequence**와 증가한 attempt_no인지 교차 행 검증한 뒤 만드는 새 행입니다. resend는 직렬화 경계 안에서 기존 최대값의 정확히 +1인 resend_sequence를 계산하고, 새 send_intent_id·authorized_by·resend_reason을 가진 새 행으로 INSERT하며 이전 행을 덮어쓰지 않습니다. 미확정 pending이 있으면 사람 승인이 있어도 resend하지 않습니다.

**치명 — 사업 영향:** “외부 성공 → 내부 sent 확정 전 종료” 장애 시험에서 재실행의 외부 발송 호출 수는 0이어야 합니다. pending이 있다는 이유로 자동 재발송하면 전체 Phase를 반려합니다.

후보 이름·연락처·프로필 URL 원문은 원장 필수 필드가 아닙니다. candidate_source_key 보관 기간은 미확정 표의 사장님 결정 전까지 운영 적용을 멈춥니다.

### 3-8. 주차, 출처, 데이터 상태 계약

- 기본 누적 보기의 조회 끝은 현재 시각입니다.
- 주차 보기의 시작은 선택한 일요일 00:00:00 KST, 끝은 다음 일요일 00:00:00 KST이며 **start <= event_at AND event_at < end**입니다.
- URL은 선택 주차를 보존해 같은 화면을 공유할 수 있어야 합니다.
- 응답에는 **window_start, window_end_exclusive, timezone, generated_at, source_tables, source_max_seen_at, contract_versions, result_status**를 포함합니다.
- 결과 상태는 **OK, STALE, NOT_RUN, PRE_INSTRUMENTATION** 중 하나입니다.
- clickup_sync_state의 last_success_at이 24시간을 넘으면 STALE입니다. 마지막 실행 오류가 있거나 필요한 목록 성공 기록이 없으면 ClickUp 의존 집계는 NOT_RUN입니다.
- 모르는 stage나 원래 상태가 발견되면 stage 의존 집계는 NOT_RUN이며 0으로 대체하지 않습니다.
- 각 출처 실패는 출처별로 표시하고 전체 색 우선순위에 필요한 상위 출처가 불명확하면 셀 색도 NOT_RUN입니다.

### 3-9. 화면 계약 — /admin/position-map

v1 §8을 다음과 같이 계승합니다.

- 위치는 v4 **app/(admin)/admin/position-map/page.tsx**입니다.
- **AdminSubNav set="weekly"**에 “포지션 맵” 탭을 추가합니다. 기존 **/admin/dashboard**는 건드리지 않습니다.
- 가로축은 고객사이며 포지션 많은 순입니다. 각 고객사 아래 포지션 셀을 세로로 쌓고 전역 포지션 행 축은 만들지 않습니다.
- 기본 범위는 종료되지 않은 포지션이고 “종료 포함” 토글을 둡니다.
- 셀은 API가 준 색·외곽선·상태만 렌더합니다. 프론트에서 stage 비교나 색 재계산을 금지합니다.
- 셀 클릭 시 AI Search 날짜×채널 건수, 발송 sent 시도, 추천·면접 전이 원자료를 최신순으로 보여 줍니다.
- 상단에는 총 포지션, 색 분포, 주간 수행 포지션, 밀도, 최근 8주 흐름과 미러 성공 시각을 둡니다.
- 실패는 0이 아니라 NOT_RUN, 오래된 자료는 STALE, P0 이전 주차는 “이력 계측 전”으로 표시합니다.
- 미연결 패널은 UNLINKED와 AMBIGUOUS를 분리하고 후보 표시는 가립니다.
- **tests/adminMenuIa.test.ts**의 weekly 세트 예상 라우트와 페이지 배선 목록에 새 경로를 추가합니다.

### 3-10. 개인정보 전달 정책

후보 실명·연락처·프로필 URL 원문은 Claude, Codex, ChatGPT 또는 그 밖의 클라우드 모델 프롬프트에 넣지 않습니다. 모델에는 익명 구조, 집계, 마스킹 표본만 전달합니다.

문서·검증 로그·시험 fixture도 같은 규칙을 따릅니다. 운영 오류를 재현해야 하면 로컬에서 원문을 읽고 산출물에는 **홍\*\***, **linkedin.com/in/\*\*\*** 같은 가림값과 집계만 남깁니다. 개인정보 보관 기간이 정해지기 전에는 P1 운영 적용을 하지 않습니다.

### 3-11. 비범위

- ai_search_runs에 포지션 연결 컬럼 신설
- 과거 P0 이전 상태 이력의 추정 백필
- 과거 발송 백필의 실제 실행
- v6 apps/admin 이관
- 채널 간 동일인 통합
- 새 이름 정규화기·유사도·LLM 포지션 연결
- ClickUp 자동 수정
- 운영 마이그레이션 적용, cron 등록, 외부 발송

## 구현 단계

모든 구현은 Valuehire_v4에서 독립 worktree, RED 시험, 최소 구현, 검증, 적대 검증 순서로 진행합니다. 운영 DB 적용·ClickUp 쓰기·cron 등록·실제 발송 경로 병합 직전에는 사장님 승인 없이는 멈춥니다.

### P0 — 미러 데이터 계약 복구

범위:

1. source_stage_raw 현재값과 원래 상태 전이 필드를 추가합니다.
2. 현재 stage와 pipeline_stage_history를 한 거래로 기록하는 RPC 또는 동등한 원자 경계를 만듭니다.
3. mirror-boards가 clickup_sync_state에 성공·실패·건수·계약 버전을 기록하게 합니다.
4. M2를 실행해 전체 일치면 v1 조인을 채택하고, 불일치면 position_batch_steps.position_card_id를 미래 실행에 필수로 연결한 뒤 기존 키를 전수 교정합니다.
5. M3·M4를 실행하고, ClickUp 원본 상태와 운영 stage 전부를 출처·업무 의미별로 계약에 편입하거나 NOT_RUN 대상으로 고정합니다.
6. P0 배포 시각을 저장해 이전 주차를 PRE_INSTRUMENTATION으로 막습니다.

종료 조건: M1~M4 성공, 원본 상태 보존, 원자적 전이, 성공·실패 상태 장부, M2 미해결 0개, ClickUp-origin 모호 상태 0개를 기계 시험으로 증명합니다. 하나라도 실패하면 P1로 가지 않습니다.

### P1 — 발송 원장과 판정 함수

범위:

1. M1 주버전 분기에 따라 proposal_send_attempts 2단 상태 원장, candidate_key_contract_state 버전 문지기, 핵심 필드 NOT NULL·채널 enum·채널별 후보키 정본화와 빈값 포함 유일성을 구현합니다.
2. 주간·누적 판정 함수가 색, 외곽선, 미연결, 출처, 상태를 한 계약으로 반환하게 합니다.
3. 일요일 KST 반열린 구간과 출처 메타데이터를 구현합니다.
4. 알 수 없는 값·조회 실패·0행 시험을 fail-closed로 만듭니다.

종료 조건: 색 우선순위, 되감기, 중복, 연결, NOT_RUN, 출처가 모두 RED→GREEN입니다. 개인정보 보관 기간 결정과 운영 적용 승인이 없으면 마이그레이션은 적용하지 않습니다.

### P2 — 발송 경계 계측

범위:

1. 사람인, 잡코리아, LinkedIn RPS, Gmail email의 실제 외부 발송 경계에 pending→readback→sent/failed 흐름을 연결합니다.
2. 각 채널의 dry-run은 원장과 외부 모두 0건 쓰기입니다.
3. 재시도는 failed 뒤 새 retry 행, 재발송은 사람 승인 뒤 새 resend 행으로만 허용합니다.

종료 조건: 성공, 명시적 실패, 재실행, pending 복구, 재시도, 재발송, 각 채널 readback 시험과 R11 강제 종료 시험이 모두 통과합니다.

### P3 — 화면

범위:

1. /admin/position-map과 상세 리스팅, 상태 배지, 미연결 패널, 주차 선택을 구현합니다.
2. API 결과만 렌더하고 색·단계 판정을 프론트에 두지 않습니다.
3. AdminSubNav weekly와 adminMenuIa.test.ts 배선 목록을 갱신합니다.

종료 조건: 접근성, 빈 상태, NOT_RUN·STALE·PRE_INSTRUMENTATION, 프론트 무판정 grep, adminMenuIa가 모두 통과합니다.

### P4 — 미러 정례화와 무인 반복 안전장치

범위:

1. 중복 실행 잠금을 둡니다.
2. 연속 실패 임계값에서 알림을 보내고 자동 실행을 중지합니다.
3. 운영 등록 전 실데이터 읽기만 하는 그림자 실행을 서로 다른 시점에 2회 수행합니다.
4. clickup_sync_state 기반 STALE과 실패 알림을 연결합니다.

종료 조건: 겹친 실행 1개만 진행, 연속 실패 후 추가 쓰기 0건, 알림 증거, 그림자 실행 2회 쓰기 0건이 입증돼야 합니다. cron 등록은 별도 승인 전 금지합니다.

## 기계 인수 기준

| AC | 기계 판정 | 연결 요구 |
|---|---|---|
| AC-01 | 고객사추천, 추천, 제안(추천기대후보자) fixture를 넣으면 DB stage는 같을 수 있어도 source_stage_raw가 각각 보존되고 BLUE는 고객사추천만 1건입니다. | R2 |
| AC-02 | stage 현재값 UPDATE 뒤 이력 INSERT를 강제 실패시키면 둘 다 0건 변경입니다. 정상 시 현재값 1건과 전이 1건입니다. | R3 |
| AC-03 | mirror 전체 성공은 last_success_at과 처리 건수를 갱신하고, 부분 실패는 last_success_at 불변·last_error와 실패 건수 기록입니다. | R3, R10 |
| AC-04 | P0 배포 시각 전 주차 요청은 PRE_INSTRUMENTATION이며 색 숫자를 반환하지 않습니다. | R3 |
| AC-05 | 계약 JSON 밖 stage fixture와 현재 self_drop 모호 fixture는 NOT_RUN이며 0 또는 transparent가 아닙니다. | R4 |
| AC-06 | 연결 fixture는 DIRECT_JD_ID → POSITION_CLICKUP_TASK_ID → RECONCILE_KEY 순서를 지키고, 동순위 다중 매치는 AMBIGUOUS입니다. | R5 |
| AC-07 | 세 연결이 모두 실패한 후보는 삭제되지 않고 UNLINKED 건수가 1 증가합니다. | R5 |
| AC-08 | sourcing_results, 성공 ai_search step, source ai_search:linkedin 각각만 있어도 ORANGE이며 ai_search_runs만 있으면 ORANGE가 아닙니다. | R1, R6 |
| AC-09 | M2가 NOT_RUN이거나 불일치 교정 뒤 position_batch_steps.position_card_id가 null 또는 link issue가 1건이면 batch_count는 NOT_RUN입니다. M2 전체 일치 또는 교정 완료 뒤 성공 run 0개는 외곽선 0, 3개는 3선+숫자 3입니다. | R8 |
| AC-10 | 같은 후보 fixture의 채널 대소문자·앞뒤 공백·후보키 공백/계약상 동치 대소문자 변형은 채널 enum과 어댑터 정본화에서 각각 거부 또는 같은 키로 수렴합니다. 후보키 계약 상태가 MIGRATING/FAILED이거나 요청 버전이 active_version과 다르면 pending은 0건이며, 버전 교정 중 강제 종료는 이전 READY 상태와 키를 전부 보존합니다. 그 뒤 같은 채널·후보·canonical position_card_id·resend_sequence에 **서로 다른 send_intent_id** 두 개를 동시에 pending INSERT하면 position_clickup_task_id가 null/값으로 서로 달라도 두 번째를 활성 범위 인덱스가 거부합니다. 미확정 pending이 있는 동안에는 다른 resend_sequence도 거부합니다. 첫 행을 failed로 확정하면 같은 resend_sequence의 retry는 허용되지만 resend_sequence가 다른 retry는 함수가 거부합니다. sent로 확정하면 같은 차수는 차단되며, 직렬화 경계에서 계산한 최대값+1과 사람 승인 정보가 있는 resend만 허용됩니다. position_card_id·status·channel·candidate_source_key 등 핵심 필드가 null이면 첫 INSERT부터 거부됩니다. | R7 |
| AC-11 | pending→sent와 pending→failed만 허용하고 sent·failed를 pending으로 되돌리지 않습니다. retry·resend는 기존 행 UPDATE가 아니라 attempt_no가 증가한 INSERT입니다. | R7 |
| AC-12 | 외부 발송 성공 직후 sent 확정 전에 프로세스를 강제 종료하고 재실행하면 외부 send 호출 0건, 중복 sent 0건입니다. | R11 |
| AC-13 | 일요일 00:00 KST 사건은 포함되고 다음 일요일 00:00 KST 사건은 제외됩니다. 응답에 범위·출처·생성 시각이 있습니다. | R10 |
| AC-14 | weekly 세트에 /admin/position-map이 있고 page.tsx가 AdminSubNav를 포함하며 tests/adminMenuIa.test.ts가 통과합니다. | R9 |
| AC-15 | 화면 소스에서 색 CASE와 stage 문자열 비교 grep 결과가 0건이며 API fixture 색을 그대로 렌더합니다. | v1 생존 AC 9 |
| AC-16 | 같은 포지션에 GREEN·YELLOW·ORANGE 근거가 있어도 GREEN 하나만 반환합니다. | v1 생존 AC 1 |
| AC-17 | 미연결·상태명·판정 시험은 실제 처리 행 수를 출력하고 0행이면 시험 자체가 실패합니다. | v1 생존 AC 5, 6, 8 |
| AC-18 | 중복 cron 두 개 중 하나만 잠금을 얻고, 연속 실패 임계값 뒤 추가 쓰기 0건과 알림 1건이며 그림자 실행 2회 쓰기 0건입니다. | R12 |
| AC-19 | 모델 호출 fixture와 저장된 프롬프트를 검사해 후보 실명·이메일·전화·원문 프로필 URL이 0건입니다. | R13 |
| AC-20 | 소스 하나를 강제 실패시키면 관련 숫자는 NOT_RUN이며 0으로 대체되지 않습니다. | R10 |

→ 뭘 시켰나: 문장형 요구를 자동 시험이 셀 수 있는 입력·출력으로 바꿨습니다.  
→ 뭐가 나왔나: R1~R13과 v1에서 살아남은 화면·미연결·0건·프론트 무판정 계약이 모두 시험에 연결됐습니다.  
→ 좋은 소식인가 나쁜 소식인가: 구현자가 임의로 “대체로 맞음”을 선언할 수 없게 됐습니다.

### R1~R13 추적표

| ID | v2 해소 | 판정 목표 |
|---|---|---|
| R1 | ai_search_runs를 주황 근거와 범위에서 제외했습니다. | CONFIRM |
| R2 | 원래 상태 고객사추천만 BLUE로 고정하고 P0 보존을 신설했습니다. | CONFIRM |
| R3 | 원자적 현재값+이력, P0 이후 되감기, 이전 표식을 고정했습니다. | CONFIRM |
| R4 | 백필 마이그레이션 영문 매핑을 고정했고, M4 성공 전 observedDbStages와 집계를 NOT_RUN으로 막았습니다. | CONFIRM 목표 — M4 실행 필요 |
| R5 | jd_id→포지션 ClickUp ID→reconcileKey, 미연결 패널을 고정했습니다. | CONFIRM |
| R6 | pipeline_candidates.source LIKE 'ai_search:%'를 주황에 추가했습니다. | CONFIRM |
| R7 | M1의 15 이상·미만 분기와 pending→sent/failed, 새 attempt를 고정했습니다. | CONFIRM 목표 — M1 실행 필요 |
| R8 | M2 전체 일치 때만 v1 조인을 채택하고, 그 밖에는 P0 교정과 외곽선 NOT_RUN을 고정했습니다. | CONFIRM 목표 — M2 실행 필요 |
| R9 | adminMenuIa.test.ts weekly 세트와 페이지 배선을 AC에 넣었습니다. | CONFIRM |
| R10 | 일요일 KST 반열린 구간, 출처, 실패 0 금지, sync_state STALE을 고정했습니다. | CONFIRM |
| R11 | 외부 성공 직후 강제 종료와 재실행 send 0건을 AC-12에 넣었습니다. | CONFIRM |
| R12 | 잠금, 연속 실패 알림+자동 중지, 그림자 실행 2회를 AC-18에 넣었습니다. | CONFIRM |
| R13 | 후보 원문을 클라우드 모델에 넣지 않는 정책과 AC-19를 신설했습니다. | CONFIRM |

→ 뭘 시켰나: 감사 R1~R13 각각이 어느 계약과 시험으로 닫혔는지 대조했습니다.  
→ 뭐가 나왔나: 13개 전부 목표 판정 CONFIRM이며 검증자가 항목별로 반증해야 합니다.  
→ 좋은 소식인가 나쁜 소식인가: 누락 여부를 표 한 장으로 기계·육안 교차 확인할 수 있습니다.

## 미확정 표

v1 §11의 세 항목을 삭제하지 않고 실측 상태에 맞게 갱신했습니다.

| 이름 | 현재 상태와 필요한 결정 | 오너 | 기한 |
|---|---|---|---|
| position_id 형식 대조·교정 | M2가 NOT_RUN입니다. 전체 일치 여부를 실행으로 확정하고, 불일치면 결정적 교정과 미래 position_card_id 필수화를 완료해야 합니다. | P0 구현자 | P0 시작 전 |
| 발송 백필 범위 | 계측 이전 과거 발송을 소급 안 함 / FY26 시작 / 증빙 있는 건만 중 선택합니다. 실행은 이번 범위가 아닙니다. | 사장님 | P2 완료 후 |
| PII 보관 | candidate_source_key와 기존 후보 식별 자료 보관 기간·마스킹·삭제 시점을 정합니다. 결정 전 P1 운영 적용 금지입니다. | 사장님 | P1 머지 전 |
| 운영 적용 승인 | 마이그레이션, ClickUp 쓰기, 발송 경로 병합, cron 등록을 각각 승인합니다. | 사장님 | 각 하드 멈춤점 직전 |
| M2 불일치 분류 | M2에서 불일치가 나오면 수기 슬러그·ClickUp ID·레거시 ID별 증거와 교정 규칙을 확정합니다. | P0 구현자 | P0 RED 종료 전 |
| 발송 채널 범위 문구 | 킥오프의 “3개 경로”와 v1 채널 4종·현 Gmail 도구의 불일치를 확정합니다. 본 v2는 누락 방지를 위해 4채널을 계약했습니다. | 사장님 + P2 구현자 | P2 RED 작성 전 |

→ 뭘 시켰나: 이미 결정된 기술 계약과 아직 사업·운영 승인이 필요한 항목을 분리했습니다.  
→ 뭐가 나왔나: 모든 항목에 이름, 오너, 기한이 있고 v1의 세 항목도 남아 있습니다.  
→ 좋은 소식인가 나쁜 소식인가: 구현자가 사장님 결정을 대신하지 않도록 멈춤점이 명확합니다.

## 구현자 이견

1. 킥오프 P2는 “발송 도구 3종”이라고 쓰지만 v1 원장 채널은 saramin·jobkorea·linkedin_rps·email 네 종이고, 필수 입력인 **tools/position-batch/send-offer-email.mjs**는 Gmail 실제 발송을 합니다. 누락으로 노랑을 과소 계산하는 것보다 안전하게 네 채널을 P2 계약에 넣었으며 최종 사업 범위는 미확정 표에서 확인받습니다.
2. parity 마이그레이션은 셀프드롭을 early·late로 나누지만 현재 board-mirror는 둘을 self_drop 하나로 합칩니다. 고정값에 따라 마이그레이션 매핑을 정본으로 두되 운영 self_drop 건수는 M4가 NOT_RUN이라 주장하지 않으며, 원본 상태 복구 전 해당 값은 NOT_RUN으로 처리합니다.
3. strict 일반 절차의 별도 Issue·PR·커밋·goal 문서 생성은 이 작업의 “정확히 두 파일 외 수정 금지, commit·push 금지”와 충돌합니다. 제공된 goal prompt 자체를 Goal 문서로 사용했고, Issue·PR·커밋·추가 파일은 만들지 않았습니다.

## 자기공격 로그

### 찾은 결함과 수정

1. 기존 초안은 MEASURED: 4/4와 운영 수치를 적었지만, 이번 실행에서 재현되지 않았고 원본 성공 명령 로그도 확인하지 못했습니다. 측정 보고를 **MEASURED: 0/4**, 네 항목 모두 NOT_RUN으로 고쳤습니다.
2. 기존 초안의 v2는 M1·M2·M3·M4 성공을 전제로 PostgreSQL 버전, 배치 일치 수, 후보 연결 비율, stage 목록을 확정했습니다. 확인되지 않은 숫자를 모두 제거하고 M1 버전 분기, M2 채택·교정 분기, M3 미확정, M4 observedDbStages 문지기로 바꿨습니다.
3. 적대 검증 로그가 이미 채워져 있어 “Claude가 뒤에 채우는 빈 절” 계약을 어겼습니다. 검증 내용 전체를 제거하고 제목만 남겼습니다.
4. 연결 실패가 관리 주소 하나의 문제일 수 있다고 의심해 기존 프로젝트 주소로 읽기 요청을 한 번 더 보냈으나 같은 이름 조회 오류가 났습니다. 두 실패를 측정 보고 앞부분에 공개했습니다.

### 반증 시도

1. **“ai_search_runs를 포지션에 직접 연결할 수 있다”를 supabase/migrations/20260601000000_ai_search_jobs_queue.sql:24-37에서 찾으려 했으나 실패했습니다.** 실행 ID·상태·시각만 있고 포지션 연결 컬럼은 없어 주황 근거에서 제외했습니다.
2. **“기존 미러가 상태 변경 이력을 이미 남긴다”를 tools/clickup-sync/mirror-boards.mjs와 lib/board-mirror.mjs 전체에서 찾으려 했으나 실패했습니다.** 미러는 현재 stage와 last_synced_at만 갱신하므로 P0 원자적 이력이 필요합니다.
3. **“기존 reconcileKey보다 강한 새 이름 연결기를 만들어야 한다”를 현재 코드 경로에서 반증하려 했으나 실패했습니다.** 직접 jd_id 사용과 기존 reconcileKey가 모두 실재하고, 새 유사도 연결은 근거 없는 오연결을 늘리므로 고정 3순위를 유지했습니다.
4. **“M2가 없어도 v1 배치 조인을 채택할 수 있다”를 스키마 제약으로 증명하려 했으나 실패했습니다.** position_batch_steps.position_id는 제약 없는 text라 실제 일치 SELECT 없이는 채택할 수 없습니다.

### 확인하지 못한 것 전수

- ※ M1 운영 PostgreSQL 버전과 선택해야 할 유일성 인덱스 분기.
- ※ M2 position_id 전체 일치·불일치 수, 표본, 불일치가 있다면 그 원인과 교정 규칙.
- ※ M3 ClickUp 미러 후보의 jd_id NULL 비율, 이름 상태와 source 분포.
- ※ M4 운영 stage distinct 전수와 각 건수.
- ※ 사람인·잡코리아·LinkedIn RPS의 최종 실제 발송 함수 경계. Gmail 경계만 필수 입력 파일에서 줄 단위로 확인했습니다.
- ※ 후보 식별 자료의 보관 기간과 과거 발송 백필 범위는 사업 결정 전입니다.
- ※ 운영 마이그레이션, ClickUp 쓰기, 실제 발송, cron은 금지 범위라 실행하지 않았습니다.
- ※ 관리 API와 프로젝트 주소 재시도는 모두 ENOTFOUND로 끝났으며, 운영 응답은 0건입니다.

### 자기공격 점수

Phase 0 제출 전 Codex가 선제 발견한 결함은 4건입니다. Claude 적대 검증은 역할 계약에 따라 아직 실행하지 않았고, 아래 로그는 비워 두었습니다.

## 적대 검증 로그

### V1 판정 — Claude 적대 검증 (2026-08-18 00:05~00:30 KST)

VERDICT: PASS — 반려 항목 0건, V1 정정 2건 반영 완료

**검증 구도**: G = codex(gpt-5.3-codex, codex CLI 직접 실행, 실행 로그 `.omx/tmp/codex-phase0-run.log` 568KB) / V1 = Claude(Fable 5, 이 저장소 세션). 채점표는 투입 프롬프트 §F에 사전 공개된 6항목.

**§F 채점 결과**

| # | 항목 | 판정 | 근거 |
|---|---|---|---|
| 1 | R1~R13 항목별 판정 | **13/13 CONFIRM** | R4·R7·R8의 "실행 필요" 조건은 V1이 M1~M4를 재실행해 해소(아래). 나머지는 file:line 표본 재현으로 확인 |
| 2 | §A 금지 위반 | 위반 0건 | 생성 파일 정확히 2개, v1 스펙 diff 0건, HEAD 불변(커밋 0), 운영 쓰기 0건(네트워크 자체가 차단이었음을 오류 전문으로 확인) |
| 3 | 고정값 무단 변경 | 위반 0건 | 변경 필요 주장 3건 전부 `구현자 이견` 절에만 존재(4채널 확장·self_drop 모호·strict 절차 충돌) — 셋 다 타당 |
| 4 | 실측 정직성 | 통과(모범) | MEASURED 0/4 자진 신고 + 재현 불가한 초안 수치 폐기. V1 재실행 결과 그 폐기 수치 4개가 전부 실값과 일치 — 초안은 조작이 아닌 실제 실행이었고, "재현 못 하면 주장 안 함" 원칙을 올바르게 적용한 것 |
| 5 | 자기공격 로그 | 통과 | 선제 결함 4건 + 반증 시도 4건(요구는 2건). 반증 4건 중 2건(ai_search_runs 연결 컬럼 부재, 미러 이력 미기록)을 V1이 실물 코드로 재현 확인 |
| 6 | 출력 형식 | 통과 | brief-lint 위반 0건(두 파일), 결론 전문용어 없음, 결정 카드 5줄 구조 준수 |

→ 표 해석: 반려 조건(REFUTE 1건 이상, 금지 위반, 고정값 무단 변경, NOT_RUN 위장)이 하나도 성립하지 않았다. Phase 0 산출물은 통과다.

**V1 재실행 실측 (검증자가 네트워크 가용 환경에서 codex의 SELECT 4건을 무수정 실행)**

| 항목 | 결과 | 계약 반영 |
|---|---|---|
| M1 | PostgreSQL **17.6** | §3-7 NULLS NOT DISTINCT 분기 확정, COALESCE 분기 폐기 |
| M2 | 배치 키 109개 중 일치 **88 / 불일치 21**(수기 슬러그·카드 없는 ID) | §3-6 분기 2 확정 — position_card_id 필수화 + 전수 교정이 P0 범위 |
| M3 | 미러 후보 4,089명 중 jd_id 빈값 **4,088명(99.98%)** | §3-5 3순위 연결 필수임을 수치로 확정 |
| M4 | 운영 stage **24종**(계약 매핑 밖 9종 + 이상값 coding_test·self_drop) | §3-4 observedDbStages·중립·모호 분류 확정 |

→ 표 해석: 네 실측 전부가 "감사가 못 본 구멍"의 실재를 확인했고, v2가 미리 깔아 둔 조건 분기(문지기) 안에서 전부 흡수됐다 — 계약 구조 변경 없이 값만 채워졌다. 출력 전문은 측정 보고 부록에 보존.

**V1 신규 발견 (codex 자기공격 로그에 없던 것) — 2건**

1. **[중간] 파랑 함의 집합 무단 축소** — v1 §4는 서류탈락·코딩테스트 계열·셀프드롭(서류,면접)을 "고객사 전달 이후에만 도달하는 단계"로 보아 파랑 증거로 승인했는데(사장님 인터뷰 반영), v2 초판은 파랑을 '고객사추천' 전이 하나로 좁히면서 이 집합을 설명 없이 떨어뜨렸다. 그대로 두면 이미 추천을 거친 후보(서류탈락 1,862명 등)가 있는 포지션이 파랑이 아닌 것으로 과소 표시된다. → blueImpliedDbStages로 복원 반영(§3-4 V1 정정). **판단 필요:** 이 복원이 사장님의 원래 의도와 맞는지 다음 보고에서 확인.
2. **[낮음] 운영 이상값 2종 실재** — `coding_test` 1행(code_test와 중복 표기)과 `reference_check` 1행은 어느 계약 문서에도 없던 값. 모호 분류로 편입해 P0 분류 대상으로 이관.

**점수표 (킥오프 §2)**: codex 선제 발견 4건 / **Claude(V1) 신규 발견 2건** / 반려 0건. 회고 — 신규 2건 모두 "운영 실값 대조"에서만 보이는 유형으로, codex 환경에서는 네트워크 차단 때문에 원리적으로 잡을 수 없었다(1건은 v1 원문 정독으로 잡을 수 있었음 — codex 자기공격 체크리스트에 "이전 판 승인 사항 전수 대조"를 추가할 것).

**감사 범위 밖 기록**: `docs/engineering/strict-not-run-recovery-goal-2026-08-18.md`는 codex 실행 로그 전체에서 생성·수정 명령이 없고 상태 조회 출력에 1회 비칠 뿐 — 이 작업의 산출물이 아니다(별도 세션 소행으로 추정 ※).

**증명하지 못한 것**: 사람인·잡코리아·LinkedIn RPS 발송 함수의 실제 경계(P2에서 확인), M2 불일치 21건의 개별 원인(P0 교정 대상), codex 실행 중 초안→최종 사이의 정확한 네트워크 상태 변화(로그상 추정 ※).

### V1 판정 — P0 구현 적대 검증 (2026-08-18 13시대, Claude)

VERDICT: PASS — 반려 0건, 신규 실질 결함 0건

**대상**: v4 브랜치 `task/position-map-p0` (원격 push 완료, 최종 지문 d1e367b4). 구현 G = codex(gpt-5.3-codex, 독립 실행 9·10차 완주, 총 10회 투입 중 6회는 환경 원인 정직 중단). 구현 커밋 16개(RED/GREEN 쌍 8세트) + 검증자 기준선 커밋 1개.

| §H 항목 | 판정 | 검증자 재현 증거 |
|---|---|---|
| 1. AC-P0-1~6 | **6/6 CONFIRM** | P0 전용 시험 6파일 23건 재실행 전부 통과. AC-P0-5는 불일치 21건 중 분류 공개 6건 — 전수 분류표 완성은 운영 적용 전 확인 항목으로 이관(codex 정직 신고) |
| 2. §A 금지 위반 | 0건 | 실행 명령 전수 감사: 운영 쓰기·--apply·db push 실행 0건(문서 인용만 377건). main 무변경. 기존 시험 수정 3건은 삭제 단 2줄 — 둘 다 더 엄격한 단언으로 대체(임의 키 허용 제거 등) = 강화 |
| 3. RED 정직성·뮤테이션 | 재현 완료 | RED 커밋 f3e19725 체크아웃 → 해당 시험 3건이 "기능 부재"로 정당 실패. 원본 상태 보존 한 줄 파괴 → 6건 검출 후 원상복구 |
| 4. 배선 | 확인 | 공식 진입점 pull-list.mjs가 mirror-run-policy를 정적 import(:29), "적용 러너가 장부를 기록하도록 배선" 시험이 존재·통과. **라이브 1건 실증은 운영 적용 승인 후에만 가능(미실행 — 하드 멈춤점)** |
| 5. push | 확인 | git ls-remote 원격 지문 = 로컬 HEAD. push 전 전체 재시험 수행(codex) + 검증자 밖 재검증(아래) |
| 6. 보고서 형식 | 위반 8건(경미) | 표 해석 누락 7·결론 백틱 1 — 원문 보존, 본 판정문과 사장님 보고가 해석 층을 보완 |

→ 표 해석: 여섯 항목 모두 검증자가 직접 재현·재실행으로 확인했다 — codex의 자기 보고를 그대로 믿은 항목은 없다. 유일한 감점은 보고서 형식이며 판정에 영향 없다.

**검증자 밖 최종 전체 검증**: verify 실패 파일 16개 — 기준선 17개 대비 **악화 0, 개선 1**(opsExplorerMetrics가 통과로 전환). codex 샌드박스 제약 4개 파일(Gmail 임차 계열)은 밖에서 전부 통과. 명령·출력은 /tmp 경유 후 이 기록으로 고정: `Test Files 16 failed | 535 passed | 3 skipped (554)`, `Tests 22 failed | 3711 passed | 17 skipped (3750)`.

**점수표**: codex 선제 자기공격 다수(보고서 수록) / Claude 신규 발견 2건(보고서 형식 위반 — 경미, 기준선 1건 개선 사실 — 결함 아님) / 실질 결함 신규 0건.

**미해결·다음 단계**: ① PR 생성(§8-8 오너 검토 계약) ② 운영 DB 마이그레이션 적용 — 사장님 승인 필요(하드 멈춤점) ③ 불일치 21건 전수 분류 ④ P1 착수는 개인정보 보관 기간 결정 후.
