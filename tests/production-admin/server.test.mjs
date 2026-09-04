import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { test } from "node:test";
import { createHash } from "node:crypto";
import health from "../../api/health.js";
import login from "../../api/admin/auth/login.js";
import logout from "../../api/admin/auth/session.js";
import candidates from "../../api/admin/candidates/index.js";
import reviewStatus from "../../api/admin/candidates/[candidateId]/review-status.js";

const goodSha = "a".repeat(40);
const goodEmail = "owner@example.invalid";
const nowSeconds = Math.floor(Date.now() / 1000);

function accessToken({ iat = nowSeconds, exp = nowSeconds + 3600 } = {}) {
  const encode = (value) => Buffer.from(JSON.stringify(value)).toString("base64url");
  return `${encode({ alg: "RS256", typ: "JWT" })}.${encode({ iat, exp, sub: "user-1" })}.test-signature`;
}

function sessionCookie(token) {
  return `vh_admin_session=${Buffer.from(JSON.stringify({ accessToken: token })).toString("base64url")}`;
}

function payloadCookie(payload) {
  return `vh_admin_session=${Buffer.from(JSON.stringify(payload)).toString("base64url")}`;
}

async function callAt(timestampSeconds, handler, request) {
  const originalNow = Date.now;
  Date.now = () => timestampSeconds * 1000;
  try {
    return await call(handler, request);
  } finally {
    Date.now = originalNow;
  }
}

const goodAccessToken = accessToken();
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

function req(method, url, { headers = {}, body = null } = {}) {
  const request = new EventEmitter();
  request.method = method;
  request.url = url;
  request.headers = headers;
  process.nextTick(() => {
    if (body) request.emit("data", Buffer.from(JSON.stringify(body)));
    request.emit("end");
  });
  return request;
}

function res() {
  return {
    statusCode: 200,
    headers: {},
    body: "",
    setHeader(key, value) { this.headers[key.toLowerCase()] = value; },
    end(value) { this.body = value || ""; },
    json() { return this.body ? JSON.parse(this.body) : null; },
  };
}

async function call(handler, request) {
  const previous = { ...process.env };
  Object.assign(process.env, env);
  const response = res();
  try {
    await handler(request, response);
    return response;
  } finally {
    process.env = previous;
  }
}

function installFetchMock() {
  const state = {
    calls: [],
    loginStatus: 200,
    loginEmail: goodEmail,
    loginAccessToken: goodAccessToken,
    userStatus: 200,
    userEmail: goodEmail,
    logoutStatus: 204,
    candidate: {
      id: "11111111-1111-4111-8111-111111111111",
      position_id: "22222222-2222-4222-8222-222222222222",
      external_key: "E2E-TEST-CANDIDATE",
      display_name: "E2E-TEST-CANDIDATE",
      review_status: "unreviewed",
      version: 1,
      updated_at: "2026-09-04T00:00:00Z",
    },
  };
  globalThis.fetch = async (url, options = {}) => {
    state.calls.push({ url, options });
    const target = new URL(url);
    if (target.pathname === "/auth/v1/token") {
      return json(state.loginStatus, { access_token: state.loginAccessToken, refresh_token: "no", user: { email: state.loginEmail } });
    }
    if (target.pathname === "/auth/v1/user") return json(state.userStatus, { id: "user-1", email: state.userEmail });
    if (target.pathname === "/auth/v1/logout") return json(state.logoutStatus, null);
    if (target.pathname === "/rest/v1/admin_positions" && options.method !== "PATCH") {
      return json(200, [{ id: state.candidate.position_id, external_key: "E2E-TEST-POSITION", title: "E2E Position" }]);
    }
    if (target.pathname === "/rest/v1/admin_candidates" && options.method !== "PATCH") {
      const queriedId = target.searchParams.get("id");
      if (queriedId && queriedId !== `eq.${state.candidate.id}`) {
        return json(200, []);
      }
      return json(200, [state.candidate]);
    }
    if (target.pathname === "/rest/v1/admin_candidates" && options.method === "PATCH") {
      const candidateMatches = target.searchParams.get("id") === `eq.${state.candidate.id}`;
      const requestedStatus = JSON.parse(options.body).review_status;
      const statusFilter = target.searchParams.get("review_status");
      const statusMatches = statusFilter
        ? statusFilter === `neq.${requestedStatus}` && state.candidate.review_status !== requestedStatus
        : true;
      if (
        candidateMatches
        && target.search.includes(`version=eq.${state.candidate.version}`)
        && statusMatches
      ) {
        state.candidate = { ...state.candidate, review_status: requestedStatus, version: 2 };
        return json(200, [state.candidate]);
      }
      return json(200, []);
    }
    return json(404, { error: "not found" });
  };
  return state;
}

function json(status, body) {
  return { ok: status >= 200 && status < 300, status, async text() { return JSON.stringify(body); } };
}

test("health returns typed deployment state without secrets", async () => {
  installFetchMock();
  const response = await call(health, req("GET", "/api/health"));
  assert.equal(response.statusCode, 200);
  assert.deepEqual(response.json().outbound, { email: "DISABLED", sms: "DISABLED", portal: "DISABLED", sentCount: 0 });
  assert.equal(JSON.stringify(response.json()).includes("service"), false);
  assert.equal(Object.hasOwn(response.json(), "supabaseRef"), false);
  assert.match(response.json().supabaseRefFingerprint, /^[0-9a-f]{12}$/);
  assert.equal(response.json().systemGitShaPresent, true);
});

test("Preview reports a missing Vercel system Git SHA without rejecting independently verified CLI provenance", async () => {
  installFetchMock();
  const previous = { ...process.env };
  Object.assign(process.env, env);
  delete process.env.VERCEL_GIT_COMMIT_SHA;
  const response = res();
  try {
    await health(req("GET", "/api/health"), response);
  } finally {
    process.env = previous;
  }
  assert.equal(response.statusCode, 200);
  assert.equal(response.json().systemGitShaPresent, false);
});

test("health is GET-only", async () => {
  installFetchMock();
  const response = await call(health, req("POST", "/api/health"));
  assert.equal(response.statusCode, 405);
  assert.equal(response.json().error.code, "METHOD_NOT_ALLOWED");
});

test("login sets only secure HttpOnly session contract", async () => {
  installFetchMock();
  const response = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  assert.equal(response.statusCode, 200);
  assert.deepEqual(response.json(), { ok: true });
  assert.match(response.headers["set-cookie"], /HttpOnly/);
  assert.match(response.headers["set-cookie"], /Secure/);
  assert.match(response.headers["set-cookie"], /Max-Age=900/);
  const encoded = response.headers["set-cookie"].split("=", 2)[1].split(";", 1)[0];
  const stored = JSON.parse(Buffer.from(encoded, "base64url").toString("utf8"));
  assert.deepEqual(stored, { accessToken: goodAccessToken });
  assert.equal(response.headers["set-cookie"].includes("refresh"), false);
});

test("login rejects wrong password as AUTH_INVALID", async () => {
  const state = installFetchMock();
  state.loginStatus = 400;
  const response = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "wrong" },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_INVALID");
});

test("login exposes provider throttling and outages as typed errors", async () => {
  const state = installFetchMock();
  state.loginStatus = 429;
  const limited = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "wrong" },
  }));
  assert.equal(limited.statusCode, 429);
  assert.equal(limited.json().error.code, "AUTH_RATE_LIMITED");
  assert.equal(Object.hasOwn(limited.headers, "set-cookie"), false);

  state.loginStatus = 503;
  const unavailable = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "wrong" },
  }));
  assert.equal(unavailable.statusCode, 503);
  assert.equal(unavailable.json().error.code, "DEPENDENCY_UNAVAILABLE");
  assert.equal(Object.hasOwn(unavailable.headers, "set-cookie"), false);
});

test("login rejects a provider session without JWT lifetime claims", async () => {
  const state = installFetchMock();
  state.loginAccessToken = ["not", "a", "jwt"].join("-");
  const response = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  assert.equal(response.statusCode, 502);
  assert.equal(response.json().error.code, "DEPENDENCY_INVALID");
  assert.equal(Object.hasOwn(response.headers, "set-cookie"), false);
});

test("login rejects valid non-allowlisted user as AUTH_FORBIDDEN", async () => {
  const state = installFetchMock();
  state.loginEmail = "other@example.invalid";
  const response = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: "other@example.invalid", password: "ok" },
  }));
  assert.equal(response.statusCode, 403);
  assert.equal(response.json().error.code, "AUTH_FORBIDDEN");
});

test("login rejects wrong origin", async () => {
  installFetchMock();
  const response = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: "https://attacker.invalid" },
    body: { email: goodEmail, password: "ok" },
  }));
  assert.equal(response.statusCode, 403);
  assert.equal(response.json().error.code, "CSRF_REJECTED");
});

test("logout expires the session cookie and expired cookie is unauthorized", async () => {
  const state = installFetchMock();
  const loginResponse = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  const cookie = loginResponse.headers["set-cookie"].split(";", 1)[0];
  const logoutResponse = await call(logout, req("DELETE", "/api/admin/auth/session", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL, cookie },
  }));
  assert.equal(logoutResponse.statusCode, 200);
  assert.match(logoutResponse.headers["set-cookie"], /Max-Age=0/);
  assert.match(logoutResponse.headers["set-cookie"], /HttpOnly/);
  const revokeCall = state.calls.find((callItem) => new URL(callItem.url).pathname === "/auth/v1/logout");
  assert.equal(new URL(revokeCall.url).searchParams.get("scope"), "local");
  assert.equal(revokeCall.options.headers.apikey, env.VALUEHIRE_SUPABASE_ANON_KEY);
  assert.equal(revokeCall.options.headers.authorization, `Bearer ${goodAccessToken}`);
  const expiredCookie = logoutResponse.headers["set-cookie"].split(";", 1)[0];
  const listResponse = await call(candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: expiredCookie },
  }));
  assert.equal(listResponse.statusCode, 401);
  assert.equal(listResponse.json().error.code, "AUTH_REQUIRED");
});

test("logout exposes remote revocation failure while clearing the local cookie", async () => {
  const state = installFetchMock();
  state.logoutStatus = 503;
  const loginResponse = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  const cookie = loginResponse.headers["set-cookie"].split(";", 1)[0];
  const response = await call(logout, req("DELETE", "/api/admin/auth/session", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL, cookie },
  }));
  assert.equal(response.statusCode, 503);
  assert.equal(response.json().error.code, "DEPENDENCY_UNAVAILABLE");
  assert.equal(response.json().error.localSessionCleared, true);
  assert.match(response.headers["set-cookie"], /Max-Age=0/);
});

test("logout rejects a malformed cookie without calling Supabase or clearing it", async () => {
  const state = installFetchMock();
  const malformedCookie = ["vh_admin_session", "not-json"].join("=");
  const response = await call(logout, req("DELETE", "/api/admin/auth/session", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL, cookie: malformedCookie },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.some((callItem) => new URL(callItem.url).pathname === "/auth/v1/logout"), false);
  assert.equal(Object.hasOwn(response.headers, "set-cookie"), false);
});

test("session rejects a null cookie payload as AUTH_REQUIRED without calling Supabase", async () => {
  const state = installFetchMock();
  const nullCookie = `vh_admin_session=${Buffer.from("null").toString("base64url")}`;
  const response = await call(candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: nullCookie },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session rejects a valid provider token after the local 15-minute window", async () => {
  const state = installFetchMock();
  const oldToken = accessToken({ iat: nowSeconds - 901, exp: nowSeconds + 1800 });
  const response = await call(candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: sessionCookie(oldToken) },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session accepts a provider-valid token one second before the local lifetime boundary", async () => {
  const state = installFetchMock();
  const fixedNow = 2_000_000_000;
  const token = accessToken({ iat: fixedNow - 899, exp: fixedNow + 1800 });
  const response = await callAt(fixedNow, candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: sessionCookie(token) },
  }));
  assert.equal(response.statusCode, 200);
  assert.equal(state.calls.some((item) => new URL(item.url).pathname === "/auth/v1/user"), true);
});

test("session rejects exactly at the local 15-minute lifetime boundary", async () => {
  const state = installFetchMock();
  const fixedNow = 2_000_000_000;
  const token = accessToken({ iat: fixedNow - 900, exp: fixedNow + 1800 });
  const response = await callAt(fixedNow, candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: sessionCookie(token) },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session rejects a syntactically valid token issued in the future", async () => {
  const state = installFetchMock();
  const fixedNow = 2_000_000_000;
  const token = accessToken({ iat: fixedNow + 1, exp: fixedNow + 1800 });
  const response = await callAt(fixedNow, candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: sessionCookie(token) },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session rejects a syntactically valid token at its provider expiry boundary", async () => {
  const state = installFetchMock();
  const fixedNow = 2_000_000_000;
  const token = accessToken({ iat: fixedNow - 60, exp: fixedNow });
  const response = await callAt(fixedNow, candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: sessionCookie(token) },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session rejects a syntactically valid token whose expiry does not follow issuance", async () => {
  const state = installFetchMock();
  const fixedNow = 2_000_000_000;
  const token = accessToken({ iat: fixedNow - 60, exp: fixedNow - 60 });
  const response = await callAt(fixedNow, candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: sessionCookie(token) },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session rejects an array cookie payload", async () => {
  const state = installFetchMock();
  const response = await call(candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: payloadCookie([goodAccessToken]) },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session rejects a cookie payload with an extra field", async () => {
  const state = installFetchMock();
  const response = await call(candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: payloadCookie({ accessToken: goodAccessToken, unexpected: true }) },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session rejects a cookie payload with a non-string access token", async () => {
  const state = installFetchMock();
  const response = await call(candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: payloadCookie({ accessToken: 123 }) },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("session rejects an access token without JWT lifetime claims", async () => {
  const state = installFetchMock();
  const response = await call(candidates, req("GET", "/api/admin/candidates", {
    headers: { cookie: sessionCookie("not-a-jwt") },
  }));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
  assert.equal(state.calls.length, 0);
});

test("logout requires DELETE and same origin", async () => {
  installFetchMock();
  const wrongMethod = await call(logout, req("POST", "/api/admin/auth/session", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
  }));
  assert.equal(wrongMethod.statusCode, 405);
  const wrongOrigin = await call(logout, req("DELETE", "/api/admin/auth/session", {
    headers: { origin: "https://attacker.invalid" },
  }));
  assert.equal(wrongOrigin.statusCode, 403);
  assert.equal(wrongOrigin.json().error.code, "CSRF_REJECTED");
});

test("candidate list requires auth and does not hide auth failure as empty list", async () => {
  installFetchMock();
  const response = await call(candidates, req("GET", "/api/admin/candidates"));
  assert.equal(response.statusCode, 401);
  assert.equal(response.json().error.code, "AUTH_REQUIRED");
});

test("candidate list queries candidates and positions within the configured tenant", async () => {
  const state = installFetchMock();
  const loginResponse = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  const cookie = loginResponse.headers["set-cookie"].split(";", 1)[0];

  const response = await call(candidates, req("GET", "/api/admin/candidates", { headers: { cookie } }));
  assert.equal(response.statusCode, 200);

  const candidateQuery = state.calls.find((callItem) => new URL(callItem.url).pathname === "/rest/v1/admin_candidates");
  const positionQuery = state.calls.find((callItem) => new URL(callItem.url).pathname === "/rest/v1/admin_positions");
  assert.match(new URL(candidateQuery.url).search, /tenant_id=eq\.E2E-TEST-LOCAL/);
  assert.match(new URL(positionQuery.url).search, /tenant_id=eq\.E2E-TEST-LOCAL/);
});

test("candidate state update persists by version and reports stale writes", async () => {
  const state = installFetchMock();
  const loginResponse = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  const cookie = loginResponse.headers["set-cookie"].split(";", 1)[0];
  const firstList = await call(candidates, req("GET", "/api/admin/candidates", { headers: { cookie } }));
  assert.equal(firstList.json().candidates[0].reviewStatus, "unreviewed");
  const userCheck = state.calls.find((callItem) => new URL(callItem.url).pathname === "/auth/v1/user");
  assert.equal(userCheck.options.headers.apikey, env.VALUEHIRE_SUPABASE_ANON_KEY);
  assert.equal(userCheck.options.headers.authorization, `Bearer ${goodAccessToken}`);
  const update = await call(reviewStatus, req("PATCH", "/api/admin/candidates/11111111-1111-4111-8111-111111111111/review-status", {
    headers: { cookie, origin: env.VALUEHIRE_PUBLIC_URL },
    body: { status: "reviewed", expectedVersion: 1 },
  }));
  assert.equal(update.statusCode, 200);
  assert.equal(update.json().reviewStatus, "reviewed");
  const patchCall = state.calls.find((callItem) => new URL(callItem.url).pathname === "/rest/v1/admin_candidates" && callItem.options.method === "PATCH");
  assert.match(new URL(patchCall.url).search, /tenant_id=eq\.E2E-TEST-LOCAL/);
  assert.match(new URL(patchCall.url).search, /version=eq\.1/);
  assert.deepEqual(JSON.parse(patchCall.options.body), {
    review_status: "reviewed",
    version: 2,
    pending_review_actor_email_sha256: env.VALUEHIRE_ADMIN_EMAIL_SHA256,
  });
  const stale = await call(reviewStatus, req("PATCH", "/api/admin/candidates/11111111-1111-4111-8111-111111111111/review-status", {
    headers: { cookie, origin: env.VALUEHIRE_PUBLIC_URL },
    body: { status: "rejected", expectedVersion: 1 },
  }));
  assert.equal(stale.statusCode, 409);
  assert.equal(stale.json().error.code, "VERSION_CONFLICT");
});

test("review update rejects wrong origin, invalid UUID, and invalid status", async () => {
  installFetchMock();
  const loginResponse = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  const cookie = loginResponse.headers["set-cookie"].split(";", 1)[0];
  const wrongOrigin = await call(reviewStatus, req("PATCH", "/api/admin/candidates/11111111-1111-4111-8111-111111111111/review-status", {
    headers: { cookie, origin: "https://attacker.invalid" },
    body: { status: "reviewed", expectedVersion: 1 },
  }));
  assert.equal(wrongOrigin.statusCode, 403);
  assert.equal(wrongOrigin.json().error.code, "CSRF_REJECTED");
  const invalidUuid = await call(reviewStatus, req("PATCH", "/api/admin/candidates/not-a-uuid/review-status", {
    headers: { cookie, origin: env.VALUEHIRE_PUBLIC_URL },
    body: { status: "reviewed", expectedVersion: 1 },
  }));
  assert.equal(invalidUuid.statusCode, 400);
  assert.equal(invalidUuid.json().error.code, "VALIDATION_FAILED");
  const invalidStatus = await call(reviewStatus, req("PATCH", "/api/admin/candidates/11111111-1111-4111-8111-111111111111/review-status", {
    headers: { cookie, origin: env.VALUEHIRE_PUBLIC_URL },
    body: { status: "sent", expectedVersion: 1 },
  }));
  assert.equal(invalidStatus.statusCode, 400);
  assert.equal(invalidStatus.json().error.code, "VALIDATION_FAILED");
});

test("review update rejects an unchanged status without surfacing a dependency error", async () => {
  installFetchMock();
  const loginResponse = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  const cookie = loginResponse.headers["set-cookie"].split(";", 1)[0];
  const unchanged = await call(reviewStatus, req("PATCH", "/api/admin/candidates/11111111-1111-4111-8111-111111111111/review-status", {
    headers: { cookie, origin: env.VALUEHIRE_PUBLIC_URL },
    body: { status: "unreviewed", expectedVersion: 1 },
  }));
  assert.equal(unchanged.statusCode, 400);
  assert.equal(unchanged.json().error.code, "VALIDATION_FAILED");
});

test("provider failures are typed errors, not empty successful lists", async () => {
  globalThis.fetch = async () => {
    throw new Error("network unavailable");
  };
  const response = await call(health, req("GET", "/api/health"));
  assert.equal(response.statusCode, 503);
  assert.equal(response.json().error.code, "DEPENDENCY_UNAVAILABLE");
});

test("tenant-scoped missing candidate returns NOT_FOUND, not version conflict", async () => {
  const state = installFetchMock();
  state.candidate = { ...state.candidate, id: "33333333-3333-4333-8333-333333333333" };
  const loginResponse = await call(login, req("POST", "/api/admin/auth/login", {
    headers: { origin: env.VALUEHIRE_PUBLIC_URL },
    body: { email: goodEmail, password: "ok" },
  }));
  const cookie = loginResponse.headers["set-cookie"].split(";", 1)[0];
  const update = await call(reviewStatus, req("PATCH", "/api/admin/candidates/11111111-1111-4111-8111-111111111111/review-status", {
    headers: { cookie, origin: env.VALUEHIRE_PUBLIC_URL },
    body: { status: "reviewed", expectedVersion: 1 },
  }));
  assert.equal(update.statusCode, 404);
  assert.equal(update.json().error.code, "NOT_FOUND");
});
