-- Extend the V4 finance ledger for customer+position fee agreements and paired documents.
create extension if not exists pgcrypto;

create or replace function normalize_invoice_key(value text)
returns text
language sql
immutable
strict
as $$
  select lower(regexp_replace(btrim(value), '\s+', ' ', 'g'));
$$;

create table if not exists recruitment_fee_agreements (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null default 'valueconnect',
  agreement_ref text not null,
  client_key text not null,
  client_name text not null,
  position_key text not null,
  position_name text not null,
  fee_rate numeric not null check (fee_rate > 0 and fee_rate <= 1),
  effective_from date not null,
  effective_to date,
  source_reference text not null,
  status text not null default 'active' check (status in ('active', 'inactive')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint recruitment_fee_agreements_ref_uniq unique (tenant_id, agreement_ref),
  constraint recruitment_fee_agreements_window_valid
    check (effective_to is null or effective_to >= effective_from),
  constraint recruitment_fee_agreements_client_key_normalized
    check (client_key = normalize_invoice_key(client_name)),
  constraint recruitment_fee_agreements_position_key_normalized
    check (position_key = normalize_invoice_key(position_name))
);

create index if not exists recruitment_fee_agreements_lookup_idx
  on recruitment_fee_agreements
  (tenant_id, client_key, position_key, effective_from, effective_to)
  where status = 'active';

create or replace function reject_overlapping_fee_agreements()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  if tg_op = 'UPDATE' and row(
    new.tenant_id, new.agreement_ref, new.client_key, new.client_name,
    new.position_key, new.position_name, new.fee_rate,
    new.effective_from, new.effective_to, new.source_reference
  ) is distinct from row(
    old.tenant_id, old.agreement_ref, old.client_key, old.client_name,
    old.position_key, old.position_name, old.fee_rate,
    old.effective_from, old.effective_to, old.source_reference
  ) then
    raise exception 'FEE_AGREEMENT_IMMUTABLE';
  end if;
  if new.status = 'active' and exists (
    select 1
    from recruitment_fee_agreements current_agreement
    where current_agreement.tenant_id = new.tenant_id
      and current_agreement.client_key = new.client_key
      and current_agreement.position_key = new.position_key
      and current_agreement.status = 'active'
      and current_agreement.agreement_ref <> new.agreement_ref
      and current_agreement.id <> new.id
      and daterange(
        current_agreement.effective_from,
        current_agreement.effective_to,
        '[]'
      ) && daterange(new.effective_from, new.effective_to, '[]')
  ) then
    raise exception 'FEE_AGREEMENT_CONFLICT';
  end if;
  return new;
end;
$$;

drop trigger if exists reject_overlapping_fee_agreements_trigger
  on recruitment_fee_agreements;
create trigger reject_overlapping_fee_agreements_trigger
before insert or update on recruitment_fee_agreements
for each row execute function reject_overlapping_fee_agreements();

alter table revenue_invoices
  add column if not exists document_number text,
  add column if not exists position_name text,
  add column if not exists start_date date,
  add column if not exists due_date date,
  add column if not exists fee_agreement_id uuid
    references recruitment_fee_agreements(id) on delete restrict,
  add column if not exists placement_set_id uuid,
  add column if not exists invoice_pdf_sha256 text,
  add column if not exists payload_sha256 text;

create unique index if not exists revenue_invoices_document_number_uniq
  on revenue_invoices (tenant_id, document_number)
  where document_number is not null;

alter table client_billing_statements
  add column if not exists placement_set_id uuid,
  add column if not exists pdf_sha256 text,
  add column if not exists payload_sha256 text;

create table if not exists invoice_settlement_details (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null default 'valueconnect',
  invoice_id uuid not null unique
    references revenue_invoices(id) on delete cascade,
  settlement_number text not null,
  placement_set_id uuid not null,
  guarantee_months integer not null check (guarantee_months between 0 and 60),
  rps_status text not null
    check (rps_status in ('pending', 'none', 'deferred', 'deducted')),
  rps_advance_krw bigint,
  rps_bearer text
    check (rps_bearer in ('account_manager', 'coworker', 'company', 'pro_rata')),
  settlement_pdf_sha256 text not null,
  payload_sha256 text not null,
  source_payload jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint invoice_settlement_details_number_uniq
    unique (tenant_id, settlement_number),
  constraint invoice_settlement_details_rps_shape check (
    (rps_status = 'pending' and rps_advance_krw is null and rps_bearer is null)
    or (rps_status in ('none', 'deferred') and rps_advance_krw = 0 and rps_bearer is null)
    or (rps_status = 'deducted' and rps_advance_krw > 0 and rps_bearer is not null)
  )
);

alter table recruitment_fee_agreements enable row level security;
alter table invoice_settlement_details enable row level security;

drop policy if exists recruitment_fee_agreements_service_role
  on recruitment_fee_agreements;
create policy recruitment_fee_agreements_service_role
  on recruitment_fee_agreements for all to service_role
  using (true) with check (true);
drop policy if exists recruitment_fee_agreements_owner
  on recruitment_fee_agreements;
create policy recruitment_fee_agreements_owner
  on recruitment_fee_agreements for select to authenticated
  using ((auth.jwt() ->> 'email') = 'sangmokang@valueconnect.kr');

drop policy if exists invoice_settlement_details_service_role
  on invoice_settlement_details;
create policy invoice_settlement_details_service_role
  on invoice_settlement_details for all to service_role
  using (true) with check (true);
drop policy if exists invoice_settlement_details_owner
  on invoice_settlement_details;
create policy invoice_settlement_details_owner
  on invoice_settlement_details for select to authenticated
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
  am_percent numeric;
  coworker_percent numeric;
  company_percent numeric := 25;
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
  if invoice_data is null or jsonb_typeof(invoice_data) <> 'object' then
    raise exception 'CONTRACT_ERROR: invoice object is required';
  end if;
  if payload_hash is null or payload_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'CONTRACT_ERROR: payload_sha256 is invalid';
  end if;

  salary := (invoice_data ->> 'annual_salary_krw')::bigint;
  fee_percent := (invoice_data ->> 'fee_percent')::numeric;
  invoice_amount := (invoice_data ->> 'invoice_amount_krw')::bigint;
  start_on := (invoice_data ->> 'start_date')::date;
  due_on := (invoice_data ->> 'due_date')::date;
  expected_amount := round(salary * fee_percent / 100)::bigint;
  if salary <= 0 or fee_percent <= 0 or fee_percent > 100
    or invoice_amount <> expected_amount or due_on <> start_on + 14 then
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
  from recruitment_fee_agreements
  where id = agreement_id;
  if agreement.agreement_ref <> invoice_data ->> 'fee_agreement_ref'
    or agreement.fee_rate <> fee_percent / 100 then
    raise exception 'FEE_AGREEMENT_MISMATCH';
  end if;

  select * into existing_invoice
  from revenue_invoices
  where tenant_id = tenant
    and document_number = invoice_data ->> 'invoice_number';
  if found then
    if existing_invoice.payload_sha256 = payload_hash then
      return jsonb_build_object(
        'status', 'idempotent',
        'invoice_id', existing_invoice.id,
        'placement_set_id', existing_invoice.placement_set_id
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
    fee_agreement_id, placement_set_id, invoice_pdf_sha256, payload_sha256
  ) values (
    tenant, (invoice_data ->> 'issue_date')::date,
    (invoice_data ->> 'issue_date')::date, invoice_data ->> 'company_name',
    invoice_data ->> 'position', invoice_amount, 0, '일반',
    invoice_data ->> 'candidate_name', salary, fee_percent / 100,
    case when (invoice_data ->> 'draft')::boolean then 'draft' else 'issued' end,
    'manual', invoice_data ->> 'invoice_number', invoice_data ->> 'position',
    start_on, due_on, agreement.id, placement_id,
    invoice_data ->> 'pdf_sha256', payload_hash
  ) returning id into invoice_id;

  insert into client_billing_statements (
    tenant_id, statement_no, recipient_name, issue_date, due_date, title,
    service_label, line_items, total_amount, bank_info, issuer_name,
    linked_invoice_id, status, placement_set_id, pdf_sha256, payload_sha256
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
      'bank', '하나은행', 'account', '588-910030-71604',
      'holder', '밸류커넥트 주식회사'
    ), '밸류커넥트 주식회사', invoice_id,
    'draft', placement_id, invoice_data ->> 'pdf_sha256', payload_hash
  );

  if settlement_data is not null and jsonb_typeof(settlement_data) <> 'null' then
    am_percent := (settlement_data ->> 'account_manager_percent')::numeric;
    coworker_percent := (settlement_data ->> 'coworker_percent')::numeric;
    if am_percent + coworker_percent + company_percent <> 100 then
      raise exception 'CONTRACT_ERROR: allocation percentages must total 100';
    end if;
    company_gross := round(invoice_amount * company_percent / 100)::bigint;
    am_gross := round(invoice_amount * am_percent / 100)::bigint;
    coworker_gross := invoice_amount - company_gross - am_gross;
    am_tax := round(am_gross * 0.033)::bigint;
    coworker_tax := round(coworker_gross * 0.033)::bigint;
    rps_amount := settlement_data ->> 'rps_advance_krw';
    rps_bearer := settlement_data ->> 'rps_bearer';
    if coalesce(rps_amount, 0) > 0 then
      if rps_bearer = 'account_manager' then am_rps := rps_amount;
      elsif rps_bearer = 'coworker' then coworker_rps := rps_amount;
      elsif rps_bearer = 'company' then company_rps := rps_amount;
      elsif rps_bearer = 'pro_rata' then
        am_rps := round(rps_amount * am_percent / (am_percent + coworker_percent))::bigint;
        coworker_rps := rps_amount - am_rps;
      else raise exception 'CONTRACT_ERROR: RPS bearer is invalid';
      end if;
    end if;
    if least(am_gross - am_tax - am_rps, coworker_gross - coworker_tax - coworker_rps,
      company_gross - company_rps) < 0 then
      raise exception 'CONTRACT_ERROR: RPS deduction exceeds allocation';
    end if;

    insert into commission_payouts (
      tenant_id, invoice_id, payee_role, payee_name, split_rate,
      gross_amount, withholding_rate, withholding_amount, net_amount, status
    ) values
      (tenant, invoice_id, 'project_owner', settlement_data ->> 'account_manager_name',
       am_percent / 100, am_gross, 0.033, am_tax, am_gross - am_tax - am_rps, 'pending'),
      (tenant, invoice_id, 'coworker', settlement_data ->> 'coworker_name',
       coworker_percent / 100, coworker_gross, 0.033, coworker_tax,
       coworker_gross - coworker_tax - coworker_rps, 'pending'),
      (tenant, invoice_id, 'company', '밸류커넥트 주식회사',
       company_percent / 100, company_gross, 0, 0, company_gross - company_rps, 'pending');

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
    'placement_set_id', placement_id, 'fee_agreement_id', agreement.id
  );
end;
$$;

revoke all on function store_invoice_placement_set(jsonb) from public;
grant execute on function store_invoice_placement_set(jsonb) to service_role;
