# ValueConnect LLM Wiki: Supabase 현황 및 필드 전수 조사

조사 시각: 2026-10-14 02:45 UTC. 범위: 운영 Supabase의 PostgREST에 노출된 `public` API 객체 222개, 필드 2,772개. 필드별 객체명·이름·타입·필수 여부·PK/FK 표기는 [전수 목록](evidence/llm-wiki-supabase-fields-2026-10-14.tsv)에 있다. 목록에는 실제 후보자나 메일 원문을 저장하지 않았다.

## 판정

**새 후보자 마스터나 전량 Markdown 위키를 만들 근거가 없다.** 현재 DB에는 후보자, AI Search 결과, Gmail, ClickUp, Notion, 고객사 온톨로지와 통합 이력 뷰가 이미 있다. 1차 구현은 기존 자료의 연결 정확도와 팀 조회 권한을 고치는 작업이다. 단, 현재 익명 API 노출이 확인되어 권한 경계 수정과 재검증이 배포 선행 조건이다.

이 조사는 API 스키마와 읽기 전용 `HEAD`/소량 `GET`으로 확인했다. PostgreSQL 내부의 실제 RLS 정책, grants, 인덱스, 트리거, 비공개 스키마와 외부 시스템 권한은 전수 조사하지 못했다. 다음 구현자는 그 항목을 별도로 확인해야 한다. 적재 건수는 조사 시점 스냅샷이며 서로 다른 테이블의 건수를 더해 고유 후보자 수로 해석하면 안 된다.

## 기능별 필드·적재 현황

| 기능 | 이미 있는 객체와 핵심 필드 | 실제 적재·결손 | 판정 |
| --- | --- | --- | --- |
| 후보자 마스터 | `pipeline_candidates` 41필드: `id`, `name`, `jd_id`, `stage`, `source`, `email`, `clickup_task_id`, `status_history`, `ai_assessment`, `tenant_id`, `resume_data` | 21,771건. `email` 674건, `clickup_task_id` 4,187건, `jd_id` 5,646건, `resume_data` 8,424건. `status_history`는 21,771건 모두 non-null이나 비어 있지 않은 배열은 27건. `embedding` 0건. | 기존 마스터를 기준으로 식별·출처 연결을 보강 |
| AI Search | `sourcing_runs`의 실행 ID/상태, `sourcing_results`의 `run_id`, `position_id`, `channel`, `candidate_name`, `match_score`, `match_points`, `fit_reason`, `evidence_urls`, `resume_data`; `search_jobs`, 별도 `candidates`, `profile_archives`도 존재 | 결과 1,436건, 실행 28건, 작업 598건, 별도 후보자 308건, 프로필 아카이브 21,651건. `sourcing_results`에 `candidate_id`가 없고 `evidence_urls` 비어 있지 않은 결과는 544건. | 결과가 이미 DB에 있으나 후보자 마스터 연결과 근거 품질 검수가 필요 |
| Gmail | `gmail_messages`: 원문·제목·발신/수신·스레드/메시지 ID·후보자명·회사명·포지션명·시각. `gmail_derived_events`: 이벤트 유형·분류 버전·신뢰도·후보자/포지션/회사 FK. `gmail_resume_attachments`, `gmail_sync_state` | 메시지 35,504건, 파생 이벤트 21,791건, 이력서 첨부 24,713건. 파생 이벤트의 `candidate_id`, `position_id`, `company_id`는 **전부 NULL**. `gmail_candidate_feedback` 및 `gmail_position_requests`는 0건. | 수집은 있으나 개인·포지션 타임라인 연결은 미완성 |
| ClickUp | `clickup_comments`: `task_id`, `task_url`, `candidate_name`, `company_name`, `position_title`, `body`, `occurred_at`; 후보자에 `clickup_task_id`/동기화 시각; `clickup_sync_state` | 댓글 11,658건, 후보자 태스크 ID 4,187건. 댓글의 후보자명 7,714건, 포지션명 7,673건. 댓글에는 `candidate_id`가 없다. | 원천 링크는 충분하나 같은 사람·포지션에 안정적 연결 필요 |
| Notion·고객사 지식 | `notion_clients`: 페이지 ID/URL·Markdown·블록·수정 시각; `notion_coffeechats`: 후보자명·회사명·본문·URL; `customer_ontology_sources`: `source`, `source_id`, URL·본문·해시·시각; `customer_ontology_documents`: 고객사별 Markdown·원천 해시 | 고객사 269건, 커피챗 158건, 온톨로지 원천 5,008건(ClickUp 4,046, Notion 961, Call 1), 문서 501건. Notion 고객사 Markdown 224/269건. | 새 Git 위키 전에 기존 온톨로지와 중복 범위 확인 |
| 후보자 이력 | `pipeline_stage_history`: `candidate_id`, 전후 단계, 변경자·시각. `candidate_activity_log`: 후보자 ID·시각·이벤트·payload·ClickUp 이벤트 ID. `unified_candidate_history_view`: 후보자 ID·원천·원천 ID·본문·시각 | 단계 이력 56건(최신 2026-05-20), 활동 로그 **0건**. 통합 뷰 34,036건 중 `candidate_id`가 있는 행은 21,496건뿐. 나머지 ClickUp 댓글 11,658, Gmail 스레드 724, Notion 커피챗 158건은 후보자 ID 없이 들어간다. | 뷰 이름과 달리 후보자별 통합 타임라인으로 바로 쓸 수 없음 |
| Discord | `discord_gateway_leases`, `discord_gateway_killswitches`, `user_discord_mapping` | 사용자 매핑 0건. 노출된 222개 API 객체 중 Discord 메시지 저장 테이블 없음. | 봇 운영 흔적만 확인. 허용 채널·보존·연결 방식을 별도 설계 |
| 의미 검색 | 여러 원천 테이블에 `embedding` 필드, 벡터 검색 RPC 노출 | 점검한 후보자·포지션·Gmail·ClickUp·Notion 등의 `embedding` 채워진 행 0건. | 기존 컬럼 존재가 의미 검색 기능의 가동을 뜻하지 않음 |

추가로 `resume_position_matches` 13,250건, `pipeline_position_cards` 1,464건, `weekly_meetings` 256건이 있다. `pipeline_candidates.source` 중 `ai_search:linkedin` 13,124건, `clickup` 4,179건 등으로 이미 AI Search와 ClickUp 입력이 후보자 테이블에 섞여 있다. `sourcing_results`만 AI Search 전체라고 간주하면 누락된다.

## P0: 익명 읽기 권한 노출

서비스 키가 아닌 프런트엔드용 공개 `anon` 키만 사용한 비로그인 요청에서 `gmail_messages` 35,504건, `unified_candidate_history_view` 34,036건, `pipeline_candidates_active` 21,771건, `profile_archives` 21,651건의 전체 건수 조회가 가능했다. `GET ...?select=body_text&limit=1`(Gmail), `select=body`(통합 뷰), `select=text_content`(프로필), `select=name`(후보자)도 실제 비어 있지 않은 값을 반환했다. 값 자체는 출력하거나 조사 파일에 저장하지 않았다. 즉, 공개 익명 클라이언트가 개인정보성 본문에 접근 가능한 상태가 확인됐다. `candidates`, `company_source_documents`, `company_source_chunks` 등에서도 익명 행 조회가 확인됐다. 반면 일부 원본 테이블은 익명 요청에서 행이 보이지 않아 접근 규칙이 일관되지 않다.

원인(뷰 권한·RLS·GRANT·함수 중 무엇인지)은 아직 확인되지 않았다. 수정 전에는 새 Wiki/API/Discord 봇에 이 데이터를 노출하지 말 것. 먼저 모든 관련 테이블·뷰·RPC의 `anon`/`authenticated`/`service_role` 권한과 RLS를 조사하고, 로그인하지 않은 요청이 본문·프로필을 읽지 못하도록 고친 뒤 실제 HTTP 요청으로 재검증해야 한다. 사용자별 팀 권한과 감사 기록도 그 다음에 확인한다.

## 기존 4개 설계안에 대한 적대 검증

- **Git Markdown 정본안:** 10만 명 공유 조회와 후보자 개인정보 삭제·권한에 맞지 않는다. 고객사 전략·채용 플레이북 등 사람이 확정한 지식이나 재생성 가능한 요약에만 검토한다.
- **Supabase 전량 재수집안:** Gmail/Notion/ClickUp 원문과 온톨로지 자료가 이미 수집돼 있다. 재수집보다 ID 연결·권한·출처 검수가 선행된다.
- **링크만 저장안:** 검색과 타임라인에 필요한 최소 원천 내용·시각·식별자는 있어야 한다. 현재 수집된 내용을 없애면 검색 가능성이 퇴보한다. 원천별 저장 최소량을 정하고 딥링크를 함께 보존한다.
- **5일 완성·0.1초 검색 단정:** 현 데이터는 21,771명의 파이프라인 후보자 외 여러 부분집합에 분산돼 있고 10만 명 부하·동시 접속은 측정되지 않았다. 인증·관계 연결·검색 정확도를 먼저 통과시키고 성능을 계측한다.
- **LLM SQL 생성·자동 병합:** LLM이 임의 SQL을 실행하거나 이름+회사만으로 후보자를 합치면 개인정보 노출·오병합 위험이 크다. 허용된 필터 API와 안정적 식별키, 애매한 경우 검토 큐를 쓴다.

## 최소 구현 순서와 검증 문턱

1. **P0 권한:** 현재 익명 노출 목록 전체를 점검·차단하고 비로그인/팀 역할별 읽기 테스트를 통과한다. 이 작업은 운영 권한 변경이므로 별도 변경 계획과 롤백 절차가 필요하다.
2. **기존 스키마 관계도:** `pipeline_candidates`와 별도 `candidates`, `sourcing_results`, `profile_archives`, `gmail_derived_events`, `clickup_comments`, `notion_coffeechats`, `customer_ontology_sources`의 키·중복·동기화 주체를 실사한다. 기존 SOT 계약(`docs/sot/ai-search-operations.md`)과 충돌을 기록한다.
3. **AI Search Inbox 및 공용 목록:** 기존 `sourcing_results`와 `pipeline_candidates`의 AI Search 행을 실행/원천/프로필 단위로 연결한다. 근거 없는 결과를 확정 사실로 승격하지 않는다. `candidate_id`가 없는 경우 원천 ID/정규화 URL/확인된 이메일로만 자동 연결하고 애매한 건 보류한다.
4. **히스토리:** 현재 빈 `candidate_activity_log`나 기존 이벤트 모델의 적합성을 검토해 추천·접촉·피드백·단계 변경을 출처와 시각이 있는 불변 이벤트로 기록한다. 기존 `unified_candidate_history_view`에서 후보자 ID가 없는 행을 조용히 후보자 이력으로 표시하지 않는다.
5. **조회 화면:** 기존 ValueHire 관리자 인증과 화면을 재사용한다. 후보자·포지션·고객사 조건 검색, 출처 링크, 최신성, 충돌 표기를 먼저 제공한다. LLM 응답은 조회한 사실과 출처만 요약하며 AI 의견을 별도 표시한다.
6. **Notion/Discord:** 이미 있는 Notion/온톨로지 범위를 재사용하고 Discord는 읽을 채널과 결정사항 승인자를 정한 뒤 소규모 연결한다. 모든 메시지를 후보자 사실로 자동 승격하지 않는다.

100,000명 규모 검증은 실제 데이터와 분리한 합성 데이터로 실행한다. 대표 쿼리(이름·회사·직무·연차·최근 접촉·추천 이력)의 실행계획, 지연 p50/p95, 동시 사용자 4명, 페이지네이션과 권한별 결과 차이를 기록한다. 목표 응답시간은 제품 요구로 합의한 뒤 측정값으로 판정한다.
