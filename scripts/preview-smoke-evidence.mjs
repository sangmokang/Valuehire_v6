#!/usr/bin/env node

import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { fileURLToPath } from "node:url";
import { checkAdminSchemaContract } from "./check-admin-schema.mjs";

const REPO_ROOT = fileURLToPath(new URL("..", import.meta.url));
const VERCEL_PROJECT_ID = "prj_isTeytMDr2EiXW5hg5rv4wPdyBW5";
const DEPLOYMENT_SOURCE_PATHS = ["api", "apps/production-admin", "server/admin", "package.json", "package-lock.json", "vercel.json"];
const ADMIN_TABLES = ["admin_candidate_review_events", "admin_candidates", "admin_positions"];
const LEGACY_TABLES = ["pipeline_candidates", "pipeline_comments", "pipeline_members", "pipeline_stage_history"];
const TABLES = [...ADMIN_TABLES, ...LEGACY_TABLES];
export const publicSensitivePaths = [
  "/supabase/migrations/20260904000100_admin_walking_skeleton.sql",
  "/supabase/migrations/20260904000150_admin_review_audit.sql",
  "/docs/engineering/production-walking-skeleton-goal-2026-09-04.md",
  "/server/admin/auth.js",
  "/scripts/smoke-preview-admin.mjs",
  "/scripts/smoke-preview-admin-ui.py",
  "/scripts/deploy-preview.sh",
  "/scripts/production-readonly-contract.mjs",
  "/scripts/verify-production-rollback.mjs",
  "/scripts/check-preview-smoke-contract.mjs",
  "/tests/production-admin/server.test.mjs",
];
const EXPECTED_COLUMNS = [
  "admin_candidate_review_events:id:uuid:NO",
  "admin_candidate_review_events:tenant_id:text:NO",
  "admin_candidate_review_events:candidate_id:uuid:NO",
  "admin_candidate_review_events:position_id:uuid:NO",
  "admin_candidate_review_events:actor_email_sha256:text:NO",
  "admin_candidate_review_events:from_review_status:text:NO",
  "admin_candidate_review_events:to_review_status:text:NO",
  "admin_candidate_review_events:candidate_version:integer:NO",
  "admin_candidate_review_events:occurred_at:timestamp with time zone:NO",
  "admin_candidates:id:uuid:NO",
  "admin_candidates:tenant_id:text:NO",
  "admin_candidates:position_id:uuid:NO",
  "admin_candidates:external_key:text:NO",
  "admin_candidates:display_name:text:NO",
  "admin_candidates:review_status:text:NO",
  "admin_candidates:version:integer:NO",
  "admin_candidates:created_at:timestamp with time zone:NO",
  "admin_candidates:updated_at:timestamp with time zone:NO",
  "admin_candidates:pending_review_actor_email_sha256:text:YES",
  "admin_positions:id:uuid:NO",
  "admin_positions:tenant_id:text:NO",
  "admin_positions:external_key:text:NO",
  "admin_positions:title:text:NO",
  "admin_positions:status:text:NO",
  "admin_positions:created_at:timestamp with time zone:NO",
  "admin_positions:updated_at:timestamp with time zone:NO",
  "pipeline_candidates:id:uuid:NO",
  "pipeline_candidates:name:text:NO",
  "pipeline_candidates:jd_id:text:YES",
  "pipeline_candidates:jd_title:text:YES",
  "pipeline_candidates:stage:text:NO",
  "pipeline_candidates:match_score:integer:YES",
  "pipeline_candidates:skills:ARRAY:YES",
  "pipeline_candidates:memo:text:YES",
  "pipeline_candidates:source:text:YES",
  "pipeline_candidates:file_name:text:YES",
  "pipeline_candidates:created_at:timestamp with time zone:YES",
  "pipeline_candidates:updated_at:timestamp with time zone:YES",
  "pipeline_comments:id:uuid:NO",
  "pipeline_comments:candidate_id:uuid:YES",
  "pipeline_comments:author_email:text:NO",
  "pipeline_comments:content:text:YES",
  "pipeline_comments:mentions:ARRAY:YES",
  "pipeline_comments:draft:text:YES",
  "pipeline_comments:created_at:timestamp with time zone:YES",
  "pipeline_members:id:uuid:NO",
  "pipeline_members:user_email:text:NO",
  "pipeline_members:role:text:NO",
  "pipeline_members:invited_by:text:YES",
  "pipeline_members:created_at:timestamp with time zone:YES",
  "pipeline_stage_history:id:uuid:NO",
  "pipeline_stage_history:candidate_id:uuid:YES",
  "pipeline_stage_history:from_stage:text:YES",
  "pipeline_stage_history:to_stage:text:NO",
  "pipeline_stage_history:changed_by:text:YES",
  "pipeline_stage_history:changed_at:timestamp with time zone:YES",
];
const EXPECTED_CONSTRAINTS = new Map([
  ["admin_candidate_review_events_pkey", ["p", /PRIMARY KEY \(id\)/]],
  ["admin_review_events_actor_hash_check", ["c", /actor_email_sha256.*\^\[0-9a-f\]\{64\}\$/]],
  ["admin_review_events_candidate_fk", ["f", /FOREIGN KEY \(tenant_id, candidate_id\) REFERENCES admin_candidates\(tenant_id, id\).*ON DELETE RESTRICT/]],
  ["admin_review_events_candidate_version_unique", ["u", /UNIQUE \(tenant_id, candidate_id, candidate_version\)/]],
  ["admin_review_events_from_status_check", ["c", /unreviewed.*reviewed.*rejected/]],
  ["admin_review_events_position_fk", ["f", /FOREIGN KEY \(tenant_id, position_id\) REFERENCES admin_positions\(tenant_id, id\).*ON DELETE RESTRICT/]],
  ["admin_review_events_tenant_id_check", ["c", /E2E-TEST-/]],
  ["admin_review_events_to_status_check", ["c", /unreviewed.*reviewed.*rejected/]],
  ["admin_review_events_transition_check", ["c", /from_review_status <> to_review_status/]],
  ["admin_review_events_version_check", ["c", /candidate_version > 1/]],
  ["admin_candidates_display_name_check", ["c", /length\(btrim\(display_name\)\).*120/]],
  ["admin_candidates_external_key_check", ["c", /length\(btrim\(external_key\)\).*160/]],
  ["admin_candidates_external_key_unique", ["u", /UNIQUE \(tenant_id, external_key\)/]],
  ["admin_candidates_pending_review_actor_check", ["c", /pending_review_actor_email_sha256 IS NULL.*\^\[0-9a-f\]\{64\}\$/]],
  ["admin_candidates_pkey", ["p", /PRIMARY KEY \(id\)/]],
  ["admin_candidates_position_fk", ["f", /FOREIGN KEY \(tenant_id, position_id\) REFERENCES admin_positions\(tenant_id, id\).*ON DELETE RESTRICT/]],
  ["admin_candidates_review_status_check", ["c", /unreviewed.*reviewed.*rejected/]],
  ["admin_candidates_tenant_id_check", ["c", /E2E-TEST-/]],
  ["admin_candidates_tenant_id_id_unique", ["u", /UNIQUE \(tenant_id, id\)/]],
  ["admin_candidates_version_check", ["c", /version > 0/]],
  ["admin_positions_external_key_check", ["c", /length\(btrim\(external_key\)\).*160/]],
  ["admin_positions_external_key_unique", ["u", /UNIQUE \(tenant_id, external_key\)/]],
  ["admin_positions_pkey", ["p", /PRIMARY KEY \(id\)/]],
  ["admin_positions_status_check", ["c", /open.*paused.*closed/]],
  ["admin_positions_tenant_id_check", ["c", /E2E-TEST-/]],
  ["admin_positions_tenant_id_id_unique", ["u", /UNIQUE \(tenant_id, id\)/]],
  ["admin_positions_title_check", ["c", /length\(btrim\(title\)\).*160/]],
]);

const REMOTE_SCHEMA_QUERY = `
select json_build_object(
  'tables', (select coalesce(json_agg(row_to_json(t) order by t.relname), '[]'::json) from (
    select c.relname, c.relrowsecurity, c.relforcerowsecurity
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname in ('admin_candidate_review_events', 'admin_candidates', 'admin_positions', 'pipeline_candidates', 'pipeline_comments', 'pipeline_members', 'pipeline_stage_history')
  ) t),
  'columns', (select coalesce(json_agg(format('%s:%s:%s:%s', table_name, column_name, data_type, is_nullable) order by table_name, ordinal_position), '[]'::json)
    from information_schema.columns where table_schema = 'public' and table_name in ('admin_candidate_review_events', 'admin_candidates', 'admin_positions', 'pipeline_candidates', 'pipeline_comments', 'pipeline_members', 'pipeline_stage_history')),
  'constraints', (select coalesce(json_agg(row_to_json(k) order by k.conname), '[]'::json) from (
    select c.relname, con.conname, con.contype, pg_get_constraintdef(con.oid) as definition
    from pg_constraint con join pg_class c on c.oid = con.conrelid join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname in ('admin_candidate_review_events', 'admin_candidates', 'admin_positions')
  ) k),
  'policies', (select coalesce(json_agg(row_to_json(p) order by p.tablename, p.policyname), '[]'::json) from (
    select tablename, policyname, cmd, roles, qual, with_check from pg_policies
    where schemaname = 'public' and tablename in ('admin_candidate_review_events', 'admin_candidates', 'admin_positions', 'pipeline_candidates', 'pipeline_comments', 'pipeline_members', 'pipeline_stage_history')
  ) p),
  'unsafe_grants', (select coalesce(json_agg(row_to_json(g)), '[]'::json) from (
    select c.relname, coalesce(r.rolname, 'PUBLIC') as grantee, x.privilege_type
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    cross join lateral aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) x
    left join pg_roles r on r.oid = x.grantee
    where n.nspname = 'public' and c.relname in ('admin_candidate_review_events', 'admin_candidates', 'admin_positions', 'pipeline_candidates', 'pipeline_comments', 'pipeline_members', 'pipeline_stage_history')
      and coalesce(r.rolname, 'PUBLIC') in ('PUBLIC', 'anon', 'authenticated')
  ) g),
  'review_event_service_role_grants', (select coalesce(json_agg(g.privilege_type order by g.privilege_type), '[]'::json) from (
    select x.privilege_type
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    cross join lateral aclexplode(coalesce(c.relacl, acldefault('r', c.relowner))) x
    join pg_roles r on r.oid = x.grantee
    where n.nspname = 'public' and c.relname = 'admin_candidate_review_events' and r.rolname = 'service_role'
  ) g),
  'triggers', (select coalesce(json_agg(row_to_json(t) order by t.relname, t.tgname), '[]'::json) from (
    select c.relname, tr.tgname, pg_get_triggerdef(tr.oid) as definition
    from pg_trigger tr join pg_class c on c.oid = tr.tgrelid join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relname in ('admin_candidate_review_events', 'admin_candidates', 'admin_positions') and not tr.tgisinternal
  ) t),
  'sensitive_views', (select coalesce(json_agg(viewname order by viewname), '[]'::json) from pg_views
    where schemaname = 'public' and (definition ilike '%admin_candidate_review_events%' or definition ilike '%admin_candidates%' or definition ilike '%admin_positions%' or definition ilike '%pipeline_candidates%' or definition ilike '%pipeline_comments%' or definition ilike '%pipeline_members%' or definition ilike '%pipeline_stage_history%')),
  'admin_functions', (select coalesce(json_agg(row_to_json(f) order by f.proname), '[]'::json) from (
    select p.proname, p.prosecdef, p.prorettype::regtype::text as return_type, p.proconfig, md5(p.prosrc) as body_md5
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public' and p.proname like 'admin_%'
  ) f),
  'unsafe_function_executes', (select coalesce(json_agg(row_to_json(x) order by x.proname, x.grantee), '[]'::json) from (
    select p.proname, coalesce(r.rolname, 'PUBLIC') as grantee, a.privilege_type
    from pg_proc p join pg_namespace n on n.oid = p.pronamespace
    cross join lateral aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a
    left join pg_roles r on r.oid = a.grantee
    where n.nspname = 'public' and p.proname like 'admin_%'
      and coalesce(r.rolname, 'PUBLIC') in ('PUBLIC', 'anon', 'authenticated')
  ) x)
) as contract`;

function command(assert, executable, args, failureCode) {
  const result = spawnSync(executable, args, {
    cwd: REPO_ROOT,
    encoding: "utf8",
    env: { ...process.env, NO_COLOR: "1" },
  });
  assert(result.status === 0, failureCode, `${executable} ${args[0]} failed`);
  return { stdout: result.stdout || "", combined: `${result.stdout || ""}\n${result.stderr || ""}` };
}

function parseJson(assert, text, code, label) {
  try {
    return JSON.parse(text);
  } catch (error) {
    if (!error) throw error;
    assert(false, code, `${label} did not return JSON`);
  }
}

function verifyLocalArtifacts(config, assert) {
  const git = command(assert, "git", ["rev-parse", "HEAD"], "LOCAL_GIT_UNAVAILABLE").stdout.trim();
  assert(/^[0-9a-f]{40}$/.test(git), "LOCAL_GIT_INVALID", "local git SHA is invalid");
  assert(config.expectedSha === git, "EXPECTED_SHA_NOT_CURRENT", "smoke expected SHA differs from local HEAD");
  const dirty = command(assert, "git", ["status", "--porcelain", "--untracked-files=all"], "LOCAL_GIT_UNAVAILABLE").stdout.trim();
  assert(dirty === "", "LOCAL_GIT_DIRTY", "smoke must run from the clean deployed HEAD");

  const schema = checkAdminSchemaContract();
  assert(schema.ok, "LOCAL_SCHEMA_CONTRACT_FAILED", "local schema contract failed");
  assert(schema.combinedDigest === config.expectedSchemaDigest, "EXPECTED_SCHEMA_NOT_CURRENT", "smoke schema digest differs from local migrations");
  const linkedRef = readFileSync(new URL("../supabase/.temp/project-ref", import.meta.url), "utf8").trim();
  assert(linkedRef === config.previewRef, "SUPABASE_LINK_MISMATCH", "linked Supabase project is not the Preview project");
  return { gitSha: git, schema };
}

function verifyMigrationHistory(config, schema, assert) {
  const listed = command(assert, "supabase", ["migration", "list", "--linked"], "REMOTE_MIGRATION_LIST_FAILED").combined;
  const rows = [...listed.matchAll(/^\s*(\d{14})\s*\|\s*(\d{14})\s*\|/gm)].map((match) => [match[1], match[2]]);
  const expected = schema.migrations.map((name) => name.split("_", 1)[0]);
  assert(rows.length === expected.length, "REMOTE_MIGRATIONS_MISMATCH", "remote migration count differs from local history");
  assert(rows.every(([local, remote], index) => local === expected[index] && remote === expected[index]), "REMOTE_MIGRATIONS_MISMATCH", "remote migration history differs from local history");
  const dryRun = command(assert, "supabase", ["db", "push", "--linked", "--dry-run"], "REMOTE_SCHEMA_DRY_RUN_FAILED").combined;
  assert(dryRun.includes("Remote database is up to date."), "REMOTE_SCHEMA_DRIFT", "remote database has pending migrations");
}

export function verifyVercelDeploymentRecord(inspected, deployment, gitSha, assert) {
  assert(inspected.target === "preview", "VERCEL_TARGET_MISMATCH", "deployment target is not Preview");
  assert(inspected.readyState === "READY", "VERCEL_NOT_READY", "deployment is not READY");
  assert(/^dpl_[A-Za-z0-9]+$/.test(inspected.id || ""), "VERCEL_DEPLOYMENT_ID_INVALID", "deployment ID is invalid");
  assert(deployment?.source === "cli", "VERCEL_DEPLOYMENT_SOURCE_MISMATCH", "Preview deployment was not created by the contracted CLI path");
  assert(Array.isArray(deployment?.env) && deployment.env.includes("VALUEHIRE_DEPLOY_SHA"), "VERCEL_RUNTIME_SHA_MISSING", "Preview deployment did not pin the application runtime SHA");
  const metadataSha = deployment?.meta?.gitCommitSha;
  assert(metadataSha === gitSha, "VERCEL_DEPLOYMENT_SHA_MISMATCH", "Vercel deployment metadata SHA differs from local HEAD");
  if (deployment?.meta?.commit_sha) {
    assert(deployment.meta.commit_sha === gitSha, "VERCEL_DEPLOYMENT_SHA_MISMATCH", "Vercel secondary SHA differs from local HEAD");
  }
  return inspected.id;
}

export function selectPreviousReadyPreviewDeployment(deployments, currentId, assert) {
  assert(Array.isArray(deployments), "PREVIEW_RECOVERY_LIST_INVALID", "Vercel Preview deployment list is invalid");
  const current = deployments.find((deployment) => deployment?.uid === currentId);
  assert(current && Number.isFinite(current.created), "PREVIEW_RECOVERY_CURRENT_MISSING", "current Preview deployment is absent from deployment history");
  const previous = deployments
    .filter((deployment) => (
      deployment?.uid !== currentId
      && deployment?.name === "valuehire-v6"
      && (deployment?.readyState === "READY" || deployment?.state === "READY")
      && deployment?.source === "cli"
      && Number.isFinite(deployment?.created)
      && deployment.created < current.created
      && typeof deployment?.url === "string"
      && /^[0-9a-f]{40}$/.test(deployment?.meta?.gitCommitSha || "")
    ))
    .sort((left, right) => right.created - left.created)[0];
  assert(previous, "PREVIEW_RECOVERY_TARGET_MISSING", "no previous healthy Preview deployment is available");
  return previous;
}

function verifyPreviewRecoveryContract(config, currentId, assert) {
  const help = spawnSync("vercel", ["rollback", "--help"], { cwd: REPO_ROOT, encoding: "utf8" });
  const helpText = `${help.stdout || ""}\n${help.stderr || ""}`;
  assert([0, 2].includes(help.status) && /vercel rollback url\|deploymentId/.test(helpText), "ROLLBACK_CLI_INVALID", "Vercel Production rollback command syntax is unavailable");
  const apiArgs = ["api", `/v6/deployments?projectId=${VERCEL_PROJECT_ID}&target=preview&limit=20`];
  if (config.vercelScope) apiArgs.push("--scope", config.vercelScope);
  const history = parseJson(assert, command(assert, "vercel", apiArgs, "PREVIEW_RECOVERY_LIST_FAILED").stdout, "PREVIEW_RECOVERY_LIST_INVALID", "Vercel Preview deployment history");
  const previous = selectPreviousReadyPreviewDeployment(history?.deployments, currentId, assert);
  const inspectArgs = ["inspect", `https://${previous.url}`];
  if (config.vercelScope) inspectArgs.push("--scope", config.vercelScope);
  inspectArgs.push("--json");
  const inspected = parseJson(assert, command(assert, "vercel", inspectArgs, "PREVIEW_RECOVERY_INSPECT_FAILED").stdout, "PREVIEW_RECOVERY_TARGET_INVALID", "Preview recovery target inspect");
  assert(inspected.id === previous.uid && inspected.target === "preview" && inspected.readyState === "READY", "PREVIEW_RECOVERY_TARGET_INVALID", "recovery target is not a healthy Preview deployment");
  const healthArgs = ["curl", "/api/health", "--deployment", `https://${previous.url}`];
  if (config.vercelScope) healthArgs.push("--scope", config.vercelScope);
  healthArgs.push("--", "--silent", "--show-error");
  const health = parseJson(
    assert,
    command(assert, "vercel", healthArgs, "PREVIEW_RECOVERY_HEALTH_FAILED").stdout,
    "PREVIEW_RECOVERY_HEALTH_INVALID",
    "Preview recovery health",
  );
  assert(
    health?.ok === true
      && health.environment === "preview"
      && health.commitSha === previous.meta.gitCommitSha
      && health.schemaDigest === config.expectedSchemaDigest
      && health.database === "reachable"
      && health.outbound?.sentCount === 0,
    "PREVIEW_RECOVERY_HEALTH_INVALID",
    "previous Preview deployment is not a healthy recovery target",
  );
  return previous.uid;
}

function verifyVercelDeployment(config, gitSha, assert) {
  const inspectArgs = ["inspect", config.baseUrl];
  if (config.vercelScope) inspectArgs.push("--scope", config.vercelScope);
  inspectArgs.push("--json");
  const inspected = parseJson(assert, command(assert, "vercel", inspectArgs, "VERCEL_INSPECT_FAILED").stdout, "VERCEL_INSPECT_INVALID", "vercel inspect");
  const apiArgs = ["api", `/v13/deployments/${inspected.id}`];
  if (config.vercelScope) apiArgs.push("--scope", config.vercelScope);
  const deployment = parseJson(assert, command(assert, "vercel", apiArgs, "VERCEL_METADATA_FAILED").stdout, "VERCEL_METADATA_INVALID", "vercel deployment metadata");
  const deploymentId = verifyVercelDeploymentRecord(inspected, deployment, gitSha, assert);
  verifyDeploymentSourceFiles(config, deploymentId, assert);
  return deploymentId;
}

function flattenSourceFiles(nodes, prefix = "", output = []) {
  if (!Array.isArray(nodes)) throw new Error("VERCEL_SOURCE_FILES_INVALID");
  for (const node of nodes) {
    const path = prefix ? `${prefix}/${node.name}` : node.name;
    if (node.type === "directory") flattenSourceFiles(node.children, path, output);
    if (node.type === "file") output.push([path, node.uid]);
  }
  return output;
}

export function verifyDeploymentSourceFileMap(remoteFiles, localFiles, assert) {
  const remote = [...remoteFiles].sort(([left], [right]) => left.localeCompare(right));
  const local = [...localFiles].sort(([left], [right]) => left.localeCompare(right));
  assert(JSON.stringify(remote.map(([path]) => path)) === JSON.stringify(local.map(([path]) => path)), "VERCEL_SOURCE_FILE_LIST_MISMATCH", "deployed source file list differs from the clean checkout");
  const localByPath = new Map(local);
  for (const [path, uid] of remote) {
    assert(uid === localByPath.get(path), "VERCEL_SOURCE_FILE_HASH_MISMATCH", `deployed source hash differs: ${path}`);
  }
}

function verifyDeploymentSourceFiles(config, deploymentId, assert) {
  const apiArgs = ["api", `/v6/deployments/${deploymentId}/files`];
  if (config.vercelScope) apiArgs.push("--scope", config.vercelScope);
  const tree = parseJson(assert, command(assert, "vercel", apiArgs, "VERCEL_SOURCE_FILES_FAILED").stdout, "VERCEL_SOURCE_FILES_INVALID", "Vercel deployment files");
  const source = Array.isArray(tree) ? tree.find((node) => node?.name === "src" && node?.type === "directory") : null;
  assert(source, "VERCEL_SOURCE_FILES_INVALID", "Vercel deployment omitted its source tree");
  const remoteFiles = flattenSourceFiles(source.children);
  const tracked = command(assert, "git", ["ls-files", "-z", "--", ...DEPLOYMENT_SOURCE_PATHS], "LOCAL_SOURCE_LIST_FAILED").stdout.split("\0").filter(Boolean);
  const localFiles = tracked.map((path) => [
    path,
    createHash("sha1").update(readFileSync(new URL(`../${path}`, import.meta.url))).digest("hex"),
  ]);
  verifyDeploymentSourceFileMap(remoteFiles, localFiles, assert);
  for (const [path, uid] of remoteFiles) {
    const contentArgs = ["api", `/v8/deployments/${deploymentId}/files/${uid}`];
    if (config.vercelScope) contentArgs.push("--scope", config.vercelScope);
    const payload = parseJson(
      assert,
      command(assert, "vercel", contentArgs, "VERCEL_SOURCE_CONTENT_FAILED").stdout,
      "VERCEL_SOURCE_CONTENT_INVALID",
      `Vercel deployed source content for ${path}`,
    );
    assert(typeof payload?.data === "string", "VERCEL_SOURCE_CONTENT_INVALID", `deployed source content is missing: ${path}`);
    const content = Buffer.from(payload.data, "base64");
    const contentHash = createHash("sha1").update(content).digest("hex");
    assert(contentHash === uid, "VERCEL_SOURCE_CONTENT_HASH_MISMATCH", `deployed source content hash differs: ${path}`);
    assert(content.equals(readFileSync(new URL(`../${path}`, import.meta.url))), "VERCEL_SOURCE_CONTENT_MISMATCH", `deployed source content differs from clean HEAD: ${path}`);
  }
}

function accessToken(assert) {
  const path = process.env.SUPABASE_ACCESS_TOKEN_FILE?.trim() || `${homedir()}/.supabase/access-token`;
  assert(existsSync(path), "SUPABASE_READONLY_TOKEN_MISSING", "Supabase read-only schema credential is unavailable");
  const token = readFileSync(path, "utf8").trim();
  assert(token.length > 0, "SUPABASE_READONLY_TOKEN_MISSING", "Supabase read-only schema credential is empty");
  return token;
}

export function verifyReviewEventServiceRoleGrants(grants, assert) {
  assert(
    JSON.stringify(grants) === JSON.stringify(["DELETE", "INSERT", "SELECT"]),
    "REMOTE_REVIEW_EVENT_GRANT_DRIFT",
    "remote review audit service_role privileges are not least-privilege exact",
  );
}

function verifyRemoteContract(contract, assert) {
  const expectedTables = TABLES.map((relname) => ({
    relname,
    relrowsecurity: true,
    relforcerowsecurity: ADMIN_TABLES.includes(relname),
  }));
  assert(JSON.stringify(contract.tables) === JSON.stringify(expectedTables), "REMOTE_RLS_DRIFT", "remote table RLS contract differs");
  assert(JSON.stringify(contract.columns) === JSON.stringify(EXPECTED_COLUMNS), "REMOTE_COLUMN_DRIFT", "remote columns or NOT NULL contract differs");
  assert(contract.constraints.length === EXPECTED_CONSTRAINTS.size, "REMOTE_CONSTRAINT_COUNT_DRIFT", "remote constraint count differs");
  for (const item of contract.constraints) {
    const expected = EXPECTED_CONSTRAINTS.get(item.conname);
    assert(expected && item.contype === expected[0] && expected[1].test(item.definition), "REMOTE_CONSTRAINT_DRIFT", `remote constraint differs: ${item.conname}`);
  }
  assert(contract.policies.length === 9, "REMOTE_POLICY_COUNT_DRIFT", "remote policy count differs");
  const policyByName = new Map(contract.policies.map((policy) => [policy.policyname, policy]));
  for (const table of ["admin_candidates", "admin_positions", ...LEGACY_TABLES]) {
    const policy = policyByName.get(`${table}_service_role`);
    assert(policy?.tablename === table && policy.cmd === "ALL" && JSON.stringify(policy.roles) === JSON.stringify(["service_role"]) && policy.qual === "true" && policy.with_check === "true", "REMOTE_POLICY_DRIFT", `remote policy differs: ${table}`);
  }
  const selectPolicy = policyByName.get("admin_review_events_service_role_select");
  assert(selectPolicy?.tablename === "admin_candidate_review_events" && selectPolicy.cmd === "SELECT" && selectPolicy.qual === "true" && selectPolicy.with_check === null, "REMOTE_POLICY_DRIFT", "review audit SELECT policy differs");
  const insertPolicy = policyByName.get("admin_review_events_service_role_insert");
  assert(insertPolicy?.tablename === "admin_candidate_review_events" && insertPolicy.cmd === "INSERT" && insertPolicy.qual === null && insertPolicy.with_check === "true", "REMOTE_POLICY_DRIFT", "review audit INSERT policy differs");
  const deletePolicy = policyByName.get("admin_review_events_service_role_delete_test");
  assert(deletePolicy?.tablename === "admin_candidate_review_events" && deletePolicy.cmd === "DELETE" && /E2E-TEST-%/.test(deletePolicy.qual || "") && deletePolicy.with_check === null, "REMOTE_POLICY_DRIFT", "review audit test cleanup policy differs");
  assert(contract.unsafe_grants.length === 0, "REMOTE_UNSAFE_GRANT", "remote schema grants access to a public application role");
  verifyReviewEventServiceRoleGrants(contract.review_event_service_role_grants, assert);
  assert(contract.triggers.length === 4, "REMOTE_TRIGGER_DRIFT", "remote trigger count differs");
  const triggerByName = new Map(contract.triggers.map((trigger) => [trigger.tgname, trigger]));
  assert(/BEFORE INSERT OR UPDATE/.test(triggerByName.get("admin_candidates_capture_review_event")?.definition || ""), "REMOTE_TRIGGER_DRIFT", "review audit capture trigger differs");
  assert(/BEFORE DELETE OR UPDATE/.test(triggerByName.get("admin_review_events_guard_mutation")?.definition || ""), "REMOTE_TRIGGER_DRIFT", "review audit mutation guard differs");
  for (const table of ["admin_candidates", "admin_positions"]) {
    assert(/BEFORE UPDATE/.test(triggerByName.get(`${table}_touch_updated_at`)?.definition || ""), "REMOTE_TRIGGER_DRIFT", `updated_at trigger differs: ${table}`);
  }
  assert(contract.sensitive_views.length === 0, "REMOTE_VIEW_DRIFT", "remote sensitive tables are exposed through a view");
  assert(JSON.stringify(contract.admin_functions) === JSON.stringify([
    { proname: "admin_capture_candidate_review_event", prosecdef: false, return_type: "trigger", proconfig: ["search_path=pg_catalog, public"], body_md5: "fc4044182ed579d128eb6576eae3a9ec" },
    { proname: "admin_guard_candidate_review_event", prosecdef: false, return_type: "trigger", proconfig: ["search_path=pg_catalog, public"], body_md5: "21906bc938d558a206a4ad3a0542b68b" },
    { proname: "admin_touch_updated_at", prosecdef: false, return_type: "trigger", proconfig: ["search_path=pg_catalog"], body_md5: "9b1889f56258bf9d6554213c05019c76" },
  ]), "REMOTE_FUNCTION_DRIFT", "remote admin function contract differs");
  assert(contract.unsafe_function_executes.length === 0, "REMOTE_UNSAFE_FUNCTION_EXECUTE", "remote admin functions grant EXECUTE to a public application role");
}

async function verifyRemoteSchema(config, assert) {
  const response = await fetch(`https://api.supabase.com/v1/projects/${config.previewRef}/database/query/read-only`, {
    method: "POST",
    headers: { authorization: `Bearer ${accessToken(assert)}`, "content-type": "application/json" },
    body: JSON.stringify({ query: REMOTE_SCHEMA_QUERY }),
  });
  assert(response.status === 201, "REMOTE_SCHEMA_QUERY_FAILED", `read-only remote schema query returned HTTP ${response.status}`);
  const payload = await response.json().catch(() => null);
  assert(Array.isArray(payload) && payload.length === 1 && payload[0]?.contract, "REMOTE_SCHEMA_RESPONSE_INVALID", "read-only remote schema query returned an invalid contract");
  verifyRemoteContract(payload[0].contract, assert);
  return createHash("sha256").update(JSON.stringify(payload[0].contract)).digest("hex");
}

async function verifyPasswordTokenRateLimit(config, assert) {
  const response = await fetch(`https://api.supabase.com/v1/projects/${config.previewRef}/config/auth`, {
    headers: { authorization: `Bearer ${accessToken(assert)}` },
  });
  assert(response.status === 200, "AUTH_RATE_LIMIT_QUERY_FAILED", `read-only Auth config query returned HTTP ${response.status}`);
  const payload = await response.json().catch(() => null);
  assert(
    Number.isInteger(payload?.rate_limit_token_refresh) && payload.rate_limit_token_refresh > 0,
    "PASSWORD_TOKEN_RATE_LIMIT_DISABLED",
    "Supabase /auth/v1/token limiter is not a positive integer",
  );
}

export function verifyReviewEventGuardResponse(status, payload, assert) {
  assert(status === 400, "REVIEW_AUDIT_GUARD_BYPASSED", "review audit UPDATE did not fail in the database");
  const message = typeof payload?.message === "string" ? payload.message : "";
  assert(/\b23514\b/.test(message), "REVIEW_AUDIT_GUARD_NOT_REACHED", "review audit UPDATE did not reach the check-violation trigger guard");
  assert(/review audit events are immutable/.test(message), "REVIEW_AUDIT_GUARD_NOT_REACHED", "review audit UPDATE did not reach the immutable trigger guard");
}

export async function proveReviewEventUpdateGuard(config, eventId, assert) {
  assert(/^[0-9a-f-]{36}$/.test(eventId), "REVIEW_AUDIT_EVENT_ID_INVALID", "review audit event ID is invalid");
  const response = await fetch(`https://api.supabase.com/v1/projects/${config.previewRef}/database/query`, {
    method: "POST",
    headers: { authorization: `Bearer ${accessToken(assert)}`, "content-type": "application/json" },
    body: JSON.stringify({
      query: `update public.admin_candidate_review_events set to_review_status = 'rejected' where tenant_id = '${config.tenantId}' and id = '${eventId}'`,
    }),
  });
  const payload = await response.json().catch(() => null);
  verifyReviewEventGuardResponse(response.status, payload, assert);
}

export async function verifyPreviewArtifacts(config, assert) {
  const { gitSha, schema } = verifyLocalArtifacts(config, assert);
  verifyMigrationHistory(config, schema, assert);
  const deploymentId = verifyVercelDeployment(config, gitSha, assert);
  const previousPreviewDeploymentId = verifyPreviewRecoveryContract(config, deploymentId, assert);
  const remoteSchemaFingerprint = await verifyRemoteSchema(config, assert);
  await verifyPasswordTokenRateLimit(config, assert);
  return { gitSha, schemaDigest: schema.combinedDigest, deploymentId, previousPreviewDeploymentId, remoteSchemaFingerprint };
}
