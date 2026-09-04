-- Make fee selection, business constants, and Gmail delivery proof database-enforced.
create extension if not exists btree_gist;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'recruitment_fee_agreements_active_window_excl'
      and conrelid = 'recruitment_fee_agreements'::regclass
  ) then
    alter table recruitment_fee_agreements
      add constraint recruitment_fee_agreements_active_window_excl
      exclude using gist (
        tenant_id with =,
        client_key with =,
        position_key with =,
        daterange(effective_from, effective_to, '[]') with &&
      ) where (status = 'active');
  end if;
end;
$$;

create table if not exists invoice_business_contract_versions (
  version text primary key,
  sha256 text not null unique check (sha256 ~ '^[0-9a-f]{64}$'),
  config jsonb not null,
  active boolean not null default false,
  created_at timestamptz not null default now()
);

create unique index if not exists invoice_business_contract_one_active
  on invoice_business_contract_versions (active) where active;

do $$
declare
  target_version constant text := 'invoice-business-2026-09-02.1';
  target_sha constant text :=
    '1728e9ae0dca3d619f0b6e65f0b8a3842b95b99752770176d27dccc0fe34094e';
  target_config constant jsonb := jsonb_build_object(
    'tenant_id', 'valueconnect',
    'issuer_name', '밸류커넥트 주식회사',
    'due_offset_days', 14,
    'tax_policy', 'NOT_APPLICABLE',
    'company_share_percent', 25,
    'withholding_percent', 3.3,
    'allocation_total_percent', 100,
    'bank_name', '하나은행',
    'account_number_display', '588-910030-71604',
    'account_holder', '밸류커넥트 주식회사',
    'default_recipient', 'sangmokang@valueconnect.kr'
  );
  current_row invoice_business_contract_versions%rowtype;
begin
  select * into current_row
  from invoice_business_contract_versions where version = target_version;
  if found and (
    current_row.sha256 <> target_sha or current_row.config <> target_config
  ) then
    raise exception 'CONTRACT_ERROR: version % has different content', target_version;
  end if;
  if not found then
    insert into invoice_business_contract_versions(version, sha256, config, active)
    values (target_version, target_sha, target_config, false);
  end if;
  update invoice_business_contract_versions set active = false where active;
  update invoice_business_contract_versions set active = true
    where version = target_version;
end;
$$;

alter table invoice_business_contract_versions enable row level security;
drop policy if exists invoice_business_contract_service_role
  on invoice_business_contract_versions;
create policy invoice_business_contract_service_role
  on invoice_business_contract_versions for all to service_role
  using (true) with check (true);
drop policy if exists invoice_business_contract_owner
  on invoice_business_contract_versions;
create policy invoice_business_contract_owner
  on invoice_business_contract_versions for select to authenticated
  using ((auth.jwt() ->> 'email') = 'sangmokang@valueconnect.kr');

alter table revenue_invoices
  add column if not exists contract_version text,
  add column if not exists contract_sha256 text;

alter table client_billing_statements
  add column if not exists contract_version text,
  add column if not exists contract_sha256 text,
  add column if not exists delivery_recipient text;

create table if not exists invoice_delivery_receipts (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null default 'valueconnect',
  statement_id uuid not null unique
    references client_billing_statements(id) on delete cascade,
  document_number text not null,
  recipient text not null,
  subject text not null,
  gmail_message_id text not null unique,
  sent_at timestamptz not null,
  attachment_sha256 text not null check (attachment_sha256 ~ '^[0-9a-f]{64}$'),
  payload_sha256 text not null check (payload_sha256 ~ '^[0-9a-f]{64}$'),
  contract_version text not null,
  contract_sha256 text not null,
  readback_confirmed boolean not null check (readback_confirmed),
  created_at timestamptz not null default now(),
  constraint invoice_delivery_receipts_document_uniq
    unique (tenant_id, document_number)
);

alter table invoice_delivery_receipts enable row level security;
drop policy if exists invoice_delivery_receipts_service_role
  on invoice_delivery_receipts;
create policy invoice_delivery_receipts_service_role
  on invoice_delivery_receipts for all to service_role
  using (true) with check (true);
drop policy if exists invoice_delivery_receipts_owner
  on invoice_delivery_receipts;
create policy invoice_delivery_receipts_owner
  on invoice_delivery_receipts for select to authenticated
  using ((auth.jwt() ->> 'email') = 'sangmokang@valueconnect.kr');

create or replace function store_invoice_placement_set(p_payload jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  invoice_data jsonb := p_payload -> 'invoice';
  settlement_data jsonb := p_payload -> 'settlement';
  contract_row invoice_business_contract_versions%rowtype;
  agreement recruitment_fee_agreements%rowtype;
  agreement_id uuid;
  existing_invoice revenue_invoices%rowtype;
  invoice_id uuid;
  placement_id uuid := gen_random_uuid();
  tenant text := coalesce(nullif(p_payload ->> 'tenant_id', ''), 'valueconnect');
  fee_matches integer;
  salary bigint;
  fee_percent numeric;
  invoice_amount bigint;
  expected_amount bigint;
  start_on date;
  due_on date;
  payload_hash text := p_payload ->> 'payload_sha256';
  canonical_payload text := p_payload ->> 'payload_canonical';
  am_percent numeric;
  coworker_percent numeric;
  company_percent numeric;
  withholding_rate numeric;
  am_gross bigint;
  coworker_gross bigint;
  company_gross bigint;
  am_tax bigint;
  coworker_tax bigint;
  am_rps bigint := 0;
  coworker_rps bigint := 0;
  company_rps bigint := 0;
  rps_amount bigint;
  rps_bearer text;
begin
  select * into contract_row
  from invoice_business_contract_versions
  where version = p_payload ->> 'contract_version'
    and sha256 = p_payload ->> 'contract_sha256';
  if not found then
    raise exception 'CONTRACT_ERROR: business contract snapshot is missing';
  end if;
  if p_payload ->> 'fee_source' <> 'SUPABASE' then
    raise exception 'CONTRACT_ERROR: final documents require SUPABASE fee authority';
  end if;
  if tenant <> contract_row.config ->> 'tenant_id' then
    raise exception 'CONTRACT_ERROR: tenant mismatch';
  end if;
  if invoice_data is null or jsonb_typeof(invoice_data) <> 'object' then
    raise exception 'CONTRACT_ERROR: invoice object is required';
  end if;
  if payload_hash is null or payload_hash !~ '^[0-9a-f]{64}$'
    or canonical_payload is null
    or canonical_payload::jsonb <>
      (p_payload - 'payload_sha256' - 'payload_canonical')
    or encode(digest(convert_to(canonical_payload, 'UTF8'), 'sha256'), 'hex') <>
      payload_hash then
    raise exception 'CONTRACT_ERROR: payload integrity proof is invalid';
  end if;

  salary := (invoice_data ->> 'annual_salary_krw')::bigint;
  fee_percent := (invoice_data ->> 'fee_percent')::numeric;
  invoice_amount := (invoice_data ->> 'invoice_amount_krw')::bigint;
  start_on := (invoice_data ->> 'start_date')::date;
  due_on := (invoice_data ->> 'due_date')::date;
  company_percent := (contract_row.config ->> 'company_share_percent')::numeric;
  withholding_rate :=
    (contract_row.config ->> 'withholding_percent')::numeric / 100;
  expected_amount := round(salary * fee_percent / 100)::bigint;
  if salary <= 0 or fee_percent <= 0 or fee_percent > 100
    or invoice_amount <> expected_amount
    or due_on <> start_on + (contract_row.config ->> 'due_offset_days')::integer
    or contract_row.config ->> 'tax_policy' <> 'NOT_APPLICABLE' then
    raise exception 'CONTRACT_ERROR: invoice calculation mismatch';
  end if;

  select count(*), (array_agg(candidate.id))[1]
    into fee_matches, agreement_id
  from recruitment_fee_agreements candidate
  where candidate.tenant_id = tenant
    and candidate.client_key = normalize_invoice_key(invoice_data ->> 'company_name')
    and candidate.position_key = normalize_invoice_key(invoice_data ->> 'position')
    and candidate.status = 'active'
    and candidate.effective_from <= start_on
    and (candidate.effective_to is null or candidate.effective_to >= start_on);
  if fee_matches = 0 then
    raise exception 'FEE_AGREEMENT_NOT_FOUND';
  elsif fee_matches > 1 then
    raise exception 'FEE_AGREEMENT_CONFLICT';
  end if;
  select * into strict agreement
  from recruitment_fee_agreements where id = agreement_id;
  if agreement.agreement_ref <> invoice_data ->> 'fee_agreement_ref'
    or agreement.fee_rate <> fee_percent / 100 then
    raise exception 'FEE_AGREEMENT_MISMATCH';
  end if;

  select * into existing_invoice
  from revenue_invoices
  where tenant_id = tenant
    and document_number = invoice_data ->> 'invoice_number';
  if found then
    if existing_invoice.payload_sha256 = payload_hash
      and existing_invoice.contract_version = contract_row.version
      and existing_invoice.contract_sha256 = contract_row.sha256 then
      return jsonb_build_object(
        'status', 'idempotent',
        'invoice_id', existing_invoice.id,
        'placement_set_id', existing_invoice.placement_set_id,
        'fee_agreement_id', existing_invoice.fee_agreement_id,
        'tenant_id', tenant,
        'document_number', invoice_data ->> 'invoice_number',
        'fee_agreement_ref', invoice_data ->> 'fee_agreement_ref',
        'invoice_pdf_sha256', invoice_data ->> 'pdf_sha256',
        'settlement_number', settlement_data ->> 'settlement_number',
        'settlement_pdf_sha256', settlement_data ->> 'pdf_sha256',
        'contract_version', contract_row.version,
        'contract_sha256', contract_row.sha256,
        'payload_sha256', payload_hash
      );
    end if;
    raise exception 'IDEMPOTENCY_CONFLICT';
  end if;

  if settlement_data is not null and jsonb_typeof(settlement_data) <> 'null' then
    if settlement_data ->> 'invoice_number' <> invoice_data ->> 'invoice_number'
      or settlement_data ->> 'company_name' <> invoice_data ->> 'company_name'
      or settlement_data ->> 'candidate_name' <> invoice_data ->> 'candidate_name'
      or settlement_data ->> 'start_date' <> invoice_data ->> 'start_date'
      or settlement_data ->> 'position' <> invoice_data ->> 'position'
      or (settlement_data ->> 'annual_salary_krw')::bigint <> salary
      or (settlement_data ->> 'fee_percent')::numeric <> fee_percent
      or settlement_data ->> 'fee_agreement_ref' <> agreement.agreement_ref
      or (settlement_data ->> 'invoice_amount_krw')::bigint <> invoice_amount then
      raise exception 'DOCUMENT_PAIR_MISMATCH';
    end if;
  end if;

  insert into revenue_invoices (
    tenant_id, write_date, issue_date, client_name, item_name, supply_amount,
    vat_amount, invoice_type, candidate_name, candidate_salary, commission_rate,
    status, source, document_number, position_name, start_date, due_date,
    fee_agreement_id, placement_set_id, invoice_pdf_sha256, payload_sha256,
    contract_version, contract_sha256
  ) values (
    tenant, (invoice_data ->> 'issue_date')::date,
    (invoice_data ->> 'issue_date')::date, invoice_data ->> 'company_name',
    invoice_data ->> 'position', invoice_amount, 0, '일반',
    invoice_data ->> 'candidate_name', salary, fee_percent / 100,
    case when (invoice_data ->> 'draft')::boolean then 'draft' else 'issued' end,
    'manual', invoice_data ->> 'invoice_number', invoice_data ->> 'position',
    start_on, due_on, agreement.id, placement_id,
    invoice_data ->> 'pdf_sha256', payload_hash,
    contract_row.version, contract_row.sha256
  ) returning id into invoice_id;

  insert into client_billing_statements (
    tenant_id, statement_no, recipient_name, issue_date, due_date, title,
    service_label, line_items, total_amount, bank_info, issuer_name,
    linked_invoice_id, status, placement_set_id, pdf_sha256, payload_sha256
    , contract_version, contract_sha256, delivery_recipient
  ) values (
    tenant, invoice_data ->> 'invoice_number', invoice_data ->> 'company_name',
    (invoice_data ->> 'issue_date')::date, due_on,
    '채용 수수료 청구서', 'Recruitment Fee',
    jsonb_build_array(jsonb_build_object(
      'candidate_name', invoice_data ->> 'candidate_name',
      'position', invoice_data ->> 'position',
      'salary', salary, 'rate_percent', fee_percent,
      'fee_agreement_ref', agreement.agreement_ref, 'amount', invoice_amount
    )), invoice_amount,
    jsonb_build_object(
      'bank', contract_row.config ->> 'bank_name',
      'account', contract_row.config ->> 'account_number_display',
      'holder', contract_row.config ->> 'account_holder'
    ), contract_row.config ->> 'issuer_name', invoice_id,
    'draft', placement_id, invoice_data ->> 'pdf_sha256', payload_hash,
    contract_row.version, contract_row.sha256,
    contract_row.config ->> 'default_recipient'
  );

  if settlement_data is not null and jsonb_typeof(settlement_data) <> 'null' then
    am_percent := (settlement_data ->> 'account_manager_percent')::numeric;
    coworker_percent := (settlement_data ->> 'coworker_percent')::numeric;
    if am_percent + coworker_percent + company_percent <>
      (contract_row.config ->> 'allocation_total_percent')::numeric then
      raise exception 'CONTRACT_ERROR: allocation percentages must total configured value';
    end if;
    company_gross := round(invoice_amount * company_percent / 100)::bigint;
    am_gross := round(invoice_amount * am_percent / 100)::bigint;
    coworker_gross := invoice_amount - company_gross - am_gross;
    am_tax := round(am_gross * withholding_rate)::bigint;
    coworker_tax := round(coworker_gross * withholding_rate)::bigint;
    rps_amount := settlement_data ->> 'rps_advance_krw';
    rps_bearer := settlement_data ->> 'rps_bearer';
    if coalesce(rps_amount, 0) > 0 then
      if rps_bearer = 'account_manager' then am_rps := rps_amount;
      elsif rps_bearer = 'coworker' then coworker_rps := rps_amount;
      elsif rps_bearer = 'company' then company_rps := rps_amount;
      elsif rps_bearer = 'pro_rata' then
        am_rps := round(rps_amount * am_percent /
          (am_percent + coworker_percent))::bigint;
        coworker_rps := rps_amount - am_rps;
      else
        raise exception 'CONTRACT_ERROR: RPS bearer is invalid';
      end if;
    end if;
    if least(
      am_gross - am_tax - am_rps,
      coworker_gross - coworker_tax - coworker_rps,
      company_gross - company_rps
    ) < 0 then
      raise exception 'CONTRACT_ERROR: RPS deduction exceeds allocation';
    end if;

    insert into commission_payouts (
      tenant_id, invoice_id, payee_role, payee_name, split_rate,
      gross_amount, withholding_rate, withholding_amount, net_amount, status
    ) values
      (tenant, invoice_id, 'project_owner', settlement_data ->> 'account_manager_name',
       am_percent / 100, am_gross, withholding_rate, am_tax,
       am_gross - am_tax - am_rps, 'pending'),
      (tenant, invoice_id, 'coworker', settlement_data ->> 'coworker_name',
       coworker_percent / 100, coworker_gross, withholding_rate, coworker_tax,
       coworker_gross - coworker_tax - coworker_rps, 'pending'),
      (tenant, invoice_id, 'company', contract_row.config ->> 'issuer_name',
       company_percent / 100, company_gross, 0, 0,
       company_gross - company_rps, 'pending');

    insert into invoice_settlement_details (
      tenant_id, invoice_id, settlement_number, placement_set_id,
      guarantee_months, rps_status, rps_advance_krw, rps_bearer,
      settlement_pdf_sha256, payload_sha256, source_payload
    ) values (
      tenant, invoice_id, settlement_data ->> 'settlement_number', placement_id,
      (settlement_data ->> 'guarantee_months')::integer,
      settlement_data ->> 'rps_status',
      (settlement_data ->> 'rps_advance_krw')::bigint,
      nullif(settlement_data ->> 'rps_bearer', ''),
      settlement_data ->> 'pdf_sha256', payload_hash, settlement_data
    );
  end if;

  return jsonb_build_object(
    'status', 'stored', 'invoice_id', invoice_id,
    'placement_set_id', placement_id, 'fee_agreement_id', agreement.id,
    'tenant_id', tenant,
    'document_number', invoice_data ->> 'invoice_number',
    'fee_agreement_ref', agreement.agreement_ref,
    'invoice_pdf_sha256', invoice_data ->> 'pdf_sha256',
    'settlement_number', settlement_data ->> 'settlement_number',
    'settlement_pdf_sha256', settlement_data ->> 'pdf_sha256',
    'contract_version', contract_row.version,
    'contract_sha256', contract_row.sha256,
    'payload_sha256', payload_hash
  );
end;
$$;

revoke all on function store_invoice_placement_set(jsonb) from public;
grant execute on function store_invoice_placement_set(jsonb) to service_role;

create or replace function record_invoice_delivery(p_payload jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  contract_row invoice_business_contract_versions%rowtype;
  statement_row client_billing_statements%rowtype;
  receipt_row invoice_delivery_receipts%rowtype;
  tenant text := coalesce(nullif(p_payload ->> 'tenant_id', ''), 'valueconnect');
  document_no text := p_payload ->> 'document_number';
  payload_hash text := p_payload ->> 'payload_sha256';
  canonical_payload text := p_payload ->> 'payload_canonical';
  receipt_id uuid;
begin
  select * into contract_row
  from invoice_business_contract_versions
  where version = p_payload ->> 'contract_version'
    and sha256 = p_payload ->> 'contract_sha256';
  if not found
    then
    raise exception 'CONTRACT_ERROR: delivery business contract mismatch';
  end if;
  if payload_hash is null or payload_hash !~ '^[0-9a-f]{64}$'
    or canonical_payload is null
    or canonical_payload::jsonb <>
      (p_payload - 'payload_sha256' - 'payload_canonical')
    or encode(digest(convert_to(canonical_payload, 'UTF8'), 'sha256'), 'hex') <>
      payload_hash then
    raise exception 'CONTRACT_ERROR: delivery payload integrity proof is invalid';
  end if;
  if tenant <> contract_row.config ->> 'tenant_id'
    or coalesce(p_payload ->> 'subject', '') = ''
    or coalesce(p_payload ->> 'gmail_message_id', '') = ''
    or coalesce((p_payload ->> 'readback_confirmed')::boolean, false) is not true
    or p_payload ->> 'attachment_sha256' !~ '^[0-9a-f]{64}$' then
    raise exception 'CONTRACT_ERROR: delivery proof is invalid';
  end if;

  select * into statement_row
  from client_billing_statements
  where tenant_id = tenant and statement_no = document_no;
  if not found then
    raise exception 'DELIVERY_DOCUMENT_NOT_FOUND';
  end if;
  if statement_row.pdf_sha256 <> p_payload ->> 'attachment_sha256' then
    raise exception 'DELIVERY_ATTACHMENT_MISMATCH';
  end if;
  if statement_row.contract_version <> contract_row.version
    or statement_row.contract_sha256 <> contract_row.sha256
    or statement_row.delivery_recipient <> p_payload ->> 'recipient' then
    raise exception 'CONTRACT_ERROR: delivery does not match document contract';
  end if;

  select * into receipt_row
  from invoice_delivery_receipts where statement_id = statement_row.id;
  if found then
    if receipt_row.recipient = p_payload ->> 'recipient'
      and receipt_row.subject = p_payload ->> 'subject'
      and receipt_row.gmail_message_id = p_payload ->> 'gmail_message_id'
      and receipt_row.sent_at = (p_payload ->> 'sent_at')::timestamptz
      and receipt_row.attachment_sha256 = p_payload ->> 'attachment_sha256'
      and receipt_row.contract_version = contract_row.version
      and receipt_row.contract_sha256 = contract_row.sha256
      and receipt_row.payload_sha256 = payload_hash then
      return jsonb_build_object(
        'status', 'idempotent', 'statement_id', statement_row.id,
        'delivery_receipt_id', receipt_row.id,
        'tenant_id', tenant, 'document_number', document_no,
        'recipient', receipt_row.recipient, 'subject', receipt_row.subject,
        'gmail_message_id', receipt_row.gmail_message_id,
        'sent_at', receipt_row.sent_at,
        'attachment_sha256', receipt_row.attachment_sha256,
        'contract_version', receipt_row.contract_version,
        'contract_sha256', receipt_row.contract_sha256,
        'payload_sha256', receipt_row.payload_sha256
      );
    end if;
    raise exception 'IDEMPOTENCY_CONFLICT';
  end if;

  insert into invoice_delivery_receipts (
    tenant_id, statement_id, document_number, recipient, subject,
    gmail_message_id, sent_at, attachment_sha256, payload_sha256,
    contract_version, contract_sha256, readback_confirmed
  ) values (
    tenant, statement_row.id, document_no, p_payload ->> 'recipient',
    p_payload ->> 'subject', p_payload ->> 'gmail_message_id',
    (p_payload ->> 'sent_at')::timestamptz,
    p_payload ->> 'attachment_sha256', payload_hash,
    contract_row.version, contract_row.sha256, true
  ) returning id into receipt_id;

  update client_billing_statements set status = 'sent'
  where id = statement_row.id;
  return jsonb_build_object(
    'status', 'stored', 'statement_id', statement_row.id,
    'delivery_receipt_id', receipt_id,
    'tenant_id', tenant, 'document_number', document_no,
    'recipient', p_payload ->> 'recipient',
    'subject', p_payload ->> 'subject',
    'gmail_message_id', p_payload ->> 'gmail_message_id',
    'sent_at', (p_payload ->> 'sent_at')::timestamptz,
    'attachment_sha256', p_payload ->> 'attachment_sha256',
    'contract_version', contract_row.version,
    'contract_sha256', contract_row.sha256,
    'payload_sha256', payload_hash
  );
end;
$$;

revoke all on function record_invoice_delivery(jsonb) from public;
grant execute on function record_invoice_delivery(jsonb) to service_role;
