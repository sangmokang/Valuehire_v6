#!/usr/bin/env node

import { createHash, randomBytes, randomUUID } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  proveReviewEventUpdateGuard,
  publicSensitivePaths,
  verifyPreviewArtifacts,
} from "./preview-smoke-evidence.mjs";
import {
  cleanupPreviewFixtures,
  createPreviewFixtures,
} from "./preview-smoke-fixtures.mjs";

const REVIEWED_STATUS = "reviewed";
const SECURITY_HEADER_PATHS = ["/admin", "/admin/ui.js", "/admin/styles.css", "/api/health"];
const PREVIEW_PROTECTION_PATHS = ["/admin", "/api/health"];
const REQUIRED_CSP_DIRECTIVES = [
  "default-src 'self'",
  "connect-src 'self'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self'",
  "object-src 'none'",
  "base-uri 'none'",
  "frame-ancestors 'none'",
  "form-action 'self'",
];
const SENSITIVE_PATTERNS = [
  /service[_-]?role/i,
  /refresh[_-]?token/i,
  /access[_-]?token/i,
  /authorization/i,
  /password/i,
  /candidate[_-]?email/i,
];

class SmokeFailure extends Error {
  constructor(code, message) {
    super(message);
    this.name = "SmokeFailure";
    this.code = code;
  }
}

function requiredEnv(name) {
  const value = process.env[name]?.trim();
  if (!value) {
    throw new SmokeFailure("SMOKE_CONFIG_INVALID", `${name} is required`);
  }
  return value;
}

function loadConfig() {
  const baseUrl = new URL(requiredEnv("VALUEHIRE_SMOKE_BASE_URL"));
  const supabaseUrl = new URL(requiredEnv("VALUEHIRE_SMOKE_SUPABASE_URL"));
  const tenantId = requiredEnv("VALUEHIRE_SMOKE_TENANT_ID");
  const expectedSha = requiredEnv("VALUEHIRE_SMOKE_EXPECTED_SHA");

  if (baseUrl.protocol !== "https:" || supabaseUrl.protocol !== "https:") {
    throw new SmokeFailure("SMOKE_CONFIG_INVALID", "Preview origins must use HTTPS");
  }
  if (!/^E2E-TEST-[A-Z0-9-]+$/.test(tenantId)) {
    throw new SmokeFailure("SMOKE_CONFIG_INVALID", "tenant must start with E2E-TEST-");
  }
  if (!/^[0-9a-f]{40}$/.test(expectedSha)) {
    throw new SmokeFailure("SMOKE_CONFIG_INVALID", "expected SHA must be 40 lowercase hex characters");
  }

  const previewRef = supabaseUrl.hostname.split(".")[0];
  const productionRef = requiredEnv("VALUEHIRE_SMOKE_PRODUCTION_SUPABASE_REF");
  if (!previewRef || previewRef === productionRef) {
    throw new SmokeFailure("SMOKE_ENVIRONMENT_COLLISION", "Preview and Production Supabase refs must differ");
  }

  return {
    baseUrl: baseUrl.origin,
    supabaseUrl: supabaseUrl.origin,
    previewRef,
    previewRefFingerprint: createHash("sha256").update(previewRef).digest("hex").slice(0, 12),
    productionRef,
    tenantId,
    expectedSha,
    expectedSchemaDigest: requiredEnv("VALUEHIRE_SMOKE_EXPECTED_SCHEMA_DIGEST"),
    anonKey: requiredEnv("VALUEHIRE_SMOKE_SUPABASE_ANON_KEY"),
    serviceRoleKey: requiredEnv("VALUEHIRE_SMOKE_SUPABASE_SERVICE_ROLE_KEY"),
    protectionBypass: process.env.VERCEL_AUTOMATION_BYPASS_SECRET?.trim() || "",
    protectionCookie: "",
    useVercelCurl: process.env.VALUEHIRE_SMOKE_VERCEL_CURL === "1",
    vercelScope: requiredEnv("VALUEHIRE_SMOKE_VERCEL_SCOPE"),
  };
}

function assert(condition, code, message) {
  if (!condition) {
    throw new SmokeFailure(code, message);
  }
}

function safeJson(value) {
  const serialized = JSON.stringify(value);
  for (const pattern of SENSITIVE_PATTERNS) {
    assert(!pattern.test(serialized), "SENSITIVE_RESPONSE", `response matched forbidden pattern ${pattern}`);
  }
  return serialized;
}

function previewHeaders(config, extra = {}) {
  const headers = { ...extra };
  if (config.protectionBypass) {
    headers["x-vercel-protection-bypass"] = config.protectionBypass;
  }
  if (config.protectionCookie) {
    headers.cookie = [headers.cookie, config.protectionCookie].filter(Boolean).join("; ");
  }
  return headers;
}

function readNetscapeCookie(file) {
  for (const line of readFileSync(file, "utf8").split(/\r?\n/)) {
    if (!line || (line.startsWith("#") && !line.startsWith("#HttpOnly_"))) continue;
    const fields = line.split("\t");
    if (fields.length >= 7 && fields[5] === "_vercel_jwt" && fields[6]) {
      return `${fields[5]}=${fields[6]}`;
    }
  }
  return "";
}

function bootstrapProtectionCookie(config) {
  if (!config.useVercelCurl || config.protectionBypass) return "";
  const directory = mkdtempSync(join(tmpdir(), "valuehire-vercel-bypass-"));
  const cookieFile = join(directory, "cookies.txt");
  const args = ["curl", "/api/health", "--deployment", config.baseUrl];
  if (config.vercelScope) args.push("--scope", config.vercelScope);
  args.push(
    "--",
    "--silent",
    "--show-error",
    "--cookie-jar",
    cookieFile,
    "--output",
    "/dev/null",
    "--header",
    "x-vercel-set-bypass-cookie: true",
  );
  try {
    const result = spawnSync("vercel", args, { encoding: "utf8" });
    assert(result.status === 0, "VERCEL_BYPASS_FAILED", "vercel curl could not establish automation access");
    const cookie = readNetscapeCookie(cookieFile);
    assert(cookie, "VERCEL_BYPASS_FAILED", "vercel curl did not return a bypass cookie");
    return cookie;
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

async function readJson(response) {
  const body = await response.text();
  if (!body) return null;
  try {
    return JSON.parse(body);
  } catch (error) {
    if (!error) throw error;
    throw new SmokeFailure("NON_JSON_RESPONSE", `expected JSON from ${response.url}, got HTTP ${response.status}`);
  }
}

async function expectJson(config, path, options, expectedStatus) {
  const response = await fetch(`${config.baseUrl}${path}`, {
    redirect: "manual",
    ...options,
    headers: previewHeaders(config, options?.headers),
  });
  const body = await readJson(response);
  assert(
    response.status === expectedStatus,
    "UNEXPECTED_HTTP_STATUS",
    `${options?.method || "GET"} ${path} returned ${response.status}, expected ${expectedStatus}`,
  );
  safeJson(body);
  return { response, body };
}

async function supabaseRequest(config, path, options = {}, expectedStatuses = [200]) {
  const response = await fetch(`${config.supabaseUrl}${path}`, {
    ...options,
    headers: {
      apikey: config.serviceRoleKey,
      authorization: `Bearer ${config.serviceRoleKey}`,
      "content-type": "application/json",
      ...options.headers,
    },
  });
  const text = await response.text();
  let body = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch (error) {
      if (!error) throw error;
      body = text;
    }
  }
  assert(
    expectedStatuses.includes(response.status),
    "SUPABASE_REQUEST_FAILED",
    `Supabase ${options.method || "GET"} ${path.split("?")[0]} returned ${response.status}`,
  );
  return body;
}

function cookieHeader(response) {
  const setCookies = typeof response.headers.getSetCookie === "function"
    ? response.headers.getSetCookie()
    : [response.headers.get("set-cookie")].filter(Boolean);
  assert(setCookies.length > 0, "SESSION_COOKIE_MISSING", "login did not set a session cookie");

  const joined = setCookies.join("\n");
  for (const attribute of ["HttpOnly", "Secure", "SameSite=Lax"]) {
    assert(joined.includes(attribute), "SESSION_COOKIE_WEAK", `session cookie is missing ${attribute}`);
  }

  return setCookies.map((item) => item.split(";", 1)[0]).join("; ");
}

function runUiWorkflow(config, fixture) {
  const result = spawnSync("python3", ["scripts/smoke-preview-admin-ui.py"], {
    cwd: process.cwd(),
    encoding: "utf8",
    input: JSON.stringify({
      base_url: config.baseUrl,
      email: fixture.adminEmail,
      password: fixture.adminPassword,
      protection_cookie: config.protectionCookie,
      protection_bypass: config.protectionBypass,
    }),
  });
  assert(result.status === 0, "UI_SMOKE_FAILED", "headless browser workflow did not complete");
  const output = result.stdout || "";
  for (const proof of [
    "UI_SMOKE: PASS",
    "LOGIN_SCREEN: PASS",
    "CANDIDATE_CARD: 1",
    "STATUS_UPDATE: PASS",
    "PAGE_RELOAD: PASS",
    "NEW_BROWSER_SESSION: PASS",
    "BROWSER_EXTERNAL_REQUESTS: 0",
  ]) {
    assert(output.includes(proof), "UI_SMOKE_EVIDENCE_MISSING", `browser workflow omitted ${proof}`);
  }
}

async function login(config, email, password) {
  const { response, body } = await expectJson(
    config,
    "/api/admin/auth/login",
    {
      method: "POST",
      headers: { "content-type": "application/json", origin: config.baseUrl },
      body: JSON.stringify({ email, password }),
    },
    200,
  );
  assert(body?.ok === true, "LOGIN_CONTRACT_INVALID", "login body did not report ok=true");
  assert(Object.keys(body).length === 1, "LOGIN_RESPONSE_OVEREXPOSED", "login response exposed unexpected fields");
  return cookieHeader(response);
}

async function expectLoginFailure(config, email, password, expectedStatus, expectedCode, includeOrigin = true) {
  const headers = { "content-type": "application/json" };
  if (includeOrigin) headers.origin = config.baseUrl;
  const { response, body } = await expectJson(
    config,
    "/api/admin/auth/login",
    { method: "POST", headers, body: JSON.stringify({ email, password }) },
    expectedStatus,
  );
  assert(body?.error?.code === expectedCode, "AUTH_FAILURE_HIDDEN", `login did not return ${expectedCode}`);
  assert(!response.headers.get("set-cookie"), "FAILED_LOGIN_SET_COOKIE", "failed login set a session cookie");
}

async function logout(config, cookie) {
  const { response, body } = await expectJson(
    config,
    "/api/admin/auth/session",
    {
      method: "DELETE",
      headers: { cookie, origin: config.baseUrl },
    },
    200,
  );
  assert(body?.ok === true, "LOGOUT_CONTRACT_INVALID", "logout body did not report ok=true");
  const cleared = response.headers.get("set-cookie") || "";
  assert(
    cleared.includes("vh_admin_session=") && cleared.includes("Max-Age=0"),
    "SESSION_COOKIE_NOT_CLEARED",
    "logout did not expire the admin session cookie",
  );
}

async function proveSecurityHeaders(config) {
  for (const path of SECURITY_HEADER_PATHS) {
    const response = await fetch(`${config.baseUrl}${path}`, {
      redirect: "manual",
      headers: previewHeaders(config),
    });
    assert(response.status === 200, "SECURITY_HEADER_PATH_UNAVAILABLE", `${path} returned ${response.status}`);
    const csp = response.headers.get("content-security-policy");
    assert(csp, "DEPLOYED_CSP_MISSING", `${path} has no Content-Security-Policy`);
    assert(
      REQUIRED_CSP_DIRECTIVES.every((directive) => csp.includes(directive)),
      "DEPLOYED_CSP_MISMATCH",
      `${path} has an incomplete Content-Security-Policy`,
    );
    assert(!/unsafe-inline|unsafe-eval/i.test(csp), "DEPLOYED_CSP_UNSAFE", `${path} permits unsafe script or style execution`);
    assert(
      response.headers.get("strict-transport-security") === "max-age=31536000; includeSubDomains",
      "DEPLOYED_HSTS_MISMATCH",
      `${path} has an invalid Strict-Transport-Security policy`,
    );
    await response.arrayBuffer();
  }
}

async function provePreviewAccessRestricted(config) {
  for (const path of PREVIEW_PROTECTION_PATHS) {
    const response = await fetch(`${config.baseUrl}${path}`, { redirect: "manual" });
    const location = response.headers.get("location");
    const redirectedToVercel = [302, 303, 307, 308].includes(response.status)
      && location
      && new URL(location, config.baseUrl).hostname === "vercel.com";
    assert(redirectedToVercel, "PREVIEW_ACCESS_PUBLIC", `Preview ${path} did not require Vercel deployment authentication`);
    await response.arrayBuffer();
  }
}

async function proveReviewAudit(config, fixture) {
  const tenant = encodeURIComponent(config.tenantId);
  const candidate = encodeURIComponent(fixture.adminCandidateId);
  const rows = await supabaseRequest(
    config,
    `/rest/v1/admin_candidate_review_events?tenant_id=eq.${tenant}&candidate_id=eq.${candidate}&select=id,tenant_id,candidate_id,position_id,actor_email_sha256,from_review_status,to_review_status,candidate_version`,
  );
  assert(Array.isArray(rows) && rows.length === 1, "REVIEW_AUDIT_CARDINALITY", "review transition did not create exactly one audit event");
  const event = rows[0];
  const actorHash = createHash("sha256").update(fixture.adminEmail.trim().toLowerCase()).digest("hex");
  assert(event.tenant_id === config.tenantId, "REVIEW_AUDIT_TENANT_MISMATCH", "review audit tenant differs");
  assert(event.candidate_id === fixture.adminCandidateId, "REVIEW_AUDIT_CANDIDATE_MISMATCH", "review audit candidate differs");
  assert(event.position_id === fixture.adminPositionId, "REVIEW_AUDIT_POSITION_MISMATCH", "review audit position differs");
  assert(event.actor_email_sha256 === actorHash, "REVIEW_AUDIT_ACTOR_MISMATCH", "review audit actor differs");
  assert(event.from_review_status === "unreviewed", "REVIEW_AUDIT_FROM_MISMATCH", "review audit origin status differs");
  assert(event.to_review_status === REVIEWED_STATUS, "REVIEW_AUDIT_TO_MISMATCH", "review audit destination status differs");
  assert(event.candidate_version === 2, "REVIEW_AUDIT_VERSION_MISMATCH", "review audit version differs");

  const restMutation = await supabaseRequest(
    config,
    `/rest/v1/admin_candidate_review_events?id=eq.${encodeURIComponent(event.id)}`,
    {
      method: "PATCH",
      headers: { prefer: "return=representation" },
      body: JSON.stringify({ to_review_status: "rejected" }),
    },
    [403],
  );
  assert(restMutation?.code === "42501", "REVIEW_AUDIT_REST_UPDATE_ALLOWED", "review audit REST UPDATE was not rejected by table privileges");
  await proveReviewEventUpdateGuard(config, event.id, assert);

  const candidates = await supabaseRequest(
    config,
    `/rest/v1/admin_candidates?tenant_id=eq.${tenant}&id=eq.${candidate}&select=pending_review_actor_email_sha256`,
  );
  assert(
    Array.isArray(candidates)
      && candidates.length === 1
      && candidates[0].pending_review_actor_email_sha256 === null,
    "REVIEW_AUDIT_TRANSIENT_ACTOR_RETAINED",
    "candidate retained the transient review actor input",
  );
}

async function provePublicAndFailureContracts(config) {
  const evidence = await verifyPreviewArtifacts(config, assert);
  await proveSecurityHeaders(config);

  const health = await expectJson(config, "/api/health", {}, 200);
  const body = health.body;
  assert(body?.ok === true, "HEALTH_INVALID", "health did not report ok=true");
  assert(body?.environment === "preview", "WRONG_DEPLOYMENT_ENV", "health is not Preview");
  assert(body?.commitSha === config.expectedSha, "DEPLOY_SHA_MISMATCH", "Preview SHA differs from git SHA");
  assert(typeof body?.systemGitShaPresent === "boolean", "PROVENANCE_STATE_MISSING", "health omitted Vercel Git provenance state");
  assert(body?.schemaDigest === config.expectedSchemaDigest, "SCHEMA_DIGEST_MISMATCH", "schema digest differs");
  assert(
    body?.supabaseRefFingerprint === config.previewRefFingerprint,
    "SUPABASE_REF_MISMATCH",
    "health reports a different Supabase ref fingerprint",
  );
  assert(!Object.hasOwn(body || {}, "supabaseRef"), "SUPABASE_REF_EXPOSED", "health exposes the raw Supabase ref");
  assert(body?.database === "reachable", "DATABASE_UNREACHABLE", "health database check failed");
  assert(body?.outbound?.email === "DISABLED", "OUTBOUND_ENABLED", "email is not disabled");
  assert(body?.outbound?.sms === "DISABLED", "OUTBOUND_ENABLED", "SMS is not disabled");
  assert(body?.outbound?.portal === "DISABLED", "OUTBOUND_ENABLED", "portal is not disabled");
  assert(body?.outbound?.sentCount === 0, "OUTBOUND_ACTIVITY", "outbound sentCount is not zero");

  const unauthenticated = await expectJson(config, "/api/admin/candidates", {}, 401);
  assert(
    unauthenticated.body?.error?.code === "AUTH_REQUIRED",
    "AUTH_ERROR_HIDDEN",
    "unauthenticated candidate access did not return AUTH_REQUIRED",
  );
  await expectLoginFailure(config, "nobody@example.invalid", "wrong", 403, "CSRF_REJECTED", false);

  const pageResponse = await fetch(`${config.baseUrl}/admin`, {
    redirect: "manual",
    headers: previewHeaders(config),
  });
  assert(pageResponse.status === 200, "ADMIN_PAGE_UNAVAILABLE", `/admin returned ${pageResponse.status}`);
  const html = await pageResponse.text();
  assert(!html.includes(config.serviceRoleKey), "SERVICE_KEY_EXPOSED", "admin HTML contains service-role key");
  assert(!html.includes(config.anonKey), "ANON_KEY_EXPOSED", "admin HTML contains anon key");

  for (const path of publicSensitivePaths) {
    const response = await fetch(`${config.baseUrl}${path}`, {
      redirect: "manual",
      headers: previewHeaders(config),
    });
    assert(response.status === 404, "PUBLIC_STATIC_EXPOSED", `${path} returned ${response.status}`);
  }
  return evidence;
}

async function exerciseWorkflow(config, fixture) {
  await expectLoginFailure(config, fixture.adminEmail, `${fixture.adminPassword}-WRONG`, 401, "AUTH_INVALID");
  await expectLoginFailure(config, fixture.deniedEmail, fixture.deniedPassword, 403, "AUTH_FORBIDDEN");
  const firstCookie = await login(config, fixture.adminEmail, fixture.adminPassword);

  const listed = await expectJson(
    config,
    "/api/admin/candidates",
    { headers: { cookie: firstCookie } },
    200,
  );
  assert(Array.isArray(listed.body?.candidates), "LIST_CONTRACT_INVALID", "candidate list is not an array");
  assert(listed.body.candidates.length === 1, "FIXTURE_NOT_ISOLATED", "candidate list did not contain exactly one row");
  const candidate = listed.body.candidates[0];
  assert(candidate.id === fixture.adminCandidateId, "WRONG_CANDIDATE", "candidate ID differs from fixture");
  assert(candidate.position?.id === fixture.adminPositionId, "POSITION_LINK_MISSING", "candidate is not linked to fixture position");
  assert(candidate.reviewStatus === "unreviewed" && candidate.version === 1, "INITIAL_STATE_INVALID", "initial review state differs");

  const invalid = await expectJson(
    config,
    `/api/admin/candidates/${fixture.adminCandidateId}/review-status`,
    {
      method: "PATCH",
      headers: { cookie: firstCookie, "content-type": "application/json", origin: config.baseUrl },
      body: JSON.stringify({ status: "not-a-status", expectedVersion: 1 }),
    },
    400,
  );
  assert(invalid.body?.error?.code === "VALIDATION_FAILED", "VALIDATION_ERROR_HIDDEN", "invalid status was not explicit");

  const foreign = await expectJson(
    config,
    `/api/admin/candidates/${fixture.foreignCandidateId}/review-status`,
    {
      method: "PATCH",
      headers: { cookie: firstCookie, "content-type": "application/json", origin: config.baseUrl },
      body: JSON.stringify({ status: REVIEWED_STATUS, expectedVersion: 1 }),
    },
    404,
  );
  assert(foreign.body?.error?.code === "NOT_FOUND", "TENANT_BOUNDARY_HIDDEN", "foreign tenant candidate was not hidden");

  await logout(config, firstCookie);
  const discardedSession = await expectJson(
    config,
    "/api/admin/candidates",
    { headers: { cookie: firstCookie } },
    401,
  );
  assert(
    discardedSession.body?.error?.code === "AUTH_REQUIRED",
    "LOGGED_OUT_SESSION_REUSABLE",
    "the logged-out first session remained authorized",
  );
  runUiWorkflow(config, fixture);
  await proveReviewAudit(config, fixture);

  const verificationCookie = await login(config, fixture.adminEmail, fixture.adminPassword);

  const stale = await expectJson(
    config,
    `/api/admin/candidates/${fixture.adminCandidateId}/review-status`,
    {
      method: "PATCH",
      headers: { cookie: verificationCookie, "content-type": "application/json", origin: config.baseUrl },
      body: JSON.stringify({ status: "rejected", expectedVersion: 1 }),
    },
    409,
  );
  assert(stale.body?.error?.code === "VERSION_CONFLICT", "CONFLICT_HIDDEN", "stale update did not return VERSION_CONFLICT");

  const reread = await expectJson(
    config,
    "/api/admin/candidates",
    { headers: { cookie: verificationCookie } },
    200,
  );
  const persisted = reread.body?.candidates?.find((item) => item.id === fixture.adminCandidateId);
  assert(persisted?.reviewStatus === REVIEWED_STATUS, "READBACK_MISMATCH", "new-session readback lost review status");
  assert(persisted?.version === 2, "READBACK_VERSION_MISMATCH", "new-session readback lost version");
  await logout(config, verificationCookie);
}

async function main() {
  const config = loadConfig();
  await provePreviewAccessRestricted(config);
  config.protectionCookie = bootstrapProtectionCookie(config);
  const runId = randomUUID().replaceAll("-", "").slice(0, 16).toUpperCase();
  const fixture = {
    runId,
    adminPositionId: randomUUID(),
    adminCandidateId: randomUUID(),
    foreignTenantId: `E2E-TEST-FOREIGN-${runId}`,
    foreignPositionId: randomUUID(),
    foreignCandidateId: randomUUID(),
    adminEmail: `valuehire-preview-admin-${createHash("sha256").update(config.tenantId).digest("hex").slice(0, 12)}@example.invalid`,
    deniedEmail: `valuehire-preview-nonadmin-${runId.toLowerCase()}@example.invalid`,
    adminPassword: randomBytes(36).toString("base64url"),
    deniedPassword: randomBytes(36).toString("base64url"),
    adminUserId: null,
    deniedUserId: null,
  };
  Object.assign(fixture, {
    positionId: fixture.adminPositionId,
    candidateId: fixture.adminCandidateId,
    email: fixture.adminEmail,
    forbiddenEmail: fixture.deniedEmail,
    password: fixture.adminPassword,
    forbiddenPassword: fixture.deniedPassword,
  });
  let evidence = null;
  let workflowError = null;
  try {
    evidence = await provePublicAndFailureContracts(config);
    await createPreviewFixtures(config, fixture, supabaseRequest, assert);
    await exerciseWorkflow(config, fixture);
  } catch (error) {
    workflowError = error;
  }

  let cleanupError = null;
  try {
    await cleanupPreviewFixtures(config, fixture, supabaseRequest, assert);
  } catch (error) {
    cleanupError = error;
  }

  if (cleanupError) throw cleanupError;
  if (workflowError) throw workflowError;

  process.stdout.write(`VERDICT: PASS\nDEPLOYMENT_ID: ${evidence.deploymentId}\nPREVIOUS_HEALTHY_PREVIEW: ${evidence.previousPreviewDeploymentId}\nDEPLOY_SHA: ${evidence.gitSha}\nSCHEMA_DIGEST: ${evidence.schemaDigest}\nREMOTE_SCHEMA_FINGERPRINT: ${evidence.remoteSchemaFingerprint}\nREMOTE_MIGRATIONS: PASS\nREMOTE_SCHEMA_CONTRACT: PASS\nDEPLOYED_SOURCE_FILES: PASS\nPASSWORD_TOKEN_RATE_LIMIT: PASS\nVERCEL_DEPLOYMENT_PROTECTED: PASS\nPREVIEW_ACCESS_RESTRICTED: PASS\nROLLBACK_CLI_SYNTAX: PASS\nAUTH_NEGATIVE_CASES: PASS\nTENANT_ISOLATION: PASS\nPRIVATE_BUILD_FILES: 404\nDEPLOYED_SECURITY_HEADERS: PASS\nREVIEW_AUDIT_EVENT: PASS\nREVIEW_AUDIT_REST_UPDATE_DENIED: PASS\nREVIEW_AUDIT_TRIGGER_UPDATE_GUARD: PASS\nTENANT_CLASS: E2E-TEST\nBROWSER_UI_WORKFLOW: PASS\nPAGE_RELOAD: PASS\nLOGGED_OUT_SESSION_REJECTED: PASS\nNEW_BROWSER_SESSION: PASS\nSESSION_RESET: PASS\nNEW_SESSION_READBACK: PASS\nDATA_CLEANUP: PASS\nAUTH_CLEANUP: PASS\nEXTERNAL_SENDS: 0\n`);
}

main().catch((error) => {
  const code = error instanceof SmokeFailure ? error.code : "UNEXPECTED_FAILURE";
  process.stderr.write(`VERDICT: FAIL\nCODE: ${code}\nMESSAGE: ${error.message}\n`);
  process.exitCode = 1;
});
