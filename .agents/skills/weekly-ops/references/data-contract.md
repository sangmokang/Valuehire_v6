# Data contract

## Source of truth

Use the repository SQL contract at `contracts/weekly-ops/db-contract-v1.sql`. An operational database
may map names to an existing schema, but it must preserve the same identities and state transitions.

Core lineage:

```text
weekly_run
  -> source_snapshots
  -> canonical_positions <- position_source_links -> customer_intents/career_observations
  -> dedupe_decisions
  -> priority_scores
  -> proposal_send_attempts -> consultant_position_focus -> grass YELLOW evidence
  -> report_snapshot
  -> publication_intents
  -> publication_receipts
```

## Allowed states

- capability: `PASS`, `FAIL`, `NOT_RUN`, `STALE`
- source snapshot: `PASS`, `PARTIAL`, `FAIL`, `NOT_RUN`, `STALE`
- run/report: `DISCOVERED`, `PARTIAL`, `BLOCKED`, `READY`, `PUBLISHED`
- origin: `SCRAPED_STAGING`, `CLIENT_REQUESTED`, `CLIENT_SHARED`, `INTERNAL_CREATED`
- lifecycle: `ACTIVE`, `PIPELINE`, `CLOSING`, `CLOSED`
- client priority: `TOP`, `HIGH`, `NORMAL`, `NONE`
- intent: `REQUESTED`, `POSITION_SHARED`, `REQUIREMENT_CHANGED`, `PIPELINE_FEEDBACK`,
  `REFERENCE_ONLY`, `NONE`
- publication: `INTENT_RECORDED`, `WRITE_STARTED`, `UNKNOWN_OUTCOME`,
  `READBACK_VERIFIED`, `FAILED`

`UNKNOWN_OUTCOME` must reconcile by reading the target before retrying.

The eight required read capability names and five publication target names are fixed by
`runtime-contract-v1.json`. Omitting a name or changing `required` to false is a contract error, not a
way to downgrade the requirement.

Every normalized fact must resolve to a valid `source_snapshot_id` and opaque `evidence_ref`. A source
snapshot records source system, protected URI reference, timezone-aware fetch time, status, SHA-256
hash of the redacted extraction, and non-empty evidence references before normalization. The protected
DB separately retains the raw-source hash. Missing lineage is `BLOCKED`.
Any valid non-`PASS` source snapshot remains an explicit source blocker; enum-valid failure cannot be
silently converted into a full `PASS`.

## Priority formula

`weekly-priority-v1` is implemented by `scripts/weekly_gate.py`.

- urgency = intent + recency + explicit deadline + late-stage signal + explicit client priority,
  capped at 100;
- difficulty = scarcity + seniority + special constraints + funnel friction, capped at 100;
- priority = `round(0.7 * urgency + 0.3 * difficulty)`;
- scraped-only priority is capped at 20 and excluded from customer actions.
- closed positions are excluded from customer actions and rendered under operating changes.

Every input enum needs an opaque evidence reference. The DB can resolve that reference to protected
source metadata; reviewers and published views cannot resolve it to raw PII.

## Dedupe contract

Normalize comparison keys with Unicode NFKC, case folding, whitespace collapse, and explicit alias
tables. Exact keys may link automatically. Fuzzy candidates go to manual review. The decision records
rule version, inputs, canonical ID, reason, actor, and timestamp.

Never mutate or delete source snapshots to make counts look clean.

The redacted bundle includes `dedupe_decisions` even when it is an empty list. Duplicate canonical IDs
or duplicate normalized company/title keys are blocked; an explicit versioned decision is required
before a future reconciler may suppress a duplicate projection.

## Consultant focus and grass evidence

For the closed weekly window, group only `proposal_send_attempts.status='SENT'` rows that have provider
readback. Compute per consultant and canonical position:

- verified sent count;
- HMAC-unique candidate count;
- active calendar days in KST;
- focus share = position verified sends / consultant total verified sends;
- channel mix.

The row is eligible for grass `YELLOW`. It does not override `GREEN` or `BLUE`, and missing channel
readback makes the affected metric `NOT_RUN`, never zero. Open tabs, searches, drafts, and pending or
failed attempts are not activity.
The provider receipt reference must resolve inside the same outreach source snapshot as the send event.
A local string or an ID found only in another snapshot is not provider readback.

## Publication receipt

`READBACK_VERIFIED` requires all of: write-ahead intent ID, idempotency key, schema readback reference,
external object ID, receipt ID, DB-persisted receipt reference, report snapshot ID, and content hash.
The target snapshot/hash must match the locally rendered report. HTTP success or an external message
ID without the DB receipt is partial evidence, not a publication receipt.

Forbidden field names and value-level personal email/phone patterns block rendering. The only plaintext
email permitted in the evidence contract is the exact allowlisted publication target in its target-ID
field; it is never accepted in report prose or business evidence.
