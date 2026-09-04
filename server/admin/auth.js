"use strict";

const { AdminError } = require("./errors");
const { hashEmail } = require("./config");
const { parseCookies } = require("./http");
const { supabaseRaw } = require("./supabase");

const COOKIE = "vh_admin_session";
const SESSION_MAX_AGE_SECONDS = 900;

// This is a local fail-fast TTL check, not signature verification. Supabase
// remains the signature/issuer authority through /auth/v1/user on every use.
function decodeAccessTokenLifetimeClaims(accessToken) {
  if (typeof accessToken !== "string") throw new Error("missing access token");
  const parts = accessToken.split(".");
  if (parts.length !== 3 || !parts[1]) throw new Error("invalid access token");
  const claims = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8"));
  if (
    !claims
    || typeof claims !== "object"
    || Array.isArray(claims)
    || !Number.isInteger(claims.iat)
    || !Number.isInteger(claims.exp)
    || claims.exp <= claims.iat
  ) {
    throw new Error("invalid access token lifetime");
  }
  return claims;
}

function enforceLocalLifetime(accessToken, nowSeconds = Math.floor(Date.now() / 1000)) {
  const claims = decodeAccessTokenLifetimeClaims(accessToken);
  if (
    claims.iat > nowSeconds
    || claims.exp <= nowSeconds
    || nowSeconds >= claims.iat + SESSION_MAX_AGE_SECONDS
  ) {
    throw new Error("expired access token lifetime");
  }
}

function sessionCookie(session) {
  try {
    enforceLocalLifetime(session?.access_token);
  } catch {
    throw new AdminError("DEPENDENCY_INVALID", 502, "Supabase session is invalid");
  }
  const payload = Buffer.from(JSON.stringify({
    accessToken: session.access_token,
  })).toString("base64url");
  return `${COOKIE}=${payload}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${SESSION_MAX_AGE_SECONDS}`;
}

function expiredSessionCookie() {
  return `${COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;
}

function readSession(req) {
  const value = parseCookies(req).get(COOKIE);
  if (!value) throw new AdminError("AUTH_REQUIRED", 401, "admin session is required");
  try {
    const session = JSON.parse(Buffer.from(value, "base64url").toString("utf8"));
    if (
      !session
      || typeof session !== "object"
      || Array.isArray(session)
      || Object.keys(session).length !== 1
      || typeof session.accessToken !== "string"
    ) {
      throw new Error("invalid session payload");
    }
    enforceLocalLifetime(session.accessToken);
    return session;
  } catch {
    throw new AdminError("AUTH_REQUIRED", 401, "admin session is invalid");
  }
}

async function passwordLogin(config, email, password) {
  const { response, body } = await supabaseRaw(
    config,
    "/auth/v1/token?grant_type=password",
    { method: "POST", body: JSON.stringify({ email, password }) },
    config.anonKey,
  );
  if (response.status === 429) {
    throw new AdminError("AUTH_RATE_LIMITED", 429, "too many login attempts");
  }
  if (response.status >= 500) {
    throw new AdminError("DEPENDENCY_UNAVAILABLE", 503, "Supabase login failed");
  }
  if (!response.ok) throw new AdminError("AUTH_INVALID", 401, "invalid credentials");
  if (!body?.access_token || !body?.user?.email) {
    throw new AdminError("AUTH_INVALID", 401, "invalid credentials");
  }
  if (!config.adminEmailHashes.has(hashEmail(body.user.email))) {
    throw new AdminError("AUTH_FORBIDDEN", 403, "admin account is not allowed");
  }
  return body;
}

async function requireAdmin(req, config) {
  const session = readSession(req);
  if (!session.accessToken) throw new AdminError("AUTH_REQUIRED", 401, "admin session is invalid");
  const { response, body } = await supabaseRaw(
    config,
    "/auth/v1/user",
    { method: "GET" },
    config.anonKey,
    session.accessToken,
  );
  if (!response.ok) throw new AdminError("AUTH_REQUIRED", 401, "admin session is invalid");
  if (!body?.email) throw new AdminError("AUTH_REQUIRED", 401, "admin session is invalid");
  if (!config.adminEmailHashes.has(hashEmail(body.email))) {
    throw new AdminError("AUTH_FORBIDDEN", 403, "admin account is not allowed");
  }
  return { id: body.id, emailHash: hashEmail(body.email) };
}

async function revokeSession(req, config) {
  const session = readSession(req);
  if (!session.accessToken) throw new AdminError("AUTH_REQUIRED", 401, "admin session is invalid");
  const { response } = await supabaseRaw(
    config,
    "/auth/v1/logout?scope=local",
    { method: "POST" },
    config.anonKey,
    session.accessToken,
  );
  if (!response.ok) throw new AdminError("DEPENDENCY_UNAVAILABLE", 503, "Supabase logout failed");
}

module.exports = { expiredSessionCookie, passwordLogin, requireAdmin, revokeSession, sessionCookie };
