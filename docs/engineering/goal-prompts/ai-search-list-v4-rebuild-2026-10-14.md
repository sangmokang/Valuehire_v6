# 착수 프롬프트 — v4 AI Search 리스트 개선 + /admin 속도 (2026-10-14)

> 이 파일 전체를 Codex 또는 Claude Code 에 붙여 넣는다. 작업 저장소는 **Valuehire_v4**, 요구 정본은 **Valuehire_v6 `docs/sot/ai-search-operations.md`** 이다.

---

## 0. 역할과 정본

당신은 `/Users/kangsangmo/Desktop/Valuehire_v4`(운영 `admin.valuehire.cc`)를 고치는 구현자다.

- **요구 정본:** `/Users/kangsangmo/Desktop/Valuehire_v6/docs/sot/ai-search-operations.md`. 이 브랜치가 아직 병합되지 않았다면 `git -C /Users/kangsangmo/Desktop/Valuehire_v6 show origin/task/aiso-sot-20261014:docs/sot/ai-search-operations.md`로 읽는다. 먼저 §4 REQ-1014(오늘 지시 원문)를 읽고, 다음으로 §2 REQ-0930 규칙 R-01~R-16과 §3.3·§3.4·§3.7을 읽는다. 9/30 원문 전체가 필요하면 `docs/engineering/ai-search-operations-sot-v1-original-2026-09-30.md`를 본다.
- 요구와 이 프롬프트가 다르면 **요구 정본이 이긴다**. 판정과 커밋 메시지에는 요구 ID(REQ-1014-C1 등)를 붙인다.
- 독립 검증 기록 `/Users/kangsangmo/Desktop/Valuehire_v6/docs/reviews/codex-adversarial-review.md`의 CAR-002·003·004·005·007은 이 작업 범위에 겹친다. 해당 PR에서 함께 닫고, PR 본문에 "CAR-xxx 해결"을 적는다.

## 1. 착수 전 0단계 (5분 이내, 불일치하면 멈추고 보고)

```bash
cd /Users/kangsangmo/Desktop/Valuehire_v4
git fetch origin && git log -1 --oneline origin/main          # 기준선. 로컬 main 은 뒤처져 있다 — 로컬 main 을 기준으로 쓰지 마라
git diff 5b0bc19d origin/main -- app/ai-search-list | wc -l   # 0 이어야 함 (PR #796 은 squash 병합됨)
gh pr list --repo sangmokang/valuehire_v4 --state open --limit 30   # 같은 파일을 만지는 열린 PR 확인
herdr pane list | rg -o '"terminal_title":"[^"]*Valuehire_v4[^"]*"'  # 동시에 v4 를 만지는 세션 확인
```

- 다른 세션이 `admin.valuehire.cc 전면 리팩토링 분석`을 v4에서 진행 중일 수 있다. 같은 파일을 고치는 열린 PR이나 세션이 있으면 착수하지 말고 사장님께 한 줄로 보고한다.
- 모든 작업은 `origin/main`에서 딴 **worktree 하나 = PR 하나**로 한다. 메인 checkout(`~/Desktop/Valuehire_v4`)의 미커밋 파일은 건드리지 않는다. reset·stash·checkout 금지.
- 이름은 `../Valuehire_v4-wt-<짧은이름>`, 브랜치는 `task/<짧은이름>`으로 한다.

## 2. 이미 확인된 사실 (2026-10-14 조사, 파일:줄은 origin/main 기준 — 다시 확인하되 처음부터 재조사하지 마라)

**속도**
- F1 `app/ai-search-list/page.tsx:58-61`의 `Promise.all`이 **숨겨진 탭**용 `loadClickUpViz()`와 `loadFleetJobs()`까지 기다린다. `fetchClickUpTasks`(`app/weekly/_lib/weeklyLiveKpi.ts:232-248`)는 최대 80페이지를 순차로 받고, `cache: "no-store"`이며 타임아웃이 없다.
- F2 목록 조회(`loader.ts:614`, `:718`)는 `ai_assessment`·`resume_data` 전체를 최대 1,000행 읽는다. 타임아웃 없이 그 결과를 클라이언트 컴포넌트에 그대로 넘긴다(RSC 페이로드가 큼). 타임아웃은 count에만 있다(3.5초).
- F3 `app/ai-search-list`·`app/kanban`·`app/weekly`에는 `loading.tsx`가 없다. 존재하는 것은 `app/(admin)/admin/loading.tsx` 하나뿐이다.
- F4 `/admin` 홈(`app/(admin)/admin/page.tsx:598-627`)은 요청마다 `count:"exact"` 11~12회와 160행 조회 2회를 실행하고, 캐시가 없다. tenant 조회가 실패하면 tenant 없이 순차로 재시도한다(`:182-186`). 상한은 6초다.
- F5 `(admin)/admin/layout.tsx`와 `AdminShell`이 서로 다른 트리라서, 이동할 때마다 사이드바가 다시 마운트된다. 이동 1회에 `whoami` 2~3회와 `auth.getUser()` 1~2회가 발생한다(`AdminShell.tsx:45-77`, `NavBar.tsx:35-66`, `layout.tsx:49-62`). 관리자 호스트에서도 `NavBar`가 CSS로만 숨겨진 채 렌더된다.
- F6 기존 측정 도구: `e2e/admin-navigation-performance.spec.ts`(+ `src/admin/adminNavigationPerformance.ts`, `docs/engineering/admin-nav-perf-v1-verdict-2026-07-25.txt`). **새 측정 프레임워크를 만들지 말고 이것을 쓴다.**

**화면 데이터**
- D1 이름: `loader.ts:754-757`의 우선순위는 `ai_assessment.candidate_name` → `name` → `"(이름 없음)"`이다. `bridge-aisearch.mjs:114-129`·`enrich-aisearch.mjs:171-183`은 `name`에 `"[미분석] 사람인 rNo=…"` 같은 **라벨**을 넣고 `candidate_name`을 비워 둔다. `run.mjs:130`은 빈 문자열을 쓴다. ChatGPT parser는 null을 허용한다.
- D2 점수 출처: 누가·모델·언제를 표준 키로 저장하는 writer가 **없다**. 예외는 calibration(`calibration.ts:152-159`, `model`·`ran_at`) 하나다. ChatGPT writer는 `generated_by:"ai_search"`로 출처를 숨긴다(`db-writer.ts:116-127`). `sourcing_results`에는 출처 칼럼이 없다.
- D3 프로필: `ResumeData.education`은 `{title, meta, detail}` 자유 텍스트이고, 부서 필드가 어디에도 없다. 경력 `period`는 `"YYYY.MM ~ YYYY.MM"`이다. ChatGPT push의 `education_periods`·`career_periods`는 loader가 select하지 않는다. 현재 렌더러는 `AiSearchListTable.tsx:385-441`이다.
- D4 근거: 리스트 셀(`AiSearchListTable.tsx:443-516`)이 이미 요약과 강점 전부를 보여 준다. 상세 드로어(`app/_components/CandidateResumeDrawer.tsx`)에는 근거·점수·출처가 하나도 없다. 별도 후보 상세 페이지는 없다.
- D5 매칭: 후보×포지션이 행 하나씩이다. `dedupeCandidateRows`(`src/lib/aiSearch/dedupeCandidateRows.ts:20-58`)가 대표 행 하나만 남기고 **다른 포지션은 조용히 버린다**.

**Fleet-job / Gmail**
- G1 Fleet 탭은 Discord 봇 작업 큐 `public.jobs`를 보여 준다(`fleetLoader.ts:26-42`). AI Search 실행 기록이 아니다.
- G2 `gmail_messages`(unique `(tenant_id, source_member_email, gmail_message_id)`)와 리더 `tools/gmail-sync/pull-inbox-full.mjs`(`gmail.readonly`, `--query`/`--label-id`)가 이미 있다. 매시간 launchd(`hourly-hook.mjs`)가 돌지만 `subject:"[추천]"`만 가져온다. **`[aisearch]` 메일은 수집되지 않는다.**
- G3 aisearch 메일: 제목은 `[aisearch]<claudecode|codex> [<태그>] <회사> <직무> — 추천 a·조건부 b (...)` 형식이다. 레이블은 2026-10-13부터 `02aisearch`(`Label_206388205034958356`, 필터 `subject:aisearch`)다. 본문은 실행마다 다른 HTML이고 run id가 없다. 본문에는 후보자 이름·이메일·URL이 있다. v6 `artifacts/search-*/ledger/mail_log.jsonl`(약 123건)에 `message_id`·`jd`가 남아 있다.

## 3. 작업 단위 — PR 5개, 순서대로, 한 번에 하나 (R-16)

각 PR은 **RED 시험 커밋 → 최소 구현 GREEN → 아래 검증 → PR → CI 초록**으로 끝낸다. 병합은 사장님이 한다(auto-merge 금지).

### PR-1 `/ai-search-list` 첫 화면 속도 (REQ-1014-P, CAR-003·004)
- 숨겨진 탭(ClickUp·Fleet)을 첫 화면의 필수 경로에서 뺀다. 방법은 탭을 열 때 불러오기 또는 탭별 `<Suspense>` 중 하나를 고른다. ClickUp 조회에 타임아웃과 짧은 캐시(revalidate 60~300초)를 둔다.
- 목록 select에서 `resume_data`와 큰 JSON을 뺀다. 화면에 필요한 칼럼만 가져오고, 이력서 원문은 드로어를 열 때 불러온다.
- 목록 조회에도 타임아웃을 둔다. DB 오류나 타임아웃은 **"조회 실패" 상태로 화면에 표시**한다(지금은 `return []` → "0건"으로 보인다. R-04). 
- `app/ai-search-list/loading.tsx`를 추가한다.
- 완료 조건:
  - `npx vitest run tests/aiSearchList*` 초록이고, 새 시험 2개를 포함한다. (a) supabase mock이 `{error}`를 돌려주면 "조회 실패" 문구가 렌더되고 "0건"은 렌더되지 않는다. (b) 목록 쿼리의 select 문자열에 `resume_data`가 없다.
  - 수정 전 코드에서 (a)·(b)가 RED인 커밋 SHA를 PR 본문에 적는다.
  - 속도 측정 전후 값은 F6 스펙으로 잰다. 로그인 세션이 필요하면 사장님께 "측정 불가 — 로그인 필요"로 보고하고, 숫자를 지어내지 않는다. 대신 로컬 `next build && next start`에서 RSC 응답 크기 전후 값(바이트)을 잰다.

### PR-2 `/admin` 홈·관리자 이동 속도 (REQ-1014-P)
- 홈 카드 count를 `count:"estimated"` 또는 `unstable_cache`(60~300초)로 바꾼다. tenant 없는 순차 재시도는 칼럼 유무를 미리 알아서 없앤다(F4).
- 관리자 호스트에서 `AppChrome/NavBar`를 렌더하지 않는다. `whoami`·`getUser`는 이동 1회당 1회 이하로 줄인다(F5). 레이아웃 통합이 크면 이 PR에서는 중복 호출 제거만 하고, 통합은 별도 이슈로 남긴다.
- 완료 조건: 이동 1회의 `whoami` 호출 수를 시험 또는 e2e로 1 이하로 고정한다. 카드 숫자는 "추정치" 표기 여부를 화면에 명시한다(정확한 수처럼 보이게 하지 않는다).

### PR-3 리스트 4개 컬럼 (REQ-1014-C1·C3·C4·C5) — 표시 계층만, DB 변경 없음
- **C1 후보자:** 표시 이름 규칙을 이 순서로 한다. `candidate_name` → 라벨이 아닌 `name` → `원천 ID`(예: `사람인 rNo=123`). `"[미분석] … rNo=…"` 같은 라벨 문자열은 이름으로 쓰지 않는다. 실명을 지어내지 않는다. writer 수정(bridge·enrich·run.mjs가 `candidate_name`을 채우도록)은 같은 PR에서 하되, 기존 행 백필은 하지 않는다.
- **C3 프로필:** `대학교, 전공(YY.MM~YY.MM)` 1줄 + 최근 경력 최대 3줄 `회사 부서 직책 YY.MM~YY.MM`을 **최신순**으로 보여 준다. `YYYY.MM` → `YY.MM` 포매터를 둔다. 부서 필드가 없으면 생략한다(지어내지 않음). 기간이 없으면 `기간 미확인`으로 표시한다. loader가 `education_periods`·`career_periods`가 있으면 쓴다(D3).
- **C4 왜 잘 맞는지:** 리스트에는 불릿 최대 3개(각 70자 이내, 확인 필요 1개 60자 이내. REQ-0930 §3.3 ⑤)만 보여 준다. 상세 드로어에 요약·강점 전부·reasons·gaps·weaknesses·점수를 **풍부하게** 옮긴다(D4). 원문은 잘라서 저장하지 않는다.
- **C5 매칭:** `회사-포지션` 표기는 유지한다. 같은 후보의 다른 포지션을 버리지 말고 묶는다(D5). 최신순으로 2개까지 보여 주고, 나머지는 `+N 더 보기`로 접는다. 드로어에서는 전체 목록을 보여 준다.
- 완료 조건(각각 RED → GREEN):
  - 라벨 이름 행이 원천 ID로 표시된다.
  - `2019.03 ~ 2023.02`가 `19.03~23.02`로 표시되고, 경력 4개 입력 시 최신 3개만 최신순으로 나온다.
  - 같은 profile_url의 3개 포지션 행이 한 행 + `+1 더 보기`로 나오고, 드로어에 3개가 모두 있다.
  - 리스트 불릿이 3개를 넘지 않는다.
  - REQ-0930 §3.5에 따라 1024px 이하에서도 후보자·포지션 칸이 남는지 e2e 또는 컴포넌트 시험으로 확인한다.

### PR-4 점수 출처 (REQ-1014-C2)
- 표시를 먼저 한다. 점수 옆에 `평가자 · 모델 · YY.MM.DD`를 표시한다. 키가 없으면 **`평가자 미기록`**으로 표시하고, 과거 점수의 출처를 추정하지 않는다(R-04). calibration이 있는 행은 `claude-haiku-4-5-20251001 · ran_at`을 쓴다.
- 저장 계약: `ai_assessment.score_provenance = {scorer: "chatgpt"|"claude"|"gemini"|"codex"|..., model_id, scored_at(ISO), score_version}`. 이 계약을 모든 점수 writer(D2 표의 ChatGPT match·enrich·register·position-cards·multiengine)에 넣는다. ChatGPT writer의 `generated_by:"ai_search"` 숨김을 실제 값으로 바꾼다.
- `sourcing_results`에 칼럼을 추가하는 것은 **운영 DB 마이그레이션이므로 멈추고 사장님 승인을 받는다**. 승인 전에는 `ai_assessment` JSON 키만 쓴다.
- 완료 조건: writer마다 저장 페이로드에 4개 키가 있는지 시험한다. 키가 없는 행은 `평가자 미기록`으로 렌더되는지 시험한다. 점수 계산식·가중치는 바꾸지 않는다(R-12).

### PR-5 Fleet-job = Gmail aisearch 실행 기록 (REQ-1014-F)
- 수집: 기존 `pull-inbox-full.mjs`를 재사용해 `hourly-hook.mjs`의 `HOURLY_CHILDREN`에 `--label-id Label_206388205034958356`(또는 `--query 'subject:"[aisearch]" newer_than:3d'`) 자식을 추가한다. 리더 토큰은 `gmail.readonly`를 쓴다(발송 토큰 금지). 착수 전에 리더 계정(`GMAIL_MEMBER_EMAIL`)이 aisearch 메일을 받는 계정인지 확인한다. 아니면 멈추고 보고한다.
- 저장: 원문은 `gmail_messages`(기존 unique 키로 중복 방지, R-07)에 둔다. 제목에서 파생한 `aisearch_runs` 뷰(또는 최소 테이블)를 둔다. 칼럼은 `gmail_message_id, thread_id, engine, company, position, tag, count_recommend, count_conditional, sent_at`이다. 뷰나 테이블 생성도 **운영 DB 마이그레이션이므로 승인 후 적용**한다. SQL 파일과 시험은 승인 전에 작성해도 된다.
- 화면: Fleet 탭에 `loadAisearchMailRuns()`를 추가한다. **제목 파생 칼럼만** select하고, `body_text`는 select하거나 렌더하지 않는다(후보 개인정보. R-10). 행에는 엔진·회사-포지션·추천 a/조건부 b·발송 시각·Gmail 스레드 링크를 둔다. 기존 `jobs` 행과는 출처 배지로 구분한다. 오류는 "조회 실패"로 표시한다(빈 화면 금지).
- 백필: v6 `artifacts/search-*/ledger/mail_log.jsonl`의 `message_id`·`jd`는 대조용으로만 쓴다. 과거 메일 일괄 수집은 사장님 승인 후에 한다.
- 완료 조건: 제목 파서 시험(엔진·회사·직무·카운트 추출, 카운트가 없는 제목은 null), 같은 메일을 두 번 넣어도 1행인지 확인하는 시험, Fleet 로더 select 문자열에 `body_text`가 없는지 확인하는 시험을 둔다.

## 4. 공통 검증 — 짧게, 한 바퀴

```bash
npm run typecheck            # 출력 마지막 줄 그대로 보고
npx vitest run <바뀐 시험 파일들>   # passed/failed 숫자 그대로
npm test                     # 전체. 실패가 기존부터 있던 것이면 origin/main 에서 같은 실패를 재현해 구분
npm run build                # PR-1·PR-2 는 필수
```

- 적대 검증은 PR마다 1회만 한다. "이 변경이 거짓 GREEN일 반례 3개"를 직접 실행해 보고, 재현된 것만 고친다. 검증을 검증하는 층을 더 쌓지 않는다.
- `next.config.ts`의 `typescript.ignoreBuildErrors: true` 때문에 build가 초록이어도 타입 오류가 숨는다. `npm run typecheck`를 따로 반드시 돌린다.

## 5. 금지

- 운영 DB 쓰기·마이그레이션 적용·백필·배포·병합·실메일 발송은 사장님 승인 없이 하지 않는다. SQL 파일 작성과 로컬 시험은 해도 된다.
- 점수 계산식·가중치 변경(R-12), 신규 인프라(검색엔진·벡터DB 등), 전면 디자인 교체, 무관한 리팩터링을 하지 않는다(R-16).
- 측정 없이 "빨라졌다"고 쓰지 않는다. 측정할 수 없으면 "측정 불가"와 그 이유를 쓴다.
- 비밀값·후보자 개인정보를 커밋·PR 본문·로그에 쓰지 않는다.

## 6. 보고 형식 (PR 하나마다, 한국어 존댓말)

1. 상태 한 줄: 무엇을 했고 PR 번호·CI 결과가 무엇인지.
2. 숫자: RED SHA, 시험 passed/failed, typecheck 결과, 측정 전후 값(또는 "측정 불가 + 이유").
3. 결정이 필요한 것 1~2개만(예: 마이그레이션 승인), "네"로 답할 수 있는 권고와 함께.
4. 보고서 사본은 `[aisearch]codex`(또는 `[aisearch]claudecode`) 제목으로 사장님 메일에 보낸다.
