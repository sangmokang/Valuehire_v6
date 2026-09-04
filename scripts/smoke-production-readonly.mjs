#!/usr/bin/env node

import { validateReadonlyCredential } from "./production-readonly-contract.mjs";

const baseUrl = process.env.PRODUCTION_BASE_URL;
const expectedSha = process.env.VALUEHIRE_DEPLOY_SHA;
const expectedDigest = process.env.VALUEHIRE_SCHEMA_DIGEST;
let writesAttempted = 0;

function fail(message) {
  console.error("VERDICT: FAIL");
  console.error(message);
  console.error(`writes_attempted=${writesAttempted}`);
  process.exit(1);
}

async function getJson(path, headers = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    method: "GET",
    cache: "no-store",
    headers: { accept: "application/json", ...headers },
  });
  const body = await response.json().catch(() => null);
  return { response, body };
}

if (!baseUrl || !/^https:\/\//.test(baseUrl)) fail("missing_https_PRODUCTION_BASE_URL");
if (!expectedSha) fail("missing_VALUEHIRE_DEPLOY_SHA");
if (!/^[0-9a-f]{40}$/.test(expectedSha)) fail("invalid_VALUEHIRE_DEPLOY_SHA");
if (!expectedDigest) fail("missing_VALUEHIRE_SCHEMA_DIGEST");
if (!/^[0-9a-f]{64}$/.test(expectedDigest)) fail("invalid_VALUEHIRE_SCHEMA_DIGEST");

const readonlyCookie = process.env.PRODUCTION_READONLY_COOKIE;
try {
  validateReadonlyCredential({
    cookie: readonlyCookie,
    cookieExpiresAt: process.env.PRODUCTION_READONLY_COOKIE_EXPIRES_AT,
  });
} catch (error) {
  fail(error.code || "invalid_PRODUCTION_READONLY_COOKIE");
}

const health = await getJson("/api/health");
if (!health.response.ok || !health.body) fail(`health_failed:${health.response.status}`);
if (health.body.environment !== "production") fail(`environment_not_production:${health.body.environment}`);
if (health.body.commitSha !== expectedSha) fail(`deploy_sha_mismatch:${health.body.commitSha}`);
if (health.body.schemaDigest !== expectedDigest) fail(`schema_digest_mismatch:${health.body.schemaDigest}`);
if (health.body.outbound?.sentCount !== 0) fail(`external_sends_not_zero:${health.body.outbound?.sentCount}`);

const blocked = await getJson("/api/admin/candidates");
if (blocked.response.status !== 401) fail(`unauthenticated_access_not_blocked:${blocked.response.status}`);

const readonly = await getJson("/api/admin/candidates", { cookie: readonlyCookie });
if (!readonly.response.ok) fail(`authorized_read_failed:${readonly.response.status}`);
if (!Array.isArray(readonly.body?.candidates)) fail("authorized_read_missing_candidates_array");

console.log("VERDICT: PASS");
console.log("health=PASS");
console.log("unauthenticated_access_blocked=PASS");
console.log("authorized_readonly_candidates=PASS");
console.log("readonly_cookie_15m_window=PASS");
console.log("access_token_expiry=PASS");
console.log(`schema_digest=${health.body.schemaDigest}`);
console.log(`commit_sha=${health.body.commitSha}`);
console.log(`writes_attempted=${writesAttempted}`);
