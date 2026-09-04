#!/usr/bin/env node

import { spawnSync } from "node:child_process";

export const EXPECTED_VERCEL_PROJECT_ID = "prj_isTeytMDr2EiXW5hg5rv4wPdyBW5";
export const EXPECTED_VERCEL_SCOPE = "sangmokangs-projects";
const READY = new Set(["READY", "ready"]);

function assert(condition, code, message) {
  if (!condition) throw Object.assign(new Error(message), { code });
}

function deploymentState(deployment) {
  return deployment?.readyState || deployment?.state;
}

function deploymentProjectId(deployment) {
  return deployment?.projectId || deployment?.project?.id || deployment?.project?.uid;
}

function isRollbackCandidate(deployment) {
  return deployment?.isRollbackCandidate === true || deployment?.rollbackCandidate === true;
}

function assertProductionDeployment(deployment, codePrefix) {
  assert(deployment?.uid || deployment?.id, `${codePrefix}_ID_MISSING`, "deployment id is missing");
  assert(READY.has(deploymentState(deployment)), `${codePrefix}_NOT_READY`, "deployment is not READY");
  assert(deployment.target === "production", `${codePrefix}_TARGET_INVALID`, "deployment is not Production");
  if (deployment.source) assert(["git", "cli"].includes(deployment.source), `${codePrefix}_SOURCE_INVALID`, "deployment source is not an accepted Production source");
}

export function selectProductionRollbackCandidate({ currentDeployment, candidates, projectId, scope }) {
  assert(projectId === EXPECTED_VERCEL_PROJECT_ID, "VERCEL_PROJECT_MISMATCH", "unexpected Vercel project id");
  assert(!scope || scope === EXPECTED_VERCEL_SCOPE, "VERCEL_SCOPE_MISMATCH", "unexpected Vercel scope");
  assert(Array.isArray(candidates), "VERCEL_ROLLBACK_LIST_INVALID", "Vercel deployment list is invalid");

  assert(currentDeployment, "PRODUCTION_CURRENT_DEPLOYMENT_MISSING", "current Production deployment is required");
  assertProductionDeployment(currentDeployment, "PRODUCTION_CURRENT");
  assert(deploymentProjectId(currentDeployment) === EXPECTED_VERCEL_PROJECT_ID, "PRODUCTION_CURRENT_PROJECT_MISMATCH", "current Production deployment belongs to a different project");
  const currentId = currentDeployment.uid || currentDeployment.id;
  const currentCreated = Number(currentDeployment.created || currentDeployment.createdAt || 0);
  assert(Number.isFinite(currentCreated) && currentCreated > 0, "PRODUCTION_CURRENT_CREATED_INVALID", "current Production deployment creation time is invalid");

  const previous = candidates
    .filter((deployment) => {
      const id = deployment?.uid || deployment?.id;
      const created = Number(deployment?.created || deployment?.createdAt || 0);
      return id
        && id !== currentId
        && isRollbackCandidate(deployment)
        && READY.has(deploymentState(deployment))
        && deployment.target === "production"
        && (!deployment.source || ["git", "cli"].includes(deployment.source))
        && deploymentProjectId(deployment) === EXPECTED_VERCEL_PROJECT_ID
        && Number.isFinite(created)
        && created > 0
        && created < currentCreated;
    })
    .sort((left, right) => Number(right.created || right.createdAt || 0) - Number(left.created || left.createdAt || 0))[0];

  assert(previous, "PRODUCTION_ROLLBACK_CANDIDATE_MISSING", "no older READY Production rollback candidate was returned by Vercel");
  assertProductionDeployment(previous, "PRODUCTION_ROLLBACK_CANDIDATE");
  assert(deploymentProjectId(previous) === EXPECTED_VERCEL_PROJECT_ID, "PRODUCTION_ROLLBACK_PROJECT_MISMATCH", "rollback candidate belongs to a different project");
  return { currentDeploymentId: currentId, rollbackDeploymentId: previous.uid || previous.id };
}

export function verifyRollbackHelp({ spawn = spawnSync, cwd = process.cwd() } = {}) {
  const result = spawn("vercel", ["rollback", "--help"], { cwd, encoding: "utf8" });
  const text = `${result.stdout || ""}\n${result.stderr || ""}`;
  assert([0, 2].includes(result.status) && /vercel rollback url\|deploymentId/.test(text), "ROLLBACK_CLI_INVALID", "Vercel rollback CLI syntax is unavailable");
}

function parseJson(text, code) {
  try {
    return JSON.parse(text);
  } catch {
    assert(false, code, "invalid JSON response");
  }
}

function runVercelApi(path, scope) {
  const args = ["api", path];
  if (scope) args.push("--scope", scope);
  const result = spawnSync("vercel", args, { cwd: process.cwd(), encoding: "utf8" });
  assert(result.status === 0, "VERCEL_ROLLBACK_LIST_FAILED", result.stderr || "Vercel deployment list failed");
  return parseJson(result.stdout, "VERCEL_ROLLBACK_LIST_INVALID");
}

function inspectCurrentProductionDeployment(scope) {
  let inspected;
  if (process.env.PRODUCTION_BASE_URL) {
    const args = ["inspect", process.env.PRODUCTION_BASE_URL, "--json"];
    if (scope) args.splice(2, 0, "--scope", scope);
    const result = spawnSync("vercel", args, { cwd: process.cwd(), encoding: "utf8" });
    assert(result.status === 0, "PRODUCTION_CURRENT_INSPECT_FAILED", result.stderr || "Production deployment inspect failed");
    inspected = parseJson(result.stdout, "PRODUCTION_CURRENT_INSPECT_INVALID");
  } else {
    assert(process.env.PRODUCTION_DEPLOYMENT_ID, "PRODUCTION_CURRENT_DEPLOYMENT_MISSING", "PRODUCTION_BASE_URL or PRODUCTION_DEPLOYMENT_ID is required");
    inspected = { id: process.env.PRODUCTION_DEPLOYMENT_ID };
  }
  const id = inspected.id || inspected.uid;
  assert(id, "PRODUCTION_CURRENT_DEPLOYMENT_MISSING", "current Production deployment id is missing");
  const response = runVercelApi(`/v13/deployments/${id}`, scope);
  return { ...inspected, ...response, uid: response.uid || response.id || id };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const scope = process.env.VERCEL_SCOPE || EXPECTED_VERCEL_SCOPE;
    verifyRollbackHelp();
    const currentDeployment = inspectCurrentProductionDeployment(scope);
    const response = runVercelApi(`/v7/deployments?projectId=${EXPECTED_VERCEL_PROJECT_ID}&target=production&state=READY&rollbackCandidate=true&limit=20`, scope);
    const result = selectProductionRollbackCandidate({
      currentDeployment,
      candidates: response?.deployments,
      projectId: EXPECTED_VERCEL_PROJECT_ID,
      scope,
    });
    process.stdout.write(`VERDICT: PASS\nROLLBACK_CLI_SYNTAX: PASS\nPRODUCTION_ROLLBACK_ELIGIBLE: PASS\nCURRENT_DEPLOYMENT_ID: ${result.currentDeploymentId}\nROLLBACK_DEPLOYMENT_ID: ${result.rollbackDeploymentId}\nWRITES_ATTEMPTED: 0\n`);
  } catch (error) {
    process.stdout.write(`VERDICT: FAIL\nERROR_CODE: ${error.code || "PRODUCTION_ROLLBACK_VERIFIER_FAILED"}\nWRITES_ATTEMPTED: 0\n`);
    process.exit(1);
  }
}
