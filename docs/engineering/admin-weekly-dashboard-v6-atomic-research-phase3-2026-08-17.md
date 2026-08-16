# Admin Weekly Dashboard v6 atomic research — phase3 — 2026-08-17

이 파일은 fresh read-only 조사자의 원문 증거입니다. 정본 계획이 아니며 controller의 수정 규칙과 독립 계획 감사를 우선합니다.

## Metis Analysis: Phase 3 Atomic Decomposition

결과: 읽기 전용으로만 조사했고 파일 수정·생성·커밋·하위 에이전트는 하지 않았습니다. 기준 HEAD는 `a02a3da8f36e22997028b0d620de4e7e970f76d8`로 일치했습니다. 저장소 루트에는 물리적 `AGENTS.md`가 없고, goal 문서가 “주입 AGENTS > docs/sot > goal” 우선순위를 명시합니다(`docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:82-93`).

### Evidence Anchors

- SOT 3상태/0건 금지: `docs/sot/coding-principles.md:18`, `docs/sot/coding-principles.md:35`, `docs/sot/verification-commands.md:56`
- 새 acceptance는 CI·SOT·registry 동시 등록 필요: `docs/sot/verification-commands.md:43`, `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:175-190`
- pre-push glob 자동 수집: `hooks/pre-push:110-165`, 계약은 `docs/sot/hook-contracts.md:30-39`
- 현재 admin 제품/계약 파일 없음: `README.md:5-7`, `rg --files` 결과에 `apps/admin`, `contracts/admin-weekly-dashboard`, `scripts/acceptance-admin-*` 없음
- ClickUp 쓰기/응답 유실 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:789-878`
- Phase 3 POST/PUT 0: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:1099-1123`
- metric/API 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:926-1001`
- Gmail 수집 증거 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:367-423`, AC-31 `:1190`

### Micro Candidates

```yaml
- parent_ac: AC-10
  micro_id: AC10-M1-synthetic-response-loss-no-second-post
  single_observable_result: POST 성공 후 응답 유실 fixture에서 상태가 UNKNOWN_OUTCOME/RECONCILING으로만 진행되고 readback 전 fake write adapter POST 호출 수가 1회 이하, 두 번째 POST 호출 수가 0임.
  single_failure_reason: UNKNOWN_OUTCOME 상태에서 readback 없이 POST adapter가 다시 호출됨.
  rollback_unit: clickup write state machine + reconciliation synthetic contract test
  dependencies: Phase 2 DB ledger/state transition; fake ClickUp write/read adapter; AC-09 write_attempt uniqueness
  allowed_files: apps/admin/src/integrations/clickup/**, apps/admin/src/jobs/**, apps/admin/src/domain/clickup/**, apps/admin/tests/integration/**, scripts/acceptance-admin-connectors.sh
  forbidden_scope: Gmail/Calendar live reads; ClickUp live POST/PUT; Phase 4 LiveWriteApproval consumption; UI rendering
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-response-loss.test.ts && bash scripts/acceptance-admin-connectors.sh
  green_command: pnpm --filter admin test -- --run tests/integration/clickup-response-loss.test.ts && bash scripts/acceptance-admin-connectors.sh
  mutation_method: mutate UNKNOWN_OUTCOME handler to call createTask again before readback; expected RED with fake POST count > 1
  production_call_path: apps/admin/src/jobs/clickup-registration-runner.ts -> apps/admin/src/integrations/clickup/write-adapter.ts
  target_count_method: fake adapter receipt counts postCalls, putCalls, readbackCalls, registrationTargets; targetCount = response-loss cases >= 1
  cannot_split_reason: The observable is exactly the no-second-POST guarantee before readback; splitting state and adapter count would allow a fake state-only pass.
  external_side_effect_count_expected: 0

- parent_ac: AC-11
  micro_id: AC11-M1-synthetic-readback-zero-manual-review
  single_observable_result: response-loss reconciliation readback returns 0 matching tasks, target moves to MANUAL_REVIEW and fake POST/PUT retry count remains 0.
  single_failure_reason: 0-match readback is treated as “safe to create” or retried blindly.
  rollback_unit: readback result classifier + test fixture for zero match
  dependencies: AC10-M1 reconciliation path; fake ClickUp read adapter
  allowed_files: apps/admin/src/integrations/clickup/**, apps/admin/src/domain/clickup/**, apps/admin/tests/integration/**, scripts/acceptance-admin-connectors.sh
  forbidden_scope: ClickUp live writes; UI; Gmail ingestion changes
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-readback-ambiguity.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/clickup-readback-ambiguity.test.ts && bash scripts/acceptance-admin-connectors.sh
  mutation_method: mutate 0-match branch to enqueue POST retry; expected RED on manualReview=false or postCalls>0
  production_call_path: apps/admin/src/jobs/clickup-reconcile-runner.ts -> apps/admin/src/integrations/clickup/read-adapter.ts
  target_count_method: targetCount = zero-match reconciliation cases executed; receipt includes postCalls=0, putCalls=0
  cannot_split_reason: 0-match handling has one failure reason distinct from multi-match ambiguity.
  external_side_effect_count_expected: 0

- parent_ac: AC-11
  micro_id: AC11-M2-synthetic-readback-multiple-manual-review
  single_observable_result: response-loss reconciliation readback returns 2+ matching tasks, target moves to MANUAL_REVIEW and fake POST/PUT retry count remains 0.
  single_failure_reason: ambiguous multi-match readback is auto-selected or retried blindly.
  rollback_unit: readback ambiguity classifier + multi-match fixture
  dependencies: AC10-M1 reconciliation path; fake ClickUp read adapter
  allowed_files: apps/admin/src/integrations/clickup/**, apps/admin/src/domain/clickup/**, apps/admin/tests/integration/**, scripts/acceptance-admin-connectors.sh
  forbidden_scope: ClickUp live writes; UI; Gmail ingestion changes
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-readback-ambiguity.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/clickup-readback-ambiguity.test.ts && bash scripts/acceptance-admin-connectors.sh
  mutation_method: mutate multi-match branch to choose first task; expected RED on manualReview=false
  production_call_path: apps/admin/src/jobs/clickup-reconcile-runner.ts -> apps/admin/src/integrations/clickup/read-adapter.ts
  target_count_method: targetCount = multi-match reconciliation cases executed; receipt includes ambiguityCount >= 2
  cannot_split_reason: Multi-match is a separate failure mode from 0-match because “choose first” can pass zero-match tests.
  external_side_effect_count_expected: 0

- parent_ac: AC-12
  micro_id: AC12-M1-synthetic-schema-fingerprint-mismatch-blocks-write
  single_observable_result: ClickUp list/status/custom-field fingerprint mismatch causes verdict FAIL and fake write adapter POST/PUT calls are 0.
  single_failure_reason: write path ignores or recomputes around mismatched fingerprint and calls adapter.
  rollback_unit: ClickUp schema fingerprint verifier + prewrite guard
  dependencies: runtime config ClickUp list/status contract; fake ClickUp list read adapter
  allowed_files: apps/admin/src/integrations/clickup/**, apps/admin/src/contracts/**, apps/admin/tests/integration/**, contracts/admin-weekly-dashboard/runtime-config.schema.json, scripts/acceptance-admin-connectors.sh
  forbidden_scope: ClickUp live writes; Gmail/Calendar; DB schema expansion beyond needed state record
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-fingerprint.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/clickup-fingerprint.test.ts && bash scripts/acceptance-admin-connectors.sh
  mutation_method: alter expected status or custom-field fingerprint in fixture; expected RED if postCalls != 0 or verdict != FAIL
  production_call_path: apps/admin/src/jobs/clickup-registration-runner.ts -> apps/admin/src/integrations/clickup/schema-fingerprint.ts -> write-adapter.ts
  target_count_method: targetCount = fingerprint mismatch fixtures executed; adapter spy postCalls+putCalls must equal 0
  cannot_split_reason: The acceptance result is the guard’s external-call count, not just fingerprint calculation.
  external_side_effect_count_expected: 0

- parent_ac: AC-17
  micro_id: AC17-M1-api-source-fail-null-not-zero
  single_observable_result: API metric sourced from failed/NOT_RUN source returns value:null, status FAIL or NOT_RUN, reason non-null, and never value:0.
  single_failure_reason: source failure is coerced to numeric 0 or reason omitted.
  rollback_unit: metric assembler + weekly snapshot API contract test
  dependencies: weekly snapshot schema; source_watermarks; metric_source_requirements
  allowed_files: apps/admin/src/domain/metrics/**, apps/admin/src/app/api/admin/weekly-snapshots/**, apps/admin/tests/integration/**, contracts/admin-weekly-dashboard/weekly-snapshot-v1.schema.json, scripts/acceptance-admin-domain.sh
  forbidden_scope: ClickUp write adapter; live Gmail/Calendar/ClickUp; visual UI parity
  red_command: pnpm --filter admin test -- --run tests/integration/weekly-metrics-source-failure.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/weekly-metrics-source-failure.test.ts && bash scripts/acceptance-admin-domain.sh
  mutation_method: mutate metric fallback to `value: 0`; expected schema/contract test RED
  production_call_path: apps/admin/src/app/api/admin/weekly-snapshots/[periodKey]/route.ts -> apps/admin/src/domain/metrics/metric-assembler.ts
  target_count_method: targetCount = failed and NOT_RUN source fixtures, minimum 2; each checked for value === null
  cannot_split_reason: FAIL/NOT_RUN share the same “not zero” invariant and reason requirement at API boundary.
  external_side_effect_count_expected: 0

- parent_ac: AC-17
  micro_id: AC17-M2-api-partial-collection-fail-partial
  single_observable_result: partial source collection returns status FAIL, completeness PARTIAL, value:null, reason non-null.
  single_failure_reason: partial collection is exposed as PASS/COMPLETE or numeric partial count.
  rollback_unit: source completeness mapper + API metric fixture
  dependencies: Gmail/ClickUp/discovery collection receipts with completeness field
  allowed_files: apps/admin/src/domain/metrics/**, apps/admin/src/app/api/admin/weekly-snapshots/**, apps/admin/tests/integration/**, scripts/acceptance-admin-domain.sh
  forbidden_scope: live connector execution; ClickUp writes; Playwright UI
  red_command: pnpm --filter admin test -- --run tests/integration/weekly-metrics-partial-source.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/weekly-metrics-partial-source.test.ts && bash scripts/acceptance-admin-domain.sh
  mutation_method: drop page-2 failure fixture and return COMPLETE; expected RED on completeness/status
  production_call_path: apps/admin/src/domain/metrics/source-status.ts -> metric-assembler.ts
  target_count_method: targetCount = partial collection fixtures executed, minimum 1
  cannot_split_reason: The single failure reason is partial-as-complete; it must be tested separately from full source failure.
  external_side_effect_count_expected: 0

- parent_ac: AC-17
  micro_id: AC17-M3-ui-runtime-source-fail-not-rendered-as-zero
  single_observable_result: running admin UI renders FAIL/NOT_RUN/PARTIAL states as status/reason text and no failed-source card displays “0” as a normal metric.
  single_failure_reason: UI formats null failed metrics as numeric 0 or hides the reason/completeness.
  rollback_unit: dashboard metric card rendering + Playwright e2e fixture
  dependencies: AC17-M1/M2 API fixtures; local Next runtime; Playwright
  allowed_files: apps/admin/src/app/admin/dashboard/**, apps/admin/src/ui/**, apps/admin/tests/e2e/**, scripts/acceptance-admin-ui.sh
  forbidden_scope: live Gmail/Calendar/ClickUp; ClickUp POST/PUT; visual parity against legacy screenshot
  red_command: pnpm --filter admin test:e2e -- tests/e2e/dashboard-source-failure.spec.ts
  green_command: pnpm --filter admin build && pnpm --filter admin test:e2e -- tests/e2e/dashboard-source-failure.spec.ts && bash scripts/acceptance-admin-ui.sh
  mutation_method: mutate MetricCard formatter to `value ?? 0`; expected Playwright RED
  production_call_path: apps/admin/src/app/admin/dashboard/page.tsx -> apps/admin/src/ui/MetricCard.tsx
  target_count_method: Playwright counts rendered failed/partial cards and normal-zero cards; targetCount = cards under test >= 2
  cannot_split_reason: UI behavior requires real runtime + browser; API tests cannot prove rendered zero absence.
  external_side_effect_count_expected: 0

- parent_ac: AC-18
  micro_id: AC18-M1-api-all-metrics-provenance-fields
  single_observable_result: every API metric has contractVersion, computedAt, typed watermark/provenance source, rowCount, watermarkId, and drilldownHref.
  single_failure_reason: any metric omits required provenance/contract fields or uses an untyped shared cursor.
  rollback_unit: weekly-snapshot schema + API serializer test
  dependencies: weekly-snapshot-v1 schema; metric source requirements; route implementation
  allowed_files: contracts/admin-weekly-dashboard/weekly-snapshot-v1.schema.json, apps/admin/src/domain/metrics/**, apps/admin/src/app/api/admin/weekly-snapshots/**, apps/admin/tests/integration/**, scripts/acceptance-admin-domain.sh
  forbidden_scope: UI rendering; connector live calls; ClickUp writes
  red_command: pnpm --filter admin test -- --run tests/integration/weekly-snapshot-api-contract.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/weekly-snapshot-api-contract.test.ts && bash scripts/acceptance-admin-domain.sh
  mutation_method: remove drilldownHref or rowCount from one metric fixture; expected RED naming the metric key
  production_call_path: apps/admin/src/app/api/admin/weekly-snapshots/[periodKey]/route.ts -> apps/admin/src/domain/metrics/serialize-snapshot.ts
  target_count_method: iterate all metric keys in snapshot payload; targetCount = metric count and must be > 0
  cannot_split_reason: AC says “all metrics”; splitting by metric risks missing new metrics unless serializer-level loop owns the invariant.
  external_side_effect_count_expected: 0

- parent_ac: AC-19
  micro_id: AC19-M1-build-output-clickup-write-disabled-without-owner-approval
  single_observable_result: Phase 0-3 build artifact and runtime wiring contain no reachable ClickUp POST/PUT execution path without valid owner approval; synthetic connector reports LIVE_NOT_RUN and postCalls/putCalls 0.
  single_failure_reason: write adapter is importable/reachable from scheduled job or API path when approval is absent.
  rollback_unit: ClickUp write capability gate + build artifact scanner
  dependencies: LiveWriteApproval domain type; build output; acceptance-admin-connectors
  allowed_files: apps/admin/src/integrations/clickup/**, apps/admin/src/jobs/**, apps/admin/src/domain/approvals/**, apps/admin/tests/unit/**, scripts/acceptance-admin-connectors.sh
  forbidden_scope: issuing real approval; ClickUp live POST/PUT; Phase 4 one-task write flow
  red_command: pnpm --filter admin build && bash scripts/acceptance-admin-connectors.sh --assert-no-live-write-path
  green_command: pnpm --filter admin build && bash scripts/acceptance-admin-connectors.sh --assert-no-live-write-path
  mutation_method: export/call write-adapter from no-approval runner or include fetch POST path in build; expected RED on reachableWritePath or postCalls>0
  production_call_path: apps/admin/src/jobs/clickup-registration-runner.ts -> apps/admin/src/domain/approvals/assert-live-write-approval.ts -> apps/admin/src/integrations/clickup/write-adapter.ts
  target_count_method: static build scan count of POST/PUT-capable call sites plus runtime fake adapter call count; targetCount >= 1 scanned bundle/module
  cannot_split_reason: Structural disablement must be proven at build/runtime boundary together; unit-only approval checks can leave a reachable production import.
  external_side_effect_count_expected: 0

- parent_ac: AC-24
  micro_id: AC24-M1-synthetic-description-body-only-readback
  single_observable_result: ClickUp description readback contains exactly canonical business body text and 0 characters from title, message id, auto-registration phrase, quote, signature, attachment, or tracking metadata.
  single_failure_reason: any non-business-body metadata appears in description readback.
  rollback_unit: description composer + readback comparator fixture
  dependencies: body extractor selection from AC-07/08; fake ClickUp readback
  allowed_files: apps/admin/src/domain/mail-body/**, apps/admin/src/integrations/clickup/**, apps/admin/tests/integration/**, scripts/acceptance-admin-connectors.sh
  forbidden_scope: live ClickUp writes; Gmail live body reads; UI
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-description-readback.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/clickup-description-readback.test.ts && bash scripts/acceptance-admin-connectors.sh
  mutation_method: append message id or “자동등록” to description fixture; expected RED per goal mutation `:1229`
  production_call_path: apps/admin/src/integrations/clickup/description.ts -> apps/admin/src/integrations/clickup/readback.ts
  target_count_method: canonical body length and forbidden substring corpus count; targetCount = forbidden metadata cases >= 1 and body fixture count >= 1
  cannot_split_reason: “0글자 metadata” is one observable body-only invariant; individual metadata types are mutation cases, not rollback units.
  external_side_effect_count_expected: 0

- parent_ac: AC-24
  micro_id: AC24-M2-synthetic-description-canonical-sha-match
  single_observable_result: readback canonicalization normalizes only line endings/trailing line spaces and observed_body_sha256 equals selected business body sha256.
  single_failure_reason: comparator accepts semantically changed body or rejects allowed line-ending/trailing-space normalization.
  rollback_unit: canonical body hash comparator + fixture
  dependencies: selected gmail_body_extractions businessBodyHmac/body payload ref
  allowed_files: apps/admin/src/integrations/clickup/readback.ts, apps/admin/src/domain/body-canonicalization.ts, apps/admin/tests/unit/**, scripts/acceptance-admin-connectors.sh
  forbidden_scope: description composition changes outside canonicalization; live writes
  red_command: pnpm --filter admin test -- --run tests/unit/clickup-description-canonical-hash.test.ts
  green_command: pnpm --filter admin test -- --run tests/unit/clickup-description-canonical-hash.test.ts && bash scripts/acceptance-admin-connectors.sh
  mutation_method: change comparator to trim all whitespace or ignore body suffix; expected RED on sha mismatch fixture
  production_call_path: apps/admin/src/integrations/clickup/readback.ts -> apps/admin/src/domain/body-canonicalization.ts
  target_count_method: targetCount = canonicalization fixture pairs; include allowed-normalization and forbidden-change cases
  cannot_split_reason: Hash equality and canonicalization rules are one comparator rollback unit.
  external_side_effect_count_expected: 0

- parent_ac: AC-25
  micro_id: AC25-M1-synthetic-existing-task-page-failure-blocks-write
  single_observable_result: if any existing-task page read fails, connector verdict is FAIL, completeness PARTIAL, “existing task 없음” is not emitted, and fake POST/PUT calls are 0.
  single_failure_reason: failed page is treated as empty result and write proceeds.
  rollback_unit: ClickUp existing task pagination reader + prewrite block test
  dependencies: fake ClickUp paginated read adapter; AC12 prewrite guard
  allowed_files: apps/admin/src/integrations/clickup/**, apps/admin/src/jobs/**, apps/admin/tests/integration/**, scripts/acceptance-admin-connectors.sh
  forbidden_scope: live ClickUp writes; UI; Gmail live
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-existing-task-pagination.test.ts
  green_command: pnpm --filter admin test -- --run tests/integration/clickup-existing-task-pagination.test.ts && bash scripts/acceptance-admin-connectors.sh
  mutation_method: catch page read error and return empty list; expected RED on verdict/completeness/postCalls
  production_call_path: apps/admin/src/integrations/clickup/existing-task-reader.ts -> apps/admin/src/jobs/clickup-registration-runner.ts
  target_count_method: targetCount = paginated read fixtures; record failedPageCount >= 1 and postCalls+putCalls == 0
  cannot_split_reason: The failure reason is one pagination failure being converted to empty; block-write is the required observable consequence.
  external_side_effect_count_expected: 0

- parent_ac: AC-31
  micro_id: AC31-M1-live-readonly-mailbox-evidence-receipt
  single_observable_result: Phase 3 read-only run receipt has exactly four mailbox refs, each with qualified count, zero-count reason distribution when applicable, MIME distribution, verdict, completeness, and evidence; if any mailbox evidence is missing, overall PASS is false.
  single_failure_reason: one mailbox has no evidence or targetCount < 4 but overall PASS is reported.
  rollback_unit: Gmail read-only collector receipt + acceptance-admin-connectors live-read lane
  dependencies: retention/access policy; Gmail readonly delegated auth; runtime config mailbox directory; explicit meetingStart or Calendar NOT_RUN
  allowed_files: apps/admin/src/integrations/gmail/**, apps/admin/src/jobs/**, apps/admin/src/domain/mail-qualification/**, apps/admin/tests/integration/**, scripts/acceptance-admin-connectors.sh
  forbidden_scope: gmail.modify/mail send; Calendar live unless configured; ClickUp POST/PUT; storing plaintext mailbox addresses in git/logs
  red_command: bash scripts/acceptance-admin-connectors.sh --live-readonly-gmail --expect-live-status LIVE_NOT_RUN
  green_command: bash scripts/acceptance-admin-connectors.sh --live-readonly-gmail
  mutation_method: remove one mailbox ref from receipt or mark missing evidence as PASS; expected RED with targetCount=3 or missingEvidenceCount>0
  production_call_path: apps/admin/src/jobs/gmail-readonly-collect.ts -> apps/admin/src/integrations/gmail/readonly-client.ts -> apps/admin/src/domain/mail-qualification/qualify-message.ts
  target_count_method: count distinct configured mailbox refs in receipt; must equal 4 (`sangmokang`, `kcs`, `julian`, `rogan`) and each mailbox targetCount/message evidence is explicit; current run status LIVE_NOT_RUN
  cannot_split_reason: AC-31’s pass/fail depends on the four-mailbox completeness aggregate; per-mailbox tests cannot prove “one missing blocks overall PASS.”
  external_side_effect_count_expected: 0
```

### Connector Split Status

- Synthetic connector contract tests: required for AC-10, AC-11, AC-12, AC-24, AC-25, and the no-write part of AC-19.
- Live Gmail/Calendar/ClickUp status for this execution: `LIVE_NOT_RUN`.
- ClickUp live POST/PUT expected and allowed in this execution: `0`.
- UI/runtime+Playwright separated: AC17-M3 only. AC17-M1/M2 remain API/domain; AC18 is API-only.

### Open Questions

- [ ] Which Phase 3 acceptance script owns these receipts: one `scripts/acceptance-admin-connectors.sh` with sublanes or separate `acceptance-admin-domain/ui/connectors` receipts? — Goal lists five scripts, but the per-AC receipt ownership affects CI registration and rollback units.
- [ ] Should AC-19’s “build 산출물의 POST·PUT 경로 구조적 비활성화” be enforced by static bundle scanning, runtime capability injection tests, or both as mandatory? — The contract implies structural proof, but the exact scanner boundary is not yet specified.
- [ ] For AC-31 live-readonly GREEN, what exact storage location is allowed for evidence receipts without leaking mailbox addresses or PII? — AC-31 needs durable evidence, while AC-21 forbids plaintext mailbox/PII in git and logs.
