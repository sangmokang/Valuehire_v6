# Valuehire v6 production walking skeleton — L3 strict goal (2026-09-04)

## 0. 결론과 배송 상태 판정 규칙

이 작업의 완료 단위는 "페이지가 열린다"가 아니라, 격리된 Vercel Preview에서 테스트 관리자가 로그인하고 한 포지션에 연결된 합성 후보자 한 명을 조회한 뒤 검토 상태를 변경하고 새 세션에서 같은 값을 재조회하며 테스트 데이터를 정리하는 종단간 업무 경로다.

Preview와 Production은 DB와 비밀값을 공유하지 않는다. 대신 같은 commit SHA, 같은 migration digest, 같은 필수 환경변수 이름/검증 규칙, 같은 인증·권한·읽기 코드 경로를 증명한다. Production 검증은 health, 비인증 차단, 15분 이하의 일회성 관리자 cookie를 사용한 핵심 목록 read-only, 배포 직후 오류 로그까지만 수행하며 자동 쓰기 smoke는 금지한다. 앱 cookie는 `Max-Age=900`이다. 서버는 access JWT의 `iat/exp`를 서명 검증 없이 먼저 decode해 발급 후 15분이면 fail-fast 거부하고, 실제 서명·issuer·세션 유효성은 모든 인증 요청의 Supabase `/auth/v1/user` 검증에 맡긴다. Production smoke는 별도 15분 운영 만료창과 cookie 안 access JWT의 실제 `exp`가 유효하고 60분 이내인지 함께 확인한다.

이 문서는 변하지 않는 계약과 시점별 영수증을 기록한다. 현재 배송 상태는 항상 최신 보고의 SHA별 증거로 판정하며, 아래 규칙보다 오래된 Preview PASS나 이 문서의 역사적 영수증을 우선하지 않는다.

- `LOCAL_ONLY`: 해당 SHA의 로컬 전체 gate가 통과했지만 원격 Preview smoke가 아직 없을 때만 현재 상태로 사용한다.
- `PREVIEW_VERIFIED`: 같은 SHA의 full Preview smoke, 독립 cleanup readback, bounded log scan이 모두 PASS일 때만 선언한다.
- `READY_TO_PROMOTE`: Preview 합격에 더해 Production 환경·DB·Git provenance·migration·rollback 계약이 모두 충족될 때만 선언한다.
- `PRODUCTION_REACHABLE`: 기능이 있는 같은 SHA의 Production 배포와 health 응답이 실제로 존재할 때만 선언한다.
- `PRODUCTION_VERIFIED`: Production GET-only 검증과 배포 직후 로그 검사가 PASS일 때만 선언한다.
- `BUSINESS_USED`: 사용자가 실제 운영 화면에서 업무 한 건을 완료하기 전까지 선언 금지한다.

## 1. 목표 프롬프트와 범위

### 목표

내 계정으로 관리자 화면에 로그인하고, 포지션 한 건에 연결된 후보자 한 명을 조회한 뒤 검토 상태를 변경하고 새로고침 또는 새 세션 후에도 유지되는 최소 업무 경로를 만든다.

### 포함

- Vercel Preview/Production 배송 계약과 환경 분리
- Supabase Auth 기반 관리자 로그인과 서버 측 관리자 allowlist
- 포지션-후보자 관계 및 후보자 검토 상태의 버전 관리 migration
- 인증 세션, 후보자 read, 상태 write, 독립 readback API/UI
- Preview 전용 합성 fixture 생성/검증/정리 smoke
- 실제 배포 UI를 실행하는 headless Chromium smoke. 검증 실행기에는 Python Playwright/Chromium이 있어야 하며 없으면 API-only 성공으로 대체하지 않고 전체 smoke를 실패시킨다.
- 오류의 명시적 실패, 비밀/개인정보 비로깅, 외부 발송 0 정적·동적 증거
- Preview 승격 gate와 Production read-only 확인기
- Preview 복구 참조와 Production rollback eligibility의 read-only 검증

### 제외

- 기존 운영 Supabase 프로젝트에 대한 schema/data write
- Production 자동 write smoke
- 이메일, 문자, 채용 포털 발송 기능
- 대시보드 수동 schema 변경
- 기존 `pipeline_*` 테이블 또는 security-definer view/RPC의 재사용
- 실제 후보자 개인정보를 fixture, 저장소, CI, 공개 Preview에 기록
- 사용자 대신 `BUSINESS_USED` 선언

## 2. 착수 진단 — 구현 전 실제 파일·명령 근거

진단 기준 시각은 2026-09-04 UTC이며, 착수 commit은 `b7240936827032d5ee6791fa8cdb7d62ef6584b4`다. 비밀값과 개인정보 값은 출력하지 않고 존재, 종류, 개수, fingerprint만 확인한다.

### 저장소/애플리케이션

- root에는 `package.json`, `vercel.json`, `.vercel/`, `.env.example`, `supabase/`가 없다.
- `apps/admin/index.html`은 `LOCAL SHADOW · 운영 아님`을 표시한다.
- `apps/admin/app.js`는 `/api/dashboard` read만 수행하며 로그인·후보자 상태 write가 없다.
- `humansearch/src/humansearch/admin_weekly_dashboard/shadow_server.py`는 loopback 전용이고 write를 405로 거부한다.
- root `.env`에는 ChatGPT 자동화 관련 변수 이름만 있고 이 앱의 Vercel/Supabase 계약은 없다.

### Vercel

- `vercel --version`: 50.37.0.
- 인증 주체: `sangmokang`.
- 보이는 프로젝트는 `valuehire-v4`, `valuehire-v2`이며 `valuehire-v6`는 없다.
- 따라서 현재 v6 Preview/Production URL, 환경 분리, 배포 SHA, rollback 대상은 `NOT_RUN`이다.

### Supabase — read-only 진단

- shell의 URL host는 `sjldbyfcesinrbkgkqwv.supabase.co`이며 key 값은 출력하지 않았다.
- key는 legacy JWT `service_role`, project ref 일치, 길이 219다. 브라우저·로그·저장소 사용을 금지한다.
- Supabase CLI 2.75.0은 로그인되어 있으나 저장소는 project에 link되어 있지 않다.
- 계정에 보이는 프로젝트:
  - `uhguznqdilfclfvjgses` (`valueconnectx`): public table 28, auth user 23, migration 28
  - `sjldbyfcesinrbkgkqwv` (`valueconnect`): public table 221, auth user 45, migration 59
- Management API database query는 `read_only: true`로 실행했고 DB role은 `supabase_read_only_user`, PostgreSQL은 17.6이었다.
- 로컬 migration은 0건, 원격 `sjld...` migration은 59건이다. 최초는 `20260507000000 pipeline`, 최신은 `20260901103000 invoice_fee_agreement_idempotent_upsert`다.
- `pipeline_candidates.jd_id`는 nullable text이고 position FK가 없으며, `pipeline_candidates.stage`에는 허용값 CHECK가 없다.
- `pipeline_members`와 `pipeline_stage_history`에는 `{public}` 대상 `ALL`/`true` 정책이 관측됐다.
- `pipeline_candidates_active`와 archive view에는 `security_invoker` reloption이 관측되지 않았다.
- 결론: 원격 drift와 권한 위험을 해소하기 전 기존 원격 프로젝트를 v6 Preview/Production DB로 재사용하지 않는다.

CLI 재현 결과도 같은 결론이다.

- `supabase db pull production_baseline --schema public` (격리 temp workdir, linked read): exit 1. 원격 59개 version 모두에 대해 "migration history does not match local files"를 반환했다. CLI가 제시한 `migration repair --status reverted ...`는 원격 history write이므로 실행하지 않았다.
- `supabase db diff --linked --schema public --file production_diff` (격리 temp workdir): exit 1. 로컬 Docker daemon이 없어 shadow database를 만들지 못했다. 이는 drift 없음의 증거가 아니라 `BLOCKED`다.
- Supabase organization `valueconnect`의 plan은 Management API read에서 `pro`로 확인됐다. Preview branch는 사용 가능하지만 공식 문서상 시간당 사용료가 발생하므로, 데이터 없이 만들고 이 작업의 검증 수명만 유지한다.

### 격리 Preview DB 준비 영수증

- 첫 Preview branch `ynomkdvfguzasdymenwi`는 데이터 없이 생성됐지만 branch 상태가 `MIGRATIONS_FAILED`였고 migration history가 한 건뿐이었다. schema가 우연히 보인다는 이유로 합격 처리하지 않았다.
- 대체 branch `drbrtkbkddhryvcmybue` (`valuehire-v6-preview-b724093-r2`)도 `--with-data` 없이 생성해 시작 시 `admin_positions=0`, `admin_candidates=0`, `auth.users=0`을 read-only query로 확인했다.
- 대체 branch에 CLI `db push`로 저장소 migration만 적용했다. 최초 다섯 version 적용 뒤 실제 Preview smoke가 Supabase 기본 ACL에 남은 audit-table `UPDATE`/DDL 권한을 RED로 잡았고, 적용된 migration을 수정하지 않은 채 `20260904000170_lock_review_audit_privileges.sql`을 forward 적용했다. 현재 `supabase migration list --linked`는 local/remote 여섯 version이 모두 일치하고 `supabase db push --dry-run`은 `Remote database is up to date`를 반환한다.
- Management API read-only query의 실행 role은 `supabase_read_only_user`였다. `admin_positions`, `admin_candidates`, `admin_candidate_review_events` 세 table의 NOT NULL/PK/UNIQUE/composite tenant FK/CHECK, RLS enabled+forced, service-role 전용 policy를 확인했고 `public`/`anon`/`authenticated`의 위험 table grant와 function EXECUTE grant는 각각 0건이었다. audit table의 `service_role` ACL은 reset 뒤 정확히 `DELETE`, `INSERT`, `SELECT` 세 권한뿐이다. 관리 table을 읽는 view/RPC는 0건이며, 세 trigger function은 모두 `security invoker`이고 고정 `search_path`를 사용한다.
- 이 준비 과정에서 기존 Production ref `sjldbyfcesinrbkgkqwv`에는 schema/data/history write를 수행하지 않았다.

### 구현 전 원칙 로드 원장

| UTC | session | commit | 명령 | exit | stdout |
| --- | --- | --- | --- | ---: | --- |
| 2026-09-04T14:08:45Z | `01a06cbf-311e-7092-8b34-61916ea5d4d4` | `b724093...` | `sed -n '1,9999p' docs/sot/coding-principles.md` | 0 | 해당 working-tree 파일 전체; SHA-256 `26c59f97eb467404c79155f55202ae8651201ea1915739f3d18e9b3e8cbcc1df` |
| 2026-09-04T14:08:50Z | same | `b724093...` | `sed -n '1,9999p' docs/sot/principles.yaml` | 0 | 해당 working-tree 파일 전체; SHA-256 `cdfe854660c4be3967be251f8ef73058844f130ade291a10f78189640bfddd56` |
| 2026-09-04T14:08:53Z | same | `b724093...` | `bash scripts/acceptance-principles-check.sh` | 0 | 아래 원문 |

```text
VERDICT: PASS
SOT_LOAD: PASS docs/sot/coding-principles.md
LEDGER_LOAD: PASS docs/sot/principles.yaml
MECHANISMS: PASS 34/34 strict-contract-bindings
WIRING: PASS pre-push=1 ci=1
CHECKED: 36
```

`make -n red-ledger`는 2026-09-04T14:23Z에 exit 2, `No rule to make target 'red-ledger'`를 반환했다. 따라서 이 저장소의 실제 RED 원장은 아래 직접 명령과 이 문서의 검증 표로 유지한다.

## 3. 배송 계약

### 3.1 환경 격리

| 항목 | Vercel Preview | Vercel Production |
| --- | --- | --- |
| 배포 원천 | task branch commit | Preview 합격과 동일한 commit SHA |
| Supabase | 전용 branch/project, 합성 데이터만 | 승인된 Production project |
| DB ref | Production ref와 달라야 함 | Preview ref와 달라야 함 |
| schema | 동일 migration digest | 동일 migration digest |
| 관리자 | 자동 생성한 E2E 계정 | 오너가 직접 사용하는 allowlisted 계정 |
| write | `E2E-TEST-*` tenant/행만 | UI의 승인된 실제 업무 write; 자동 smoke write 금지 |
| 외부 발송 | 코드/설정 모두 차단 | 이 skeleton에는 기능 자체가 없음 |
| URL 노출 | Vercel deployment protection 또는 동등한 접근 제한 필수 | 공식 Production URL |

Preview/Production 값 자체가 같다는 주장은 금지한다. 차이를 허용하는 값은 URL, Supabase ref/key, tenant, 계정이다. 반드시 같아야 하는 것은 commit SHA, migration digest, 환경 계약 version, 인증·권한·read 코드 경로다.

### 3.2 필수 환경변수 계약

서버는 다음 이름을 부팅/요청 진입 전에 검증하고, 누락·형식 오류 시 `CONFIG_INVALID`로 503을 반환한다. 비밀값은 응답과 로그에 포함하지 않는다.

- `VALUEHIRE_ENV`: `preview` 또는 `production`
- `VALUEHIRE_PUBLIC_URL`: HTTPS origin 한 개
- `VALUEHIRE_DEPLOY_SHA`: 40자리 git SHA
- `VALUEHIRE_SCHEMA_DIGEST`: 적용 migration digest
- `VALUEHIRE_SUPABASE_URL`: HTTPS Supabase origin
- `VALUEHIRE_SUPABASE_ANON_KEY`: 서버의 Auth 로그인/refresh 전용
- `VALUEHIRE_SUPABASE_SERVICE_ROLE_KEY`: 서버 전용 DB/Auth admin key
- `VALUEHIRE_ADMIN_EMAIL_SHA256`: lower-case email의 SHA-256 allowlist
- `VALUEHIRE_TENANT_ID`: Production tenant 또는 Preview의 `E2E-TEST-*`

Preview는 `VALUEHIRE_ENV=preview`, `VALUEHIRE_TENANT_ID=E2E-TEST-*`를 강제한다. Production은 반대로 E2E tenant를 거부한다. `SUPABASE_URL` 등 모호한 legacy 이름은 앱이 읽지 않는다.

### 3.3 SHA·승격·rollback 계약

- `/api/health`는 비밀/PII 없이 runtime, commit SHA, schema digest, 환경 이름, DB 연결 상태를 반환한다.
- 이 프로젝트는 Git provider에 연결되지 않은 source-upload CLI 배포다. `scripts/deploy-preview.sh`만 정식 Preview 배포 경로로 사용하며, 고정한 Vercel scope/project/org link와 clean worktree를 먼저 확인한 뒤 `HEAD`를 application-owned `VALUEHIRE_DEPLOY_SHA`에 deployment-scoped `--env`로 고정한다. Git trigger가 없는 Preview에서 비어 있을 수 있는 Vercel-owned `VERCEL_GIT_COMMIT_SHA`는 덮어쓰지 않는다. `--target preview`를 생략하거나 `--prod`를 사용하는 경로는 이 계약 밖이다.
- application runtime SHA나 Vercel의 best-effort `source=cli` 표시는 단독 합격 근거가 아니다. Preview smoke가 별도 Deployment API에서 자동 기록된 `meta.gitCommitSha=HEAD`, `VALUEHIRE_DEPLOY_SHA` runtime 이름을 확인하고, Vercel source-file API가 반환한 전체 배포 입력 경로와 각 파일 내용을 clean HEAD의 추적된 배포 입력과 SHA-1로 대조한다. Vercel system Git SHA가 존재하면 runtime에서 같은 SHA를 강제하고, Production은 system Git SHA가 없으면 설정 오류로 차단한다.
- Preview smoke가 읽은 SHA와 `git rev-parse HEAD`가 일치해야 한다.
- Production 승격 직전 Vercel deployment SHA와 현재 commit SHA가 일치해야 한다.
- migration history와 저장소 digest가 다르면 배포/승격을 실패시킨다.
- Production 승격 전 `npm run verify:production-schema-readonly`는 Management API의 `/database/query/read-only`로 Production catalog를 조회하고, Preview에서 확보한 `VALUEHIRE_PREVIEW_REMOTE_SCHEMA_FINGERPRINT`와 동일한 schema/권한/RLS/trigger/function 계약을 증명해야 한다. Production ref 또는 Preview fingerprint가 없으면 네트워크 전에 실패한다.
- Preview smoke는 `vercel rollback --help`의 구문과 직전 건강한 Preview deployment ID를 읽기 전용으로 확인한다. 직전 Preview는 alias 복구·재배포를 위한 recovery reference일 뿐 Production rollback 후보로 부르지 않는다.
- Production 승격 계약의 rollback 검증은 `npm run verify:production-rollback-readonly`가 현재 READY Production deployment를 확인하고, Vercel의 `target=production&state=READY&rollbackCandidate=true` 목록에서 더 오래된 eligible Production deployment ID를 특정해야 PASS다. 이 명령은 조회와 `vercel rollback --help`만 수행하며 rollback 자체를 실행하지 않는다. eligible 후보가 없으면 `READY_TO_PROMOTE`는 false다. 실제 `vercel rollback` 실행은 장애 대응 또는 명시 승인 때만 수행한다.

## 4. 데이터·인증·개인정보·외부 효과 계약

### 입력

- 로그인: email/password. password는 브라우저 메모리에만 잠시 존재하고 서버/로그/저장소에 남기지 않는다.
- 후보자 조회: 서버가 환경별 고정 tenant와 인증된 관리자 주체를 사용한다.
- 상태 변경: candidate UUID, 허용된 review status, `expectedVersion` 정수.

### 출력

- 로그인 성공: HttpOnly, Secure, SameSite=Lax 세션 cookie; body에는 `{ok:true}`만 반환한다.
- 후보자 목록: 합성 Preview에서는 synthetic display label만, Production에서는 업무에 필요한 최소 필드만 반환한다.
- 상태 변경: candidate ID, 새 status, 증가된 version, updatedAt.
- health: PII/secret 없는 상태와 fingerprint만 반환한다.

### 오류

- `AUTH_REQUIRED` 401: cookie 없음/만료/위조.
- `AUTH_INVALID` 401: 잘못된 자격증명. provider 원문을 숨긴다.
- `AUTH_FORBIDDEN` 403: 유효한 사용자지만 관리자 hash 불일치.
- `AUTH_RATE_LIMITED` 429: Supabase Auth의 password-token rate limit 도달.
- `CSRF_REJECTED` 403: write의 Origin 불일치.
- `VALIDATION_FAILED` 400: UUID/status/version 형식 오류.
- `NOT_FOUND` 404: 현재 tenant에 후보자 없음.
- `VERSION_CONFLICT` 409: stale update.
- `CONFIG_INVALID` 503: 필수 환경 누락/불일치.
- `DEPENDENCY_UNAVAILABLE` 502/503: Supabase/network 실패.
- 오류는 빈 목록, null, 200, 낙관적 UI 성공으로 변환하지 않는다. 로그는 request correlation ID, 코드, 경계만 남기고 email/name/token/body는 남기지 않는다.

### DB 제약

- position과 candidate는 UUID PK와 `tenant_id NOT NULL`을 가진다.
- candidate의 `(tenant_id, position_id)`는 position의 `(tenant_id, id)`를 참조해 cross-tenant 연결을 DB에서 차단한다.
- review status는 DB CHECK와 앱 allowlist가 같은 versioned authority에서 생성/대조된다.
- 필수값은 NOT NULL, 자연 중복은 UNIQUE, 관계는 FOREIGN KEY, 허용값/버전은 CHECK로 강제한다.
- RLS를 활성화하고 anon/authenticated 직접 table 접근 정책을 두지 않는다. 검증된 서버만 service role로 최소 query를 수행한다.
- review status 변경은 actor email의 SHA-256만 transient 입력으로 받아 DB `BEFORE UPDATE` trigger가 정확한 version +1과 함께 감사 event를 같은 statement에서 원자적으로 기록하고 transient 값을 candidate row에서 제거한다. 감사 event의 `service_role` ACL은 `SELECT`/`INSERT`/`DELETE`만 허용해 UPDATE·TRUNCATE·REFERENCES·TRIGGER를 회수한다. REST UPDATE는 정확히 HTTP 403/SQLSTATE 42501로 거부되고 owner 경로 UPDATE도 trigger의 23514로 막혀야 하며, DELETE는 `E2E-TEST-*` cleanup에만 허용해 Production 이력을 append-only로 강제한다.
- 이 audit trail은 정상 app/API 경로와 일반 table 권한에 대한 append-only 증거다. 서버의 `service_role` 자체가 탈취된 경우 임의 event insert까지 막는 tamper-proof ledger는 아니며, 그 위협까지 다루려면 후속 버전에서 좁은 transition RPC/별도 감사 writer로 권한을 분리해야 한다.
- view/RPC는 이 skeleton에서 사용하지 않는다. 추가 시 `security_invoker`와 RLS 동작을 별도 테스트하기 전 금지한다.

### 운영 쓰기와 외부 효과

- 구현 중 원격 Production schema/data write: 0건.
- Production 자동 smoke write: 0건.
- Production read-only smoke cookie는 값 자체를 출력하지 않는다. 운영자가 별도 입력한 만료창이 15분 이하이고, cookie에 든 access JWT의 `exp`도 아직 유효하며 남은 수명이 60분 이하일 때만 사용한다.
- 로그인은 Supabase `/auth/v1/token?grant_type=password`의 Token limiter를 사용한다. 현재 Supabase Auth upstream에서 이 limiter는 이름이 다소 넓은 `rate_limit_token_refresh` 설정에 연결되므로, Preview artifact 검증은 Management API read-only Auth config에서 그 값이 양의 정수인지 확인한다. 앱은 provider 429를 `AUTH_RATE_LIMITED`로 숨김없이 전달하며 Production 승격 때 Production project 설정도 다시 확인한다.
- 로그아웃은 Supabase `/auth/v1/logout?scope=local`의 현재 session 폐기를 요청한 뒤 앱 cookie를 제거한다. 원격 폐기가 실패하면 503을 반환해 실패를 숨기지 않으면서 앱 cookie와 화면의 로컬 후보자 상태는 제거한다. 성공한 logout 뒤 smoke는 기존 cookie를 `/auth/v1/user` 경로에 다시 제시해 401을 요구한다. session row를 보지 않는 JWT-only 검증기는 서명된 `exp`까지 token을 받아들일 수 있으므로, 로컬 JWT decode만으로 즉시 무효화라고 주장하지 않는다.
- Preview write: `E2E-TEST-*` tenant와 테스트 auth user에 한정하고 `finally` cleanup을 강제한다.
- 외부 email/SMS/portal 전송: 0건. SMTP, SMS, portal client/URL 호출을 코드와 dependency에서 금지한다.
- 테스트 auth user는 admin create API로 email-confirmed 상태로 만들며 invite/recovery/magic-link API를 호출하지 않는다.
- cleanup 실패는 전체 smoke FAIL이고 잔존 ID만 비-PII 형태로 보고한다.

## 5. EARS 인수 기준과 counter-AC

### Preview

- **AC-P1** When Preview smoke starts, the system shall prove the deployment environment is Preview and its Supabase ref differs from Production.
- **AC-P2** When valid isolated credentials are submitted, the system shall establish an HttpOnly session; invalid or non-allowlisted credentials shall fail explicitly.
- **AC-P3** When the authenticated admin opens the candidate route, the system shall return exactly one `E2E-TEST-*` candidate linked to exactly one position.
- **AC-P4** When an allowed review status with the current version and authenticated actor hash is submitted, the DB shall persist it, increment version exactly once, and append one immutable review event in the same statement.
- **AC-P5** When the first session is logged out, the old cookie shall fail through `/auth/v1/user`; when a separate browser session logs in again, it shall return the updated status/version.
- **AC-P6** When smoke exits for success or failure, it shall delete review event, candidate, position, and test auth user in dependency order, then prove every row/user absent.
- **AC-P7** During the whole smoke, no email/SMS/portal sending endpoint or dependency shall be invoked.
- **AC-P8** When config/auth/DB/network fails, the response shall be a non-2xx typed error rather than an empty collection or success.

### 승격과 Production

- **AC-R1** When `READY_TO_PROMOTE` is evaluated, Preview smoke, commit/deploy SHA, env contract, migration digest, rollback CLI syntax, eligible prior Production rollback candidate, and PII scans shall all PASS.
- **AC-R1a** When Production schema readiness is evaluated, the read-only catalog contract and fingerprint shall match the Preview contract; missing target, credential, or fingerprint shall fail before any network request.
- **AC-R2** When Production is checked, health shall report the expected SHA/schema/environment without secrets or PII.
- **AC-R3** When an unauthenticated Production client calls an admin API/page, access shall be blocked.
- **AC-R4** When the authorized owner loads the core list in Production verification, the check shall be read-only and shall not mutate rows or auth users.
- **AC-R5** After deployment, Vercel error logs shall be inspected with a bounded window and shall contain neither unhandled errors nor PII.
- **AC-R6** `BUSINESS_USED` shall remain false until the owner personally completes one real Production review update and supplies the receipt.

### counter-AC — 가짜 완료

- localhost/in-memory test만 통과하고 Preview E2E를 PASS라고 한다.
- Preview와 Production이 같은 Supabase ref/service key를 사용한다.
- fixture seed/read/update/cleanup을 service-role 직통으로만 수행하고 실제 로그인/API/UI 경로를 검증하지 않는다.
- cookie를 유지한 readback만 하고 새 세션 영속성이라고 부른다.
- 상태 PATCH가 0행을 바꿔도 200을 반환한다.
- provider 오류를 `[]`, `null`, 200 또는 "후보자 없음"으로 숨긴다.
- 로그/HTML/번들/CI artifact에 email, 이름, token, key 또는 candidate payload가 남는다.
- cleanup을 성공 가정하고 실제 absence를 조회하지 않는다.
- Preview PASS 뒤 다른 commit 또는 다른 migration digest를 Production에 배포한다.
- Production verification에서 편의를 위해 합성 write를 수행한다.
- migration file 없이 Dashboard/SQL editor에서 수동 변경한다.
- app validation만 있고 DB NOT NULL/UNIQUE/FK/CHECK가 없다.
- service role을 브라우저에 보내거나 public RLS `ALL true` 정책에 의존한다.
- 실제 사용자 업무 영수증 없이 `BUSINESS_USED`를 선언한다.

## 6. Harness 게이트와 RED 원장

| 단계 | 필수 명령/증거 | 최초 기대 | 최종 기대 |
| --- | --- | --- | --- |
| G0 원칙 | `bash scripts/acceptance-principles-check.sh` | PASS | PASS |
| G1 계약 | goal 정적 검사 | PASS | PASS |
| G2 Preview smoke | `node scripts/smoke-preview-admin.mjs` with Preview env | **FAIL을 먼저 보존** | PASS |
| G3 mutation | auth 우회, 빈 목록 은폐, status CHECK 제거, cleanup 제거 mutation | FAIL | FAIL |
| G4 코드 | targeted unit/integration tests, lint/type/static gates | 일부 RED | PASS |
| G5 DB drift | read-only migration list/schema digest compare + `npm run verify:production-schema-readonly` | current remote 재사용 FAIL | isolated Preview/Production contract PASS |
| G6 보안 | secret/PII scan + bundle scan + outbound allowlist | PASS | PASS |
| G7 V1/V2 | Claude 1차 + fresh Codex 2차 적대검증 | NOT_RUN | 모두 PASS |
| G8 전체 | `bash scripts/session-status.sh`, `bash verify.sh`, CI-equivalent | baseline 기록 | PASS |

Preview 최초 RED는 배포된 URL을 대상으로 실행한다. URL이나 필수 smoke 입력 누락만으로 만든 인위적 RED는 인정하지 않고, 배포에 login/DB workflow가 없어 계약된 endpoint/동작에서 실패해야 한다.

의존성 공급망 gate는 dependency 0개인 현재 상태에서도 생략하지 않는다. npm lockfile v3를 버전 관리하고 `npm audit --omit=dev --audit-level=high`를 acceptance에서 실행하며, lockfile이 없거나 감사 명령이 실패하면 G6도 실패한다.

### Preview RED 영수증 — 2026-09-04T14:32:39Z

- project: `sangmokangs-projects/valuehire-v6` (`prj_isTeytMDr2EiXW5hg5rv4wPdyBW5`)
- Preview deployment: `dpl_4oW5mVL9RS3ZYPmQZVfm88EFzeV3`
- Preview URL: `https://valuehire-v6-133xu4nmc-sangmokangs-projects.vercel.app`
- Vercel inspect: `target=preview`, `readyState=READY`, output 0개
- 명령: 모든 smoke 입력을 채운 `node scripts/smoke-preview-admin.mjs`
- exit: 1

```text
VERDICT: FAIL
CODE: NON_JSON_RESPONSE
MESSAGE: expected JSON from https://valuehire-v6-133xu4nmc-sangmokangs-projects.vercel.app/api/health, got HTTP 302
```

302는 Vercel Deployment Protection이 자동화 요청을 차단한 첫 실패다. 인증된 `vercel curl`로 같은 URL의 실제 앱 경계를 확인한 후 다음 RED를 얻었다.

```text
HTTP/2 404
content-type: text/plain; charset=utf-8
x-robots-tag: noindex
x-vercel-error: NOT_FOUND

The page could not be found
NOT_FOUND
```

즉, 보호 우회 입력 누락이 아니라 실제 배포에 `/api/health`와 walking-skeleton endpoint가 없어서 실패함을 확인했다. 이후 GREEN smoke는 보호를 끄지 않고 Vercel automation bypass를 사용해야 한다.

smoke runner가 `vercel curl`로 HttpOnly `_vercel_jwt` automation cookie를 메모리에 부트스트랩하도록 보강한 뒤 같은 전체 입력으로 재실행한 최종 RED는 다음과 같다. cookie 값은 출력하지 않았고 임시 파일은 즉시 삭제한다.

```text
VERDICT: FAIL
CODE: NON_JSON_RESPONSE
MESSAGE: expected JSON from https://valuehire-v6-133xu4nmc-sangmokangs-projects.vercel.app/api/health, got HTTP 404
```

주의: 새 프로젝트의 첫 `vercel deploy`는 `--prod` 없이도 최초 production target `dpl_74oMWgh1g2HA1J3M5XJGB3kzxQkp`를 만들었다. output 0개이고 공식 alias `/`는 HTTP 404이며 DB/env/기능/PII가 없다. 이 배포는 `PRODUCTION_REACHABLE`로 세지 않는다. 이후 모든 비운영 배포는 `scripts/deploy-preview.sh`가 `--target preview`를 명시하며, Production에는 승격 gate 전 새 기능을 배포하지 않는다.

### 첫 로컬 GREEN 영수증 — 2026-09-04T16:00Z

- 대상 worktree: `worktrees/production-walking-skeleton-20260904`
- 당시 판정: `LOCAL_ONLY`
- 아직 원격 Preview GREEN, Production reachability, Production verification, business use는 선언하지 않는다.
- `/api/health`는 raw Supabase ref를 노출하지 않고 `supabaseRefFingerprint = sha256(ref).slice(0,12)`만 반환한다.
- `loadConfig()`는 Vercel runtime에서만 `preview|production`을 허용하며 `VERCEL_ENV === VALUEHIRE_ENV`를 강제한다. system Git SHA가 있으면 `VERCEL_GIT_COMMIT_SHA === VALUEHIRE_DEPLOY_SHA`를 강제하고, Production에서는 system Git SHA 자체를 필수화한다. source-upload CLI Preview에서는 배포 스크립트가 application SHA를 clean `HEAD`로 고정하고 smoke가 독립 Vercel metadata를 대조한다.
- Production read-only smoke는 `VALUEHIRE_DEPLOY_SHA`를 필수 40자 lowercase hex로 검증하고 GET-only/read-only contract를 유지한다.
- smoke/static/contract checker는 외부 email/SMS/portal 발송 0건, raw ref/secret/PII 노출 금지, typed error fail-closed를 검사한다.

```text
node --test tests/production-admin/*.test.mjs
1..34
# pass 34
# fail 0

bash scripts/verify/run-acceptance.sh scripts/acceptance-production-walking-skeleton.sh
VERDICT: PASS
delivery_state=LOCAL_ONLY
OK(run-acceptance): scripts/acceptance-production-walking-skeleton.sh — 판정 4건, CHECKED 11

bash verify.sh
PASS: no secret-pattern match in any tracked file, .env not tracked

git diff --check
PASS
```

위 영수증 뒤 Vercel SHA metadata와 실제 배포 source-file 내용 결합, 원격 catalog/function-body 및 audit-table exact ACL read-only 검증, 공개 source 404, 실제 동작 mutation, 다중 후보 UI 보존, Supabase logout 후 기존 cookie 재사용 401, Auth password-token rate-limit 판정, Production read-only credential·rollback eligibility 검증, headless Chromium 실제 화면 경로, fail-closed Preview 배포기, 전 경로 CSP/HSTS·Vercel Deployment Protection 실응답 검증, 서버측 15분 세션 수명 거부, DB 원자적 review audit trail과 trigger guard의 `23514` 행동 검증, Preview cleanup을 추가했다. 첫 V1이 찾은 635줄 테스트 파일은 분할했고, 정적 gate가 현재 commit/작업tree/index/untracked 변경 파일을 모두 600줄 이하로 검사한다. 따라서 위 34-test 수치는 역사적 영수증일 뿐 최신 합격 수치로 재사용하지 않는다. 코드 고정 직전 로컬 gate는 `105/105`, Preview 정적 계약 `21`, 실제 server behavior mutant `7/7 killed`, migration `6/6`, npm 취약점 `0`으로 PASS했다. schema digest는 `14e3755595b5804f5059dd0a455f0c8a38ef3106d18b53555fa0c56e47868089`이며, 원격 catalog fingerprint와 최신 상태는 SHA별 full smoke 영수증에서 기록한다.

`bash scripts/session-status.sh`는 repo 전체 acceptance inventory를 집계하며 `RED: 7/29 (acceptance-0-7.sh 제외 — CI 담당)`를 보고했다. 이는 walking skeleton 전용 acceptance 실패가 아니며, 승격 판단에는 위 전용 gate와 Preview smoke 결과를 별도 증거로 사용한다.

## 7. 작업 단위와 롤백

1. **PLAN**: 이 goal, 원격 read-only drift snapshot, 배송/PII/write 계약.
2. **SKELETON-RED**: zero-dependency Preview smoke와 빈 v6 Preview 배포; 실제 실패 receipt.
3. **BUILD-DB**: migration, constraint/RLS 검사, Preview 전용 branch/project.
4. **BUILD-APP**: auth/session, candidate read/update, UI, typed errors.
5. **VERIFY-PREVIEW**: fixture lifecycle, new-session readback, zero outbound, cleanup.
6. **AUDIT**: R2~R5, mutation, V1 Claude, V2 Codex, file/function budget.
7. **CHECKPOINT**: 한 로컬 Lore commit. push/PR/merge는 별도 승인 범위다.
8. **SHIP**: Preview 합격과 승격 준비 판정. Production 배포가 없으면 정직하게 그 단계에서 중단한다.

각 작업 단위는 independently revertable하게 유지한다. DB rollback은 forward corrective migration을 우선하며, Preview fixture는 ID/tenant 단위 delete와 auth user delete를 사용한다. Production 자동 데이터 rollback은 하지 않는다. Vercel Preview의 직전 건강 배포는 recovery reference로만 기록하고, Production Instant Rollback eligibility와 혼동하지 않는다.

## 8. 검증 보고 계약

모든 사용자 보고는 다음 순서를 사용한다.

1. 결론과 현재 배송 상태 여섯 개
2. 판단 근거: PASS/FAIL/BLOCKED/NOT_RUN을 섞지 않은 표
3. 증거 원문: 명령, UTC 시각, exit, SHA/URL/fingerprint; secret/PII는 redaction
4. 다음 안전한 자동 단계 또는 정말 필요한 권한 blocker

최종 완료 전에는 pending work 없음, 기능 동작, 테스트 통과, known error 0, 검증 증거 수집을 재확인한다. 하나라도 거짓이면 계속 진행하거나 정확히 BLOCKED로 남긴다.
