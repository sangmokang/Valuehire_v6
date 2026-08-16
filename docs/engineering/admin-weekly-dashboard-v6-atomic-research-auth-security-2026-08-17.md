# Admin Weekly Dashboard v6 atomic research — auth-security — 2026-08-17

이 파일은 fresh read-only 조사자의 원문 증거입니다. 정본 계획이 아니며 controller의 수정 규칙과 독립 계획 감사를 우선합니다.

## Metis Analysis: AC-20/21/22/32/36/37 원자 분해

읽기 전용 조사 결과: 기준 HEAD `a02a3da8f36e22997028b0d620de4e7e970f76d8` 일치. 저장소 `AGENTS.md` 파일은 발견되지 않았고, 현재 세션 주입 AGENTS 계약 + `docs/sot/*` 6개 + 전체 admin weekly goal을 기준으로 분해했다. `apps/admin` 및 `contracts/admin-weekly-dashboard`는 아직 없음.

근거:
- 정본 우선순위: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:82`
- 새 admin 구조: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:126`
- receipt 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:184`
- data exposure admin 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:192`
- auth/OIDC/CSRF 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:315`
- bootstrap 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:317`
- RBAC/audit/UI 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:1007`
- 대상 AC: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:1179`
- mutation 요구: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:1218`
- CI/pre-push/SOT 배선: `docs/sot/verification-commands.md:43`, `hooks/pre-push:110`, `.github/workflows/verify.yml:161`
- 0건 NOT_RUN: `docs/sot/coding-principles.md:18`, `scripts/scan-data-exposure.sh:7`

### Micro Candidates

```yaml
- parent_ac: AC-20
  micro_id: AC20-M01-reference-missing-not-run
  single_observable_result: reference screenshot fixture/config가 없으면 visual parity verdict가 BLOCKED_UI_REFERENCE/NOT_RUN이고 targetCount>=1 receipt를 낸다.
  single_failure_reason: reference 없음에도 PASS 또는 FAIL로 접는다.
  rollback_unit: visual parity gate + test fixture 한 묶음 제거
  dependencies: admin UI gate receipt 형식, local fixture resolver
  allowed_files: [apps/admin/tests/unit/visual-reference-gate.test.ts, apps/admin/src/ui/visual-parity-gate.ts, scripts/acceptance-admin-ui.sh, .github/workflows/verify.yml, docs/sot/verification-commands.md, docs/sot/mechanism-registry.yaml]
  forbidden_scope: 실제 운영 캡처 획득, v4/v5 화면 import, iframe/static HTML/CSS 복사, 배포 전환
  red_command: pnpm --filter admin test -- visual-reference-gate
  green_command: bash scripts/acceptance-admin-ui.sh
  mutation_method: reference-required 조건을 제거하거나 missing을 PASS로 바꾸면 RED
  production_call_path: /admin/dashboard visual parity status computation
  target_count_method: missing-reference fixture 1건을 카운트하고 receipt targetCount=1 검증
  cannot_split_reason: reference 부재 판정과 Phase 5 차단은 같은 UI parity blocker의 단일 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-20
  micro_id: AC20-M02-phase5-cutover-blocked
  single_observable_result: visual parity verdict가 BLOCKED_UI_REFERENCE/NOT_RUN이면 Phase 5 cutover readiness가 blocked=true를 반환한다.
  single_failure_reason: visual blocker가 있는데 cutover readiness가 true다.
  rollback_unit: cutover readiness guard + test 한 묶음 제거
  dependencies: AC20-M01 verdict enum
  allowed_files: [apps/admin/src/domain/cutover-readiness.ts, apps/admin/tests/unit/cutover-readiness.test.ts, scripts/acceptance-admin-ui.sh]
  forbidden_scope: 운영 주소 변경, 배포, 실제 screenshot 비교
  red_command: pnpm --filter admin test -- cutover-readiness
  green_command: bash scripts/acceptance-admin-ui.sh
  mutation_method: BLOCKED_UI_REFERENCE 분기를 허용으로 바꾸면 RED
  production_call_path: Phase 5 readiness checker used before cutover task
  target_count_method: blocked verdict fixture 1건 + ready verdict fixture 1건
  cannot_split_reason: 차단 여부가 단일 boolean/receipt 결과이며 외부 전환 실행과 분리되어야 한다.
  external_side_effect_count_expected: 0

- parent_ac: AC-21
  micro_id: AC21-M01-tracked-secrets-and-mail-address-scan
  single_observable_result: git 추적 파일에 비밀 모양, 실제 메일주소, mail raw body canary가 있으면 scanner가 FAIL한다.
  single_failure_reason: tracked runtime config 또는 문서 예시에 실제 mailbox 주소가 남는다.
  rollback_unit: admin scanner mode + mutation fixture tests 제거
  dependencies: scripts/scan-data-exposure.sh existing all-mode pattern
  allowed_files: [scripts/scan-data-exposure.sh, scripts/acceptance-admin-security.sh, .github/workflows/verify.yml, docs/sot/verification-commands.md, docs/sot/mechanism-registry.yaml]
  forbidden_scope: 실제 메일주소/실제 OIDC secret/실제 운영 URL fixture 사용
  red_command: bash scripts/acceptance-admin-security.sh --case tracked-mail-address-canary
  green_command: bash scripts/acceptance-admin-security.sh
  mutation_method: scanner에서 email/raw-mail regex를 제거하면 RED
  production_call_path: pre-commit/pre-push/CI data exposure path
  target_count_method: synthetic canary file 3종(secret/mail/raw-body) 각각 1건 이상
  cannot_split_reason: git 추적 노출이라는 하나의 개인정보/비밀 경계 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-21
  micro_id: AC21-M02-admin-artifact-log-scan
  single_observable_result: apps/admin build/test/log root의 synthetic canary를 scanner가 잡고 root/file 0건이면 exit 2 NOT_RUN이다.
  single_failure_reason: artifact root 하나가 scan 대상에서 빠진다.
  rollback_unit: admin artifact roots scanner + acceptance fixture 제거
  dependencies: admin mode scanner contract from goal line 192
  allowed_files: [scripts/scan-data-exposure.sh, scripts/acceptance-admin-security.sh, apps/admin/tests/unit/data-exposure-roots.test.ts]
  forbidden_scope: 실제 로그 생성, 실제 개인정보, production log location 조회
  red_command: bash scripts/acceptance-admin-security.sh --case artifact-root-canaries
  green_command: bash scripts/scan-data-exposure.sh admin
  mutation_method: .next/test-results/playwright-report/coverage/log root 중 하나 제거하면 RED
  production_call_path: local/CI artifact scanner after admin build/test
  target_count_method: root 5개 각각 synthetic canary 1개, scannedRootCount와 scannedFileCount 검증
  cannot_split_reason: artifact/log 노출 스캔의 단일 관측 결과이며 git tracked 스캔과 경계가 다르다.
  external_side_effect_count_expected: 0

- parent_ac: AC-22
  micro_id: AC22-M01-viewer-aggregate-allowed
  single_observable_result: viewer session은 weekly snapshot aggregate endpoint를 200으로 읽고 민감 필드가 응답에 없다.
  single_failure_reason: viewer aggregate 응답에 raw body/customer/candidate drilldown 필드가 포함된다.
  rollback_unit: viewer aggregate route guard + contract test 제거
  dependencies: weekly snapshot schema, synthetic viewer session helper
  allowed_files: [apps/admin/src/auth/rbac.ts, apps/admin/src/app/api/admin/weekly-snapshots/[periodKey]/route.ts, apps/admin/tests/integration/viewer-aggregate.test.ts]
  forbidden_scope: 민감 drilldown, audit 검증, OIDC claim 검증
  red_command: pnpm --filter admin test -- viewer-aggregate
  green_command: pnpm --filter admin test -- viewer-aggregate
  mutation_method: response serializer에 raw field를 추가하면 RED
  production_call_path: GET /api/admin/weekly-snapshots/{periodKey}?revision=latest
  target_count_method: synthetic viewer 1명 + snapshot 1개 + forbidden field list 길이
  cannot_split_reason: viewer의 허용된 집계 읽기만 검증하는 독립 RBAC 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-22
  micro_id: AC22-M02-viewer-sensitive-drilldown-403
  single_observable_result: viewer가 sensitive rows/drilldown endpoint를 직접 호출하면 403이다.
  single_failure_reason: UI 숨김만 있고 직접 URL 호출이 200이다.
  rollback_unit: sensitive drilldown route guard + integration test 제거
  dependencies: synthetic viewer session, drilldown route skeleton
  allowed_files: [apps/admin/src/auth/rbac.ts, apps/admin/src/app/api/admin/weekly-snapshots/[periodKey]/metrics/[metricKey]/rows/route.ts, apps/admin/tests/integration/viewer-drilldown-403.test.ts]
  forbidden_scope: operator/owner audit, OIDC validation, UI rendering
  red_command: pnpm --filter admin test -- viewer-drilldown-403
  green_command: pnpm --filter admin test -- viewer-drilldown-403
  mutation_method: requiredRole을 viewer로 낮추면 RED
  production_call_path: GET /api/admin/weekly-snapshots/{periodKey}/metrics/{metricKey}/rows
  target_count_method: forbidden viewer request 1건
  cannot_split_reason: 직접 URL 403이라는 단일 권한 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-22
  micro_id: AC22-M03-operator-sensitive-read-audit
  single_observable_result: operator의 sensitive drilldown 성공은 access_audit_events에 outcome=ALLOW 1건을 남긴다.
  single_failure_reason: sensitive read는 200이지만 audit event가 없다.
  rollback_unit: operator audit transaction + integration test 제거
  dependencies: access_audit_events table, synthetic operator session
  allowed_files: [apps/admin/prisma/migrations/*, apps/admin/src/auth/audit.ts, apps/admin/tests/integration/operator-sensitive-audit.test.ts]
  forbidden_scope: owner policy/admin mutations, viewer 403, OIDC claims
  red_command: pnpm --filter admin test -- operator-sensitive-audit
  green_command: pnpm --filter admin test -- operator-sensitive-audit
  mutation_method: audit insert를 no-op 처리하면 RED
  production_call_path: sensitive drilldown read service
  target_count_method: request 1건 후 audit row count delta=1
  cannot_split_reason: operator sensitive read의 허용과 감사 기록은 같은 transaction 성공 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-22
  micro_id: AC22-M04-owner-sensitive-read-audit
  single_observable_result: owner의 sensitive drilldown 성공은 access_audit_events에 outcome=ALLOW 1건을 남긴다.
  single_failure_reason: owner read가 감사 없이 통과한다.
  rollback_unit: owner sensitive audit test + shared audit assertion 제거
  dependencies: access_audit_events table, synthetic owner session
  allowed_files: [apps/admin/src/auth/audit.ts, apps/admin/tests/integration/owner-sensitive-audit.test.ts]
  forbidden_scope: owner user-management mutation, CSRF, bootstrap
  red_command: pnpm --filter admin test -- owner-sensitive-audit
  green_command: pnpm --filter admin test -- owner-sensitive-audit
  mutation_method: owner role branch에서 audit call 제거하면 RED
  production_call_path: sensitive drilldown read service
  target_count_method: request 1건 후 audit row count delta=1
  cannot_split_reason: owner sensitive read 감사라는 단일 audit 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-22
  micro_id: AC22-M05-inactive-session-rejected
  single_observable_result: revoked/expired/inactive user session은 page와 API 접근이 403이고 data read가 0건이다.
  single_failure_reason: inactive session이 snapshot API를 읽는다.
  rollback_unit: session active guard + test fixture 제거
  dependencies: admin_sessions/admin_users schema
  allowed_files: [apps/admin/src/auth/session.ts, apps/admin/src/auth/require-admin.ts, apps/admin/tests/integration/inactive-session.test.ts]
  forbidden_scope: OIDC claim matrix, CSRF, role-specific drilldown
  red_command: pnpm --filter admin test -- inactive-session
  green_command: pnpm --filter admin test -- inactive-session
  mutation_method: active=false check 제거하면 RED
  production_call_path: requireAdminSession middleware for /admin/dashboard and /api/admin/*
  target_count_method: inactive user fixture 1개, rejected API/page requests 2건
  cannot_split_reason: 비활성 세션 거부라는 단일 auth result다.
  external_side_effect_count_expected: 0

- parent_ac: AC-22
  micro_id: AC22-M06-synthetic-tampered-or-expired-token-rejected
  single_observable_result: synthetic tampered session token과 expired session token은 403이며 session rotation/user binding이 생성되지 않는다.
  single_failure_reason: 변조 또는 만료 token이 active session으로 인정된다.
  rollback_unit: session token verifier + unit/integration test 제거
  dependencies: token hash storage, synthetic clock
  allowed_files: [apps/admin/src/auth/session-token.ts, apps/admin/tests/unit/session-token-validation.test.ts]
  forbidden_scope: Google OIDC real token, browser UI, claim-level OIDC matrix
  red_command: pnpm --filter admin test -- session-token-validation
  green_command: pnpm --filter admin test -- session-token-validation
  mutation_method: hash comparison 또는 expires_at check 제거하면 RED
  production_call_path: cookie session validation before admin route handler
  target_count_method: tampered 1건 + expired 1건 + valid control 1건
  cannot_split_reason: 합성 session token validation micro이며 실제 Next runtime auth screen과 분리해야 한다.
  external_side_effect_count_expected: 0

- parent_ac: AC-32
  micro_id: AC32-M01-bootstrap-owner-command-single-pending-grant
  single_observable_result: admin:bootstrap-owner가 synthetic valueconnect.kr email HMAC으로 pending owner grant 1건만 생성한다.
  single_failure_reason: 같은 email로 pending grant가 2건 생성된다.
  rollback_unit: bootstrap CLI + DB unique constraint + test 제거
  dependencies: admin_bootstrap_grants schema
  allowed_files: [apps/admin/prisma/migrations/*, apps/admin/src/auth/bootstrap-owner.ts, apps/admin/tests/integration/bootstrap-owner.test.ts, apps/admin/package.json]
  forbidden_scope: 실제 메일주소, 웹 요청 bootstrap, OIDC login binding
  red_command: pnpm --filter admin test -- bootstrap-owner
  green_command: pnpm --filter admin admin:bootstrap-owner --email owner@example.invalid --dry-run-test
  mutation_method: UNIQUE(email_hmac) WHERE state='pending' 제거하면 RED
  production_call_path: pnpm --filter admin admin:bootstrap-owner --email <synthetic>
  target_count_method: pending grant insert count delta=1, duplicate insert rejected count=1
  cannot_split_reason: 최초 pending grant 생성의 DB/CLI 원자성 한 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-32
  micro_id: AC32-M02-first-oidc-bind-consumes-grant
  single_observable_result: 첫 유효 synthetic OIDC login이 pending grant email_hmac과 subject를 원자 결합하고 OWNER_BOOTSTRAPPED audit event 1건을 남긴다.
  single_failure_reason: grant consumed 없이 admin_user가 생긴다.
  rollback_unit: first-login bind transaction + test 제거
  dependencies: AC32-M01 pending grant, synthetic OIDC validator, access_audit_events
  allowed_files: [apps/admin/src/auth/owner-binding.ts, apps/admin/src/auth/audit.ts, apps/admin/tests/integration/bootstrap-bind.test.ts]
  forbidden_scope: 실제 Google OIDC, browser UI, CSRF mutation
  red_command: pnpm --filter admin test -- bootstrap-bind
  green_command: pnpm --filter admin test -- bootstrap-bind
  mutation_method: transaction에서 audit insert 또는 grant state update 제거하면 RED
  production_call_path: OIDC callback post-validation owner binding service
  target_count_method: pending grant 1건 -> consumed 1건, admin_user 1건, audit 1건
  cannot_split_reason: subject 결합과 grant 소비는 분리하면 중간 상태가 보안 결함이다.
  external_side_effect_count_expected: 0

- parent_ac: AC-32
  micro_id: AC32-M03-active-owner-blocks-bootstrap-rerun
  single_observable_result: 활성 owner가 있으면 bootstrap command 재실행과 두 번째 pending owner grant가 모두 DB/CLI에서 거부된다.
  single_failure_reason: 활성 owner 이후 두 번째 pending owner grant가 생성된다.
  rollback_unit: active-owner guard + constraint test 제거
  dependencies: AC32-M02 active owner fixture
  allowed_files: [apps/admin/src/auth/bootstrap-owner.ts, apps/admin/prisma/migrations/*, apps/admin/tests/integration/bootstrap-rerun-rejected.test.ts]
  forbidden_scope: role management API, OIDC claim matrix
  red_command: pnpm --filter admin test -- bootstrap-rerun-rejected
  green_command: pnpm --filter admin test -- bootstrap-rerun-rejected
  mutation_method: active owner existence check 제거하면 RED
  production_call_path: admin:bootstrap-owner command
  target_count_method: rerun attempts 2건(command + direct DB), created grants delta=0
  cannot_split_reason: bootstrap 재실행 차단이라는 단일 owner lifecycle 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-36
  micro_id: AC36-M01-oidc-issuer-audience-azp-rejected
  single_observable_result: wrong issuer, wrong audience, wrong azp synthetic ID token 각각이 401이고 session/user binding을 만들지 않는다.
  single_failure_reason: issuer/audience/azp 중 하나가 검증 없이 통과한다.
  rollback_unit: OIDC claim verifier + unit test 제거
  dependencies: synthetic ID token factory, no-network OIDC adapter
  allowed_files: [apps/admin/src/auth/oidc/verify-google-token.ts, apps/admin/tests/unit/oidc-issuer-audience-azp.test.ts]
  forbidden_scope: 실제 Google discovery 호출, browser UI, session cookie e2e
  red_command: pnpm --filter admin test -- oidc-issuer-audience-azp
  green_command: pnpm --filter admin test -- oidc-issuer-audience-azp
  mutation_method: 각 claim assertion 하나씩 제거하면 RED
  production_call_path: /api/auth/callback/google token validation service
  target_count_method: invalid cases 3건 + valid control 1건
  cannot_split_reason: issuer/audience/azp는 client identity validation 묶음이며 failure result는 동일하다.
  external_side_effect_count_expected: 0

- parent_ac: AC-36
  micro_id: AC36-M02-oidc-nonce-state-exp-rejected
  single_observable_result: nonce 불일치, state replay, exp 만료 각각이 401이고 session/user binding을 만들지 않는다.
  single_failure_reason: replayed state가 두 번째 session을 만든다.
  rollback_unit: nonce/state/exp verifier + replay store test 제거
  dependencies: synthetic auth transaction store, fake clock
  allowed_files: [apps/admin/src/auth/oidc/auth-state.ts, apps/admin/src/auth/oidc/verify-google-token.ts, apps/admin/tests/unit/oidc-nonce-state-exp.test.ts]
  forbidden_scope: real browser auth page, Google network, RBAC
  red_command: pnpm --filter admin test -- oidc-nonce-state-exp
  green_command: pnpm --filter admin test -- oidc-nonce-state-exp
  mutation_method: state consumed flag check 제거하면 RED
  production_call_path: /api/auth/callback/google callback state validation
  target_count_method: invalid cases 3건 + valid control 1건
  cannot_split_reason: OIDC transaction freshness validation의 단일 합성 token micro다.
  external_side_effect_count_expected: 0

- parent_ac: AC-36
  micro_id: AC36-M03-oidc-email-verified-and-hosted-domain-rejected
  single_observable_result: email_verified=false와 hosted domain 불일치 각각이 401이고 session/user binding을 만들지 않는다.
  single_failure_reason: non-valueconnect synthetic email domain이 로그인된다.
  rollback_unit: domain/email verification rule + test 제거
  dependencies: synthetic token factory
  allowed_files: [apps/admin/src/auth/oidc/verify-google-token.ts, apps/admin/tests/unit/oidc-email-domain.test.ts]
  forbidden_scope: 실제 메일주소, Workspace directory lookup, UI
  red_command: pnpm --filter admin test -- oidc-email-domain
  green_command: pnpm --filter admin test -- oidc-email-domain
  mutation_method: hosted domain check 제거하면 RED
  production_call_path: /api/auth/callback/google token validation service
  target_count_method: invalid cases 2건 + valid synthetic control 1건
  cannot_split_reason: email claim eligibility라는 단일 auth validation 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-36
  micro_id: AC36-M04-next-runtime-auth-screen-playwright
  single_observable_result: 실제 Next runtime에서 /admin/dashboard 비인증 접근은 로그인 화면/redirect를 보이고 synthetic invalid callback은 401 화면/API 응답이며 session cookie가 없다.
  single_failure_reason: 브라우저 런타임에서 invalid auth callback 뒤 admin session cookie가 생긴다.
  rollback_unit: Playwright auth screen spec + runtime route wiring 제거
  dependencies: Next app router, Playwright local server, synthetic callback fixture
  allowed_files: [apps/admin/src/app/admin/dashboard/page.tsx, apps/admin/src/app/api/auth/callback/google/route.ts, apps/admin/tests/e2e/auth-screen.spec.ts, apps/admin/playwright.config.ts]
  forbidden_scope: 실제 Google OIDC redirect, 실제 운영 URL, unit token matrix
  red_command: pnpm --filter admin exec playwright test tests/e2e/auth-screen.spec.ts
  green_command: pnpm --filter admin exec playwright test tests/e2e/auth-screen.spec.ts
  mutation_method: callback error path가 session cookie를 set하도록 바꾸면 RED
  production_call_path: GET /admin/dashboard and GET /api/auth/callback/google under Next runtime
  target_count_method: browser scenarios 2건, cookie count assertion 0
  cannot_split_reason: 실제 Next runtime+Playwright 인증 화면 micro이며 synthetic token validation micro와 의도적으로 분리한다.
  external_side_effect_count_expected: 0

- parent_ac: AC-37
  micro_id: AC37-M01-non-get-wrong-origin-host-403
  single_observable_result: GET이 아닌 admin API는 wrong Origin 또는 wrong Host 각각을 403으로 막고 mutation count=0이다.
  single_failure_reason: wrong Origin POST가 상태를 변경한다.
  rollback_unit: origin/host guard + integration test 제거
  dependencies: ADMIN_ORIGIN synthetic config, mutation endpoint fixture
  allowed_files: [apps/admin/src/auth/request-origin.ts, apps/admin/src/app/api/admin/users/route.ts, apps/admin/tests/integration/admin-origin-host-guard.test.ts]
  forbidden_scope: CSRF, role checks, audit evidence
  red_command: pnpm --filter admin test -- admin-origin-host-guard
  green_command: pnpm --filter admin test -- admin-origin-host-guard
  mutation_method: Origin check 제거하면 RED
  production_call_path: non-GET /api/admin/* request guard
  target_count_method: invalid requests 2건, DB mutation delta=0
  cannot_split_reason: Origin/Host는 same request-boundary validation 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-37
  micro_id: AC37-M02-csrf-missing-or-reused-403
  single_observable_result: CSRF 누락과 재사용 token 각각이 403이고 mutation count=0이다.
  single_failure_reason: reused CSRF token으로 두 번째 mutation이 성공한다.
  rollback_unit: CSRF guard + token store test 제거
  dependencies: session-bound CSRF token, synthetic mutation endpoint
  allowed_files: [apps/admin/src/auth/csrf.ts, apps/admin/src/auth/admin-request-guard.ts, apps/admin/tests/integration/csrf-guard.test.ts]
  forbidden_scope: Origin/Host, role authorization, OIDC
  red_command: pnpm --filter admin test -- csrf-guard
  green_command: pnpm --filter admin test -- csrf-guard
  mutation_method: consumed-token check 제거하면 RED
  production_call_path: non-GET /api/admin/* request guard
  target_count_method: invalid requests 2건 + valid control 1건
  cannot_split_reason: CSRF token lifecycle의 단일 request-boundary 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-37
  micro_id: AC37-M03-insufficient-role-403
  single_observable_result: 부족한 role의 non-GET admin API 요청은 403이고 mutation count=0이다.
  single_failure_reason: viewer/operator가 owner-only mutation을 성공한다.
  rollback_unit: role guard + integration test 제거
  dependencies: RBAC policy map, synthetic users
  allowed_files: [apps/admin/src/auth/rbac.ts, apps/admin/src/auth/admin-request-guard.ts, apps/admin/tests/integration/admin-role-mutation-guard.test.ts]
  forbidden_scope: CSRF, Origin/Host, audit evidence
  red_command: pnpm --filter admin test -- admin-role-mutation-guard
  green_command: pnpm --filter admin test -- admin-role-mutation-guard
  mutation_method: requiredRole map을 viewer로 낮추면 RED
  production_call_path: owner-only non-GET /api/admin/users or /api/admin/policies
  target_count_method: denied role requests 2건, mutation delta=0
  cannot_split_reason: 부족한 role 차단이라는 단일 authorization 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-37
  micro_id: AC37-M04-successful-mutation-audit-evidence
  single_observable_result: 허용된 admin mutation은 요청 전후 HMAC audit evidence 1건을 같은 transaction에 남기고 audit 실패 시 mutation도 실패한다.
  single_failure_reason: mutation은 성공하지만 audit row가 없다.
  rollback_unit: mutation audit transaction + test 제거
  dependencies: access_audit_events table, HMAC key provider synthetic
  allowed_files: [apps/admin/src/auth/audit.ts, apps/admin/src/app/api/admin/users/route.ts, apps/admin/tests/integration/admin-mutation-audit.test.ts]
  forbidden_scope: denied attempt audit, CSRF/Origin/RBAC guards
  red_command: pnpm --filter admin test -- admin-mutation-audit
  green_command: pnpm --filter admin test -- admin-mutation-audit
  mutation_method: audit insert를 transaction 밖으로 빼거나 제거하면 RED
  production_call_path: owner mutation service for user/role/policy changes
  target_count_method: successful mutation 1건, audit row delta=1, forced audit failure mutation delta=0
  cannot_split_reason: 성공 mutation과 감사 증거의 transaction 원자성 한 결과다.
  external_side_effect_count_expected: 0

- parent_ac: AC-37
  micro_id: AC37-M05-denied-sensitive-attempt-audit-evidence
  single_observable_result: 거부된 민감 non-GET 시도는 403과 outcome=DENY audit evidence 1건을 남긴다.
  single_failure_reason: 민감 거부가 audit 없이 403만 반환한다.
  rollback_unit: denied-attempt audit hook + test 제거
  dependencies: request guard ordering, access_audit_events table
  allowed_files: [apps/admin/src/auth/admin-request-guard.ts, apps/admin/src/auth/audit.ts, apps/admin/tests/integration/denied-sensitive-audit.test.ts]
  forbidden_scope: successful mutation audit, viewer GET drilldown, OIDC
  red_command: pnpm --filter admin test -- denied-sensitive-audit
  green_command: pnpm --filter admin test -- denied-sensitive-audit
  mutation_method: deny path audit call 제거하면 RED
  production_call_path: non-GET sensitive admin API guard deny path
  target_count_method: denied request 1건, audit row delta=1, mutation delta=0
  cannot_split_reason: 거부된 민감 시도의 감사 evidence라는 단일 audit 결과다.
  external_side_effect_count_expected: 0
```

### Open Questions

- [ ] `scripts/acceptance-admin-security.sh`, `acceptance-admin-auth.sh`, `acceptance-admin-ui.sh`를 분리할지 하나의 `acceptance-admin-security.sh`로 묶을지 결정 필요 — pre-push/CI/SOT receipt targetCount와 rollback 단위가 달라진다.
- [ ] admin API owner-only mutation fixture의 최소 리소스를 `users`, `policies`, `manual-review` 중 무엇으로 둘지 결정 필요 — AC-37의 production call path와 audit resource_type이 고정되어야 한다.
- [ ] synthetic OIDC token factory를 직접 JWS 검증까지 할지, claim verifier 단위 입력으로 제한할지 결정 필요 — AC-36의 no-network 보장과 실제 `openid-client` adapter 경계가 달라진다.
