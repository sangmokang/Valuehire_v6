# Codex 실행 프롬프트 — LLM 위키 WU-② 아카이버 동기화에 구조화 칼럼 추가 (2026-10-14)

아래 "프롬프트 본문" 전체를 Codex 에 그대로 준다. 저장소는 **Valuehire_v4**(아카이버 서버가 있는 쪽). 선행 WU-⓪(anon 차단)·WU-①(기존 행 12,9xx 건 채움)은 2026-10-14 에 끝났다. 이 WU 는 **앞으로 새로 저장되는 프로필**이 같은 공백을 다시 만들지 않게 하는 코드 수정이다.

---

## 프롬프트 본문

`/strict` L2. 저장소 `~/Desktop/Valuehire_v4`, origin/main 에서 워크트리 `worktrees/llm-wiki-wu2-archiver-sync`(브랜치 `task/llm-wiki-wu2-archiver-sync`)를 새로 파서 그 안에서만 작업한다. 메인 작업트리는 다른 세션이 쓰고 있으므로 건드리지 않는다. push·PR 은 만들지 말고 로컬 커밋까지만 하고 보고한다.

### 목표 한 줄
로컬 아카이버(`tools/profile-archiver/server/index.js`)가 Supabase `profile_archives` 로 보내는 upsert 에 `structured_json`·`career_companies_json`·`salary_man` 세 칼럼을 포함시켜, 새로 저장되는 프로필의 구조화 결과가 운영에 즉시 반영되게 한다.

### 사실 (직접 확인한 것, 다시 확인해도 됨)
- `tools/profile-archiver/server/index.js:1606-1631` `syncToSupabase(payload)` 의 upsert 객체에 위 세 칼럼이 없다. `rowToSyncPayload(row)`(같은 파일 1636 부근)도 세 값을 payload 에 넣지 않는다. 이것이 운영 `profile_archives.structured_json` 이 2.4%(514/21,651)였던 직접 원인이다.
- 로컬 SQLite `archives` 테이블 칼럼: `structured_json TEXT`, `salary_man INTEGER`, `career_companies_json TEXT`. 운영 `profile_archives` 칼럼: `structured_json text`, `career_companies_json text`, `salary_man integer` (관리 API `information_schema.columns` 2026-10-14 13:57 조회). **둘 다 text 이므로 JSON 파싱 없이 문자열 그대로 보낸다.**
- 로컬 `structured_json` 값 규약(정본 Valuehire_v6 `docs/sot/llm-wiki.md` §2·`scripts/llm_wiki/backfill_structured_profiles.py` `_valid_structured`): JSON 객체이고 `_meta.source`·`_meta.input_hash` 가 비어있지 않은 문자열이며 `_meta` 밖에 null 아닌 값이 1개 이상. 이 규약에 미달하면(로컬 668건이 그렇다 — 내용이 전부 null) **보내지 않고 null 로 둔다**. 
- QA #192 재발 금지: 운영 스키마에 없는 칼럼을 보내면 upsert 가 통째로 실패한다. 세 칼럼은 운영에 존재함을 위에서 확인했으니 그 외 칼럼은 추가하지 않는다.
- 별도 경로 `tools/profile-archiver/recruiter/src/sync-to-supabase.ts`(시험 `__tests__/sync-to-supabase.test.ts`)도 같은 테이블에 쓴다. 이 경로가 세 칼럼을 보내는지 확인하고, 안 보내면 같은 규약으로 같이 고친다. 보내면 손대지 않고 보고에 적는다.
- 시험 러너는 루트 `vitest`(`vitest.config.*` include: `tests/**/*.test.ts`, `tools/**/tests/**/*.test.mjs`). `index.js` 는 express 앱을 바로 띄우는 파일이라 import 하면 서버가 뜬다 → **upsert 객체를 만드는 순수 함수**(예: `buildProfileArchiveUpsertRow(payload)`)를 `tools/profile-archiver/server/lib/` 에 분리해 그것만 시험한다. 분리한 함수를 `syncToSupabase` 가 실제로 호출해야 한다(테스트만 부르는 고아 금지).

### 인수 기준 — 명령·기대값으로만 판정한다
RED 를 먼저 커밋한다(구현 전 아래 시험이 "빠진 동작" 때문에 실패해야 하며 import 오류·문법 오류 실패는 RED 가 아니다).

| ID | 단언(EARS) | 명령 | 기대 |
|---|---|---|---|
| AC-1 | When 로컬 행에 규약을 만족하는 `structured_json` 이 있으면, 시스템은 upsert 행에 `structured_json`(원문 문자열)·`career_companies_json`·`salary_man` 을 포함해야 한다 | `npx vitest run tools/profile-archiver/server/tests/profile-archive-upsert-row.test.mjs` | 통과. 단언: 세 키 존재, `structured_json` 이 입력과 동일 문자열, `salary_man` 이 정수 |
| AC-2 | If `structured_json` 이 `''`·`null`·JSON 아님·`_meta.input_hash` 없음·내용 전부 null 이면, 시스템은 `structured_json: null` 을 보내야 한다(빈 문자열을 text 에 넣지 않는다) | 같은 시험 파일 | 다섯 입력 각각 `null` |
| AC-3 | While 규약 미달이어도 시스템은 나머지 칼럼(`local_id`·`url`·`text_content` …)을 종전과 같이 보내야 한다(동기화 자체를 막지 않는다) | 같은 시험 파일 | 종전 13개 키 전부 존재·값 동일 |
| AC-4 | 시스템은 운영 스키마에 없는 키(`match_*`, `selected_*`, `embedding_*`)를 upsert 행에 넣지 않아야 한다 | 같은 시험 파일 | 키 집합 == 종전 13개 + 신규 3개, 그 외 0 |
| AC-5 | `syncToSupabase` 와 재시도 워커 양쪽이 분리 함수를 호출해야 한다(배선) | `rg -n "buildProfileArchiveUpsertRow" tools/profile-archiver/server/index.js` | 정의 import 1곳 + 호출 ≥1곳. `rg -n "upsert\(\{" tools/profile-archiver/server/index.js` 의 profile_archives 인라인 객체는 0건 |
| AC-6 | 변조: 분리 함수에서 `structured_json` 줄을 지우면 AC-1 시험이 실패해야 한다 | sed 로 사본 변조 후 같은 vitest | FAIL(단언 실패), 원본 복구 후 PASS |
| AC-7 | 라이브 1건: 아카이버 서버(`localhost:7777`)를 재시작한 뒤 로컬에 이미 `structured_json` 이 있고 운영엔 null 인 행 1건을 `sync_status='pending'` 으로 되돌려 재시도 워커가 보내게 하고, 운영에서 service 키 HEAD count 로 `local_id=eq.<그 id>&structured_json=not.is.null` 이 1 인지 읽는다 | curl -I … `Prefer: count=exact` | `content-range: 0-0/1`. 값(개인정보)은 출력하지 않는다. **운영에서 이미 채워진 행을 고르지 말 것**(2026-10-14 WU-① 뒤 대부분 채워져 있음 — `structured_json=is.null` 로 먼저 후보를 센다). 후보가 0건이면 AC-7 은 `BLOCKED` 로 적고 끝낸다 |

counter-AC(가짜 합격): (a) 시험이 분리 함수를 직접 만들어 쓰고 `index.js` 는 옛 인라인 객체 그대로 — AC-5 로 잡는다. (b) `JSON.parse` 해서 객체를 보내 text 칼럼에 `[object Object]` 가 들어감 — AC-1 의 "입력과 동일 문자열" 로 잡는다. (c) 규약 검사를 빼고 `''` 를 그대로 보냄 — AC-2. (d) 전체 재동기화(기존 2만 행 재전송)를 끼워 넣음 — 비범위, 하지 말 것(WU-① 이 이미 채웠고 서버측 `is.null` 보호는 backfill 도구에만 있다).

### 하지 말 것
새 칼럼·새 테이블·마이그레이션, `--no-verify`, 메인 작업트리 수정, 운영 데이터 대량 재전송, 후보자 원문을 로그·문서에 출력, upsert 에 `match_*`/`selected_*` 복원.

### 보고 형식
첫 줄 `VERDICT: PASS|FAIL`. 결론 → 판단 근거 → 증거 원문(명령·시각·종료값·전체 출력). 전문용어는 첫 등장 문장 안에서 풀고, 출력 아래에 `→` 해석 한 줄. AC 표를 PASS/FAIL/BLOCKED 로 채우고, 건너뛴 것·추정은 앞부분에 쓴다. 커밋 SHA 와 워크트리 경로를 적는다. 한국어 존칭체.
