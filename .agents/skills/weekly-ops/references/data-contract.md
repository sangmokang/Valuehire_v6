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
  -> zero_result_assertions
  -> priority_scores
  -> consultants -> consultant_provider_accounts -> proposal_send_attempts
  -> consultant_position_focus -> grass YELLOW evidence
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
- outreach access: `AUTHENTICATED`, `AUTH_REQUIRED`, `TUTORIAL_OR_DEMO`,
  `AUTOMATION_DENIED`, `CHALLENGE`, `MISSING_PROFILE`, `STALE_PAGE`

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

## DB operating snapshot

When `db_read=PASS`, the bundle must include one `operating_snapshot` backed by a `PASS` database
source snapshot and exact provenance `sql_rpc:weekly_brief_snapshot`. The RPC's closed week must equal
the run's seven-day Monday 00:00-to-Monday 00:00 Asia/Seoul half-open window. Its source URI must be
exactly `rpc:weekly_brief_snapshot:{meeting_date}`. Closed-week SQL counts, current funnel state, and
targets remain separate exact-key fields; unknown metrics are invalid so the current funnel cannot be
silently mixed with weekly performance. Generated and source freshness timestamps after the meeting
cutoff are invalid. Non-negative numeric validation, source linkage, and the complete operating
snapshot are bound into `report_snapshot_id`.

## Priority formula

`weekly-priority-v1` is implemented by `scripts/weekly_gate.py`.

- urgency = intent + recency + explicit deadline + late-stage signal + explicit client priority,
  capped at 100;
- difficulty = scarcity (`0/20/35`) + seniority (`0/15/25`) + special constraints
  (`0/15/25`) + funnel friction (`0/8/15`), capped at 100;
- priority = `round(0.7 * urgency + 0.3 * difficulty)`;
- scraped-only priority is capped at 20 and excluded from customer actions.
- closed positions are excluded from customer actions and rendered under operating changes.

Every input enum needs an opaque evidence reference. The DB can resolve that reference to protected
source metadata; reviewers and published views cannot resolve it to raw PII.

When the capabilities responsible for `positions` or three-channel `outreach_events` are all `PASS`
but the observed result is zero, the bundle must carry one `weekly-zero-result-v1` assertion. Its
provider receipt must resolve inside the named source snapshot and `observed_count` must be the integer
zero. An empty array without that receipt is `BLOCKED`, not a business conclusion of zero.

## Dedupe contract

Normalize comparison keys with Unicode NFKC, case folding, whitespace collapse, and explicit alias
tables. Exact keys may link automatically. Fuzzy candidates go to manual review. The decision records
rule version, inputs, canonical ID, reason, actor, and timestamp. The redacted gate requires
`rule_version=weekly-dedupe-v1`, a kept canonical ID that exists in the same bundle, and removed source
references that resolve to the same bundle's source snapshots.

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

The current aggregation contract is `consultant-focus-v2`; its version is part of snapshot identity.
Its exact output shape is one consultant summary per `consultant_focus[]` item with these required
fields: `consultant_id`, `consultant_display`, `verified_sent_count`, `unique_candidate_count`,
`active_days`, `channel_mix`, `comparison_status`, and `positions`. Each `positions[]` item is one
canonical consultant-by-position ledger row with `position_id`, `company`, `title`,
`verified_sent_count`, `unique_candidate_count`, `active_days`, `channels`, `channel_mix`,
`evidence_refs`, `focus_share`, and `grass_evidence`.

The DB projection to `consultant_position_focus` is a mechanical flatten only: copy the parent
`consultant_id`, copy `positions[].position_id` to the DB `position_id`, and copy the position-level
counts, share, mix, and grass evidence. It may not rejoin by title, recompute focus, or create rows
from the consultant-level totals.

The row is eligible for grass `YELLOW`. It does not override `GREEN` or `BLUE`, and missing channel
readback makes the affected metric `NOT_RUN`, never zero. Open tabs, searches, drafts, and pending or
failed attempts are not activity.
Each counted row must carry an opaque provider actor/account reference that maps to exactly one active
consultant for that channel. An internal assignment email, copied recipient, shared mailbox, or display
name is not identity evidence. LinkedIn's provider actor and seat references must agree.
The tuple `(channel, provider_receipt_ref)` is unique for aggregation across snapshot re-imports. Duplicate
local event IDs, forwarded copies, and re-imports of the same receipt block the focus projection rather
than increasing the count.
The provider receipt reference must resolve inside the same outreach source snapshot as the send event.
A local string or an ID found only in another snapshot is not provider readback.
An authenticated screen is only a capability precondition. Screenshots, OCR, open tabs, cached routes,
and aggregate portal totals remain non-ledger evidence unless each counted event has the required
provider identity, sent time, consultant identity, and canonical-position join.
When all three outreach capabilities are `PASS`, and before any portal event is accepted, the hashed
input must contain exactly one diagnostic for each of JobKorea, Saramin, and LinkedIn RPS. Each
diagnostic records access state, allowlisted surface kind,
protected surface reference, stable-receipt availability, covered provider actor refs, and its source
snapshot. A non-authenticated
or receipt-unavailable diagnostic also requires a blocker reason. A counted event must share that
diagnostic's source snapshot; LinkedIn additionally requires provider seat and project references.
Generic email is not an outreach channel for this metric; Gmail customer mail is classified separately
as customer intent.
The publication result always contains `channel_coverage`, `consultant_focus`, and `excluded_rows`.
Out-of-window sends appear only in `excluded_rows` and do not suppress the in-window
`weekly-zero-result-v1` requirement.
Any coverage gap sets consultant focus `comparison_status=NOT_COMPARABLE`; observed counts may remain
visible, but the renderer must not rank consultants against one another.

## Publication receipt

`READBACK_VERIFIED` requires all of: write-ahead intent ID, idempotency key, schema readback reference,
external object ID, receipt ID, DB-persisted receipt reference, report snapshot ID, and content hash.
The target snapshot/hash must match the locally rendered report. HTTP success or an external message
ID without the DB receipt is partial evidence, not a publication receipt.

Forbidden field names and value-level personal email/phone patterns block rendering. The only plaintext
email permitted in the evidence contract is the exact allowlisted publication target in its target-ID
field; it is never accepted in report prose or business evidence.
