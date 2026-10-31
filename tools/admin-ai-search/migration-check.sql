DO $$ DECLARE a jsonb; b jsonb; c jsonb; i integer; denied boolean:=false; BEGIN
  a:=public.admin_ai_search_register_batch('{"id":"migration-test-a","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"migration-test-a"}}');
  b:=public.admin_ai_search_register_batch('{"id":"migration-test-b","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"migration-test-b"}}');
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-a","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"migration-test-a"}}');
  IF a->>'display_number'<>'W44-01' OR b->>'display_number'<>'W44-02' OR c->>'display_number'<>'W44-01' THEN
    RAISE EXCEPTION 'permanent batch number invariant failed';
  END IF;
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-p","week_year":2000,"week_number":44,"grouping_status":"PROVISIONAL","document":{"id":"migration-test-p","actor":"CODEX"}}');
  IF c->>'display_number'<>'W44-03' THEN RAISE EXCEPTION 'executors do not share the weekly sequence'; END IF;
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-p","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"migration-test-p"}}');
  IF c->>'display_number'<>'W44-03' OR c->>'grouping_status'<>'CONFIRMED' THEN
    RAISE EXCEPTION 'confirmation changed the permanent display number';
  END IF;
  INSERT INTO public.admin_ai_search_batches VALUES('migration-test-legacy',2000,44,NULL,9,'PROVISIONAL','W44-P09','{"id":"migration-test-legacy"}');
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-legacy","week_year":2000,"week_number":44,"grouping_status":"PROVISIONAL","document":{"id":"migration-test-legacy"}}');
  IF c->>'display_number'<>'W44-04' OR NOT (c->'document'->'display_number_history') ? 'W44-P09' THEN
    RAISE EXCEPTION 'legacy provisional number not converted once with history';
  END IF;
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-legacy","week_year":2000,"week_number":44,"grouping_status":"PROVISIONAL","document":{"id":"migration-test-legacy"}}');
  IF c->>'display_number'<>'W44-04' THEN RAISE EXCEPTION 'legacy number reassigned twice'; END IF;
  FOR i IN 6..100 LOOP
    c:=public.admin_ai_search_register_batch(jsonb_build_object('id','migration-test-n'||i,'week_year',2000,'week_number',45,'grouping_status','PROVISIONAL','document','{}'::jsonb));
  END LOOP;
  IF c->>'display_number'<>'W45-95' THEN RAISE EXCEPTION 'sequence gap in other week'; END IF;
  FOR i IN 96..100 LOOP
    c:=public.admin_ai_search_register_batch(jsonb_build_object('id','migration-test-m'||i,'week_year',2000,'week_number',45,'grouping_status','PROVISIONAL','document','{}'::jsonb));
  END LOOP;
  IF c->>'display_number'<>'W45-100' THEN RAISE EXCEPTION 'three digit batch number truncated'; END IF;
  c:=public.admin_ai_search_register_batch('{"id":"migration-test-p2","week_year":2000,"week_number":44,"grouping_status":"PROVISIONAL","document":{"id":"migration-test-p2"}}');
  IF c->>'display_number'<>'W44-05' THEN RAISE EXCEPTION 'shared number reused'; END IF;
  BEGIN
    INSERT INTO public.admin_ai_search_contact_events VALUES('migration-bad-negative','{"channel":"GMAIL","actor":"UNKNOWN","status":"CONFIRMED_NOT_CONTACTED","pagination_exhausted":false}');
  EXCEPTION WHEN check_violation THEN denied:=true; END;
  IF NOT denied THEN RAISE EXCEPTION 'unproven negative contact accepted'; END IF;
  IF has_function_privilege('anon','public.admin_ai_search_read(text,jsonb)','execute') OR
     has_table_privilege('authenticated','public.admin_ai_search_source_messages','select') THEN
    RAISE EXCEPTION 'PII permission leak';
  END IF;
END $$;
DELETE FROM public.admin_ai_search_batches WHERE id LIKE 'migration-test-%' OR id IN ('migration-test-a','migration-test-b','migration-test-p','migration-test-p2','migration-test-legacy');
SELECT 'batch allocation, negative-contact gate, anonymous access: PASS' AS migration_checks;
