import assert from "node:assert/strict";
import test from "node:test";

import {
  EXPECTED_VERCEL_PROJECT_ID,
  EXPECTED_VERCEL_SCOPE,
  selectProductionRollbackCandidate,
  verifyRollbackHelp,
} from "../../scripts/verify-production-rollback.mjs";

const current = {
  uid: "dpl_current",
  projectId: EXPECTED_VERCEL_PROJECT_ID,
  target: "production",
  readyState: "READY",
  source: "git",
  created: 300,
};

const previous = {
  uid: "dpl_previous",
  projectId: EXPECTED_VERCEL_PROJECT_ID,
  target: "production",
  readyState: "READY",
  source: "git",
  isRollbackCandidate: true,
  created: 200,
};

function select(overrides = {}) {
  return selectProductionRollbackCandidate({
    currentDeployment: current,
    candidates: [previous],
    projectId: EXPECTED_VERCEL_PROJECT_ID,
    scope: EXPECTED_VERCEL_SCOPE,
    ...overrides,
  });
}

function rejectedCode(overrides = {}) {
  try {
    select(overrides);
  } catch (error) {
    return error.code;
  }
  return null;
}

test("Production rollback verifier selects an older READY rollback candidate", () => {
  assert.deepEqual(select(), {
    currentDeploymentId: "dpl_current",
    rollbackDeploymentId: "dpl_previous",
  });
});

test("Production rollback verifier fails closed for the wrong project", () => {
  assert.equal(rejectedCode({ projectId: "prj_wrong" }), "VERCEL_PROJECT_MISMATCH");
});

test("Production rollback verifier fails closed when the current Production deployment is missing", () => {
  assert.equal(rejectedCode({ currentDeployment: null }), "PRODUCTION_CURRENT_DEPLOYMENT_MISSING");
});

test("Production rollback verifier fails closed without an eligible previous rollback candidate", () => {
  assert.equal(rejectedCode({ candidates: [{ ...previous, isRollbackCandidate: false }] }), "PRODUCTION_ROLLBACK_CANDIDATE_MISSING");
});

test("Production rollback verifier accepts the legacy rollbackCandidate field when Vercel returns it", () => {
  assert.deepEqual(select({ candidates: [{ ...previous, isRollbackCandidate: false, rollbackCandidate: true }] }), {
    currentDeploymentId: "dpl_current",
    rollbackDeploymentId: "dpl_previous",
  });
});

test("Production rollback verifier rejects a current deployment from another project when projectId is known", () => {
  assert.equal(rejectedCode({ currentDeployment: { ...current, projectId: "prj_wrong" } }), "PRODUCTION_CURRENT_PROJECT_MISMATCH");
});

test("Production rollback verifier rejects missing current project id", () => {
  const { projectId, ...withoutProject } = current;
  assert.equal(rejectedCode({ currentDeployment: withoutProject }), "PRODUCTION_CURRENT_PROJECT_MISMATCH");
});

test("Production rollback verifier rejects Preview target when Vercel exposes target", () => {
  assert.equal(rejectedCode({ currentDeployment: { ...current, target: "preview" } }), "PRODUCTION_CURRENT_TARGET_INVALID");
});

test("Production rollback verifier rejects missing candidate target", () => {
  const { target, ...withoutTarget } = previous;
  assert.equal(rejectedCode({ candidates: [withoutTarget] }), "PRODUCTION_ROLLBACK_CANDIDATE_MISSING");
});

test("Production rollback verifier rejects invalid source when Vercel exposes source", () => {
  assert.equal(rejectedCode({ candidates: [{ ...previous, source: "preview" }] }), "PRODUCTION_ROLLBACK_CANDIDATE_MISSING");
});

test("Production rollback CLI syntax verifier accepts Vercel help output without executing rollback", () => {
  verifyRollbackHelp({
    spawn: () => ({ status: 2, stdout: "vercel rollback url|deploymentId", stderr: "" }),
    cwd: process.cwd(),
  });
});

test("Production rollback CLI syntax verifier rejects help output without the command target", () => {
  assert.throws(
    () => verifyRollbackHelp({ spawn: () => ({ status: 0, stdout: "usage", stderr: "" }) }),
    (error) => error.code === "ROLLBACK_CLI_INVALID",
  );
});
