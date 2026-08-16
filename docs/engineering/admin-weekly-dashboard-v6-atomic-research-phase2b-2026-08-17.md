# Admin Weekly Dashboard v6 atomic research — phase2b — 2026-08-17

이 파일은 fresh read-only 조사자의 원문 증거입니다. 정본 계획이 아니며 controller의 수정 규칙과 독립 계획 감사를 우선합니다.

## Metis Analysis: Phase 2b AC Atomic Decomposition

읽기 전용 조사 완료. 기준 HEAD `a02a3da8f36e22997028b0d620de4e7e970f76d8` 일치. 저장소/상위 경로에는 `AGENTS.md` 파일이 없었고, 현재 세션 주입 AGENTS 계약을 상위 정본으로 적용했다. `docs/sot`는 현재 5개 파일만 존재한다: `INDEX.md`, `coding-principles.md`, `hook-contracts.md`, `git-workflow.md`, `verification-commands.md`, `mechanism-registry.yaml`.

근거:
- admin 제품 코드/DB 스키마는 아직 없음: `apps/`, `contracts/admin-weekly-dashboard/` 미존재.
- 새 acceptance는 CI와 SOT 동시 등록 필요: `docs/sot/verification-commands.md:43`, `.github/workflows/verify.yml:161`, `.github/workflows/verify.yml:178`, `docs/sot/mechanism-registry.yaml:1`.
- pre-push는 `acceptance-*.sh` 글로브 자동 수집: `hooks/pre-push:110`.
- 0건 처리 금지/NOT_RUN: `scripts/scan-data-exposure.sh:7`, `scripts/scan-data-exposure.sh:68`, `docs/sot/verification-commands.md:56`.
- PostgreSQL 원장/불변식 계약: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:532`, `:771-787`.
- 실제 PostgreSQL 17.11 통합 시험 필요: `docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md:1080`, `:1094`.

### Micro Candidates

```yaml
- parent_ac: AC-16
  micro_id: AC16-M1-snapshot-byte-stable
  single_observable_result: same as_of + same metric_contract_version + same typed source_watermarks creates identical weekly_snapshots.payload_sha256 byte-for-byte
  single_failure_reason: snapshot procedure uses nondeterministic generated_at/order/json serialization or omits a watermark from query inputs
  rollback_unit: revert create_weekly_snapshot determinism procedure + deterministic JSON payload test only
  dependencies: [Phase2 schema, weekly_reporting_periods, source_watermarks, weekly_snapshots, weekly_snapshot_watermarks]
  allowed_files: [apps/admin/prisma/schema.prisma, apps/admin/prisma/migrations/**, apps/admin/src/db/**, apps/admin/src/domain/weekly-snapshot/**, apps/admin/tests/integration/**, scripts/acceptance-admin-db.sh]
  forbidden_scope: UI/API rendering, Gmail/ClickUp live reads, actual legacy exports, external network
  red_command: pnpm --filter admin test -- --run tests/integration/snapshot-determinism.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case snapshot-determinism
  mutation_method: inject same synthetic rows twice and assert payload_sha256 equality; then randomize row order to prove stable canonicalization
  production_call_path: create_weekly_snapshot(...) DB procedure called by admin weekly snapshot job/API read model
  target_count_method: count two generated snapshots for same as_of and require targetCount=2 in ADMIN_GATE_JSON
  cannot_split_reason: one observable only, payload hash equality; watermark mutation/error is separate
  external_side_effect_count_expected: 0

- parent_ac: AC-16
  micro_id: AC16-M2-watermark-bound-change-detected
  single_observable_result: changing one source_watermark.upper_bound changes payload_sha256 or returns contract error
  single_failure_reason: snapshot query ignores source-specific upper_bound
  rollback_unit: revert watermark bound predicate in create_weekly_snapshot and its integration fixture
  dependencies: [AC16-M1, typed source_watermarks]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/weekly-snapshot/**, apps/admin/tests/integration/**]
  forbidden_scope: API schema changes, visual dashboard, external connectors
  red_command: pnpm --filter admin test -- --run tests/integration/snapshot-watermark-bounds.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case snapshot-watermark-bounds
  mutation_method: create synthetic event above upper_bound and prove excluded/included hash differs
  production_call_path: create_weekly_snapshot(...) DB procedure
  target_count_method: targetCount = number of bound mutation cases, minimum 1
  cannot_split_reason: upper_bound is a single source cutoff invariant; query_digest is separate
  external_side_effect_count_expected: 0

- parent_ac: AC-16
  micro_id: AC16-M3-required-watermark-missing-fails
  single_observable_result: omitting one metric_source_requirements watermark causes snapshot creation failure
  single_failure_reason: procedure treats missing required source as empty source instead of contract failure
  rollback_unit: revert required watermark validation procedure/test
  dependencies: [metric_source_requirements, source_watermarks]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/db/**, apps/admin/tests/integration/**]
  forbidden_scope: frontend fallback states, live collector behavior
  red_command: pnpm --filter admin test -- --run tests/integration/snapshot-required-watermarks.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case snapshot-required-watermarks
  mutation_method: delete one synthetic required watermark before create_weekly_snapshot
  production_call_path: create_weekly_snapshot(...)
  target_count_method: targetCount = required source count attempted; missing count must be 1
  cannot_split_reason: single absence/failure invariant
  external_side_effect_count_expected: 0

- parent_ac: AC-23
  micro_id: AC23-M1-purge-removes-payload-blob
  single_observable_result: expired payload purge deletes ciphertext blob/data-key record and writes lifecycle/deletion event
  single_failure_reason: purge only writes event or nulls URI while payload remains decryptable
  rollback_unit: revert purge_pii_payload procedure and synthetic object-store adapter test
  dependencies: [pii_payload_refs, pii_payload_blobs, retention_policies, data_deletion_events]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/db/retention/**, apps/admin/tests/integration/retention/**]
  forbidden_scope: real object storage, real KMS, real Gmail data
  red_command: pnpm --filter admin test -- --run tests/integration/retention-purge-payload.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case retention-payload-purge
  mutation_method: insert synthetic expired payload; purge; attempt decrypt/read through fake key/object provider
  production_call_path: purge_pii_payload(payload_ref_id, policy_version)
  target_count_method: targetCount = expired synthetic payload refs purged, minimum 1
  cannot_split_reason: payload deletion observable is independent from Gmail lookup key removal
  external_side_effect_count_expected: 0

- parent_ac: AC-23
  micro_id: AC23-M2-purge-removes-gmail-provider-lookup
  single_observable_result: after purge, provider_message_key_hmac lookup cannot resolve provider message id
  single_failure_reason: gmail_message_lookup_keys survives derived identifier purge
  rollback_unit: revert lookup-key retention procedure and lookup API guard test
  dependencies: [gmail_message_lookup_keys, gmail_messages, retention_policies]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/db/gmail/**, apps/admin/tests/integration/retention/**]
  forbidden_scope: Gmail API calls, mailbox config, real provider ids
  red_command: pnpm --filter admin test -- --run tests/integration/retention-purge-gmail-lookup.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case retention-gmail-lookup-purge
  mutation_method: seed synthetic HMAC lookup key past active_until; purge; compare API must fail
  production_call_path: retention purge procedure + provider-message lookup repository
  target_count_method: targetCount = lookup keys removed and failed lookup attempts
  cannot_split_reason: single provider lookup observable
  external_side_effect_count_expected: 0

- parent_ac: AC-23
  micro_id: AC23-M3-immutable-ledger-tombstone-only
  single_observable_result: immutable ledger row remains with random payload_ref tombstone and no plaintext/HMAC payload
  single_failure_reason: purge deletes ledger row or leaves plaintext/HMAC identifier in immutable ledger
  rollback_unit: revert ledger tombstone constraints/test
  dependencies: [pii_payload_refs, ledger tables, append-only permissions]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/db/retention/**, apps/admin/tests/integration/**]
  forbidden_scope: UI masking, external storage deletion
  red_command: pnpm --filter admin test -- --run tests/integration/retention-tombstone-ledger.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case retention-tombstone-ledger
  mutation_method: purge synthetic payload then scan ledger columns for forbidden plaintext/hash fields and assert ref row remains
  production_call_path: purge_pii_payload + ledger read model
  target_count_method: targetCount = tombstoned ledger refs inspected
  cannot_split_reason: one persisted tombstone shape
  external_side_effect_count_expected: 0

- parent_ac: AC-33
  micro_id: AC33-M1-six-source-coverage-required
  single_observable_result: every snapshot has exactly six weekly_discovery_source_coverage rows for v4/v5/v6 × aisearch/humansearch
  single_failure_reason: create_weekly_snapshot allows missing pair or duplicate pair
  rollback_unit: revert six-pair coverage constraint/procedure/test
  dependencies: [weekly_discovery_source_coverage, source_watermarks]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/discovery/**, apps/admin/tests/integration/coverage/**]
  forbidden_scope: real legacy export import, UI cards
  red_command: pnpm --filter admin test -- --run tests/integration/discovery-coverage-six-pairs.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case discovery-coverage-six-pairs
  mutation_method: omit one pair and duplicate another; DB/procedure must reject both
  production_call_path: create_weekly_snapshot(...)
  target_count_method: targetCount = coverage rows per snapshot, must equal 6
  cannot_split_reason: exact cardinality invariant
  external_side_effect_count_expected: 0

- parent_ac: AC-33
  micro_id: AC33-M2-missing-source-nullable-not-run
  single_observable_result: unavailable source pair stores nullable counts + status NOT_RUN + reason, not PASS+0
  single_failure_reason: missing source is coerced to numeric zero and PASS
  rollback_unit: revert NOT_RUN coverage mapping/test
  dependencies: [coverage status enum/check constraints]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/discovery/**, apps/admin/tests/integration/coverage/**]
  forbidden_scope: actual source adapters, cross-source identity matching
  red_command: pnpm --filter admin test -- --run tests/integration/discovery-coverage-not-run.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case discovery-coverage-not-run
  mutation_method: seed no manifest for one pair; assert counts null and status NOT_RUN
  production_call_path: discovery coverage builder used by snapshot procedure
  target_count_method: targetCount = unavailable source pair rows, minimum 1
  cannot_split_reason: one missing-source representation invariant
  external_side_effect_count_expected: 0

- parent_ac: AC-33
  micro_id: AC33-M3-empty-manifest-pass-zero-only
  single_observable_result: PASS+0 is accepted only with complete empty manifest/watermark evidence
  single_failure_reason: implementation treats absent export as proven empty manifest
  rollback_unit: revert empty manifest validator/test
  dependencies: [legacy_export_batches, native_discovery_batches, source_watermarks]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/discovery/**, apps/admin/tests/integration/coverage/**]
  forbidden_scope: real export files, external storage writes
  red_command: pnpm --filter admin test -- --run tests/integration/discovery-empty-manifest.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case discovery-empty-manifest
  mutation_method: compare absent manifest vs manifest rowCount=0 + rowsSha256 evidence
  production_call_path: legacy/native source coverage ingestion
  target_count_method: targetCount = empty manifest cases verified
  cannot_split_reason: PASS+0 authorization invariant
  external_side_effect_count_expected: 0

- parent_ac: AC-34
  micro_id: AC34-M1-approval-target-mismatch-no-db-side-effects
  single_observable_result: mismatched approval target creates zero consumed approvals, zero leases, zero attempts
  single_failure_reason: claim_clickup_write_lease consumes approval before validating mail/business/target linkage
  rollback_unit: revert claim_clickup_write_lease validation transaction/test
  dependencies: [live_write_approvals, mail_business_links, clickup_registration_targets, clickup_write_leases, clickup_write_attempts]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/db/clickup/**, apps/admin/tests/integration/clickup/**]
  forbidden_scope: ClickUp HTTP adapter, real approvals, UI approval flow
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-approval-target-mismatch.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case approval-target-mismatch
  mutation_method: seed approval for object A; request lease for target object B
  production_call_path: claim_clickup_write_lease(registration_target_id, approval_id)
  target_count_method: count rows changed across approvals/leases/attempts; all must be 0
  cannot_split_reason: DB side-effect zero invariant, external-call zero is separate
  external_side_effect_count_expected: 0

- parent_ac: AC-34
  micro_id: AC34-M2-approval-target-mismatch-no-external-call
  single_observable_result: mismatched approval target produces ClickUp POST/PUT call count 0
  single_failure_reason: write runner calls adapter despite failed lease claim
  rollback_unit: revert write runner lease gate/test
  dependencies: [AC34-M1, disabled network spy/fake adapter]
  allowed_files: [apps/admin/src/jobs/clickup/**, apps/admin/src/integrations/clickup/**, apps/admin/tests/integration/clickup/**]
  forbidden_scope: real ClickUp token, real network, Phase4 live approval
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-no-call-on-approval-mismatch.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case approval-target-mismatch-no-call
  mutation_method: inject fake ClickUp adapter spy; force mismatched approval; assert spy count 0
  production_call_path: ClickUp write job -> claim_clickup_write_lease -> ClickUp adapter
  target_count_method: fake adapter call counter, expected 0
  cannot_split_reason: one external side-effect observable
  external_side_effect_count_expected: 0

- parent_ac: AC-35
  micro_id: AC35-M1-expired-derived-key-compare-rejected
  single_observable_result: compare API rejects derived identifier key version after retention window
  single_failure_reason: compare path ignores retention_policies.derived_identifier_days or key active_to
  rollback_unit: revert compare key eligibility guard/test
  dependencies: [business_object_keys, retention_policies, cryptographic_key_versions]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/crypto/**, apps/admin/src/db/business-objects/**, apps/admin/tests/integration/crypto/**]
  forbidden_scope: real PII payloads, key provider destruction
  red_command: pnpm --filter admin test -- --run tests/integration/derived-key-compare-expiry.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case derived-key-compare-expiry
  mutation_method: seed expired derived identifier key and attempt compare/dedupe
  production_call_path: compare/dedupe repository and claim_business_object(...)
  target_count_method: targetCount = rejected expired key compare attempts
  cannot_split_reason: compare rejection only; purge receipt is separate
  external_side_effect_count_expected: 0

- parent_ac: AC-35
  micro_id: AC35-M2-expired-derived-key-dedupe-rejected
  single_observable_result: dedupe/claim does not use expired key version to match or create business object
  single_failure_reason: claim_business_object still computes or accepts expired key HMAC
  rollback_unit: revert claim_business_object key eligibility/test
  dependencies: [claim_business_object, business_object_keys, cryptographic_key_versions]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/db/business-objects/**, apps/admin/tests/integration/crypto/**]
  forbidden_scope: Gmail parser changes, ClickUp write path
  red_command: pnpm --filter admin test -- --run tests/integration/derived-key-dedupe-expiry.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case derived-key-dedupe-expiry
  mutation_method: mark key expired; try claim using only expired key
  production_call_path: claim_business_object(...)
  target_count_method: targetCount = expired-key claim attempts rejected
  cannot_split_reason: dedupe path eligibility only
  external_side_effect_count_expected: 0

- parent_ac: AC-35
  micro_id: AC35-M3-key-destroy-receipt-required-for-purge-pass
  single_observable_result: purge PASS is impossible without key destroy event/receipt for destroyed key version
  single_failure_reason: purge records success before key provider destruction evidence exists
  rollback_unit: revert key destroy receipt check/test
  dependencies: [cryptographic_key_state_events, data_deletion_events]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/crypto/**, apps/admin/src/db/retention/**, apps/admin/tests/integration/retention/**]
  forbidden_scope: real KMS deletion, real secrets
  red_command: pnpm --filter admin test -- --run tests/integration/key-destroy-receipt-required.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case key-destroy-receipt-required
  mutation_method: attempt DESTROYED/PASS without destroy_receipt_sha256
  production_call_path: key lifecycle procedure + retention purge procedure
  target_count_method: targetCount = purge attempts without receipt rejected
  cannot_split_reason: single evidence-required invariant
  external_side_effect_count_expected: 0

- parent_ac: AC-38
  micro_id: AC38-M1-active-write-key-exactly-one
  single_observable_result: DB rejects ACTIVE 0 or ACTIVE >1 per purpose for write-capable key selection
  single_failure_reason: key selection silently picks first key or allows no active key fallback
  rollback_unit: revert partial unique/check constraint and selection test
  dependencies: [cryptographic_key_versions]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/crypto/**, apps/admin/tests/integration/crypto/**]
  forbidden_scope: envelope encryption payload implementation
  red_command: pnpm --filter admin test -- --run tests/integration/key-active-cardinality.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case key-active-cardinality
  mutation_method: insert zero and duplicate ACTIVE keys for same purpose
  production_call_path: key selection procedure used by claim/compare/encrypt
  target_count_method: targetCount = cardinality cases, minimum 2
  cannot_split_reason: one cardinality invariant
  external_side_effect_count_expected: 0

- parent_ac: AC-38
  micro_id: AC38-M2-retired-destroyed-key-use-rejected
  single_observable_result: RETIRED or DESTROYED key cannot be used by claim/compare/encrypt procedures
  single_failure_reason: procedure checks key existence but not state
  rollback_unit: revert key state eligibility guards/test
  dependencies: [cryptographic_key_versions, claim/compare/encrypt procedures]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/crypto/**, apps/admin/tests/integration/crypto/**]
  forbidden_scope: key rotation migration, retention purge
  red_command: pnpm --filter admin test -- --run tests/integration/key-retired-destroyed-use.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case key-retired-destroyed-use
  mutation_method: set key state to RETIRED/DESTROYED and call procedures
  production_call_path: claim_business_object, compare API, encrypt payload path
  target_count_method: targetCount = rejected state/procedure combinations
  cannot_split_reason: one invalid-state usage observable
  external_side_effect_count_expected: 0

- parent_ac: AC-38
  micro_id: AC38-M3-key-state-projection-event-consistency
  single_observable_result: DB rejects projection state that lacks matching latest cryptographic_key_state_events row
  single_failure_reason: direct update of key projection bypasses lifecycle event log
  rollback_unit: revert projection/event trigger and test
  dependencies: [cryptographic_key_versions, cryptographic_key_state_events]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/tests/integration/crypto/**]
  forbidden_scope: key provider adapters
  red_command: pnpm --filter admin test -- --run tests/integration/key-state-event-projection.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case key-state-event-projection
  mutation_method: mutate cryptographic_key_versions.state without event, then commit
  production_call_path: key lifecycle procedure
  target_count_method: targetCount = projection mismatch mutations rejected
  cannot_split_reason: projection/event consistency only
  external_side_effect_count_expected: 0

- parent_ac: AC-38
  micro_id: AC38-M4-destroyed-requires-provider-receipt
  single_observable_result: DESTROYED state cannot be recorded without provider destruction receipt sha256
  single_failure_reason: lifecycle accepts DESTROYED event without external proof
  rollback_unit: revert destroyed receipt constraint/test
  dependencies: [cryptographic_key_state_events]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/domain/crypto/**, apps/admin/tests/integration/crypto/**]
  forbidden_scope: real KMS destroy call
  red_command: pnpm --filter admin test -- --run tests/integration/key-destroyed-receipt.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case key-destroyed-receipt
  mutation_method: attempt lifecycle transition to DESTROYED with null destroy_receipt_sha256
  production_call_path: key lifecycle procedure
  target_count_method: targetCount = DESTROYED attempts without receipt rejected
  cannot_split_reason: receipt requirement only
  external_side_effect_count_expected: 0

- parent_ac: AC-40
  micro_id: AC40-M1-raw-lease-token-not-persisted
  single_observable_result: DB has lease_token_hash only; raw ClickUp lease token is absent from lease/attempt/event/audit tables
  single_failure_reason: lease claim stores raw token or includes it in event evidence
  rollback_unit: revert lease token persistence schema/procedure/test
  dependencies: [clickup_write_leases, clickup_write_attempts, live_write_approval_events, access_audit_events]
  allowed_files: [apps/admin/prisma/migrations/**, apps/admin/src/db/clickup/**, apps/admin/tests/integration/clickup/**]
  forbidden_scope: real ClickUp adapter, production logs
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-raw-lease-token-db.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case clickup-raw-token-db
  mutation_method: claim lease with known synthetic token; search DB text columns for raw token and require 0 hits
  production_call_path: claim_clickup_write_lease(...)
  target_count_method: targetCount = inspected DB rows/columns with synthetic token canary
  cannot_split_reason: DB persistence only; receipt/log scan is separate
  external_side_effect_count_expected: 0

- parent_ac: AC-40
  micro_id: AC40-M2-raw-lease-token-not-in-receipts-or-logs
  single_observable_result: ADMIN_GATE_JSON receipt and admin application logs contain zero raw lease token occurrences
  single_failure_reason: test receipt or logger serializes token returned by claim procedure
  rollback_unit: revert receipt/log redaction test and logger context handling
  dependencies: [acceptance-admin-db receipt format, admin logger]
  allowed_files: [scripts/acceptance-admin-db.sh, apps/admin/src/jobs/clickup/**, apps/admin/src/lib/logging/**, apps/admin/tests/integration/clickup/**]
  forbidden_scope: production log sink, external observability service
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-raw-lease-token-logs.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case clickup-raw-token-logs
  mutation_method: use synthetic token canary; capture local log buffer + receipt stdout; grep exact canary
  production_call_path: ClickUp write job logging + acceptance receipt
  target_count_method: targetCount = inspected receipt/log files, must be >0 and raw hits 0
  cannot_split_reason: log/receipt exposure observable
  external_side_effect_count_expected: 0

- parent_ac: AC-40
  micro_id: AC40-M3-hash-mismatch-token-no-external-call
  single_observable_result: token whose hash does not match active unreleased lease causes ClickUp external call count 0
  single_failure_reason: write runner trusts caller token without DB hash/fencing readback
  rollback_unit: revert pre-network fencing check/test
  dependencies: [clickup_write_leases, write runner, fake ClickUp adapter]
  allowed_files: [apps/admin/src/jobs/clickup/**, apps/admin/src/integrations/clickup/**, apps/admin/tests/integration/clickup/**]
  forbidden_scope: real network, real ClickUp token
  red_command: pnpm --filter admin test -- --run tests/integration/clickup-token-hash-mismatch-no-call.test.ts
  green_command: bash scripts/acceptance-admin-db.sh --case clickup-token-hash-mismatch-no-call
  mutation_method: seed lease hash for token A, invoke worker with token B, assert fake adapter POST/PUT count 0
  production_call_path: ClickUp write job before POST/PUT adapter
  target_count_method: fake adapter call counter, expected 0
  cannot_split_reason: one fencing side-effect invariant
  external_side_effect_count_expected: 0
```

### Guardrails

- DB constraint and PostgreSQL 17.11 runtime proof should be paired for the same invariant but reported separately: migration/check/trigger failure reason versus integration behavior failure reason. This follows Phase 2 exit at `docs/...goal...md:1094`.
- All tests must use synthetic canaries only. For PII/secret/external-write boundaries, proof method is local fake object store, fake key provider, fake ClickUp adapter, captured stdout/log buffers, and DB text-column scan. No Gmail/ClickUp/Calendar network call is required for these ACs.
- Every admin acceptance receipt should emit one machine-readable line as required by `docs/...goal...md:190`, with `targetCount > 0`; otherwise use `NOT_RUN`, never PASS.

### Open Questions

- [ ] Should `acceptance-admin-db.sh` own all seven parent ACs as case flags, or should Phase 2 split into multiple admin DB acceptance scripts? — CI/SOT registration overhead differs, and `verification-commands.md:43` requires every new script to be mirrored.
- [ ] What exact Docker Compose filename/path should become the PostgreSQL 17.11 SOT for Phase 2? — Current repo has no compose/admin package, but Phase 2 requires digest-locked `postgres:17.11-alpine`.
- [ ] Should key lifecycle receipt fields live on `cryptographic_key_versions`, `cryptographic_key_state_events`, or both? — AC-35 and AC-38 both require destroy receipts, but the current goal text defines `destroy_receipt_sha256_nullable` on key versions and `evidence_sha256` on events.
