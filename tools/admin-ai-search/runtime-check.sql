BEGIN;
DO $$ BEGIN
  IF EXISTS(SELECT 1 FROM public.admin_ai_search_batches WHERE display_number<>
    'W'||lpad(week_number::text,2,'0')||'-'||CASE WHEN grouping_status='PROVISIONAL' THEN 'P' ELSE '' END||
    CASE WHEN COALESCE(sequence,provisional_sequence)<10 THEN '0' ELSE '' END||COALESCE(sequence,provisional_sequence)::text) THEN
    RAISE EXCEPTION 'batch number truncated or reassigned';
  END IF;
  IF EXISTS(SELECT 1 FROM public.admin_ai_search_weekly_rows GROUP BY week_id,candidate_id,position_id HAVING count(*)<>1) THEN
    RAISE EXCEPTION 'candidate position row duplicated';
  END IF;
  IF jsonb_array_length(public.admin_ai_search_read('weeks')->'weeks')<>4 THEN
    RAISE EXCEPTION 'recent week count incorrect';
  END IF;
  IF has_function_privilege('anon','public.admin_ai_search_read(text,jsonb)','execute') OR
     has_table_privilege('authenticated','public.admin_ai_search_source_messages','select') THEN
    RAISE EXCEPTION 'anonymous PII access';
  END IF;
END $$;
-- A completed collection can include a genuine zero-candidate execution.
INSERT INTO public.admin_ai_search_collection_runs VALUES('fixture-run','{"id":"fixture-run","started_at":"9999-01-01","status":"SUCCEEDED","normalization_complete":true,"contact_scopes_complete":false,"scopes":{}}');
INSERT INTO public.admin_ai_search_source_messages VALUES('fixture-message','{"id":"fixture-message"}');
INSERT INTO public.admin_ai_search_positions VALUES('fixture-position','{"id":"fixture-position","company":"Fixture Client","title":"Fixture Engineer","status":"PASS"}');
SELECT public.admin_ai_search_register_batch('{"id":"fixture-batch","week_year":2000,"week_number":44,"grouping_status":"CONFIRMED","document":{"id":"fixture-batch","week_id":"2000-W44","actor":"GROK"}}');
INSERT INTO public.admin_ai_search_batch_source_messages VALUES('fixture-batch-source','{"id":"fixture-batch-source","batch_id":"fixture-batch","source_message_id":"fixture-message","position_id":"fixture-position","raw":0,"parsed":0,"duplicate":0,"unparsed":0,"excluded":0,"counts_status":"PASS"}');
DO $$ DECLARE response jsonb; BEGIN
  response:=public.admin_ai_search_read('weekly','{"week":"2000-W44"}');
  IF response->'summary'->>'batches'<>'1' OR response->'summary'->>'positions'<>'1' OR response->'summary'->>'candidates'<>'0' THEN
    RAISE EXCEPTION 'zero-candidate execution was lost';
  END IF;
END $$;
INSERT INTO public.admin_ai_search_candidates VALUES('fixture-candidate','{"id":"fixture-candidate"}');
INSERT INTO public.admin_ai_search_candidate_batches VALUES('fixture-cb','{"id":"fixture-cb","candidate_id":"fixture-candidate","position_id":"fixture-position","batch_id":"fixture-batch"}');
INSERT INTO public.admin_ai_search_candidate_position_evaluations VALUES('fixture-eval','{"id":"fixture-eval","candidate_id":"fixture-candidate","position_id":"fixture-position","batch_id":"fixture-batch","source_message_id":"fixture-message","week_id":"2000-W44","score_status":"NOT_RUN","score":null,"candidate_name":"Fixture Candidate","evaluated_at":"2000-10-22T00:00:00+09:00"}');
DO $$ DECLARE response jsonb; BEGIN
  response:=public.admin_ai_search_read('high-score-uncontacted','{"week":"2000-W44"}');
  IF response->'summary'->'high_score_uncontacted'<>'null'::jsonb OR response->>'total'<>'0' THEN
    RAISE EXCEPTION 'missing score/contact evidence became confirmed uncontacted';
  END IF;
  response:=public.admin_ai_search_read('weekly','{"week":"2000-W44","q":"absent"}');
  IF response->>'total'<>'0' OR response->'summary'->>'candidates'<>'0' THEN
    RAISE EXCEPTION 'summary and row filters diverged';
  END IF;
  response:=public.admin_ai_search_read('weekly','{"week":"2000-W44","contact_status":"NOT_RUN","channel":"LINKEDIN"}');
  IF response->>'total'<>'1' THEN RAISE EXCEPTION 'unverified channel filter incorrect'; END IF;
END $$;
ROLLBACK;
SELECT 'number identity, row merging, zero-candidate batch, filters, fail-closed scores, RLS: PASS' AS runtime_checks;
