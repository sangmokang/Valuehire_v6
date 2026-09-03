# Notion Weekly Golden Sample contract

Read this file when the user asks to standardize, copy, or create a weekly Notion dashboard or a
`FY..W..-1` Golden Sample. Authority is `docs/sot/weekly-ops-contract.md`. The v1 machine contract is
`contracts/weekly-ops/notion-golden-sample-v1.json`, but it is legacy
`CONTRACT_ONLY_NOT_EXECUTABLE`. Use this reference for audit and migration only. Publication is
`NOT_RUN` until the SOT-required v2 contract, callable registry, CLI, and runtime acceptance exist.

## Prompt audit

Reject or rewrite a request before execution when it has any of these defects:

- it asks the model to decide what management should execute without a fixed formula;
- it mixes recent client intake, late-stage pipeline, and market accessibility in one priority list;
- it treats a new ClickUp card, a reactivated candidate, and a stage movement as the same count;
- it asks for a four-week trend but provides fewer than four source-bound weekly snapshots;
- it fills an unread channel or week with zero;
- it calls an unfiltered LinkedIn result count a qualified candidate pool;
- it repeats one candidate-position record in multiple current-state counts;
- under an executable Golden v2 contract, it publishes candidate display names outside the exact
  user-authorized private Notion page.

## Semantic corrections

1. `최근 인입 포지션` is a chronological fact list. It has no P0/P1 and no action verbs.
2. `시장 접근성` is a LinkedIn Recruiter search measurement with frozen filters and a reviewed
   sample. It is not inferred from a title or a single visible profile.
3. `소싱 커버리지 위험지수` is the versioned formula output defined in the JSON contract. It is a
   coverage-risk measurement, not a management decision.
4. `포지션 변동 사항` lists evidenced opens, changes, closing signals, hires, and closures without
   prescribing the response.
5. `후보자 소싱` separates Saramin, JobKorea, and LinkedIn Recruiter and shows four contiguous weeks.
   It contains the required `channel_coverage`, `consultant_focus`, and `excluded_rows` collections.
6. `지난주 신규 Task` counts canonical candidate-position identities created in the closed week.
   Reactivation and stage movement are separate metrics.
7. `활성 Pipeline` uses the latest state at the cutoff. `면접 Pipeline` is the narrower subset defined
   by the contract; neither count may double-count a candidate-position identity.

## Required source input

```text
run:
  meeting_at, window_start, window_end_exclusive, timezone
target:
  notion_database_id, template_version=notion-weekly-golden-v1, publication_mode
week_series[4]:
  week_label, metric_iso_week, window_start, window_end_exclusive
  live_client_position_count
  new_task_count, reactivated_task_count
  active_pipeline_count, interview_pipeline_count, pre_interview_pipeline_count
  channel_outreach.saramin|jobkorea|linkedin_rps
recent_client_positions[]:
  position_id, company, title, requested_headcount, observed_at, intent_type,
  source_snapshot_id, evidence_refs
linkedin_market_searches[]:
  position_id, search_url_ref, query, geography, job_titles, skills,
  seniority_or_years, languages, sort_order, ordered_result_snapshot_hash,
  must_have_predicates, first 20 HMAC-unique sample_evaluations,
  result_count_lower_bound, count_is_exact, provider_result_receipt_ref, evaluated_sample_size=20,
  qualified_sample_matches, captured_at, source_snapshot_id
candidate_tasks[]:
  task_id, candidate_key_hmac, position_id, hiring_cycle_id, created_at, current_stage, source_snapshot_id
pipeline_events[]:
  candidate_key_hmac, position_id, hiring_cycle_id, from_stage, to_stage, event_at, source_snapshot_id
position_changes[]:
  position_id, change_type, observed_at, source_snapshot_id, evidence_refs
```

Legacy v1 input must not contain a display-name map or any candidate display name. A future v2 resolver
is not an input to this audit contract; it can run only at an authorized private write after all six exact
SOT-named v2 artifacts pass their wrapped acceptance gate. A caller assertion never satisfies that gate.

Every metric cell is an object, not a bare number:

```text
value: <non-negative integer|null>
status: VERIFIED|PARTIAL|NOT_RUN
as_of: <ISO-8601>
source_snapshot_id: <opaque ID|null>
```

`value=null` renders as `—`. Zero is permitted only with `status=VERIFIED` and a source-bound zero
receipt. A trend direction is rendered only when at least three of the four observations are verified.

## LinkedIn market measurement

Use the authenticated Aside LinkedIn Recruiter surface. Freeze one search per canonical position and
record its URL reference, query, geography, job-title Boolean, skills, seniority/years, and language.
Review exactly the captured order's first 20 HMAC-unique results against the same versioned must-have
predicates. Each row has exactly `candidate_key_hmac`, `rank`, and `predicate_results`; ranks are 1..20,
predicate keys equal the frozen must-have set, and values are `TRUE|FALSE|UNKNOWN`. Do not store profile
names or URLs in the report bundle.

The code computes:

```text
precision_rate = qualified_sample_matches / evaluated_sample_size
market_accessibility = (pool_points * precision_points * 100) // 2500
```

If the required filters or 20-profile sample are missing, the position is `UNRANKED`. Do not replace
the missing search with general web counts or an LLM estimate.
`pool_points` maps `result_count_lower_bound`; `precision_points` maps
`qualified_sample_matches / evaluated_sample_size`. The 0-point pipeline-gap bucket applies to three
or more active candidates.
`week_label` is the report slot, while `metric_iso_week` names the closed data window. For example,
FY26W36 can report the closed FY26W35 window; the fields are never aliases.
The result count and exactness flag come from an immutable PASS-bound provider result receipt and may
not be supplied independently by the market row.
Render `market_formula_version` and `coverage_risk_formula_version` as separate fields.

The separate sourcing coverage index is:

```text
sourcing_coverage_risk = recency_points
                       + pipeline_gap_points
                       + scarcity_points
```

Render the three components beside the total. Use `A/B/C` only as formula bands and never write
“즉시 실행”, “우선 착수”, “해야 한다”, or similar managerial directives.

## Fixed Notion layout

The first viewport is a compact dashboard:

1. `4주 KPI` — live client positions, new tasks, active pipeline, interview pipeline;
2. `최근 인입 포지션` — company, role, headcount, received date, evidence status;
3. `시장 접근성 / 소싱 커버리지 위험지수` — formula inputs and result;
4. `포지션 변동 사항`;
5. `후보자 소싱` — four-week channel table.

Put the following detailed tables in collapsed toggles:

6. `지난주 신규 Task`;
7. `지난주 재활성 Task`;
8. `지난주 이동 후보자`;
9. `활성 Pipeline`;
10. `면접 직전 Pipeline`;
11. `데이터 커버리지`.

Legacy v1 preflight never resolves candidate display names and keeps `candidate_key_hmac` only. A future
executable v2 contract may allow names only at explicitly authorized private Notion write time; the hashed
snapshot, Git, email, admin page, and reviewer artifacts still keep `candidate_key_hmac` only.
Every section uses the exact row fields in `section_schemas`; missing fields make the section
PARTIAL/BLOCKED rather than inviting generated filler.
`마감 후 경보` is the `post_cutoff_alerts` collection inside `데이터 커버리지`, not a twelfth section.
Ineligible coverage-risk lifecycles keep the fields with null/`UNRANKED`/`INELIGIBLE_LIFECYCLE`.

## Legacy prompting contract — audit and migration only

Do not publish from this block. Use it only to inventory v1 inputs while external writes remain forbidden:

```text
MODE
NOTION_WEEKLY_GOLDEN_SAMPLE_V1

PUBLICATION_MODE
PREFLIGHT_ONLY

EXTERNAL_WRITE
FORBIDDEN

GOAL
Create one private FY{yy}W{iso_week}-1 Notion Golden Sample from four source-bound weekly snapshots.
Report facts and deterministic formula outputs. Do not issue management directives.

AUTHORITY
- Recent intake is listed by observed_at descending; it is not ranked.
- Only the contract-defined sourcing_coverage_risk may emit A/B/C.
- An unverified LinkedIn market search is UNRANKED.
- Unknown history or channels render as —, never 0.

SOURCE OF TRUTH
- Live client positions: canonical ClickUp positions with CLIENT_REQUESTED or CLIENT_SHARED origin;
  exclude SCRAPED_STAGING, closedpositions, and complete.
- New Task: first canonical candidate_key_hmac + position_id + hiring_cycle_id created in the closed week.
- Reactivation and stage movement are separate events.
- Current pipeline: latest state per candidate_key_hmac + position_id + hiring_cycle_id at the cutoff.
- Sourcing: provider-readback sends, separated by Saramin, JobKorea, and LinkedIn Recruiter.

MARKET ANALYSIS
For each active recent-client position, use an authenticated Aside LinkedIn Recruiter saved search
with frozen geography, job title, skills, seniority/years, and language filters. Review exactly the
captured order's first 20 HMAC-unique results. Compute market_accessibility and sourcing_coverage_risk from
contracts/weekly-ops/notion-golden-sample-v1.json. Do not estimate missing inputs.

DEDUPE
Normalize company/title to one position_id. Deduplicate current candidate records by
candidate_key_hmac + position_id + hiring_cycle_id. Keep the latest stage at cutoff. Do not count a reactivation as a
new canonical Task. Preserve source lineage and list ambiguous records under data coverage.

RENDER
Use the exact section order in the contract. Keep the first five sections dashboard-length and put
candidate-level detail in collapsed toggles. Rename 운영 변경 to 포지션 변동 사항 and 소싱 실행 to
후보자 소싱. Explain every total with its unit and cutoff; add no generic performance commentary.

PRIVACY
Do not resolve candidate display names in this legacy preflight. A future executable v2 contract may
resolve them only while writing an explicitly authorized private Notion page. Never place those names in
Git, email, admin web, logs, or the review bundle.

STOP
Preflight requires four week slots, metric status per cell, source lineage, dedupe results, and complete
LinkedIn measurement for every ranked position. Do not write from this legacy block. Return
`NOT_RUN` and list the exact missing v2 contract, callable registry, CLI, runtime acceptance, source, or
field. The future v2 contract must define reload verification for title, section order, totals, trend
cells, private visibility, and absence of managerial directive phrases.
```

## Migration-contract consistency conditions — not publication acceptance

- The page title matches `FY{yy}W{iso_week}-1` and uses template version
  `notion-weekly-golden-v1`.
- The top KPI section contains exactly four contiguous weeks for all required metrics.
- Live position counts exclude scraped and closed positions; headcount is a separate field.
- Channel sourcing is split into three rows and missing cells are not zero-filled.
- Recent intake contains no P0/P1 or imperative action sentence.
- Every ranked position has a complete LinkedIn search and exactly the first 20 HMAC-unique reviewed results.
- New Task, reactivation, movement, active pipeline, and interview pipeline totals use their own units.
- Current pipeline has one row per canonical candidate-position identity.
- Legacy v1 contains no candidate display names; a future v2 may resolve them only in an authorized
  private Notion detail.
- A future executable v2 readback must match the expected page title, section order, totals, and metric
  states; v1 performs no write or readback.
