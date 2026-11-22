# 인계 프롬프트 — 익명 차단 검증 마무리 → 동기화 보강 → 표본 복구

기존 LLM Wiki 필드 복구 작업을 이어받아라. 이번 목표는 **운영 권한 변경의 검증을 마무리하고, 구조화 프로필이 계속 누락되는 동기화 경로를 고친 뒤, 보호 조건과 복원 절차를 갖춘 소량 표본 복구까지 검증하는 것**이다. 승인된 범위와 기록을 확인한 다음 전량 복구를 진행한다. 제품 조회 화면·Gmail 사건 연결·LLM 요약은 이 단계 완료 이후 별도 작업이다.

## 1. 작업 위치와 현재 근거

- v6: `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/llm-wiki-field-recovery`, 현재 확인 HEAD `fd33340`.
- v4: `/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/llm-wiki-anon-lockdown`, 현재 확인 HEAD `06a65482`.
- 운영 환경 파일: `/Users/kangsangmo/Desktop/Valuehire_v4/.env.local`. 값은 출력하지 말 것.
- 원천 SQLite: `/Users/kangsangmo/Desktop/Valuehire_v4/tools/profile-archiver/server/data/archive.db`.
- 정본: v6 `docs/sot/llm-wiki.md`.
- 기존 goal·검증: `docs/engineering/llm-wiki-field-recovery-goal-2026-10-14.md`, `docs/engineering/evidence/llm-wiki-field-recovery-evidence-2026-10-14.md`.
- 최신 재확인: `/Users/kangsangmo/Desktop/Valuehire_v6/docs/engineering/evidence/llm-wiki-next-handoff-readback-2026-10-14.md`.

착수 때 HEAD·미커밋 변경·다른 세션의 진행을 다시 확인하라. 작업트리가 다른 세션에서 사용 중이면 별도 작업트리를 만들고 해당 커밋을 기준으로 진행하라. 다른 세션의 변경을 revert하거나 같은 파일에 동시 작성하지 말 것.

**2026-10-14 13:54 KST 직접 확인:** 운영 마이그레이션 장부에 `20261014140000/llm_wiki_anon_lockdown`이 있으며 대상 7개 객체의 익명 HEAD는 모두 0건이다. 서비스 키로 프로필 21,651건, 구조화 값 non-null 514건, Gmail 35,506건, 별도 candidates 308건, 활성 후보자 21,771건이 조회됐다. `profile_archives.local_id` UNIQUE 인덱스도 확인됐다. 36개 단위시험은 통과했지만 로그인 JWT·사용자 화면·운영 PATCH·전량 복구는 이 증거에 포함되지 않는다.

## 2. 다음 작업 A — WU-⓪ 완료를 증명

마이그레이션을 다시 적용하기 전에 현재 상태와 적용 기록을 대조하라. 적용·승인·롤백 트랜잭션 검증·V1/V2 결과가 다른 세션에 이미 있으면 재사용하고, 없는 증거만 보완하라. 예전 goal의 “운영 쓰기 0건” 또는 “차단 미적용” 단언은 상태별로 갱신해야 한다. 승인 여부는 실제 지시/기록으로 확인하며 적용됐다는 사실만으로 승인을 추정하지 않는다.

다음 검사를 실행하고 명령·시각·종료값을 기록하라.

```bash
cd /Users/kangsangmo/Desktop/Valuehire_v6/worktrees/llm-wiki-field-recovery
python3 -m unittest scripts.llm_wiki.test_anon_exposure scripts.llm_wiki.test_backfill_structured_profiles scripts.llm_wiki.test_field_audit
bash scripts/acceptance-llm-wiki-fields.sh
python3 scripts/llm_wiki/anon_exposure_audit.py --env /Users/kangsangmo/Desktop/Valuehire_v4/.env.local
```

현재 36건·skip 0, 변조 8종은 기존 검사 기준이다. 결과를 개선할 때는 새 시험 건수를 같이 올리고, 문법/import 오류를 변조 차단으로 인정하지 않는다. 보안 범위는 다음 7개 모두다: `profile_archives`, `gmail_messages`, `gmail_sync_state`, `candidates`, `pipeline_candidates_active`, `pipeline_candidates_archive`, `unified_candidate_history_view`.

비로그인 요청뿐 아니라 승인된 팀원의 JWT, 권한 없는 로그인 사용자의 JWT, 서비스 역할로 읽기 결과를 대조하라. 특히 `unified_candidate_history_view`는 materialized view이며 현재 authenticated SELECT가 유지돼 있다. 팀 밖 로그인 사용자의 읽기가 차단되는지 별도로 확인하라. `profile_archives`/구 `candidates`의 고정 테넌트 정책도 현재 데이터 소유권과 일치하는지 확인한다. 민감 원문은 출력하지 않고 접근 가능 여부와 건수만 기록한다. 테스트 계정이 없으면 해당 항목은 NOT_RUN으로 남기고 전체 권한 검증 PASS라고 쓰지 않는다.

`admin.valuehire.cc/ai-search-list`와 프로필 아카이버/Gmail 수집 서비스 경로가 정상인지 필요한 실제 조회만 확인하라. 알려진 관련 뷰·RPC·API 우회 경로를 점검하고 7객체 HEAD 통과를 전체 DB 안전 판정으로 확대하지 않는다. 운영 down은 이전 익명 노출을 되살리므로 검증용으로 운영에서 실행하지 말 것. 원래 요청 범위를 벗어나는 권한 변경은 구체적 변경안·영향·롤백을 먼저 만들고 기존 승인 범위를 확인한다.

## 3. 다음 작업 B — WU-② 동기화 누락 보강을 먼저 준비

v4 `tools/profile-archiver/server/index.js`의 `rowToSyncPayload → syncToSupabase`가 `structured_json`, `career_companies_json`, `salary_man`을 실제로 전달하는지 확인하고 누락을 고쳐라. 이 작업을 복구 전에 준비해 같은 공백이 계속 쌓이지 않게 한다. 원천 아카이버 프로세스가 어느 작업트리/파일을 실행하는지도 확인한다. 배포하지 않은 브랜치 변경을 운영 동기화 수정 완료라고 부르지 않는다.

최소 회귀시험: 유효한 JSON은 DB 타입에 맞게 전달되고, 비정상 JSON·빈 문자열은 jsonb로 전송되지 않으며, 신규 저장/재시도 양쪽이 같은 매핑을 사용한다. 재동기화 시 로컬 빈 값이 이미 채워진 운영 구조화 값을 NULL로 덮어쓰지 않아야 한다. 단순한 “세 키 존재” 시험만으로 끝내지 말 것. 기존 onConflict·스키마 허용 컬럼·동기화 성공 판정도 유지한다. 더 큰 저장 구조를 새로 만들지 않는다.

## 4. 다음 작업 C — WU-① 복구 도구의 남은 위험을 고치고 dry-run

다음 사항을 작은 변경과 회귀시험으로 확인하라.

- **표본 limit:** 현재 `--limit`은 로컬 입력을 먼저 잘라 유효·미채움 계획이 10건보다 적을 수 있다. “표본 실제 쓰기 10건”이면 검증된 계획에 제한을 적용하는지 명확히 정하고 시험한다. 임의로 기대값을 바꾸어 통과시키지 않는다.
- **매치 수:** 원격 대상은 PK와 `local_id`로 정확히 식별한다. 0매치는 다른 작성자의 선행 채움으로 확인·보고하고, 2행 이상은 즉시 실패한다. UNIQUE 인덱스 확인을 증거에 반영하되 원천 ID 충돌 가능성은 URL/site 교차 확인으로 걸러낸다.
- **안전한 복원:** 장부의 local_id 전체를 무조건 NULL로 만드는 방법을 폐기한다. 실행 ID·대상 PK·쓰기 전 상태·기록한 값의 canonical JSON 해시·시각·처리 상태를 개인 장부에 남긴다. 현재 값이 이번 실행의 기록 값과 동일할 때만 원래 NULL로 조건부 복원한다. 후속 변경은 보류하고 경합을 보고한다. 값 확인과 복원 쓰기 사이 경합도 서버 조건으로 보호한다.
- **장부·재시작:** 쓰기 전에 intent를 기록하고 완료/오류를 남긴다. intent만 남은 행은 readback으로 현재 값과 해시를 확인한다. 기존 JSONL 규약은 intent→done/error 2줄이며 표본 10건 성공 시 기본 20줄이다. `cut`으로 local_id를 추출하지 말고 JSON 파서로 실행 ID/phase/matched를 읽는다. 장부는 repo 밖에 보관한다.
- **유효성:** `_meta` 존재와 non-null만으로 빈 객체/빈 배열/빈 문자열을 유효 프로필로 인정하지 않는지 확인한다. 내용이 실제로 있는 행만 계획에 넣고 불확실한 행은 제외 사유를 남긴다. 구조가 유효해도 사실 정확성이 자동 증명되는 것은 아니므로 표본의 원천 대조를 포함한다.

기존 최신 dry-run은 `to_fill=12932`, `skipped_invalid=668`, `skipped_filled=33`, `written=0`이다. 13,600건이라는 이전 숫자로 강제하지 말고 현재 계획을 재집계하라. non-null 514건에 12,932건이 추가된다고 가정하면 13,446/21,651, 약 **62.1%**다. 목표 65%를 맞추려고 빈 내용을 채우지 않는다.

```bash
python3 scripts/llm_wiki/backfill_structured_profiles.py \
  --db /Users/kangsangmo/Desktop/Valuehire_v4/tools/profile-archiver/server/data/archive.db \
  --env /Users/kangsangmo/Desktop/Valuehire_v4/.env.local
```

dry-run은 운영 쓰기 0건이어야 한다. 원격 absent·이미 채움·무효 원천·ID 충돌·동시 채움·HTTP 오류·응답 유실·후속 수정 복원 거부를 검사하라. 실제 읽기/쓰기/복원 흐름은 로컬 또는 격리 DB에서 검증하고, 민감 데이터가 담긴 장부는 커밋하지 않는다.

## 5. 표본 → 전량 복구의 통과 조건

보안 검증과 운영 쓰기 승인이 확인되면 명시적 실행 ID의 별도 장부로 유효 계획 중 10건만 적용한다. 실제 PATCH 매치 10건과 원문 대조·readback을 확인하고 동일 표본 재실행 쓰기 0건을 확인한다. 오류·경합·의심 연결이 있으면 전량으로 넘어가지 않는다. 승인 기록이 없으면 완료된 코드·dry-run·표본 계획·영향/복원안을 제시하고 운영 쓰기 승인만 확인한다.

표본 통과 후 승인된 범위에서만 전량 적용한다. 이미 채워진 행을 건너뛰며 계획 변동과 실제 쓰기 수를 구분한다. 전후 건수·유효 내용 비율·무효 제외·원천별 분포·재실행 쓰기 0건을 기록한다. 퇴행 하한은 측정 근거로 상향하고 목표 달성과 구분한다.

## 6. 이번 작업 이후

WU-⓪/②/①이 증명된 다음에는 **후보자 상세 하나에서 원천 근거와 이력이 조회되는 수직 구현**을 다음 goal로 제안하라. Gmail `gmail_derived_events`의 후보자·포지션 연결과 미연결 검토 큐부터 작은 범위로 설계하고, ClickUp 미러의 단계 변경 이벤트 기록을 이어 붙인다. 구조화 프로필 채움률 상승은 검색·이력·LLM Wiki 완료를 뜻하지 않는다. 10만 명 성능·Discord·LLM 요약은 실제 목록/관계 조회가 동작한 뒤 검증할 별도 범위다.

## 인계 산출물과 종료 조건

현재 권한 상태·운영 적용 기록, 필요한 범위의 독립 검증, 동기화 누락 수정과 시험, 안전한 복원/재시작 계약, 최신 dry-run과 표본 결과, 전량 적용 여부와 정확한 잔여 항목을 남긴다. 기존 goal·SOT·실행 프롬프트의 오래된 수치/명령은 같은 변경에서 바로잡는다. main에 다른 작업 변경을 섞지 말고 해당 작업의 diff만 보고한다. 현재 작업 승인 범위를 다시 묻지 말고 이미 승인된 부분을 계속하되 확인되지 않은 운영 쓰기는 실행하지 않는다.
