# Mail governance core (offline implementation)

This directory implements decisions, immutable SQLite intents, imported observations,
and coverage accounting. **It neither reads Gmail nor applies labels nor sends mail.**
No credentials, network adapters, background worker, all-member rollout, or provider
authentication is implemented here. `VERIFIED` means the supplied observations satisfy
the local contract; imported JSON is not an independently authenticated Gmail receipt.
The live adapter must obtain those observations from the respective authenticated account.

Run from repository root:

```sh
python3 -m unittest discover -s tools/mail_governance -p 'test_*.py' -v
python3 -m tools.mail_governance.mutation_check
python3 -m compileall -q tools/mail_governance
python3 -m tools.mail_governance --db /private/path/mail.sqlite import-review --input review.json
python3 -m tools.mail_governance --db /private/path/mail.sqlite plan --input review-id.json
```

`--input -` reads JSON from stdin. Exit 1 and `status: FAIL` means an invalid input,
hash mismatch, conflicting immutable review, or unsafe state transition. Keep private
mail outside git. The database is mode 0600; its directory must also be private.
Re-importing an unchanged review after observation time or existing labels change
returns the same review ID and retains the first observation snapshot. Those later
observation fields are not appended to this review journal. Other message/review
changes still conflict. Plans remain additive; adapters must add labels to the current
provider state rather than replace that state with the first snapshot.

## Input contract

`import-review` receives `{ "message": {...}, "review": {...} }`. All fields below
are required unless marked optional. No additional fields are accepted.

Message fields:

| Field | Type / meaning |
|---|---|
| `account`, `message_id` | Authenticated mailbox identity and provider-local ID |
| `rfc_message_id` | RFC Message-ID string or null; null retains local identity and blocks automatic sharing |
| `source_hash` | `content_hash(authored_text, html)` defined below |
| `from_address` | One unambiguous mailbox; a valid display name is accepted |
| `to_addresses` | All **observed** recipient addresses; include known Cc/Bcc, never infer hidden Bcc |
| `subject`, `authored_text` | Current authored subject/body, with quoted earlier mail excluded upstream |
| `html` | Optional authored HTML string or null, excluding quoted earlier mail upstream |
| `observed_at` | ISO-8601 timestamp with timezone |
| `occurred_at` | ISO-8601 timestamp with timezone or null; never replace unknown with observation time |
| `existing_labels` | Provider labels resolved to names, not account-local label IDs |
| `source_kind` | `direct_customer`, `internal`, `candidate`, or `unknown`; upstream assertion, not identity proof |
| `company_id` | Optional verified unique company identifier or null |

The content hash is SHA-256 of UTF-8 JSON with `ensure_ascii=False`, sorted keys,
and separators `(',', ':')`, containing exactly
`{"authored_text": <text>, "html": <html-or-null>}`. No whitespace or Unicode
normalization is performed. Python indexes in evidence are Unicode code-point offsets,
not JavaScript UTF-16 offsets. CLI `hash` accepts `{authored_text, html?}` and returns
`{source_hash}` without opening the database.

Review example (`N` offsets must be actual offsets, not literal placeholders):

```json
{
  "content_hash": "SHA256_OF_THE_MESSAGE_REPRESENTATIONS",
  "rule_version": "2026-10-21.v1",
  "reviewer": "claude:review-run-id",
  "mail_types": ["jd", "ontology"],
  "golden_axes": {
    "company": {"status": "met", "evidence": {"representation": "authored_text", "start": 0, "end": 6, "quote": "정확한 원문"}},
    "role": {"status": "unknown", "evidence": null},
    "personalization": {"status": "missing", "evidence": null},
    "layout": {"status": "unknown", "evidence": null}
  },
  "candidate_ready": null,
  "internal_confidential": null,
  "ontology_events": []
}
```

`mail_types` is a duplicate-free list drawn from `jd`, `interview`, `daily_weekly`,
`ontology`; empty means no supported type. Four golden axes are always required,
each `met|missing|unknown` plus `evidence` object or null. A `met` assertion must cite
an exact, nonempty source span. Every non-null span is verified, regardless of status.
Layout must cite an authored HTML/plaintext span containing the cited company, role,
and introductory personalization. The static check requires at least three visible
blocks of 12 alphanumeric characters each. Company/role/personalization evidence must
contain at least 40/40/24 visible alphanumeric characters respectively, and the intro
must precede company and role. Empty tags, comments, script/style and statically hidden
nodes do not qualify. HTML is parsed in its full source context before citation offsets
filter visible text; an omitted ancestor, comment, or attribute cannot make a hidden
fragment visible. These conservative floors reject trivial citations; they do not
prove substantive company facts, complete responsibilities, person-fit, or browser
computed CSS quality. The named reviewer owns those semantic assertions. Unknown
confidentiality or candidate readiness prevents golden; no human approval gate is added.
Ambiguous crossing closes, nonvoid self-closing tags, and duplicate attributes cannot
establish visible HTML evidence. Closed `details` content is also excluded; an
explicit `open` attribute permits it. Supported omitted paragraph/list endings and real
void elements remain accepted; this is not a complete HTML5 tree-repair algorithm.

`rule_version` must exactly match the running code's `RULE_VERSION`, currently
`2026-10-21.v1`. Whitespace, alternate spellings, and reviewer-chosen versions are
rejected. A rule change requires a code release and explicit migration; existing
reviews and operations remain in the journal. Changing imported JSON is not migration.
Mailbox account, sender, and recipient values must each parse as exactly one mailbox.
`normalize_address` strips valid display names and casefolds canonical addr-specs for
comparisons. Quoted display names and local parts are accepted; malformed addresses,
groups, multiple mailboxes in one item, control characters and outer padding are rejected.
Parsing does not authenticate the sender or mailbox. Legacy review keys stay unchanged;
new source-label operation payloads use the canonical account.
Equivalent account display names/case cannot create a second immutable review for
the same provider message, content and rule version. Existing raw IDs and row bytes
are preserved; conflicting legacy aliases require reconciliation.

Golden requires JD + all four axes `met` + qualifying layout evidence +
`candidate_ready: true` + `internal_confidential: false`. Financial amounts are not
mechanically mandatory. Non-JD mail never gains `01JD`; labels are independent and
additive: `01JD`, `01JD/goldensample`, `05인터뷰메일`, `04dailyweekly`, `06온톨로지`.
Old labels are preserved, including old golden labels; a failed current review does
not silently delete a prior classification. A separate audited correction is needed.

## Ontology events

Each event has exactly these fields:

```json
{
  "actor": "client",
  "event_type": "client_rejection",
  "stage": "document",
  "reason_quote": null,
  "company_id": "company-1",
  "position_id": "position-1",
  "candidate_id": null,
  "application_id": null,
  "review_status": "unresolved",
  "evidence": {"representation": "authored_text", "start": 0, "end": 6, "quote": "정확한 원문"}
}
```

Actors: `client|candidate|internal|unknown`. Event types:
`position_update|client_rejection|client_hold|feedback_clarification|interview_scheduled|candidate_withdrawal|candidate_no_response|feedback`.
Stages: `document|interview|offer|unknown`. Review statuses: `proposed|confirmed|unresolved`.
Reason is null or an exact substring of the cited event span. Absence produces
`reason_status: reason_unknown`, never a synthesized reason.
`client_hold` preserves a client's hold/pending decision; it is not a rejection.
`feedback_clarification` preserves a request or response clarifying feedback criteria;
it is not itself a rejection outcome. The reviewer must choose the evidenced event type;
the core does not infer a negative hiring outcome from either event.

Confirmed customer events require `source_kind: direct_customer`, client actor, and
non-null verified company/position IDs. The event company must match the verified
`message.company_id`; a missing or conflicting message company prevents confirmation.
Candidate-related events additionally require candidate/application IDs. Candidate
withdrawal/no-response events can also be confirmed from `source_kind: candidate`
with candidate actor and the same verified entity prerequisites. Internal reports and
candidate assertions of customer decisions remain unresolved. An assertion lacking
those prerequisites becomes unresolved.
`source_kind: direct_customer` is only the importer's declaration. The core does not
authenticate the sender, verify a customer-contact mapping, check SPF/DKIM, inspect
forwarded provenance, or prove the actor identity. `confirmed` here means all local
review prerequisites were declared and source spans matched, not that sender identity
was independently verified. A live adapter must establish trusted customer/contact
and entity/application mappings before importing that declaration; otherwise use
`source_kind: unknown` and unresolved events. A sender display name/domain alone or
quoted customer text is insufficient.
Uniqueness/entity resolution must be established upstream; a string ID alone is not
proof of that work. Multiple event payloads yield separate deterministic IDs. Complete
authored representations are stored only for direct-customer ontology mail. Other
mail retains metadata and Golden-axis evidence offsets/SHA-256 rather than another body
copy. Exact ontology event evidence and reason quotes remain available. Legacy rows are
compared through the same minimization but never rewritten. Minimized stored review
objects are audit records, not fresh classifier inputs; obtain original evidence to rerun.

## Plans, observations, and sharing

`plan`: `{review_id}`. `operation`: `{operation_id}`.
`receipt`: `{operation_id, state, receipt}`.

States are append-only:
`PLANNED -> SENDING -> SENT_UNVERIFIED -> VERIFIED`, with
`SENDING/SENT_UNVERIFIED -> AMBIGUOUS|FAILED`, and
`AMBIGUOUS -> VERIFIED` only after reconciliation/readback. Re-entering `SENDING`,
blind retries, and retries from `FAILED` are rejected. The adapter must claim SENDING
before an external effect; opening an existing SENDING/AMBIGUOUS operation is a
reconciliation task, not permission to resend.
For a share operation, the SENDING receipt must include `original_sha256`, the
lowercase SHA-256 of the original provider RFC bytes fetched before sending. It is
immutable send-intent evidence, separate from the authored-content hash.
`sharing` reflects the existing share state: `forward_planned`, `forward_sending`,
`forward_sent_unverified`, or `forward_verified`. Failed/ambiguous shares return
`forward_failed_reconciliation_required` / `forward_ambiguous_reconciliation_required`;
these statuses do not grant a retry or create a new send intent. A separate safe
share-recovery contract remains unimplemented.

The only sharing destination is `dev@valueconnect.kr`, for supported types. Plans
contain source additive-label work, receiver additive-label work, and (when needed)
one global share intent. The send adapter must add the exact, case-sensitive reserved
token `[VC-MIRROR:v1]` to the subject;
dev sources, dev senders, and that marker never relay again. Known dev recipients skip
forwarding while **receiver label work remains PLANNED**. Unknown hidden Bcc is not
proof of delivery. Global send dedup uses RFC Message-ID + content hash + destination.
Absent RFC IDs return `local_identity_reconciliation_required`, `duplicate_risk: true`,
and the local `source_identity`; only source-label work is planned until reconciliation.
There is no automatic cross-mailbox equivalence or send permission from a local ID. Additional label
sets can generate new receiver-label operations without generating another send.
RFC identity matching ignores optional angle brackets and outer whitespace while
preserving the ID's case. Existing share/receiver intents reuse their original dedup
keys; legacy scope reservations also seed canonical scopes without rewriting history.
Multiple conflicting legacy identity groups return `rfc_identity_reconciliation_required`
and do not plan receiver/send work. Readback compares RFC identities using the same
normalization; local identities still require an exact match. The received RFC verifier
separately validates actual original header syntax.

The content hash is representation-sensitive: extracting quoted text differently,
changing HTML rendering/escaping, or even changing whitespace can change the hash of
the same underlying email across mailboxes. Therefore an RFC-ID+destination scope is
reserved transactionally before planning receiver work, including known recipients.
A known-recipient observation in any reviewed mailbox suppresses sending on future
plans for the same RFC ID and content, even if their recipient headers omit that
destination. Existing pending intents remain recorded; adapters must reconcile them
and refresh the plan before acting. If the same scope has any different
content hash, `plan` returns `sharing: rfc_variant_review_required` and creates neither
a new share nor a receiver-label intent for that variant. Source-mailbox label work
can still proceed. Existing share and receiver-label intents seed this guard when an
older journal is opened. Genuine revised content reusing a Message-ID also requires review; the core
never silently declares the two variants equivalent. A reservation left by an
interrupted plan is conservatively retained. The adapter must reconcile variants
against original provider content before deciding how to share them. Without an RFC
Message-ID, cross-mailbox identity cannot be established by the fallback key; callers
must supply a separate reconciliation decision rather than claim global deduplication.

VERIFIED requires separate body and label observations. Share work additionally
requires a received ZIP observation, for example:

```json
{
  "receiver_observation": {"account": "dev@valueconnect.kr", "message_id": "received-id", "content_hash": "EXPECTED_SOURCE_HASH", "source_identity": ["rfc", "<original@example.test>"]},
  "label_observation": {"account": "dev@valueconnect.kr", "message_id": "received-id", "labels": ["01JD", "06온톨로지"]},
  "archive_observation": {"account": "dev@valueconnect.kr", "message_id": "received-id", "original_sha256": "SHA256_OF_RECEIVED_ZIP_ORIGINAL_EML"}
}
```

All observations must refer to the same actual receiver message. Receiver body
observations must match the planned `source_identity`: `["rfc", rfc_message_id]`,
or `["local", source_account, source_message_id]` when the RFC ID is absent. The
adapter must establish that match from original message metadata or the unique mirror
marker and its stored source mapping, rather than matching body text alone.
The adapter must download `original.zip`, extract `original.eml`, and hash those
received bytes for `archive_observation.original_sha256`. The journal compares that
hash with the original RFC hash recorded at SENDING; a sender header or authored-body
hash cannot substitute for this observation. Source/receiver label operations do not
require an archive, including messages already delivered directly to the destination.
Old share intents without a source RFC hash, or receiver intents without source
identity, cannot be verified under this contract; they require reconciliation.
Source-label work must refer to the original account/message and preserve prior labels. A sender's SENT
receipt alone never verifies receiver delivery or receiver labels. The live adapter
must recover the same authored representations from the forwarded content before
hashing; hashing an outer forward wrapper will correctly fail. No claim about Gmail
delivery, all-member coverage, or permissions follows from local tests.
The receipt JSON can be fabricated by a process allowed to invoke this CLI: matching
field values pass local validation, but provide no cryptographic or provider-backed
proof. Imported `VERIFIED` must not be presented as an authenticated live result by
itself. The adapter must capture receiver identity/body and independent label readback
from authenticated provider calls and preserve their provider request/message references
in the receipt. A sender SENT response, an outbound payload copied into receiver fields,
or assumed receiver label IDs does not meet that operational requirement. SQLite
append-only triggers prevent ordinary updates/deletes and duplicate-key INSERT/REPLACE,
including from a separate SQLite connection; idempotent application inserts skip rows
that already exist. They do not secure the journal
against a malicious database owner who can drop tables or replace the file.

## Pure MIME transport builder

`mime.mjs` constructs a Gmail API raw payload without credentials, filesystem access,
or network effects. The recipient is fixed to `dev@valueconnect.kr`; it rejects header
injection, invalid source/operation IDs and oversized encoded payloads. It includes a
readable text/HTML body, a unique operation marker, and `original.zip` containing the
unchanged `original.eml`. The ZIP uses STORE and CRC32 without dependencies.

Live pilot readback found that a `message/rfc822` attachment and an octet-stream
attachment named `.eml` could arrive as expanded body parts without the original file.
The archive avoids relying on that representation. Construction tests prove payload
properties only; a live adapter must download the received ZIP and compare the inner
RFC bytes with the original provider raw bytes. Delivery and recipient labels remain
separate checks. No live Gmail adapter is shipped in this directory.

`verifyReceivedOriginal` verifies the actual extracted RFC bytes against their expected
SHA-256, then parses exactly one Message-ID before the header/body boundary. Displayed
mirror text is not original-identity authority. It accepts CRLF/LF and legacy mixed CR
header separators without changing hashed bytes; ambiguous IDs fail closed.

## Label preflight recovery

`recovery.recover_label_preflight` is a local, label-only reconciliation helper. A trusted
adapter must first establish zero provider mutation attempts from durable private reports.
It appends FAILED to an eligible old receiver-label SENDING intent and plans exactly one
distinct receiver-label successor. Same-proof replay is idempotent, including interruption
between failure and successor creation; it never reopens the original intent or sends mail.
Uncertain effects, another failure reason, differing proof, and share operations are rejected.
The complete old receipt history must be exactly PLANNED→SENDING, optionally followed
by its matching FAILED proof. An earlier provider-result receipt contradicts zero effects
and prevents recovery even when the latest state and imported proof look eligible.

A legacy intent missing `source_identity` requires explicit original archive observation
matching its immutable review's RFC identity and content hash, plus received original SHA
and actual receiver message ID. The successor retains this receiver binding for readback.
Old payloads remain untouched. Report hashes and observation JSON are adapter assertions;
they do not authenticate Gmail. The live adapter must collect source/receiver observations
and independent post-modification GETs. Historical shares missing the current
original-byte send-intent field cannot be retroactively declared VERIFIED through
this helper.

## Historical delivery findings

`historical_delivery` records separate immutable `delivery_resolutions`; it never
changes an old operation or receipt, creates a send intent, or fabricates a pre-send
hash. CLI commands `resolve-delivery-archive` and `resolve-delivery-repair` accept
`{operation_id, proof}` and `{operation_id, repair_operation_id, proof}` respectively;
`delivery-status` accepts `{operation_id}`. Invalid or conflicting proof fails closed.

`ARCHIVE_CONFIRMED_AFTER_DELIVERY` requires independently obtained source bytes,
the actual receiver ZIP's original bytes, recorded sender/receiver IDs, RFC identity,
content hash, mirror/operation markers, and a separate required-label readback.
Existing legacy `raw_sha256` intent fields are crosschecked without renaming them.
`REPAIRED_BY_CONFIRMED_DELIVERY` keeps the original archive failure explicit and
links its exact prior sender/receiver/source references to an archive-confirmed
repair. Repair labels must also satisfy the original label set.

Status exposes both `historical_state` and the separate resolution. A resolved old
`SENT_UNVERIFIED` row remains that state; resolution is not a current-contract
`VERIFIED` receipt. Proof JSON/report hashes are trusted adapter assertions, not
cryptographic Gmail attestation. The live adapter must independently obtain them.

```sh
node --test tools/mail_governance/test_mime.mjs
```

## Coverage

`coverage` accepts `{account, query, cursor, next_cursor, count, outcome, capped}`;
cursor fields are strings or null, outcome `ok|failed|unknown`, capped boolean.
`coverage-status` accepts `{account, query}`. Start with null cursor, append each
successful page in sequence, finish with null next cursor. Any cap, missing page,
failure, unknown result, out-of-order page, or continuation after terminal page makes
coverage incomplete. Use a new query/run identity for a restarted scan; do not conceal
an unsuccessful page by rewriting it. A mailbox cohort and its complete set of queries
must be enumerated upstream before an all-members/all-mail completeness claim.
