# Codex 적대적 검증 기록

- 갱신: 2026-10-14 14:08 KST · 회차 13. 시각은 변경 컨텍스트 스냅샷 `20261014-140831`에서 가져왔다. 실제 작성 시각은 확인하지 못했다.
- 대상:
  - v4 worktree `Valuehire_v4/worktrees/llm-wiki-anon-lockdown`, 브랜치 `task/llm-wiki-anon-lockdown`, HEAD `88e45deb`. 이 브랜치는 `ac6fae86`에서 출발했고 그 뒤에 `06a65482`와 `88e45deb`가 올라갔다.
  - v6 worktree `Valuehire_v6/worktrees/llm-wiki-field-recovery`, HEAD `f8ce20f`. 커밋 범위는 `ac6184b..f8ce20f`이다.
  - 새 v4 worktree `llm-wiki-wu2-archiver-sync`. HEAD가 `ac6fae86`이고 diff가 비어 있다.
  - v6 `main` @ `3e804be`의 미커밋 문서. 11·12회차와 목록이 같다.
- 판정 요약: P0 1 · P1 7 · P2 16 · P3 4 (열림 기준)
- 실행 증거: 셸이 없어 테스트, `git log`, HTTP 재현을 하지 않았다. 모든 판정은 Read·Grep 결과다.

## Codex 에게 — 지금 할 일 (우선순위 순, 최대 5개)
1. **[CAR-028] `/ai-search-list` 서버 인증 게이트를 넣는다.**
   - `anon-lockdown` 브랜치의 diff는 SQL 4파일뿐이다. 이 페이지는 service key를 쓰므로 DB 잠금은 아무 효과가 없다.
   - DB의 익명 경로를 막은 지금, 인증 없는 후보자 전체 열람 경로로 남은 것은 이 페이지다.
   - 완료 조건:
     - `resolveAuthRedirect("/ai-search-list", null, "admin")` → `/login?next=%2Fai-search-list` 시험이 있다.
     - `shouldRejectByHost("app","/ai-search-list") === true` 시험이 있다.
     - 비로그인 `curl -sI`가 307 또는 404를 반환한다.
2. **[CAR-029] 증거 M-6의 "authenticated(외부) 전부 0"을 정정한다. 후속 마이그레이션 `20261014150000`의 운영 적용 증거를 남긴다.**
   - 완료 조건:
     - 증거 파일에 적용 명령, 시각, `schema_migrations` 행이 있다.
     - 외부 도메인 JWT로 `unified_candidate_history_view`를 읽으면 401/403 또는 `*/0`이 나온다.
3. **[CAR-027/025] 실행 프롬프트 `:30`의 화면 캡처 대조군을 JWT 직접 호출로 바꾼다. AI Search 정본 프롬프트에는 "llm-wiki §5 ⓪ GREEN + CAR-028 GREEN"을 의존 조건으로 적는다.**
4. **[CAR-020/021] main 미추적 `ai-search-admin-v4-performance-and-list-2026-10-14.md`를 정본으로 정하고 §3.7 전용 PR 카드를 추가한다.**
   - 카드에는 501번째 행, `kim_jh`, `100%`, `김민수 토스` RED 시험과 rollback을 넣는다.
5. **[CAR-003] `loader.ts:627`, `:732`의 `return []`에 대한 RED 시험을 먼저 커밋한다.**
   - 완료 조건: 오류 mock에서 "조회 실패"가 렌더되고 "0건"은 렌더되지 않는다.

## 이번 회차 변화
- 신규: **CAR-029**
  - 증거 M-6은 외부 로그인 사용자가 아무것도 읽지 못한다고 단언한다.
  - 같은 날 작성된 다른 두 기록과 후속 마이그레이션 주석은 같은 시점에 그 경로가 열려 있었다고 적는다.
- 해결: 없음
- 부분 진전:
  - **CAR-025**: anon-lockdown 브랜치에 뷰 `security_invoker` 마이그레이션과 rollback이 생겼다.
    - `supabase/migrations/20261014140000_llm_wiki_anon_lockdown.sql`의 4)절
    - `supabase/rollback/20261014140000_llm_wiki_anon_lockdown.down.sql`
    - 후속 `20261014150000_llm_wiki_lockdown_followup.sql:12-14`는 두 뷰의 anon grant를 회수한다.
    - 남은 조건: AI Search 정본 프롬프트에 의존 문장을 넣는 것.
  - **CAR-027**:
    - 실제 증거는 화면 캡처 대신 관리 API로 역할을 흉내 내는 방식(`set local role`)을 썼다(증거 M-3·M-6). 화면 캡처보다 낫다.
    - 하지만 실행 프롬프트 `llm-wiki-field-recovery-exec-prompt-2026-10-14.md:30`은 여전히 "화면 `admin.valuehire.cc/ai-search-list` 1회 실조회 캡처"다.
    - 인계 재확인 문서도 "로그인 JWT를 사용한 실제 사용자 조회 … 확인하지 않았다"고 적는다.
- 유지: CAR-001~016, 019~028 (CAR-018 제외)
- 참고:
  - v6 `llm-wiki-field-recovery` 작업트리 파일은 이미 `f8ce20f`보다 앞서 있다. 미커밋 GREEN 작업으로 보인다.
    - `anon_exposure_audit.py:104`는 `42501` 오류 코드일 때만 차단으로 센다.
    - `docs/sot/llm-wiki.md:77`에는 1-c 조항이 있다.
  - 커밋된 `f8ce20f`의 감사기는 401/403을 모두 0으로 센다(diff `collect`). 그래서 13:53 PASS 증거는 무효 키 hole이 있던 도구로 만든 것이다.
    - 같은 증거의 "profile_archives 200(0행)"은 그때 키가 유효했다는 뜻이므로 결론 자체는 유지된다고 본다(PLAUSIBLE).
    - Codex가 이미 RED로 고정했으므로 새 번호를 주지 않는다.
- 무관 변경:
  - `llm-wiki-wu2-archiver-sync`: diff 없음.
  - v6 `wu2-archiver-sync` 프롬프트, backfill rollback RED 시험: 아카이버·백필 범위이고 리스트 재구축과 파일이 겹치지 않는다.
  - v4 로컬 main의 `.serena`, manifest, `customer-ontology/*`, `.tmp/ai-search-*`: 12회차와 같다.

## 열린 발견 사항

### CAR-028 [P0] `/ai-search-list`가 서버 인증 없이 service key로 후보 전체를 렌더한다 (코드 CONFIRMED @ 88e45deb · HTTP 재현 없음)
- 파일:
  - `88e45deb`: `middleware.ts:337` matcher. `ai-search` Grep 결과 0건이다.
  - `src/lib/supabase.ts:6`, `:9-10`: `createServerSupabaseClient`가 service key를 쓴다.
  - `app/ai-search-list/page.tsx:59`
  - `src/auth/hostType.ts:31-39`, `:47-51`
  - `app/ai-search-list/layout.tsx:7-16`
  - `app/_components/AdminShell.tsx:45-56`
- 문제:
  - 비로그인 GET 요청이 SSR HTML로 후보 이름, 프로필 URL, 평가 요약을 받는다. service key를 쓰므로 RLS도 우회한다. 정본 R-10과 §1.3을 위반한다.
  - 이번 DB 잠금(`20261014140000`, `150000`)은 anon·authenticated 역할에만 걸린다. 이 경로에는 효과가 없다.
  - 같은 파일 `:18-28`에 `getServerPageUser`가 이미 있는데 쓰이지 않는다.
- 재현:
  1. `middleware.ts`에서 `ai-search` Grep → 0건(이번 회차 재확인).
  2. `app/ai-search-list`에서 `getServerPageUser|redirect|requireAdmin|getUser` Grep → 0건(12회차).
  3. 비운영 배포에서 쿠키 없이 `curl -s <host>/ai-search-list | grep -c '<tr'`을 실행한다(미실행).
- 수정 방향:
  - matcher와 `INTERNAL_OPS_PATHS`에 `/ai-search-list`, `/ai-search-list/:path*`를 추가한다.
  - `resolveAuthRedirect` 보호 영역에 이 경로를 넣는다.
  - `page.tsx` 첫 줄에서 `getServerPageUser()`를 호출하고 사용자가 없으면 `redirect`한다.
  - `@valueconnect.kr` 도메인 제한(`middleware.ts:263-269`)이 이 경로에도 적용되는지 확인한다.
- 완료 조건:
  - 위 두 단위 시험이 있다.
  - 외부 도메인 사용자가 이 경로에 오면 `/b2b`로 이동하는 시험이 있다.
  - 비운영 배포에서 비로그인 `curl -sI`가 307 또는 404를 반환한다. 원문 출력을 첨부한다.
  - 운영 노출 기간과 접근 로그 확인 여부를 보고한다.

### CAR-029 [P1] WU-⓪ 증거가 외부 로그인 사용자의 자료형 뷰 열람을 "0"으로 기록했지만 다른 기록과 모순된다. 후속 마이그레이션은 운영 적용 증거가 없다 (모순 CONFIRMED · 운영 상태 PLAUSIBLE)
- 파일:
  - v6 `llm-wiki-field-recovery-evidence-2026-10-14.md` M-6: "authenticated(외부) 전부 0", "정책 … 두 뷰 reloptions"
  - v6 main `llm-wiki-next-handoff-readback-2026-10-14.md`(13:54): "`unified_candidate_history_view`: anon SELECT 없음, authenticated SELECT는 있음"
  - v4 `20261014150000_llm_wiki_lockdown_followup.sql:2-4`: RLS가 없는 materialized view라서 "B2C 가입으로 얻는 authenticated 세션도 … 전체를 직접 읽을 수 있었다"
  - 같은 파일 `:12`: `revoke all … from authenticated`
  - 증거 M-5: 적용 기록에는 `20261014140000`만 있다.
- 문제:
  - materialized view에는 RLS가 없다. authenticated grant가 남아 있으면 외부 도메인 JWT도 34,036행을 읽을 수 있다.
  - 그런데 M-6은 외부 로그인 사용자의 열람을 "전부 0"으로 적고 WU-⓪ GREEN을 선언했다. 역할 시뮬레이션에 이 뷰가 빠졌거나 결과가 틀렸다.
  - 후속 마이그레이션은 커밋됐지만, 운영 적용 명령과 장부 행은 증거에 없다(PLAUSIBLE 미적용).
  - 이 경로가 열려 있으면 AI Search 리스트 재구축의 전제인 "권한 있는 전체 DB"(§3.7, R-10)가 무너진다.
- 재현:
  1. M-6의 "authenticated(외부) 전부 0"과 readback의 "authenticated SELECT는 있음"을 대조한다.
  2. 관리 API로 `select has_table_privilege('authenticated','public.unified_candidate_history_view','SELECT')`를 실행한다(미실행).
- 수정 방향:
  - 증거 M-6 줄을 정정한다. "WU-⓪ GREEN"을 "후속 적용 전 PARTIAL"로 바꾼다.
  - `150000`을 승인 경계 안에서 적용하고 명령, 시각, 장부 행을 기록한다.
  - `anon_exposure_audit.py`에 외부 JWT 모드를 추가하거나 별도 검사를 둔다.
- 완료 조건:
  - 증거에 `20261014150000` 장부 행이 있다.
  - 외부 도메인 JWT 실제 HTTP 호출로 `unified_candidate_history_view`를 읽으면 401/403 또는 `*/0`이다.
  - 같은 호출을 `@valueconnect.kr` 구성원 JWT로 하면 `pipeline_candidates_active`가 `*/N`(N>0)이다.
  - `candidate-timeline` route가 service_role로 계속 동작한다는 확인이 있다(`app/api/admin/candidate-timeline/route.ts:544`).

### CAR-019 [P1] 착수 프롬프트 PR-2가 v4의 exact count 계약과 CI 가드를 어기라고 지시한다 (CONFIRMED)
- 파일:
  - 브랜치 프롬프트 `ai-search-list-v4-rebuild-2026-10-14.md:66`
  - v4 `docs/sot/32-admin-count-spec.md:9`, `:49-50`
  - `tests/adminCountGuard417.test.ts:90-117`
- 문제: `count:"estimated"`는 SOT-32, §1.2, R-04에 어긋난다. Codex 자체 감사도 같은 결론이다.
- 완료 조건: 정본 착수 프롬프트에 `estimated`가 0건이다. PR-2 완료 조건에 "SOT-32 가드 B 통과"가 있다.

### CAR-020 [P1] SOT와 착수 프롬프트가 두 버전으로 갈라졌고, 7컬럼·검색 범위 해석이 반대다 (CONFIRMED)
- 파일:
  - 브랜치 SOT `:3`, `:23`
  - main 미추적 SOT("고정 7컬럼 전체를 삭제하라는 지시로 해석하지 않는다")
  - 브랜치 프롬프트 `:66`, `:70`, `:119`
  - main 미추적 프롬프트 인수 조건 6·7
- 완료 조건: SOT, 정본 사본, 착수 프롬프트가 각각 1개다. 7컬럼 문장이 하나다.

### CAR-021 [P1] 착수 프롬프트에 전체 DB 검색·페이지네이션 PR이 없는데, 관련 CAR를 닫는다고 쓴다 (CONFIRMED)
- 파일: 브랜치 프롬프트 `:13`, 브랜치 SOT `§5:103`, main 미추적 프롬프트 인수 조건 7·작업 순서 4
- 문제: §1.2 S3와 §3.7을 맡는 PR 카드가 없다. 10-07 브리핑 ②가 미충족으로 남는다.
- 완료 조건: 카드에 501번째 행, `kim_jh`, `100%`, `김민수 토스` RED 시험이 있다. 카드가 CAR-002·005·007·009를 닫는다고 명시한다.

### CAR-014 [P1] v4 후보 표가 §3.3 고정 7컬럼을 충족하지 않고, 브랜치 계획도 이를 복원하지 않는다 (CONFIRMED)
- 파일: worktree `AiSearchListTable.tsx:151`(머리글 6개), `page.tsx:8-10`, 브랜치 프롬프트 `:70`, 브랜치 SOT `:23`
- 문제: 서치 일시, 제안 발송, 담당·다음 행동 칸이 없다. 원천 ID만 보여도 시험이 통과한다.
- 완료 조건:
  - 7개 머리글 렌더 시험이 있다.
  - 발송 증거가 없는 fixture에서 `확인 불가`가 표시된다.
  - 이름이 있는 fixture에서 이름이 표시된다는 단언이 있다.

### CAR-002 [P1] 한글 이름 서버 검색 필터가 7~13KB URL을 만든다 (길이 CONFIRMED · 실패 PLAUSIBLE)
- 파일: `_lib/koreanNameSearch.ts:181`, `:196`, `_data/loader.ts:699`
- 완료 조건: 4글자 복성 이름의 요청 길이 상한 시험이 있다. 비운영 Supabase에서 200 응답을 받는다.

### CAR-003 [P1] DB 조회 오류가 빈 목록으로 접힌다 (CONFIRMED @ ac6fae86)
- 파일: `loader.ts:625-628`, `:730-733`(`return []`)
- 문제: §9.2와 R-04를 위반한다. count 경로는 `null`, 목록 경로는 `[]`를 돌려줘 비대칭이다.
- 완료 조건: 오류 mock에서 "조회 실패"가 렌더되고 "0건"은 렌더되지 않는 시험이 RED에서 GREEN으로 바뀐다.

### CAR-025 [P2] 익명 읽기 노출을 막는 게이트가 AI Search 정본 프롬프트에 연결돼 있지 않다 (CONFIRMED · 부분 해결)
- 파일: v4 `20261014140000_llm_wiki_anon_lockdown.sql`, `20261014150000_…followup.sql`, rollback 2개. main 미추적 AI Search 프롬프트에서 `anon|익명|401|403` Grep 결과는 0건이다.
- 진전: 마이그레이션과 rollback이 생겼다(13회차).
- 완료 조건: 정본 프롬프트 선행 게이트에 "llm-wiki SOT §5 ⓪ GREEN(CAR-029 포함)"과 "CAR-028 GREEN"이 있다.

### CAR-027 [P2] llm-wiki WU-⓪의 양성 대조군이 `authenticated` 정책을 증명하지 못한다 (CONFIRMED · 부분 진전)
- 파일: 실행 프롬프트 `llm-wiki-field-recovery-exec-prompt-2026-10-14.md:30`, v4 `src/lib/supabase.ts:9-10`, readback("로그인 JWT … 확인하지 않았다")
- 문제:
  - 프롬프트 문구는 여전히 RLS를 우회하는 화면 캡처를 대조군으로 쓴다.
  - 실제 증거는 역할 시뮬레이션을 썼지만 JWT 기반 HTTP 호출은 아니다. 그리고 CAR-029의 모순을 낳았다.
- 완료 조건: `:30`이 JWT 직접 호출로 바뀌어 있다. 증거에 구성원·외부 JWT 각각의 상태 코드와 content-range가 있다.

### CAR-026 [P2] 브랜치 SOT가 Gmail을 Fleet-job "현재 정본"으로 선언해 R-02·R-03과 충돌한다 (CONFIRMED)
- 파일: 브랜치 SOT `:97`, `:87`, 원문 `ai-search-operations-original-2026-09-30.md:88-89`
- 완료 조건: `현재 정본은 Gmail`이 0건이다. PR-5 시험에 "DB 저장 없는 Gmail 보고는 Fleet 성공 아님" 사례가 있다.

### CAR-001 [P2] Codex 보고 오류: 병합된 브랜치를 "main에 미병합"으로 판정했다 (CONFIRMED)
- 파일: 브랜치 프롬프트 `:19-20`, `.omx/artifacts/claude-ai-search-list-flow-20261014.md:9`
- 완료 조건: `gh pr view 796 --json state,mergeCommit`과 `git diff 5b0bc19d origin/main -- app/ai-search-list | wc -l`(0이어야 한다)의 원문을 첨부한다.

### CAR-016 [P2] 실행 프롬프트의 PR 분할에 rollback과 선행 근거가 없다 (CONFIRMED · 부분 해결)
- 파일: 브랜치 프롬프트 `:51-93`(`rollback|롤백` 0건), main 미추적 프롬프트 작업 순서 6
- 완료 조건: PR 카드마다 rollback 한 줄이 있다. PR-5는 수집, 저장, 화면으로 나뉘어 있고 후보별 결과 값 저장 시험이 있다.

### CAR-022 [P2] `[aisearch]` 제목 구현 보고 메일이 PR-5 수집을 오염시킨다 (모순 CONFIRMED · 오염 PLAUSIBLE)
- 파일: 브랜치 프롬프트 `:119`, `:89`, v6 main `search-query-and-filter-rules.md:43`
- 완료 조건: `:119`가 수정돼 있다. 파서 시험에 "구현·감사 보고 제목은 run 0건" 사례가 2개 이상 있다.

### CAR-023 [P2] profile_url 묶음과 기존 dedupe 때문에 목록 행 단위와 총수 단위가 다르다 (코드 CONFIRMED · 계획 영향 PLAUSIBLE)
- 파일: `loader.ts:536`, `dedupeCandidateRows.ts:20-58`, `loader.ts:656`
- 완료 조건: 같은 profile_url 매칭 3건 fixture에서 1명과 3건이 각각 표시된다(R-06, §3.7).

### CAR-012 [P2] SOT 절 단위 대조 표가 부분적이다 (CONFIRMED · 부분 해결)
- 파일: 브랜치 SOT `§5:99-107`
- 완료 조건: R-01~R-16, §3.3, §3.4, §3.7, §9.2 행마다 상태와 `파일:줄`이 있다. R-10 행은 CAR-028과 CAR-029를 반영한다.

### CAR-013 [P2] "merged_into_local_main=1" 출력과 로컬 main 내용이 모순된다 (PLAUSIBLE)
- 근거: 컨텍스트 log에서 `40d5880b`(#794)는 `00b5f5a7`(#796)보다 아래에 있다.
- 완료 조건: `git merge-base --is-ancestor 00b5f5a7 40d5880b; echo $?`의 원문을 첨부한다.

### CAR-004 [P2] 목록 조회에는 시간 제한이 없고 count에만 있다 (코드 CONFIRMED · 성능 PLAUSIBLE)
- 파일: `loader.ts:624`, `:728`(타임아웃 없음), `:638-641`, `:660-663`(`3_500`)
- 완료 조건: 목록 쿼리 타임아웃이 "조회 실패"로 표시되는 시험이 있다. 비운영 DB의 응답 시간과 실행계획이 기록돼 있다(§9.3).

### CAR-005 [P2] 전체 건수와 목록의 출처 범위가 다르다 (CONFIRMED @ ac6fae86)
- 파일: `loader.ts:656`(`ilike "ai_search%"`), `:723`(`like "ai_search:%"`)
- 완료 조건: `source='ai_search_legacy'` mock에서 count와 목록이 일치하는 시험이 있다(§3.7).

### CAR-006 [P2] "분석 실패"를 status 필드로만 판정한다 (PLAUSIBLE)
- 파일: `loader.ts:769`, `:775`
- 반례 근거: v4 `.tmp/ai-search-dreamtech/ingest.mjs`는 status 없이 `match_score`를 넣고, 숫자가 아니면 `null`로 넣는다(컨텍스트 원문).
- 완료 조건: status 없는 행과 `match_score=0`인 행의 시험이 있다(§3.4, R-04).

### CAR-007 [P2] 검색어 정제가 `%`, `_`, `"`를 삭제한다 (CONFIRMED · §3.7 위반)
- 파일: `loader.ts:690`, `:694`, `:698`
- 완료 조건: `kim_jh`, `100%`, `"a b"`, `김민수 토스` 시험이 있다. 비운영 DB에서 200 응답을 받는다.

### CAR-009 [P2] 출처 필터와 목록이 최신 500건 안에서만 동작한다 (CONFIRMED @ ac6fae86)
- 파일: `page.tsx:59`, `loader.ts:707`, `:728`
- 완료 조건: 501번째 이후 행이 출처 필터와 검색에 걸리는 시험이 있다(§1.2 S3, §3.7).

### CAR-011 [P2] Claude 교차 검토가 Codex의 틀린 전제를 되풀이한 순환 검증이다 (CONFIRMED)
- 파일: `.omx/artifacts/claude-ai-search-list-flow-20261014.md:9`, `:13`, `:17`, `:21`
- 완료 조건: 정정 주석이 들어가 있다.

### CAR-015 [P2] 점수 상태에 "레거시·근거 미확인" 구분이 없다 (CONFIRMED)
- 파일: worktree `loader.ts:74`
- 완료 조건: 근거나 버전이 없는 수치 행이 legacy로 렌더되고, 기본 정렬의 신뢰 점수에서 빠지는 시험이 있다(§3.4).

### CAR-008 [P3] 테스트가 실패 경로를 하나도 다루지 않는다 (CONFIRMED)
- 파일: `tests/aiSearchListFullSearchScoreState.test.ts:60`. 인증 경로 시험도 없다(CAR-028).

### CAR-010 [P3] 정제 후 비는 검색어가 "검색 중"으로 표시되고 화면 필터까지 꺼진다 (CONFIRMED)
- 파일: `page.tsx:56`, `loader.ts:694-695`, `AiSearchListTable.tsx:74`, `:79`, `:97`
- 완료 조건: `?q=,`일 때 "검색 일치" 문구가 없고, count가 비검색 count와 같다.

### CAR-017 [P3] §3.7·§9.2 요구 일부가 실행 계획에 없다 (CONFIRMED · 부분 해결)
- 문제: 401/403/422 구분(§9.2), 수집 불완전 표시(§3.7), 고적합 80점 임의 고정 금지(§3.7)가 실행 계획에 없다.
- 완료 조건: CAR-021 검색 PR의 인수 조건에 위 항목이 들어 있다.

### CAR-024 [P3] 브랜치 SOT의 Gmail 레이블명이 10-13 변경 전 값이다 (CONFIRMED)
- 파일: 브랜치 SOT `:97`(`aisearch`). v6 main `search-query-and-filter-rules.md:43`은 `02aisearch`와 `Label_206388205034958356`이다.
- 완료 조건: `:97`이 `02aisearch`와 레이블 ID로 고쳐져 있다. CAR-026과 함께 처리한다.

## 해결된 발견 사항
- CAR-018 — 6회차에 해결. 브랜치 SOT `:78-87`에 원문이 인용됐고, `:90` REQ-1014-T가 범위를 명시한다.

## 이번 회차에 보지 못한 것
- `20261014150000`의 실제 운영 적용 여부와 `unified_candidate_history_view`의 현재 ACL. CAR-029는 운영 상태에 대해 PLAUSIBLE이다.
- `valuehire_can_read_tenant` 함수 본문. 정의 위치(`20260526010000_phase1_data_lake_schema.sql`, `20260724090000_notion_client_sub_pages.sql`)만 Grep했고 외부 도메인 거부 로직은 Read하지 않았다.
- v6 `llm-wiki-field-recovery` 작업트리의 미커밋 GREEN 변경 전체(`anon_exposure_audit.py:104`, `llm-wiki.md:77`)와 시험 결과.
- CAR-028의 HTTP 재현과 `admin.valuehire.cc` 배포 SHA.
- 다른 최상위 경로(`/market`, `/operations`, `/dev`)의 페이지 단 인증.
- `aiso-sot-20261014` HEAD SHA, 정본 사본 두 개의 SHA-256 일치 여부.
- 테스트 실행과 DB 실측.
- 정본 §4~§8, §10, §12~§15와 R-06·R-07·R-09의 v4 대조.
- `.tmp/ai-search-*` 스크립트가 운영 DB에 실제로 INSERT를 실행했는지(CAR-006 반례 행의 존재 여부).

---
이 파일은 `~/.valuehire-codex-watch` 감시 프로세스가 git 변경을 감지할 때마다 덮어쓴다. 이전 회차 사본: `~/.valuehire-codex-watch/history/`.
