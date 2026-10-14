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
| profile_archives.structured_json | 2 | 2.4% | 60 | 로컬 13,600건 복구 대기(§5 ①) |
| pipeline_candidates.ai_assessment | 75 | 77.6% | 90 | AI Search 유입 행의 점수 근거 |
| pipeline_candidates.resume_data | 35 | 38.7% | 70 | 이력서 구조화 |
| pipeline_candidates.email | 3 | 3.1% | — | 자동 병합 키로 쓰기엔 부족 |
| sourcing_results.fit_reason | 85 | 86.7% | 95 | 목록의 "왜 잘 맞는지" |
| gmail_derived_events.candidate_id | 0 | 0.0% | 50 | 사건→사람 연결 미구현(§5 ③) |

판정: 하한 미달·검사 대상 0건·표에 있는데 집계 없음 → FAIL, 조회 오류 → NOT_RUN(rc 2). 자격증명이 없어도 PASS 가 아니다. 값(개인정보)은 읽지 않는다.

## 5. 복구 절차와 순서 (고정)

| # | 작업 | 선행 조건 | 도구 | 되돌리기 |
|---|---|---|---|---|
| ⓪ | **익명(anon) 읽기 차단** — `profile_archives`·`gmail_messages`·`pipeline_candidates_active`(뷰) | 운영 권한 변경 승인 | 마이그레이션(RLS/`security_invoker`/GRANT 회수) + HTTP 재검증 | 마이그레이션 down |
| ① | `profile_archives.structured_json` 13,600건 채움 | ⓪ 완료, HTTP 로 anon 0건 확인 | `backfill_structured_profiles.py --apply` | 장부(`~/valuehire-private/llm-wiki/backfill-ledger.jsonl`)의 `local_id` 를 null 로 |
| ② | 아카이버 동기화에 `structured_json`·`career_companies_json`·`salary_man` 추가 | ① 과 같은 PR 권장 | v4 `tools/profile-archiver/server/index.js` `syncToSupabase` | 코드 revert |
| ③ | `gmail_derived_events` → 후보·포지션 연결 | 식별 규칙 §3 | 신규 goal | 연결 컬럼 null |
| ④ | `pipeline_stage_history` 를 ClickUp 미러에서도 기록 + `on delete cascade` 제거 | 신규 goal | v4 미러·마이그레이션 | — |

⓪ 이전에 ①을 실행하지 않는다. 개인정보 노출 면적을 키우기 때문이며, 유예 대상이 아니다.

## 6. 유지보수 — 다음 세션이 할 일

1. `python3 -m unittest scripts.llm_wiki.test_backfill_structured_profiles scripts.llm_wiki.test_field_audit` 가 CI(`bash scripts/acceptance-llm-wiki-fields.sh`)에서 돈다. 보호 조건을 빼면 빨개져야 한다(검사기 자체의 변조 시험 포함).
2. 복구를 한 번 돌릴 때마다 `field_audit.py` 를 실행해 출력 전체를 `docs/engineering/evidence/` 에 날짜로 남기고 §4 하한을 올린다.
3. 새 필드를 위키에 쓰려면 §2 표에 정본·쓰기 주체를 먼저 적고 §4 에 하한을 넣는다. 표에 없는 필드는 위키 필드가 아니다.
4. 이 문서는 `docs/sot/INDEX.md` 에 등재된다. 스크립트가 참조하는 유일한 답이므로 `docs/engineering/` 로 내리지 않는다.
