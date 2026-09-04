-- Supabase's default table privileges can grant service_role more than a
-- later narrow GRANT removes. Reset the ACL before restoring only the
-- operations required by the server and E2E cleanup path.
revoke all privileges on table public.admin_candidate_review_events from service_role;
grant select, insert, delete on table public.admin_candidate_review_events to service_role;
