# Notion Weekly Golden Sample contract

Read this file when the user asks to standardize, copy, or create a weekly Notion dashboard or a
`FY..W..-1` Golden Sample. The machine contract is
`contracts/weekly-ops/notion-golden-sample-v1.json`.

## Prompt audit

Reject or rewrite a request before execution when it has any of these defects:

- it asks the model to decide what management should execute without a fixed formula;
- it mixes recent client intake, late-stage pipeline, and market accessibility in one priority list;
- it treats a new ClickUp card, a reactivated candidate, and a stage movement as the same count;
- it asks for a four-week trend but provides fewer than four source-bound weekly snapshots;
- it fills an unread channel or week with zero;
- it calls an unfiltered LinkedIn result count a qualified candidate pool;
- it repeats one candidate-position record in multiple current-state counts;
- it publishes candidate display names outside the exact user-authorized private Notion page.

## Semantic corrections

1. `최근 인입 포지션` is a chronological fact list. It has no P0/P1 and no action verbs.
2. `시장 접근성` is a LinkedIn Recruiter search measurement with frozen filters and a reviewed
   sample. It is not inferred from a title or a single visible profile.
3. `소싱 커버리지 Priority` is the versioned formula output defined in the JSON contract. It is an
   operating attention index, not a management decision.
4. `포지션 변동 사항` lists evidenced opens, changes, closing signals, hires, and closures without
   prescribing the response.
5. `후보자 소싱` separates Saramin, JobKorea, and LinkedIn Recruiter and shows four contiguous weeks.
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
  iso_week, window_start, window_end_exclusive
  live_client_position_count
  new_task_count, reactivated_task_count
  active_pipeline_count, interview_pipeline_count
  channel_outreach.saramin|jobkorea|linkedin_rps
recent_client_positions[]:
  position_id, company, title, requested_headcount, observed_at, intent_type,
  source_snapshot_id, evidence_refs
linkedin_market_searches[]:
  position_id, search_url_ref, query, geography, job_titles, skills,
  seniority_or_years, languages, result_count_lower_bound, count_is_exact,
  qualified_sample_size, qualified_sample_matches, captured_at, source_snapshot_id
candidate_tasks[]:
  task_id, candidate_key_hmac, position_id, created_at, current_stage, source_snapshot_id
pipeline_events[]:
  candidate_key_hmac, position_id, from_stage, to_stage, event_at, source_snapshot_id
position_changes[]:
  position_id, change_type, observed_at, source_snapshot_id, evidence_refs
private_display_map:
  candidate_key_hmac -> candidate_display_name
```

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
Review at least the first 20 results against the role's must-have criteria. Do not store profile names
or URLs in the report bundle.

The code computes:

```text
precision_rate = qualified_sample_matches / qualified_sample_size
market_accessibility = clamp(pool_points(result_count_lower_bound)
                             + precision_adjustment(precision_rate), 0, 100)
```

If the required filters or 20-profile sample are missing, the position is `UNRANKED`. Do not replace
the missing search with general web counts or an LLM estimate.

The separate sourcing coverage index is:

```text
coverage_priority = request_recency_points
                  + active_pipeline_gap_points
                  + market_scarcity_points
```

Render the three components beside the total. Use `A/B/C` only as formula bands and never write
“즉시 실행”, “우선 착수”, “해야 한다”, or similar managerial directives.

## Fixed Notion layout

The first viewport is a compact dashboard:

1. `4주 KPI` — live client positions, new tasks, active pipeline, interview pipeline;
2. `최근 인입 포지션` — company, role, headcount, received date, evidence status;
3. `시장 접근성 / 소싱 커버리지 Priority` — formula inputs and result;
4. `포지션 변동 사항`;
5. `후보자 소싱` — four-week channel table.

Put the following detailed tables in collapsed toggles:

6. `지난주 신규 Task`;
7. `지난주 이동 후보자`;
8. `활성 Pipeline`;
9. `면접 직전 Pipeline`;
10. `데이터 커버리지`.

The detailed lists may resolve candidate display names only at private Notion write time. The hashed
snapshot, Git, email, admin page, and reviewer artifacts keep `candidate_key_hmac` only.

## Executable prompting contract

Use this block as the normalized prompt for Claude or Codex:

```text
MODE
NOTION_WEEKLY_GOLDEN_SAMPLE_V1

GOAL
Create one private FY{yy}W{iso_week}-1 Notion Golden Sample from four source-bound weekly snapshots.
Report facts and deterministic formula outputs. Do not issue management directives.

AUTHORITY
- Recent intake is listed by observed_at descending; it is not ranked.
- Only the contract-defined sourcing_coverage_priority may emit A/B/C.
- An unverified LinkedIn market search is UNRANKED.
- Unknown history or channels render as —, never 0.

SOURCE OF TRUTH
- Live client positions: canonical ClickUp positions with CLIENT_REQUESTED or CLIENT_SHARED origin;
  exclude SCRAPED_STAGING, closedpositions, and complete.
- New Task: first canonical candidate_key_hmac + position_id created in the closed week.
- Reactivation and stage movement are separate events.
- Current pipeline: latest state per candidate_key_hmac + position_id at the cutoff.
- Sourcing: provider-readback sends, separated by Saramin, JobKorea, and LinkedIn Recruiter.

MARKET ANALYSIS
For each active recent-client position, use an authenticated Aside LinkedIn Recruiter saved search
with frozen geography, job title, skills, seniority/years, and language filters. Review at least 20
results. Compute market_accessibility and sourcing_coverage_priority from
contracts/weekly-ops/notion-golden-sample-v1.json. Do not estimate missing inputs.

DEDUPE
Normalize company/title to one position_id. Deduplicate current candidate records by
candidate_key_hmac + position_id. Keep the latest stage at cutoff. Do not count a reactivation as a
new canonical Task. Preserve source lineage and list ambiguous records under data coverage.

RENDER
Use the exact section order in the contract. Keep the first five sections dashboard-length and put
candidate-level detail in collapsed toggles. Rename 운영 변경 to 포지션 변동 사항 and 소싱 실행 to
후보자 소싱. Explain every total with its unit and cutoff; add no generic performance commentary.

PRIVACY
Resolve candidate display names only while writing the explicitly authorized private Notion page.
Never place those names in Git, email, admin web, logs, or the review bundle.

STOP
Before writing, require four week slots, metric status per cell, source lineage, dedupe results, and
complete LinkedIn measurement for every ranked position. After writing, reload the Notion page and
verify title, section order, totals, trend cells, private visibility, and absence of managerial
directive phrases. If any check fails, return PARTIAL and name the exact missing source or field.
```

## Acceptance conditions

- The page title matches `FY{yy}W{iso_week}-1` and uses template version
  `notion-weekly-golden-v1`.
- The top KPI section contains exactly four contiguous weeks for all required metrics.
- Live position counts exclude scraped and closed positions; headcount is a separate field.
- Channel sourcing is split into three rows and missing cells are not zero-filled.
- Recent intake contains no P0/P1 or imperative action sentence.
- Every ranked position has a complete LinkedIn search and at least 20 reviewed results.
- New Task, reactivation, movement, active pipeline, and interview pipeline totals use their own units.
- Current pipeline has one row per canonical candidate-position identity.
- Candidate display names exist only in the authorized private Notion detail.
- A reload readback matches the expected page title, section order, totals, and metric states.
