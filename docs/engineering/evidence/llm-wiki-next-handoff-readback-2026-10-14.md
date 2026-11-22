# 다음 작업 인계 전 재확인 — 2026-10-14

조사 시각: 2026-10-14 13:54 KST. 이 세션은 운영 DB에 쓰지 않았다. 이전 사용자 로그 이후 상태가 바뀌어 운영 API와 관리 API를 읽기 전용으로 확인했다. 후보자 원문 및 자격증명은 기록하지 않았다.

## 직접 확인한 결과

- v6 작업트리 `/Users/kangsangmo/Desktop/Valuehire_v6/worktrees/llm-wiki-field-recovery`: 최신 커밋 `fd33340`, 조사 종료 시 `git status --short` 출력 없음. 조사 시작에는 감사기/인수검사 변경이 staged였으나 다른 세션이 조사 중 커밋했다. 이 세션은 해당 파일을 수정하지 않았다.
- v4 작업트리 `/Users/kangsangmo/Desktop/Valuehire_v4/worktrees/llm-wiki-anon-lockdown`: 커밋 `06a65482`, 마이그레이션 `20261014140000_llm_wiki_anon_lockdown.sql`과 down 파일 있음.
- 운영 `supabase_migrations.schema_migrations`에 `version=20261014140000`, `name=llm_wiki_anon_lockdown` 있음. 적용 주체와 승인 기록은 이 조회로 확인하지 못했다.
- 운영 `profile_archives`, `gmail_messages`, `gmail_sync_state`, `candidates`: RLS 활성화. `pipeline_candidates_active`/`archive`: `security_invoker=true`. `unified_candidate_history_view`: anon SELECT 없음, authenticated SELECT는 있음. 따라서 익명 차단 확인과 로그인 사용자 권한 확인은 서로 다른 검사다.
- `profile_archives_local_id_key`: `local_id`의 UNIQUE 인덱스 존재. 기존 goal의 유일 제약 미확인은 해소됨. 서로 다른 수집기가 같은 로컬 ID를 사용하지 않는다는 보장은 별도 확인 필요.

## 운영 HEAD 실측

다음 명령을 현재 v6 작업트리에서 실행했다.

```text
python3 scripts/llm_wiki/anon_exposure_audit.py --env /Users/kangsangmo/Desktop/Valuehire_v4/.env.local
anon profile_archives                 count=0
anon gmail_messages                   count=0
anon gmail_sync_state                 count=0
anon candidates                       count=0
anon pipeline_candidates_active       count=0
anon pipeline_candidates_archive      count=0
anon unified_candidate_history_view   count=0
{"VERDICT": "PASS", "failures": []}
exit_code=0
```

서비스 키 HEAD 별도 확인: `profile_archives` 21,651건, 그중 `structured_json=not.is.null` 514건; `gmail_messages` 35,506건; `candidates` 308건; `pipeline_candidates_active` 21,771건. 서비스 조회 경로의 건수 유지가 확인됐다. 로그인 JWT를 사용한 실제 사용자 조회 및 화면 동작은 확인하지 않았다.

## 시험과 남은 한계

```text
python3 -m unittest scripts.llm_wiki.test_anon_exposure scripts.llm_wiki.test_backfill_structured_profiles scripts.llm_wiki.test_field_audit
Ran 36 tests in 0.054s
OK
exit_code=0
```

시험 중 가짜 HTTPError 객체의 ResourceWarning은 있었다. 이번 세션은 전체 변조 인수검사를 재실행하지 않았다. 36건은 도구의 단위 계약을 확인하며 운영 권한·실제 PATCH·전체 Wiki 완료를 증명하지 않는다.

v4 `syncToSupabase`/`rowToSyncPayload` 경로에서 구조화 데이터 전송 누락이 여전히 확인됐다. v6 최신 dry-run 증거는 `to_fill=12932`, `skipped_invalid=668`, `skipped_filled=33`, `written=0`이다. 기존 실행 프롬프트의 13,600건, 표본 장부 10줄, local_id만 이용하는 일괄 null 복원은 최신 장부 규약과 안전한 복원 요건에 맞게 고쳐야 한다.
