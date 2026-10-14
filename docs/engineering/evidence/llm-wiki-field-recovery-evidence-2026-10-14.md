# LLM 위키 필드 실사 증거 — 2026-10-14 (읽기 전용, 개인정보 값 없음)

## A. Supabase 테이블 건수·컬럼 수 (11:42:49, PostgREST OpenAPI + HEAD count=exact, 222 객체)
  887578 v_position_similar_companies (11c)
  287477 company_financials (25c)
  247935 career_discovery_log (8c)
  149100 positions (10c)
  131757 v_position_corp_match (5c)
  128179 industry_micro_segment_evidence (15c)
  127993 industry_micro_segment_members (20c)
  113695 industry_micro_segments (19c)
   78970 company_similarity_edges (6c)
   69683 company_financials_multi (10c)
   64905 company_disclosures (8c)
   51739 org_members (25c)
   39189 company_business_terms (10c)
   36985 company_job_postings (17c)
   35504 gmail_messages (19c)
   34036 unified_candidate_history_view (8c)
   29352 career_failures (8c)
   24713 gmail_resume_attachments (23c)
   23677 company_business_term_evidence (6c)
   23439 career_company_edges (16c)
   21791 gmail_derived_events (19c)
   21771 pipeline_candidates (41c)
   21771 pipeline_candidates_active (37c)
   21651 profile_archives (18c)
   19953 career_jobs (24c)
   19694 company_source_documents (15c)
   18785 career_targets (18c)
   13250 resume_position_matches (20c)
   11658 clickup_comments (17c)
   11361 company_source_chunks (10c)
   10895 jobmarket_positions (23c)
    9308 company_workforce (19c)
    8006 xbrl_taxonomy (9c)
    7772 position_details (7c)
    7484 company_identity_links (28c)
    7387 position_embeddings (3c)
    6203 companies (15c)
    6203 v_company_similarity_summary (9c)
    6169 company_weekly (19c)
    5195 industry_company_source_profiles (16c)
    5008 customer_ontology_sources (19c)
    4573 position_batch_steps (12c)
    3959 company_clusters (7c)
    3959 company_embeddings (6c)
    3396 company_material_events (6c)
    2930 company_business_sections (8c)
    2900 company_products (8c)
    2318 career_company_segments (12c)
    1514 company_news (16c)
    1464 pipeline_position_cards (21c)
    1436 sourcing_results (24c)
    1263 org_talent_flow (10c)
    1263 v_org_talent_network (6c)
    1142 pipeline_candidates_archive (37c)
    1044 ingest_failures (8c)
     959 company_business_narrative_raw (8c)
     949 gmail_reconciliation_ledger (19c)
     906 notion_client_sub_pages (18c)
     724 gmail_threads (21c)
     703 candidate_outcomes (14c)
     598 search_jobs (11c)
     528 org_company_mapping (19c)
     501 customer_ontology_documents (15c)
     487 ti_talent_flow_detail (10c)
     464 page_snapshots (10c)
     308 candidates (19c)
     281 customer_ontology_clients (20c)
     270 job_match_results (12c)
     269 notion_clients (14c)
     259 career_runs (8c)
     256 weekly_meetings (11c)
     247 ontology_companies (18c)
     233 ingest_runs (8c)
     225 company_product_segments (14c)
     220 ontology_meetings (13c)
     158 notion_coffeechats (13c)
     153 vcx_recommendations (10c)
     140 position_offer_bodies (6c)
     139 company_executives (16c)
     138 position_batch_runs (8c)
     127 b2b_v2_audit_logs (8c)
     121 client_companies (28c)
     104 ti_company_mapping (12c)
     103 company_top_shareholders (13c)
     102 company_dividends (10c)
     100 jobmarket_company_aggregates (8c)
     100 weekly_growth_snapshots (8c)
      98 market_intel (12c)
      81 outstanding_articles (11c)
      76 gmail_sync_state (11c)
      76 jobs (15c)
      68 company_treasury_stock (13c)
      66 company_financial_indicators (11c)
      64 v_org_talent_density (8c)
      63 v_cluster_position_density (5c)
      57 commission_payouts (15c)
      56 pipeline_stage_history (6c)
      55 weekly_snapshot (13c)
      53 user_profiles (25c)
      50 company_linkedin (4c)
      47 client_ontology (20c)
      40 consultant_weekly_goals (8c)
      36 ti_overview (24c)
      35 ti_talent_flow_summary (15c)
      34 priority_positions (12c)
      33 org_role_salary_stats (7c)
      33 resumes (13c)
      32 company_exec_compensation_by_type (10c)
      30 company_total_shares (11c)
      28 sourcing_runs (6c)
      24 company_audit_contracts (12c)
      24 company_audit_opinions (11c)
      23 revenue_invoices (30c)
      22 company_top_shareholder_changes (11c)
      22 vcx_members (23c)
      18 b2b_v2_terms_acceptances (7c)
      18 weekly_growth_metrics (6c)
      17 resume_profiles (19c)
      15 company_exec_compensation_approved (11c)
      15 resume_optimizations (16c)
      15 resume_uploads (29c)
      14 b2c_intake_terms_acceptances (9c)
      14 company_debt_issuance (12c)
      14 jobmarket_snapshots (8c)
      13 ontology_meta (7c)
      13 supply_snapshot (19c)
      12 company_capital_changes (11c)
      12 newsletters (15c)
      12 v_latest_positions (8c)
      10 owner_consultants (14c)
       9 company_exec_compensation_individual (9c)
       9 company_top5_compensation (9c)
       9 pipeline_boards (10c)
       9 weekly_growth_nudges (10c)
       8 company_commercial_paper_balance (14c)
       8 company_contingent_capital_balance (14c)
       8 company_corporate_bond_balance (14c)
       8 company_exec_compensation_all (10c)
       8 company_minority_shareholders (12c)
       8 company_new_capital_balance (14c)
       8 company_non_audit_services (9c)
       8 company_outside_directors (9c)
       8 company_private_offering_use (15c)
       8 company_public_offering_use (15c)
       8 company_research (3c)
       8 company_short_term_bond_balance (14c)
       8 company_unregistered_exec_comp (10c)
       7 career_periods (5c)
       7 pipeline_candidate_resume_quarantine (6c)
       6 client_billing_statements (21c)
       6 vcx_corporate_users (9c)
       5 org_collection_log (12c)
       5 recruitment_fee_agreements (14c)
       4 clickup_sync_state (11c)
       3 machine_heartbeats (6c)
       3 ontology_positions (9c)
       2 app_kv (3c)
       2 invite_tokens (13c)
       2 invite_tokens_public (6c)
       2 jd_analyses (6c)
       2 member_loans (12c)
       2 organization_analysis (10c)
       2 resume_share_links (9c)
       2 resume_view_consents (11c)
       2 similarity_runs (10c)
       2 v_company_dashboard (14c)
       2 weekly_meeting_note_entries (7c)
       1 alembic_version (1c)
       1 b2c_users (5c)
       1 daily_health_metrics (10c)
       1 discord_gateway_leases (13c)
       1 gmail_ingestion_runs (13c)
       1 industry_micro_segment_runs (8c)
       1 invoice_settlement_details (14c)
       1 notion_golden_captures (11c)
       1 ontology_version (4c)
       1 vcx_invites (11c)
       1 weekly_meeting_notes (5c)
       1 workspaces (6c)
       0 account_locks (4c)
       0 admin_client_notes (7c)
       0 b2c_1chon_pool (11c)
       0 b2c_invite_campaign (36c)
       0 b2c_invite_feedback (16c)
       0 b2c_user_profiles (9c)
       0 billing_history (12c)
       0 candidate_activity_log (8c)
       0 candidate_market_profiles (9c)
       0 candidate_match_feedback (10c)
       0 candidate_mentions (7c)
       0 candidate_messages (14c)
       0 card_registrations (11c)
       0 company_business_narrative (12c)
       0 company_goals (9c)
       0 consultant_weekly_metrics (12c)
       0 consultants (6c)
       0 daily_briefs (9c)
       0 dart_career_discovery_runs (15c)
       0 discord_gateway_killswitches (5c)
       0 error_logs (13c)
       0 evaluation_notes (6c)
       0 expenses (13c)
       0 gmail_candidate_feedback (16c)
       0 gmail_position_requests (17c)
       0 inmail_records (13c)
       0 interview_position_libraries (19c)
       0 interview_prep_jobs (14c)
       0 interview_prep_sessions (13c)
       0 job_match_subscriptions (15c)
       0 ledger_closings (10c)
       0 monitors (11c)
       0 organization_members (5c)
       0 organizations (10c)
       0 owner_capital_ledger (10c)
       0 pipeline_comments (7c)
       0 pipeline_members (6c)
       0 ti_collection_log (12c)
       0 user_discord_mapping (4c)
       0 v_market_index (12c)
       0 v_mlai_positions (6c)
       0 vcx_ceo_coffee_sessions (14c)
       0 vcx_coffee_applications (7c)

## B. 핵심 필드 빈 값 비율 (11:44:13)

## pipeline_candidates total=21771
  email                            null=  21097  filled=3.1%
  match_score                      null=      4  filled=100.0%
  ai_assessment                    null=   4887  filled=77.6%
  resume_data                      null=  13347  filled=38.7%
  clickup_task_id                  null=  17584  filled=19.2%
  client_company                   null=   4913  filled=77.4%
  jd_id                            null=  16125  filled=25.9%
  embedding                        null=  21771  filled=0.0%
  source                           null=      0  filled=100.0%

## profile_archives total=21651
  structured_json                  null=  21137  filled=2.4%
  career_companies_json            null=      0  filled=100.0%
  ocr_text                         null=  20775  filled=4.0%
  run_id                           null=  20217  filled=6.6%
  local_id                         null=    481  filled=97.8%

## sourcing_results total=1436
  education_periods                null=      0  filled=100.0%
  career_periods                   null=      0  filled=100.0%
  fit_reason                       null=    191  filled=86.7%
  evidence_urls                    null=      0  filled=100.0%
  match_score                      null=      0  filled=100.0%
  resume_data                      null=     96  filled=93.3%

## gmail_derived_events total=21791
  candidate_id                     null=  21791  filled=0.0%
  position_id                      null=  21791  filled=0.0%
  company_id                       null=  21791  filled=0.0%
  occurred_at                      null=      0  filled=100.0%

## candidates total=308
  profile_id                       null=      5  filled=98.4%
  profile_url                      null=      0  filled=100.0%
  score                            null=    289  filled=6.2%
  proposal_sent_at                 null=    308  filled=0.0%
  discord_sent_at                  null=    299  filled=2.9%
  search_job_id                    null=     19  filled=93.8%

## candidate_outcomes total=703
  clickup_task_id                  null=      0  filled=100.0%
  outcome                          null=      0  filled=100.0%
  scraped_profile_path             null=    700  filled=0.4%

## C. 로컬 SQLite (sqlite3 -readonly)
archive.db archives: 20,862행 / distinct url 16,707 / 중복 URL 2,889 / structured_json 채움 13,633 / sync_status synced 20,862
archive.db 사이트별(건수, 구조화, 점수, OCR): linkedin_recruiter 17,295/10,354/0/244; saramin_hiring 1,358/1,273/6/312; saramin 752/640/0/7; linkedin 434/417/3/92; jobkorea_corp 423/406/6/100; linkedin_recruiter_search 373/364/1/21; other 131/119/0/22; jobkorea 93/59/0/17; outstanding 3/1/0/0
~/.valuehire/profile_archives.sqlite3 profile_archive_receipts: 702행 (2026-08-05 정지)
gmail-resume-clickup-match.sqlite: attachments_stage 844 / matches_stage 1,601
customer-ontology.db: 일반 열기 실패(오류 14) → immutable=1 로 테이블 2개 확인(customer_ontology_clients_stage, customer_ontology_sources_stage)

## D. 로컬↔운영 교차 표본 (11:48)
로컬 linkedin_recruiter structured_json 최신 30건 → 운영 profile_archives 30건 존재, structured_json 채움 0/30, career_companies_json 비어있지 않음 30/30

## E. anon 키 건수 조회 (11:48:35, HEAD, 값 미조회)
profile_archives 206 */21651 | gmail_messages 206 */35504 | pipeline_candidates 200 */0 | pipeline_candidates_active 206 */21771 | sourcing_results 200 */0 | profile_archives?structured_json=not.is.null → 200 0-513/514

## F. dry-run (11:53:48~11:54:02, 쓰기 0건, 장부 미생성)
{"mode": "dry-run", "local_rows": 13633, "remote_rows_found": 13633, "to_fill": 13600, "skipped_absent": 0, "skipped_filled": 33, "skipped_invalid": 0, "written": 0, "unmatched": 0}

## G. field_audit.py 실측 (11:55:46, VERDICT PASS = 퇴행 하한 기준)
gmail_derived_events.candidate_id total=21791 null=21791 filled=0.0%
pipeline_candidates.ai_assessment total=21771 null=4887 filled=77.6%
pipeline_candidates.email total=21771 null=21097 filled=3.1%
pipeline_candidates.resume_data total=21771 null=13347 filled=38.7%
profile_archives.structured_json total=21651 null=21137 filled=2.4%
sourcing_results.fit_reason total=1436 null=191 filled=86.7%
{"VERDICT": "PASS", "failures": []}

## H. 인수 검사 (11:55:45) bash scripts/acceptance-llm-wiki-fields.sh
UNIT: PASS ran=14 / UNIT_COUNT: PASS ran=14 / MUTATION[is_null_guard]: PASS / MUTATION[zero_total_pass]: PASS / SOT_THRESHOLDS: PASS / VERDICT: PASS rc=0
