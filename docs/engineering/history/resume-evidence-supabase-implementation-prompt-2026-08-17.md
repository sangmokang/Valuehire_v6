> **v4 전제 역사 기록 — 실행 금지.** 이 문서는 2026-08-17 에 `task/resume-evidence-supabase-prompt` 워크트리의 미추적 파일로 작성됐고, "기존 ValueHire v4 프로필 아카이버를 재사용"을 전제로 한다. 사장님 결정(2026-08-14 v1~v5 의존 0)과 충돌하므로 v6 설계서가 아니다. 보존 이유: 8개 counter-AC(구간 무누락 manifest·마지막 화면·NULL 구분·회사별 duty·검색 조건 보존·원격 경로 금지·readback·회사 별칭)와 2026-08-17 실측 수치가 v6 클린룸 계약(WU-0B, `docs/sot/humansearch-evidence-contract.md`)의 시험 문제로 쓰인다. 2026-09-09 회수, 본문은 원문 그대로(sha256 아래).
> 원문 sha256: 0ba1e992f63cbdfcaf02d41383c709f2b5f502b8270c646f8a9eff0ee8d4b50d

# 핵심구현내용-260817

## 사장님용 결론

ValueHire에는 이미 실제로 쓰이는 프로필 아카이버가 있다. 로컬 기준 796개 archive와 유효하게 연결된 12,848장의 이미지가 있고, 이 유효 집합의 이미지 파일 누락과 sequence 단절은 0건이다. 따라서 “긴 이력서를 여러 장으로 이어 저장”하는 기반은 존재한다. 별도로 부모 archive가 없는 screenshot 행 6개와 DB가 참조하지 않는 파일 2개가 있어 정합성 청소 계약은 추가해야 한다.

하지만 현재 완료 판정은 사업 목적에 못 미친다.

- 전체 페이지 무누락을 증명할 수 있는 archive는 0건이다. 운영 DB의 `doc_height`와 screenshot geometry가 함께 완성된 행이 없기 때문이다.
- 로컬 796건 중 salary 구조화는 34건, 회사별 경력 구조화는 12건뿐이다.
- Supabase `profile_archives` 1,386건 중 salary 33건, 회사별 경력 12건, 구조화 JSON 514건이다.
- 검색결과 전체 페이지 보존은 LinkedIn 일부 경로 중심이고, 사람인·잡코리아까지 동일한 페이지네이션 증거 계약으로 묶여 있지 않다.
- Supabase batch는 upsert 응답 후 원격 row/hash readback 없이 로컬을 `synced`로 바꿀 수 있다.
- live `organization_analysis`는 1행뿐이지만, 회사·커리어 자산은 다른 테이블에 이미 많이 쌓여 있다. 새 분석 테이블을 중복 생성하기보다 기존 회사 식별·문서·커리어 graph를 연결하는 뷰가 먼저다.
- repository의 `profile_archives` 생성 migration에는 RLS enable/policy가 없다. live policy를 직접 dump하지 못했으므로 현재 raw archive 접근통제는 안전하다고 가정할 수 없다.

우선순위는 다음과 같다.

1. 캡처 무누락 manifest와 실패 닫힘.
2. 검색 페이지 전체 자산화.
3. 연봉·회사별 수행업무의 evidence-linked 구조화.
4. SQLite 정본 → Supabase 파생본의 readback 검증.
5. 회사 식별자 기준 Organization Analysis와 영업용 talent-density 뷰.
6. 개인정보 보존·삭제·접근통제와 비용 상한.

## 구현 에이전트에게 전달할 프롬프트

아래 작업을 `$strict` 방식으로 수행하라. goal 문서와 원자적 AC를 먼저 만들고, 실제 저장소 SOT를 읽고, 별도 worktree에서 RED→GREEN→회귀검증 순으로 구현하라. 구현 완료 전 `claude -p` 1차 적대검증과 Codex 2차 재공격을 수행한다. 실제 후보자 PII, 원본 스크린샷, API key를 git이나 검증 출력에 남기지 않는다.

### 1. 목표

사람인, 잡코리아, LinkedIn Recruiter/RPS에서 다음을 하나의 evidence archive로 만든다.

- 검색 결과의 모든 방문 페이지와 적용 필터
- 후보자 상세 이력서의 첫 화면부터 마지막 화면까지의 연속 스크린샷
- 전체 DOM/iframe 텍스트와 펼침 영역
- 표시된 연봉 정보의 원문과 정규화 observation
- 한 후보자의 회사별 직무·수행업무 원문과 정규화 observation
- 캡처 버전, extractor 버전, 원문 span, 해시, 보존 상태
- SQLite 정본에서 승인된 Supabase 파생본으로의 idempotent batch와 원격 readback
- 회사 단위 학교/이전 회사/역할/수행업무/연봉 분포를 읽을 수 있는 Organization Analysis 뷰

### 2. 바꿀 기준선

먼저 아래 실제 구현을 읽고 call graph와 DB DDL을 확정하라.

- `Valuehire_v4/tools/profile-archiver/extension/background.js`
- `Valuehire_v4/tools/profile-archiver/server/index.js`
- `Valuehire_v4/tools/profile-archiver/server/sync-batch.js`
- `Valuehire_v4/tools/profile-archiver/tests/*.mjs`
- `Valuehire_v4/supabase/migrations/20260530000000_profile_archives_sync.sql`
- `Valuehire_v4/supabase/migrations/20260610000000_profile_archives_run_id.sql`

v6 HumanSearch는 현재 런타임이 아니라 package/gate skeleton이므로, 검증된 v4 archiver를 먼저 보강한다. v6로의 이동은 별도 migration 단계로 분리한다. 기존 동작을 복사해 두 번째 파이프라인을 만들지 않는다.

### 3. 절대 불변식

1. SQLite만 정본이다. Supabase는 SQLite에서 만든 승인된 파생본이며 역방향 갱신을 금지한다.
2. 외부 effect는 idempotency key, 실행 영수증, readback이 없으면 완료가 아니다.
3. screenshot 장수만으로 전체 페이지 완료를 판정하지 않는다.
4. salary `NULL` 하나로 `화면에 없음`, `가려짐`, `추출 실패`, `명시 금액`, `추정값`을 합치지 않는다.
5. 회사 free-text만으로 조직 분석을 집계하지 않는다. canonical company identity 또는 manual-review 상태가 필요하다.
6. raw screenshot/이력서 원문은 private data class다. 암호화 객체 저장소, 역할 기반 접근, 보존기간, 삭제 영수증이 승인되기 전에는 Supabase raw export를 실행하지 않는다.
7. Supabase에 로컬 파일 경로를 cloud asset처럼 기록하지 않는다. 원본을 보낼 수 없는 상태면 hash와 `LOCAL_ONLY` 상태만 보낸다.
8. LinkedIn/RPS는 채널 정책과 사용자 권한을 기록한다. 정책이 불명확하면 human-driven capture만 허용하고 자동 pagination/click은 막는다.
9. 집계 분석에서 개인 salary나 개인 수행업무를 고객에게 직접 노출하지 않는다. 최소 cohort 크기와 redaction을 적용한다.
10. `PASS`, `FAIL`, `NOT_RUN`, `PARTIAL`, `BLOCKED_POLICY`를 구분하고 실행하지 않은 것을 성공으로 표시하지 않는다.
11. 암호화 key는 SQLite, git, 로그, Supabase 행에 넣지 않는다. 별도 key manager와 key version, rotation, backup/restore 시험이 없으면 `source_text_encrypted`를 구현 완료로 보지 않는다.

### 4. SQLite 스키마

현재 `archives`와 `screenshots`를 무중단 additive migration으로 확장한다. 실제 기존 key/type을 introspect하고 이름 충돌을 피하라.

#### `archive_runs`

- `id`, `source_channel`, `mode`(`search|profile|job_post`)
- `started_at`, `finished_at`, `status`, `abort_reason`
- `operator_type`(`human|assisted|approved_automation`), `policy_contract_version`
- `capture_contract_version`, `extractor_version`, `extension_version`
- `page_cap`, `screenshot_cap`, `storage_byte_cap`, `retry_cap`
- `actual_pages`, `actual_screenshots`, `actual_storage_bytes`

#### `archive_pages`

- `id`, `run_id`, `archive_id`, `page_kind`(`search|profile|job_post`)
- `source_url_normalized`, `navigation_url_hash`, `page_index`, `cursor_hash`
- `document_height`, `viewport_width`, `viewport_height`
- `capture_started_at`, `capture_finished_at`, `status`
- `text_hash`, `manifest_hash`, `screenshot_count`
- `expected_result_count`, `observed_unique_item_count`, `occluded_item_count`
- `loading_absent`, `bottom_reached`, `full_coverage`, `failure_reason`

#### `archive_segments`

- `id`, `page_id`, `sequence`
- `scroll_container_selector_hash`, `scroll_top`, `viewport_height`, `document_height`
- `previous_segment_id`, `overlap_px`, `gap_px`
- `content_hash`, `image_sha256`, `image_bytes`, `mime_type`
- `local_relative_path`, `object_storage_key`, `storage_state`
- `capture_reason`, `captured_at`, `duration_ms`
- unique `(page_id, sequence)`; unique `(page_id, image_sha256, scroll_top)`

#### `search_page_snapshots`

- `id`, `page_id`, `search_context_id`, `filter_snapshot_json`, `filter_hash`
- `page_index`, `cursor_hash`, `displayed_total`, `displayed_range`
- `zero_result_state`, `next_control_state`, `previous_control_state`
- `result_identity_hashes_json`, `result_count`, `status`

#### `search_result_items`

- `id`, `search_page_snapshot_id`, `source_item_key_hash`, `position_on_page`
- `candidate_identity_key` 또는 privacy-safe hash
- `headline_text_hash`, `company_text_hash`, `salary_text_hash`
- `detail_opened`, `detail_archive_id`, `captured_at`

#### `salary_observations`

- `id`, `archive_id`, `candidate_key`, `position_id`, `canonical_company_id`
- `salary_type`(`current|expected|job_posted|company_band|other`)
- `state`(`explicit|range|redacted|not_present|parse_failed|inferred|manual_review`)
- `amount_min`, `amount_max`, `currency`, `period`, `gross_net`
- `source_text_encrypted` 또는 local-only reference, `source_text_hash`
- `evidence_page_id`, `evidence_segment_id`, `span_start`, `span_end`
- `confidence`, `visibility_class`, `extractor_version`, `captured_at`

추정 salary는 명시 salary와 같은 집계에 섞지 않는다. 개인 salary는 민감도 등급을 높이고 Supabase whitelist에서 기본 제외한다.

#### `career_duty_observations`

- `id`, `archive_id`, `candidate_key`, `employment_sequence`
- `company_name_raw`, `canonical_company_id`, `company_resolution_state`
- `title_raw`, `title_normalized`, `started_on`, `ended_on`, `employment_state`
- `duty_text_encrypted` 또는 local-only reference, `duty_text_hash`
- `normalized_tasks_json`, `skills_json`, `products_json`, `outcomes_json`
- `evidence_page_id`, `evidence_segment_id`, `span_start`, `span_end`
- `confidence`, `extractor_version`, `captured_at`

원문을 버리고 요약만 저장하지 않는다. 원문 evidence와 정규화 결과를 분리하고, extractor 재실행 시 새 revision을 만든다.

#### `company_resolution_reviews`

- raw name과 후보 canonical company, domain/alias evidence, confidence, review state, reviewer receipt
- exact domain/approved alias만 자동 연결한다. fuzzy name-only는 manual review다.

#### `export_batches`, `export_batch_items`

- batch: SQLite high-water mark, whitelist version, source row count, payload hash, started/finished, accepted/rejected/readback counts, status, retry count
- item: entity type/id, idempotency key, payload hash, remote key, response status, readback hash, error class
- 불변식: `source_row_count = accepted_count + rejected_count`
- remote row count와 canonicalized payload hash가 일치한 뒤에만 local item을 `synced`로 바꾼다.
- batch worker는 lease owner/expiry와 compare-and-swap을 사용한다. 두 worker가 같은 high-water range를 집어도 idempotency key 하나만 원격에 남아야 한다.

#### `retention_policies`, `deletion_receipts`

- channel/data class별 retention days, legal/policy basis, storage target, approved version
- 삭제 영수증은 대상 범위, local/object/derived 삭제 건수, 실패, 재시도, 완료시각을 남긴다.

### 5. 캡처 알고리즘

#### 프로필 상세

1. URL/channel을 분류하고 capture policy를 확인한다.
2. 자동 경로는 현재 위치와 무관하게 `scroll_top=0` 증거부터 시작한다. 수동 경로가 중간에서 시작하면 `PARTIAL_TOP_MISSING`으로 시작하고, 사용자가 위로 이동해 0 구간을 확보해야 PASS가 된다.
3. top window와 실제 scrollable container를 구분하고 선택 근거를 manifest에 저장한다.
4. 접힌 섹션, 더보기, iframe, dialog/panel을 채널 adapter로 탐지한다. 허용된 상호작용만 수행하고 성공/실패를 기록한다.
5. 인접 이동 폭은 `min(configured_step, viewport_height * 0.75)` 이하로 제한한다.
6. 각 이동 후 DOM/content 안정과 loading 부재를 bounded wait한다. 무한 대기하지 않는다.
7. 화면 이미지, DOM/iframe text snapshot, geometry, content/image hash를 같은 segment에 원자적으로 저장한다.
8. 마지막 segment가 `scroll_top + viewport_height >= document_height - tolerance`를 만족해야 한다.
9. 모든 인접 구간의 gap이 0이고 sequence가 연속이며 첫 구간이 0, 마지막이 하단일 때만 `full_coverage=true`다.
10. document height가 동적으로 늘면 manifest를 갱신하고 bounded 재순회한다. 상한 초과 시 `PARTIAL_DYNAMIC_GROWTH`다.
11. 한 tab/run에는 capture owner 하나만 허용하고, 새 세션은 기존 세션을 이어받거나 명시적으로 거절한다. file은 임시 이름으로 쓴 뒤 hash 검증 후 atomic rename하고, DB transaction 실패 시 orphan reconciliation queue에 남긴다.

현재 코드의 `manual start`는 첫 화면을 자동 저장하지 않아 첫 좌표가 900~1,800px로 시작해도 smoke가 통과한다. manual/auto 모두 entry segment를 만들고 coverage validator를 공통 적용하라.

#### 검색 결과 전체

1. 검색 실행마다 `search_context_id`를 만들고 검색 URL, query, 필터 chip/text/value, displayed total을 저장한다.
2. 현재 페이지를 profile과 동일한 segment manifest로 먼저 완전 캡처한다.
3. 가상 목록은 DOM node 수가 아니라 unique source item key/hash의 누적 수로 완료를 판단한다.
4. 페이지네이션마다 page index/cursor, displayed range, result identity hash 집합을 저장한다.
5. 다음 페이지로 이동하기 전에 SQLite transaction commit과 image file fsync/hash 검증을 끝낸다.
6. 마지막 페이지는 next disabled/absent, 결과 범위, unique item count로 증명한다.
7. zero-result는 성공이 아니라 별도 evidence state다. 필터와 빈 결과 화면이 함께 있어야 한다.
8. RPS, 사람인, 잡코리아 adapter가 모두 같은 contract tests를 통과해야 한다.

### 6. Supabase 파생 구조

라이브 구조를 먼저 dump하고 RLS를 확인하라. 2026-08-17 read-only 관찰 기준 핵심 규모는 다음과 같다.

| 대상 | 행 수 |
|---|---:|
| `profile_archives` | 1,386 |
| `organization_analysis` | 1 |
| `org_company_mapping` | 528 |
| `org_role_salary_stats` | 33 |
| `company_identity_links` | 7,484 |
| `company_source_documents` | 19,694 |
| `company_business_terms` | 39,189 |
| `industry_company_source_profiles` | 5,195 |
| `career_company_edges` | 23,439 |
| `career_company_segments` | 2,318 |

새로운 public 원본 테이블을 성급히 만들지 않는다. 다음 원칙으로 migration을 작성한다.

- 기존 `profile_archives`는 compatibility summary로 유지한다.
- 상세 manifest와 민감 원문은 private schema/private bucket을 사용한다.
- public/analytics에는 허용된 derived observation과 aggregate만 둔다.
- `company_identity_links`와 실제 canonical key를 재사용한다.
- `organization_analysis` 1개 테이블에 JSON을 계속 덮어쓰지 말고 evidence-backed views/materialized views를 만든다.
- migration에는 RLS enable, deny-by-default policy, service-role ingest, 최소 analyst role read, signed URL TTL, audit log를 포함한다.
- repository migration의 `profile_archives`에는 RLS 선언이 없으므로 이를 L3 결함으로 다룬다. RLS를 실제 DB에서 읽고 역할별 allow/deny test를 통과하지 못하면 raw export를 `NOT_RUN`으로 둔다.

### 7. Organization Analysis와 영업용 뷰

“인재밀도”는 표본 편향을 숨기는 하나의 숫자로 만들지 않는다. 최소 다음 둘을 분리한다.

- `observed_archive_density`: ValueHire가 캡처한 표본 안에서 해당 회사·역할이 차지하는 비율
- `market_estimated_density`: 검색 표시 total과 채널 coverage를 분모로 쓴 추정치. 근거와 confidence가 있을 때만 노출

다음 뷰를 canonical company id 기준으로 제공한다.

- `v_org_talent_density_observed`: role/seniority/location별 numerator, denominator, sample size, coverage, freshness
- `v_org_school_origin_distribution`: 학교 분포, 졸업연도 bucket, sample size
- `v_org_prior_company_distribution`: 이전 회사 유입 분포와 `career_company_edges` 연결
- `v_org_role_activity_summary`: 회사에서 실제 수행한 업무/제품/기술/성과 taxonomy와 원문 evidence count
- `v_org_hiring_departure_flows`: 기존 dashboard/company edge 자산을 이용한 유입·이탈 흐름
- `v_org_salary_distribution_safe`: 역할·연차 bucket별 min/median/max, cohort `k>=5`; 개인 원문 비노출
- `v_org_analysis_freshness`: field별 source count, confidence, captured_at, stale_after, conflict state
- `v_archive_coverage_status`: 검색/프로필별 full coverage, partial reason, missing data class
- `v_supabase_export_backlog`: pending/failed/readback mismatch와 age

새 고객사 A가 들어오면 다음이 한 번에 조회돼야 한다.

1. A의 canonical identity와 별칭/도메인 확정 상태
2. 관찰 표본 수와 채널/기간 coverage
3. 학교·이전 회사·현 역할·연차 분포
4. 재직자들이 실제로 수행한 업무·제품·기술·성과 주제
5. 채용/이탈 흐름과 역할별 연봉 분포
6. 각 숫자의 분모, evidence count, freshness, confidence, conflict
7. 개인을 열람할 권한이 있을 때만 근거 후보 archive로 drill-down

### 8. 사업적으로 추가할 요구사항

1. **표본 편향 표시** — ValueHire archive는 시장 전체가 아니다. 채널별 coverage와 분모 없는 순위를 금지한다.
2. **회사 identity 품질 KPI** — exact/alias/domain/manual-review 비율을 매주 본다. 미해결 회사는 고객 리포트 집계에서 제외한다.
3. **필드별 provenance** — 조직 분석 JSON 전체에 confidence 하나를 주지 말고 각 필드가 어느 archive/search/JD에서 왔는지 연결한다.
4. **변경 이력** — JD, 회사 업무 taxonomy, salary band, 조직분석은 overwrite하지 않고 revision을 만든다.
5. **영업 trigger** — 신규 고객 company id가 생성되면 precompute job을 만들되, raw evidence 권한과 cohort 기준을 지킨다.
6. **재사용 권리 상태** — source channel별로 `internal_recruiting`, `analytics_aggregate`, `customer_report`, `model_training` 사용 가능 여부를 별도 기록한다.
7. **삭제 전파** — 후보자 삭제 요청이나 retention 만료가 local file, object, derived observation, vector/embedding, cache까지 전파돼야 한다.
8. **관측 가능성** — capture latency, screenshot bytes, retry, gap, extractor coverage, export backlog/readback mismatch를 dashboard로 본다.
9. **비용 상한** — 페이지/장수/바이트/OCR/LLM/export retry cap을 초과하면 부분 결과를 보존하고 명시적으로 중단한다.
10. **고객 리포트 안전성** — 개인 salary와 소수 cohort를 숨기고, 개인 업무 원문을 고객에게 자동 노출하지 않는다.
11. **운영자가 읽는 화면** — 회사 입력 시 위 조직분석·운영 뷰의 표본 수·분모·최신성·확신도·충돌 상태를 한 화면에 보여주고, 권한이 있을 때만 evidence로 내려가게 한다. JSON을 직접 읽는 것을 완료로 보지 않는다.

### 9. 테스트

#### RED fixture

- 4,200px, 20,000px, 100,000px 문서
- sticky header/footer, nested iframe, nested scroll container
- 펼침 전후 document height 변경
- 동일 이미지처럼 보이는 반복 영역과 content hash 변화
- virtualized search list, duplicate item, missing page, zero-result
- 첫 스크롤이 900/1,800px인 manual capture
- salary explicit/range/redacted/not-present/parse-failed/inferred
- 동일 회사 한글/영문/법인/브랜드/자회사/동명이름
- Supabase 200 응답 후 readback 누락/변조/부분반영
- 같은 tab에서 capture start 2회, batch worker 2개가 같은 range를 집는 동시성
- image file rename 직전/직후와 SQLite commit 직전/직후 process crash
- retention 삭제 중 object만 실패하는 경우

#### 합격 단언

- 첫 segment 0, 마지막 하단, 모든 gap 0, sequence 연속, image/content hash 존재
- SQLite archive/page/segment/file transaction 회복 시험
- 기존 796건 additive migration 후 row/file count 보존
- 검색 모든 페이지의 filter/page/item evidence가 재현 가능
- salary와 career duty state가 누락/실패를 구분
- 원문 span으로 structured observation을 역추적 가능
- export payload whitelist snapshot, idempotency, accepted/rejected 회계, remote readback hash 일치
- role별 RLS 허용/차단 test
- encryption key rotation과 backup restore 후 원문 복호화/삭제 test
- 두 capture/batch worker의 idempotency와 expired lease recovery test
- cohort 미달 salary aggregate 비노출
- 삭제 영수증과 derived/view 비노출 검증

#### 라이브 검증 게이트

- 채널별 owner-approved sample 1개 이상, 식별정보는 로그에 출력하지 않는다.
- 실제 sample은 로컬 capture까지만 기본 허용한다.
- raw Supabase/object export는 retention/RLS/delete receipt가 승인되고 테스트된 뒤 별도 실행한다.
- LinkedIn/RPS 자동 pagination은 policy contract가 승인되지 않으면 실행하지 않는다.

### 10. 성능·운영 목표

- 화면 캡처 자체 p95 500ms 이하를 목표로 하되, DOM 안정 대기와 batch flush는 별도 지표로 분리한다.
- 장당 평균은 `capture_duration_ms`, `stability_wait_ms`, `flush_duration_ms`, `total_elapsed_ms`로 나눠 기록한다.
- 100,000px fixture를 bounded retry 안에 완전 캡처하고 메모리 상한을 넘지 않는다. segment는 주기적으로 SQLite/file에 flush해 브라우저 종료 시 손실 범위를 제한한다.
- 이미지 품질/용량은 채널별 동일 품질 contract로 비교하고, 원본 해시를 유지한 채 approved derivative를 만들 수 있다.

### 11. 구현 순서

1. 현재 v4 DB/extension/server 계약을 테스트로 고정한다.
2. coverage validator와 4k/20k/100k RED fixture를 먼저 추가한다.
3. manual/auto 공통 entry segment와 geometry manifest를 구현한다.
4. search page/pagination archive와 세 channel adapter contract를 구현한다.
5. salary/career-duty observations와 company resolution을 구현한다.
6. export batch ledger/readback/whitelist를 구현한다.
7. private storage/RLS/retention/delete receipt를 구현한다.
8. Organization Analysis views와 cohort privacy를 구현한다.
9. 기존 archive backfill은 hash/geometry가 없는 행을 `LEGACY_PARTIAL`로 유지하고 완료로 승격하지 않는다.
10. targeted tests → migration rehearsal → full verify → live approved sample → Claude 공격 감사 → Codex 재공격 순으로 검증한다.

### 11-1. 단계별 되돌리기

- capture manifest는 feature flag로 기존 저장 경로와 병행 시작하고, 구형 `archives`/`screenshots` read path를 유지한다.
- DB migration은 table/column/index 추가만 허용한다. legacy backfill은 원본 행을 갱신하지 않고 revision/상태 행을 추가한다.
- Supabase export는 whitelist version별 kill switch를 두고, 원격 오류 시 SQLite 상태를 `pending`으로 되돌릴 수 있어야 한다.
- Organization Analysis는 새 view 이름으로 출시하고 기존 `organization_analysis` consumer를 즉시 교체하지 않는다.
- rollback rehearsal은 feature flag off → 구형 read path 정상 → 신규 batch 중단 → pending 보존 → 기존 archive/file count 동일을 증명한다.

### 12. 배송 중단선

다음 중 하나라도 남으면 merge/deploy/live raw export를 하지 않는다.

- full coverage false positive 가능성
- search pagination의 누락 또는 무한순회
- salary/career duty provenance 부재
- company identity fuzzy auto-link
- export readback 불일치
- RLS/retention/delete receipt `NOT_RUN`
- 기존 archive/file 손실
- 실제 후보자 식별정보가 로그·git·테스트 fixture에 노출

최종 보고는 결론 → 판단 근거 → 명령/출력/DB readback의 3층으로 작성하고, 실행하지 못한 항목을 명시한다.

## 현재 검증 증거

### 로컬 운영 자산

- archives 796, archive에 유효하게 연결된 screenshots 12,848
- 유효 연결 집합의 missing screenshot file 0; 부모 archive 없는 screenshot 행 6, DB 미참조 파일 2
- screenshot sequence gap archive 0
- screenshot count mismatch archive 0
- salary structured 34, career company structured 12
- screenshot count p50 5, p95 70, p99 167, max 264
- `doc_height` 양수 34건이 있으나 해당 archive들의 screenshot geometry가 비어 있어 full coverage 증명 0건

### Supabase read-only 관찰

- `profile_archives` 1,386
- screenshot positive 1,056, text positive 1,127
- salary non-null 33, career nonempty 12, structured nonempty 514
- document height positive 51, viewport height positive 551
- 직접 DB 인증이 되지 않아 live RLS policy dump는 `NOT_RUN`; PostgREST schema와 집계만 확인. repository의 `20260530000000_profile_archives_sync.sql`에는 RLS enable/policy가 없음

### 기존 smoke

- archive append: PASS
- extension auto capture: PASS
- extension human capture: PASS
- extension host permission: PASS
- mock Supabase explicit batch: PASS

단, 기존 smoke는 여러 장 저장과 sequence 연속만 보고 full coverage를 보지 않는다. 수동 smoke의 첫 screenshot이 1,650px, 채널 smoke 일부가 900~1,800px에서 시작해도 통과하는 반례를 확인했다.

### 긴 페이지 벤치마크

임시 Chrome profile, 임시 SQLite, 합성 문서만 사용했으며 사장님 Aside 브라우저와 실제 후보자 데이터에는 접촉하지 않았다.

| 실제 측정 문서 높이 | 1차 run | 독립 2차 run | coverage |
|---:|---:|---:|---|
| 4,261px | 9장, 11.839s, p50/p95/max 56/266/282ms | 10장, 14.159s, p50/p95/max 57/72/124ms | PASS/PASS |
| 20,061px | 60장, 46.780s, p50/p95/max 56/131/368ms | 59장, 48.493s, p50/p95/max 57/101/317ms | PASS/PASS |
| 100,061px | 293장, 209.276s, p50/p95/max 57/186/559ms | 279장, 181.945s, p50/p95/max 55/294/1,155ms | PASS/PASS |

PASS는 첫 좌표 0, 실제 브라우저 문서 하단 도달, 최대 gap 0, 모든 geometry 유효, sequence 연속, 브라우저 세션 장수=archive 선언 장수=SQLite screenshot 행 수, 모든 이미지 SHA-256 고유를 뜻한다. 최초 판정기는 서버의 `doc_height=NULL`을 숫자 0처럼 비교해 거짓 PASS 가능성이 있었고, 다음 판정기는 마지막 메모리 frame과 DB 장수의 완전 일치를 강제하지 않았다. 두 결함을 차례로 고친 뒤 3종을 전부 재실행했다. 서버가 document height를 저장하지 않는 현재 결함은 그대로 구현 대상이다.

재시도가 많은 이유는 단일 wheel event가 항상 새 frame을 만들지 않기 때문이다. 1차 run의 20k/100k에서 시도 중 약 46~48%가 보조 이벤트를 필요로 했다. 합성 시험에서는 bounded 보조 key event로 회복했지만 제품은 이 재시도·coverage 검증을 내부 상태기계로 가져와야 한다. 장수와 시간의 실행별 변동도 있으므로 p50/p95뿐 아니라 페이지별 총시간·장수·retry율을 운영 지표로 저장한다. 실제 운영 이미지 12,850개 파일의 평균 크기는 약 255KB, p50 241KB, p95 449KB, 최대 1.57MB다. 따라서 저장비 계산은 합성 이미지 용량이 아니라 이 운영 분포를 사용한다.

현재 benchmark fixture는 긴 단일 합성 본문만 검증한다. iframe, sticky header, 동적 확장, virtualized list, 검색 pagination, 연봉 variant, 실제 사람인·잡코리아·LinkedIn/RPS DOM은 아직 검증하지 않았으므로 `NOT_RUN`으로 유지하고, 아래 구현 AC의 RED/GREEN fixture와 승인된 live sample gate에서 별도로 증명한다. 또한 현 server의 `doc_height=NULL`이어도 benchmark가 실제 browser 측정 높이로 coverage를 계산해 PASS할 수 있으므로, 이 결과는 캡처 알고리즘의 연속성 증거이지 제품 저장 manifest가 완성됐다는 증거가 아니다.
