# P0-04A codeaudit a2 evidence metadata

- verdict: `REQUEST_CHANGES`
- auditor_id: `/root/p0_04a_codeaudit_a2`
- base_commit: `f91b59c7cd8e0c423f83225336ce61d46bb72597`
- red_commit: `d97d89a599307362858276dc3002b881be361765`
- intermediate_commit: `c8141265df6b1da96152fbbebdd948eb89287694`
- candidate_commit: `2325103e5b7f8553c30b8f591f5760befb5b4b76`
- raw_evidence_path: `docs/engineering/admin-weekly-dashboard-v6-p0-04a-codeaudit-a2-2026-08-17.md`
- raw_evidence_sha256: `6b10375f110f440891823ac92df6b4ab49d4dd1db985f66bee85e757a5d5951c`
- raw_evidence_bytes: `7664`
- stored_at_utc: `2026-08-16T23:49:04Z`
- redaction: `none`
- external_side_effect_count: `0`
- data_exposure_result: `no sensitive values observed in the audit artifact`
- failure_1: `candidate modified a file outside the exact allowed-file contract`
- failure_2: `the canonical artifact-ignore selector remained unsupported`
- next_state: `REWORK from f91b59c7cd8e0c423f83225336ce61d46bb72597 in a fresh branch/worktree`
- preservation_note: `The raw auditor output is stored byte-for-byte. Any trailing whitespace reported by git diff --check is retained as part of the immutable audit record.`
