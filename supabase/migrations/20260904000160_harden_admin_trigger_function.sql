create or replace function admin_touch_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = pg_catalog
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

revoke all on function admin_touch_updated_at() from public, anon, authenticated;
grant execute on function admin_touch_updated_at() to service_role;
