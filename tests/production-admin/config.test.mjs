import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";
import health from "../../api/health.js";

const goodSha = "a".repeat(40);
const goodEmail = "owner@example.invalid";
const env = {
  VALUEHIRE_ENV: "preview",
  VALUEHIRE_PUBLIC_URL: "https://preview.valuehire.invalid",
  VALUEHIRE_DEPLOY_SHA: goodSha,
  VALUEHIRE_SCHEMA_DIGEST: "b".repeat(64),
  VALUEHIRE_SUPABASE_URL: "https://preview-ref.supabase.co",
  VALUEHIRE_SUPABASE_ANON_KEY: "anon",
  VALUEHIRE_SUPABASE_SERVICE_ROLE_KEY: "svc",
  VALUEHIRE_ADMIN_EMAIL_SHA256: createHash("sha256").update(goodEmail).digest("hex"),
  VALUEHIRE_TENANT_ID: "E2E-TEST-LOCAL",
  VERCEL: "1",
  VERCEL_ENV: "preview",
  VERCEL_GIT_COMMIT_SHA: goodSha,
};

function responseRecorder() {
  return {
    statusCode: 200,
    headers: {},
    body: "",
    setHeader(key, value) { this.headers[key.toLowerCase()] = value; },
    end(value) { this.body = value || ""; },
    json() { return this.body ? JSON.parse(this.body) : null; },
  };
}

async function healthWithEnv(overrides, deleted = []) {
  const previous = { ...process.env };
  Object.assign(process.env, env, overrides);
  for (const key of deleted) delete process.env[key];
  const response = responseRecorder();
  try {
    await health({ method: "GET", url: "/api/health", headers: {} }, response);
  } finally {
    process.env = previous;
  }
  return response;
}

function assertConfigInvalid(response) {
  assert.equal(response.statusCode, 503);
  assert.equal(response.json().error.code, "CONFIG_INVALID");
}

test("production rejects E2E tenant during config validation", async () => {
  assertConfigInvalid(await healthWithEnv({ VALUEHIRE_ENV: "production" }));
});

test("config binds VALUEHIRE_ENV and deploy SHA to Vercel runtime", async () => {
  const cases = [
    [{}, ["VERCEL"]],
    [{ VERCEL_ENV: "production" }, []],
    [{ VERCEL_GIT_COMMIT_SHA: "A".repeat(40) }, []],
    [{ VERCEL_GIT_COMMIT_SHA: "c".repeat(40) }, []],
  ];
  for (const [override, deleted] of cases) {
    assertConfigInvalid(await healthWithEnv(override, deleted));
  }
});

test("Production rejects a missing Vercel system Git SHA", async () => {
  assertConfigInvalid(await healthWithEnv({
    VALUEHIRE_ENV: "production",
    VERCEL_ENV: "production",
    VALUEHIRE_TENANT_ID: "owner-tenant",
  }, ["VERCEL_GIT_COMMIT_SHA"]));
});

test("config rejects malformed digest, admin hash, tenant, and non-origin URLs", async () => {
  const cases = [
    { VALUEHIRE_SCHEMA_DIGEST: "not-a-digest" },
    { VALUEHIRE_ADMIN_EMAIL_SHA256: "not-a-hash" },
    { VALUEHIRE_TENANT_ID: "E2E-TEST-" },
    { VALUEHIRE_PUBLIC_URL: "https://preview.valuehire.invalid/path" },
    { VALUEHIRE_SUPABASE_URL: "http://preview-ref.supabase.co" },
  ];
  for (const override of cases) {
    assertConfigInvalid(await healthWithEnv(override));
  }
});
