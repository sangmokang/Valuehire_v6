#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO_ROOT = new URL('..', import.meta.url).pathname;
const MIGRATIONS_DIR = join(REPO_ROOT, 'supabase', 'migrations');
const EXPECTED_MIGRATIONS = [
  '20260507000000_pipeline.sql',
  '20260904000050_lock_legacy_pipeline_surface.sql',
  '20260904000100_admin_walking_skeleton.sql',
  '20260904000150_admin_review_audit.sql',
  '20260904000160_harden_admin_trigger_function.sql',
  '20260904000170_lock_review_audit_privileges.sql',
];
const LEGACY_TABLES = [
  ['pipeline_candidates', 'service_all_candidates'],
  ['pipeline_stage_history', 'service_all_history'],
  ['pipeline_comments', 'service_all_comments'],
  ['pipeline_members', 'service_all_members'],
];

function normalizeSql(sql) {
  return sql
    .replace(/--.*$/gm, ' ')
    .replace(/\s+/g, ' ')
    .replace(/\bpublic\./gi, '')
    .trim();
}

function readMigrations() {
  if (!existsSync(MIGRATIONS_DIR)) {
    return new Map();
  }
  return new Map(readdirSync(MIGRATIONS_DIR)
    .filter((name) => /^\d+_.*\.sql$/.test(name))
    .sort()
    .map((name) => [name, readFileSync(join(MIGRATIONS_DIR, name), 'utf8')]));
}

function has(sql, pattern) {
  return pattern.test(normalizeSql(sql));
}

function requirePattern(errors, sql, label, pattern) {
  if (!has(sql, pattern)) {
    errors.push(`missing ${label}`);
  }
}

function checkOrder(errors, names) {
  if (names.join(',') !== EXPECTED_MIGRATIONS.join(',')) {
    errors.push(`migration order mismatch: expected ${EXPECTED_MIGRATIONS.join(',')} got ${names.join(',')}`);
  }
}

function checkBaseline(errors, sql) {
  for (const [table, policy] of LEGACY_TABLES) {
    requirePattern(errors, sql, `baseline table ${table}`,
      new RegExp(`create\\s+table\\s+if\\s+not\\s+exists\\s+${table}\\s*\\(`, 'i'));
    requirePattern(errors, sql, `baseline RLS ${table}`,
      new RegExp(`alter\\s+table\\s+${table}\\s+enable\\s+row\\s+level\\s+security`, 'i'));
    requirePattern(errors, sql, `baseline broad policy ${policy}`,
      new RegExp(`create\\s+policy\\s+"?${policy}"?\\s+on\\s+${table}\\s+for\\s+all\\s+using\\s*\\(\\s*true\\s*\\)`, 'i'));
  }
  requirePattern(errors, sql, 'baseline pipeline_members role check',
    /role\s+text\s+not\s+null\s+default\s+'viewer'\s+check\s*\(\s*role\s+in\s*\(\s*'admin'\s*,\s*'reviewer'\s*,\s*'viewer'\s*\)\s*\)/i);
}

function checkLegacyLock(errors, sql) {
  for (const [table, policy] of LEGACY_TABLES) {
    requirePattern(errors, sql, `legacy lock must drop broad public policy ${policy}`,
      new RegExp(`drop\\s+policy\\s+if\\s+exists\\s+"?${policy}"?\\s+on\\s+${table}`, 'i'));
    requirePattern(errors, sql, `legacy lock revokes public access on ${table}`,
      new RegExp(`revoke\\s+all\\s+on\\s+${table}\\s+from\\s+public\\s*,\\s*anon\\s*,\\s*authenticated`, 'i'));
    requirePattern(errors, sql, `legacy lock grants service_role CRUD on ${table}`,
      new RegExp(`grant\\s+select\\s*,\\s*insert\\s*,\\s*update\\s*,\\s*delete\\s+on\\s+${table}\\s+to\\s+service_role`, 'i'));
    requirePattern(errors, sql, `legacy lock service_role policy on ${table}`,
      new RegExp(`create\\s+policy\\s+${table}_service_role\\s+on\\s+${table}\\s+for\\s+all\\s+to\\s+service_role\\s+using\\s*\\(\\s*true\\s*\\)\\s+with\\s+check\\s*\\(\\s*true\\s*\\)`, 'i'));
  }
  if (/drop\s+(table|column|constraint|schema)\b/i.test(normalizeSql(sql))) {
    errors.push('legacy lock must not drop tables, columns, constraints, or schemas');
  }
  if (/create\s+policy\s+"?service_all_/i.test(normalizeSql(sql))) {
    errors.push('legacy lock must not recreate broad public service_all policies');
  }
}

function checkAdmin(errors, sql) {
  const checks = [
    ['admin_positions table', /create\s+table\s+if\s+not\s+exists\s+admin_positions\s*\(/i],
    ['admin_candidates table', /create\s+table\s+if\s+not\s+exists\s+admin_candidates\s*\(/i],
    ['admin_positions uuid id', /id\s+uuid\s+not\s+null\s+default\s+gen_random_uuid\s*\(\s*\)/i],
    ['admin_positions external_key', /external_key\s+text\s+not\s+null/i],
    ['admin_positions primary key id', /primary\s+key\s*\(\s*id\s*\)/i],
    ['admin_positions tenant id unique', /constraint\s+admin_positions_tenant_id_id_unique\s+unique\s*\(\s*tenant_id\s*,\s*id\s*\)/i],
    ['admin_positions external key unique', /constraint\s+admin_positions_external_key_unique\s+unique\s*\(\s*tenant_id\s*,\s*external_key\s*\)/i],
    ['admin_positions tenant E2E check', /constraint\s+admin_positions_tenant_id_check\s+check\s*\([^)]*E2E-TEST-/i],
    ['admin_candidates uuid id', /id\s+uuid\s+not\s+null\s+default\s+gen_random_uuid\s*\(\s*\)/i],
    ['admin_candidates position uuid', /position_id\s+uuid\s+not\s+null/i],
    ['admin_candidates external_key', /external_key\s+text\s+not\s+null/i],
    ['admin_candidates display_name', /display_name\s+text\s+not\s+null/i],
    ['admin_candidates review status default', /review_status\s+text\s+not\s+null\s+default\s+'unreviewed'/i],
    ['admin_candidates version', /version\s+integer\s+not\s+null\s+default\s+1/i],
    ['admin_candidates primary key id', /primary\s+key\s*\(\s*id\s*\)/i],
    ['admin_candidates tenant id unique', /constraint\s+admin_candidates_tenant_id_id_unique\s+unique\s*\(\s*tenant_id\s*,\s*id\s*\)/i],
    ['admin_candidates external key unique', /constraint\s+admin_candidates_external_key_unique\s+unique\s*\(\s*tenant_id\s*,\s*external_key\s*\)/i],
    ['admin_candidates composite tenant fk', /constraint\s+admin_candidates_position_fk\s+foreign\s+key\s*\(\s*tenant_id\s*,\s*position_id\s*\)\s+references\s+admin_positions\s*\(\s*tenant_id\s*,\s*id\s*\)/i],
    ['admin_candidates tenant E2E check', /constraint\s+admin_candidates_tenant_id_check\s+check\s*\([^)]*E2E-TEST-/i],
    ['admin_candidates review status check', /constraint\s+admin_candidates_review_status_check\s+check\s*\(\s*review_status\s+in\s*\(\s*'unreviewed'\s*,\s*'reviewed'\s*,\s*'rejected'\s*\)\s*\)/i],
    ['admin_candidates version check', /constraint\s+admin_candidates_version_check\s+check\s*\(\s*version\s*>\s*0\s*\)/i],
    ['admin touch trigger function', /create\s+or\s+replace\s+function\s+admin_touch_updated_at\s*\(\s*\)\s+returns\s+trigger/i],
    ['admin_positions updated_at trigger', /create\s+trigger\s+admin_positions_touch_updated_at[\s\S]+before\s+update\s+on\s+admin_positions[\s\S]+execute\s+function\s+admin_touch_updated_at\s*\(\s*\)/i],
    ['admin_candidates updated_at trigger', /create\s+trigger\s+admin_candidates_touch_updated_at[\s\S]+before\s+update\s+on\s+admin_candidates[\s\S]+execute\s+function\s+admin_touch_updated_at\s*\(\s*\)/i],
    ['admin_positions RLS', /alter\s+table\s+admin_positions\s+enable\s+row\s+level\s+security/i],
    ['admin_candidates RLS', /alter\s+table\s+admin_candidates\s+enable\s+row\s+level\s+security/i],
    ['admin_positions revoke public', /revoke\s+all\s+on\s+admin_positions\s+from\s+public\s*,\s*anon\s*,\s*authenticated/i],
    ['admin_candidates revoke public', /revoke\s+all\s+on\s+admin_candidates\s+from\s+public\s*,\s*anon\s*,\s*authenticated/i],
    ['admin_positions service_role CRUD', /grant\s+select\s*,\s*insert\s*,\s*update\s*,\s*delete\s+on\s+admin_positions\s+to\s+service_role/i],
    ['admin_candidates service_role CRUD', /grant\s+select\s*,\s*insert\s*,\s*update\s*,\s*delete\s+on\s+admin_candidates\s+to\s+service_role/i],
    ['admin_positions service_role policy', /create\s+policy\s+admin_positions_service_role\s+on\s+admin_positions\s+for\s+all\s+to\s+service_role\s+using\s*\(\s*true\s*\)\s+with\s+check\s*\(\s*true\s*\)/i],
    ['admin_candidates service_role policy', /create\s+policy\s+admin_candidates_service_role\s+on\s+admin_candidates\s+for\s+all\s+to\s+service_role\s+using\s*\(\s*true\s*\)\s+with\s+check\s*\(\s*true\s*\)/i],
  ];
  for (const [label, pattern] of checks) {
    requirePattern(errors, sql, label, pattern);
  }
  if (/new\.version\s*:?=|review_version/i.test(normalizeSql(sql))) {
    errors.push('admin trigger must not increment version');
  }
  if (/create\s+(?:or\s+replace\s+)?view\b/i.test(normalizeSql(sql))) {
    errors.push('admin schema must not create views');
  }
  if (/create\s+(?:or\s+replace\s+)?function\s+(?!admin_touch_updated_at\s*\()/i.test(normalizeSql(sql))) {
    errors.push('admin schema must not create RPC functions');
  }
}

function checkReviewAudit(errors, sql) {
  const checks = [
    ['candidate transient review actor column', /alter\s+table\s+admin_candidates\s+add\s+column\s+pending_review_actor_email_sha256\s+text/i],
    ['candidate transient review actor hash check', /constraint\s+admin_candidates_pending_review_actor_check\s+check\s*\([\s\S]*pending_review_actor_email_sha256\s+is\s+null[\s\S]*\^\[0-9a-f\]\{64\}\$/i],
    ['review audit table', /create\s+table\s+admin_candidate_review_events\s*\(/i],
    ['review audit primary key', /primary\s+key\s*\(\s*id\s*\)/i],
    ['review audit unique candidate version', /constraint\s+admin_review_events_candidate_version_unique\s+unique\s*\(\s*tenant_id\s*,\s*candidate_id\s*,\s*candidate_version\s*\)/i],
    ['review audit candidate foreign key', /constraint\s+admin_review_events_candidate_fk\s+foreign\s+key\s*\(\s*tenant_id\s*,\s*candidate_id\s*\)\s+references\s+admin_candidates\s*\(\s*tenant_id\s*,\s*id\s*\)/i],
    ['review audit position foreign key', /constraint\s+admin_review_events_position_fk\s+foreign\s+key\s*\(\s*tenant_id\s*,\s*position_id\s*\)\s+references\s+admin_positions\s*\(\s*tenant_id\s*,\s*id\s*\)/i],
    ['review audit actor hash check', /constraint\s+admin_review_events_actor_hash_check\s+check\s*\(\s*actor_email_sha256\s*~\s*'\^\[0-9a-f\]\{64\}\$'\s*\)/i],
    ['review audit status checks', /constraint\s+admin_review_events_transition_check\s+check\s*\(\s*from_review_status\s*<>\s*to_review_status\s*\)/i],
    ['review audit candidate version check', /constraint\s+admin_review_events_version_check\s+check\s*\(\s*candidate_version\s*>\s*1\s*\)/i],
    ['review audit capture function', /create\s+or\s+replace\s+function\s+admin_capture_candidate_review_event\s*\(\s*\)\s+returns\s+trigger/i],
    ['review audit atomic insert', /insert\s+into\s+admin_candidate_review_events\s*\([\s\S]*actor_email_sha256[\s\S]*old\.review_status[\s\S]*new\.review_status[\s\S]*new\.version/i],
    ['review audit transient actor clearing', /new\.pending_review_actor_email_sha256\s*:=\s*null/i],
    ['review audit exact version transition', /new\.version\s+is\s+distinct\s+from\s+old\.version\s*\+\s*1/i],
    ['review audit capture trigger', /create\s+trigger\s+admin_candidates_capture_review_event\s+before\s+insert\s+or\s+update\s+on\s+admin_candidates[\s\S]*execute\s+function\s+admin_capture_candidate_review_event\s*\(\s*\)/i],
    ['review audit immutable guard function', /create\s+or\s+replace\s+function\s+admin_guard_candidate_review_event\s*\(\s*\)\s+returns\s+trigger/i],
    ['review audit production delete guard', /old\.tenant_id\s*!~\s*'\^E2E-TEST-'[\s\S]*production review audit events cannot be deleted/i],
    ['review audit immutable trigger', /create\s+trigger\s+admin_review_events_guard_mutation\s+before\s+update\s+or\s+delete\s+on\s+admin_candidate_review_events/i],
    ['review audit RLS', /alter\s+table\s+admin_candidate_review_events\s+enable\s+row\s+level\s+security/i],
    ['review audit forced RLS', /alter\s+table\s+admin_candidate_review_events\s+force\s+row\s+level\s+security/i],
    ['review audit public revoke', /revoke\s+all\s+on\s+admin_candidate_review_events\s+from\s+public\s*,\s*anon\s*,\s*authenticated/i],
    ['review audit service role least privilege', /grant\s+select\s*,\s*insert\s*,\s*delete\s+on\s+admin_candidate_review_events\s+to\s+service_role/i],
    ['review audit select policy', /create\s+policy\s+admin_review_events_service_role_select\s+on\s+admin_candidate_review_events\s+for\s+select\s+to\s+service_role\s+using\s*\(\s*true\s*\)/i],
    ['review audit insert policy', /create\s+policy\s+admin_review_events_service_role_insert\s+on\s+admin_candidate_review_events\s+for\s+insert\s+to\s+service_role\s+with\s+check\s*\(\s*true\s*\)/i],
    ['review audit test cleanup policy', /create\s+policy\s+admin_review_events_service_role_delete_test\s+on\s+admin_candidate_review_events\s+for\s+delete\s+to\s+service_role\s+using\s*\(\s*tenant_id\s+like\s+'E2E-TEST-%'\s*\)/i],
  ];
  for (const [label, pattern] of checks) {
    requirePattern(errors, sql, label, pattern);
  }
  const normalized = normalizeSql(sql);
  const invokerCount = Array.from(normalized.matchAll(/security\s+invoker/gi)).length;
  if (invokerCount !== 2 || /security\s+definer/i.test(normalized)) {
    errors.push('audit trigger functions must be security invoker');
  }
  const searchPathCount = Array.from(normalized.matchAll(/set\s+search_path\s*=\s*pg_catalog\s*,\s*public/gi)).length;
  if (searchPathCount !== 2) {
    errors.push('audit trigger functions must pin search_path');
  }
  if (/grant\s+[^;]*update[^;]*on\s+admin_candidate_review_events/i.test(normalized)) {
    errors.push('review audit table must not grant update');
  }
  if (/create\s+(?:or\s+replace\s+)?view\b/i.test(normalized)) {
    errors.push('review audit migration must not create views');
  }
}

function checkTriggerHardening(errors, sql) {
  const checks = [
    ['hardened updated-at trigger function', /create\s+or\s+replace\s+function\s+admin_touch_updated_at\s*\(\s*\)\s+returns\s+trigger/i],
    ['updated-at trigger function must be security invoker', /security\s+invoker/i],
    ['updated-at trigger function must pin search_path', /set\s+search_path\s*=\s*pg_catalog/i],
    ['updated-at trigger function public execute revoke', /revoke\s+all\s+on\s+function\s+admin_touch_updated_at\s*\(\s*\)\s+from\s+public\s*,\s*anon\s*,\s*authenticated/i],
    ['updated-at trigger function service role execute', /grant\s+execute\s+on\s+function\s+admin_touch_updated_at\s*\(\s*\)\s+to\s+service_role/i],
  ];
  for (const [label, pattern] of checks) {
    requirePattern(errors, sql, label, pattern);
  }
  if (/security\s+definer/i.test(normalizeSql(sql))) {
    errors.push('updated-at trigger function must not be security definer');
  }
}

function checkReviewAuditPrivilegeLock(errors, sql) {
  const checks = [
    ['review audit service role privilege reset', /revoke\s+all(?:\s+privileges)?\s+on(?:\s+table)?\s+admin_candidate_review_events\s+from\s+service_role/i],
    ['review audit service role exact grant', /grant\s+select\s*,\s*insert\s*,\s*delete\s+on(?:\s+table)?\s+admin_candidate_review_events\s+to\s+service_role/i],
  ];
  for (const [label, pattern] of checks) {
    requirePattern(errors, sql, label, pattern);
  }
  if (/grant\s+[^;]*(?:update|truncate|references|trigger)[^;]*on(?:\s+table)?\s+admin_candidate_review_events/i.test(normalizeSql(sql))) {
    errors.push('review audit privilege lock must not restore write or DDL privileges beyond insert and E2E delete');
  }
}

export function checkAdminSchemaContract(options = {}) {
  const migrations = options.migrationsOverride || readMigrations();
  const names = [...migrations.keys()].sort();
  const errors = [];
  checkOrder(errors, names);

  const baseline = migrations.get(EXPECTED_MIGRATIONS[0]) || '';
  const lock = migrations.get(EXPECTED_MIGRATIONS[1]) || '';
  const admin = migrations.get(EXPECTED_MIGRATIONS[2]) || '';
  const reviewAudit = migrations.get(EXPECTED_MIGRATIONS[3]) || '';
  const triggerHardening = migrations.get(EXPECTED_MIGRATIONS[4]) || '';
  const reviewAuditPrivilegeLock = migrations.get(EXPECTED_MIGRATIONS[5]) || '';
  checkBaseline(errors, baseline);
  checkLegacyLock(errors, lock);
  checkAdmin(errors, admin);
  checkReviewAudit(errors, reviewAudit);
  checkTriggerHardening(errors, triggerHardening);
  checkReviewAuditPrivilegeLock(errors, reviewAuditPrivilegeLock);

  const combinedSource = EXPECTED_MIGRATIONS
    .map((name) => `-- ${name}\n${migrations.get(name) || ''}`)
    .join('\n');
  const combinedDigest = createHash('sha256').update(combinedSource).digest('hex');
  return {
    ok: errors.length === 0,
    checkedMigrations: names.length,
    migrations: names,
    combinedDigest,
    errors,
  };
}

export function summarizeAdminSchemaContract(result) {
  const lines = [
    `VERDICT: ${result.ok ? 'PASS' : 'FAIL'}`,
    `CHECKED_MIGRATIONS: ${result.checkedMigrations}`,
    `MIGRATIONS: ${result.migrations.join(',')}`,
    `COMBINED_DIGEST: ${result.combinedDigest}`,
    'LEGACY_LOCK: service_role_only',
    'TABLES: pipeline_candidates pipeline_stage_history pipeline_comments pipeline_members admin_positions admin_candidates admin_candidate_review_events',
  ];
  if (result.errors.length > 0) {
    lines.push('ERRORS:');
    for (const error of result.errors) {
      lines.push(`- ${error}`);
    }
  }
  return lines.join('\n');
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const result = checkAdminSchemaContract();
  console.log(summarizeAdminSchemaContract(result));
  process.exit(result.ok ? 0 : 1);
}
