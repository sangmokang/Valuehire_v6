# LLM 위키 — 데이터 필드 정본과 유지보수 계약 (SOT)

- 문서 ID: `VH6-LLMWIKI-SOT-001`
- 최종 갱신: 2026-10-14
- 근거: `docs/engineering/llm-wiki-field-recovery-goal-2026-10-14.md`(실측·판정), `docs/engineering/llm-wiki-supabase-audit-2026-10-14.md`(API 객체 222개 전수, 다른 세션 산출물)
- 현 상태: **필드 계약·복구 절차·유지보수 검사만 고정.** 조회 화면·LLM 요약·Discord 연동은 미구현이며 이 문서가 그 완료를 주장하지 않는다.

## 1. 한 줄 계약

LLM 위키는 새 저장소가 아니다. 운영 Supabase(v4 프로젝트)의 기존 테이블을 **원천 ID로 연결하고 빈 필드를 채우는** 일이며, 모든 값은 원천·시각·평가 주체를 함께 갖는다. 후보자 개인정보 원문은 Git·Notion·Markdown 으로 복제하지 않는다.

## 2. 데이터 성격별 정본(SOT)

| 데이터 | 정본 | 위키가 보관하는 것 | 쓰기 주체 |
|---|---|---|---|
| 후보자 마스터 | Supabase `pipeline_candidates` | 전부 | ClickUp 미러(`sync_origin=clickup`) + AI Search 저장 경로 |
| 프로필 원문·구조화 | Supabase `profile_archives` (로컬 아카이버 `archive.db`가 1차 수집) | `structured_json`·`career_companies_json`·`salary_man` | 아카이버 동기화 + `scripts/llm_wiki/backfill_structured_profiles.py` |
| AI Search 결과 | Supabase `sourcing_results` + `pipeline_candidates(source like 'ai_search:%')` | 실행 ID·채널·원천 ID·URL·점수·평가 주체·근거 | AI Search 실행기 |
| 진행 단계 | **ClickUp** | 현재값 미러 + `pipeline_stage_history` 사건 | ClickUp 미러만(Valuehire 화면은 읽기) |
| 메일 | **Gmail** | `gmail_messages`(원문·ID·시각) + `gmail_derived_events`(분류·후보/포지션 연결) | Gmail 적재기 |
| 팀 결정·논의 | **Discord/Notion** | 메시지 ID·링크·발생 시각·요약(원문 대량 복제 금지) | 미구현 |
| 고객사 지식 | Supabase `customer_ontology_documents`·`notion_clients` | Markdown + 원천 해시 | 온톨로지 수집기(브라우저 경로 정본 `v4 docs/sot/11-customer-ontology-ingestion.md`) |
| 점수 | 점수를 만든 **순수 함수**(P14) | 숫자 + `평가 주체·모델·버전·시각·입력 해시` | 평가 실행기. Jev(`jev-1.13.0`, TypeSafe) 결과는 평가 주체로 기록하되 공식 변경은 별도 goal |

## 3. 식별·중복 규칙

1. 사람 묶기는 **(provider, provider_subject_id)** 또는 정규화 공개 URL·확인된 이메일이 정확히 일치할 때만 자동. 이름+회사만 같으면 검토 큐.
2. 같은 사람의 재발견은 중복이 아니라 **새 관측 사건**이다. 원천 ID 하나로 접어 재검색 이력을 지우지 않는다.
3. `occurred_at`(발생)과 `observed_at/ingested_at`(수집)을 분리한다. 원래 시각이 없으면 null 이며 현재 시각을 넣지 않는다.
4. 내부 보고 메일은 발송 증거가 아니다. 채널별 실제 발송 증거만 발송으로 센다.

## 4. 최소 채움률 (유지보수 검사 문턱)

`scripts/llm_wiki/field_audit.py --env <v4 .env.local>` 가 이 표를 읽어 운영 DB 를 건수만으로 집계한다. **하한은 퇴행 감지용**이며 실측값 바로 아래에 둔다. 복구가 끝나면 이 표의 숫자를 올리는 변경을 같은 PR 에 동봉한다. 목표 열은 검사하지 않는다.

| 객체.필드 | 최소 채움률 | 2026-10-14 실측 | 목표 | 비고 |
|---|---|---|---|---|
| profile_archives.structured_json | 60 | 62.1% (10-14 14:33, ① 완료 후; 적용 전 2.4%) | 70 | 나머지 38% 는 로컬에도 구조화가 없는 행(아카이버 재추출 대상) |
| pipeline_candidates.ai_assessment | 75 | 77.6% | 90 | AI Search 유입 행의 점수 근거 |
| pipeline_candidates.resume_data | 35 | 38.7% | 70 | 이력서 구조화 |
| pipeline_candidates.email | 3 | 3.1% | — | 자동 병합 키로 쓰기엔 부족 |
| sourcing_results.fit_reason | 85 | 86.7% | 95 | 목록의 "왜 잘 맞는지" |
| gmail_derived_events.candidate_id | 0 | 0.0% | 50 | 사건→사람 연결 미구현(§5 ③) |

판정: 하한 미달·검사 대상 0건·표에 있는데 집계 없음 → FAIL, 조회 오류 → NOT_RUN(rc 2). 자격증명이 없어도 PASS 가 아니다. 값(개인정보)은 읽지 않는다.

### 4-b. 익명(anon) 키 허용 건수 — 전부 0

`scripts/llm_wiki/anon_exposure_audit.py --env <v4 .env.local>` 가 이 표를 읽어 **비로그인 anon 키**로 각 객체의 건수를 HEAD 로 센다. 허용 건수는 0 만 쓸 수 있다(다른 숫자는 정본 오류로 거부). 1건이라도 보이면 FAIL, 401/403 은 차단된 것이므로 0 으로 센다. 2026-10-14 13:45 실측은 아래 전부 노출(§5 ⓪ 적용 전).

| 객체 | anon 허용 건수 |
|---|---|
| profile_archives | 0 |
| gmail_messages | 0 |
| gmail_sync_state | 0 |
| candidates | 0 |
| pipeline_candidates_active | 0 |
| pipeline_candidates_archive | 0 |
| unified_candidate_history_view | 0 |

## 5. 복구 절차와 순서 (고정)

| # | 작업 | 선행 조건 | 도구 | 되돌리기 |
|---|---|---|---|---|
| ⓪ | **익명(anon) 읽기 차단** — `profile_archives`·`gmail_messages`·`pipeline_candidates_active`(뷰) | 운영 권한 변경 승인 | 마이그레이션(RLS/`security_invoker`/GRANT 회수) + HTTP 재검증 | 마이그레이션 down |
| ① | `profile_archives.structured_json` 12,932건 채움 | ⓪ 완료, HTTP 로 anon 0건 확인 | `backfill_structured_profiles.py --apply` | `--rollback --apply`: 장부 `done·matched=1` 행 중 **원격 현재 값의 정규화 지문이 장부에 기록된 우리 값과 같은 행만**, 읽은 스냅샷의 md5 를 서버 필터(계산 칼럼 `llm_wiki_structured_md5`, v4 마이그레이션 20261014160000)로 붙여 null. 경쟁 쓰기(`matched=0`)·응답 유실(`intent`만)·로컬 재추출로 장부 지문과 달라진 행(`local_changed`)은 손대지 않고 보고 |
| ② | 아카이버 동기화에 `structured_json`·`career_companies_json`·`salary_man` 추가 | ① 과 같은 PR 권장 | v4 `tools/profile-archiver/server/index.js` `syncToSupabase` | 코드 revert |
| ③ | `gmail_derived_events` → 후보·포지션 연결 | 식별 규칙 §3 | 신규 goal | 연결 컬럼 null |
| ④ | `pipeline_stage_history` 를 ClickUp 미러에서도 기록 + `on delete cascade` 제거 | 신규 goal | v4 미러·마이그레이션 | — |

⓪ 이전에 ①을 실행하지 않는다. 개인정보 노출 면적을 키우기 때문이며, 유예 대상이 아니다.

## 6. 유지보수 — 다음 세션이 할 일

1. `python3 -m unittest scripts.llm_wiki.test_backfill_structured_profiles scripts.llm_wiki.test_field_audit scripts.llm_wiki.test_anon_exposure`(49건, skip 0)가 CI(`bash scripts/acceptance-llm-wiki-fields.sh`)에서 돈다. 보호 조건 변조 12종(서버 is.null 제거·원격 부재 행 채움·0건 통과·HTTP 오류 은폐·해시 검사 삭제·문턱 중복 허용·anon 노출 통과·0 아닌 허용값·무효 키를 차단으로 계수·지문 무시 롤백·스냅샷 md5 필터 제거·장부 sha256 무시)은 **기대한 시험 이름의 단언 실패**로만 차단으로 인정하고, 문법·import 오류 종료는 불합격이다. SOT 검사기는 양성(원본)·음성(필수 행 삭제·백틱 변조) 한 쌍으로 자기 생존을 증명한다.
1-b. 복구 장부는 쓰기당 `intent → done|error` 2줄이다. `intent`만 남은 `local_id`는 응답을 잃은 행이므로 `structured_json=not.is.null` readback 으로 대조한 뒤 재시도·되돌리기를 정한다. **장부의 `local_id` 를 일괄 null 로 되돌리지 않는다** — 다른 주체가 그 사이 쓴 값을 지운다. 되돌리기는 `--rollback`(지문 일치 행만)으로만 한다. 소유권의 근거는 **장부에 기록된 쓰기 당시 지문**(`canonical`, 구 장부는 `sha256` 이 현재 로컬 원문과 일치할 때만)이지 "지금 로컬 값"이 아니며, PATCH 는 읽은 스냅샷의 md5 를 서버 필터로 붙여 읽기와 쓰기 사이의 경쟁 갱신을 지우지 않는다(Codex 2차 2026-10-14).
1-c. anon 감사기는 먼저 anon 키가 인증을 통과하는지(탐침 객체에 2xx 또는 권한 거부 42501; "Invalid API key" 401 이면 NOT_RUN) 양성 대조군을 확인하고, 권한 거부(Postgres `42501`) 응답만 차단으로 센다. 무효 키의 401 은 NOT_RUN 이다. §4-b 표는 머리글 아래 모든 행이 `| 식별자 | 0 |` 이어야 하며 필수 7객체가 빠지면 정본 오류로 거부된다.
1-d. `pipeline_candidates_active`·`_archive` 뷰를 재정의할 때는 반드시 `with (security_invoker = true)` 를 붙인다. 옵션 없이 `create or replace view` 하면 옵션이 사라진다. anon 의 뷰 SELECT grant 는 회수돼 있어(2026-10-14 후속 마이그레이션) 옵션이 사라져도 anon 은 막히지만, 로그인 사용자의 테넌트 격리는 옵션에 의존한다.
2. 복구를 한 번 돌릴 때마다 `field_audit.py` 를 실행해 출력 전체를 `docs/engineering/evidence/` 에 날짜로 남기고 §4 하한을 올린다.
3. 새 필드를 위키에 쓰려면 §2 표에 정본·쓰기 주체를 먼저 적고 §4 에 하한을 넣는다. 표에 없는 필드는 위키 필드가 아니다.
4. 이 문서는 `docs/sot/INDEX.md` 에 등재된다. 스크립트가 참조하는 유일한 답이므로 `docs/engineering/` 로 내리지 않는다.
