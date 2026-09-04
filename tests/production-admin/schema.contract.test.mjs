import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import {
  checkAdminSchemaContract,
  summarizeAdminSchemaContract,
} from '../../scripts/check-admin-schema.mjs';

const EXPECTED_MIGRATIONS = [
  '20260507000000_pipeline.sql',
  '20260904000050_lock_legacy_pipeline_surface.sql',
  '20260904000100_admin_walking_skeleton.sql',
  '20260904000150_admin_review_audit.sql',
  '20260904000160_harden_admin_trigger_function.sql',
  '20260904000170_lock_review_audit_privileges.sql',
];

test('production admin schema contract pins preview baseline, legacy lock, and admin skeleton', () => {
  const result = checkAdminSchemaContract();
  assert.equal(result.ok, true, result.errors.join('\n'));
  assert.deepEqual(result.migrations, EXPECTED_MIGRATIONS);
  assert.equal(result.checkedMigrations, 6);

  const summary = summarizeAdminSchemaContract(result);
  assert.match(summary, /VERDICT: PASS/);
  assert.match(summary, /MIGRATIONS: 20260507000000_pipeline.sql,20260904000050_lock_legacy_pipeline_surface.sql,20260904000100_admin_walking_skeleton.sql,20260904000150_admin_review_audit.sql,20260904000160_harden_admin_trigger_function.sql,20260904000170_lock_review_audit_privileges.sql/);
  assert.match(summary, /LEGACY_LOCK: service_role_only/);
  assert.match(summary, /TABLES: pipeline_candidates pipeline_stage_history pipeline_comments pipeline_members admin_positions admin_candidates admin_candidate_review_events/);
});

test('checker rejects missing remote baseline migration', () => {
  const result = checkAdminSchemaContract({
    migrationsOverride: new Map([
      ['20260904000050_lock_legacy_pipeline_surface.sql', lockSql()],
      ['20260904000100_admin_walking_skeleton.sql', adminSql()],
      ['20260904000150_admin_review_audit.sql', auditSql()],
      ['20260904000160_harden_admin_trigger_function.sql', hardeningSql()],
      ['20260904000170_lock_review_audit_privileges.sql', privilegeLockSql()],
    ]),
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /migration order mismatch/);
});

test('checker rejects broad public legacy pipeline policies after lock migration', () => {
  const result = checkAdminSchemaContract({
    migrationsOverride: new Map([
      ['20260507000000_pipeline.sql', baselineSql()],
      ['20260904000050_lock_legacy_pipeline_surface.sql', `
        create policy "service_all_candidates" on pipeline_candidates for all using (true);
      `],
      ['20260904000100_admin_walking_skeleton.sql', adminSql()],
      ['20260904000150_admin_review_audit.sql', auditSql()],
      ['20260904000160_harden_admin_trigger_function.sql', hardeningSql()],
      ['20260904000170_lock_review_audit_privileges.sql', privilegeLockSql()],
    ]),
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /legacy lock must drop broad public policy service_all_candidates/);
});

test('checker rejects schema that increments version in the database trigger', () => {
  const result = checkAdminSchemaContract({
    migrationsOverride: new Map([
      ['20260507000000_pipeline.sql', baselineSql()],
      ['20260904000050_lock_legacy_pipeline_surface.sql', lockSql()],
      ['20260904000100_admin_walking_skeleton.sql', `${adminSql()} new.version := old.version + 1;`],
      ['20260904000150_admin_review_audit.sql', auditSql()],
      ['20260904000160_harden_admin_trigger_function.sql', hardeningSql()],
      ['20260904000170_lock_review_audit_privileges.sql', privilegeLockSql()],
    ]),
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /admin trigger must not increment version/);
});

test('checker rejects a security-definer review audit trigger', () => {
  const result = checkAdminSchemaContract({
    migrationsOverride: new Map([
      ['20260507000000_pipeline.sql', baselineSql()],
      ['20260904000050_lock_legacy_pipeline_surface.sql', lockSql()],
      ['20260904000100_admin_walking_skeleton.sql', adminSql()],
      ['20260904000150_admin_review_audit.sql', auditSql().replaceAll('security invoker', 'security definer')],
      ['20260904000160_harden_admin_trigger_function.sql', hardeningSql()],
      ['20260904000170_lock_review_audit_privileges.sql', privilegeLockSql()],
    ]),
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /audit trigger functions must be security invoker/);
});

test('checker rejects an updated-at trigger function without a pinned search path', () => {
  const result = checkAdminSchemaContract({
    migrationsOverride: new Map([
      ['20260507000000_pipeline.sql', baselineSql()],
      ['20260904000050_lock_legacy_pipeline_surface.sql', lockSql()],
      ['20260904000100_admin_walking_skeleton.sql', adminSql()],
      ['20260904000150_admin_review_audit.sql', auditSql()],
      ['20260904000160_harden_admin_trigger_function.sql', hardeningSql().replace(/set search_path = pg_catalog\n/i, '')],
      ['20260904000170_lock_review_audit_privileges.sql', privilegeLockSql()],
    ]),
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /updated-at trigger function must pin search_path/);
});

test('checker rejects a review audit privilege lock without a full service-role reset', () => {
  const result = checkAdminSchemaContract({
    migrationsOverride: new Map([
      ['20260507000000_pipeline.sql', baselineSql()],
      ['20260904000050_lock_legacy_pipeline_surface.sql', lockSql()],
      ['20260904000100_admin_walking_skeleton.sql', adminSql()],
      ['20260904000150_admin_review_audit.sql', auditSql()],
      ['20260904000160_harden_admin_trigger_function.sql', hardeningSql()],
      ['20260904000170_lock_review_audit_privileges.sql', privilegeLockSql().replace(/revoke all privileges[^;]+;/i, '')],
    ]),
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join('\n'), /review audit service role privilege reset/);
});

function auditSql() {
  return readFileSync(new URL('../../supabase/migrations/20260904000150_admin_review_audit.sql', import.meta.url), 'utf8');
}

function hardeningSql() {
  return readFileSync(new URL('../../supabase/migrations/20260904000160_harden_admin_trigger_function.sql', import.meta.url), 'utf8');
}

function privilegeLockSql() {
  return readFileSync(new URL('../../supabase/migrations/20260904000170_lock_review_audit_privileges.sql', import.meta.url), 'utf8');
}

function baselineSql() {
  return `
    create table if not exists pipeline_candidates (id uuid primary key default gen_random_uuid());
    alter table pipeline_candidates enable row level security;
    create policy "service_all_candidates" on pipeline_candidates for all using (true);
    create table if not exists pipeline_stage_history (id uuid primary key default gen_random_uuid());
    alter table pipeline_stage_history enable row level security;
    create policy "service_all_history" on pipeline_stage_history for all using (true);
    create table if not exists pipeline_comments (id uuid primary key default gen_random_uuid());
    alter table pipeline_comments enable row level security;
    create policy "service_all_comments" on pipeline_comments for all using (true);
    create table if not exists pipeline_members (
      id uuid primary key default gen_random_uuid(),
      role text not null default 'viewer' check (role in ('admin','reviewer','viewer'))
    );
    alter table pipeline_members enable row level security;
    create policy "service_all_members" on pipeline_members for all using (true);
  `;
}

function lockSql() {
  return `
    drop policy if exists "service_all_candidates" on pipeline_candidates;
    drop policy if exists "service_all_history" on pipeline_stage_history;
    drop policy if exists "service_all_comments" on pipeline_comments;
    drop policy if exists "service_all_members" on pipeline_members;
    revoke all on pipeline_candidates from public, anon, authenticated;
    revoke all on pipeline_stage_history from public, anon, authenticated;
    revoke all on pipeline_comments from public, anon, authenticated;
    revoke all on pipeline_members from public, anon, authenticated;
    grant select, insert, update, delete on pipeline_candidates to service_role;
    grant select, insert, update, delete on pipeline_stage_history to service_role;
    grant select, insert, update, delete on pipeline_comments to service_role;
    grant select, insert, update, delete on pipeline_members to service_role;
    create policy pipeline_candidates_service_role on pipeline_candidates for all to service_role using (true) with check (true);
    create policy pipeline_stage_history_service_role on pipeline_stage_history for all to service_role using (true) with check (true);
    create policy pipeline_comments_service_role on pipeline_comments for all to service_role using (true) with check (true);
    create policy pipeline_members_service_role on pipeline_members for all to service_role using (true) with check (true);
  `;
}

function adminSql() {
  return `
    create table if not exists admin_positions (
      id uuid not null default gen_random_uuid(),
      tenant_id text not null,
      external_key text not null,
      title text not null,
      status text not null default 'open',
      created_at timestamptz not null default now(),
      updated_at timestamptz not null default now(),
      primary key (id),
      constraint admin_positions_tenant_id_id_unique unique (tenant_id, id),
      constraint admin_positions_external_key_unique unique (tenant_id, external_key),
      constraint admin_positions_tenant_id_check check (tenant_id ~ '^(E2E-TEST-[A-Za-z0-9_-]{1,80}|[a-z0-9][a-z0-9_-]{1,62})$'),
      constraint admin_positions_status_check check (status in ('open', 'paused', 'closed'))
    );
    create table if not exists admin_candidates (
      id uuid not null default gen_random_uuid(),
      tenant_id text not null,
      position_id uuid not null,
      external_key text not null,
      display_name text not null,
      review_status text not null default 'unreviewed',
      version integer not null default 1,
      created_at timestamptz not null default now(),
      updated_at timestamptz not null default now(),
      primary key (id),
      constraint admin_candidates_tenant_id_id_unique unique (tenant_id, id),
      constraint admin_candidates_external_key_unique unique (tenant_id, external_key),
      constraint admin_candidates_position_fk foreign key (tenant_id, position_id)
        references admin_positions (tenant_id, id),
      constraint admin_candidates_tenant_id_check check (tenant_id ~ '^(E2E-TEST-[A-Za-z0-9_-]{1,80}|[a-z0-9][a-z0-9_-]{1,62})$'),
      constraint admin_candidates_review_status_check check (review_status in ('unreviewed', 'reviewed', 'rejected')),
      constraint admin_candidates_version_check check (version > 0)
    );
    create or replace function admin_touch_updated_at() returns trigger language plpgsql as $$ begin new.updated_at = now(); return new; end; $$;
    create trigger admin_positions_touch_updated_at before update on admin_positions for each row execute function admin_touch_updated_at();
    create trigger admin_candidates_touch_updated_at before update on admin_candidates for each row execute function admin_touch_updated_at();
    alter table admin_positions enable row level security;
    alter table admin_candidates enable row level security;
    revoke all on admin_positions from public, anon, authenticated;
    revoke all on admin_candidates from public, anon, authenticated;
    grant select, insert, update, delete on admin_positions to service_role;
    grant select, insert, update, delete on admin_candidates to service_role;
    create policy admin_positions_service_role on admin_positions for all to service_role using (true) with check (true);
    create policy admin_candidates_service_role on admin_candidates for all to service_role using (true) with check (true);
  `;
}
