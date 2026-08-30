-- Contract only. Do not apply without selecting the operational database and migration owner.

create table weekly_runs (
  run_id text primary key,
  contract_version text not null,
  meeting_at timestamptz not null,
  window_start timestamptz not null,
  window_end_exclusive timestamptz not null,
  late_alert_end timestamptz not null,
  status text not null check (status in ('DISCOVERED', 'PARTIAL', 'BLOCKED', 'READY', 'PUBLISHED')),
  idempotency_key text not null unique,
  lock_token text not null,
  created_at timestamptz not null,
  check (window_start < window_end_exclusive),
  check (window_end_exclusive <= meeting_at),
  check (meeting_at <= late_alert_end)
);

create table source_snapshots (
  snapshot_id text primary key,
  run_id text not null references weekly_runs(run_id),
  source_system text not null,
  source_uri text not null,
  source_record_id_ciphertext text,
  event_at timestamptz,
  fetched_at timestamptz not null,
  status text not null check (status in ('PASS', 'PARTIAL', 'FAIL', 'NOT_RUN', 'STALE')),
  raw_hash text not null,
  evidence_uri text not null,
  unique (run_id, source_system, source_uri, fetched_at)
);

create table canonical_positions (
  position_id text primary key,
  company_key text not null,
  title_key text not null,
  display_company text not null,
  display_title text not null,
  origin text not null check (
    origin in ('SCRAPED_STAGING', 'CLIENT_REQUESTED', 'CLIENT_SHARED', 'INTERNAL_CREATED')
  ),
  category text not null,
  lifecycle_stage text not null check (
    lifecycle_stage in ('ACTIVE', 'PIPELINE', 'CLOSING', 'CLOSED')
  ),
  active boolean not null,
  version integer not null,
  unique (company_key, title_key, version)
);

create table position_source_links (
  position_id text not null references canonical_positions(position_id),
  snapshot_id text not null references source_snapshots(snapshot_id),
  link_type text not null,
  confidence_basis text not null,
  is_active boolean not null,
  primary key (position_id, snapshot_id, link_type)
);

create table customer_intents (
  intent_id text primary key,
  position_id text not null references canonical_positions(position_id),
  snapshot_id text not null references source_snapshots(snapshot_id),
  intent_type text not null check (
    intent_type in (
      'REQUESTED', 'POSITION_SHARED', 'REQUIREMENT_CHANGED',
      'PIPELINE_FEEDBACK', 'REFERENCE_ONLY', 'NONE'
    )
  ),
  confidence text not null check (confidence in ('LOW', 'MEDIUM', 'HIGH')),
  client_priority text not null check (client_priority in ('TOP', 'HIGH', 'NORMAL', 'NONE')),
  evidence_ref text not null,
  observed_at timestamptz not null,
  classifier_version text not null,
  unique (position_id, snapshot_id, intent_type)
);

create table career_page_observations (
  observation_id text primary key,
  position_id text not null references canonical_positions(position_id),
  snapshot_id text not null references source_snapshots(snapshot_id),
  stable_job_url text not null,
  location_key text,
  job_hash text not null,
  observed_status text not null check (observed_status in ('OPEN', 'CLOSED', 'UNKNOWN')),
  parser_version text not null,
  unique (snapshot_id, stable_job_url)
);

create table dedupe_decisions (
  decision_id text primary key,
  run_id text not null references weekly_runs(run_id),
  duplicate_snapshot_id text not null references source_snapshots(snapshot_id),
  canonical_position_id text not null references canonical_positions(position_id),
  rule_version text not null,
  reason_code text not null,
  decided_by text not null,
  decided_at timestamptz not null,
  unique (run_id, duplicate_snapshot_id)
);

create table zero_result_assertions (
  run_id text not null references weekly_runs(run_id),
  collection_name text not null check (collection_name in ('positions', 'outreach_events')),
  source_snapshot_id text not null references source_snapshots(snapshot_id),
  provider_receipt_ref text not null,
  observed_count integer not null check (observed_count = 0),
  rule_version text not null,
  primary key (run_id, collection_name)
);

create table priority_scores (
  run_id text not null references weekly_runs(run_id),
  position_id text not null references canonical_positions(position_id),
  urgency_score integer not null check (urgency_score between 0 and 100),
  difficulty_score integer not null check (difficulty_score between 0 and 100),
  priority_score integer not null check (priority_score between 0 and 100),
  formula_version text not null,
  evidence_labels jsonb not null,
  input_hash text not null,
  primary key (run_id, position_id, formula_version)
);

create table proposal_send_attempts (
  send_attempt_id text primary key,
  run_id text not null references weekly_runs(run_id),
  consultant_id text not null,
  channel text not null check (channel in ('saramin', 'jobkorea', 'linkedin_rps')),
  candidate_key_hmac text not null,
  position_id text not null references canonical_positions(position_id),
  status text not null check (status in ('PENDING', 'SENT', 'FAILED')),
  provider_request_key text not null,
  provider_message_id_ciphertext text,
  provider_receipt_ref text,
  requested_at timestamptz not null,
  sent_at timestamptz,
  finalized_at timestamptz,
  evidence_uri text not null,
  check (
    (status = 'PENDING' and sent_at is null and finalized_at is null)
    or (
      status = 'SENT' and sent_at is not null and finalized_at is not null
      and provider_receipt_ref is not null
    )
    or (status = 'FAILED' and finalized_at is not null)
  ),
  unique (channel, candidate_key_hmac, position_id, provider_request_key)
);

create table consultant_position_focus (
  run_id text not null references weekly_runs(run_id),
  consultant_id text not null,
  position_id text not null references canonical_positions(position_id),
  verified_sent_count integer not null check (verified_sent_count > 0),
  unique_candidate_count integer not null check (unique_candidate_count > 0),
  active_days integer not null check (active_days > 0),
  focus_share numeric not null check (focus_share > 0 and focus_share <= 1),
  channel_mix jsonb not null,
  formula_version text not null,
  grass_evidence text not null check (grass_evidence = 'YELLOW_ELIGIBLE'),
  input_hash text not null,
  primary key (run_id, consultant_id, position_id, formula_version)
);

create table report_snapshots (
  report_snapshot_id text primary key,
  run_id text not null references weekly_runs(run_id),
  status text not null check (status in ('PARTIAL', 'BLOCKED', 'READY', 'PUBLISHED')),
  content_hash text not null,
  score_version text not null,
  evidence_bundle_hash text not null,
  brief_markdown text not null,
  created_at timestamptz not null,
  unique (run_id, content_hash)
);

create table publication_intents (
  publication_intent_id text primary key,
  report_snapshot_id text not null references report_snapshots(report_snapshot_id),
  target_name text not null,
  target_id text not null,
  idempotency_key text not null unique,
  expected_content_hash text not null,
  schema_readback_ref text not null,
  status text not null check (
    status in ('INTENT_RECORDED', 'WRITE_STARTED', 'UNKNOWN_OUTCOME', 'READBACK_VERIFIED', 'FAILED')
  ),
  created_at timestamptz not null,
  unique (report_snapshot_id, target_name, target_id)
);

create table publication_receipts (
  receipt_id text primary key,
  publication_intent_id text not null unique references publication_intents(publication_intent_id),
  external_object_id text not null,
  readback_at timestamptz not null,
  readback_content_hash text not null,
  readback_report_snapshot_id text not null,
  persisted_receipt_ref text not null unique,
  verified boolean not null,
  check (verified = true)
);
