drop policy if exists "service_all_candidates" on pipeline_candidates;
drop policy if exists "service_all_history" on pipeline_stage_history;
drop policy if exists "service_all_comments" on pipeline_comments;
drop policy if exists "service_all_members" on pipeline_members;

revoke all on pipeline_candidates from public, anon, authenticated;
revoke all on pipeline_stage_history from public, anon, authenticated;
revoke all on pipeline_comments from public, anon, authenticated;
revoke all on pipeline_members from public, anon, authenticated;

grant select, insert, update, delete on pipeline_candidates to service_role;
grant select, insert, update, delete on pipeline_stage_history to service_role;
grant select, insert, update, delete on pipeline_comments to service_role;
grant select, insert, update, delete on pipeline_members to service_role;

create policy pipeline_candidates_service_role
  on pipeline_candidates
  for all
  to service_role
  using (true)
  with check (true);

create policy pipeline_stage_history_service_role
  on pipeline_stage_history
  for all
  to service_role
  using (true)
  with check (true);

create policy pipeline_comments_service_role
  on pipeline_comments
  for all
  to service_role
  using (true)
  with check (true);

create policy pipeline_members_service_role
  on pipeline_members
  for all
  to service_role
  using (true)
  with check (true);
