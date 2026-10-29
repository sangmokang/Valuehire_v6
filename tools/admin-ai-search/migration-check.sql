DO $$ DECLARE a jsonb; b jsonb; c jsonb; denied boolean:=false; BEGIN
  a:=public.admin_ai_search_register_batch('{"id":"migration-test-a","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"migration-test-a"}}');
  b:=public.admin_ai_search_register_batch('{"id":"migration-test-b","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"migration-test-b"}}');
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-a","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"migration-test-a"}}');
  IF a->>'display_number'<>'W44-01' OR b->>'display_number'<>'W44-02' OR c->>'display_number'<>'W44-01' THEN
    RAISE EXCEPTION 'permanent batch number invariant failed';
  END IF;
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-p","week_year":2000,"week_number":44,"grouping_status":"PROVISIONAL","document":{"id":"migration-test-p"}}');
  IF c->>'display_number'<>'W44-P01' THEN RAISE EXCEPTION 'provisional number invariant failed'; END IF;
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-p","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"migration-test-p"}}');
  IF c->>'display_number'<>'W44-03' OR c->>'provisional_sequence'<>'1' THEN
    RAISE EXCEPTION 'confirmation lost permanent identity or provisional reservation';
  END IF;
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-p2","week_year":2000,"week_number":44,"grouping_status":"PROVISIONAL","document":{"id":"migration-test-p2"}}');
  IF c->>'display_number'<>'W44-P02' THEN RAISE EXCEPTION 'provisional number reused'; END IF;
  BEGIN
    INSERT INTO public.admin_ai_search_contact_events VALUES('migration-bad-negative','{"channel":"GMAIL","actor":"UNKNOWN","status":"CONFIRMED_NOT_CONTACTED","pagination_exhausted":false}');
  EXCEPTION WHEN check_violation THEN denied:=true; END;
  IF NOT denied THEN RAISE EXCEPTION 'unproven negative contact accepted'; END IF;
  IF has_function_privilege('anon','public.admin_ai_search_read(text,jsonb)','execute') OR
     has_table_privilege('authenticated','public.admin_ai_search_source_messages','select') THEN
    RAISE EXCEPTION 'PII permission leak';
  END IF;
END $$;
DELETE FROM public.admin_ai_search_batches WHERE id IN ('migration-test-a','migration-test-b','migration-test-p','migration-test-p2');
SELECT 'batch allocation, negative-contact gate, anonymous access: PASS' AS migration_checks;
