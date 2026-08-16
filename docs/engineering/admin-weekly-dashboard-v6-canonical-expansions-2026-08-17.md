# Admin Weekly Dashboard v6 canonical atomic expansions — 2026-08-17

## 1층 — 결론

이 문서는 여러 실패 이유를 섞은 조사행을 한 실패 이유씩 다시 나눈 계획이며, 합쳐진 조사행은 실행 대상에서 뺍니다.

## 2층 — 판단 근거

YAML merge key를 해석한 뒤 각 child row는 사용자 지정 15개 필드를 모두 가집니다. `supersedes`에 든 조사행은 실행하지 않습니다.

## 3층 — 치환 행

## Superseded and retained rows

- supersedes: AC17-M1-api-source-fail-null-not-zero, AC17-M2-api-partial-collection-fail-partial
- supersedes: AC21-M01-tracked-secrets-and-mail-address-scan, AC21-M02-admin-artifact-log-scan
- supersedes: AC22-M05-inactive-session-rejected, AC22-M06-synthetic-tampered-or-expired-token-rejected
- supersedes: AC31-M1-live-readonly-mailbox-evidence-receipt
- supersedes: AC36-M01-oidc-issuer-audience-azp-rejected, AC36-M02-oidc-nonce-state-exp-rejected, AC36-M03-oidc-email-verified-and-hosted-domain-rejected
- supersedes: AC36-M04-next-runtime-auth-screen-playwright
- supersedes: AC37-M01-non-get-wrong-origin-host-403, AC37-M02-csrf-missing-or-reused-403
- supersedes: AC38-M1-active-write-key-exactly-one, AC38-M2-retired-destroyed-key-use-rejected
- retained without change: AC17-M3-ui-runtime-source-fail-not-rendered-as-zero, AC22-M01-viewer-aggregate-allowed, AC22-M02-viewer-sensitive-drilldown-403, AC22-M03-operator-sensitive-read-audit, AC22-M04-owner-sensitive-read-audit, AC37-M03-insufficient-role-403, AC37-M04-successful-mutation-audit-evidence, AC37-M05-denied-sensitive-attempt-audit-evidence, AC38-M3-key-state-projection-event-consistency, AC38-M4-destroyed-requires-provider-receipt

## Canonical replacement rows

~~~yaml
x-ac17-source: &ac17-source
  parent_ac: AC-17
  rollback_unit: source status mapper + direct API test + micro goal
  dependencies: [AC-10/11/12 synthetic receipt schema PASS hashes]
  allowed_files: [apps/admin/src/domain/metrics/source-status.ts, apps/admin/src/domain/metrics/metric-assembler.ts, apps/admin/src/app/api/admin/weekly-snapshots/[periodKey]/route.ts, apps/admin/tests/integration/weekly-metrics-source-status.test.ts, scripts/acceptance-admin-domain.sh, docs/engineering/admin-weekly-dashboard-v6-ac17-*-goal-2026-08-17.md]
  forbidden_scope: [live connectors, UI, ClickUp write, numeric fallback]
  red_command: pnpm --filter admin test -- --run tests/integration/weekly-metrics-source-status.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/weekly-metrics-source-status.test.ts && bash scripts/acceptance-admin-domain.sh
  production_call_path: source receipt -> source-status.ts -> metric-assembler.ts -> weekly snapshot API
  target_count_method: matching source-status fixture count=1
  cannot_split_reason: 한 source 상태가 API의 단일 null/status/reason 결과를 만든다
  external_side_effect_count_expected: 0
- <<: *ac17-source
  micro_id: AC17-M1F-api-fail-null
  single_observable_result: FAIL source는 value:null, status:FAIL, reason non-null이다
  single_failure_reason: FAIL이 숫자 0 또는 reason 없는 응답이 된다
  mutation_method: disposable clone에서 FAIL branch를 value:0으로 바꾼다
- <<: *ac17-source
  micro_id: AC17-M1N-api-not-run-null
  single_observable_result: NOT_RUN source는 value:null, status:NOT_RUN, reason non-null이다
  single_failure_reason: NOT_RUN이 숫자 0 또는 reason 없는 응답이 된다
  mutation_method: disposable clone에서 NOT_RUN branch를 value:0으로 바꾼다
- <<: *ac17-source
  micro_id: AC17-M2-api-partial-null
  single_observable_result: PARTIAL source는 value:null, status:FAIL, completeness:PARTIAL, reason non-null이다
  single_failure_reason: PARTIAL이 COMPLETE/PASS 또는 숫자 값으로 노출된다
  mutation_method: disposable clone에서 PARTIAL branch를 COMPLETE로 바꾼다

x-ac21-canary: &ac21-canary
  parent_ac: AC-21
  rollback_unit: 한 data-class canary + scanner rule + direct mutation test + micro goal
  dependencies: [P0-15~P0-19 root canary PASS hashes]
  allowed_files: [scripts/scan-data-exposure.sh, scripts/verify/fixtures/admin-exposure/**, scripts/acceptance-admin-foundation.sh, docs/engineering/admin-weekly-dashboard-v6-ac21-*-goal-2026-08-17.md]
  forbidden_scope: [actual secret, actual email address, actual mail body, external log service]
  red_command: bash scripts/scan-data-exposure.sh admin
  green_command: bash scripts/scan-data-exposure.sh admin
  production_call_path: tracked/admin artifact roots -> exposure scanner -> foundation receipt
  target_count_method: one synthetic data-class canary per canonical root; roots scanned>0
  cannot_split_reason: 한 금지 데이터 종류의 탐지 결과 하나
  external_side_effect_count_expected: 0
- <<: *ac21-canary
  micro_id: AC21-M01-secret-pattern-canary
  single_observable_result: tracked와 admin artifact root의 합성 secret canary를 scanner가 FAIL로 잡는다
  single_failure_reason: secret-shaped value가 scan을 통과한다
  mutation_method: disposable clone에서 secret rule 하나를 제거한다
- <<: *ac21-canary
  micro_id: AC21-M02-mailbox-address-canary
  single_observable_result: tracked와 admin artifact root의 합성 mailbox-address canary를 scanner가 FAIL로 잡는다
  single_failure_reason: mailbox address가 scan을 통과한다
  mutation_method: disposable clone에서 mailbox-address rule을 제거한다
- <<: *ac21-canary
  micro_id: AC21-M03-raw-mail-body-canary
  single_observable_result: tracked와 admin artifact root의 합성 raw-mail-body canary를 scanner가 FAIL로 잡는다
  single_failure_reason: raw mail body marker가 scan을 통과한다
  mutation_method: disposable clone에서 raw-mail-body rule을 제거한다

x-ac22-session: &ac22-session
  parent_ac: AC-22
  rollback_unit: 한 session rejection guard + direct integration test + micro goal
  dependencies: [admin_users/admin_sessions DB PASS hashes]
  allowed_files: [apps/admin/src/auth/session.ts, apps/admin/src/auth/session-token.ts, apps/admin/src/auth/require-admin.ts, apps/admin/tests/integration/session-rejection.test.ts, scripts/acceptance-admin-domain.sh, docs/engineering/admin-weekly-dashboard-v6-ac22-*-goal-2026-08-17.md]
  forbidden_scope: [Google live token, UI, CSRF, role-specific read]
  red_command: pnpm --filter admin test -- --run tests/integration/session-rejection.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/session-rejection.test.ts && bash scripts/acceptance-admin-domain.sh
  production_call_path: admin cookie -> session verifier -> requireAdminSession -> page/API guard
  target_count_method: selected rejection fixture=1 and protected data reads=0
  cannot_split_reason: 한 session invalidity reason의 403 결과 하나
  external_side_effect_count_expected: 0
- <<: *ac22-session
  micro_id: AC22-M05A-inactive-user-rejected
  single_observable_result: inactive admin user session은 403이고 protected data read가 0건이다
  single_failure_reason: inactive user가 protected data를 읽는다
  mutation_method: disposable clone에서 user active guard를 제거한다
- <<: *ac22-session
  micro_id: AC22-M05B-revoked-session-rejected
  single_observable_result: revoked session은 403이고 protected data read가 0건이다
  single_failure_reason: revoked_at이 있는 session이 통과한다
  mutation_method: disposable clone에서 revoked_at guard를 제거한다
- <<: *ac22-session
  micro_id: AC22-M05C-expired-session-rejected
  single_observable_result: expired session은 403이고 protected data read가 0건이다
  single_failure_reason: expires_at이 지난 session이 통과한다
  mutation_method: disposable clone에서 expiration guard를 제거한다
- <<: *ac22-session
  micro_id: AC22-M06-tampered-token-rejected
  single_observable_result: tampered session token은 403이고 protected data read가 0건이다
  single_failure_reason: token hash 불일치가 통과한다
  mutation_method: disposable clone에서 constant-time hash comparison을 무조건 true로 바꾼다

x-ac31-mailbox: &ac31-mailbox
  parent_ac: AC-31
  rollback_unit: 한 symbolic mailbox 합성 receipt + direct connector test + micro goal
  dependencies: [AC-10 synthetic Gmail collector PASS hash, AC-21 exposure PASS hashes]
  allowed_files: [apps/admin/src/integrations/gmail/**, apps/admin/src/jobs/gmail-readonly-collect.ts, apps/admin/tests/integration/gmail-mailbox-receipt.test.ts, scripts/acceptance-admin-connectors.sh, docs/engineering/admin-weekly-dashboard-v6-ac31-*-goal-2026-08-17.md]
  forbidden_scope: [Gmail live read/write, actual mailbox address, raw body, Calendar live, ClickUp call]
  red_command: pnpm --filter admin test -- --run tests/integration/gmail-mailbox-receipt.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/gmail-mailbox-receipt.test.ts && bash scripts/acceptance-admin-connectors.sh
  production_call_path: synthetic readonly client -> gmail-readonly-collect.ts -> per-mailbox receipt
  target_count_method: selected symbolic mailbox receipts=1 and synthetic adapter calls>0 and network calls=0
  cannot_split_reason: 한 symbolic mailbox의 evidence receipt 결과 하나
  external_side_effect_count_expected: 0
- <<: *ac31-mailbox
  micro_id: AC31-M01-mailbox-ref-1-synthetic-receipt
  single_observable_result: MAILBOX_REF_1 합성 receipt에 qualified count, zero reason, MIME distribution, verdict, completeness, evidence가 있다
  single_failure_reason: MAILBOX_REF_1의 필수 evidence가 하나 빠진다
  mutation_method: disposable clone에서 MAILBOX_REF_1 receipt의 MIME distribution을 제거한다
- <<: *ac31-mailbox
  micro_id: AC31-M02-mailbox-ref-2-synthetic-receipt
  single_observable_result: MAILBOX_REF_2 합성 receipt에 qualified count, zero reason, MIME distribution, verdict, completeness, evidence가 있다
  single_failure_reason: MAILBOX_REF_2의 필수 evidence가 하나 빠진다
  mutation_method: disposable clone에서 MAILBOX_REF_2 receipt의 completeness를 제거한다
- <<: *ac31-mailbox
  micro_id: AC31-M03-mailbox-ref-3-synthetic-receipt
  single_observable_result: MAILBOX_REF_3 합성 receipt에 qualified count, zero reason, MIME distribution, verdict, completeness, evidence가 있다
  single_failure_reason: MAILBOX_REF_3의 필수 evidence가 하나 빠진다
  mutation_method: disposable clone에서 MAILBOX_REF_3 receipt의 verdict를 제거한다
- <<: *ac31-mailbox
  micro_id: AC31-M04-mailbox-ref-4-synthetic-receipt
  single_observable_result: MAILBOX_REF_4 합성 receipt에 qualified count, zero reason, MIME distribution, verdict, completeness, evidence가 있다
  single_failure_reason: MAILBOX_REF_4의 필수 evidence가 하나 빠진다
  mutation_method: disposable clone에서 MAILBOX_REF_4 receipt의 evidence를 제거한다
- parent_ac: AC-31
  micro_id: AC31-M05-exactly-four-synthetic-aggregate
  single_observable_result: aggregate receipt는 서로 다른 symbolic mailbox ref 정확히 4개가 모두 있어야 PASS다
  single_failure_reason: mailbox evidence 하나가 빠져도 overall PASS가 된다
  rollback_unit: aggregate completeness guard + direct connector test + micro goal
  dependencies: [AC31-M01~M04 PASS hashes]
  allowed_files: [apps/admin/src/jobs/gmail-readonly-collect.ts, apps/admin/tests/integration/gmail-mailbox-aggregate.test.ts, scripts/acceptance-admin-connectors.sh, docs/engineering/admin-weekly-dashboard-v6-ac31-m05-goal-2026-08-17.md]
  forbidden_scope: [live mailbox, actual mailbox address, external call]
  red_command: pnpm --filter admin test -- --run tests/integration/gmail-mailbox-aggregate.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/gmail-mailbox-aggregate.test.ts && bash scripts/acceptance-admin-connectors.sh
  mutation_method: disposable clone에서 aggregate required count를 3으로 낮춘다
  production_call_path: four per-mailbox receipts -> aggregate completeness guard -> connector receipt
  target_count_method: distinct symbolic mailbox refs=4 and missingEvidenceCount=0
  cannot_split_reason: exactly-four completeness라는 집계 결과 하나
  external_side_effect_count_expected: 0
- parent_ac: AC-31
  micro_id: AC31-M06-live-readonly
  single_observable_result: 이번 실행의 live mailbox 상태는 LIVE_NOT_RUN이고 PASS count에 포함되지 않는다
  single_failure_reason: live evidence 없이 AC-31 또는 제품 완료를 주장한다
  rollback_unit: live-status receipt declaration + micro goal
  dependencies: [retention/access/delete policy, Gmail readonly credentials]
  allowed_files: [docs/engineering/admin-weekly-dashboard-v6-ac31-m06-goal-2026-08-17.md]
  forbidden_scope: [Gmail/Calendar/ClickUp call, credential use, live PASS claim]
  red_command: bash scripts/acceptance-admin-connectors.sh --live-readonly-gmail
  green_command: BLOCKED_EXTERNAL_AUTHORITY; no GREEN in this execution
  mutation_method: disposable receipt에서 LIVE_NOT_RUN을 PASS로 바꾸면 phase audit FAIL
  production_call_path: future authorized Gmail readonly adapter -> live evidence receipt
  target_count_method: live connector calls=0 and live PASS claims=0
  cannot_split_reason: 외부 권한이 필요한 live 증거 상태 하나
  external_side_effect_count_expected: 0

x-ac36-claim: &ac36-claim
  parent_ac: AC-36
  rollback_unit: 한 OIDC claim guard + direct no-network test + micro goal
  dependencies: [synthetic signed ID-token factory PASS hash]
  allowed_files: [apps/admin/src/auth/oidc/verify-google-token.ts, apps/admin/src/auth/oidc/auth-state.ts, apps/admin/tests/unit/oidc-claim-validation.test.ts, scripts/acceptance-admin-domain.sh, docs/engineering/admin-weekly-dashboard-v6-ac36-*-goal-2026-08-17.md]
  forbidden_scope: [Google network, real identity, UI, RBAC]
  red_command: pnpm --filter admin test -- --run tests/unit/oidc-claim-validation.test.ts
  green_command: pnpm --filter admin test -- --run tests/unit/oidc-claim-validation.test.ts && bash scripts/acceptance-admin-domain.sh
  production_call_path: auth callback -> OIDC verifier/state store -> no session/user binding on rejection
  target_count_method: selected invalid claim case=1, valid control=1, created bindings=0
  cannot_split_reason: 한 OIDC 검증 실패 원인의 401 결과 하나
  external_side_effect_count_expected: 0
- <<: *ac36-claim
  micro_id: AC36-M01A-wrong-issuer
  single_observable_result: wrong issuer token은 401이고 binding을 만들지 않는다
  single_failure_reason: issuer 불일치가 통과한다
  mutation_method: disposable clone에서 issuer assertion을 제거한다
- <<: *ac36-claim
  micro_id: AC36-M01B-wrong-audience
  single_observable_result: wrong audience token은 401이고 binding을 만들지 않는다
  single_failure_reason: audience 불일치가 통과한다
  mutation_method: disposable clone에서 audience assertion을 제거한다
- <<: *ac36-claim
  micro_id: AC36-M01C-wrong-azp
  single_observable_result: wrong azp token은 401이고 binding을 만들지 않는다
  single_failure_reason: azp 불일치가 통과한다
  mutation_method: disposable clone에서 azp assertion을 제거한다
- <<: *ac36-claim
  micro_id: AC36-M02A-nonce-mismatch
  single_observable_result: nonce mismatch token은 401이고 binding을 만들지 않는다
  single_failure_reason: nonce 불일치가 통과한다
  mutation_method: disposable clone에서 nonce assertion을 제거한다
- <<: *ac36-claim
  micro_id: AC36-M02B-state-replay
  single_observable_result: 재사용 state callback은 401이고 두 번째 binding을 만들지 않는다
  single_failure_reason: consumed state가 다시 통과한다
  mutation_method: disposable clone에서 consumed-state guard를 제거한다
- <<: *ac36-claim
  micro_id: AC36-M02C-expired-token
  single_observable_result: exp 만료 token은 401이고 binding을 만들지 않는다
  single_failure_reason: 만료 token이 통과한다
  mutation_method: disposable clone에서 exp assertion을 제거한다
- <<: *ac36-claim
  micro_id: AC36-M03A-email-not-verified
  single_observable_result: email_verified=false token은 401이고 binding을 만들지 않는다
  single_failure_reason: 미검증 email claim이 통과한다
  mutation_method: disposable clone에서 email_verified assertion을 제거한다
- <<: *ac36-claim
  micro_id: AC36-M03B-hosted-domain-mismatch
  single_observable_result: hosted domain 불일치 token은 401이고 binding을 만들지 않는다
  single_failure_reason: 허용되지 않은 hosted domain이 통과한다
  mutation_method: disposable clone에서 hosted-domain assertion을 제거한다

x-ac36-runtime: &ac36-runtime
  parent_ac: AC-36
  rollback_unit: 한 auth runtime guard + Next route + Playwright direct test + micro goal
  dependencies: [canonical dependency overlay]
  allowed_files: [apps/admin/src/app/admin/dashboard/page.tsx, apps/admin/src/app/api/auth/callback/google/route.ts, apps/admin/tests/e2e/auth-screen.spec.ts, apps/admin/playwright.config.ts, scripts/acceptance-admin-ui.sh, docs/engineering/admin-weekly-dashboard-v6-ac36-runtime-*-goal-2026-08-17.md]
  forbidden_scope: [Google live redirect, production origin, claim unit matrix, other dashboard UI]
  red_command: pnpm --filter admin exec playwright test tests/e2e/auth-screen.spec.ts
  green_command: pnpm --filter admin exec playwright test tests/e2e/auth-screen.spec.ts && bash scripts/acceptance-admin-ui.sh
  production_call_path: local Next runtime -> auth route boundary -> browser-visible response
  target_count_method: selected Playwright auth scenario=1 and local Next requests>0
  cannot_split_reason: 한 runtime auth 실패 원인과 직접 browser 결과를 묶는 분할 금지 invariant
  external_side_effect_count_expected: 0
- <<: *ac36-runtime
  micro_id: AC36-M04A-unauthenticated-dashboard-runtime
  single_observable_result: 실제 local Next runtime에서 비인증 GET /admin/dashboard는 로그인 화면 또는 인증 redirect를 반환한다
  single_failure_reason: 비인증 browser가 보호된 dashboard 내용을 받는다
  mutation_method: disposable clone에서 dashboard auth guard를 제거한다
- <<: *ac36-runtime
  micro_id: AC36-M04B-invalid-callback-no-session
  single_observable_result: 실제 local Next runtime에서 합성 invalid callback은 401이고 session cookie를 만들지 않는다
  single_failure_reason: invalid callback이 admin session cookie를 만든다
  mutation_method: disposable clone에서 callback rejection branch가 session cookie를 쓰게 바꾼다

x-ac37-deny: &ac37-deny
  parent_ac: AC-37
  rollback_unit: 한 non-GET request guard + direct integration test + micro goal
  dependencies: [synthetic owner mutation endpoint PASS hash]
  allowed_files: [apps/admin/src/auth/request-origin.ts, apps/admin/src/auth/csrf.ts, apps/admin/src/auth/admin-request-guard.ts, apps/admin/src/auth/rbac.ts, apps/admin/src/app/api/admin/users/route.ts, apps/admin/tests/integration/admin-request-guard.test.ts, scripts/acceptance-admin-domain.sh, docs/engineering/admin-weekly-dashboard-v6-ac37-*-goal-2026-08-17.md]
  forbidden_scope: [external origin, audit evidence, OIDC, live data]
  red_command: pnpm --filter admin test -- --run tests/integration/admin-request-guard.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/admin-request-guard.test.ts && bash scripts/acceptance-admin-domain.sh
  production_call_path: non-GET admin API -> request guard -> mutation service
  target_count_method: selected denied request=1 and mutation delta=0
  cannot_split_reason: 한 request guard 실패 원인의 403 결과 하나
  external_side_effect_count_expected: 0
- <<: *ac37-deny
  micro_id: AC37-M01A-wrong-origin
  single_observable_result: wrong Origin non-GET 요청은 403이고 mutation 0건이다
  single_failure_reason: wrong Origin 요청이 상태를 바꾼다
  mutation_method: disposable clone에서 Origin guard를 제거한다
- <<: *ac37-deny
  micro_id: AC37-M01B-wrong-host
  single_observable_result: wrong Host non-GET 요청은 403이고 mutation 0건이다
  single_failure_reason: wrong Host 요청이 상태를 바꾼다
  mutation_method: disposable clone에서 Host guard를 제거한다
- <<: *ac37-deny
  micro_id: AC37-M02A-missing-csrf
  single_observable_result: CSRF 누락 non-GET 요청은 403이고 mutation 0건이다
  single_failure_reason: CSRF 없는 요청이 상태를 바꾼다
  mutation_method: disposable clone에서 CSRF presence guard를 제거한다
- <<: *ac37-deny
  micro_id: AC37-M02B-reused-csrf
  single_observable_result: 재사용 CSRF non-GET 요청은 403이고 두 번째 mutation은 0건이다
  single_failure_reason: consumed CSRF가 다시 상태를 바꾼다
  mutation_method: disposable clone에서 consumed-token guard를 제거한다

x-ac38-key: &ac38-key
  parent_ac: AC-38
  rollback_unit: 한 DB key-state invariant + migration + PostgreSQL 17.11 integration test + micro goal
  dependencies: [cryptographic_key_versions schema PASS hash, PostgreSQL 17.11 digest PASS hash]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/crypto/**, apps/admin/tests/integration/crypto/**, scripts/acceptance-admin-db.sh, docs/engineering/admin-weekly-dashboard-v6-ac38-*-goal-2026-08-17.md]
  forbidden_scope: [real KMS, payload encryption expansion, in-memory-only test]
  red_command: pnpm --filter admin test -- --run tests/integration/crypto/key-state-invariants.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/crypto/key-state-invariants.test.ts && bash scripts/acceptance-admin-db.sh
  production_call_path: DB key lifecycle/selection procedure -> claim/compare/encrypt caller
  target_count_method: selected PostgreSQL rejection fixture=1
  cannot_split_reason: 한 DB 제약과 실제 PostgreSQL 통합시험은 분할 금지 묶음
  external_side_effect_count_expected: 0
- <<: *ac38-key
  micro_id: AC38-M1A-active-zero-rejected
  single_observable_result: write-capable key selection은 목적별 ACTIVE 0개를 거부한다
  single_failure_reason: ACTIVE 0개에서 임의 fallback key가 선택된다
  mutation_method: disposable clone에서 zero-cardinality guard를 제거한다
- <<: *ac38-key
  micro_id: AC38-M1B-active-multiple-rejected
  single_observable_result: DB는 목적별 ACTIVE 복수 key를 거부한다
  single_failure_reason: 같은 purpose에 ACTIVE key 둘이 저장된다
  mutation_method: disposable clone에서 partial unique constraint를 제거한다
- <<: *ac38-key
  micro_id: AC38-M2A-retired-use-rejected
  single_observable_result: RETIRED key는 claim/compare/encrypt procedure에서 거부된다
  single_failure_reason: RETIRED key가 write-capable procedure에 사용된다
  mutation_method: disposable clone에서 RETIRED state guard를 제거한다
- <<: *ac38-key
  micro_id: AC38-M2B-destroyed-use-rejected
  single_observable_result: DESTROYED key는 claim/compare/encrypt procedure에서 거부된다
  single_failure_reason: DESTROYED key가 write-capable procedure에 사용된다
  mutation_method: disposable clone에서 DESTROYED state guard를 제거한다
~~~

→ 각 child는 anchor의 공통 경계와 자기 결과·실패·변조를 합쳐 한 원자 행이 됩니다.

## Blocked rows

AC31-M06은 external authority가 생기기 전까지 LIVE_NOT_RUN입니다. 다른 replacement row도 dependency가 PASS하지 않으면 시작하지 않습니다. AC13 충돌과 AC07 dependency gap은 이 파일로 해소하지 않습니다.
