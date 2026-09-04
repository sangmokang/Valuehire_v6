#!/usr/bin/env node

import { readFileSync } from "node:fs";

const smokePath = process.env.VALUEHIRE_SMOKE_CONTRACT_PATH || "scripts/smoke-preview-admin.mjs";
const fixturePath = process.env.VALUEHIRE_SMOKE_FIXTURE_CONTRACT_PATH || "scripts/preview-smoke-fixtures.mjs";
const source = [
  readFileSync(smokePath, "utf8"),
  readFileSync("scripts/smoke-preview-admin-ui.py", "utf8"),
  readFileSync("scripts/preview-smoke-evidence.mjs", "utf8"),
  readFileSync(fixturePath, "utf8"),
].join("\n");

const required = [
  {
    name: "preview_production_ref_collision_guard",
    patterns: [
      /SMOKE_ENVIRONMENT_COLLISION/,
      /previewRef\s*===\s*productionRef/,
      /Preview and Production Supabase refs must differ/,
    ],
  },
  {
    name: "local_and_vercel_sha_binding",
    patterns: [
      /verifyPreviewArtifacts\(config,\s*assert\)/,
      /EXPECTED_SHA_NOT_CURRENT/,
      /VERCEL_DEPLOYMENT_SHA_MISMATCH/,
      /VERCEL_DEPLOYMENT_SOURCE_MISMATCH/,
      /VERCEL_RUNTIME_SHA_MISSING/,
      /VERCEL_TARGET_MISMATCH/,
      /LOCAL_GIT_DIRTY/,
    ],
  },
  {
    name: "rollback_syntax_and_preview_recovery_target",
    patterns: [
      /ROLLBACK_CLI_INVALID/,
      /selectPreviousReadyPreviewDeployment/,
      /PREVIEW_RECOVERY_TARGET_MISSING/,
      /PREVIEW_RECOVERY_TARGET_INVALID/,
      /PREVIEW_RECOVERY_HEALTH_INVALID/,
      /health\.commitSha === previous\.meta\.gitCommitSha/,
      /ROLLBACK_CLI_SYNTAX: PASS/,
      /PREVIOUS_HEALTHY_PREVIEW:/,
    ],
  },
  {
    name: "deployed_source_files_match_clean_head",
    patterns: [
      /\/v6\/deployments\/\$\{deploymentId\}\/files/,
      /\/v8\/deployments\/\$\{deploymentId\}\/files\/\$\{uid\}/,
      /createHash\("sha1"\)/,
      /verifyDeploymentSourceFileMap/,
      /VERCEL_SOURCE_FILE_LIST_MISMATCH/,
      /VERCEL_SOURCE_FILE_HASH_MISMATCH/,
      /VERCEL_SOURCE_CONTENT_HASH_MISMATCH/,
      /VERCEL_SOURCE_CONTENT_MISMATCH/,
      /DEPLOYED_SOURCE_FILES: PASS/,
    ],
  },
  {
    name: "remote_schema_history_binding",
    patterns: [
      /verifyMigrationHistory/,
      /REMOTE_MIGRATIONS_MISMATCH/,
      /REMOTE_SCHEMA_CONTRACT: PASS/,
      /Remote database is up to date\./,
    ],
  },
  {
    name: "local_digest_and_remote_catalog_binding",
    patterns: [
      /checkAdminSchemaContract/,
      /EXPECTED_SCHEMA_NOT_CURRENT/,
      /database\/query\/read-only/,
      /REMOTE_CONSTRAINT_DRIFT/,
      /pipeline_members/,
      /pipeline_comments:author_email:text:NO/,
      /pipeline_members:user_email:text:NO/,
      /sensitive_views/,
      /REMOTE_RLS_DRIFT/,
      /body_md5/,
    ],
  },
  {
    name: "preview_requires_deployment_protection",
    patterns: [
      /await provePreviewAccessRestricted\(config\)/,
      /PREVIEW_PROTECTION_PATHS = \["\/admin", "\/api\/health"\]/,
      /PREVIEW_ACCESS_PUBLIC/,
      /assert\(redirectedToVercel/,
      /hostname === "vercel\.com"/,
      /VERCEL_DEPLOYMENT_PROTECTED: PASS/,
      /PREVIEW_ACCESS_RESTRICTED: PASS/,
    ],
  },
  {
    name: "public_sensitive_paths_are_not_static",
    patterns: [
      /publicSensitivePaths/,
      /PUBLIC_STATIC_EXPOSED/,
      /\/server\/admin\/auth\.js/,
      /\/supabase\/migrations\/20260904000100_admin_walking_skeleton\.sql/,
    ],
  },
  {
    name: "deployed_security_headers_are_verified",
    patterns: [
      /await proveSecurityHeaders\(config\)/,
      /SECURITY_HEADER_PATHS/,
      /content-security-policy/,
      /DEPLOYED_CSP_MISSING/,
      /DEPLOYED_CSP_MISMATCH/,
      /DEPLOYED_CSP_UNSAFE/,
      /DEPLOYED_HSTS_MISMATCH/,
      /DEPLOYED_SECURITY_HEADERS: PASS/,
    ],
  },
  {
    name: "unauthenticated_candidates_fail_closed",
    patterns: [
      /\/api\/admin\/candidates/,
      /,\s*401\s*\)/,
      /AUTH_REQUIRED/,
      /AUTH_ERROR_HIDDEN/,
    ],
  },
  {
    name: "exact_one_candidate_isolation",
    patterns: [
      /candidates\.length\s*===\s*1/,
      /FIXTURE_NOT_ISOLATED/,
      /WRONG_CANDIDATE/,
      /POSITION_LINK_MISSING/,
    ],
  },
  {
    name: "negative_authentication_cases",
    patterns: [
      /expectLoginFailure/,
      /AUTH_INVALID/,
      /AUTH_FORBIDDEN/,
      /CSRF_REJECTED/,
      /FAILED_LOGIN_SET_COOKIE/,
    ],
  },
  {
    name: "provider_password_token_rate_limit_is_enabled",
    patterns: [
      /config\/auth/,
      /rate_limit_token_refresh/,
      /PASSWORD_TOKEN_RATE_LIMIT: PASS/,
    ],
  },
  {
    name: "foreign_tenant_is_hidden",
    patterns: [
      /foreignCandidateId/,
      /,\s*404,\s*\)/,
      /NOT_FOUND/,
      /TENANT_BOUNDARY_HIDDEN/,
    ],
  },
  {
    name: "new_session_persistent_readback",
    patterns: [
      /runUiWorkflow\(config,\s*fixture\)/,
      /browser\.new_context/,
      /page\.reload/,
      /LOGGED_OUT_SESSION_REUSABLE/,
      /LOGGED_OUT_SESSION_REJECTED: PASS/,
      /READBACK_MISMATCH/,
      /NEW_SESSION_READBACK: PASS/,
    ],
  },
  {
    name: "atomic_review_audit_and_cleanup",
    patterns: [
      /await proveReviewAudit\(config,\s*fixture\)/,
      /admin_candidate_review_events/,
      /REVIEW_AUDIT_CARDINALITY/,
      /REVIEW_AUDIT_ACTOR_MISMATCH/,
      /REVIEW_AUDIT_TRANSIENT_ACTOR_RETAINED/,
      /REVIEW_AUDIT_REST_UPDATE_ALLOWED/,
      /\[\s*403\s*\]/,
      /restMutation\?\.code\s*===\s*["']42501["']/,
      /await proveReviewEventUpdateGuard\(config, event\.id, assert\)/,
      /REVIEW_AUDIT_GUARD_BYPASSED/,
      /REVIEW_AUDIT_GUARD_NOT_REACHED/,
      /REVIEW_AUDIT_REST_UPDATE_DENIED: PASS/,
      /REVIEW_AUDIT_TRIGGER_UPDATE_GUARD: PASS/,
      /proveReviewEventsAbsent/,
      /REVIEW_AUDIT_EVENT: PASS/,
    ],
  },
  {
    name: "deployed_browser_ui_workflow",
    patterns: [
      /smoke-preview-admin-ui\.py/,
      /LOGIN_SCREEN: PASS/,
      /CANDIDATE_CARD: 1/,
      /STATUS_UPDATE: PASS/,
      /BROWSER_UI_WORKFLOW: PASS/,
      /BROWSER_EXTERNAL_REQUESTS: 0/,
    ],
  },
  {
    name: "cleanup_absence_proof",
    patterns: [
      /cleanupPreviewFixtures/,
      /\$\{label\}-absence/,
      /=>\s*proveRowAbsent\(config,\s*request,\s*assert,\s*table,\s*id,\s*label\)/,
      /\$\{prefix\}-auth-absence/,
      /CLEANUP_INCOMPLETE/,
      /cleanup_target_ids=/,
      /DATA_CLEANUP: PASS/,
      /AUTH_CLEANUP: PASS/,
    ],
  },
  {
    name: "external_sends_zero",
    patterns: [
      /OUTBOUND_ENABLED/,
      /OUTBOUND_ACTIVITY/,
      /sentCount\s*===\s*0/,
      /EXTERNAL_SENDS: 0/,
    ],
  },
  {
    name: "typed_error_and_conflict_checks",
    patterns: [
      /VALIDATION_FAILED/,
      /VALIDATION_ERROR_HIDDEN/,
      /,\s*409,\s*\)/,
      /VERSION_CONFLICT/,
      /CONFLICT_HIDDEN/,
    ],
  },
  {
    name: "non_json_and_secret_fail_closed",
    patterns: [
      /NON_JSON_RESPONSE/,
      /SENSITIVE_RESPONSE/,
      /SERVICE_KEY_EXPOSED/,
      /ANON_KEY_EXPOSED/,
    ],
  },
];

function assertPattern(contract, pattern) {
  if (!pattern.test(source)) {
    throw new Error(`${contract.name} missing ${pattern}`);
  }
}

function main() {
  const failures = [];
  for (const contract of required) {
    for (const pattern of contract.patterns) {
      try {
        assertPattern(contract, pattern);
      } catch (error) {
        failures.push(error.message);
      }
    }
  }
  if (failures.length > 0) {
    process.stdout.write(`VERDICT: FAIL\nCHECKED: ${required.length}\nFAILURES: ${failures.length}\n${failures.join("\n")}\n`);
    process.exit(1);
  }
  process.stdout.write(`VERDICT: PASS\nSTATIC_CONTRACTS: ${required.length}\n`);
}

main();
