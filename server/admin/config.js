"use strict";

const { createHash } = require("node:crypto");
const { AdminError } = require("./errors");

const REQUIRED = [
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

const GIT_SHA = /^[0-9a-f]{40}$/;

function requiredEnv(env, name) {
  const value = env[name];
  if (!value || !String(value).trim()) {
    throw new AdminError("CONFIG_INVALID", 503, `${name} is required`);
  }
  return String(value).trim();
}

function origin(value, name, { allowLocalhost = false } = {}) {
  try {
    const parsed = new URL(value);
    const localHttp = allowLocalhost
      && parsed.protocol === "http:"
      && ["localhost", "127.0.0.1", "[::1]"].includes(parsed.hostname);
    if (parsed.protocol !== "https:" && !localHttp) {
      throw new Error("bad protocol");
    }
    if (parsed.username || parsed.password || parsed.pathname !== "/" || parsed.search || parsed.hash) {
      throw new Error("not an origin");
    }
    return parsed.origin;
  } catch (error) {
    throw new AdminError("CONFIG_INVALID", 503, `${name} must be an origin`);
  }
}

function validateVercelBinding(env, environment, deploySha) {
  if (env.VERCEL !== "1") {
    throw new AdminError("CONFIG_INVALID", 503, "Vercel runtime is required");
  }
  if (env.VERCEL_ENV !== environment) {
    throw new AdminError("CONFIG_INVALID", 503, "VERCEL_ENV must match VALUEHIRE_ENV");
  }
  const systemGitSha = String(env.VERCEL_GIT_COMMIT_SHA || "").trim();
  if (!systemGitSha) {
    if (environment === "production") {
      throw new AdminError("CONFIG_INVALID", 503, "Production requires Vercel Git provenance");
    }
    return false;
  }
  if (!GIT_SHA.test(systemGitSha)) {
    throw new AdminError("CONFIG_INVALID", 503, "VERCEL_GIT_COMMIT_SHA must be a git SHA");
  }
  if (systemGitSha !== deploySha) {
    throw new AdminError("CONFIG_INVALID", 503, "Vercel deployment SHA mismatch");
  }
  return true;
}

function loadConfig(env = process.env) {
  const missing = REQUIRED.filter((name) => !env[name] || !String(env[name]).trim());
  if (missing.length) {
    throw new AdminError("CONFIG_INVALID", 503, `missing env: ${missing.join(",")}`);
  }
  const environment = requiredEnv(env, "VALUEHIRE_ENV");
  const tenantId = requiredEnv(env, "VALUEHIRE_TENANT_ID");
  if (!["preview", "production"].includes(environment)) {
    throw new AdminError("CONFIG_INVALID", 503, "VALUEHIRE_ENV must be preview or production");
  }
  const deploySha = requiredEnv(env, "VALUEHIRE_DEPLOY_SHA");
  if (!GIT_SHA.test(deploySha)) {
    throw new AdminError("CONFIG_INVALID", 503, "VALUEHIRE_DEPLOY_SHA must be a git SHA");
  }
  const systemGitShaPresent = validateVercelBinding(env, environment, deploySha);
  if (!/^[0-9a-f]{64}$/.test(requiredEnv(env, "VALUEHIRE_SCHEMA_DIGEST"))) {
    throw new AdminError("CONFIG_INVALID", 503, "VALUEHIRE_SCHEMA_DIGEST must be a SHA-256 digest");
  }
  if (!/^(E2E-TEST-[A-Za-z0-9_-]{1,80}|[a-z0-9][a-z0-9_-]{1,62})$/.test(tenantId)) {
    throw new AdminError("CONFIG_INVALID", 503, "VALUEHIRE_TENANT_ID is invalid");
  }
  if (environment === "preview" && !tenantId.startsWith("E2E-TEST-")) {
    throw new AdminError("CONFIG_INVALID", 503, "Preview tenant must be E2E-TEST scoped");
  }
  if (environment === "production" && tenantId.startsWith("E2E-TEST-")) {
    throw new AdminError("CONFIG_INVALID", 503, "Production tenant must not be E2E-TEST scoped");
  }
  const adminEmailHashes = requiredEnv(env, "VALUEHIRE_ADMIN_EMAIL_SHA256").split(",").map((value) => value.trim());
  if (adminEmailHashes.some((value) => !/^[0-9a-f]{64}$/.test(value))) {
    throw new AdminError("CONFIG_INVALID", 503, "VALUEHIRE_ADMIN_EMAIL_SHA256 is invalid");
  }
  return {
    environment,
    publicUrl: origin(requiredEnv(env, "VALUEHIRE_PUBLIC_URL"), "VALUEHIRE_PUBLIC_URL", { allowLocalhost: true }),
    deploySha,
    systemGitShaPresent,
    schemaDigest: requiredEnv(env, "VALUEHIRE_SCHEMA_DIGEST"),
    supabaseUrl: origin(requiredEnv(env, "VALUEHIRE_SUPABASE_URL"), "VALUEHIRE_SUPABASE_URL"),
    anonKey: requiredEnv(env, "VALUEHIRE_SUPABASE_ANON_KEY"),
    serviceRoleKey: requiredEnv(env, "VALUEHIRE_SUPABASE_SERVICE_ROLE_KEY"),
    adminEmailHashes: new Set(adminEmailHashes),
    tenantId,
  };
}

function hashEmail(email) {
  return createHash("sha256").update(String(email).trim().toLowerCase()).digest("hex");
}

module.exports = { hashEmail, loadConfig };
