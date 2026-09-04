alter table admin_candidates
  add column pending_review_actor_email_sha256 text;

alter table admin_candidates
  add constraint admin_candidates_pending_review_actor_check
  check (
    pending_review_actor_email_sha256 is null
    or pending_review_actor_email_sha256 ~ '^[0-9a-f]{64}$'
  );

create table admin_candidate_review_events (
  id uuid not null default gen_random_uuid(),
  tenant_id text not null,
  candidate_id uuid not null,
  position_id uuid not null,
  actor_email_sha256 text not null,
  from_review_status text not null,
  to_review_status text not null,
  candidate_version integer not null,
  occurred_at timestamptz not null default statement_timestamp(),
  primary key (id),
  constraint admin_review_events_candidate_version_unique
    unique (tenant_id, candidate_id, candidate_version),
  constraint admin_review_events_candidate_fk
    foreign key (tenant_id, candidate_id)
    references admin_candidates (tenant_id, id)
    on update cascade
    on delete restrict,
  constraint admin_review_events_position_fk
    foreign key (tenant_id, position_id)
    references admin_positions (tenant_id, id)
    on update cascade
    on delete restrict,
  constraint admin_review_events_tenant_id_check
    check (tenant_id ~ '^(E2E-TEST-[A-Za-z0-9_-]{1,80}|[a-z0-9][a-z0-9_-]{1,62})$'),
  constraint admin_review_events_actor_hash_check
    check (actor_email_sha256 ~ '^[0-9a-f]{64}$'),
  constraint admin_review_events_from_status_check
    check (from_review_status in ('unreviewed', 'reviewed', 'rejected')),
  constraint admin_review_events_to_status_check
    check (to_review_status in ('unreviewed', 'reviewed', 'rejected')),
  constraint admin_review_events_transition_check
    check (from_review_status <> to_review_status),
  constraint admin_review_events_version_check
    check (candidate_version > 1)
);

create index admin_review_events_candidate_time_idx
  on admin_candidate_review_events (tenant_id, candidate_id, occurred_at);

create or replace function admin_capture_candidate_review_event()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public
as $$
begin
  if tg_op = 'INSERT' then
    if new.pending_review_actor_email_sha256 is not null then
      raise exception 'review actor input is only valid for a transition'
        using errcode = '23514';
    end if;
    return new;
  end if;

  if new.review_status is distinct from old.review_status then
    if new.version is distinct from old.version + 1 then
      raise exception 'review transition must increment version exactly once'
        using errcode = '23514';
    end if;
    if new.pending_review_actor_email_sha256 is null
      or new.pending_review_actor_email_sha256 !~ '^[0-9a-f]{64}$' then
      raise exception 'review transition requires an actor hash'
        using errcode = '23514';
    end if;

    insert into public.admin_candidate_review_events (
      tenant_id,
      candidate_id,
      position_id,
      actor_email_sha256,
      from_review_status,
      to_review_status,
      candidate_version
    ) values (
      new.tenant_id,
      new.id,
      new.position_id,
      new.pending_review_actor_email_sha256,
      old.review_status,
      new.review_status,
      new.version
    );
    new.pending_review_actor_email_sha256 := null;
    return new;
  end if;

  if new.version is distinct from old.version then
    raise exception 'candidate version may change only with review status'
      using errcode = '23514';
  end if;
  if new.pending_review_actor_email_sha256 is not null then
    raise exception 'review actor input is only valid for a transition'
      using errcode = '23514';
  end if;
  return new;
end;
$$;

drop trigger if exists admin_candidates_capture_review_event on admin_candidates;
create trigger admin_candidates_capture_review_event
  before insert or update on admin_candidates
  for each row
  execute function admin_capture_candidate_review_event();

create or replace function admin_guard_candidate_review_event()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog, public
as $$
begin
  if tg_op = 'UPDATE' then
    raise exception 'review audit events are immutable'
      using errcode = '23514';
  end if;
  if old.tenant_id !~ '^E2E-TEST-' then
    raise exception 'production review audit events cannot be deleted'
      using errcode = '23514';
  end if;
  return old;
end;
$$;

drop trigger if exists admin_review_events_guard_mutation on admin_candidate_review_events;
create trigger admin_review_events_guard_mutation
  before update or delete on admin_candidate_review_events
  for each row
  execute function admin_guard_candidate_review_event();

alter table admin_candidate_review_events enable row level security;
alter table admin_candidate_review_events force row level security;

revoke all on admin_candidate_review_events from public, anon, authenticated;
grant select, insert, delete on admin_candidate_review_events to service_role;

drop policy if exists admin_review_events_service_role_select on admin_candidate_review_events;
create policy admin_review_events_service_role_select
  on admin_candidate_review_events
  for select
  to service_role
  using (true);

drop policy if exists admin_review_events_service_role_insert on admin_candidate_review_events;
create policy admin_review_events_service_role_insert
  on admin_candidate_review_events
  for insert
  to service_role
  with check (true);

drop policy if exists admin_review_events_service_role_delete_test on admin_candidate_review_events;
create policy admin_review_events_service_role_delete_test
  on admin_candidate_review_events
  for delete
  to service_role
  using (tenant_id like 'E2E-TEST-%');

revoke all on function admin_capture_candidate_review_event() from public, anon, authenticated;
revoke all on function admin_guard_candidate_review_event() from public, anon, authenticated;
grant execute on function admin_capture_candidate_review_event() to service_role;
grant execute on function admin_guard_candidate_review_event() to service_role;
