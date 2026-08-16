# Admin Weekly Dashboard v6 canonical atomic plan — Phase 0 — 2026-08-17

## 1층 — 결론

이 문서는 실행 바닥을 한 번에 한 결과씩 만드는 Phase 0 계획입니다. 막힌 의존성 뒤의 제품 작업은 시작하지 않습니다.

## 2층 — 판단 근거

각 행은 결과·실패 이유·되돌림을 하나만 갖고, 새 관리자 검사를 등록하는 분할 금지 묶음만 예외로 유지합니다.

## 3층 — 원자 작업

### Phase 0 canonical rows

~~~yaml
- parent_ac: RUN-CONTRACT
  micro_id: P0-01-baseline-and-audited-plan
  single_observable_result: exact source 상태, 기존 RED 1/19, 40 parent mapping, audit PASS hash가 보존된다
  single_failure_reason: 계획 감사 PASS 없이 제품 writer가 시작된다
  rollback_unit: 이 controller plan과 plan-audit evidence commit
  dependencies: [a02a3da]
  allowed_files: [docs/engineering/admin-weekly-dashboard-v6-atomic-research-*-2026-08-17.md, docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md, docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md, docs/engineering/admin-weekly-dashboard-v6-canonical-expansions-2026-08-17.md, docs/engineering/admin-weekly-dashboard-v6-plan-audit-*.md]
  forbidden_scope: [제품 코드, dependency install, main 변경, 외부 호출]
  red_command: fresh auditor가 계획 후보에서 CODEAUDIT SPEC v2를 실행
  green_command: fresh auditor verdict PASS와 계획 PASS 조건 결함 0
  mutation_method: parent AC 하나 또는 필수 필드 하나를 폐기 가능한 계획 사본에서 제거해 audit FAIL 확인
  production_call_path: 사용자 계약 -> controller plan -> writer packet
  target_count_method: parent AC distinct count=40, required field missing count=0
  cannot_split_reason: baseline과 audited plan은 제품 작업 시작 자격이라는 단일 결과
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-02-node-version-pin
  single_observable_result: .node-version이 정확히 24.19.0 한 줄이다
  single_failure_reason: Node pin이 없거나 다른 값이다
  rollback_unit: .node-version + 직접 shell contract test + micro goal
  dependencies: [P0-01 PASS hash]
  allowed_files: [.node-version, scripts/verify/check-admin-foundation.sh, docs/engineering/admin-weekly-dashboard-v6-p0-02-node-version-pin-goal-2026-08-17.md]
  forbidden_scope: [package.json, pnpm, apps/admin, lockfile]
  red_command: bash scripts/verify/check-admin-foundation.sh node-version
  green_command: bash scripts/verify/check-admin-foundation.sh node-version
  mutation_method: disposable clone에서 .node-version을 24.19.1로 바꾼다
  production_call_path: .node-version -> local/CI runtime bootstrap contract
  target_count_method: checked version files=1
  cannot_split_reason: 단일 파일의 단일 exact value
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-03-pnpm-version-pin
  single_observable_result: root packageManager가 정확히 pnpm@11.22.0이다
  single_failure_reason: packageManager가 없거나 다른 값이다
  rollback_unit: root package.json의 packageManager field + 직접 contract test + micro goal
  dependencies: [P0-02 PASS hash]
  allowed_files: [package.json, scripts/verify/check-admin-foundation.sh, docs/engineering/admin-weekly-dashboard-v6-p0-03-pnpm-version-pin-goal-2026-08-17.md]
  forbidden_scope: [workspace declaration, apps/admin, lockfile]
  red_command: bash scripts/verify/check-admin-foundation.sh pnpm-version
  green_command: bash scripts/verify/check-admin-foundation.sh pnpm-version
  mutation_method: disposable clone에서 packageManager를 pnpm@11.22.1로 바꾼다
  production_call_path: package.json packageManager -> Corepack/pnpm invocation
  target_count_method: checked packageManager fields=1
  cannot_split_reason: 단일 field의 단일 exact value
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-04-root-private-workspace
  single_observable_result: root package가 private이고 apps/*만 포함하는 pnpm workspace다
  single_failure_reason: publish 가능하거나 apps/admin이 workspace에서 빠진다
  rollback_unit: package.json private/workspaces + pnpm-workspace.yaml + direct contract test
  dependencies: [P0-03 PASS hash]
  allowed_files: [package.json, pnpm-workspace.yaml, scripts/verify/check-admin-foundation.sh, docs/engineering/admin-weekly-dashboard-v6-p0-04-root-private-workspace-goal-2026-08-17.md]
  forbidden_scope: [apps/admin package, dependencies, lockfile]
  red_command: bash scripts/verify/check-admin-foundation.sh root-workspace
  green_command: bash scripts/verify/check-admin-foundation.sh root-workspace
  mutation_method: disposable clone에서 private를 false로 바꾸거나 workspace package 경로를 제거한다
  production_call_path: pnpm-workspace.yaml -> pnpm workspace discovery
  target_count_method: workspace patterns=1 and root private fields=1
  cannot_split_reason: private root workspace라는 하나의 package-manager boundary
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-04A-generated-artifact-ignore
  single_observable_result: pnpm와 admin build/test가 만드는 local artifact가 git status 대상에서 제외되고 tracked artifact는 0건이다
  single_failure_reason: node_modules 또는 admin build/test artifact가 사용자 변경처럼 worktree에 남거나 추적된다
  rollback_unit: root .gitignore + direct artifact-ignore contract test + micro goal
  dependencies: [P0-04 PASS hash]
  allowed_files: [.gitignore, scripts/verify/check-admin-foundation.sh, docs/engineering/admin-weekly-dashboard-v6-p0-04a-generated-artifact-ignore-goal-2026-08-17.md]
  forbidden_scope: [실제 artifact 생성, 기존 ignore 규칙 삭제, source file ignore]
  red_command: bash scripts/verify/check-admin-foundation.sh artifact-ignore
  green_command: bash scripts/verify/check-admin-foundation.sh artifact-ignore
  mutation_method: disposable clone에서 node_modules 또는 apps/admin/.next ignore 항목을 제거한다
  production_call_path: package/build/test outputs -> git status boundary
  target_count_method: required ignore patterns exact count and tracked forbidden artifacts=0
  cannot_split_reason: 생성물로 인한 worktree 오염을 막는 하나의 repository boundary
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-05-admin-exact-package-contract
  single_observable_result: apps/admin package가 goal의 모든 npm package exact version을 범위 기호 없이 선언한다
  single_failure_reason: 필수 package 누락·추가·버전 drift가 있다
  rollback_unit: apps/admin/package.json + version contract test
  dependencies: [P0-04A PASS hash]
  allowed_files: [apps/admin/package.json, scripts/verify/check-admin-foundation.sh, docs/engineering/admin-weekly-dashboard-v6-p0-05-admin-exact-package-contract-goal-2026-08-17.md]
  forbidden_scope: [install, lockfile, source route, goal 밖 dependency]
  red_command: bash scripts/verify/check-admin-foundation.sh admin-package-versions
  green_command: bash scripts/verify/check-admin-foundation.sh admin-package-versions
  mutation_method: disposable clone에서 package 하나의 patch를 바꾸거나 범위 기호를 붙인다
  production_call_path: apps/admin/package.json -> pnpm resolver
  target_count_method: expected dependency keys exact count and mismatch count=0
  cannot_split_reason: 한 package manifest의 exact dependency set equality
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-06-lockfile-resolution
  single_observable_result: 고정 runtime에서 frozen install이 성공하고 lockfile importer/package targetCount가 0보다 크다
  single_failure_reason: exact version이 해석되지 않거나 lockfile이 manifest와 다르다
  rollback_unit: pnpm-lock.yaml + resolution receipt + micro goal
  dependencies: [P0-05 PASS hash, Node 24.19.0 available, pnpm 11.22.0 available]
  allowed_files: [pnpm-lock.yaml, docs/engineering/admin-weekly-dashboard-v6-p0-06-lockfile-resolution-goal-2026-08-17.md]
  forbidden_scope: [version substitution, package.json 변경, goal 밖 dependency]
  red_command: pnpm install --frozen-lockfile
  green_command: pnpm install --frozen-lockfile
  mutation_method: MINIMAL_GREEN에서 pnpm install --lockfile-only로 생성한 뒤 disposable clone에서 lockfile importer version을 manifest와 다르게 바꾼다
  production_call_path: exact manifests -> pnpm resolver -> pnpm-lock.yaml
  target_count_method: workspace importers>0 and resolved packages>0
  cannot_split_reason: manifests 전체와 lockfile 해석은 하나의 resolution 결과
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-07-minimal-start-route
  single_observable_result: local Next runtime에서 GET /admin/dashboard가 응답 1건을 낸다
  single_failure_reason: route 또는 start script가 없어 runtime 응답이 없다
  rollback_unit: minimal Next config/root layout/dashboard route/start script + runtime test
  dependencies: [P0-06 PASS hash]
  allowed_files: [apps/admin/next.config.ts, apps/admin/tsconfig.json, apps/admin/src/app/layout.tsx, apps/admin/src/app/admin/dashboard/page.tsx, apps/admin/package.json, apps/admin/tests/e2e/minimal-start.spec.ts, apps/admin/playwright.config.ts, docs/engineering/admin-weekly-dashboard-v6-p0-07-minimal-start-route-goal-2026-08-17.md]
  forbidden_scope: [dashboard metrics, auth, DB, connector, legacy asset, visual parity]
  red_command: pnpm --filter admin exec playwright test tests/e2e/minimal-start.spec.ts
  green_command: pnpm --filter admin exec playwright test tests/e2e/minimal-start.spec.ts
  mutation_method: disposable clone에서 dashboard route export를 제거한다
  production_call_path: Next start -> /admin/dashboard -> page component -> HTTP response
  target_count_method: Playwright requests=1 and responses=1
  cannot_split_reason: 실제 runtime route와 직접 browser test가 하나의 invariant
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-08-lint-target
  single_observable_result: eslint . --max-warnings=0이 admin 파일 1개 이상을 검사해 성공한다
  single_failure_reason: lint script가 없거나 대상 0건 또는 warning 허용이다
  rollback_unit: eslint config/script + one lint-target canary test
  dependencies: [P0-07 PASS hash]
  allowed_files: [apps/admin/eslint.config.mjs, apps/admin/package.json, apps/admin/tests/unit/foundation/lint-target.test.ts, docs/engineering/admin-weekly-dashboard-v6-p0-08-lint-target-goal-2026-08-17.md]
  forbidden_scope: [typecheck, test runner, build]
  red_command: pnpm --filter admin lint
  green_command: pnpm --filter admin lint
  mutation_method: disposable clone에서 lint target을 존재하지 않는 directory로 바꾼다
  production_call_path: package script -> ESLint -> admin source files
  target_count_method: enumerated lint input file count>0
  cannot_split_reason: lint command and nonzero target proof are one result
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-09-typecheck-target
  single_observable_result: strict TypeScript 검사 대상이 1개 이상이고 오류 없이 끝난다
  single_failure_reason: strict가 꺼지거나 include가 비어 검사 대상이 0이다
  rollback_unit: tsconfig typecheck script + direct target-count test
  dependencies: [P0-08 PASS hash]
  allowed_files: [apps/admin/tsconfig.json, apps/admin/package.json, apps/admin/tests/unit/foundation/typecheck-target.test.ts, docs/engineering/admin-weekly-dashboard-v6-p0-09-typecheck-target-goal-2026-08-17.md]
  forbidden_scope: [domain types, DB, build]
  red_command: pnpm --filter admin typecheck
  green_command: pnpm --filter admin typecheck
  mutation_method: disposable clone에서 strict를 false로 바꾼다
  production_call_path: package script -> tsc noEmit -> admin TypeScript inputs
  target_count_method: tsc listFilesOnly admin-owned target count>0
  cannot_split_reason: strict compiler command and nonzero target proof are one result
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-10-unit-test-target
  single_observable_result: Vitest가 runtime import를 포함한 unit case 1개 이상을 실행한다
  single_failure_reason: test 0건·skip·text-only 검사로 초록이 된다
  rollback_unit: Vitest config/script + foundation runtime test
  dependencies: [P0-09 PASS hash]
  allowed_files: [apps/admin/vitest.config.ts, apps/admin/package.json, apps/admin/tests/unit/foundation/runtime-import.test.ts, docs/engineering/admin-weekly-dashboard-v6-p0-10-unit-test-target-goal-2026-08-17.md]
  forbidden_scope: [domain feature, DB integration, e2e]
  red_command: pnpm --filter admin test
  green_command: pnpm --filter admin test
  mutation_method: disposable clone에서 imported production value를 반대로 바꾼다
  production_call_path: package test -> Vitest -> production runtime import
  target_count_method: executed test cases>0 and runtime imported modules>0
  cannot_split_reason: 한 unit runner의 실제 실행 증명
  external_side_effect_count_expected: 0

- parent_ac: AC-01
  micro_id: P0-11-build-target
  single_observable_result: Next build가 성공하고 .next 파일 targetCount가 0보다 크다
  single_failure_reason: build no-op 또는 route 누락으로 실제 산출물이 없다
  rollback_unit: build script/config + build artifact assertion
  dependencies: [P0-10 PASS hash]
  allowed_files: [apps/admin/package.json, apps/admin/next.config.ts, apps/admin/tests/unit/foundation/build-target.test.ts, docs/engineering/admin-weekly-dashboard-v6-p0-11-build-target-goal-2026-08-17.md]
  forbidden_scope: [deployment, production origin, metrics UI]
  red_command: pnpm --filter admin build
  green_command: pnpm --filter admin build
  mutation_method: disposable clone에서 build script를 no-op으로 바꾼다
  production_call_path: package build -> Next compiler -> apps/admin/.next
  target_count_method: .next regular files>0
  cannot_split_reason: build command과 실제 산출물은 하나의 결과
  external_side_effect_count_expected: 0

- parent_ac: AC-02
  micro_id: P0-12-foundation-receipt
  single_observable_result: foundation gate가 정확히 한 ADMIN_GATE_JSON과 targetCount>0을 출력한다
  single_failure_reason: receipt 누락·복수·잘못된 verdict·0-target이다
  rollback_unit: foundation gate receipt parser/emitter + mutation test
  dependencies: [P0-11 PASS hash]
  allowed_files: [scripts/verify/check-admin-foundation.sh, scripts/verify/fixtures/admin-foundation/**, docs/engineering/admin-weekly-dashboard-v6-p0-12-foundation-receipt-goal-2026-08-17.md]
  forbidden_scope: [acceptance script 등록, CI, SOT, registry]
  red_command: bash scripts/verify/check-admin-foundation.sh receipt
  green_command: bash scripts/verify/check-admin-foundation.sh receipt
  mutation_method: disposable clone에서 receipt targetCount를 0으로 바꾼다
  production_call_path: foundation checks -> receipt emitter -> caller parser
  target_count_method: receipt lines=1 and targetCount>0
  cannot_split_reason: 한 gate 영수증의 shape와 nonzero 판정
  external_side_effect_count_expected: 0

- parent_ac: AC-02
  micro_id: P0-13-admin-acceptance-registration-bundle
  single_observable_result: 다섯 admin acceptance 실제 집합이 pre-push glob, CI 고정 목록, verification SOT, mechanism registry와 정확히 같다
  single_failure_reason: 한 검사라도 로컬·CI·두 명부 중 한 곳에서 빠진다
  rollback_unit: 다섯 acceptance + CI admin entries + verification table + mechanism entries + set-equality mutation
  dependencies: [P0-12 PASS hash]
  allowed_files: [scripts/acceptance-admin-foundation.sh, scripts/acceptance-admin-domain.sh, scripts/acceptance-admin-db.sh, scripts/acceptance-admin-connectors.sh, scripts/acceptance-admin-ui.sh, .github/workflows/verify.yml, docs/sot/verification-commands.md, docs/sot/mechanism-registry.yaml, docs/engineering/admin-weekly-dashboard-v6-p0-13-admin-acceptance-registration-bundle-goal-2026-08-17.md]
  forbidden_scope: [hooks/pre-push rewrite, existing acceptance weakening, product feature]
  red_command: bash scripts/acceptance-admin-foundation.sh
  green_command: bash scripts/acceptance-admin-foundation.sh && bash scripts/acceptance-verify-ac-m.sh
  mutation_method: disposable clone에서 CI admin run line 하나를 제거한다
  production_call_path: acceptance files -> pre-push glob and CI fixed runs -> SOT/registry checker
  target_count_method: script set size=5 and symmetric difference=0
  cannot_split_reason: 사용자 지정 분할 금지 묶음
  external_side_effect_count_expected: 0

- parent_ac: AC-02
  micro_id: P0-14-admin-zero-target-guard
  single_observable_result: admin gate targetCount=0 또는 receipt 누락이면 foundation aggregate가 NOT_RUN/FAIL이다
  single_failure_reason: 실행 대상 없는 gate가 PASS로 집계된다
  rollback_unit: admin receipt aggregate parser + zero/missing receipt mutation cases
  dependencies: [P0-13 PASS hash]
  allowed_files: [scripts/acceptance-admin-foundation.sh, scripts/verify/fixtures/admin-foundation/**, docs/engineering/admin-weekly-dashboard-v6-p0-14-admin-zero-target-guard-goal-2026-08-17.md]
  forbidden_scope: [CI/SOT registration changes, product feature]
  red_command: bash scripts/acceptance-admin-foundation.sh
  green_command: bash scripts/acceptance-admin-foundation.sh
  mutation_method: disposable clone에서 한 admin gate receipt를 targetCount=0으로 바꾼다
  production_call_path: child admin gate receipt -> foundation aggregate verdict
  target_count_method: zero-target mutations detected>=1 and missing-receipt mutations detected>=1
  cannot_split_reason: false PASS를 막는 aggregate verdict 하나
  external_side_effect_count_expected: 0

- parent_ac: AC-39
  micro_id: P0-15-build-root-canary
  single_observable_result: admin scanner가 .next 합성 개인정보 canary 1건을 FAIL로 잡는다
  single_failure_reason: .next root가 scanner 대상에서 빠진다
  rollback_unit: admin scan .next root + one mutation fixture
  dependencies: [P0-14 PASS hash, P0-11 build artifact]
  allowed_files: [scripts/scan-data-exposure.sh, scripts/verify/fixtures/admin-exposure/**, docs/engineering/admin-weekly-dashboard-v6-p0-15-build-root-canary-goal-2026-08-17.md]
  forbidden_scope: [다른 artifact root, 실제 개인정보]
  red_command: bash scripts/scan-data-exposure.sh admin
  green_command: bash scripts/scan-data-exposure.sh admin
  mutation_method: disposable clone에서 admin root 목록의 .next 항목을 제거한다
  production_call_path: build output -> admin exposure scanner
  target_count_method: scanned .next files>0 and canary hits=1
  cannot_split_reason: 한 artifact root의 한 탐지 결과
  external_side_effect_count_expected: 0

- parent_ac: AC-39
  micro_id: P0-16-test-results-root-canary
  single_observable_result: admin scanner가 test-results canary 1건을 FAIL로 잡는다
  single_failure_reason: test-results root가 scanner 대상에서 빠진다
  rollback_unit: test-results root + mutation fixture
  dependencies: [P0-15 PASS hash]
  allowed_files: [scripts/scan-data-exposure.sh, scripts/verify/fixtures/admin-exposure/**, docs/engineering/admin-weekly-dashboard-v6-p0-16-test-results-root-canary-goal-2026-08-17.md]
  forbidden_scope: [다른 roots, 실제 개인정보]
  red_command: bash scripts/scan-data-exposure.sh admin
  green_command: bash scripts/scan-data-exposure.sh admin
  mutation_method: disposable clone에서 test-results root를 제거한다
  production_call_path: test output -> admin exposure scanner
  target_count_method: scanned test-results files>0 and canary hits=1
  cannot_split_reason: 한 artifact root의 한 탐지 결과
  external_side_effect_count_expected: 0

- parent_ac: AC-39
  micro_id: P0-17-playwright-report-root-canary
  single_observable_result: admin scanner가 playwright-report canary 1건을 FAIL로 잡는다
  single_failure_reason: playwright-report root가 scanner 대상에서 빠진다
  rollback_unit: playwright-report root + mutation fixture
  dependencies: [P0-16 PASS hash]
  allowed_files: [scripts/scan-data-exposure.sh, scripts/verify/fixtures/admin-exposure/**, docs/engineering/admin-weekly-dashboard-v6-p0-17-playwright-report-root-canary-goal-2026-08-17.md]
  forbidden_scope: [다른 roots, 실제 개인정보]
  red_command: bash scripts/scan-data-exposure.sh admin
  green_command: bash scripts/scan-data-exposure.sh admin
  mutation_method: disposable clone에서 playwright-report root를 제거한다
  production_call_path: Playwright output -> admin exposure scanner
  target_count_method: scanned report files>0 and canary hits=1
  cannot_split_reason: 한 artifact root의 한 탐지 결과
  external_side_effect_count_expected: 0

- parent_ac: AC-39
  micro_id: P0-18-coverage-root-canary
  single_observable_result: admin scanner가 coverage canary 1건을 FAIL로 잡는다
  single_failure_reason: coverage root가 scanner 대상에서 빠진다
  rollback_unit: coverage root + mutation fixture
  dependencies: [P0-17 PASS hash]
  allowed_files: [scripts/scan-data-exposure.sh, scripts/verify/fixtures/admin-exposure/**, docs/engineering/admin-weekly-dashboard-v6-p0-18-coverage-root-canary-goal-2026-08-17.md]
  forbidden_scope: [다른 roots, 실제 개인정보]
  red_command: bash scripts/scan-data-exposure.sh admin
  green_command: bash scripts/scan-data-exposure.sh admin
  mutation_method: disposable clone에서 coverage root를 제거한다
  production_call_path: coverage output -> admin exposure scanner
  target_count_method: scanned coverage files>0 and canary hits=1
  cannot_split_reason: 한 artifact root의 한 탐지 결과
  external_side_effect_count_expected: 0

- parent_ac: AC-39
  micro_id: P0-19-admin-log-root-canary
  single_observable_result: 고정된 local admin log root canary 1건을 scanner가 FAIL로 잡는다
  single_failure_reason: log root가 미정이거나 scanner 대상에서 빠진다
  rollback_unit: log root contract + scanner root + mutation fixture
  dependencies: [P0-18 PASS hash]
  allowed_files: [contracts/admin-weekly-dashboard/runtime-config.schema.json, scripts/scan-data-exposure.sh, scripts/verify/fixtures/admin-exposure/**, docs/engineering/admin-weekly-dashboard-v6-p0-19-admin-log-root-canary-goal-2026-08-17.md]
  forbidden_scope: [외부 logging service, 실제 production log]
  red_command: BLOCKED until log root is fixed by contract
  green_command: bash scripts/scan-data-exposure.sh admin
  mutation_method: disposable clone에서 fixed log root를 scanner 목록에서 제거한다
  production_call_path: local admin logger -> fixed artifact root -> scanner
  target_count_method: scanned log files>0 and canary hits=1
  cannot_split_reason: log 위치 계약과 그 위치 탐지는 호출 경로 하나
  external_side_effect_count_expected: 0

- parent_ac: AC-03
  micro_id: P0-20-runtime-dependency-cleanroom
  single_observable_result: runtime dependency graph의 v4/v5 path/module/asset/DB endpoint hit가 0이고 targetCount>0이다
  single_failure_reason: runtime source가 형제 세대 실행물에 의존한다
  rollback_unit: cleanroom runtime graph test + deny pattern reuse
  dependencies: [P0-18 PASS hash, P0-11 PASS hash]
  allowed_files: [apps/admin/src/**, apps/admin/tests/unit/foundation/runtime-cleanroom.test.ts, contracts/cleanroom-deny-patterns.txt, docs/engineering/admin-weekly-dashboard-v6-p0-20-runtime-dependency-cleanroom-goal-2026-08-17.md]
  forbidden_scope: [build artifact scan, legacy import, deny pattern weakening]
  red_command: pnpm --filter admin test -- runtime-cleanroom
  green_command: pnpm --filter admin test -- runtime-cleanroom
  mutation_method: disposable clone에서 production runtime import에 Valuehire_v5 경로를 추가한다
  production_call_path: admin production entrypoints -> runtime import graph
  target_count_method: graph nodes>0 and deny hits=0
  cannot_split_reason: runtime graph라는 하나의 cleanroom boundary
  external_side_effect_count_expected: 0

- parent_ac: AC-03
  micro_id: P0-21-build-output-cleanroom
  single_observable_result: .next build output의 v4/v5 path/module/asset/DB endpoint hit가 0이고 targetCount>0이다
  single_failure_reason: build artifact가 legacy reference를 포함한다
  rollback_unit: build output scanner + direct build artifact mutation
  dependencies: [P0-20 PASS hash, P0-11 PASS hash]
  allowed_files: [apps/admin/tests/unit/foundation/build-cleanroom.test.ts, contracts/cleanroom-deny-patterns.txt, docs/engineering/admin-weekly-dashboard-v6-p0-21-build-output-cleanroom-goal-2026-08-17.md]
  forbidden_scope: [runtime graph test, legacy import]
  red_command: pnpm --filter admin build && pnpm --filter admin test -- build-cleanroom
  green_command: pnpm --filter admin build && pnpm --filter admin test -- build-cleanroom
  mutation_method: disposable clone에서 production route에 legacy marker를 넣고 다시 build한다
  production_call_path: admin source -> Next build -> .next scan
  target_count_method: scanned build files>0 and deny hits=0
  cannot_split_reason: build output이라는 하나의 cleanroom boundary
  external_side_effect_count_expected: 0

- parent_ac: AC-39
  micro_id: P0-22-admin-scan-registration-bundle
  single_observable_result: scan-data-exposure admin 명령이 다섯 acceptance 중 소유 gate, pre-push, CI, verification SOT, mechanism registry에서 실제 실행된다
  single_failure_reason: admin scan이 한 실행 경계나 명부에서 빠진다
  rollback_unit: scan registration bundle + CI deletion mutation
  dependencies: [P0-15 PASS hash, P0-16 PASS hash, P0-17 PASS hash, P0-18 PASS hash, P0-19 PASS hash, P0-20 PASS hash, P0-21 PASS hash]
  allowed_files: [scripts/acceptance-admin-foundation.sh, .github/workflows/verify.yml, docs/sot/verification-commands.md, docs/sot/mechanism-registry.yaml, docs/engineering/admin-weekly-dashboard-v6-p0-22-admin-scan-registration-bundle-goal-2026-08-17.md]
  forbidden_scope: [hooks/pre-push rewrite, existing all-mode removal]
  red_command: bash scripts/acceptance-admin-foundation.sh
  green_command: bash scripts/acceptance-admin-foundation.sh && bash scripts/acceptance-verify-ac-m.sh
  mutation_method: disposable clone에서 CI admin scan run line을 제거한다
  production_call_path: scanner -> foundation acceptance -> pre-push/CI -> SOT registry checker
  target_count_method: active execution edges expected count and symmetric difference=0
  cannot_split_reason: 사용자 지정 acceptance+CI+SOT+registry+mutation 분할 금지 묶음
  external_side_effect_count_expected: 0
~~~

→ Phase 0은 사용자가 지정한 최소 순서를 그대로 펼쳤고, install 전에 생성물 ignore 작업만 추가했습니다. P0-05는 React 타입 패키지 exact version이 없어 차단입니다. P0-19는 정확한 local log root가 목표에 없어 차단입니다. P0-20과 P0-21은 log root와 독립이므로 P0-18의 마지막 검증 기록에서 시작할 수 있지만 P0-22와 Phase 0 경계 완료는 P0-19 없이는 통과하지 않습니다.
