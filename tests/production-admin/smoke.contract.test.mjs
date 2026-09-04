import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

const sourcePath = "scripts/smoke-preview-admin.mjs";
const fixturePath = "scripts/preview-smoke-fixtures.mjs";
const checker = "scripts/check-preview-smoke-contract.mjs";

function runChecker(filePath = sourcePath, fixtureFilePath = fixturePath) {
  return spawnSync(process.execPath, [checker], {
    cwd: process.cwd(),
    encoding: "utf8",
    env: {
      ...process.env,
      VALUEHIRE_SMOKE_CONTRACT_PATH: filePath,
      VALUEHIRE_SMOKE_FIXTURE_CONTRACT_PATH: fixtureFilePath,
    },
  });
}

function mutatedSource(pattern, replacement) {
  const original = readFileSync(sourcePath, "utf8");
  assert.match(original, pattern);
  return original.replace(pattern, replacement);
}

function writeMutation(name, text) {
  const directory = mkdtempSync(join(tmpdir(), `valuehire-smoke-mutant-${name}-`));
  const filePath = join(directory, "smoke-preview-admin.mjs");
  writeFileSync(filePath, text);
  return { directory, filePath };
}

function mutatedFixture(pattern, replacement) {
  const original = readFileSync(fixturePath, "utf8");
  assert.match(original, pattern);
  return original.replace(pattern, replacement);
}

function writeFixtureMutation(name, text) {
  const directory = mkdtempSync(join(tmpdir(), `valuehire-smoke-fixture-mutant-${name}-`));
  const filePath = join(directory, "preview-smoke-fixtures.mjs");
  writeFileSync(filePath, text);
  return { directory, filePath };
}

function assertMutantKilled(name, pattern, replacement, expectedNeedle) {
  const mutation = writeMutation(name, mutatedSource(pattern, replacement));
  try {
    const result = runChecker(mutation.filePath);
    assert.notEqual(result.status, 0);
    assert.match(result.stdout, /VERDICT: FAIL/);
    assert.match(result.stdout, expectedNeedle);
  } finally {
    rmSync(mutation.directory, { recursive: true, force: true });
  }
}

test("preview smoke contract checker passes the real smoke harness", () => {
  const result = runChecker();
  assert.equal(result.status, 0);
  assert.match(result.stdout, /VERDICT: PASS/);
  assert.match(result.stdout, /STATIC_CONTRACTS: 21/);
});

test("checker rejects removing the Preview and Production ref collision guard", () => {
  assertMutantKilled(
    "ref-collision",
    /if \(!previewRef \|\| previewRef === productionRef\) \{\n    throw new SmokeFailure\("SMOKE_ENVIRONMENT_COLLISION", "Preview and Production Supabase refs must differ"\);\n  \}/,
    "if (!previewRef) {\n    throw new SmokeFailure(\"SMOKE_CONFIG_INVALID\", \"preview ref is required\");\n  }",
    /preview_production_ref_collision_guard/,
  );
});

test("checker rejects removing the unauthenticated 401 and code check", () => {
  assertMutantKilled(
    "unauth",
    /const unauthenticated = await expectJson[\s\S]*?AUTH_REQUIRED",\n  \);/,
    "const unauthenticated = await expectJson(config, \"/api/admin/candidates\", {}, 200);\n  assert(Array.isArray(unauthenticated.body?.candidates), \"AUTH_ERROR_HIDDEN\", \"candidate list hidden\");",
    /unauthenticated_candidates_fail_closed/,
  );
});

test("checker rejects removing deployed security-header verification", () => {
  assertMutantKilled(
    "security-headers",
    /  await proveSecurityHeaders\(config\);/,
    "  // mutant: deployed security-header proof removed",
    /deployed_security_headers_are_verified/,
  );
});

test("checker rejects removing Preview deployment-protection verification", () => {
  assertMutantKilled(
    "preview-protection",
    /  await provePreviewAccessRestricted\(config\);/,
    "  // mutant: Preview deployment-protection proof removed",
    /preview_requires_deployment_protection/,
  );
});

test("checker rejects removing deployed source-file evidence", () => {
  assertMutantKilled(
    "deployed-source-files",
    /\\nDEPLOYED_SOURCE_FILES: PASS/,
    "",
    /deployed_source_files_match_clean_head/,
  );
});

test("checker rejects removing atomic review-audit verification", () => {
  assertMutantKilled(
    "review-audit",
    /  await proveReviewAudit\(config, fixture\);/,
    "  // mutant: review audit proof removed",
    /atomic_review_audit_and_cleanup/,
  );
});

test("checker rejects the wrong REST status for audit-table privilege denial", () => {
  assertMutantKilled(
    "review-audit-rest-status",
    /\[403\],\n  \);\n  assert\(restMutation\?\.code === "42501"/,
    "[400],\n  );\n  assert(restMutation?.code === \"42501\"",
    /atomic_review_audit_and_cleanup/,
  );
});

test("checker rejects removing exact-one candidate isolation", () => {
  assertMutantKilled(
    "isolation",
    /assert\(listed\.body\.candidates\.length === 1, "FIXTURE_NOT_ISOLATED", "candidate list did not contain exactly one row"\);/,
    "assert(listed.body.candidates.length > 0, \"CANDIDATE_PRESENT\", \"candidate list was empty\");",
    /exact_one_candidate_isolation/,
  );
});

test("checker rejects removing new-session persisted readback", () => {
  assertMutantKilled(
    "readback",
    /await logout\(config, firstCookie\);[\s\S]*?assert\(persisted\?\.version === 2, "READBACK_VERSION_MISMATCH", "new-session readback lost version"\);/,
    "await logout(config, firstCookie);\n  assert(firstCookie.length > 0, \"SESSION_RESET\", \"first session existed\");",
    /new_session_persistent_readback/,
  );
});

test("checker rejects removing cleanup absence proofs", () => {
  const mutation = writeFixtureMutation(
    "cleanup",
    mutatedFixture(
      /for \(const \[label, table, id\] of rows\) \{\n    await attempt\(failures, `\$\{label\}-absence`[\s\S]*?\n  \}/,
      "for (const [label] of rows) {\n    await attempt(failures, `${label}-delete-check`, async () => {});\n  }",
    ),
  );
  try {
    const result = runChecker(sourcePath, mutation.filePath);
    assert.notEqual(result.status, 0);
    assert.match(result.stdout, /VERDICT: FAIL/);
    assert.match(result.stdout, /cleanup_absence_proof/);
  } finally {
    rmSync(mutation.directory, { recursive: true, force: true });
  }
});

test("checker rejects removing external sends zero assertions", () => {
  assertMutantKilled(
    "outbound",
    /assert\(body\?\.outbound\?\.sentCount === 0, "OUTBOUND_ACTIVITY", "outbound sentCount is not zero"\);/,
    "assert(body?.outbound, \"OUTBOUND_PRESENT\", \"outbound state exists\");",
    /external_sends_zero/,
  );
});

test("checker rejects removing typed validation and conflict checks", () => {
  assertMutantKilled(
    "conflict",
    /const stale = await expectJson[\s\S]*?assert\(stale\.body\?\.error\?\.code === "VERSION_CONFLICT", "CONFLICT_HIDDEN", "stale update did not return VERSION_CONFLICT"\);/,
    "const stale = await expectJson(config, `/api/admin/candidates/${fixture.candidateId}/review-status`, { method: \"PATCH\", headers: { cookie: firstCookie, \"content-type\": \"application/json\", origin: config.baseUrl }, body: JSON.stringify({ status: \"rejected\", expectedVersion: 1 }) }, 200);\n  assert(stale.body, \"STALE_DONE\", \"stale update returned body\");",
    /typed_error_and_conflict_checks/,
  );
});

test("checker rejects removing non-JSON and secret fail-closed checks", () => {
  assertMutantKilled(
    "secret",
    /for \(const pattern of SENSITIVE_PATTERNS\) \{\n    assert\(!pattern\.test\(serialized\), "SENSITIVE_RESPONSE", `response matched forbidden pattern \$\{pattern\}`\);\n  \}/,
    "for (const pattern of SENSITIVE_PATTERNS) {\n    if (!pattern) throw pattern;\n  }",
    /non_json_and_secret_fail_closed/,
  );
});
