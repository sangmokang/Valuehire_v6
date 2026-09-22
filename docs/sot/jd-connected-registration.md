# JD Connected Registration SOT

Last updated: 2026-09-22. Applies to Codex and Claude.

This document is the single source of truth for turning a JD source into candidate-facing registration text and proving that Saramin or JobKorea contains what was intended. Runtime-specific skills should link here instead of copying their own portal logic.

## Scope

The workflow covers:

- raw JD capture from pasted text or an official job URL
- company briefing research for candidate-facing context
- semantic unit construction
- deterministic packet generation
- Aside browser portal entry
- saved UI readback
- one owner report email per registered position when explicitly requested

The workflow does not imply candidate outreach, bulk posting, unattended login automation, paid actions, ontology/org mapping, or reuse of old company caches unless the user asks for those actions in the current task. When the user asks for LinkedIn/company organization research as part of a JD packet or owner report, run the company-intelligence workflow before final wording and report the scope, sources, and unknowns.

## Source Identity

User-supplied sources are separate jobs only when the user says so or when company, role, and current source identity do not match. A pasted JD and a URL are often two references to the same job; do not split or merge blindly.

For pasted text:

- preserve the raw text exactly, including truncation
- set `source_kind=pasted_text`
- set `source_status=READY_SOURCE` only after company, position, and body are readable

For URL input:

- fetch the current official page
- verify company, position title, and page body against the user request
- set `source_kind=url`
- set `source_status=READY_SOURCE` only when the page currently matches the requested job
- if the page differs from the pasted prompt, do not blend them; record separate jobs only when identity differs, otherwise mark `NEEDS_SOURCE_REVIEW`

Do not use previous drafts, old generated copy, stale CDP flows, or hidden assumptions as source truth.

## Company Briefing

When company context is requested or needed for candidate copy, collect nine facts with sources:

1. company history
2. financial state
3. funding stage
4. cumulative funding
5. product lineup
6. recent CEO interview
7. CEO profile
8. company location
9. headcount

Use current public sources or approved internal records. Separate `company_fact_status` from `jd_source_status`. Unknown facts do not block packet generation unless the user required that fact in the candidate-facing copy; then mark `NEEDS_SOURCE_REVIEW`.

Candidate-facing copy may include sourced facts and careful date labels. Unknown facts are omitted. Do not soften an unknown into a claim. Candidate-facing text must not include internal uncertainty labels such as `unknown`, `not verified`, source IDs, or audit tags. Public measurement bases and dates, such as 국민연금 가입자 수, must remain when needed to avoid misleading headcount claims.

Company introductions in Saramin and JobKorea candidate-facing fields are bullet-first and concise by default. Prefer short bullets for history/funding, product and channel scale, team mission, traffic or GMV scale, and leadership facts when those facts are relevant and sourced. Avoid one long prose paragraph that mixes every company fact. Keep detailed source URLs and caveats in the owner report or evidence JSON, not in the candidate-facing field.

## Candidate-Facing Removal Rules

Remove these from every portal field and owner email's "registered text" candidate body:

- employer apply URLs, ATS links, career page buttons, and QR codes
- employer direct emails and "apply here" wording
- "자사 지원", "지원하기", "채용페이지에서 지원" style CTAs

Replace next-step language with ValueConnect routing, for example: `후속 절차는 밸류커넥트를 통해 안내드립니다.`

Do not remove actual hiring process facts such as interview stages, tasks, reference checks, employment type, location, or required documents by default.

If the user explicitly excludes generic or obvious candidate-facing boilerplate, such as the entire support-documents section, employment type `정규직`, `채용 시 마감`, or a self-evident office label, remove it from Saramin/JobKorea candidate fields and owner-email registered-text blocks. Preserve the raw fact in `excluded_units` with `reason` starting `explicit_user_exclusion`, including the user instruction, source, and captured text. This is an intentional source-coverage exception, not a renderer drop.

## Semantic Units

Before generation, map every substantive raw JD statement to a unit ID or an explicit exclusion reason (direct application routing, site navigation, or duplicate display text). Check conditions and hiring stages line by line. A packet validates curated units, not the completeness of the upstream extraction; missing raw-source coverage blocks entry.

The unit file is the only input to deterministic packet generation. Required top-level fields:

- `company`
- `position`
- `source_url` or source marker
- `captured_at`
- `source_status`
- `jd_id`
- `company_slug`
- `position_slug`
- `units`
- optional `excluded_units`

Each unit must have:

- `id`
- `section`
- `kind`
- `meaning`
- `full`
- `compact`
- `source`

Each `excluded_units` item must have:

- `id`
- `section`
- `reason` beginning with `explicit_user_exclusion`
- `full`
- `source`

Supported sections, in display order: `company`, `team`, `domain`, `role`, `duties`, `requirements`, `preferred`, `growth`, `conditions`, `process`, `documents`.

Core hiring facts use `kind=core` and cannot be dropped. Company and extra units may move between fields to fit portal limits, but each source unit must appear exactly once across the packet fields for that portal unless the packet explicitly returns `BLOCKED` or the raw fact is represented in `excluded_units` under an explicit current-user exclusion.

## Shared CLI Contract

Preferred commands:

```bash
PYTHONPATH=scripts python3 -m jd_channels packet --source <units.json> --channel saramin --output <packet.json>
PYTHONPATH=scripts python3 -m jd_channels packet --source <units.json> --channel jobkorea --output <packet.json>
PYTHONPATH=scripts python3 -m jd_channels readback --packet <packet.json> --observed <observed.json> --output <readback.json>
```

The packet command returns:

- `READY_FOR_UI` when every generated field fits and contains no known forbidden text or portal-risk characters
- `BLOCKED` when length, source, unit assignment, direct-apply text, invisible characters, or portal-risk checks fail

The readback command returns:

- `COMPLETE` when every required persistent field and required transient field has been observed and matches
- `PARTIAL` only for JobKorea when persistent position fields match but transient proposal evidence is incomplete
- `FAIL` on mismatch

Required dependencies are this SOT, the active packet/readback script implementation, and any referenced contracts. If any required dependency is missing in the active tree, record `BLOCKED_DEPENDENCY` and stop that lane. Do not claim automation exists until the command is present and executed in the active tree.

## Portal Field Limits

### Saramin

Fields:

- `hiringTitle`: title, 35 characters max
- `offerComment`: body field 1, 2,000 characters max
- `chargeWork`: body field 2, 2,000 characters max

Use both 2,000-character fields as one candidate-facing surface. A good split usually places company briefing, team, role, growth, conditions, and process in field 1, then duties, requirements, and preferred qualifications in field 2. The split may change as long as facts are preserved exactly once and readback passes.

For candidate readability, `offerComment` should normally start with ValueConnect routing and a concise bullet-first `[회사 소개]`, then team/growth/process/remaining conditions. Do not use a long company prose paragraph when the same facts can be carried as bullets.

### JobKorea

Fields:

- `GI_PSTN`: title, 50 characters max
- `proposalMessage`: position proposal "제안 내용"; target 3,000 characters including spaces and LF
- `EXEC_WORK`: registration modal "입사 후 업무"; target 1,000 characters including spaces
- `ST`: registration modal "우대사항"; target 1,000 characters including spaces

Observed HTML limits are `proposalMessage maxlength=3000`, `EXEC_WORK maxlength=1000`, and `ST maxlength=1000`. `EXEC_WORK` and `ST` are each 1,000 characters, not a combined 1,000-character budget. The user also provided a measured accepted proposal sample of 2,999 characters including spaces/LF and 2,351 characters after removing spaces and line breaks. The permanent modal fields are tight. Put substantial company/team context into `proposalMessage`, but use free `ST` capacity for overflow duties, qualifications, process, and conditions before leaving core facts transient. Keep explicit section headings so fields do not reclassify required qualifications as preferences.

`proposalMessage` company context follows the same concise bullet-first company-introduction rule as Saramin. Keep generic application-document boilerplate out when explicitly excluded; do not spend transient proposal space on statements professional candidates already know unless the user requests them.

`proposalMessage` is transient proposal content unless a screen proves otherwise. It must be injected and verified for each candidate proposal or position proposal operation. Do not report it as saved permanent position content merely because the permanent modal saved.

If `GI_PSTN` is disabled in JobKorea, treat the observed disabled title as the canonical portal identity for that saved record. Do not overwrite it blindly. If the disabled title differs from the intended packet title, report the binding explicitly and decide whether the existing portal record is the correct target before saving.

### LinkedIn RPS

RPS content limit is 1,900 characters total. This is a compact outreach/inmail body, not a Saramin/JobKorea registration packet. Do not run RPS external actions unless the user explicitly requests RPS.

## Aside Operation

Use the Aside browser and the user's existing logged-in portal sessions. The main operator owns live browser work; do not delegate live portal manipulation to subagents. Do not implement or call legacy automatic login, fixed browser credentials, old CDP snippets, or employment defaults.

Before saving:

- confirm the target portal and company/position identity
- check for duplicate existing position records
- paste packet field values exactly
- close autocomplete/chip UI only after the selected value is visibly committed
- capture field counts and any portal warnings

After saving:

- reopen the saved position or proposal
- read every field back from the UI
- for new observations, record both `fresh_saved_position` and `persisted_reopen`; a current-screen value without a persisted reopen is not saved readback
- normalize only documented portal transformations
- compare against the packet with the readback CLI
- preserve screenshot/HTML/text artifacts outside git if they contain portal or candidate data

Success messages, toast notifications, and "button clicked" states are not completion evidence.

## Known Portal Transformations

Current measured transformations:

- JobKorea stores en dash as `?`
- JobKorea permanent fields convert ASCII `>` into `≫`. For interview process separators, use `→` in semantic units; it survives JobKorea and becomes `>` in Saramin. Do not silently normalize failed readback away.
- JobKorea stores single quotes as backticks
- Saramin deletes right arrow `→`
- Saramin encodes ASCII single quote as literal `&#39;` on edit readback. Adjust quotation formatting in semantic units before entry; do not normalize this away as successful exact storage.

The renderer should sanitize these before UI entry. If a new transformation appears during readback, record it and do not pass the registration until packet generation or expected comparison accounts for it.

## Live Observations

These are observed portal outcomes, not universal guarantees.

- Saramin QA Manager live save: saved position `1731926`; two body fields measured 1,107 and 1,048 characters; saved readback matched.
- JobKorea QA live save: existing title field was disabled and displayed `뤼튼, QA`; group `1505694`, old position `1598265` updated to `1600822`; permanent fields measured 571 and 475 characters; saved position readback matched exactly.
- JobKorea QA proposal: proposal text measured 1,103 characters and filled exactly on the active proposal screen, but after save-checkbox and reopen it reset to the 112-character default. No candidate was sent. Therefore position status was `COMPLETE`, proposal status was `NOT_SAVED`, and overall status was `PARTIAL`.

- Bunjang Global Team Lead live save: Saramin `1833171`, body fields 1810/1410; JobKorea group `1506767`, final position `1600840`, body fields 1000/715. Permanent fields matched fresh readback. Proposal1503 reset to112 on reopen, so proposal `NOT_SAVED`.

This observation creates a rule: when JobKorea proposal text is required for a candidate send, replay the proposal packet into the proposal field during that authorized send operation and verify the active proposal screen. Do not mark the whole JobKorea job `COMPLETE` unless both the persisted position fields and the required proposal state are proven for the specific operation. Proposal completion additionally requires `fresh_saved_proposal=true` and a proposal ID; position reopen evidence alone is insufficient.

## Owner Report Email

Send only when the user explicitly requested it or the current task instruction already authorized it. If already authorized, do not ask for a second approval before the owner report. Send one email per position after its requested portal outcomes are verified, to the explicit recipient.

The email must include:

- portal name
- company and position
- saved position id and proposal id when available
- packet status and readback status
- field names and character counts
- the complete original JD source text plus its URL/source marker
- exact registered text for each field
- partial status and reason, if any
- remaining caveats such as `proposalMessage` transient verification
- explicit `excluded_units` and the current user instruction that authorized each exclusion
- LinkedIn/company organization research scope when requested, including sources checked and unresolved unknowns

Do not combine two positions into one report when the user asked to process them separately.

## Status Vocabulary

Use these exact labels in artifacts and reports:

- `READY_SOURCE`: source captured and suitable for unit extraction
- `NEEDS_SOURCE_REVIEW`: source missing, changed, or conflicting
- `READY_FOR_UI`: packet generated and safe to enter
- `BLOCKED`: packet cannot safely be entered
- `UI_ENTERED`: fields entered but not saved/read back
- `READBACK_COMPLETE`: saved UI readback matches packet
- `READBACK_PARTIAL`: only part of the required UI readback is proven
- `PROPOSAL_NOT_SAVED`: JobKorea proposal text was observed in the active proposal screen but did not persist after reopen
- `EMAIL_SENT_VERIFIED`: owner report sent and sent-mail/readback evidence recorded

For a Saramin registration, `READBACK_COMPLETE` plus `EMAIL_SENT_VERIFIED` completes a user request that asks for actual registration and report email. For JobKorea, permanent position readback can be complete while proposal readback is `PROPOSAL_NOT_SAVED`; that outcome is `READBACK_PARTIAL`, not whole-job complete.


## Evidence boundary and packet integrity

`source_hash_version=2` covers company, position, source URL/status, JD ID and unit IDs/sections/full text. Readback recomputes it, rejects unresolved packet errors, and validates raw counts and field content. It detects inconsistent or accidentally modified artifacts; it is not a signature or authority to write/send. The operator must capture real browser state. Fabricating `observed.json` can fabricate evidence, so retain the original capture and its time/URL outside git, and do not describe this as tamper-proof browser attestation.

Disabled-title binding only accepts the title value already in the reviewed packet. Adding `approved_bound_title`, `title`, or similar alias metadata cannot authorize a different title during comparison. Before an existing disabled-title update, verify the target record and construct the reviewed packet using its actual retained title, recording the source role and before/group IDs.

Readback JSON is the result artifact. Input packets remain immutable generation artifacts; their initial `NOT_VERIFIED` markers are not overwritten by the readback command. Read the result file. Exit code 3 requires inspection of `position_status` and `proposal_status`; it is never an unqualified success code.

See [Aside operations](jd-aside-operations.md) for the repeated browser procedure. The tested local/manual workflow does not provide unattended registration, server-side browser attestation, or candidate-send automation.
