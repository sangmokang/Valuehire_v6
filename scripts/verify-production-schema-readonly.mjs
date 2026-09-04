#!/usr/bin/env node

import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";

import { REMOTE_SCHEMA_QUERY, verifyRemoteContract } from "./preview-smoke-evidence.mjs";

function fail(code, detail = "") {
  console.error("VERDICT: FAIL");
  console.error(`code=${code}`);
  if (detail) console.error(`detail=${detail}`);
  process.exit(1);
}

function assertContract(condition, code, message) {
  if (!condition) fail(code, message);
}

const productionRef = process.env.PRODUCTION_SUPABASE_REF?.trim();
const expectedPreviewFingerprint = process.env.VALUEHIRE_PREVIEW_REMOTE_SCHEMA_FINGERPRINT?.trim();
const tokenFile = process.env.SUPABASE_ACCESS_TOKEN_FILE?.trim() || `${homedir()}/.supabase/access-token`;

if (!productionRef || !/^[a-z0-9]{20}$/.test(productionRef)) fail("PRODUCTION_SUPABASE_REF_MISSING_OR_INVALID");
if (!expectedPreviewFingerprint || !/^[0-9a-f]{64}$/.test(expectedPreviewFingerprint)) fail("PREVIEW_SCHEMA_FINGERPRINT_MISSING_OR_INVALID");
if (!existsSync(tokenFile)) fail("SUPABASE_READONLY_TOKEN_MISSING");

const token = readFileSync(tokenFile, "utf8").trim();
if (!token) fail("SUPABASE_READONLY_TOKEN_EMPTY");

const response = await fetch(`https://api.supabase.com/v1/projects/${productionRef}/database/query/read-only`, {
  method: "POST",
  headers: {
    authorization: `Bearer ${token}`,
    "content-type": "application/json",
  },
  body: JSON.stringify({ query: REMOTE_SCHEMA_QUERY }),
});

if (response.status !== 201) fail("PRODUCTION_SCHEMA_QUERY_FAILED", `http=${response.status}`);
const payload = await response.json().catch(() => null);
if (!Array.isArray(payload) || payload.length !== 1 || !payload[0]?.contract) fail("PRODUCTION_SCHEMA_RESPONSE_INVALID");

const contract = payload[0].contract;
verifyRemoteContract(contract, assertContract);
const fingerprint = createHash("sha256").update(JSON.stringify(contract)).digest("hex");
if (fingerprint !== expectedPreviewFingerprint) fail("PRODUCTION_SCHEMA_FINGERPRINT_MISMATCH");

console.log("VERDICT: PASS");
console.log("production_schema_contract=PASS");
console.log("preview_schema_fingerprint_match=PASS");
console.log(`schema_fingerprint=${fingerprint}`);
console.log("query_mode=read-only");
console.log("writes_attempted=0");
