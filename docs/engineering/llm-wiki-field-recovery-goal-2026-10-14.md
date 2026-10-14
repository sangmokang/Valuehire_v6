# LLM 위키 필드 실사·복구 goal — 2026-10-14

위험등급 **L3**(운영 DB·후보자 개인정보). 명령: 2026-10-14 `/strict` "Supabase·SQLite 데이터 확인 → 위키 필드 미비 복구·업서트 → 프롬프트 → 실행 → 메일 보고". 추가 지시: 통과 수준이면 SOT 등재·유지보수 문서화, Jev(TypeSafe) 검토 결과를 정확도 작업에 활용.

## 1층 결론

- 위키에 필요한 필드는 운영 Supabase에 **이미 있지만 비어 있거나 연결이 끊겨** 있다. 새 테이블은 필요 없다.
- 복구 가능한 가장 큰 공백 하나를 찾아 복구 도구를 만들고 dry-run으로 실측했다: 로컬 아카이버에만 있는 구조화 프로필 **13,600건**을 운영 `profile_archives`에 채울 수 있다(쓰기 0건으로 확인).
- ~~실제 업서트는 실행하지 않았다~~ → **2026-10-14 13:4x 사장님 승인("네, anon 차단부터 순서대로 진행해")으로 ⓪·① 을 실행했다.** ⓪ anon 차단은 13:53 운영 적용·검증 완료(7객체 anon 0건, 서비스 키·구성원 로그인 불변). ① 업서트는 표본 7건 readback 뒤 전량 적용(결과는 아래 "실행 결과" 절).
- 승인 대상 3객체 외에 같은 종류 노출 4객체(`pipeline_candidates_archive`·`unified_candidate_history_view`·`candidates`·`gmail_sync_state`)를 같은 마이그레이션에 포함했다(범위 확장, 되돌리기 스크립트 동봉). Codex 적대 검토 뒤 자료형 뷰의 **로그인 사용자 직접 읽기**도 후속 마이그레이션으로 막았다(B2C 가입 세션이 내부 이력을 읽을 수 있었음).
- Codex 적대 검토(`/codex:adversarial-review`) 2건: v6 도구 결함 4건·v4 마이그레이션 결함 3건 → 6건 수정, 1건 수용(사유 기록). 재검증 통과.
- 다른 세션이 같은 날 같은 주제의 감사 문서 3개를 먼저 만들었다(미커밋). 중복 제작하지 않고 참조했다.
- 사장님이 결정할 것: ① v6 `task/llm-wiki-field-recovery`·v4 `task/llm-wiki-anon-lockdown` push·PR 승인 ② WU-②(아카이버 동기화 코드)를 Codex 에 넘길지 — 프롬프트는 `goal-prompts/llm-wiki-wu2-archiver-sync-codex-2026-10-14.md`.

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
- 되돌리기: `--rollback [--apply]`. 장부 `done·matched=1` 행 중 원격 현재 값의 정규화 지문(키 순서·공백 무시 sha256)이 로컬 값과 같은 행만 `structured_json=not.is.null` 보호 조건으로 null. 경쟁 쓰기·응답 유실 행은 보고만. (Codex 2026-10-14 지적으로 "장부 local_id 일괄 null" 규칙 폐기.)
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

> **무엇을** — anon 차단 범위를 승인된 3객체에서 같은 종류 노출 7객체로 넓히고, 자료형 뷰는 로그인 사용자 직접 읽기까지 회수한다
> **왜** — 같은 조사에서 발견된 같은 종류의 개인정보 노출이고, 읽는 코드가 전부 service_role 이라 깨질 경로가 없다. PII 결함은 유예 대상이 아니다
> **버린 길** — 3객체만 막고 나머지는 보고만(노출 지속), 자료형 뷰를 RLS 가능한 일반 뷰로 재작성(범위 밖·성능 영향 미측정)
> **대가** — 앞으로 로그인 세션으로 자료형 뷰를 직접 읽는 기능을 만들려면 service_role 서버 경로를 거쳐야 한다
> **되돌리기** — `supabase/rollback/2026101414…down.sql`, `…15….down.sql` (실행 시 노출 재개 — 일반 복구가 아니라 비상용)

> **무엇을** — 마이그레이션은 관리 API SQL 로 적용하고 `schema_migrations` 에 같은 버전을 직접 기록한다
> **왜** — `supabase db push` 는 로컬에만 있는 0928 두 건을 같이 밀고, 원격에만 있는 4건 때문에 repair 를 요구한다(남의 드리프트를 이 작업이 건드리면 안 된다)
> **버린 길** — `db push --include-all`(무관 마이그레이션 동반 적용), psql(비밀번호 없음)
> **대가** — CLI 가 아닌 손 기록이므로 파일과 장부가 어긋날 수 있다 → `migration list --linked` 로 양쪽 버전 일치를 증거에 남겼다
> **되돌리기** — down 스크립트가 장부 행도 지운다

## 배송 상태

`PRODUCTION_VERIFIED`(DB 권한 변경·데이터 채움에 한함). 운영 URL: Supabase 프로젝트 `sjld…`(v4). 적용 SHA: v4 `06a65482`·`88e45deb` 의 SQL 을 관리 API 로 실행, `schema_migrations` 20261014140000·20261014150000. readback: anon 감사기 PASS·역할 시뮬레이션·service 키 건수 불변·표본 7건 readback 7/7. 롤백: `supabase/rollback/*.down.sql`(미실행). 제품 화면 변경 없음(SKELETON 해당 없음). `BUSINESS_USED` 는 주장하지 않는다. push·PR 은 승인 뒤 수동.

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
| **⓪ RED** | anon 키 HEAD 7객체 | 13:45:48 | 전부 `*/N` | RED 확인(증거 M-1) |
| ⓪ 사전 검증 | 마이그레이션 `commit→rollback` 치환 실행 | 13:52:25 | HTTP 201, 상태 불변 | PASS |
| ⓪ 적용 | 관리 API query + schema_migrations 기록 | 13:53:15 | 201 / 201 | PASS |
| ⓪ GREEN | `anon_exposure_audit.py --env …` | 13:53:23 | 0 (7객체 0건) | PASS |
| ⓪ 양성 대조군 | service 키 HEAD 7객체 / 역할 시뮬레이션 authenticated(@valueconnect.kr) | 13:53 | 전부 적용 전과 동일 | PASS |
| ⓪ 음성 대조군 | 역할 시뮬레이션 anon·authenticated(외부) | 13:53 | 전부 0 / matview 42501 | PASS |
| RED(anon 감사기) | `… test_anon_exposure` | 13:50:57 | 1 (8F 1E, import 오류 0) | RED, 커밋 ec820cc |
| GREEN | 세 묶음 + 인수 검사 | 13:52:52 | 0 (36 OK, 변조 8종 차단) | PASS, 커밋 fd33340 |
| ① dry-run | `backfill … ` | 13:54:07 | 0, to_fill 12932, written 0 | PASS |
| ① 표본 | `--apply --limit 10` | 13:54:21 | 0, written 7, readback 7/7 | PASS |
| ① 전량 | `--apply` (백그라운드, 로그 backfill-full-20261014.log) | 13:54:39→ | 아래 "실행 결과" | |
| Codex 적대 검토 | `/codex:adversarial-review` v6·v4 | 13:55→14:04 | needs-attention ×2 | 결함 7건 → 6 수정·1 수용 |
| 후속 ⓪ 적용 | `20261014150000` 관리 API | 14:05:19 | 201, ACL·역할 시뮬레이션 확인 | PASS |
| RED(Codex 반영) | 45건 중 7 FAIL(단언) | 14:06 | 1 | RED, 커밋 f8ce20f |
| GREEN(Codex 반영) | 45 OK · 인수 검사 변조 10종·SOT 음성 3종 | 14:10:47 | 0 | PASS, 커밋 ed6bfc7 |
| 운영 anon 감사(재) | 키 탐침 + 7객체 | 14:10 | 0 | PASS. 무효 키 → rc 2 NOT_RUN |

## 비범위

아카이버 동기화 코드 보강(②, Codex 프롬프트 작성됨), Gmail 사건 연결(③), 단계 이력 복구(④), 조회 화면·LLM 요약·Discord, Jev 점수 공식 변경, 10만 명 성능 측정, v4 마이그레이션 드리프트(로컬 0928 두 건·원격 전용 4건) 정리.

## Jev(TypeSafe) 활용 판정

`~/valuehire-private/wu3/wu35/jev_results.jsonl` 1,514줄(`jev-1.13.0`)은 키가 `회사|이름|idx`라 DB ID로 바로 붙지 않고, WU3-7까지 결론은 "점수 공식이 결과를 못 가른다(역전율 37.5%)"이다. 따라서 이번 WU에서는 위키 점수 필드의 **평가 주체·모델·시각 기록 계약**만 SOT §2에 고정했고, Jev 재연결·공식 수정은 별도 goal로 남긴다. 사용 가능한 자산이지 즉시 정확도를 올리는 입력은 아니다.

## 적대 검증 로그

(아래에 명령·전체 출력·세션 식별자를 덧붙인다)

### 저장소 게이트 (2026-10-14, 워크트리 HEAD b7e58e2)

| 검사 | 명령 | 시각 | 결과 |
|---|---|---|---|
| 비밀 스캔 | `bash verify.sh` | 11:56:23 | rc 0 `PASS: no secret-pattern match in any tracked file, .env not tracked` |
| 원칙 정본·배선 | `bash scripts/acceptance-principles-check.sh` | 11:56 | `VERDICT: PASS` (34/34) |
| 조용한 실패 린트 | `bash scripts/acceptance-silent-failure-lint.sh` | 11:56 | `CHECKED_FILES: 66`, 패턴 0건 |
| 데이터 노출 | `bash scripts/scan-data-exposure.sh all` | 11:57→12:06 | `PASS: csv/tsv/sql 5개 검사(추적 281개 중), 개인정보 적재 0건` |
| CI 스텝 무결성 | `bash scripts/verify/check-ci-step-integrity.sh` | 12:01:48 | `PASS … (job·step 32개 검사)` — 새 스텝 포함 |
| 무력화 5종 차단 | `bash scripts/acceptance-semantic-mutations.sh` | 12:03:00 | rc 0, `CHECKED: 16`, `VERDICT: PASS` (첫 실행은 커밋 중 저장소 상태 변경으로 FAIL → 커밋 뒤 재실행 PASS) |
| CI 래퍼 | `bash scripts/verify/run-acceptance.sh scripts/acceptance-llm-wiki-fields.sh` | 12:03 | rc 0 `OK(run-acceptance): … 판정 6건` |
| SOT 문서 검사 | `bash scripts/check-docs-sot.sh` | 12:01 | **FAIL(선행)**: `coding-principles.md` 20,476바이트 > 20,000. `git diff origin/main -- docs/sot/coding-principles.md` 0줄 — 이 작업과 무관, CI 목록에도 없음. 그대로 보고 |
| 함수 길이(P11) | ast 계산 | 12:01 | backfill `main` 24줄, field_audit `judge` 22줄 (hard 100) |

→ 이 작업이 만든 검사와 코드는 전부 초록이고, 유일한 빨강은 제가 손대지 않은 정본 파일 크기 검사입니다.

### V1 — Codex 독립 적대검증 (2026-10-14 12:05→12:17)

- 호출: `codex exec -s workspace-write -C <--no-local 클론> --skip-git-repo-check -o … "<중립 프롬프트>" </dev/null` (클론 HEAD b7e58e2, 응답 모델 `gpt-6.1-sol`, codex-companion 아님 → 독립 엔진 확인). 프롬프트에 구현자 결론·의심을 넣지 않았다.
- 판정 원문: `private-reviews/llm-wiki/codex-v1-verdict-2026-10-14.md`(4,091줄, sha256 `9d9ef1f2dc9fd97dfdc7cb3425c5ed3ef167054670879ace27b9e23ff4f156ab`), 실행 로그 `codex-v1-run-2026-10-14.log`. 무시 폴더라 저장소엔 없다.
- **VERDICT: FAIL — 결함 6건** (전부 실행으로 재현됨, 제 판단: 전부 타당)

| # | 심각도 | 원문 제목 | 원인 | 사업 영향 | 조치(커밋) |
|---|---|---|---|---|---|
| 1 | 높음 | 보호 조건을 빼면 검사가 빨개져야 한다 / HTTP 오류 은폐 금지 | 시험이 가짜 전송만 보고 `RestTransport` 를 호출하지 않음. 질의를 망가뜨리거나 예외를 0매치로 바꿔도 초록 | 복구가 멈추거나 일부만 성공해도 승인될 수 있음 | opener 주입으로 질의·본문·`return=representation`·HTTPError 전파 시험 3건 추가 (b5f1bc8→7ed8770) |
| 2 | 높음 | 처리한 시험 수 최소치(P20) | unittest `Ran N` 이 skip 을 포함. 12건 건너뛰어도 PASS | 보호 시험을 꺼도 정상 검증으로 표시 | `skipped=N>0` → FAIL, 최소 25건 |
| 3 | 중간 | SOT 문턱 표 실제 읽기 | 같은 필드 두 번 적으면 마지막(낮은) 값으로 덮임, 숫자 아님 행은 조용히 탈락 | 문서 편집 실수로 감사 기준이 느슨해짐 | 중복·오형식 → ValueError, 필수 필드 집합 대조 |
| 4 | 중간 | 쓰기 1건마다 장부 1줄 | 장부가 응답 뒤에만 기록돼 응답을 잃은 행은 흔적이 없음 | 장애 뒤 어느 행을 되돌릴지 장부만으로 모름 | 쓰기 전 `intent`, 뒤 `done`, 예외 `error` 줄 + 예외 전파 |
| 5 | 중간 | 구조화 JSON 최소 규약 | `_meta.input_hash` 존재만 검사. 메타만 있는 객체·숫자 해시도 통과, 검사 삭제도 시험이 못 잡음 | 형식만 갖춘 빈 자료가 채움으로 취급 | `source`·`input_hash` 문자열 + `_meta` 외 non-null 1개 이상. 재 dry-run에서 668건 제외 |
| 6 | 중간 | 변조 시험은 반드시 실패해야 한다 | 문법 오류 종료도 "차단 성공"으로 셈, 출력 버림 | 복제·파싱 장애가 보호 성공으로 기록 | 기대 시험 이름의 FAIL/ERROR 줄 요구, SyntaxError/ImportError 는 불합격, 로그 보존 |

→ V1 의 PASS 항목(AC-1~4, P11 현재 크기, 새 CI 스텝의 무출력 거부)은 제 실행과 일치했고, FAIL 항목 6건은 전부 재현 가능한 코드 결함이었습니다. "P11 한도를 이 인수 검사가 안 막는다"는 지적은 맞지만 그 검사는 별도 CI 스텝(파일 500줄 게이트)의 몫이라 결함으로 세지 않았습니다.

**수정 후 재실행 (12:20:17)**: `unittest` 25 OK, skip 0 / `acceptance-llm-wiki-fields.sh` VERDICT PASS (변조 6종 전부 기대 시험 실패로 차단) / 운영 dry-run(12:20:43) `to_fill 12932, skipped_invalid 668, skipped_filled 33, written 0`.

### V2 — NOT_RUN (사유 기록)

L3 규칙상 V2 가 필수이나 사장님 2026-09-18 지시("검증 계층을 무한히 쌓지 마라 — 추가 라운드는 삭제·권한·인증·대규모 마이그레이션에만")에 따라 이번 변경(운영 쓰기 0건, 도구·문서·검사기)에는 적용하지 않았다. V1 재현은 제가 로컬에서 6건 전부 같은 방법으로 다시 돌려 확인했다(위 표의 재실행). 운영 쓰기(WU-①)와 anon 차단(WU-⓪)은 권한·개인정보 범주이므로 그 단계에서 V1→V2 를 다시 적용한다.

→ 규약 미달 668건은 전부 `_meta` 외 값이 모두 null 인 "추출 실패 객체"였다(사이트별 내역은 증거 K). 보내지 않는 것이 맞고, 로컬에 그대로 남아 재추출 대상이 된다.

### V1-2 — Codex 적대 검토 (⓪·① 실행 단계, 2026-10-14 13:55→14:04, `/codex:adversarial-review`)

권한 변경·운영 쓰기 단계이므로 독립 검증을 다시 돌렸다(09-18 지시의 "권한·인증·마이그레이션" 범주). 호출은 플러그인 companion(`codex-companion.mjs adversarial-review --background --base origin/main`)이며 v6 워크트리와 v4 워크트리에서 각각 1회. 원문 `private-reviews/llm-wiki/codex-adv-v6-20261014.md`·`codex-adv-v4-20261014.md`(무시 폴더). 두 판정 모두 `Verdict: needs-attention`.

| # | 대상 | 심각도 | 원문 제목(요지) | 원인 | 사업 영향 | 재현 | 조치 |
|---|---|---|---|---|---|---|---|
| 1 | v6 | high | 무효 anon 키도 노출 차단 성공으로 판정 | 401/403 을 원인 구분 없이 0건으로 계수 | 키가 폐기되면 "차단됨"으로 오보고 → 복구 선행 조건을 거짓 충족 | bogus 키 → 7객체 0건 PASS | 키 양성 대조군·`42501` 만 차단·HEAD 무본문은 GET 재조회 (ed6bfc7) |
| 2 | v6 | high | 장부 local_id 일괄 롤백은 다른 주체 데이터 삭제 | `matched=0` 도 `done` 으로 기록, SOT 가 일괄 null 지시 | 되돌리기가 경쟁 쓰기 값을 지움 | 장부 형식으로 확인 | `--rollback` 지문 일치 행만, SOT §5①·§6 1-b (ed6bfc7) |
| 3 | v6 | medium | SOT 필수 필드 검사가 실제로 실행되지 않음 | heredoc 뒤 `</dev/null` 이 stdin 을 덮음 | 정본 행 삭제를 CI 가 못 막음 | `raise` 를 넣어도 PASS | 리다이렉션 수정 + 음성 대조군 3종 (ed6bfc7) |
| 4 | v6 | medium | anon 정본 행 형식 변경이 검사 누락으로 접힘 | 비매칭 행 조용히 건너뜀, 필수 집합 미확인 | 백틱 하나로 객체가 검사에서 빠짐 | 백틱 행 → 6객체 PASS | 표 엄격 파싱 + 필수 7객체 (ed6bfc7) |
| 5 | v4 | high | 외부 B2C 계정이 자료형 뷰 전체 이력을 읽음 | matview 는 RLS 없음 + authenticated grant | 가입만 하면 후보·메일·Notion 이력 전체 열람 | 역할 시뮬레이션 외부 authenticated uchv=34036 | 후속 마이그레이션 authenticated 회수 (88e45deb, 14:05 적용·검증) |
| 6 | v4 | medium | 뷰 재정의 시 `security_invoker` 소실 → anon 재노출 | 옵션 하나에 의존, anon grant 유지 | 누군가 옛 정의로 뷰를 다시 만들면 재노출 | 정적 확인 | 두 뷰 anon grant 회수(두 겹) + SOT §6 1-d |
| 7 | v4 | medium | `candidates` 없는 환경에서 전체 롤백 | legacy 테이블 DDL 이 저장소에 없음 | 다른 환경에서 마이그레이션 전체 실패 | 운영엔 존재, v4 에 로컬 DB 없음 | **수용**: fail-closed 가 부분 적용보다 낫고, 적용된 파일은 바꾸지 않는다 |

→ 제 쪽 과장·오탐은 없었다. 7건 모두 사실이며 1건만 조치 없이 수용했다. 수정 과정에서 운영 실측이 제 1차 수정의 오류 2건(루트 탐침·HEAD 무본문)을 추가로 잡았다(증거 O-2).
