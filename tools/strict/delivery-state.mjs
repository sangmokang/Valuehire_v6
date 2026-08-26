#!/usr/bin/env node
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";

const VERSION = "valuehire.delivery-state/v1";
const OID = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/;
const SHA256 = /^[0-9a-f]{64}$/;
const LOCAL_STATES = new Set(["PASS", "FAIL", "NOT_RUN", "BLOCKED"]);
const REMOTE_STATES = new Set(["NOT_RUN", "BLOCKED", "OPEN", "GREEN", "FAIL", "MERGED"]);

function parseArgs(argv) {
  const args = { runId: null, stateCommit: null, stateBlob: null, candidate: null, json: false };
  const valued = new Map([
    ["--run-id", "runId"],
    ["--state-commit", "stateCommit"],
    ["--state-blob", "stateBlob"],
    ["--candidate", "candidate"],
  ]);
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === "--json") args.json = true;
    else if (valued.has(flag)) {
      const value = argv[++index];
      if (!value || value.startsWith("--")) throw new Error(`${flag} requires a value`);
      args[valued.get(flag)] = value;
    } else throw new Error(`unknown argument: ${flag}`);
  }
  for (const [flag, key] of valued) if (!args[key]) throw new Error(`${flag} is required`);
  if (!/^[A-Za-z0-9._-]+$/.test(args.runId)) throw new Error("--run-id has invalid characters");
  for (const [flag, key] of valued) {
    if (key !== "runId" && !OID.test(args[key])) throw new Error(`${flag} requires a full Git object ID`);
  }
  return args;
}

function git(args, { buffer = false, allowFailure = false } = {}) {
  const result = spawnSync("git", args, {
    encoding: buffer ? null : "utf8",
    maxBuffer: 64 * 1024 * 1024,
    env: process.env,
  });
  if (!allowFailure && result.status !== 0) {
    const stderr = buffer ? result.stderr.toString("utf8") : result.stderr;
    throw new Error((stderr || `git ${args.join(" ")} failed`).trim());
  }
  return result;
}

function gitText(args) {
  return git(args).stdout.trim();
}

function gitBuffer(args) {
  return git(args, { buffer: true }).stdout;
}

function isAncestor(older, newer) {
  return git(["merge-base", "--is-ancestor", older, newer], { allowFailure: true }).status === 0;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function lines(buffer) {
  if (buffer.length === 0) return 0;
  const text = buffer.toString("utf8");
  return text.endsWith("\n") ? text.split("\n").length - 1 : text.split("\n").length;
}

function safePath(path) {
  return typeof path === "string" && path.length > 0 && !path.startsWith("/") && !path.split("/").includes("..");
}

function add(violations, field, detail) {
  violations.push({ field, detail });
}

function validateProof(violations, field, proof, stateCommit, targetSha, usedPaths) {
  if (proof.target_sha !== targetSha) add(violations, field, `${field} proof target does not match candidate or merge SHA`);
  if (proof.output_complete !== true) add(violations, field, `${field} output_complete must be true`);
  if (!safePath(proof.output_path)) {
    add(violations, field, `${field} output path is unsafe or empty`);
    return;
  }
  if (usedPaths.has(proof.output_path)) add(violations, field, `${field} must use separate evidence output`);
  usedPaths.add(proof.output_path);
  let output;
  try { output = gitBuffer(["show", `${stateCommit}:${proof.output_path}`]); }
  catch (error) {
    add(violations, field, `${field} output is missing: ${error.message}`);
    return;
  }
  if (output.length === 0) add(violations, field, `${field} output is empty`);
  if (!SHA256.test(proof.output_sha256 ?? "") || sha256(output) !== proof.output_sha256) {
    add(violations, field, `${field} output SHA-256 mismatch`);
  }
  if (output.length !== proof.output_bytes) add(violations, field, `${field} output byte count mismatch`);
  if (lines(output) !== proof.output_lines || proof.output_lines < 1) add(violations, field, `${field} output line count mismatch`);
  if (!output.toString("utf8").includes(targetSha)) add(violations, field, `${field} output does not name its target SHA`);
}

function validState(violations, field, value, allowed = REMOTE_STATES) {
  if (!value || typeof value !== "object" || !allowed.has(value.state)) {
    add(violations, field, `${field} state is missing or unknown`);
    return false;
  }
  return true;
}

function validateState(args, state) {
  const violations = [];
  const usedPaths = new Set();
  if (!state || typeof state !== "object" || Array.isArray(state)) {
    add(violations, "state", "state must be a JSON object");
    return violations;
  }
  if (state.schema_version !== VERSION) add(violations, "schema_version", "unsupported schema version");
  if (state.run_id !== args.runId) add(violations, "run_id", "run_id does not match CLI authority");
  if (state.candidate_sha !== args.candidate) add(violations, "candidate_sha", "state candidate does not match CLI authority");
  for (const key of ["full_strict", "codeaudit", "adversarial"]) {
    if (!LOCAL_STATES.has(state.local?.[key])) add(violations, `local.${key}`, `local ${key} state is missing or unknown`);
  }

  const prValid = validState(violations, "pr", state.pr);
  const ciValid = validState(violations, "ci", state.ci);
  const mergeValid = validState(violations, "merge", state.merge);
  const deployValid = validState(violations, "deploy", state.deploy);
  const liveValid = validState(violations, "live_verify", state.live_verify);
  if (prValid && state.pr.state === "OPEN") {
    if (!Number.isInteger(state.pr.number) || state.pr.number < 1 || !/^https:\/\/github\.com\//.test(state.pr.url ?? "")) {
      add(violations, "pr", "OPEN PR requires a GitHub number and URL");
    }
    if (state.pr.head_sha !== args.candidate) add(violations, "pr", "PR head does not match candidate");
  }
  if (ciValid && state.ci.state === "GREEN") {
    if (state.pr?.state !== "OPEN") add(violations, "ci", "CI GREEN requires a real OPEN PR");
    if (state.ci.head_sha !== args.candidate || state.pr?.head_sha !== args.candidate) add(violations, "ci", "CI or PR head does not match candidate");
    if (!Array.isArray(state.ci.checks) || state.ci.checks.length === 0) add(violations, "ci", "CI GREEN has zero checks");
    else if (state.ci.checks.some((check) => !check?.name || check.conclusion !== "SUCCESS")) {
      add(violations, "ci", "CI GREEN contains a missing or non-successful check");
    }
    validateProof(violations, "ci", state.ci, args.stateCommit, args.candidate, usedPaths);
  }

  const merged = mergeValid && state.merge.state === "MERGED";
  if (merged) {
    if (state.ci?.state !== "GREEN") add(violations, "merge", "user merge requires CI GREEN");
    if (state.pr?.state !== "OPEN" || state.merge.pr_number !== state.pr.number) add(violations, "merge", "merge does not match the recorded PR");
    if (state.merge.actor !== "USER") add(violations, "merge", "merge actor must be USER");
    if (!OID.test(state.merge.merge_sha ?? "")) add(violations, "merge", "merge SHA must be a full Git object ID");
    else validateProof(violations, "merge", state.merge, args.stateCommit, state.merge.merge_sha, usedPaths);
  }
  for (const [field, value] of [["checkpoint readiness", state.checkpoint_readiness], ["overall T", state.overall_t]]) {
    if (!new Set(["NOT_RUN", "PASS", "FAIL", "BLOCKED"]).has(value)) add(violations, field, `${field} state is missing or unknown`);
    if (!merged && value !== "NOT_RUN") add(violations, field, `${field} cannot be promoted before merge`);
    if (value === "PASS" && (state.ci?.state !== "GREEN" || Object.values(state.local ?? {}).some((item) => item !== "PASS"))) {
      add(violations, field, `${field} PASS requires local PASS and CI GREEN`);
    }
  }
  if (deployValid && state.deploy.state === "GREEN") {
    if (!merged) add(violations, "deploy", "deploy evidence is allowed only after merge");
    if (state.deploy.merge_sha !== state.merge?.merge_sha) add(violations, "deploy", "deploy merge SHA does not match merge evidence");
    if (OID.test(state.merge?.merge_sha ?? "")) validateProof(violations, "deploy", state.deploy, args.stateCommit, state.merge.merge_sha, usedPaths);
  }
  if (liveValid && state.live_verify.state === "GREEN") {
    if (state.deploy?.state !== "GREEN") add(violations, "live_verify", "live verify evidence is allowed only after deploy GREEN");
    if (state.live_verify.merge_sha !== state.merge?.merge_sha) add(violations, "live_verify", "live verify merge SHA does not match merge evidence");
    if (OID.test(state.merge?.merge_sha ?? "")) validateProof(violations, "live_verify", state.live_verify, args.stateCommit, state.merge.merge_sha, usedPaths);
  }
  return violations;
}

function emit(result, json) {
  if (json) process.stdout.write(`${JSON.stringify(result)}\n`);
  else if (result.pass) process.stdout.write("PASS delivery state\n");
  else for (const violation of result.violations) process.stdout.write(`${violation.field}: ${violation.detail}\n`);
}

function main() {
  let args;
  const violations = [];
  try {
    args = parseArgs(process.argv.slice(2));
    process.chdir(gitText(["rev-parse", "--show-toplevel"]));
    gitText(["rev-parse", "--verify", `${args.stateCommit}^{commit}`]);
    gitText(["rev-parse", "--verify", `${args.candidate}^{commit}`]);
    if (!isAncestor(args.candidate, args.stateCommit)) add(violations, "state_commit", "state commit is not descended from candidate");
    const path = `.strict/delivery-state/${args.runId}.json`;
    const actualBlob = gitText(["rev-parse", `${args.stateCommit}:${path}`]);
    if (actualBlob !== args.stateBlob) add(violations, "state_blob", "state blob does not match the approved blob pin");
    const state = JSON.parse(gitBuffer(["show", `${args.stateCommit}:${path}`]).toString("utf8"));
    violations.push(...validateState(args, state));
  } catch (error) { add(violations, "input", error.message); }
  const result = { pass: violations.length === 0, violations };
  emit(result, args?.json ?? process.argv.includes("--json"));
  process.exit(result.pass ? 0 : 1);
}

main();
