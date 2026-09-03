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
  check (window_end_exclusive = window_start + interval '7 days'),
  check (
    window_end_exclusive =
      (date_trunc('week', meeting_at at time zone 'Asia/Seoul') at time zone 'Asia/Seoul')
  ),
  check (window_end_exclusive <= meeting_at),
  check (meeting_at <= late_alert_end)
);

create function weekly_evidence_refs_are_valid(evidence_refs jsonb)
returns boolean
language sql
immutable
as $$
  select case
    when jsonb_typeof(evidence_refs) <> 'array'
      or jsonb_array_length(evidence_refs) = 0
    then false
    else (
      select count(*) = count(distinct evidence_ref #>> '{}')
        and bool_and(
          jsonb_typeof(evidence_ref) = 'string'
          and btrim(evidence_ref #>> '{}') <> ''
        )
      from jsonb_array_elements(evidence_refs) as refs(evidence_ref)
    )
  end
$$;

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
  evidence_refs jsonb not null check (weekly_evidence_refs_are_valid(evidence_refs)),
  evidence_uri text not null check (btrim(evidence_uri) <> ''),
  unique (run_id, snapshot_id),
  unique (run_id, source_system, source_uri, fetched_at)
);

create function weekly_reject_mutation()
returns trigger
language plpgsql
as $$
begin
  raise exception 'IMMUTABLE_WEEKLY_LEDGER:%', tg_table_name;
end
$$;

create function weekly_reject_truncate()
returns trigger
language plpgsql
as $$
begin
  raise exception 'WEEKLY_LEDGER_TRUNCATE_FORBIDDEN:%', tg_table_name;
end
$$;

create function weekly_run_transition_is_valid()
returns trigger
language plpgsql
as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'WEEKLY_RUN_DELETE_FORBIDDEN';
  end if;
  if row(
    new.run_id, new.contract_version, new.meeting_at, new.window_start,
    new.window_end_exclusive, new.late_alert_end, new.idempotency_key,
    new.lock_token, new.created_at
  ) is distinct from row(
    old.run_id, old.contract_version, old.meeting_at, old.window_start,
    old.window_end_exclusive, old.late_alert_end, old.idempotency_key,
    old.lock_token, old.created_at
  ) then
    raise exception 'WEEKLY_RUN_IDENTITY_IMMUTABLE';
  end if;
  if not (
    old.status = new.status
    or (
      old.status = 'DISCOVERED'
      and new.status in ('PARTIAL', 'BLOCKED', 'READY')
    )
    or (
      old.status = 'PARTIAL'
      and new.status in ('BLOCKED', 'READY')
    )
    or (
      old.status = 'BLOCKED'
      and new.status in ('PARTIAL', 'READY')
    )
    or (
      old.status = 'READY'
      and (
        new.status = 'BLOCKED'
        or (
          new.status = 'PUBLISHED'
          and weekly_run_publication_is_complete(new.run_id)
        )
      )
    )
  ) then
    raise exception 'WEEKLY_RUN_TRANSITION_INVALID';
  end if;
  return new;
end
$$;

create trigger weekly_run_transition_guard
before update or delete on weekly_runs
for each row execute function weekly_run_transition_is_valid();

create trigger source_snapshots_immutable
before update or delete on source_snapshots
for each row execute function weekly_reject_mutation();

create trigger source_snapshots_no_truncate
before truncate on source_snapshots
for each statement execute function weekly_reject_truncate();

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

create function weekly_canonical_position_transition_is_valid()
returns trigger
language plpgsql
as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'CANONICAL_POSITION_DELETE_FORBIDDEN';
  end if;
  if tg_op = 'INSERT' then
    if new.origin in ('CLIENT_REQUESTED', 'CLIENT_SHARED') then
      raise exception 'CANONICAL_POSITION_CLIENT_ORIGIN_REQUIRES_INTENT';
    end if;
    return new;
  end if;
  if row(new.position_id, new.company_key, new.title_key, new.version)
    is distinct from row(old.position_id, old.company_key, old.title_key, old.version) then
    raise exception 'CANONICAL_POSITION_IDENTITY_IMMUTABLE';
  end if;
  if new.origin is distinct from old.origin then
    if old.origin not in ('SCRAPED_STAGING', 'INTERNAL_CREATED')
      or new.origin not in ('CLIENT_REQUESTED', 'CLIENT_SHARED')
      or not exists (
        select 1
        from customer_intents as intent
        join source_snapshots as source on source.snapshot_id = intent.snapshot_id
        where intent.position_id = old.position_id
          and source.status = 'PASS'
          and (
            (new.origin = 'CLIENT_REQUESTED' and intent.intent_type = 'REQUESTED')
            or (new.origin = 'CLIENT_SHARED' and intent.intent_type = 'POSITION_SHARED')
          )
      ) then
      raise exception 'CANONICAL_POSITION_ORIGIN_PROMOTION_INVALID';
    end if;
  end if;
  return new;
end
$$;

create trigger canonical_position_transition_guard
before insert or update or delete on canonical_positions
for each row execute function weekly_canonical_position_transition_is_valid();

create trigger canonical_positions_no_truncate
before truncate on canonical_positions
for each statement execute function weekly_reject_truncate();

create table position_source_links (
  position_id text not null references canonical_positions(position_id),
  snapshot_id text not null references source_snapshots(snapshot_id),
  link_type text not null,
  confidence_basis text not null,
  is_active boolean not null,
  primary key (position_id, snapshot_id, link_type)
);

create function weekly_position_source_link_transition_is_valid()
returns trigger
language plpgsql
as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'POSITION_SOURCE_LINK_DELETE_FORBIDDEN';
  end if;
  if row(new.position_id, new.snapshot_id, new.link_type, new.confidence_basis)
    is distinct from row(old.position_id, old.snapshot_id, old.link_type, old.confidence_basis)
    or old.is_active = false or new.is_active <> false then
    raise exception 'POSITION_SOURCE_LINK_TRANSITION_INVALID';
  end if;
  return new;
end
$$;

create trigger position_source_link_transition_guard
before update or delete on position_source_links
for each row execute function weekly_position_source_link_transition_is_valid();

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
  evidence_ref text not null check (btrim(evidence_ref) <> ''),
  observed_at timestamptz not null,
  classifier_version text not null,
  unique (position_id, snapshot_id, intent_type)
);

create function weekly_customer_intent_is_valid()
returns trigger
language plpgsql
as $$
declare
  current_origin text;
begin
  select origin into strict current_origin from canonical_positions where position_id = new.position_id;
  if not exists (
    select 1 from source_snapshots as source
    where source.snapshot_id = new.snapshot_id and source.status = 'PASS'
      and source.evidence_refs ? new.evidence_ref
  ) then
    raise exception 'CUSTOMER_INTENT_SOURCE_NOT_PASS';
  end if;
  if new.intent_type in ('REQUIREMENT_CHANGED', 'PIPELINE_FEEDBACK')
    and current_origin not in ('CLIENT_REQUESTED', 'CLIENT_SHARED') then
    raise exception 'CUSTOMER_INTENT_EXISTING_CLIENT_POSITION_REQUIRED';
  end if;
  return new;
end
$$;

create trigger customer_intent_insert_guard
before insert on customer_intents
for each row execute function weekly_customer_intent_is_valid();

create trigger customer_intents_immutable
before update or delete on customer_intents
for each row execute function weekly_reject_mutation();

create table canonical_position_state_events (
  position_state_event_id text primary key,
  position_id text not null references canonical_positions(position_id),
  source_snapshot_id text not null references source_snapshots(snapshot_id),
  origin text not null check (
    origin in ('SCRAPED_STAGING', 'CLIENT_REQUESTED', 'CLIENT_SHARED', 'INTERNAL_CREATED')
  ),
  lifecycle_stage text not null check (
    lifecycle_stage in ('ACTIVE', 'PIPELINE', 'CLOSING', 'CLOSED')
  ),
  active boolean not null,
  event_at timestamptz not null,
  recorded_at timestamptz not null,
  evidence_ref text not null check (btrim(evidence_ref) <> ''),
  stable_event_fingerprint text not null check (btrim(stable_event_fingerprint) <> ''),
  unique (position_id, stable_event_fingerprint)
);

create function weekly_position_state_event_is_valid()
returns trigger
language plpgsql
as $$
begin
  if not exists (
    select 1 from source_snapshots as source
    where source.snapshot_id = new.source_snapshot_id and source.status = 'PASS'
      and source.evidence_refs ? new.evidence_ref
  ) then
    raise exception 'POSITION_STATE_EVENT_SOURCE_NOT_PASS';
  end if;
  if new.origin in ('CLIENT_REQUESTED', 'CLIENT_SHARED') and not exists (
    select 1
    from customer_intents as intent
    join source_snapshots as source on source.snapshot_id = intent.snapshot_id
    where intent.position_id = new.position_id
      and intent.observed_at <= new.event_at and source.status = 'PASS'
      and (
        (new.origin = 'CLIENT_REQUESTED' and intent.intent_type = 'REQUESTED')
        or (new.origin = 'CLIENT_SHARED' and intent.intent_type = 'POSITION_SHARED')
      )
  ) then
    raise exception 'POSITION_STATE_EVENT_CLIENT_INTENT_MISSING';
  end if;
  return new;
end
$$;

create trigger canonical_position_state_event_insert_guard
before insert on canonical_position_state_events
for each row execute function weekly_position_state_event_is_valid();

create trigger canonical_position_state_events_immutable
before update or delete on canonical_position_state_events
for each row execute function weekly_reject_mutation();

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

create trigger career_page_observations_immutable
before update or delete on career_page_observations
for each row execute function weekly_reject_mutation();

create table dedupe_decisions (
  decision_id text primary key,
  run_id text not null references weekly_runs(run_id),
  duplicate_snapshot_id text not null references source_snapshots(snapshot_id),
  canonical_position_id text not null references canonical_positions(position_id),
  rule_version text not null,
  reason_code text not null check (btrim(reason_code) <> ''),
  decided_by text not null,
  decided_at timestamptz not null,
  foreign key (run_id, duplicate_snapshot_id)
    references source_snapshots(run_id, snapshot_id),
  unique (run_id, duplicate_snapshot_id)
);

create trigger dedupe_decisions_immutable
before update or delete on dedupe_decisions
for each row execute function weekly_reject_mutation();

create table zero_result_assertions (
  run_id text not null references weekly_runs(run_id),
  collection_name text not null check (
    collection_name in ('position_state', 'outreach_events', 'pipeline_events', 'pipeline_state')
  ),
  dimension_key text not null check (
    (collection_name in ('position_state', 'pipeline_events', 'pipeline_state') and dimension_key = 'all')
    or (collection_name = 'outreach_events' and dimension_key in ('saramin', 'jobkorea', 'linkedin_rps'))
  ),
  week_index smallint not null check (week_index between 0 and 3),
  window_start timestamptz not null,
  window_end_exclusive timestamptz not null,
  source_snapshot_id text not null references source_snapshots(snapshot_id),
  provider_receipt_ref text not null check (btrim(provider_receipt_ref) <> ''),
  observed_count integer not null check (observed_count = 0),
  rule_version text not null,
  foreign key (run_id, source_snapshot_id)
    references source_snapshots(run_id, snapshot_id),
  check (window_end_exclusive = window_start + interval '7 days'),
  primary key (run_id, collection_name, dimension_key, week_index, source_snapshot_id)
);

create function weekly_zero_result_assertion_is_valid()
returns trigger
language plpgsql
as $$
begin
  if not exists (
    select 1
    from source_snapshots as source
    join weekly_runs as run on run.run_id = source.run_id
    where source.run_id = new.run_id and source.snapshot_id = new.source_snapshot_id
      and source.status = 'PASS'
      and source.evidence_refs ? new.provider_receipt_ref
      and source.fetched_at <= run.meeting_at
      and new.window_end_exclusive = run.window_end_exclusive
        - make_interval(days => 7 * new.week_index)
      and new.window_start = new.window_end_exclusive - interval '7 days'
  ) then
    raise exception 'ZERO_RESULT_WINDOW_OR_SOURCE_INVALID';
  end if;
  return new;
end
$$;

create trigger zero_result_assertion_insert_guard
before insert on zero_result_assertions
for each row execute function weekly_zero_result_assertion_is_valid();

create trigger zero_result_assertions_immutable
before update or delete on zero_result_assertions
for each row execute function weekly_reject_mutation();

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

create trigger priority_scores_immutable
before update or delete on priority_scores
for each row execute function weekly_reject_mutation();

create table consultants (
  consultant_id text primary key,
  consultant_display text not null,
  roster_version text not null,
  active boolean not null default true
);

create trigger consultants_immutable
before update or delete on consultants
for each row execute function weekly_reject_mutation();

create table consultant_provider_accounts (
  consultant_id text not null references consultants(consultant_id),
  channel text not null check (channel in ('saramin', 'jobkorea', 'linkedin_rps')),
  provider_actor_ref text not null,
  primary key (channel, provider_actor_ref),
  unique (consultant_id, channel, provider_actor_ref)
);

create trigger consultant_provider_accounts_immutable
before update or delete on consultant_provider_accounts
for each row execute function weekly_reject_mutation();

create table outreach_channel_coverage (
  run_id text not null references weekly_runs(run_id),
  source_snapshot_id text not null references source_snapshots(snapshot_id),
  consultant_id text not null,
  channel text not null,
  provider_actor_ref text not null,
  access_state text not null check (
    access_state in (
      'AUTHENTICATED', 'AUTH_REQUIRED', 'TUTORIAL_OR_DEMO', 'AUTOMATION_DENIED',
      'CHALLENGE', 'MISSING_PROFILE', 'STALE_PAGE'
    )
  ),
  coverage_status text not null check (coverage_status in ('COVERED', 'NOT_RUN')),
  blocker_reason text,
  check (coverage_status <> 'COVERED' or access_state = 'AUTHENTICATED'),
  foreign key (run_id, source_snapshot_id)
    references source_snapshots(run_id, snapshot_id),
  foreign key (consultant_id, channel, provider_actor_ref)
    references consultant_provider_accounts(consultant_id, channel, provider_actor_ref),
  primary key (run_id, channel, provider_actor_ref)
);

create trigger outreach_channel_coverage_immutable
before update or delete on outreach_channel_coverage
for each row execute function weekly_reject_mutation();

create table proposal_send_attempts (
  send_attempt_id text primary key,
  run_id text not null references weekly_runs(run_id),
  source_snapshot_id text not null references source_snapshots(snapshot_id),
  consultant_id text not null,
  channel text not null check (channel in ('saramin', 'jobkorea', 'linkedin_rps')),
  provider_actor_ref text not null,
  candidate_key_hmac text not null,
  position_id text not null references canonical_positions(position_id),
  status text not null check (status in ('PENDING', 'SENT', 'FAILED')),
  provider_request_key text not null,
  provider_message_id_ciphertext text,
  provider_receipt_ref text check (
    provider_receipt_ref is null or btrim(provider_receipt_ref) <> ''
  ),
  requested_at timestamptz not null,
  sent_at timestamptz,
  finalized_at timestamptz,
  evidence_uri text not null check (btrim(evidence_uri) <> ''),
  foreign key (run_id, source_snapshot_id)
    references source_snapshots(run_id, snapshot_id),
  foreign key (consultant_id, channel, provider_actor_ref)
    references consultant_provider_accounts(consultant_id, channel, provider_actor_ref),
  check (
    (
      status = 'PENDING' and sent_at is null and finalized_at is null
      and provider_receipt_ref is null
    )
    or (
      status = 'SENT' and sent_at is not null and finalized_at is not null
      and provider_receipt_ref is not null
    )
    or (
      status = 'FAILED' and finalized_at is not null
      and sent_at is null and provider_receipt_ref is null
    )
  ),
  unique (channel, candidate_key_hmac, position_id, provider_request_key)
);

create unique index proposal_send_receipt_once
  on proposal_send_attempts(channel, provider_receipt_ref)
  where provider_receipt_ref is not null;

create function weekly_proposal_send_insert_is_valid()
returns trigger
language plpgsql
as $$
begin
  if new.status <> 'PENDING' or not exists (
    select 1 from source_snapshots
    where run_id = new.run_id and snapshot_id = new.source_snapshot_id and status = 'PASS'
  ) then
    raise exception 'PROPOSAL_SEND_ATTEMPT_WRITE_AHEAD_INVALID';
  end if;
  return new;
end
$$;

create trigger proposal_send_attempt_insert_guard
before insert on proposal_send_attempts
for each row execute function weekly_proposal_send_insert_is_valid();

create function weekly_proposal_send_transition_is_valid()
returns trigger
language plpgsql
as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'PROPOSAL_SEND_ATTEMPT_DELETE_FORBIDDEN';
  end if;
  if row(
    new.send_attempt_id, new.run_id, new.source_snapshot_id, new.consultant_id,
    new.channel, new.provider_actor_ref, new.candidate_key_hmac, new.position_id,
    new.provider_request_key, new.requested_at, new.evidence_uri
  ) is distinct from row(
    old.send_attempt_id, old.run_id, old.source_snapshot_id, old.consultant_id,
    old.channel, old.provider_actor_ref, old.candidate_key_hmac, old.position_id,
    old.provider_request_key, old.requested_at, old.evidence_uri
  ) then
    raise exception 'PROPOSAL_SEND_ATTEMPT_IDENTITY_IMMUTABLE';
  end if;
  if old.status in ('SENT', 'FAILED') then
    raise exception 'PROPOSAL_SEND_ATTEMPT_FINAL_IMMUTABLE';
  end if;
  if old.status <> 'PENDING' or new.status not in ('PENDING', 'SENT', 'FAILED') then
    raise exception 'PROPOSAL_SEND_ATTEMPT_TRANSITION_INVALID';
  end if;
  if new.status = 'SENT' and not exists (
    select 1
    from source_snapshots as source
    join weekly_runs as run on run.run_id = new.run_id
    where source.run_id = new.run_id
      and source.snapshot_id = new.source_snapshot_id
      and source.status = 'PASS'
      and source.evidence_refs ? new.provider_receipt_ref
      and new.sent_at >= run.window_start
      and new.sent_at < run.window_end_exclusive
  ) then
    raise exception 'PROPOSAL_SEND_ATTEMPT_SENT_EVIDENCE_INVALID';
  end if;
  return new;
end
$$;

create trigger proposal_send_attempts_transition_guard
before update or delete on proposal_send_attempts
for each row execute function weekly_proposal_send_transition_is_valid();

create function weekly_channel_mix_is_valid(channel_mix jsonb, expected_total integer)
returns boolean
language sql
immutable
as $$
  select case
    when jsonb_typeof(channel_mix) <> 'object' or expected_total <= 0 then false
    else not exists (
      select 1
      from jsonb_each(channel_mix) as entry(channel, value)
      where channel not in ('saramin', 'jobkorea', 'linkedin_rps')
        or jsonb_typeof(value) <> 'number'
        or (value #>> '{}') !~ '^[0-9]+$'
    ) and coalesce((
      select sum(case when jsonb_typeof(value) = 'number' and (value #>> '{}') ~ '^[0-9]+$'
        then (value #>> '{}')::integer else 0 end)
      from jsonb_each(channel_mix)
    ), 0) = expected_total
  end
$$;

create table consultant_position_focus (
  run_id text not null references weekly_runs(run_id),
  consultant_id text not null references consultants(consultant_id),
  position_id text not null references canonical_positions(position_id),
  verified_sent_count integer not null check (verified_sent_count > 0),
  unique_candidate_count integer not null check (unique_candidate_count > 0),
  active_days integer not null check (active_days > 0),
  focus_share numeric not null check (focus_share > 0 and focus_share <= 1),
  channel_mix jsonb not null check (weekly_channel_mix_is_valid(channel_mix, verified_sent_count)),
  formula_version text not null,
  grass_evidence text not null check (grass_evidence = 'YELLOW_ELIGIBLE'),
  input_hash text not null,
  primary key (run_id, consultant_id, position_id, formula_version)
);

create function weekly_consultant_position_focus_is_valid()
returns trigger
language plpgsql
as $$
declare
  actual_sent integer;
  actual_unique integer;
  actual_days integer;
  consultant_total integer;
  actual_mix jsonb;
begin
  select count(*), count(distinct send.candidate_key_hmac),
    count(distinct (send.sent_at at time zone 'Asia/Seoul')::date)
    into actual_sent, actual_unique, actual_days
  from proposal_send_attempts as send
  join weekly_runs as target_run on target_run.run_id = new.run_id
  join source_snapshots as source
    on source.run_id = send.run_id and source.snapshot_id = send.source_snapshot_id
  where send.consultant_id = new.consultant_id
    and send.position_id = new.position_id and send.status = 'SENT' and source.status = 'PASS'
    and source.fetched_at <= target_run.meeting_at
    and send.sent_at >= target_run.window_start and send.sent_at < target_run.window_end_exclusive;

  select count(*) into consultant_total
  from proposal_send_attempts as send
  join weekly_runs as target_run on target_run.run_id = new.run_id
  join source_snapshots as source
    on source.run_id = send.run_id and source.snapshot_id = send.source_snapshot_id
  where send.consultant_id = new.consultant_id
    and send.status = 'SENT' and source.status = 'PASS'
    and source.fetched_at <= target_run.meeting_at
    and send.sent_at >= target_run.window_start and send.sent_at < target_run.window_end_exclusive;

  select coalesce(jsonb_object_agg(channel, sent_count order by channel), '{}'::jsonb)
    into actual_mix
  from (
    select send.channel, count(*)::integer as sent_count
    from proposal_send_attempts as send
    join weekly_runs as target_run on target_run.run_id = new.run_id
    join source_snapshots as source
      on source.run_id = send.run_id and source.snapshot_id = send.source_snapshot_id
    where send.consultant_id = new.consultant_id
      and send.position_id = new.position_id and send.status = 'SENT' and source.status = 'PASS'
      and source.fetched_at <= target_run.meeting_at
      and send.sent_at >= target_run.window_start and send.sent_at < target_run.window_end_exclusive
    group by send.channel
  ) as channel_counts;

  if actual_sent = 0 or consultant_total = 0
    or new.verified_sent_count <> actual_sent
    or new.unique_candidate_count <> actual_unique
    or new.active_days <> actual_days
    or new.channel_mix is distinct from actual_mix
    or new.focus_share <> actual_sent::numeric / consultant_total::numeric
    or new.formula_version <> 'consultant-focus-v2' then
    raise exception 'CONSULTANT_POSITION_FOCUS_DERIVATION_INVALID';
  end if;
  return new;
end
$$;

create trigger consultant_position_focus_insert_guard
before insert on consultant_position_focus
for each row execute function weekly_consultant_position_focus_is_valid();

create trigger consultant_position_focus_immutable
before update or delete on consultant_position_focus
for each row execute function weekly_reject_mutation();

create table candidate_position_tasks (
  candidate_task_id text primary key,
  candidate_key_hmac text not null,
  position_id text not null references canonical_positions(position_id),
  hiring_cycle_id text not null,
  source_snapshot_id text not null references source_snapshots(snapshot_id),
  external_task_id text not null,
  first_created_at timestamptz not null,
  unique (candidate_key_hmac, position_id, hiring_cycle_id)
);

create function weekly_candidate_task_source_is_valid()
returns trigger
language plpgsql
as $$
begin
  if not exists (
    select 1 from source_snapshots
    where snapshot_id = new.source_snapshot_id and status = 'PASS'
  ) then
    raise exception 'CANDIDATE_TASK_SOURCE_NOT_PASS';
  end if;
  return new;
end
$$;

create trigger candidate_position_task_insert_guard
before insert on candidate_position_tasks
for each row execute function weekly_candidate_task_source_is_valid();

create trigger candidate_position_tasks_immutable
before update or delete on candidate_position_tasks
for each row execute function weekly_reject_mutation();

create table candidate_pipeline_events (
  pipeline_event_id text primary key,
  candidate_task_id text not null references candidate_position_tasks(candidate_task_id),
  source_snapshot_id text not null references source_snapshots(snapshot_id),
  event_type text not null check (
    event_type in ('CREATED', 'REACTIVATED', 'STAGE_CHANGED', 'CLOSED')
  ),
  from_stage text check (
    from_stage is null or from_stage in (
      'RECOMMENDATION_PENDING', 'CLIENT_REVIEW', 'ASSIGNMENT', 'INTERVIEW_1',
      'INTERVIEW_2', 'FINAL_INTERVIEW', 'OFFER', 'FINAL_ACCEPTED', 'JOINED',
      'REJECTED', 'WITHDRAWN', 'CLOSED'
    )
  ),
  to_stage text not null check (
    to_stage in (
      'RECOMMENDATION_PENDING', 'CLIENT_REVIEW', 'ASSIGNMENT', 'INTERVIEW_1',
      'INTERVIEW_2', 'FINAL_INTERVIEW', 'OFFER', 'FINAL_ACCEPTED', 'JOINED',
      'REJECTED', 'WITHDRAWN', 'CLOSED'
    )
  ),
  event_at timestamptz not null,
  recorded_at timestamptz not null,
  evidence_ref text not null check (btrim(evidence_ref) <> ''),
  stable_event_fingerprint text not null,
  unique (candidate_task_id, stable_event_fingerprint)
);

create function weekly_pipeline_event_is_valid()
returns trigger
language plpgsql
as $$
declare
  task_source_snapshot_id text;
  task_first_created_at timestamptz;
  previous_stage text;
  next_from_stage text;
  next_to_stage text;
  next_event_type text;
  previous_exists boolean;
  next_exists boolean;
begin
  if not exists (
    select 1 from source_snapshots as source
    where source.snapshot_id = new.source_snapshot_id and source.status = 'PASS'
      and source.evidence_refs ? new.evidence_ref
  ) then
    raise exception 'PIPELINE_EVENT_SOURCE_NOT_PASS';
  end if;
  select source_snapshot_id, first_created_at
    into strict task_source_snapshot_id, task_first_created_at
  from candidate_position_tasks
  where candidate_task_id = new.candidate_task_id
  for update;

  select event.to_stage
    into previous_stage
  from candidate_pipeline_events as event
  where event.candidate_task_id = new.candidate_task_id
    and (event.event_at, event.recorded_at, event.pipeline_event_id)
      < (new.event_at, new.recorded_at, new.pipeline_event_id)
  order by event.event_at desc, event.recorded_at desc, event.pipeline_event_id desc
  limit 1;
  previous_exists := found;

  select event.from_stage, event.to_stage, event.event_type
    into next_from_stage, next_to_stage, next_event_type
  from candidate_pipeline_events as event
  where event.candidate_task_id = new.candidate_task_id
    and (event.event_at, event.recorded_at, event.pipeline_event_id)
      > (new.event_at, new.recorded_at, new.pipeline_event_id)
  order by event.event_at, event.recorded_at, event.pipeline_event_id
  limit 1;
  next_exists := found;

  if not previous_exists then
    if new.event_type <> 'CREATED' or new.from_stage is not null
      or new.to_stage in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED')
      or new.source_snapshot_id <> task_source_snapshot_id
      or new.event_at <> task_first_created_at then
      raise exception 'PIPELINE_INITIAL_EVENT_INVALID';
    end if;
  else
    if new.from_stage is distinct from previous_stage then
      raise exception 'PIPELINE_FROM_STAGE_MISMATCH';
    end if;
    if previous_stage in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED') then
      if new.event_type <> 'REACTIVATED'
        or new.to_stage in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED') then
        raise exception 'PIPELINE_REACTIVATION_INVALID';
      end if;
    elsif not (
      (new.event_type = 'STAGE_CHANGED'
        and new.to_stage is distinct from previous_stage
        and new.to_stage not in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED'))
      or (new.event_type = 'CLOSED'
        and new.to_stage in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED'))
    ) then
      raise exception 'PIPELINE_TRANSITION_INVALID';
    end if;
  end if;

  if next_exists then
    if next_from_stage is distinct from new.to_stage then
      raise exception 'PIPELINE_NEXT_FROM_STAGE_MISMATCH';
    end if;
    if new.to_stage in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED') then
      if next_event_type <> 'REACTIVATED'
        or next_to_stage in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED') then
        raise exception 'PIPELINE_NEXT_REACTIVATION_INVALID';
      end if;
    elsif not (
      (next_event_type = 'STAGE_CHANGED'
        and next_to_stage is distinct from new.to_stage
        and next_to_stage not in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED'))
      or (next_event_type = 'CLOSED'
        and next_to_stage in ('JOINED', 'REJECTED', 'WITHDRAWN', 'CLOSED'))
    ) then
      raise exception 'PIPELINE_NEXT_TRANSITION_INVALID';
    end if;
  end if;
  return new;
end
$$;

create trigger candidate_pipeline_event_transition_guard
before insert on candidate_pipeline_events
for each row execute function weekly_pipeline_event_is_valid();

create trigger candidate_pipeline_events_immutable
before update or delete on candidate_pipeline_events
for each row execute function weekly_reject_mutation();

create view candidate_task_current_state as
select
  candidate_task_id,
  to_stage as current_stage,
  event_at as current_stage_at,
  pipeline_event_id,
  source_snapshot_id
from (
  select
    event.*,
    row_number() over (
      partition by candidate_task_id
      order by event_at desc, recorded_at desc, pipeline_event_id desc
    ) as current_rank
  from candidate_pipeline_events as event
) as ranked
where current_rank = 1;

create function weekly_zero_collection_for_metric(target_metric_name text)
returns text
language sql
immutable
as $$
  select case
    when target_metric_name = 'live_client_position_count' then 'position_state'
    when target_metric_name = 'channel_outreach' then 'outreach_events'
    when target_metric_name in ('new_task_count', 'reactivated_task_count') then 'pipeline_events'
    when target_metric_name in (
      'active_pipeline_count', 'interview_pipeline_count', 'pre_interview_pipeline_count'
    ) then 'pipeline_state'
    else null
  end
$$;

create function weekly_metric_expected_value(
  target_run_id text,
  target_metric_name text,
  target_dimension_key text,
  target_week_index integer
) returns integer
language plpgsql
stable
as $$
declare
  target_start timestamptz;
  target_end timestamptz;
  target_meeting timestamptz;
  expected_value integer;
begin
  select run.window_end_exclusive - make_interval(days => 7 * (target_week_index + 1)),
    run.window_end_exclusive - make_interval(days => 7 * target_week_index), run.meeting_at
    into strict target_start, target_end, target_meeting
  from weekly_runs as run where run.run_id = target_run_id;

  if target_metric_name = 'live_client_position_count' then
    select count(*)::integer into expected_value
    from (
      select distinct on (event.position_id)
        event.origin, event.lifecycle_stage, event.active
      from canonical_position_state_events as event
      join source_snapshots as source on source.snapshot_id = event.source_snapshot_id
      where event.event_at < target_end and event.recorded_at <= target_meeting
        and source.status = 'PASS' and source.fetched_at <= target_meeting
      order by event.position_id, event.event_at desc,
        event.recorded_at desc, event.position_state_event_id desc
    ) as current_state
    where current_state.origin in ('CLIENT_REQUESTED', 'CLIENT_SHARED')
      and current_state.active and current_state.lifecycle_stage <> 'CLOSED';
  elsif target_metric_name = 'new_task_count' then
    select count(distinct event.candidate_task_id)::integer into expected_value
    from candidate_pipeline_events as event
    join candidate_position_tasks as task on task.candidate_task_id = event.candidate_task_id
    join source_snapshots as source on source.snapshot_id = event.source_snapshot_id
    where event.event_type = 'CREATED'
      and event.event_at = task.first_created_at
      and event.source_snapshot_id = task.source_snapshot_id
      and event.event_at >= target_start and event.event_at < target_end
      and event.recorded_at <= target_meeting
      and source.status = 'PASS' and source.fetched_at <= target_meeting;
  elsif target_metric_name = 'reactivated_task_count' then
    select count(distinct event.candidate_task_id)::integer into expected_value
    from candidate_pipeline_events as event
    join source_snapshots as source on source.snapshot_id = event.source_snapshot_id
    where event.event_type = 'REACTIVATED'
      and event.event_at >= target_start and event.event_at < target_end
      and event.recorded_at <= target_meeting
      and source.status = 'PASS' and source.fetched_at <= target_meeting;
  elsif target_metric_name in (
    'active_pipeline_count', 'interview_pipeline_count', 'pre_interview_pipeline_count'
  ) then
    select count(*)::integer into expected_value
    from (
      select distinct on (event.candidate_task_id) event.to_stage
      from candidate_pipeline_events as event
      join source_snapshots as source on source.snapshot_id = event.source_snapshot_id
      where event.event_at < target_end and event.recorded_at <= target_meeting
        and source.status = 'PASS' and source.fetched_at <= target_meeting
      order by event.candidate_task_id, event.event_at desc,
        event.recorded_at desc, event.pipeline_event_id desc
    ) as current_state
    where (target_metric_name = 'active_pipeline_count' and current_state.to_stage in (
        'RECOMMENDATION_PENDING', 'CLIENT_REVIEW', 'ASSIGNMENT', 'INTERVIEW_1',
        'INTERVIEW_2', 'FINAL_INTERVIEW', 'OFFER', 'FINAL_ACCEPTED'
      )) or (target_metric_name = 'interview_pipeline_count' and current_state.to_stage in (
        'ASSIGNMENT', 'INTERVIEW_1', 'INTERVIEW_2', 'FINAL_INTERVIEW', 'OFFER', 'FINAL_ACCEPTED'
      )) or (target_metric_name = 'pre_interview_pipeline_count' and current_state.to_stage in (
        'RECOMMENDATION_PENDING', 'CLIENT_REVIEW'
      ));
  elsif target_metric_name = 'channel_outreach' then
    select count(*)::integer into expected_value
    from proposal_send_attempts as send
    join source_snapshots as source
      on source.run_id = send.run_id and source.snapshot_id = send.source_snapshot_id
    where send.status = 'SENT' and send.channel = target_dimension_key
      and send.sent_at >= target_start and send.sent_at < target_end
      and source.status = 'PASS' and source.fetched_at <= target_meeting;
  else
    raise exception 'WEEKLY_METRIC_NAME_INVALID';
  end if;
  return expected_value;
end
$$;

create table weekly_metric_snapshots (
  metric_snapshot_id text primary key,
  run_id text not null references weekly_runs(run_id),
  metric_name text not null check (
    metric_name in (
      'live_client_position_count', 'new_task_count', 'reactivated_task_count',
      'active_pipeline_count', 'interview_pipeline_count', 'pre_interview_pipeline_count',
      'channel_outreach'
    )
  ),
  dimension_key text not null check (btrim(dimension_key) <> ''),
  week_index smallint not null check (week_index between 0 and 3),
  week_label text not null check (btrim(week_label) <> ''),
  metric_iso_week text not null check (btrim(metric_iso_week) <> ''),
  metric_window_start timestamptz not null,
  metric_window_end_exclusive timestamptz not null,
  value integer check (value is null or value >= 0),
  status text not null check (status in ('VERIFIED', 'PARTIAL', 'NOT_RUN')),
  as_of timestamptz not null,
  source_snapshot_id text references source_snapshots(snapshot_id),
  evidence_refs jsonb not null,
  input_hash text not null,
  contract_version text not null,
  foreign key (run_id, source_snapshot_id)
    references source_snapshots(run_id, snapshot_id),
  check (status <> 'VERIFIED' or (value is not null and source_snapshot_id is not null)),
  check (status = 'VERIFIED' or value is null),
  check (metric_window_end_exclusive = metric_window_start + interval '7 days'),
  check (weekly_evidence_refs_are_valid(evidence_refs)),
  unique (run_id, metric_name, dimension_key, week_index, contract_version)
);

create function weekly_metric_snapshot_zero_is_verified()
returns trigger
language plpgsql
as $$
declare
  run_meeting_at timestamptz;
  run_window_end timestamptz;
  expected_start timestamptz;
  expected_end timestamptz;
  expected_label text;
  expected_metric_iso_week text;
  source_status text;
  source_fetched_at timestamptz;
begin
  select run.meeting_at, run.window_end_exclusive, source.status, source.fetched_at
    into strict run_meeting_at, run_window_end, source_status, source_fetched_at
  from weekly_runs as run
  left join source_snapshots as source
    on source.run_id = run.run_id and source.snapshot_id = new.source_snapshot_id
  where run.run_id = new.run_id;
  expected_end := run_window_end - make_interval(days => 7 * new.week_index);
  expected_start := expected_end - interval '7 days';
  expected_label := 'FY' || to_char(
    (run_meeting_at at time zone 'Asia/Seoul') - make_interval(days => 7 * new.week_index),
    'IY"W"IW'
  );
  expected_metric_iso_week := 'FY' || to_char(
    expected_start at time zone 'Asia/Seoul', 'IY"W"IW'
  );
  if new.metric_window_start is distinct from expected_start
    or new.metric_window_end_exclusive is distinct from expected_end
    or new.week_label is distinct from expected_label
    or new.metric_iso_week is distinct from expected_metric_iso_week
    or new.as_of < new.metric_window_end_exclusive
    or new.as_of > run_meeting_at then
    raise exception 'WEEKLY_METRIC_WINDOW_INVALID';
  end if;
  if (new.metric_name = 'channel_outreach'
      and new.dimension_key not in ('saramin', 'jobkorea', 'linkedin_rps'))
    or (new.metric_name <> 'channel_outreach' and new.dimension_key <> 'all') then
    raise exception 'WEEKLY_METRIC_DIMENSION_INVALID';
  end if;
  if new.status = 'VERIFIED' and (
    source_status is distinct from 'PASS' or source_fetched_at > run_meeting_at
  ) then
    raise exception 'WEEKLY_METRIC_SOURCE_NOT_PASS';
  end if;
  if new.status = 'VERIFIED' and new.value is distinct from weekly_metric_expected_value(
    new.run_id, new.metric_name, new.dimension_key, new.week_index
  ) then
    raise exception 'WEEKLY_METRIC_DERIVATION_INVALID';
  end if;
  if new.status = 'VERIFIED' and new.value = 0 and not exists (
    select 1
    from zero_result_assertions as assertion
    where assertion.run_id = new.run_id
      and assertion.collection_name = weekly_zero_collection_for_metric(new.metric_name)
      and assertion.dimension_key = new.dimension_key
      and assertion.week_index = new.week_index
      and assertion.window_start = new.metric_window_start
      and assertion.window_end_exclusive = new.metric_window_end_exclusive
      and assertion.source_snapshot_id = new.source_snapshot_id
      and assertion.rule_version = 'weekly-zero-result-v1'
      and new.evidence_refs ? assertion.provider_receipt_ref
  ) then
    raise exception 'WEEKLY_METRIC_ZERO_RECEIPT_MISSING';
  end if;
  return new;
end
$$;

create trigger weekly_metric_snapshot_zero_guard
before insert on weekly_metric_snapshots
for each row execute function weekly_metric_snapshot_zero_is_verified();

create trigger weekly_metric_snapshots_immutable
before update or delete on weekly_metric_snapshots
for each row execute function weekly_reject_mutation();

create function weekly_market_sample_is_valid(
  sample_evaluations jsonb,
  must_have_predicates jsonb
) returns boolean
language sql
immutable
as $$
  select case
    when jsonb_typeof(sample_evaluations) is distinct from 'array'
      or jsonb_typeof(must_have_predicates) is distinct from 'array'
      or jsonb_array_length(sample_evaluations) <> 20
      or jsonb_array_length(must_have_predicates) = 0
    then false
    else
      (
        select count(*) = count(distinct predicate #>> '{}')
          and bool_and((
            jsonb_typeof(predicate) = 'string'
            and btrim(predicate #>> '{}') <> ''
          ) is true)
        from jsonb_array_elements(must_have_predicates) as predicates(predicate)
      )
      and (
        select count(*) = 20
          and count(distinct evaluation->>'candidate_key_hmac') = 20
          and bool_and((
            case
              when jsonb_typeof(evaluation) <> 'object'
                or jsonb_typeof(evaluation->'predicate_results') <> 'object'
              then false
              else
                jsonb_typeof(evaluation->'candidate_key_hmac') = 'string'
                and btrim(evaluation->>'candidate_key_hmac') <> ''
                and length(evaluation->>'candidate_key_hmac') >= 32
                and jsonb_typeof(evaluation->'rank') = 'number'
                and case
                  when coalesce(evaluation->>'rank', '') ~ '^(?:[1-9]|1[0-9]|20)$'
                  then (evaluation->>'rank')::integer = ordinal::integer
                  else false
                end
                and (
                  select array_agg(key order by key)
                  from jsonb_object_keys(evaluation) as evaluation_keys(key)
                ) is not distinct from
                  array['candidate_key_hmac', 'predicate_results', 'rank']::text[]
                and (
                  select array_agg(key order by key)
                  from jsonb_object_keys(evaluation->'predicate_results') as result_keys(key)
                ) is not distinct from (
                  select array_agg(predicate #>> '{}' order by predicate #>> '{}')
                  from jsonb_array_elements(must_have_predicates) as predicates(predicate)
                )
                and not exists (
                  select 1
                  from jsonb_each_text(evaluation->'predicate_results') as results(key, value)
                  where value is null or value not in ('TRUE', 'FALSE', 'UNKNOWN')
                )
            end
          ) is true)
        from jsonb_array_elements(sample_evaluations)
          with ordinality as sample(evaluation, ordinal)
      )
  end
$$;

create function weekly_market_qualified_count(
  sample_evaluations jsonb,
  must_have_predicates jsonb
) returns integer
language sql
immutable
as $$
  select case
    when weekly_market_sample_is_valid(sample_evaluations, must_have_predicates) is not true then null
    else (
      select count(*)::integer
      from jsonb_array_elements(sample_evaluations) as sample(evaluation)
      where (
        select count(*)
        from jsonb_array_elements_text(must_have_predicates) as required(predicate_key)
        where evaluation->'predicate_results'->>predicate_key = 'TRUE'
      ) = jsonb_array_length(must_have_predicates)
    )
  end
$$;

create function weekly_market_filter_set_is_valid(filter_set jsonb)
returns boolean
language sql
immutable
as $$
  select jsonb_typeof(filter_set) = 'object'
    and (
      select array_agg(key order by key)
      from jsonb_object_keys(filter_set) as keys(key)
    ) = array['geography', 'job_titles', 'languages', 'seniority_or_years', 'skills']::text[]
    and not exists (
      select 1 from jsonb_each(filter_set) as filters(key, value)
      where jsonb_typeof(value) <> 'array'
        or jsonb_array_length(value) = 0
        or exists (
          select 1 from jsonb_array_elements(value) as entries(entry)
          where jsonb_typeof(entry) <> 'string' or btrim(entry #>> '{}') = ''
        )
    )
$$;

create table linkedin_market_result_receipts (
  source_snapshot_id text primary key references source_snapshots(snapshot_id),
  run_id text not null references weekly_runs(run_id),
  protected_provider_receipt_ref text not null check (btrim(protected_provider_receipt_ref) <> ''),
  ordered_result_snapshot_hash text not null check (btrim(ordered_result_snapshot_hash) <> ''),
  result_count_lower_bound integer not null check (result_count_lower_bound >= 0),
  count_is_exact boolean not null,
  captured_at timestamptz not null,
  foreign key (run_id, source_snapshot_id)
    references source_snapshots(run_id, snapshot_id),
  unique (run_id, protected_provider_receipt_ref)
);

create function weekly_market_result_receipt_is_valid()
returns trigger
language plpgsql
as $$
begin
  if not exists (
    select 1
    from source_snapshots as source
    join weekly_runs as run on run.run_id = source.run_id
    where source.run_id = new.run_id and source.snapshot_id = new.source_snapshot_id
      and source.source_system = 'linkedin_rps' and source.status = 'PASS'
      and source.evidence_refs ? new.protected_provider_receipt_ref
      and source.raw_hash = new.ordered_result_snapshot_hash
      and new.captured_at <= run.meeting_at
  ) then
    raise exception 'MARKET_RESULT_RECEIPT_LINEAGE_INVALID';
  end if;
  return new;
end
$$;

create trigger linkedin_market_result_receipt_insert_guard
before insert on linkedin_market_result_receipts
for each row execute function weekly_market_result_receipt_is_valid();

create trigger linkedin_market_result_receipts_immutable
before update or delete on linkedin_market_result_receipts
for each row execute function weekly_reject_mutation();

create table linkedin_market_search_snapshots (
  market_search_snapshot_id text primary key,
  run_id text not null references weekly_runs(run_id),
  position_id text not null references canonical_positions(position_id),
  source_snapshot_id text not null references source_snapshots(snapshot_id),
  protected_search_url_ref text not null check (btrim(protected_search_url_ref) <> ''),
  query_text text not null check (btrim(query_text) <> ''),
  filter_set jsonb not null check (weekly_market_filter_set_is_valid(filter_set) is true),
  sort_order text not null check (btrim(sort_order) <> ''),
  ordered_result_snapshot_hash text not null check (btrim(ordered_result_snapshot_hash) <> ''),
  must_have_predicates jsonb not null check (
    jsonb_typeof(must_have_predicates) = 'array'
    and jsonb_array_length(must_have_predicates) > 0
  ),
  sample_evaluations jsonb not null check (
    jsonb_typeof(sample_evaluations) = 'array'
    and jsonb_array_length(sample_evaluations) = 20
    and weekly_market_sample_is_valid(sample_evaluations, must_have_predicates) is true
  ),
  result_count_lower_bound integer not null,
  count_is_exact boolean not null,
  evaluated_sample_size integer not null check (evaluated_sample_size = 20),
  check (result_count_lower_bound >= evaluated_sample_size),
  qualified_sample_matches integer not null check (
    qualified_sample_matches >= 0 and qualified_sample_matches <= evaluated_sample_size
    and weekly_market_qualified_count(sample_evaluations, must_have_predicates) is not null
    and qualified_sample_matches = weekly_market_qualified_count(sample_evaluations, must_have_predicates)
  ),
  pool_points integer not null check (
    pool_points = case
      when result_count_lower_bound = 0 then 0
      when result_count_lower_bound <= 9 then 10
      when result_count_lower_bound <= 24 then 20
      when result_count_lower_bound <= 49 then 30
      when result_count_lower_bound <= 99 then 40
      else 50
    end
  ),
  precision_points integer not null check (
    precision_points = case
      when qualified_sample_matches < 4 then 0
      when qualified_sample_matches < 8 then 15
      when qualified_sample_matches < 12 then 30
      when qualified_sample_matches < 16 then 40
      else 50
    end
  ),
  accessibility_score integer not null check (
    accessibility_score between 0 and 100
    and accessibility_score = (pool_points * precision_points * 100) / 2500
  ),
  accessibility_band text not null check (
    accessibility_band in ('EASY', 'MEDIUM', 'HARD')
    and (accessibility_score < 40) = (accessibility_band = 'HARD')
    and (accessibility_score between 40 and 69) = (accessibility_band = 'MEDIUM')
    and (accessibility_score >= 70) = (accessibility_band = 'EASY')
    and (qualified_sample_matches <> 0 or (accessibility_score = 0 and accessibility_band = 'HARD'))
  ),
  position_lifecycle text not null check (
    position_lifecycle in ('ACTIVE', 'PIPELINE', 'CLOSING', 'CLOSED')
  ),
  position_age_days integer,
  active_candidate_count integer,
  recency_points integer,
  pipeline_gap_points integer,
  scarcity_points integer,
  coverage_risk_score integer,
  coverage_risk_band text not null check (coverage_risk_band in ('A', 'B', 'C', 'UNRANKED')),
  coverage_risk_reason text,
  captured_at timestamptz not null,
  market_formula_version text not null check (market_formula_version = 'market-accessibility-v2'),
  coverage_risk_formula_version text not null check (
    coverage_risk_formula_version = 'sourcing-coverage-risk-v1'
  ),
  input_hash text not null check (btrim(input_hash) <> ''),
  foreign key (run_id, source_snapshot_id)
    references source_snapshots(run_id, snapshot_id),
  check (
    (
      position_lifecycle = 'ACTIVE'
      and position_age_days >= 0 and active_candidate_count >= 0
      and recency_points = case
        when position_age_days <= 2 then 40 when position_age_days <= 7 then 30
        when position_age_days <= 14 then 15 else 0 end
      and pipeline_gap_points = case
        when active_candidate_count = 0 then 30 when active_candidate_count = 1 then 20
        when active_candidate_count = 2 then 10 else 0 end
      and scarcity_points = case accessibility_band
        when 'HARD' then 30 when 'MEDIUM' then 15 else 0 end
      and coverage_risk_score = recency_points + pipeline_gap_points + scarcity_points
      and coverage_risk_score between 0 and 100
      and (coverage_risk_score >= 70) = (coverage_risk_band = 'A')
      and (coverage_risk_score between 40 and 69) = (coverage_risk_band = 'B')
      and (coverage_risk_score < 40) = (coverage_risk_band = 'C')
      and coverage_risk_reason is null
    )
    or (
      position_lifecycle <> 'ACTIVE'
      and position_age_days is null and active_candidate_count is null
      and recency_points is null and pipeline_gap_points is null and scarcity_points is null
      and coverage_risk_score is null and coverage_risk_band = 'UNRANKED'
      and coverage_risk_reason = 'INELIGIBLE_LIFECYCLE'
    )
  ),
  unique (run_id, position_id, market_formula_version, coverage_risk_formula_version)
);

create function weekly_market_snapshot_lineage_is_valid()
returns trigger
language plpgsql
as $$
declare
  canonical_origin text;
  canonical_lifecycle text;
  canonical_active boolean;
  source_status text;
  source_system_name text;
  source_raw_hash text;
  receipt_result_count integer;
  receipt_count_is_exact boolean;
  receipt_captured_at timestamptz;
  meeting_time timestamptz;
  run_window_end timestamptz;
  position_observed_at timestamptz;
  expected_position_age_days integer;
  expected_active_candidate_count integer;
begin
  select position.origin, position.lifecycle_stage, position.active
    into strict canonical_origin, canonical_lifecycle, canonical_active
  from canonical_positions as position where position.position_id = new.position_id;
  select source.status, source.source_system, source.raw_hash, run.meeting_at,
    run.window_end_exclusive, receipt.result_count_lower_bound, receipt.count_is_exact,
    receipt.captured_at
    into strict source_status, source_system_name, source_raw_hash, meeting_time, run_window_end,
      receipt_result_count, receipt_count_is_exact, receipt_captured_at
  from source_snapshots as source
  join weekly_runs as run on run.run_id = source.run_id
  join linkedin_market_result_receipts as receipt
    on receipt.run_id = source.run_id and receipt.source_snapshot_id = source.snapshot_id
  where source.run_id = new.run_id and source.snapshot_id = new.source_snapshot_id;
  select max(intent.observed_at) into position_observed_at
  from customer_intents as intent
  join source_snapshots as intent_source on intent_source.snapshot_id = intent.snapshot_id
  where intent.position_id = new.position_id
    and intent.intent_type in ('REQUESTED', 'POSITION_SHARED', 'REQUIREMENT_CHANGED')
    and intent_source.status = 'PASS'
    and intent.observed_at < run_window_end;

  expected_position_age_days :=
    (run_window_end at time zone 'Asia/Seoul')::date
    - (position_observed_at at time zone 'Asia/Seoul')::date;

  select count(*)::integer into expected_active_candidate_count
  from (
    select distinct on (task.candidate_task_id) event.to_stage
    from candidate_position_tasks as task
    join candidate_pipeline_events as event
      on event.candidate_task_id = task.candidate_task_id
    join source_snapshots as event_source
      on event_source.snapshot_id = event.source_snapshot_id
    where task.position_id = new.position_id
      and event.event_at < run_window_end
      and event.recorded_at <= meeting_time
      and event_source.status = 'PASS'
      and event_source.fetched_at <= meeting_time
    order by task.candidate_task_id, event.event_at desc,
      event.recorded_at desc, event.pipeline_event_id desc
  ) as current_at_cutoff
  where current_at_cutoff.to_stage in (
    'RECOMMENDATION_PENDING', 'CLIENT_REVIEW', 'ASSIGNMENT', 'INTERVIEW_1',
    'INTERVIEW_2', 'FINAL_INTERVIEW', 'OFFER', 'FINAL_ACCEPTED'
  );

  if canonical_origin not in ('CLIENT_REQUESTED', 'CLIENT_SHARED')
    or canonical_active is not true
    or canonical_lifecycle is distinct from new.position_lifecycle
    or source_status <> 'PASS'
    or source_system_name <> 'linkedin_rps'
    or new.ordered_result_snapshot_hash is distinct from source_raw_hash
    or new.result_count_lower_bound is distinct from receipt_result_count
    or new.count_is_exact is distinct from receipt_count_is_exact
    or new.captured_at is distinct from receipt_captured_at
    or new.captured_at > meeting_time then
    raise exception 'MARKET_SNAPSHOT_LINEAGE_INVALID';
  end if;
  if position_observed_at is null or (
    new.position_lifecycle = 'ACTIVE' and (
      new.position_age_days is distinct from expected_position_age_days
      or new.active_candidate_count is distinct from expected_active_candidate_count
    )
  ) then
    raise exception 'MARKET_COVERAGE_RISK_DERIVATION_INVALID';
  end if;
  return new;
end
$$;

create trigger linkedin_market_search_snapshot_insert_guard
before insert on linkedin_market_search_snapshots
for each row execute function weekly_market_snapshot_lineage_is_valid();

create trigger linkedin_market_search_snapshots_immutable
before update or delete on linkedin_market_search_snapshots
for each row execute function weekly_reject_mutation();

create table report_snapshots (
  report_snapshot_id text primary key,
  run_id text not null references weekly_runs(run_id),
  revision integer not null check (revision > 0),
  status text not null check (status in ('PARTIAL', 'BLOCKED', 'READY')),
  content_hash text not null,
  score_version text not null,
  template_version text not null,
  evidence_bundle_hash text not null,
  brief_markdown text not null,
  created_at timestamptz not null,
  unique (run_id, revision),
  unique (run_id, content_hash),
  unique (report_snapshot_id, content_hash)
);

create function weekly_report_snapshot_insert_is_valid()
returns trigger
language plpgsql
as $$
declare
  run_status text;
  expected_revision integer;
begin
  select status into strict run_status
  from weekly_runs
  where run_id = new.run_id
  for update;
  if run_status not in ('PARTIAL', 'BLOCKED', 'READY')
    or new.status is distinct from run_status then
    raise exception 'REPORT_SNAPSHOT_RUN_STATE_MISMATCH';
  end if;
  select coalesce(max(revision), 0) + 1 into expected_revision
  from report_snapshots
  where run_id = new.run_id;
  if new.revision <> expected_revision then
    raise exception 'REPORT_SNAPSHOT_REVISION_INVALID';
  end if;
  return new;
end
$$;

create trigger report_snapshot_insert_guard
before insert on report_snapshots
for each row execute function weekly_report_snapshot_insert_is_valid();

create trigger report_snapshots_immutable
before update or delete on report_snapshots
for each row execute function weekly_reject_mutation();

create function weekly_report_snapshot_is_current(target_report_snapshot_id text)
returns boolean
language sql
stable
as $$
  select exists (
    select 1
    from report_snapshots as report
    where report.report_snapshot_id = target_report_snapshot_id
      and report.status = 'READY'
      and report.revision = (
        select max(candidate.revision)
        from report_snapshots as candidate
        where candidate.run_id = report.run_id
      )
  )
$$;

create function weekly_report_snapshot_is_publishable(target_report_snapshot_id text)
returns boolean
language sql
stable
as $$
  select weekly_report_snapshot_is_current(target_report_snapshot_id)
    and exists (
      select 1
      from report_snapshots as report
      join weekly_runs as run on run.run_id = report.run_id
      where report.report_snapshot_id = target_report_snapshot_id and run.status = 'READY'
    )
$$;

create table publication_intents (
  publication_intent_id text primary key,
  report_snapshot_id text not null,
  target_name text not null check (
    target_name in ('database', 'clickup', 'notion', 'admin_web', 'email')
  ),
  target_id text not null check (btrim(target_id) <> ''),
  idempotency_key text not null unique,
  expected_content_hash text not null check (btrim(expected_content_hash) <> ''),
  schema_readback_ref text not null check (btrim(schema_readback_ref) <> ''),
  status text not null check (
    status in (
      'INTENT_RECORDED', 'WRITE_STARTED', 'UNKNOWN_OUTCOME', 'READBACK_VERIFIED',
      'RECONCILED_STALE', 'FAILED'
    )
  ),
  created_at timestamptz not null,
  foreign key (report_snapshot_id, expected_content_hash)
    references report_snapshots(report_snapshot_id, content_hash),
  unique (report_snapshot_id, target_name),
  unique (publication_intent_id, target_name, target_id)
);

create function weekly_publication_intent_snapshot_is_ready()
returns trigger
language plpgsql
as $$
declare
  snapshot_run_id text;
begin
  select run_id into strict snapshot_run_id
  from report_snapshots
  where report_snapshot_id = new.report_snapshot_id;
  perform 1 from weekly_runs where run_id = snapshot_run_id for update;
  if not weekly_report_snapshot_is_publishable(new.report_snapshot_id) then
    raise exception 'PUBLICATION_INTENT_SNAPSHOT_NOT_CURRENT';
  end if;
  return new;
end
$$;

create trigger publication_intent_snapshot_guard
before insert on publication_intents
for each row execute function weekly_publication_intent_snapshot_is_ready();

create function weekly_publication_intent_transition_is_valid()
returns trigger
language plpgsql
as $$
declare
  intent_run_id text;
begin
  if tg_op = 'DELETE' then
    raise exception 'PUBLICATION_INTENT_DELETE_FORBIDDEN';
  end if;
  if row(
    new.publication_intent_id, new.report_snapshot_id, new.target_name,
    new.target_id, new.idempotency_key, new.expected_content_hash,
    new.schema_readback_ref, new.created_at
  ) is distinct from row(
    old.publication_intent_id, old.report_snapshot_id, old.target_name,
    old.target_id, old.idempotency_key, old.expected_content_hash,
    old.schema_readback_ref, old.created_at
  ) then
    raise exception 'PUBLICATION_INTENT_LINEAGE_IMMUTABLE';
  end if;
  select report.run_id into strict intent_run_id
  from report_snapshots as report where report.report_snapshot_id = new.report_snapshot_id;
  perform 1 from weekly_runs where run_id = intent_run_id for update;
  if new.status in ('WRITE_STARTED', 'READBACK_VERIFIED')
    and not weekly_report_snapshot_is_publishable(new.report_snapshot_id) then
    raise exception 'PUBLICATION_INTENT_SNAPSHOT_NOT_PUBLISHABLE';
  end if;
  if not (
    old.status = new.status
    or (old.status = 'INTENT_RECORDED' and new.status in ('WRITE_STARTED', 'FAILED'))
    or (
      old.status = 'WRITE_STARTED'
      and new.status in ('UNKNOWN_OUTCOME', 'READBACK_VERIFIED', 'FAILED')
    )
    or (
      old.status = 'UNKNOWN_OUTCOME'
      and new.status in ('READBACK_VERIFIED', 'RECONCILED_STALE', 'FAILED')
    )
  ) then
    raise exception 'PUBLICATION_INTENT_TRANSITION_INVALID';
  end if;
  if new.status = 'READBACK_VERIFIED' and not exists (
    select 1 from publication_receipts
    where publication_intent_id = new.publication_intent_id
      and verified = true and publication_eligible = true
  ) then
    raise exception 'PUBLICATION_INTENT_RECEIPT_MISSING';
  end if;
  if new.status = 'RECONCILED_STALE' and not exists (
    select 1 from publication_receipts
    where publication_intent_id = new.publication_intent_id
      and verified = true and publication_eligible = false
  ) then
    raise exception 'PUBLICATION_INTENT_STALE_RECEIPT_MISSING';
  end if;
  return new;
end
$$;

create trigger publication_intent_transition_guard
before update or delete on publication_intents
for each row execute function weekly_publication_intent_transition_is_valid();

create table publication_receipts (
  receipt_id text primary key,
  publication_intent_id text not null unique references publication_intents(publication_intent_id),
  target_name text not null check (
    target_name in ('database', 'clickup', 'notion', 'admin_web', 'email')
  ),
  target_id text not null check (btrim(target_id) <> ''),
  external_object_id text not null check (btrim(external_object_id) <> ''),
  readback_at timestamptz not null,
  readback_content_hash text not null check (btrim(readback_content_hash) <> ''),
  readback_report_snapshot_id text not null references report_snapshots(report_snapshot_id),
  persisted_receipt_ref text not null unique check (btrim(persisted_receipt_ref) <> ''),
  verified boolean not null,
  publication_eligible boolean not null,
  foreign key (publication_intent_id, target_name, target_id)
    references publication_intents(publication_intent_id, target_name, target_id),
  check (verified = true),
  unique (readback_report_snapshot_id, target_name, external_object_id)
);

create function weekly_publication_receipt_matches_intent()
returns trigger
language plpgsql
as $$
declare
  intent_snapshot_id text;
  intent_content_hash text;
  intent_status text;
  intent_run_id text;
  intent_target_name text;
  intent_target_id text;
  intent_created_at timestamptz;
begin
  select intent.report_snapshot_id, intent.expected_content_hash, intent.status, report.run_id,
    intent.target_name, intent.target_id, intent.created_at
    into strict intent_snapshot_id, intent_content_hash, intent_status, intent_run_id,
      intent_target_name, intent_target_id, intent_created_at
  from publication_intents as intent
  join report_snapshots as report
    on report.report_snapshot_id = intent.report_snapshot_id
  where intent.publication_intent_id = new.publication_intent_id;
  perform 1 from weekly_runs where run_id = intent_run_id for update;
  if intent_status not in ('WRITE_STARTED', 'UNKNOWN_OUTCOME') then
    raise exception 'PUBLICATION_RECEIPT_INTENT_STATE_INVALID';
  end if;
  if new.target_name is distinct from intent_target_name
    or new.target_id is distinct from intent_target_id then
    raise exception 'PUBLICATION_RECEIPT_TARGET_MISMATCH';
  end if;
  if new.readback_report_snapshot_id is distinct from intent_snapshot_id
    or new.readback_content_hash is distinct from intent_content_hash then
    raise exception 'PUBLICATION_RECEIPT_LINEAGE_MISMATCH';
  end if;
  if new.readback_at < intent_created_at then
    raise exception 'PUBLICATION_RECEIPT_TIME_INVALID';
  end if;
  if weekly_report_snapshot_is_publishable(intent_snapshot_id) then
    if new.publication_eligible is not true then
      raise exception 'PUBLICATION_RECEIPT_ELIGIBILITY_INVALID';
    end if;
  elsif intent_status = 'UNKNOWN_OUTCOME' then
    if new.publication_eligible is not false then
      raise exception 'PUBLICATION_STALE_RECEIPT_MUST_BE_INELIGIBLE';
    end if;
  else
    raise exception 'PUBLICATION_RECEIPT_SNAPSHOT_NOT_CURRENT';
  end if;
  return new;
end
$$;

create trigger publication_receipt_lineage_guard
before insert on publication_receipts
for each row execute function weekly_publication_receipt_matches_intent();

create trigger publication_receipts_immutable
before update or delete on publication_receipts
for each row execute function weekly_reject_mutation();

create function weekly_run_publication_is_complete(target_run_id text)
returns boolean
language sql
stable
as $$
  select count(*) = 5
    and count(distinct intent.target_name) = 5
    and bool_and(
      intent.status = 'READBACK_VERIFIED' and receipt.verified and receipt.publication_eligible
    )
  from report_snapshots as report
  join publication_intents as intent
    on intent.report_snapshot_id = report.report_snapshot_id
  join publication_receipts as receipt
    on receipt.publication_intent_id = intent.publication_intent_id
  where report.run_id = target_run_id
    and weekly_report_snapshot_is_current(report.report_snapshot_id)
    and exists (
      select 1 from weekly_runs as run
      where run.run_id = target_run_id and run.status in ('READY', 'PUBLISHED')
    )
$$;

create trigger weekly_runs_no_truncate before truncate on weekly_runs
for each statement execute function weekly_reject_truncate();
create trigger consultants_no_truncate before truncate on consultants
for each statement execute function weekly_reject_truncate();
create trigger consultant_provider_accounts_no_truncate before truncate on consultant_provider_accounts
for each statement execute function weekly_reject_truncate();
create trigger position_source_links_no_truncate before truncate on position_source_links
for each statement execute function weekly_reject_truncate();
create trigger customer_intents_no_truncate before truncate on customer_intents
for each statement execute function weekly_reject_truncate();
create trigger canonical_position_state_events_no_truncate before truncate on canonical_position_state_events
for each statement execute function weekly_reject_truncate();
create trigger career_page_observations_no_truncate before truncate on career_page_observations
for each statement execute function weekly_reject_truncate();
create trigger dedupe_decisions_no_truncate before truncate on dedupe_decisions
for each statement execute function weekly_reject_truncate();
create trigger zero_result_assertions_no_truncate before truncate on zero_result_assertions
for each statement execute function weekly_reject_truncate();
create trigger priority_scores_no_truncate before truncate on priority_scores
for each statement execute function weekly_reject_truncate();
create trigger outreach_channel_coverage_no_truncate before truncate on outreach_channel_coverage
for each statement execute function weekly_reject_truncate();
create trigger proposal_send_attempts_no_truncate before truncate on proposal_send_attempts
for each statement execute function weekly_reject_truncate();
create trigger consultant_position_focus_no_truncate before truncate on consultant_position_focus
for each statement execute function weekly_reject_truncate();
create trigger candidate_position_tasks_no_truncate before truncate on candidate_position_tasks
for each statement execute function weekly_reject_truncate();
create trigger candidate_pipeline_events_no_truncate before truncate on candidate_pipeline_events
for each statement execute function weekly_reject_truncate();
create trigger weekly_metric_snapshots_no_truncate before truncate on weekly_metric_snapshots
for each statement execute function weekly_reject_truncate();
create trigger linkedin_market_result_receipts_no_truncate before truncate on linkedin_market_result_receipts
for each statement execute function weekly_reject_truncate();
create trigger linkedin_market_search_snapshots_no_truncate before truncate on linkedin_market_search_snapshots
for each statement execute function weekly_reject_truncate();
create trigger report_snapshots_no_truncate before truncate on report_snapshots
for each statement execute function weekly_reject_truncate();
create trigger publication_intents_no_truncate before truncate on publication_intents
for each statement execute function weekly_reject_truncate();
create trigger publication_receipts_no_truncate before truncate on publication_receipts
for each statement execute function weekly_reject_truncate();
