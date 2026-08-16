# P0-04A independent codeaudit a1 evidence metadata — 2026-08-17

- verdict: `REQUEST_CHANGES`
- micro_id: `P0-04A-generated-artifact-ignore`
- parent_ac: `AC-01`
- parent_status: `PARTIAL_PARENT_AC`
- auditor_id: `/root/p0_04a_codeaudit_a1`
- exact_base: `7e7fe3937c43a3abbcb4687c51ad85fb66eaab13`
- red_commit: `3963ad74f3ccfbea399c968aa46c2595a009e50d`
- candidate_head: `02c7f0e2bdd2b91c09ea6b00c711d85a9394a555`
- raw_evidence_file: `docs/engineering/admin-weekly-dashboard-v6-p0-04a-codeaudit-a1-2026-08-17.md`
- raw_evidence_sha256: `6bf426b40989a889a14a48cbd4fe09aeac1fcf9e203a05fbe1d5063aef2f1c42`
- raw_evidence_bytes: `6685`
- saved_at_utc: `2026-08-16T22:56:53Z`
- sensitive_redaction: `none_required`
- external_side_effect_count: `0`
- failure_reason: `RED and candidate commits do not contain separate git-native Lore trailers; tracked-canary reason ordering is also inaccurate`
- next_state: `REWORK_FROM_P0_04_PASS_CHECKPOINT`

The audit is preserved as received. The implementation is not a PASS dependency because its commit history violates the mandatory Lore protocol.
