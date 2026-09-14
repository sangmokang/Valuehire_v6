create role service_role;
create role authenticated;
create schema auth;
create function auth.jwt() returns jsonb
language sql stable as $$
  select '{"email":"sangmokang@valueconnect.kr"}'::jsonb;
$$;

create extension if not exists pgcrypto;

create table revenue_invoices (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null default 'valueconnect',
  write_date date,
  issue_date date,
  client_name text,
  item_name text,
  supply_amount bigint not null,
  vat_amount bigint not null default 0,
  invoice_type text not null default '일반',
  candidate_name text,
  candidate_salary bigint,
  commission_rate numeric not null default 0.20,
  status text not null default 'issued'
    check (status in ('draft', 'issued', 'paid', 'canceled')),
  source text not null default 'manual' check (source in ('manual', 'excel')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table commission_payouts (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null default 'valueconnect',
  invoice_id uuid not null references revenue_invoices(id) on delete cascade,
  payee_role text not null
    check (payee_role in ('coworker', 'project_owner', 'company')),
  payee_name text,
  split_rate numeric not null,
  gross_amount bigint not null,
  withholding_rate numeric not null default 0.033,
  withholding_amount bigint not null default 0,
  net_amount bigint not null,
  status text not null default 'pending' check (status in ('pending', 'paid')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table client_billing_statements (
  id uuid primary key default gen_random_uuid(),
  tenant_id text not null default 'valueconnect',
  statement_no text not null unique,
  recipient_name text not null,
  issue_date date not null,
  due_date date,
  title text not null default '인력알선에 따른 청구의 건',
  service_label text not null default 'HR Service',
  line_items jsonb not null default '[]'::jsonb,
  total_amount bigint not null default 0,
  bank_info jsonb not null default '{}'::jsonb,
  issuer_name text not null default '밸류커넥트 주식회사',
  linked_invoice_id uuid references revenue_invoices(id) on delete set null,
  status text not null default 'draft' check (status in ('draft', 'sent', 'paid')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
