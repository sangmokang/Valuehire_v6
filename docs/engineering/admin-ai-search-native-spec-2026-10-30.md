# AI Search 주간 운영표 — 실제 관리자 통합 명세

Issue [#142](https://github.com/sangmokang/Valuehire_v6/issues/142), 기존 Draft PR
[#140](https://github.com/sangmokang/Valuehire_v6/pull/140)를 이어받는다. 최초 HEAD는 f0156e0다.
[현재 SOT](../sot/admin-ai-search-evidence.md)가 제품 계약이며 과거 shadow 숫자는 기본값이 아니다.

## 조사 및 연결 지점

- 요청 저장소와 작업트리 및 상위 경로에서 AGENTS.md를 찾았으나 없었다. 기존 SOT와 기존 AI Search
  명세를 읽고 기존 코드를 보존했다.
- 실제 `admin.valuehire.cc/admin`의 소스는 별도 저장소 `/Volumes/SSD/valuehire_v4`에 있다.
  Next.js 16.2.4 / React 19 / Supabase를 사용한다. 호스트 AGENTS.md 및 관련 제품·인증·TDD 문서를 읽었다.
- 원래 호스트 저장소의 다수 사용자 변경은 건드리지 않았다. d273c088eaf9480df397e746a77ff186efe49a21에서
  이 작업트리 아래 `worktrees/host-admin`, 브랜치 `task/admin-ai-search-weekly`를 분리했다.
- 기존 `app/(admin)` 레이아웃을 유지한다. `adminMenu.ts`, `adminNavigationRouteManifest.ts`에 새 경로를
  추가하며 기존 메뉴 테스트의 실제 항목 수를 갱신한다. 변경 소스 전체는 `apps/admin-integration/overlay`
  와 멱등 설치기로 기존 PR 안에서 검토한다. 별도 PR은 만들지 않는다.
- API는 기존 `requireInternalOpsAccess`를 호출하고 `getRequestUser`와 회사 도메인을 추가 확인한다.
  기존 개발용 bypass가 있더라도 이 모듈의 실제 세션 검사는 항상 실행된다. 페이지도 동일하다.
- Gmail은 호스트의 `gmail-accounts.mjs`, `backfill-ingestion.mjs` 및 `textify.mjs` 인증·텍스트 파서를
  재사용한다. 계정 레지스트리의 기존 DWD 인증만 사용하며 클라이언트에 전달하지 않는다.

## 서버 작업과 저장

`collect.py` → GET 전용 `gmail-reader.mjs` → private SQLite 체크포인트 → `normalize.py` → 기존 Supabase
형식의 PostgreSQL migration/upsert → 인증된 Next API → 관리자 표 순서다.

수집 작업은 labels를 현재 계정에서 조회해 정확한 `02aisearch` ID를 확인한다. Inbox와 해당 라벨은
각각 끝까지 읽고 합집합으로 만든다. Sent는 별도 읽기 범위다. 페이지의 ID와 다음 토큰을 먼저 저장한
뒤 본문을 읽으며, quota/일시 오류에는 backoff를 적용한다. 실패 원문은 비공개 run에 저장한다.
재시도 후에도 원문 실패가 있으면 PARTIAL이다. 완전한 재개와 신규 실행을 구분한다.
작업 중 도착분은 시작 epoch 이후 Inbox/Sent delta와 전체 AI 라벨 재확인으로 보충할 수 있다.

```sh
export AI_SEARCH_HOST_APP="$ADMIN_SOURCE"
export AI_SEARCH_MAILBOX="$MAILBOX"
PYTHONPATH=humansearch/src humansearch/.venv/bin/python tools/admin-ai-search/collect.py --database "$PRIVATE_DB" --run-id "$RUN_ID" --include-sent
PYTHONPATH=humansearch/src humansearch/.venv/bin/python tools/admin-ai-search/attachments.py --database "$PRIVATE_DB"
PYTHONPATH=humansearch/src humansearch/.venv/bin/python tools/admin-ai-search/normalize.py --database "$PRIVATE_DB"
PYTHONPATH=humansearch/src humansearch/.venv/bin/python tools/admin-ai-search/load-postgres.py --database "$PRIVATE_DB" --dsn "$MODULE_DSN"
```

`--refresh-since-start`는 같은 run의 마무리 delta를 추가한다. 신규 전수 수집은 새 run ID로 실행한다.
정규화 캐시는 원문 checksum·parser version·AI 라벨 포함 여부를 모두 비교한다. 지원 가능한 첨부만
기존 textify로 읽고, 나머지 형식과 미분류 메일은 review queue에 남긴다.
실제 JSONB가 거부한 NUL은 DB 표현에서 `\\u0000`으로 표시하며 원본 MIME와 raw checksum은 유지한다.

추가 migration은 `20261029090000_admin_ai_search_weekly.sql`이다. 기존 migration을 수정하지 않고 호스트의
`supabase/migrations/`에도 설치된다. 명시적 DSN 적재기는 모듈 테이블만 upsert한다. 프로덕션 적용은 하지 않았다.

## 영구 관계와 화면

14개 개념 테이블에 settings를 추가한 15개 테이블이다. generated FK, 후보+포지션+Batch uniqueness,
주차별 표시번호 uniqueness, 점수/상태 check, RLS 및 anon/authenticated 권한 차단을 적용한다.
원본은 비공개 SQLite에도 유지하며 정규화 메일에는 Gmail 링크·checksum·parser·처리 사유를 보존한다.

Batch allocator는 DB transaction/advisory lock을 사용한다. 기존 ID를 재사용하고 confirmed/provisional
순번을 별도 배정한다. provisional 확정 후에도 이전 P번호를 예약해 두며 과거 표시번호를 보존한다.
새 원문은 과거 번호를 다시 정렬하지 않는다. 근거가 부족한 실제 메일은 모두 provisional로 유지했다.

서버가 최근 4개 주차와 동일 필터 범위의 집계·행을 만든다. 행은 후보+포지션 단위이며 모든 Batch와
평가 이력은 별도로 남는다. 현재 parser와 일치하지 않는 과거 해석은 Raw에 남고 현재 집계에서 제외한다.
총 후보가 불완전하면 null과 사유 및 관찰된 후보 수를 제공한다. JD·고점수 미컨택도 불완전하면 null이다.

원본 URL은 http/https만 허용하고 사용자정보가 포함된 URL을 거부한다. 원문은 React 텍스트로 표시한다.
원문 HTML을 실행하지 않는다. 필터와 pagination은 바인딩한 JSON RPC 인자로 전달한다.
상태 변경 API와 화면의 데이터 가져오기 버튼은 없다. 인증된 읽기 API도 private/no-store다.

## 그록 컨택 보고 연결

자유 형식 총계는 contact_evidence.reported_totals와 원문을 보존하고 개별 후보에게 배분하지 않는다.
정밀 보고는 아래 형식을 지원한다. 기존 메일이 이 형식이 아니라면 review queue에서 원문을 확인한다.

```json
{"version":"ai-search-contact-report/v1","events":[{"candidate_profile_url":"https://linkedin.com/in/example","company":"고객사","position":"포지션","channel":"LINKEDIN","actor":"OWNER","status":"CONTACTED","sent_at":"2026-10-23T12:00:00+09:00","checked_at":"2026-10-24T12:00:00+09:00","evidence_reference":"inmail:검증된메시지ID"}]}
```

미발송은 위 식별자에 정확히 일치하는 scope, `complete_for_candidate_position:true`,
`pagination_exhausted:true`, checked_at, evidence_reference가 모두 필요하다. 발송 시각과 상충하면
REVIEW_REQUIRED다. 이메일 수신자·이름·문체로 후보를 연결하지 않는다.

## 검증과 제한

[실행 보고](admin-ai-search-native-validation-2026-10-30.md)에 실데이터·테스트·환경 실패를 구분했다.
localhost RPC 어댑터는 실제 PostgreSQL을 service role로 읽으며 기존 관리자 세션 검사를 생략하지 않는다.
시스템 DNS가 없는 환경에서 선택적으로 DoH를 사용했고 TLS 호스트 검증을 유지했다. OS DNS는 변경하지 않았다.
UID 501의 passwd 조회가 실패해 격리된 로컬 PostgreSQL 프로세스에만 사용자 조회 interpose를 적용했다.
OS 계정·인증·프로덕션 DB는 변경하지 않았다. 이 임시 도구와 PII DB는 ignored artifacts 안에만 있다.

브라우저 UI 실증, 실제 개별 채널 연락 이력 완료, 프로덕션 schema 적용·머지·배포는 완료로 보고하지 않는다.
