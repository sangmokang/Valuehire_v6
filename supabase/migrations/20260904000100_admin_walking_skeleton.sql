create table if not exists admin_positions (
  id uuid not null default gen_random_uuid(),
  tenant_id text not null,
  external_key text not null,
  title text not null,
  status text not null default 'open',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (id),
  constraint admin_positions_tenant_id_id_unique
    unique (tenant_id, id),
  constraint admin_positions_external_key_unique
    unique (tenant_id, external_key),
  constraint admin_positions_tenant_id_check
    check (tenant_id ~ '^(E2E-TEST-[A-Za-z0-9_-]{1,80}|[a-z0-9][a-z0-9_-]{1,62})$'),
  constraint admin_positions_external_key_check
    check (length(btrim(external_key)) between 1 and 160),
  constraint admin_positions_title_check
    check (length(btrim(title)) between 1 and 160),
  constraint admin_positions_status_check
    check (status in ('open', 'paused', 'closed'))
);

create table if not exists admin_candidates (
  id uuid not null default gen_random_uuid(),
  tenant_id text not null,
  position_id uuid not null,
  external_key text not null,
  display_name text not null,
  review_status text not null default 'unreviewed',
  version integer not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (id),
  constraint admin_candidates_tenant_id_id_unique
    unique (tenant_id, id),
  constraint admin_candidates_external_key_unique
    unique (tenant_id, external_key),
  constraint admin_candidates_position_fk
    foreign key (tenant_id, position_id)
    references admin_positions (tenant_id, id)
    on update cascade
    on delete restrict,
  constraint admin_candidates_tenant_id_check
    check (tenant_id ~ '^(E2E-TEST-[A-Za-z0-9_-]{1,80}|[a-z0-9][a-z0-9_-]{1,62})$'),
  constraint admin_candidates_external_key_check
    check (length(btrim(external_key)) between 1 and 160),
  constraint admin_candidates_display_name_check
    check (length(btrim(display_name)) between 1 and 120),
  constraint admin_candidates_review_status_check
    check (review_status in ('unreviewed', 'reviewed', 'rejected')),
  constraint admin_candidates_version_check
    check (version > 0)
);

create or replace function admin_touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists admin_positions_touch_updated_at on admin_positions;
create trigger admin_positions_touch_updated_at
  before update on admin_positions
  for each row
  execute function admin_touch_updated_at();

drop trigger if exists admin_candidates_touch_updated_at on admin_candidates;
create trigger admin_candidates_touch_updated_at
  before update on admin_candidates
  for each row
  execute function admin_touch_updated_at();

alter table admin_positions enable row level security;
alter table admin_candidates enable row level security;
alter table admin_positions force row level security;
alter table admin_candidates force row level security;

revoke all on admin_positions from public, anon, authenticated;
revoke all on admin_candidates from public, anon, authenticated;

grant select, insert, update, delete on admin_positions to service_role;
grant select, insert, update, delete on admin_candidates to service_role;

drop policy if exists admin_positions_service_role on admin_positions;
create policy admin_positions_service_role
  on admin_positions
  for all
  to service_role
  using (true)
  with check (true);

drop policy if exists admin_candidates_service_role on admin_candidates;
create policy admin_candidates_service_role
  on admin_candidates
  for all
  to service_role
  using (true)
  with check (true);
