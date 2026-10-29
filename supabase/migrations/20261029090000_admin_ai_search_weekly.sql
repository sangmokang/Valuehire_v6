-- Additive module; existing administrator tables and policies are untouched.
-- JSON documents belong to separate entities; indexed generated keys enforce relations.
CREATE TABLE public.admin_ai_search_collection_runs (id text PRIMARY KEY, document jsonb NOT NULL);
CREATE TABLE public.admin_ai_search_source_messages (id text PRIMARY KEY, document jsonb NOT NULL);
CREATE TABLE public.admin_ai_search_collection_checkpoints (id text PRIMARY KEY, document jsonb NOT NULL);
CREATE TABLE public.admin_ai_search_settings (id text PRIMARY KEY, document jsonb NOT NULL);
CREATE TABLE public.admin_ai_search_positions (id text PRIMARY KEY, document jsonb NOT NULL);
CREATE TABLE public.admin_ai_search_candidates (id text PRIMARY KEY, document jsonb NOT NULL);
CREATE TABLE public.admin_ai_search_batches (
  id text PRIMARY KEY, week_year integer NOT NULL, week_number integer NOT NULL CHECK(week_number BETWEEN 1 AND 53),
  sequence integer, provisional_sequence integer,
  grouping_status text NOT NULL CHECK(grouping_status IN ('CONFIRMED','PROVISIONAL')),
  display_number text NOT NULL, document jsonb NOT NULL,
  UNIQUE(week_year,week_number,sequence), UNIQUE(week_year,week_number,provisional_sequence),
  CHECK ((grouping_status='CONFIRMED' AND sequence>0 AND (provisional_sequence IS NULL OR provisional_sequence>0)) OR
         (grouping_status='PROVISIONAL' AND sequence IS NULL AND provisional_sequence>0))
);
CREATE TABLE public.admin_ai_search_source_attachments (
  id text PRIMARY KEY, document jsonb NOT NULL,
  source_message_id text GENERATED ALWAYS AS(document->>'source_message_id') STORED
    REFERENCES public.admin_ai_search_source_messages(id)
);
CREATE TABLE public.admin_ai_search_batch_source_messages (
  id text PRIMARY KEY, document jsonb NOT NULL,
  source_message_id text GENERATED ALWAYS AS(document->>'source_message_id') STORED
    REFERENCES public.admin_ai_search_source_messages(id),
  batch_id text GENERATED ALWAYS AS(document->>'batch_id') STORED REFERENCES public.admin_ai_search_batches(id)
);
CREATE TABLE public.admin_ai_search_candidate_batches (
  id text PRIMARY KEY, document jsonb NOT NULL,
  candidate_id text GENERATED ALWAYS AS(document->>'candidate_id') STORED REFERENCES public.admin_ai_search_candidates(id),
  position_id text GENERATED ALWAYS AS(document->>'position_id') STORED REFERENCES public.admin_ai_search_positions(id),
  batch_id text GENERATED ALWAYS AS(document->>'batch_id') STORED REFERENCES public.admin_ai_search_batches(id),
  UNIQUE(candidate_id,position_id,batch_id)
);
CREATE TABLE public.admin_ai_search_candidate_position_evaluations (
  id text PRIMARY KEY, document jsonb NOT NULL,
  candidate_id text GENERATED ALWAYS AS(document->>'candidate_id') STORED REFERENCES public.admin_ai_search_candidates(id),
  position_id text GENERATED ALWAYS AS(document->>'position_id') STORED REFERENCES public.admin_ai_search_positions(id),
  batch_id text GENERATED ALWAYS AS(document->>'batch_id') STORED REFERENCES public.admin_ai_search_batches(id),
  source_message_id text GENERATED ALWAYS AS(document->>'source_message_id') STORED REFERENCES public.admin_ai_search_source_messages(id),
  CHECK(document->>'score_status' IN ('PASS','NOT_RUN')),
  CHECK(document->>'score_status'<>'PASS' OR COALESCE((
    document->>'score' IS NOT NULL AND jsonb_typeof(document->'score_components')='object'
    AND document->'score_components' ?& ARRAY['education','job_fit','difficult_work','job_description_logic']
    AND document->>'score_input_hash' IS NOT NULL),false))
);
CREATE INDEX admin_ai_search_evaluation_week ON public.admin_ai_search_candidate_position_evaluations((document->>'week_id'),candidate_id,position_id);
CREATE INDEX admin_ai_search_evaluation_pair ON public.admin_ai_search_candidate_position_evaluations(candidate_id,position_id,source_message_id);
CREATE TABLE public.admin_ai_search_score_components (
  id text PRIMARY KEY, document jsonb NOT NULL,
  evaluation_id text GENERATED ALWAYS AS(document->>'evaluation_id') STORED REFERENCES public.admin_ai_search_candidate_position_evaluations(id),
  CHECK((document->>'score')::numeric BETWEEN 0 AND 100)
);
CREATE UNIQUE INDEX admin_ai_search_component_axis ON public.admin_ai_search_score_components(evaluation_id,(document->>'axis'));
CREATE TABLE public.admin_ai_search_contact_events (
  id text PRIMARY KEY, document jsonb NOT NULL,
  candidate_id text GENERATED ALWAYS AS(document->>'candidate_id') STORED REFERENCES public.admin_ai_search_candidates(id),
  position_id text GENERATED ALWAYS AS(document->>'position_id') STORED REFERENCES public.admin_ai_search_positions(id),
  CHECK(document->>'channel' IN ('SARAMIN','JOBKOREA','LINKEDIN','GMAIL')),
  CHECK(document->>'actor' IN ('AI','OWNER','UNKNOWN')),
  CHECK(document->>'status' IN ('CONTACTED','REPLIED','CONFIRMED_NOT_CONTACTED','NOT_RUN','REVIEW_REQUIRED','FAILED')),
  CHECK(document->>'status'<>'CONFIRMED_NOT_CONTACTED' OR COALESCE((
    document->'pagination_exhausted'='true'::jsonb AND document->>'scope' IS NOT NULL
    AND document->>'checked_at' IS NOT NULL AND candidate_id IS NOT NULL AND position_id IS NOT NULL),false))
);
CREATE INDEX admin_ai_search_contact_pair ON public.admin_ai_search_contact_events(candidate_id,position_id);
CREATE TABLE public.admin_ai_search_contact_evidence (id text PRIMARY KEY, document jsonb NOT NULL);
CREATE TABLE public.admin_ai_search_review_queue (id text PRIMARY KEY, document jsonb NOT NULL);
CREATE INDEX admin_ai_search_review_source ON public.admin_ai_search_review_queue((document->>'source_message_id'));
CREATE INDEX admin_ai_search_contact_evidence_source ON public.admin_ai_search_contact_evidence((document->>'source_message_id'));

-- Allocation is serialized for a week; rediscovery never renumbers an existing ID.
CREATE FUNCTION public.admin_ai_search_register_batch(p_batch jsonb)
RETURNS jsonb LANGUAGE plpgsql SET search_path=public,pg_temp AS $$
DECLARE existing public.admin_ai_search_batches; n integer; provisional boolean; history jsonb;
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext('admin_ai_search_batch_registry'));
  SELECT * INTO existing FROM admin_ai_search_batches WHERE id=p_batch->>'id' FOR UPDATE;
  IF FOUND THEN
    IF existing.grouping_status='PROVISIONAL' AND p_batch->>'grouping_status'='CONFIRMED' THEN
      SELECT COALESCE(MAX(sequence),0)+1 INTO n FROM admin_ai_search_batches
        WHERE week_year=existing.week_year AND week_number=existing.week_number;
      history:=COALESCE(p_batch->'document'->'display_number_history',existing.document->'display_number_history','[]'::jsonb);
      IF NOT history ? existing.display_number THEN history:=history||jsonb_build_array(existing.display_number); END IF;
      UPDATE admin_ai_search_batches SET sequence=n,grouping_status='CONFIRMED',
        display_number='W'||lpad(existing.week_number::text,2,'0')||'-'||CASE WHEN n<10 THEN '0' ELSE '' END||n::text,
        document=existing.document||p_batch->'document'||jsonb_build_object('display_number_history',history)
        WHERE id=existing.id RETURNING * INTO existing;
      RETURN to_jsonb(existing);
    END IF;
    UPDATE admin_ai_search_batches SET document=existing.document || p_batch->'document' WHERE id=existing.id;
    RETURN to_jsonb(existing);
  END IF;
  provisional := p_batch->>'grouping_status'='PROVISIONAL';
  SELECT COALESCE(MAX(CASE WHEN provisional THEN provisional_sequence ELSE sequence END),0)+1 INTO n
    FROM admin_ai_search_batches WHERE week_year=(p_batch->>'week_year')::integer
    AND week_number=(p_batch->>'week_number')::integer;
  INSERT INTO admin_ai_search_batches VALUES (
    p_batch->>'id',(p_batch->>'week_year')::integer,(p_batch->>'week_number')::integer,
    CASE WHEN NOT provisional THEN n END,CASE WHEN provisional THEN n END,p_batch->>'grouping_status',
    'W'||lpad(p_batch->>'week_number',2,'0')||'-'||CASE WHEN provisional THEN 'P' ELSE '' END||
      CASE WHEN n<10 THEN '0' ELSE '' END||n::text,
    p_batch->'document') RETURNING * INTO existing;
  RETURN to_jsonb(existing);
END $$;

CREATE VIEW public.admin_ai_search_active_evaluations WITH(security_invoker=true) AS
SELECT e.* FROM public.admin_ai_search_candidate_position_evaluations e
JOIN public.admin_ai_search_source_messages m ON m.id=e.source_message_id
WHERE e.document->>'evaluation_version'=m.document->>'parser_version'
  AND m.document->>'processing_status'='PROCESSED';

CREATE VIEW public.admin_ai_search_active_batch_sources WITH(security_invoker=true) AS
SELECT s.* FROM public.admin_ai_search_batch_source_messages s
JOIN public.admin_ai_search_source_messages m ON m.id=s.source_message_id
WHERE s.document->>'parser_version'=m.document->>'parser_version'
  AND m.document->>'processing_status'='PROCESSED';

CREATE VIEW public.admin_ai_search_weekly_rows WITH(security_invoker=true) AS
WITH ranked AS (
  SELECT e.*,row_number() OVER(PARTITION BY document->>'week_id',candidate_id,position_id
    ORDER BY document->>'evaluated_at' DESC,document->>'evaluation_version' DESC,id DESC) AS ranking
  FROM public.admin_ai_search_active_evaluations e
)
SELECT e.id,e.candidate_id,e.position_id,e.document->>'week_id' AS week_id,
  p.document->>'company' AS company,p.document->>'title' AS position,
  p.document->>'status' AS position_status,e.document AS evaluation,
  (SELECT jsonb_agg(to_jsonb(b) ORDER BY b.week_year,b.week_number,COALESCE(b.sequence,b.provisional_sequence))
   FROM admin_ai_search_batches b WHERE b.id IN (SELECT batch_id FROM admin_ai_search_active_evaluations ae
     WHERE ae.candidate_id=e.candidate_id AND ae.position_id=e.position_id AND ae.document->>'week_id'=e.document->>'week_id')) AS batches,
  (SELECT COALESCE(jsonb_agg(c.document),'[]'::jsonb) FROM admin_ai_search_contact_events c
   WHERE c.candidate_id=e.candidate_id AND c.position_id=e.position_id) AS contacts,
  (SELECT COALESCE(jsonb_agg(c.document),'[]'::jsonb) FROM admin_ai_search_contact_events c
   WHERE c.candidate_id=e.candidate_id AND c.position_id=e.position_id
   AND (c.document->>'sent_at')::timestamptz >= ((to_date(e.document->>'week_id','IYYY-"W"IW')-8)::timestamp AT TIME ZONE 'Asia/Seoul')
   AND (c.document->>'sent_at')::timestamptz < ((to_date(e.document->>'week_id','IYYY-"W"IW')-1)::timestamp AT TIME ZONE 'Asia/Seoul')) AS weekly_contacts
FROM ranked e JOIN admin_ai_search_positions p ON p.id=e.position_id WHERE ranking=1;

CREATE FUNCTION public.admin_ai_search_read(p_action text,p_args jsonb DEFAULT '{}')
RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path=public,pg_temp AS $$
DECLARE result jsonb; run jsonb; rows jsonb; total integer; summary jsonb;
  limit_n integer := least(200,greatest(1,COALESCE((p_args->>'limit')::integer,50)));
  offset_n integer := greatest(0,COALESCE((p_args->>'offset')::integer,0));
  threshold integer; complete boolean;
BEGIN
  SELECT document INTO run FROM admin_ai_search_collection_runs ORDER BY document->>'started_at' DESC LIMIT 1;
  SELECT (document->>'high_score_threshold')::integer INTO threshold FROM admin_ai_search_settings WHERE id='contract';
  complete := COALESCE(run->>'status'='SUCCEEDED' AND run->'normalization_complete'='true'::jsonb,false);
  IF p_action='collection-status' THEN
    RETURN jsonb_build_object('run',(run-'error'-'errors'-'scopes') || jsonb_build_object('scopes',
      (SELECT jsonb_object_agg(k,(v-'message_ids'-'page_history'-'next_page_token') ||
        jsonb_build_object('message_count',jsonb_array_length(v->'message_ids'))) FROM jsonb_each(run->'scopes') AS s(k,v))),
      'complete',complete,
      'review_count',(SELECT count(*) FROM admin_ai_search_review_queue WHERE document->>'status'='OPEN'),
      'failed_count',(SELECT count(*) FROM admin_ai_search_source_messages WHERE document->>'processing_status'='FAILED'));
  ELSIF p_action='weeks' THEN
    SELECT jsonb_agg(jsonb_build_object('week_id',to_char(sunday+8,'IYYY-"W"IW'),
      'start_date',sunday,'end_date',sunday+6) ORDER BY sunday DESC) INTO result
    FROM (SELECT (date_trunc('week',(now() AT TIME ZONE 'Asia/Seoul')+interval '1 day')::date-1 - g*7) AS sunday
      FROM generate_series(0,3) g) w;
    RETURN jsonb_build_object('weeks',result,'collection_complete',complete,'high_score_threshold',threshold);
  ELSIF p_action='review-queue' THEN
    SELECT count(*) INTO total FROM admin_ai_search_review_queue WHERE document->>'status'='OPEN';
    SELECT COALESCE(jsonb_agg(document),'[]') INTO rows FROM (
      SELECT document FROM admin_ai_search_review_queue WHERE document->>'status'='OPEN' ORDER BY id LIMIT limit_n OFFSET offset_n) q;
    RETURN jsonb_build_object('total',total,'rows',rows);
  ELSIF p_action='batches' THEN
    SELECT to_jsonb(b) || jsonb_build_object(
      'sources',(SELECT jsonb_agg(s.document) FROM admin_ai_search_batch_source_messages s WHERE s.batch_id=b.id),
      'candidate_counts',(SELECT jsonb_build_object(
        'status',CASE WHEN bool_and(s.document->>'counts_status'='PASS') THEN 'PASS' ELSE 'NOT_RUN' END,
        'raw',CASE WHEN bool_and(s.document->>'counts_status'='PASS') THEN sum((s.document->>'raw')::integer) END,
        'parsed',(SELECT count(DISTINCT candidate_id) FROM admin_ai_search_active_evaluations WHERE batch_id=b.id),
        'unparsed',CASE WHEN bool_and(s.document->>'counts_status'='PASS') THEN sum((s.document->>'unparsed')::integer) END,
        'excluded',sum((s.document->>'excluded')::integer),
        'duplicate',CASE WHEN bool_and(s.document->>'counts_status'='PASS') THEN
          sum((s.document->>'raw')::integer-(s.document->>'unparsed')::integer-(s.document->>'excluded')::integer)
          -(SELECT count(DISTINCT candidate_id) FROM admin_ai_search_active_evaluations WHERE batch_id=b.id) END)
        FROM admin_ai_search_active_batch_sources s WHERE s.batch_id=b.id))
      INTO result FROM admin_ai_search_batches b WHERE id=p_args->>'id';
    RETURN result;
  ELSIF p_action='candidates' THEN
    SELECT jsonb_build_object('candidate',c.document,
      'evaluations',(SELECT jsonb_agg(e.document ORDER BY e.document->>'evaluated_at' DESC) FROM admin_ai_search_candidate_position_evaluations e WHERE e.candidate_id=c.id),
      'positions',(SELECT jsonb_agg(p.document) FROM admin_ai_search_positions p WHERE p.id IN (SELECT position_id FROM admin_ai_search_candidate_position_evaluations WHERE candidate_id=c.id)),
      'batches',(SELECT jsonb_agg(to_jsonb(b)) FROM admin_ai_search_batches b WHERE b.id IN (SELECT batch_id FROM admin_ai_search_candidate_batches WHERE candidate_id=c.id)),
      'contacts',(SELECT COALESCE(jsonb_agg(document),'[]') FROM admin_ai_search_contact_events WHERE candidate_id=c.id),
      'score_components',(SELECT COALESCE(jsonb_agg(s.document),'[]') FROM admin_ai_search_score_components s WHERE s.evaluation_id IN (SELECT id FROM admin_ai_search_candidate_position_evaluations WHERE candidate_id=c.id)),
      'source_messages',(SELECT jsonb_agg(m.document) FROM admin_ai_search_source_messages m WHERE m.id IN (SELECT source_message_id FROM admin_ai_search_candidate_position_evaluations WHERE candidate_id=c.id)),
      'review_queue',(SELECT COALESCE(jsonb_agg(document),'[]') FROM admin_ai_search_review_queue WHERE document->>'source_message_id' IN (SELECT source_message_id FROM admin_ai_search_candidate_position_evaluations WHERE candidate_id=c.id)))
      INTO result FROM admin_ai_search_candidates c WHERE id=p_args->>'id';
    RETURN result;
  ELSIF p_action NOT IN ('weekly','high-score-uncontacted') THEN
    RAISE EXCEPTION 'unknown read action';
  END IF;
  -- All predicates apply before both summary and pagination; no client-side counting.
  WITH scoped AS (
    SELECT chosen.id,w.candidate_id,w.position_id,w.week_id,w.company,w.position,w.position_status,
      chosen.document AS evaluation,
      (SELECT jsonb_agg(b) FROM jsonb_array_elements(w.batches) b WHERE COALESCE(p_args->>'actor','')=''
        OR b->'document'->>'actor'=p_args->>'actor') AS batches,w.contacts,w.weekly_contacts
    FROM admin_ai_search_weekly_rows w CROSS JOIN LATERAL (
      SELECT e.id,e.document FROM admin_ai_search_active_evaluations e
      JOIN admin_ai_search_batches b ON b.id=e.batch_id WHERE e.candidate_id=w.candidate_id
        AND e.position_id=w.position_id AND e.document->>'week_id'=w.week_id
        AND (COALESCE(p_args->>'actor','')='' OR b.document->>'actor'=p_args->>'actor')
      ORDER BY e.document->>'evaluated_at' DESC,e.document->>'evaluation_version' DESC,e.id DESC LIMIT 1
    ) chosen
  ), filtered AS (
    SELECT w.*,NOT EXISTS(SELECT 1 FROM admin_ai_search_review_queue WHERE document->>'reason' IN
      ('unlinked_sent_contact','contact_report_binding_pending') AND document->>'status'='OPEN')
      AND (SELECT count(DISTINCT c->>'channel')=4 FROM jsonb_array_elements(w.contacts) c
           WHERE c->>'status'='CONFIRMED_NOT_CONTACTED')
      AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(w.contacts) c WHERE c->>'status' IN ('CONTACTED','REPLIED','FAILED','REVIEW_REQUIRED'))
      AS confirmed_uncontacted,
      EXISTS(SELECT 1 FROM jsonb_array_elements(w.weekly_contacts) c WHERE c->>'status' IN ('CONTACTED','REPLIED')
        AND c->>'event_type' IN ('JD_SENT','PROPOSAL_SENT','INMAIL_SENT')) AS jd_sent_verified,
      (SELECT count(DISTINCT c->>'channel')=4 FROM jsonb_array_elements(w.contacts) c
        WHERE c->>'status' IN ('CONTACTED','REPLIED','CONFIRMED_NOT_CONTACTED')
        AND c->'pagination_exhausted'='true'::jsonb
        AND c->'scope'->'complete_for_candidate_position'='true'::jsonb
        AND (c->>'checked_at')::timestamptz >= ((to_date(w.week_id,'IYYY-"W"IW')-1)::timestamp AT TIME ZONE 'Asia/Seoul')) AS contact_scope_complete
    FROM scoped w
    WHERE w.week_id=p_args->>'week'
      AND (COALESCE(p_args->>'q','')='' OR concat_ws(' ',w.company,w.position,w.evaluation->>'candidate_name') ILIKE '%'||(p_args->>'q')||'%')
      AND (COALESCE(p_args->>'company','')='' OR w.company=p_args->>'company')
      AND (COALESCE(p_args->>'position','')='' OR w.position=p_args->>'position')
      AND (COALESCE(p_args->>'actor','')='' OR EXISTS(SELECT 1 FROM jsonb_array_elements(w.batches) b WHERE b->'document'->>'actor'=p_args->>'actor'))
      AND (COALESCE(p_args->>'contact_status','')='' OR EXISTS(SELECT 1 FROM jsonb_array_elements(w.contacts) c
        WHERE (COALESCE(p_args->>'channel','')='' OR c->>'channel'=p_args->>'channel') AND c->>'status'=p_args->>'contact_status')
        OR (p_args->>'contact_status'='NOT_RUN' AND EXISTS(SELECT 1 FROM unnest(ARRAY['SARAMIN','JOBKOREA','LINKEDIN','GMAIL']) ch
          WHERE (COALESCE(p_args->>'channel','')='' OR ch=p_args->>'channel') AND NOT EXISTS(
            SELECT 1 FROM jsonb_array_elements(w.contacts) c WHERE c->>'channel'=ch))))
  ), targets AS (
    SELECT DISTINCT b.id AS batch_id,b.grouping_status,s.document->>'position_id' AS position_id,p.document->>'status' AS position_status
    FROM admin_ai_search_batches b JOIN admin_ai_search_active_batch_sources s ON s.batch_id=b.id
    JOIN admin_ai_search_positions p ON p.id=s.document->>'position_id'
    WHERE b.document->>'week_id'=p_args->>'week'
      AND (COALESCE(p_args->>'actor','')='' OR b.document->>'actor'=p_args->>'actor')
      AND (COALESCE(p_args->>'company','')='' OR p.document->>'company'=p_args->>'company')
      AND (COALESCE(p_args->>'position','')='' OR p.document->>'title'=p_args->>'position')
      AND (COALESCE(p_args->>'q','')='' OR concat_ws(' ',p.document->>'company',p.document->>'title') ILIKE '%'||(p_args->>'q')||'%'
        OR EXISTS(SELECT 1 FROM filtered f WHERE f.position_id=p.id AND EXISTS(SELECT 1 FROM jsonb_array_elements(f.batches) fb WHERE fb->>'id'=b.id)))
      AND (COALESCE(p_args->>'contact_status','')='' OR EXISTS(SELECT 1 FROM filtered f WHERE f.position_id=p.id AND EXISTS(
        SELECT 1 FROM jsonb_array_elements(f.batches) fb WHERE fb->>'id'=b.id)))
  ), readiness AS (
    SELECT complete AND NOT EXISTS(SELECT 1 FROM targets t JOIN admin_ai_search_active_batch_sources s ON s.batch_id=t.batch_id
        WHERE s.document->>'counts_status'<>'PASS' OR COALESCE((s.document->>'unparsed')::integer,0)>0)
      AND NOT EXISTS(SELECT 1 FROM admin_ai_search_source_messages m WHERE m.document->>'processing_status'='REVIEW_REQUIRED'
        AND m.document->>'reason' IN ('potential_ai_search_requires_review','ai_search_result_identity_not_proven')
        AND (m.document->>'received_at')::timestamptz >= ((to_date(p_args->>'week','IYYY-"W"IW')-8)::timestamp AT TIME ZONE 'Asia/Seoul')
        AND (m.document->>'received_at')::timestamptz < ((to_date(p_args->>'week','IYYY-"W"IW')-1)::timestamp AT TIME ZONE 'Asia/Seoul')) AS candidate_ready,
      complete AND NOT EXISTS(SELECT 1 FROM filtered WHERE NOT jd_sent_verified AND NOT contact_scope_complete)
      AND NOT EXISTS(SELECT 1 FROM admin_ai_search_review_queue WHERE document->>'status'='OPEN'
        AND document->>'reason' IN ('unlinked_sent_contact','contact_report_binding_pending')) AS jd_ready,
      complete AND threshold IS NOT NULL
      AND NOT EXISTS(SELECT 1 FROM filtered WHERE evaluation->>'score_status'<>'PASS' OR
        ((evaluation->>'score')::integer>=threshold AND NOT confirmed_uncontacted AND NOT EXISTS(
          SELECT 1 FROM jsonb_array_elements(contacts) c WHERE c->>'status' IN ('CONTACTED','REPLIED'))))
      AND NOT EXISTS(SELECT 1 FROM admin_ai_search_review_queue WHERE document->>'status'='OPEN'
        AND document->>'reason' IN ('unlinked_sent_contact','contact_report_binding_pending')) AS high_ready
  ), selected AS (
    SELECT * FROM filtered WHERE p_action='weekly' OR (confirmed_uncontacted AND evaluation->>'score_status'='PASS'
      AND (evaluation->>'score')::integer>=threshold)
  ), page AS (
    SELECT * FROM selected ORDER BY
      CASE WHEN p_args->>'sort'='score' THEN (evaluation->>'score')::integer END DESC NULLS LAST,
      company,position,candidate_id LIMIT limit_n OFFSET offset_n
  )
  SELECT jsonb_build_object('rows',(SELECT COALESCE(jsonb_agg(to_jsonb(page)),'[]') FROM page),
    'total',(SELECT count(*) FROM selected),'complete',complete,'week',p_args->>'week',
    'summary',jsonb_build_object(
      'batches',CASE WHEN complete THEN (SELECT count(DISTINCT batch_id) FROM targets WHERE grouping_status='CONFIRMED') END,
      'positions',CASE WHEN complete THEN (SELECT count(DISTINCT position_id) FROM targets WHERE position_status='PASS') END,
      'candidates',CASE WHEN (SELECT candidate_ready FROM readiness) THEN (SELECT count(DISTINCT candidate_id) FROM filtered) END,
      'observed_candidates',(SELECT count(DISTINCT candidate_id) FROM filtered),
      'provisional_batches',(SELECT count(DISTINCT batch_id) FROM targets WHERE grouping_status='PROVISIONAL'),
      'jd_sent',CASE WHEN (SELECT jd_ready FROM readiness) THEN (SELECT count(*) FROM filtered WHERE jd_sent_verified) END,
      'high_score_uncontacted',CASE WHEN (SELECT high_ready FROM readiness)
        THEN (SELECT count(*) FROM filtered WHERE confirmed_uncontacted AND (evaluation->>'score')::integer>=threshold) END,
      'reason',CASE WHEN NOT complete THEN 'collection_or_normalization_incomplete'
        WHEN (SELECT NOT candidate_ready FROM readiness) THEN 'candidate_parsing_or_source_review_incomplete'
        WHEN (SELECT NOT jd_ready OR NOT high_ready FROM readiness) THEN 'contact_or_score_verification_incomplete' ELSE NULL END))
    INTO result;
  RETURN result;
END $$;

-- Only the server's existing service role can access this module. Session guards
-- in the host app authorize every page/API request before using that role.
DO $$ DECLARE t text; BEGIN
  FOR t IN SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'admin_ai_search_%' LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',t);
    EXECUTE format('REVOKE ALL ON public.%I FROM anon,authenticated',t);
    EXECUTE format('GRANT SELECT,INSERT,UPDATE ON public.%I TO service_role',t);
  END LOOP;
END $$;
REVOKE ALL ON public.admin_ai_search_weekly_rows FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.admin_ai_search_weekly_rows TO service_role;
REVOKE ALL ON public.admin_ai_search_active_evaluations FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.admin_ai_search_active_evaluations TO service_role;
REVOKE ALL ON public.admin_ai_search_active_batch_sources FROM PUBLIC,anon,authenticated;
GRANT SELECT ON public.admin_ai_search_active_batch_sources TO service_role;
REVOKE ALL ON FUNCTION public.admin_ai_search_register_batch(jsonb) FROM PUBLIC,anon,authenticated;
REVOKE ALL ON FUNCTION public.admin_ai_search_read(text,jsonb) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.admin_ai_search_register_batch(jsonb) TO service_role;
GRANT EXECUTE ON FUNCTION public.admin_ai_search_read(text,jsonb) TO service_role;
