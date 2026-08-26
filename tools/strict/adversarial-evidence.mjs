#!/usr/bin/env node
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";

const VERSION = "valuehire.adversarial-evidence/v1";
const OID = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/;
const SHA256 = /^[0-9a-f]{64}$/;
const REVIEWERS = ["G", "V1", "V2"];
const ATTACKS = [
  "fake-green",
  "ledger-worktree-decoy",
  "secret-pattern-decoy",
  "wu-commit-mismatch",
  "stale-branch-worktree",
  "zero-target",
  "concurrent-rerun-partial-output",
  "existing-regression",
];

function parseArgs(argv) {
  const args = { runId: null, evidenceCommit: null, manifestBlob: null, candidate: null, json: false };
  const valued = new Map([
    ["--run-id", "runId"],
    ["--evidence-commit", "evidenceCommit"],
    ["--manifest-blob", "manifestBlob"],
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

function authoritativeOutputText(rawText) {
  const trimmed = rawText.trim();
  if (!trimmed.startsWith("{") || !trimmed.endsWith("}")) return rawText;
  try {
    const envelope = JSON.parse(trimmed);
    if (envelope && typeof envelope === "object" && typeof envelope.result === "string") return envelope.result;
  } catch {}
  return rawText;
}

function safePath(path) {
  return typeof path === "string" && path.length > 0 && !path.startsWith("/") && !path.split("/").includes("..");
}

function add(violations, field, detail) {
  violations.push({ field, detail });
}

function validateReviewer(violations, id, reviewer, manifest, evidenceCommit, usedPaths) {
  const field = `reviewers.${id}`;
  if (!reviewer || typeof reviewer !== "object" || Array.isArray(reviewer)) {
    add(violations, field, `${id} reviewer evidence is missing`);
    return;
  }
  if (reviewer.candidate_sha !== manifest.candidate_sha) add(violations, field, `${id} candidate is stale or mismatched`);
  if (reviewer.verdict !== "PASS") add(violations, field, `${id} verdict is not PASS`);
  if (typeof reviewer.session_id !== "string" || reviewer.session_id.trim() === "") add(violations, field, `${id} session ID is missing`);
  if (typeof reviewer.command !== "string" || reviewer.command.trim() === "") add(violations, field, `${id} command is missing`);
  if (id === "V1" && !reviewer.command.startsWith("env -u ANTHROPIC_API_KEY claude -p")) {
    add(violations, field, "V1 command must remove ANTHROPIC_API_KEY before claude -p");
  }
  if (!reviewer.attacks || typeof reviewer.attacks !== "object" || Array.isArray(reviewer.attacks)) {
    add(violations, field, `${id} attack results are missing`);
  } else {
    for (const attack of ATTACKS) {
      if (reviewer.attacks[attack] !== "PASS") add(violations, field, `${id} required attack ${attack} is not PASS`);
    }
    for (const attack of Object.keys(reviewer.attacks)) {
      if (!ATTACKS.includes(attack)) add(violations, field, `${id} has an unknown attack ${attack}`);
    }
  }
  if (reviewer.output_complete !== true) add(violations, field, `${id} output_complete must be true`);
  if (!safePath(reviewer.output_path)) {
    add(violations, field, `${id} output path is unsafe or empty`);
    return;
  }
  if (usedPaths.has(reviewer.output_path)) add(violations, field, `${id} output path is duplicated`);
  usedPaths.add(reviewer.output_path);
  let output;
  try { output = gitBuffer(["show", `${evidenceCommit}:${reviewer.output_path}`]); }
  catch (error) {
    add(violations, field, `${id} raw output blob is missing: ${error.message}`);
    return;
  }
  if (output.length === 0) add(violations, field, `${id} raw output is empty`);
  if (!SHA256.test(reviewer.output_sha256 ?? "") || sha256(output) !== reviewer.output_sha256) {
    add(violations, field, `${id} raw output SHA-256 mismatch`);
  }
  if (output.length !== reviewer.output_bytes) add(violations, field, `${id} raw output byte count mismatch`);
  if (lines(output) !== reviewer.output_lines || reviewer.output_lines < 1) add(violations, field, `${id} raw output line count mismatch`);
  const text = authoritativeOutputText(output.toString("utf8"));
  if (!text.includes(manifest.candidate_sha)) add(violations, field, `${id} raw output does not name the candidate`);
  const nonempty = text.split(/\r?\n/).filter((line) => line.trim().length > 0);
  const markers = nonempty.filter((line) => /^FINAL: (?:PASS|FAIL)$/.test(line));
  if (markers.length !== 1 || markers[0] !== "FINAL: PASS" || nonempty.at(-1) !== "FINAL: PASS") {
    add(violations, field, `${id} raw output final PASS marker is not unique and authoritative`);
  }
}

function validateManifest(args, manifest) {
  const violations = [];
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
    add(violations, "manifest", "manifest must be a JSON object");
    return violations;
  }
  if (manifest.schema_version !== VERSION) add(violations, "schema_version", "unsupported schema version");
  if (manifest.run_id !== args.runId) add(violations, "run_id", "run_id does not match CLI authority");
  if (manifest.candidate_sha !== args.candidate) add(violations, "candidate_sha", "manifest candidate does not match CLI authority");
  if (!SHA256.test(manifest.t_contract_sha256 ?? "")) add(violations, "t_contract_sha256", "T contract SHA-256 is invalid");
  if (manifest.logic_verdict !== "PASS") add(violations, "logic_verdict", "logic verdict is not PASS");
  if (!Array.isArray(manifest.disagreements) || manifest.disagreements.length !== 0) {
    add(violations, "disagreements", "reviewer disagreement is unresolved");
  }
  const reviewerKeys = Object.keys(manifest.reviewers ?? {});
  if (reviewerKeys.length !== REVIEWERS.length || reviewerKeys.some((id) => !REVIEWERS.includes(id))) {
    add(violations, "reviewers", "reviewer set must be exactly G, V1, and V2");
  }
  const usedPaths = new Set();
  for (const id of REVIEWERS) validateReviewer(violations, id, manifest.reviewers?.[id], manifest, args.evidenceCommit, usedPaths);
  const reproduced = manifest.v2_reproduced_v1_attacks;
  if (!Array.isArray(reproduced) || reproduced.length !== ATTACKS.length || ATTACKS.some((attack) => !reproduced.includes(attack))) {
    add(violations, "v2_reproduced_v1_attacks", "V2 must reproduce every required V1 attack");
  }
  return violations;
}

function emit(result, json) {
  if (json) process.stdout.write(`${JSON.stringify(result)}\n`);
  else if (result.pass) process.stdout.write("PASS adversarial evidence\n");
  else for (const violation of result.violations) process.stdout.write(`${violation.field}: ${violation.detail}\n`);
}

function main() {
  let args;
  const violations = [];
  try {
    args = parseArgs(process.argv.slice(2));
    process.chdir(gitText(["rev-parse", "--show-toplevel"]));
    gitText(["rev-parse", "--verify", `${args.evidenceCommit}^{commit}`]);
    gitText(["rev-parse", "--verify", `${args.candidate}^{commit}`]);
    if (!isAncestor(args.candidate, args.evidenceCommit)) add(violations, "evidence_commit", "evidence commit is not descended from candidate");
    const path = `.strict/adversarial-evidence/${args.runId}.json`;
    const actualBlob = gitText(["rev-parse", `${args.evidenceCommit}:${path}`]);
    if (actualBlob !== args.manifestBlob) add(violations, "manifest_blob", "manifest blob does not match the approved blob pin");
    const manifest = JSON.parse(gitBuffer(["show", `${args.evidenceCommit}:${path}`]).toString("utf8"));
    violations.push(...validateManifest(args, manifest));
  } catch (error) { add(violations, "input", error.message); }
  const result = { pass: violations.length === 0, violations };
  emit(result, args?.json ?? process.argv.includes("--json"));
  process.exit(result.pass ? 0 : 1);
}

main();
