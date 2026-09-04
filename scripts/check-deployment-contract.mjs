#!/usr/bin/env node

import { existsSync, readFileSync } from "node:fs";
import { checkAdminSchemaContract } from "./check-admin-schema.mjs";

const EXPECTED_SCHEMA_DIGEST = "14e3755595b5804f5059dd0a455f0c8a38ef3106d18b53555fa0c56e47868089";
const REQUIRED_ENV = [
  "VALUEHIRE_ENV",
  "VALUEHIRE_PUBLIC_URL",
  "VALUEHIRE_DEPLOY_SHA",
  "VALUEHIRE_SCHEMA_DIGEST",
  "VALUEHIRE_SUPABASE_URL",
  "VALUEHIRE_SUPABASE_ANON_KEY",
  "VALUEHIRE_SUPABASE_SERVICE_ROLE_KEY",
  "VALUEHIRE_ADMIN_EMAIL_SHA256",
  "VALUEHIRE_TENANT_ID",
];

function readText(path) {
  if (!existsSync(path)) throw new Error(`missing_file:${path}`);
  return readFileSync(path, "utf8");
}

function addIfMissing(errors, label, condition) {
  if (!condition) errors.push(label);
}

export function checkDeploymentContract({ env = process.env, requireCurrentEnv = false } = {}) {
  const errors = [];
  const warnings = [];
  const pkg = JSON.parse(readText("package.json"));
  const lock = JSON.parse(readText("package-lock.json"));
  const vercel = readText("vercel.json");
  const vercelIgnore = readText(".vercelignore");
  const previewDeploy = readText("scripts/deploy-preview.sh");
  const staticVerifier = readText("scripts/verify-production-admin-static.mjs");
  const productionSmoke = readText("scripts/smoke-production-readonly.mjs");
  const productionReadonlyContract = readText("scripts/production-readonly-contract.mjs");
  const productionRollback = readText("scripts/verify-production-rollback.mjs");
  const previewSmoke = readText("scripts/smoke-preview-admin.mjs");
  const mutationHarness = readText("scripts/mutate-production-admin-behavior.mjs");
  const acceptance = readText("scripts/acceptance-production-walking-skeleton.sh");
  const workflow = readText(".github/workflows/verify.yml");
  const serverConfig = readText("server/admin/config.js");
  const schema = checkAdminSchemaContract();

  addIfMissing(errors, "package_missing_acceptance_script", pkg.scripts?.["acceptance:production-walking-skeleton"]);
  addIfMissing(errors, "package_missing_preview_deploy_script", pkg.scripts?.["deploy:preview"] === "bash scripts/deploy-preview.sh");
  addIfMissing(errors, "package_missing_production_audit_script", pkg.scripts?.["audit:production"] === "npm audit --omit=dev --audit-level=high");
  addIfMissing(errors, "package_lock_invalid", lock.lockfileVersion === 3 && lock.packages?.[""]?.name === pkg.name);
  addIfMissing(errors, "package_missing_production_readonly_smoke", pkg.scripts?.["smoke:production-readonly"]);
  addIfMissing(errors, "package_missing_production_rollback_verifier", pkg.scripts?.["verify:production-rollback-readonly"] === "node scripts/verify-production-rollback.mjs");
  addIfMissing(errors, "vercel_output_directory_missing", vercel.includes('"outputDirectory": "apps/production-admin"'));
  addIfMissing(errors, "vercel_admin_rewrite_missing", vercel.includes('"source": "/admin"') && vercel.includes('"destination": "/index.html"'));
  addIfMissing(errors, "vercel_csp_missing", vercel.includes("Content-Security-Policy"));
  addIfMissing(errors, "vercelignore_root_deny_missing", vercelIgnore.includes("/*"));
  addIfMissing(errors, "vercelignore_api_missing", vercelIgnore.includes("!api/**"));
  addIfMissing(errors, "vercelignore_admin_app_missing", vercelIgnore.includes("!apps/production-admin/**"));
  addIfMissing(errors, "vercelignore_server_missing", vercelIgnore.includes("server/*") && vercelIgnore.includes("!server/admin/**"));
  addIfMissing(errors, "vercelignore_admin_package_excluded", vercelIgnore.includes("apps/production-admin/package.json"));
  addIfMissing(errors, "vercelignore_must_not_allow_docs", !vercelIgnore.includes("!docs"));
  addIfMissing(errors, "vercelignore_must_not_allow_supabase", !vercelIgnore.includes("!supabase"));
  addIfMissing(errors, "vercelignore_must_not_allow_scripts_tree", !vercelIgnore.includes("!scripts/**"));
  addIfMissing(errors, "static_verifier_schema_digest_missing", staticVerifier.includes(EXPECTED_SCHEMA_DIGEST));
  addIfMissing(errors, "static_verifier_missing_session_inventory", staticVerifier.includes("api") && staticVerifier.includes("server/admin"));
  addIfMissing(errors, "static_verifier_must_recurse", staticVerifier.includes("function walk(") && staticVerifier.includes("walk(outputDirectory)") && staticVerifier.includes("deploymentRoots.flatMap"));
  addIfMissing(errors, "static_verifier_missing_changed_file_budget", staticVerifier.includes("verifyChangedFileBudgets") && staticVerifier.includes("changed file exceeds 600-line budget") && staticVerifier.includes("BUDGET_FILES"));
  const previewEvidence = readText("scripts/preview-smoke-evidence.mjs");
  addIfMissing(errors, "preview_smoke_must_probe_static_exposure", previewSmoke.includes("PUBLIC_STATIC_EXPOSED") && previewEvidence.includes("/supabase/migrations/"));
  addIfMissing(errors, "preview_smoke_must_bind_deployment_meta", previewSmoke.includes("verifyPreviewArtifacts") && previewEvidence.includes("VERCEL_DEPLOYMENT_SHA_MISMATCH") && previewEvidence.includes("VERCEL_DEPLOYMENT_SOURCE_MISMATCH") && previewEvidence.includes("VERCEL_RUNTIME_SHA_MISSING") && previewEvidence.includes("/v13/deployments/"));
  addIfMissing(errors, "preview_smoke_must_require_clean_local_head", previewEvidence.includes("LOCAL_GIT_DIRTY") && previewEvidence.includes("--untracked-files=all"));
  addIfMissing(errors, "preview_smoke_must_validate_rollback_syntax_and_recovery_target", previewEvidence.includes("ROLLBACK_CLI_INVALID") && previewEvidence.includes("selectPreviousReadyPreviewDeployment") && previewEvidence.includes("PREVIEW_RECOVERY_TARGET_MISSING") && previewEvidence.includes("PREVIEW_RECOVERY_HEALTH_INVALID") && previewEvidence.includes("health.commitSha === previous.meta.gitCommitSha") && previewSmoke.includes("ROLLBACK_CLI_SYNTAX: PASS") && previewSmoke.includes("PREVIOUS_HEALTHY_PREVIEW:"));
  addIfMissing(errors, "preview_smoke_must_match_deployed_source_content", previewEvidence.includes("/v6/deployments/${deploymentId}/files") && previewEvidence.includes("/v8/deployments/${deploymentId}/files/${uid}") && previewEvidence.includes('createHash("sha1")') && previewEvidence.includes("verifyDeploymentSourceFileMap") && previewEvidence.includes("VERCEL_SOURCE_FILE_LIST_MISMATCH") && previewEvidence.includes("VERCEL_SOURCE_FILE_HASH_MISMATCH") && previewEvidence.includes("VERCEL_SOURCE_CONTENT_HASH_MISMATCH") && previewEvidence.includes("VERCEL_SOURCE_CONTENT_MISMATCH") && previewSmoke.includes("DEPLOYED_SOURCE_FILES: PASS"));
  addIfMissing(errors, "preview_smoke_must_check_remote_migrations", previewSmoke.includes("verifyPreviewArtifacts") && previewEvidence.includes("REMOTE_MIGRATIONS_MISMATCH") && previewEvidence.includes("Remote database is up to date."));
  addIfMissing(errors, "preview_smoke_must_check_remote_catalog_readonly", previewEvidence.includes("database/query/read-only") && previewEvidence.includes("REMOTE_CONSTRAINT_DRIFT") && previewEvidence.includes("REMOTE_UNSAFE_GRANT") && previewEvidence.includes("review_event_service_role_grants") && previewEvidence.includes("REMOTE_REVIEW_EVENT_GRANT_DRIFT"));
  addIfMissing(errors, "preview_smoke_must_cover_legacy_pii_catalog", previewEvidence.includes("pipeline_candidates") && previewEvidence.includes("pipeline_comments") && previewEvidence.includes("pipeline_members") && previewEvidence.includes("pipeline_stage_history") && previewEvidence.includes("sensitive_views"));
  addIfMissing(errors, "preview_smoke_must_hash_admin_function_bodies", previewEvidence.includes("md5(p.prosrc)") && previewEvidence.includes("21906bc938d558a206a4ad3a0542b68b"));
  addIfMissing(errors, "preview_smoke_must_require_vercel_access_protection", previewSmoke.includes("provePreviewAccessRestricted") && previewSmoke.includes("assert(redirectedToVercel") && previewSmoke.includes("PREVIEW_ACCESS_PUBLIC") && previewSmoke.includes("VERCEL_DEPLOYMENT_PROTECTED: PASS"));
  addIfMissing(errors, "preview_smoke_must_exercise_audit_trigger_guard", previewSmoke.includes("proveReviewEventUpdateGuard(config, event.id, assert)") && previewEvidence.includes("/database/query") && previewEvidence.includes("REVIEW_AUDIT_GUARD_BYPASSED") && previewEvidence.includes("REVIEW_AUDIT_GUARD_NOT_REACHED") && previewSmoke.includes("REVIEW_AUDIT_TRIGGER_UPDATE_GUARD: PASS"));
  addIfMissing(errors, "server_config_must_bind_vercel_runtime", serverConfig.includes("VERCEL_GIT_COMMIT_SHA") && serverConfig.includes("VERCEL_ENV") && serverConfig.includes("Vercel deployment SHA mismatch") && serverConfig.includes("Production requires Vercel Git provenance"));
  addIfMissing(errors, "preview_deploy_must_bind_clean_head", previewDeploy.includes("git status --porcelain") && previewDeploy.includes("git rev-parse HEAD") && previewDeploy.includes("VALUEHIRE_DEPLOY_SHA differs from HEAD"));
  addIfMissing(errors, "preview_deploy_must_pin_vercel_project", previewDeploy.includes("prj_isTeytMDr2EiXW5hg5rv4wPdyBW5") && previewDeploy.includes("team_NB0uDciuQYLf5akFKK7Sb3pU") && previewDeploy.includes('projectName !== "valuehire-v6"'));
  addIfMissing(errors, "preview_deploy_must_pin_app_sha_without_overriding_system_provenance", previewDeploy.includes('--env "VALUEHIRE_DEPLOY_SHA=$deploy_sha"') && !previewDeploy.includes('--env "VERCEL_GIT_COMMIT_SHA=$deploy_sha"'));
  addIfMissing(errors, "preview_deploy_must_target_preview_only", previewDeploy.includes("--target preview") && !previewDeploy.includes("--prod"));
  addIfMissing(errors, "behavior_mutation_harness_missing", pkg.scripts?.["mutate:production-admin"] && mutationHarness.includes("candidate_route_auth_gate_removed") && mutationHarness.includes("session_local_lifetime_guard_removed") && mutationHarness.includes("review_update_status_guard_removed") && mutationHarness.includes("SURVIVORS: 0"));
  addIfMissing(errors, "acceptance_missing_behavior_mutation", acceptance.includes("mutate-production-admin-behavior.mjs"));
  addIfMissing(errors, "production_smoke_must_be_readonly", productionSmoke.includes("writesAttempted") && !/method:\s*['\"](?:POST|PATCH|PUT|DELETE)['\"]/.test(productionSmoke));
  addIfMissing(errors, "production_rollback_verifier_must_be_readonly_and_fail_closed", productionRollback.includes('["rollback", "--help"]') && productionRollback.includes("/v13/deployments/${id}") && productionRollback.includes("/v7/deployments?projectId=") && productionRollback.includes("target=production&state=READY&rollbackCandidate=true") && productionRollback.includes("isRollbackCandidate") && productionRollback.includes("deployment.target === \"production\"") && productionRollback.includes("deploymentProjectId(currentDeployment) === EXPECTED_VERCEL_PROJECT_ID") && productionRollback.includes("PRODUCTION_BASE_URL or PRODUCTION_DEPLOYMENT_ID is required") && productionRollback.includes("PRODUCTION_ROLLBACK_CANDIDATE_MISSING") && productionRollback.includes("ROLLBACK_CLI_SYNTAX: PASS") && productionRollback.includes("WRITES_ATTEMPTED: 0") && !/rollback\", \[(?!\"--help\")/.test(productionRollback));
  addIfMissing(errors, "production_smoke_must_require_sha", productionSmoke.includes("missing_VALUEHIRE_DEPLOY_SHA") && !productionSmoke.includes("expectedSha &&"));
  addIfMissing(errors, "production_smoke_must_require_schema_digest", productionSmoke.includes("missing_VALUEHIRE_SCHEMA_DIGEST") && !productionSmoke.includes("VALUEHIRE_SCHEMA_DIGEST ||"));
  addIfMissing(errors, "production_smoke_must_require_readonly_cookie", productionReadonlyContract.includes("missing_PRODUCTION_READONLY_COOKIE"));
  addIfMissing(errors, "production_smoke_must_check_15m_cookie_and_token_expiry", productionSmoke.includes("validateReadonlyCredential") && productionSmoke.includes("PRODUCTION_READONLY_COOKIE_EXPIRES_AT") && productionReadonlyContract.includes("production_readonly_cookie_ttl_exceeds_15_minutes") && productionReadonlyContract.includes("production_readonly_access_token_expired") && productionReadonlyContract.includes("production_readonly_access_token_ttl_exceeds_60_minutes"));
  addIfMissing(errors, "acceptance_missing_preview_smoke_contract", acceptance.includes("check-preview-smoke-contract.mjs"));
  addIfMissing(errors, "acceptance_missing_production_audit", acceptance.includes("npm run audit:production --silent"));
  addIfMissing(errors, "acceptance_must_not_recurse_session_status", !acceptance.includes("session-status.sh"));
  addIfMissing(errors, "ci_missing_walking_skeleton_acceptance", workflow.includes("acceptance-production-walking-skeleton.sh"));
  for (const name of REQUIRED_ENV) {
    addIfMissing(errors, `server_config_missing_env:${name}`, serverConfig.includes(name));
    if (!env[name]) warnings.push(`missing_current_env:${name}`);
  }
  addIfMissing(errors, "schema_migration_count_not_6", schema.checkedMigrations === 6);
  addIfMissing(errors, `schema_digest_mismatch:${schema.combinedDigest}`, schema.combinedDigest === EXPECTED_SCHEMA_DIGEST);
  for (const error of schema.errors) errors.push(`schema_contract:${error}`);
  if (env.VALUEHIRE_SCHEMA_DIGEST && env.VALUEHIRE_SCHEMA_DIGEST !== EXPECTED_SCHEMA_DIGEST) {
    errors.push(`current_env_schema_digest_mismatch:${env.VALUEHIRE_SCHEMA_DIGEST}`);
  }
  if (requireCurrentEnv && warnings.length) {
    errors.push(`missing_required_current_env:${warnings.join(",")}`);
  }
  return {
    ok: errors.length === 0,
    errors,
    warnings,
    migrationFiles: schema.migrations,
    schemaDigest: schema.combinedDigest,
    expectedSchemaDigest: EXPECTED_SCHEMA_DIGEST,
    currentEnvValidation: requireCurrentEnv ? (warnings.length ? "FAIL" : "PASS") : "NOT_RUN",
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const requireCurrentEnv = process.argv.includes("--require-current-env");
  const result = checkDeploymentContract({ requireCurrentEnv });
  console.log(`${requireCurrentEnv ? "VERDICT" : "STATIC_CONTRACT"}: ${result.ok ? "PASS" : "FAIL"}`);
  console.log(`migrations=${result.migrationFiles.length}`);
  console.log(`schema_digest=${result.schemaDigest}`);
  console.log(`expected_schema_digest=${result.expectedSchemaDigest}`);
  console.log(`current_env_validation=${result.currentEnvValidation}`);
  if (process.argv.includes("--require-current-env")) {
    for (const warning of result.warnings) console.log(`warning=${warning}`);
  }
  for (const error of result.errors) console.log(`error=${error}`);
  process.exit(result.ok ? 0 : 1);
}
