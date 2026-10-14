# LLM 위키 필드 실사·복구 goal — 2026-10-14

위험등급 **L3**(운영 DB·후보자 개인정보). 명령: 2026-10-14 `/strict` "Supabase·SQLite 데이터 확인 → 위키 필드 미비 복구·업서트 → 프롬프트 → 실행 → 메일 보고". 추가 지시: 통과 수준이면 SOT 등재·유지보수 문서화, Jev(TypeSafe) 검토 결과를 정확도 작업에 활용.

## 1층 결론

- 위키에 필요한 필드는 운영 Supabase에 **이미 있지만 비어 있거나 연결이 끊겨** 있다. 새 테이블은 필요 없다.
- 복구 가능한 가장 큰 공백 하나를 찾아 복구 도구를 만들고 dry-run으로 실측했다: 로컬 아카이버에만 있는 구조화 프로필 **13,600건**을 운영 `profile_archives`에 채울 수 있다(쓰기 0건으로 확인).
- **실제 업서트는 실행하지 않았다.** 비로그인(anon) 키로 운영 프로필·Gmail·활성 후보 전부가 읽히는 상태를 독립 확인했고, 그 위에 구조화 프로필을 올리면 노출 면적만 커진다. anon 차단 승인이 먼저다.
- 다른 세션이 같은 날 같은 주제의 감사 문서 3개를 먼저 만들었다(미커밋). 중복 제작하지 않고 참조했다.
- 사장님이 결정할 것: ① anon 차단 마이그레이션 운영 적용 승인 ② 승인 뒤 `--apply` 실행 승인.

## 2층 판단 근거

**선택한 길** — 기존 `profile_archives`의 빈 `structured_json`만 채우는 최소 복구. 원격에 행이 있고 값이 null인 경우만, 서버측 `structured_json=is.null` 조건을 붙여 PATCH한다. 다른 주체가 먼저 채우면 0행 매치로 끝나고 덮어쓰지 않는다. 쓰기마다 장부(local_id·sha256·매치 수)를 남겨 되돌릴 수 있다.

**버린 길** — (a) 새 후보자 마스터/인박스 4테이블 신설: 정본이 둘이 된다. (b) upsert(INSERT…ON CONFLICT)로 한 번에: 원격에 없는 행을 부분 INSERT할 수 있어 거부. (c) 로컬 SQLite를 정본으로: 8월에 멈춘 수령증 DB와 2,889개 중복 URL이 있어 정본 자격이 없다. (d) 업서트 즉시 실행: anon 노출 위에서 개인정보를 늘리는 것이라 유예 대상이 아니다(`feedback_no_default_suppression`).

**틀리면 깨지는 것** — `local_id`가 운영에서 유일하지 않으면 PATCH가 여러 행에 닿는다(dry-run에서 13,633 로컬 ↔ 13,633 원격 1:1 확인, 그러나 유일 제약 존재는 PG 카탈로그로 미확인). anon 노출 원인이 뷰/GRANT가 아니라 다른 경로면 ⓪ 차단안이 바뀐다.

## 3층 현재 상태 (file:line·실행 출력)

- `Valuehire_v4/tools/profile-archiver/server/index.js:1611-1624` — `syncToSupabase`의 upsert 페이로드. `local_id·url·site·page_title·captured_at·text_content·ocr_text·…·run_id`만 보내고 **`structured_json`·`career_companies_json`·`salary_man`을 보내지 않는다**. → 로컬 13,633건이 운영에 2.4%(514건)만 있는 직접 원인.
- `Valuehire_v4/supabase/migrations/20260526010000_phase1_data_lake_schema.sql:236` — `pipeline_candidates_active` 뷰 정의. `security_invoker` 없음. 기본 테이블은 anon 0건(RLS 동작)인데 뷰는 21,771건 반환 → 뷰가 소유자 권한으로 RLS를 우회.
- `Valuehire_v4/supabase/migrations/20260530000000_profile_archives_sync.sql` — `row level security`·`policy`·`grant` 문구 0건. → `profile_archives`에 RLS 자체가 없다.
- `Valuehire_v4/app/api/pipeline/candidates/[id]/route.ts:44` — 단계 이력 insert 결과 미확인(Codex 지적 재확인). `supabase/migrations/20260507000000_pipeline.sql:20` — `pipeline_stage_history.candidate_id … on delete cascade`.
- 실측 전체: [`evidence/llm-wiki-field-recovery-evidence-2026-10-14.md`](evidence/llm-wiki-field-recovery-evidence-2026-10-14.md) (A 테이블 222개 건수, B 빈 비율, C 로컬 SQLite, D 교차 표본, E anon 건수, F dry-run, G 감사기, H 인수 검사).

### 근본 원인
1. 동기화 코드가 구조화 칼럼을 누락(위 index.js). 2. `profile_archives`에 RLS가 없고 활성 후보 뷰가 `security_invoker` 없이 노출. 3. Gmail 파생 사건(21,791)과 단계 이력(56)은 사람·포지션에 연결하는 코드가 애초에 없다.

## 인수 기준 (EARS) — 이번 WU 범위

| ID | 단언 | 검증 명령 | 기대 |
|---|---|---|---|
| AC-1 | When 원격 행이 없으면 시스템은 그 local_id를 쓰지 않아야 한다 | `python3 -m unittest scripts.llm_wiki.test_backfill_structured_profiles -k present_and_empty` | OK |
| AC-2 | If 원격 값이 이미 있으면 시스템은 덮어쓰지 않아야 한다(계획·서버 양쪽) | 위 + `-k zero_match` | OK, 쓰기 URL에 `structured_json=is.null` |
| AC-3 | While dry-run이면 쓰기 요청과 장부가 0이어야 한다 | `-k dry_run` + 운영 dry-run 출력 `"written": 0` | OK / 장부 파일 없음 |
| AC-4 | If 자격증명이 없으면 rc 2(NOT_RUN)여야 한다 | `-k missing_creds` | OK |
| AC-5 | 감사기는 검사 대상 0건·문턱 필드 누락을 PASS로 만들지 않아야 한다 | `python3 -m unittest scripts.llm_wiki.test_field_audit` | 7 OK |
| AC-6 | 보호 조건을 빼면 검사가 빨개져야 한다(P13⑥) | `bash scripts/acceptance-llm-wiki-fields.sh` | `MUTATION[*]: PASS`, `VERDICT: PASS` |
| AC-7 | SOT 문턱 표는 감사기가 실제로 읽어야 한다 | 같은 스크립트 `SOT_THRESHOLDS: PASS` | PASS |

counter-AC: 시험이 FakeTransport만 보고 실제 PostgREST 질의 문법을 못 본다(→ 운영 dry-run으로 GET 경로만 실증, PATCH 경로는 승인 전 미실증 — **알려진 한계**); `local_id` 유일성 가정; 장부 파일이 지워지면 되돌리기 불가; 감사기 하한을 실측 바로 아래에 두어 "항상 PASS"로 보이는 것(→ 의도된 퇴행 감지이며 §4 목표 열은 검사 안 함을 SOT에 명기).

## 입출력·오류·경계 계약

- 입력: `--db`(sqlite, `mode=ro`), `--env`(v4 `.env.local`), `--apply`, `--limit`, `--ledger`. 출력: JSON 한 줄(`mode, local_rows, remote_rows_found, to_fill, skipped_*, written, unmatched, ledger`). 오류: 자격증명 없음 rc 2, HTTP 오류는 예외로 종료(조용히 0건 성공 금지). 경계: 200건 배치 GET, PATCH는 행당 1회·`return=representation`으로 매치 수 readback, 재실행 멱등(이미 채운 행은 `skipped_filled`).
- 되돌리기: 장부의 `local_id`마다 `structured_json=null` PATCH. 비용 13,600 요청(~15분).
- 영향 반경: `profile_archives.structured_json` 한 칼럼. 다른 테이블·칼럼 무변경.

## 결정 카드

> **무엇을** — 복구 도구+감사기+SOT를 만들고 실행은 anon 차단 뒤로 미룬다
> **왜** — 개인정보 노출 위에 데이터를 더 얹지 않는다. 도구는 승인 즉시 한 명령으로 돈다
> **버린 길** — 즉시 실행(노출 확대), 새 스키마(정본 분열), 로컬 정본화(중복·정지 DB)
> **대가** — 위키 점수·프로필 필드가 승인 전까지 2.4%로 남는다
> **되돌리기** — 도구는 git revert, 데이터는 장부 기반 null 복원

> **무엇을** — 감사기 하한을 실측 바로 아래 "퇴행 감지"로 두고 목표는 검사하지 않는다
> **왜** — 목표를 하한으로 두면 복구 전까지 영구 FAIL이고, 그 FAIL은 아무 정보도 주지 않는다
> **버린 길** — 목표치 하한(영구 빨강), 하한 없음(퇴행을 못 봄)
> **대가** — 복구 후 사람이 하한을 올리는 PR을 잊으면 느슨해진다(SOT §6-2에 절차 고정)
> **되돌리기** — 표의 숫자 수정

## 배송 상태

`LOCAL_ONLY`. 제품 표면 신설 없음(SKELETON 해당 없음). 운영 쓰기 0건. PR·push는 수동 승인 뒤.

## 검증 장부 (T)

| 항목 | 명령 | 시각 | 종료값 | 상태 |
|---|---|---|---|---|
| 원칙 정본 직접 로드 | `head docs/sot/coding-principles.md`, `principles.yaml` | 11:41:33 | 0 | PASS |
| 원칙 검사기 | `bash scripts/acceptance-principles-check.sh` | 11:41:38 | 0 (`MECHANISMS: PASS 34/34`) | PASS |
| RED | `python3 -m unittest scripts.llm_wiki.test_backfill_structured_profiles` | 11:52:10 | 1 (6/7 AssertionError) | RED 확인, 커밋 d2889f2 |
| RED(감사기) | `… test_field_audit` | 11:52:45 | 1 (5F 1E) | RED 확인, 커밋 3ed0c7f |
| GREEN | 두 묶음 | 11:53:43 / 11:55:32 | 0 (7+7 OK) | PASS |
| R2 변조 | is.null 제거 / 부재 행 채우기 | 11:55:32 | 1 / 1 | 둘 다 차단 |
| 인수 검사 | `bash scripts/acceptance-llm-wiki-fields.sh` | 11:55:45 | 0 | PASS |
| 운영 dry-run | `backfill_structured_profiles.py --db … --env …` | 11:53:48→11:54:02 | 0, written 0 | PASS |
| 운영 감사기 | `field_audit.py --env …` | 11:55:46 | 0 | PASS |
| 저장소 게이트 | verify.sh·silent-failure·data-exposure·check-docs-sot·ci-step-integrity | 아래 적대 검증 로그에 기록 | | |
| V1 (독립 엔진) | Codex | | | 아래 |
| V2 | | | | 아래 |

## 비범위

anon 차단 마이그레이션 작성·적용(승인 뒤 별도 WU ⓪), Gmail 사건 연결(③), 단계 이력 복구(④), 조회 화면·LLM 요약·Discord, Jev 점수 공식 변경, 10만 명 성능 측정.

## Jev(TypeSafe) 활용 판정

`~/valuehire-private/wu3/wu35/jev_results.jsonl` 1,514줄(`jev-1.13.0`)은 키가 `회사|이름|idx`라 DB ID로 바로 붙지 않고, WU3-7까지 결론은 "점수 공식이 결과를 못 가른다(역전율 37.5%)"이다. 따라서 이번 WU에서는 위키 점수 필드의 **평가 주체·모델·시각 기록 계약**만 SOT §2에 고정했고, Jev 재연결·공식 수정은 별도 goal로 남긴다. 사용 가능한 자산이지 즉시 정확도를 올리는 입력은 아니다.

## 적대 검증 로그

(아래에 명령·전체 출력·세션 식별자를 덧붙인다)
