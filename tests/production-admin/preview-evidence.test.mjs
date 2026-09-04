import assert from "node:assert/strict";
import test from "node:test";

import {
  selectPreviousReadyPreviewDeployment,
  verifyDeploymentSourceFileMap,
  verifyReviewEventServiceRoleGrants,
  verifyReviewEventGuardResponse,
  verifyVercelDeploymentRecord,
} from "../../scripts/preview-smoke-evidence.mjs";

const gitSha = "a".repeat(40);
const inspected = {
  target: "preview",
  readyState: "READY",
  id: "dpl_contract123",
};
const deployment = {
  source: "cli",
  env: ["VALUEHIRE_DEPLOY_SHA"],
  meta: { gitCommitSha: gitSha },
};

function contractAssert(condition, code, message) {
  if (!condition) throw Object.assign(new Error(message), { code });
}

function rejectedCode(inspectOverride = {}, deploymentOverride = {}) {
  try {
    verifyVercelDeploymentRecord(
      { ...inspected, ...inspectOverride },
      { ...deployment, ...deploymentOverride },
      gitSha,
      contractAssert,
    );
  } catch (error) {
    return error.code;
  }
  return null;
}

test("Preview deployment record accepts exact target, readiness, source, runtime SHA, and metadata SHA", () => {
  assert.equal(verifyVercelDeploymentRecord(inspected, deployment, gitSha, contractAssert), inspected.id);
});

test("Preview deployment record rejects a Production target", () => {
  assert.equal(rejectedCode({ target: "production" }), "VERCEL_TARGET_MISMATCH");
});

test("Preview deployment record rejects a deployment that is not READY", () => {
  assert.equal(rejectedCode({ readyState: "ERROR" }), "VERCEL_NOT_READY");
});

test("Preview deployment record rejects a non-CLI source", () => {
  assert.equal(rejectedCode({}, { source: "git" }), "VERCEL_DEPLOYMENT_SOURCE_MISMATCH");
});

test("Preview deployment record rejects a missing application runtime SHA pin", () => {
  assert.equal(rejectedCode({}, { env: [] }), "VERCEL_RUNTIME_SHA_MISSING");
});

test("Preview deployment record rejects a different metadata SHA", () => {
  assert.equal(rejectedCode({}, { meta: { gitCommitSha: "b".repeat(40) } }), "VERCEL_DEPLOYMENT_SHA_MISMATCH");
});

test("Preview recovery selection returns the newest older READY CLI Preview", () => {
  const deployments = [
    { uid: "dpl_newer", url: "newer.example.test", name: "valuehire-v6", created: 40, readyState: "READY", source: "cli", meta: { gitCommitSha: "d".repeat(40) } },
    { uid: "dpl_current", url: "current.example.test", name: "valuehire-v6", created: 30, readyState: "READY", source: "cli", meta: { gitCommitSha: gitSha } },
    { uid: "dpl_failed", url: "failed.example.test", name: "valuehire-v6", created: 29, readyState: "ERROR", source: "cli", meta: { gitCommitSha: "c".repeat(40) } },
    { uid: "dpl_previous", url: "previous.example.test", name: "valuehire-v6", created: 28, readyState: "READY", source: "cli", meta: { gitCommitSha: "b".repeat(40) } },
    { uid: "dpl_old", url: "old.example.test", name: "valuehire-v6", created: 20, readyState: "READY", source: "cli", meta: { gitCommitSha: "a".repeat(40) } },
  ];
  assert.equal(selectPreviousReadyPreviewDeployment(deployments, "dpl_current", contractAssert).uid, "dpl_previous");
});

test("Preview recovery selection fails closed without a previous healthy deployment", () => {
  assert.throws(
    () => selectPreviousReadyPreviewDeployment([
      { uid: "dpl_current", name: "valuehire-v6", created: 30, readyState: "READY", source: "cli", meta: { gitCommitSha: gitSha } },
    ], "dpl_current", contractAssert),
    (error) => error.code === "PREVIEW_RECOVERY_TARGET_MISSING",
  );
});

test("Deployment source file map accepts exact paths and hashes regardless of ordering", () => {
  const remoteFiles = [
    ["src/server/index.js", "hash-server"],
    ["src/ui/admin.js", "hash-admin"],
  ];
  const localFiles = [
    ["src/ui/admin.js", "hash-admin"],
    ["src/server/index.js", "hash-server"],
  ];

  assert.equal(verifyDeploymentSourceFileMap(remoteFiles, localFiles, contractAssert), undefined);
});

test("Deployment source file map rejects a path list mismatch", () => {
  assert.throws(
    () => verifyDeploymentSourceFileMap(
      [["src/server/index.js", "hash-server"]],
      [["src/ui/admin.js", "hash-admin"]],
      contractAssert,
    ),
    (error) => error.code === "VERCEL_SOURCE_FILE_LIST_MISMATCH",
  );
});

test("Deployment source file map rejects a source hash mismatch", () => {
  assert.throws(
    () => verifyDeploymentSourceFileMap(
      [["src/server/index.js", "remote-hash"]],
      [["src/server/index.js", "local-hash"]],
      contractAssert,
    ),
    (error) => error.code === "VERCEL_SOURCE_FILE_HASH_MISMATCH",
  );
});

test("Review audit guard accepts only the trigger's immutable check violation", () => {
  assert.equal(
    verifyReviewEventGuardResponse(400, { message: "ERROR: 23514: review audit events are immutable" }, contractAssert),
    undefined,
  );
});

test("Review audit guard rejects an UPDATE that reaches the database without failing", () => {
  assert.throws(
    () => verifyReviewEventGuardResponse(201, [], contractAssert),
    (error) => error.code === "REVIEW_AUDIT_GUARD_BYPASSED",
  );
});

test("Review audit guard rejects a privilege error that never reaches the trigger", () => {
  assert.throws(
    () => verifyReviewEventGuardResponse(400, { message: "ERROR: 42501: permission denied" }, contractAssert),
    (error) => error.code === "REVIEW_AUDIT_GUARD_NOT_REACHED",
  );
});

test("Review audit service role grants accept only SELECT, INSERT, and DELETE", () => {
  assert.equal(
    verifyReviewEventServiceRoleGrants(["DELETE", "INSERT", "SELECT"], contractAssert),
    undefined,
  );
});

test("Review audit service role grants reject inherited UPDATE and DDL privileges", () => {
  assert.throws(
    () => verifyReviewEventServiceRoleGrants(
      ["DELETE", "INSERT", "REFERENCES", "SELECT", "TRIGGER", "TRUNCATE", "UPDATE"],
      contractAssert,
    ),
    (error) => error.code === "REMOTE_REVIEW_EVENT_GRANT_DRIFT",
  );
});
