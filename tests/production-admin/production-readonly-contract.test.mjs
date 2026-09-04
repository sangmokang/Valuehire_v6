import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";

import {
  readonlyTokenExpiresAt,
  validateReadonlyCredential,
} from "../../scripts/production-readonly-contract.mjs";

const NOW = Date.parse("2026-09-05T00:00:00.000Z");

function cookieWithClaims(claims) {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
  const payload = Buffer.from(JSON.stringify(claims)).toString("base64url");
  const token = `${header}.${payload}.synthetic-signature`;
  const session = Buffer.from(JSON.stringify({ accessToken: token })).toString("base64url");
  return `vh_admin_session=${session}`;
}

function validate(cookie, expiryOffsetMs = 10 * 60 * 1000) {
  return validateReadonlyCredential({
    cookie,
    cookieExpiresAt: new Date(NOW + expiryOffsetMs).toISOString(),
    now: NOW,
  });
}

test("production read-only credential accepts a 15-minute cookie window and live JWT", () => {
  const cookie = cookieWithClaims({ exp: Math.floor((NOW + 60 * 60 * 1000) / 1000) });
  assert.equal(readonlyTokenExpiresAt(cookie), NOW + 60 * 60 * 1000);
  assert.deepEqual(validate(cookie), {
    cookieTtlMs: 10 * 60 * 1000,
    accessTokenTtlMs: 60 * 60 * 1000,
  });
});

test("production read-only credential rejects malformed or missing JWT expiry", () => {
  assert.throws(() => validate("vh_admin_session=not-json"), { code: "invalid_PRODUCTION_READONLY_COOKIE_token_expiry" });
  assert.throws(() => validate(cookieWithClaims({ sub: "synthetic" })), { code: "invalid_PRODUCTION_READONLY_COOKIE_token_expiry" });
});

test("production read-only credential rejects expired cookies and access tokens", () => {
  const liveToken = cookieWithClaims({ exp: Math.floor((NOW + 60 * 60 * 1000) / 1000) });
  const expiredToken = cookieWithClaims({ exp: Math.floor((NOW - 1000) / 1000) });
  assert.throws(() => validate(liveToken, -1000), { code: "production_readonly_cookie_expired" });
  assert.throws(() => validate(expiredToken), { code: "production_readonly_access_token_expired" });
});

test("production read-only credential rejects operator windows above 15 minutes", () => {
  const cookie = cookieWithClaims({ exp: Math.floor((NOW + 60 * 60 * 1000) / 1000) });
  assert.throws(() => validate(cookie, 15 * 60 * 1000 + 1), {
    code: "production_readonly_cookie_ttl_exceeds_15_minutes",
  });
});

test("production read-only credential rejects access tokens above one hour", () => {
  const cookie = cookieWithClaims({ exp: Math.floor((NOW + 60 * 60 * 1000 + 1000) / 1000) });
  assert.throws(() => validate(cookie), {
    code: "production_readonly_access_token_ttl_exceeds_60_minutes",
  });
});

test("production smoke rejects missing schema and credential inputs before network", () => {
  const baseEnv = {
    PATH: process.env.PATH,
    PRODUCTION_BASE_URL: "https://example.invalid",
    VALUEHIRE_DEPLOY_SHA: "a".repeat(40),
  };
  const missingDigest = spawnSync(process.execPath, ["scripts/smoke-production-readonly.mjs"], {
    cwd: process.cwd(),
    encoding: "utf8",
    env: baseEnv,
  });
  assert.notEqual(missingDigest.status, 0);
  assert.match(missingDigest.stderr, /missing_VALUEHIRE_SCHEMA_DIGEST/);

  const missingCookie = spawnSync(process.execPath, ["scripts/smoke-production-readonly.mjs"], {
    cwd: process.cwd(),
    encoding: "utf8",
    env: { ...baseEnv, VALUEHIRE_SCHEMA_DIGEST: "b".repeat(64) },
  });
  assert.notEqual(missingCookie.status, 0);
  assert.match(missingCookie.stderr, /missing_PRODUCTION_READONLY_COOKIE/);
  assert.doesNotMatch(missingCookie.stderr, /health_failed/);
});

test("production schema verifier fails closed before network without its target and Preview fingerprint", () => {
  const result = spawnSync(process.execPath, ["scripts/verify-production-schema-readonly.mjs"], {
    cwd: process.cwd(),
    encoding: "utf8",
    env: { PATH: process.env.PATH, PRODUCTION_SUPABASE_REF: "", VALUEHIRE_PREVIEW_REMOTE_SCHEMA_FINGERPRINT: "" },
  });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /PRODUCTION_SUPABASE_REF_MISSING_OR_INVALID/);
});
