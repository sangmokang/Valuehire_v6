-- pipeline_candidates
create table if not exists pipeline_candidates (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  jd_id text,
  jd_title text,
  stage text not null default 'talent_pool',
  match_score int default 0,
  skills text[] default '{}',
  memo text default '',
  source text default 'local_upload',
  file_name text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- pipeline_stage_history
create table if not exists pipeline_stage_history (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid references pipeline_candidates(id) on delete cascade,
  from_stage text,
  to_stage text not null,
  changed_by text,
  changed_at timestamptz default now()
);

-- pipeline_comments
create table if not exists pipeline_comments (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid references pipeline_candidates(id) on delete cascade,
  author_email text not null,
  content text,
  mentions text[] default '{}',
  draft text,
  created_at timestamptz default now()
);

-- pipeline_members
create table if not exists pipeline_members (
  id uuid primary key default gen_random_uuid(),
  user_email text not null unique,
  role text not null default 'viewer' check (role in ('admin','reviewer','viewer')),
  invited_by text,
  created_at timestamptz default now()
);

-- RLS 활성화
alter table pipeline_candidates enable row level security;
alter table pipeline_stage_history enable row level security;
alter table pipeline_comments enable row level security;
alter table pipeline_members enable row level security;

-- 서비스 롤 전체 접근
create policy "service_all_candidates" on pipeline_candidates for all using (true);
create policy "service_all_history" on pipeline_stage_history for all using (true);
create policy "service_all_comments" on pipeline_comments for all using (true);
create policy "service_all_members" on pipeline_members for all using (true);
