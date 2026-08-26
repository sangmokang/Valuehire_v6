import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const VALIDATOR = join(ROOT, "tools/strict/delivery-state.mjs");
const RUN_ID = "delivery-fixture";
const STATE_PATH = `.strict/delivery-state/${RUN_ID}.json`;
const cleanups = [];

test.after(() => {
  for (const directory of cleanups) rmSync(directory, { recursive: true, force: true });
});

function git(cwd, ...args) {
  return execFileSync("git", args, {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      GIT_CONFIG_NOSYSTEM: "1",
      GIT_AUTHOR_NAME: "delivery state test",
      GIT_AUTHOR_EMAIL: "delivery-state@example.invalid",
      GIT_COMMITTER_NAME: "delivery state test",
      GIT_COMMITTER_EMAIL: "delivery-state@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function proof(path, output, targetSha) {
  return {
    target_sha: targetSha,
    output_path: path,
    output_sha256: sha256(output),
    output_bytes: Buffer.byteLength(output),
    output_lines: output.split("\n").length - 1,
    output_complete: true,
  };
}

function localOnly(candidate) {
  return {
    schema_version: "valuehire.delivery-state/v1",
    run_id: RUN_ID,
    candidate_sha: candidate,
    local: { full_strict: "PASS", codeaudit: "PASS", adversarial: "PASS" },
    pr: { state: "NOT_RUN" },
    ci: { state: "NOT_RUN" },
    merge: { state: "NOT_RUN" },
    checkpoint_readiness: "NOT_RUN",
    overall_t: "NOT_RUN",
    deploy: { state: "NOT_RUN" },
    live_verify: { state: "NOT_RUN" },
  };
}

function merged(state, outputs, mergeSha) {
  const candidate = state.candidate_sha;
  state.pr = { state: "OPEN", number: 17, url: "https://github.com/example/valuehire/pull/17", head_sha: candidate };
  state.ci = {
    state: "GREEN",
    head_sha: candidate,
    checks: [{ name: "verify", conclusion: "SUCCESS" }],
    source_kind: "github-pr-status-check-rollup",
    source_command: "gh pr view 17 --json title,body,url,statusCheckRollup,headRefOid",
    ...proof("evidence/ci.txt", outputs.ci, candidate),
  };
  state.merge = {
    state: "MERGED",
    actor: "USER",
    pr_number: 17,
    merge_sha: mergeSha,
    ...proof("evidence/merge.txt", outputs.merge, mergeSha),
  };
  state.checkpoint_readiness = "PASS";
  state.overall_t = "PASS";
}

function makeRepo(mutate = () => {}) {
  const cwd = mkdtempSync(join(tmpdir(), "delivery-state-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q", "-b", "task/delivery-fixture");
  write(cwd, "src/value.mjs", "export const value = 1;\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "candidate");
  const candidate = git(cwd, "rev-parse", "HEAD");
  const candidateTree = git(cwd, "rev-parse", `${candidate}^{tree}`);
  const unrelated = git(cwd, "commit-tree", candidateTree, "-m", "unrelated merge object");
  write(cwd, "src/value.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/value.mjs");
  git(cwd, "commit", "-qm", "user merge result");
  const mergeSha = git(cwd, "rev-parse", "HEAD");
  const outputs = {
    ci: `${JSON.stringify({ title: "fixture", url: "https://github.com/example/valuehire/pull/17", headRefOid: candidate, statusCheckRollup: [{ name: "verify", conclusion: "SUCCESS" }] })}\n`,
    merge: `merge=${mergeSha}\nUSER MERGED\n`,
    deploy: `merge=${mergeSha}\nDEPLOY GREEN\n`,
    live: `merge=${mergeSha}\nLIVE GREEN\n`,
  };
  const state = localOnly(candidate);
  mutate({ state, outputs, candidate, mergeSha, unrelated, merged: () => merged(state, outputs, mergeSha) });
  for (const [name, output] of Object.entries(outputs)) write(cwd, `evidence/${name}.txt`, output);
  write(cwd, STATE_PATH, `${JSON.stringify(state, null, 2)}\n`);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "pin delivery evidence");
  const stateCommit = git(cwd, "rev-parse", "HEAD");
  const stateBlob = git(cwd, "rev-parse", `${stateCommit}:${STATE_PATH}`);
  return { cwd, candidate, stateCommit, stateBlob };
}

function runValidator(fixture) {
  const result = spawnSync(process.execPath, [
    VALIDATOR,
    "--run-id", RUN_ID,
    "--state-commit", fixture.stateCommit,
    "--state-blob", fixture.stateBlob,
    "--candidate", fixture.candidate,
    "--json",
  ], { cwd: fixture.cwd, encoding: "utf8" });
  let body = null;
  try { body = JSON.parse(result.stdout); } catch {}
  return { ...result, body };
}

function expectFailure(fixture, detail) {
  const result = runValidator(fixture);
  assert.equal(result.status, 1, result.stderr);
  assert.equal(result.body?.pass, false, result.stdout);
  assert.ok(result.body.violations.some((item) => item.detail.includes(detail)), JSON.stringify(result.body));
}

test("local GREEN keeps remote, merge, deploy, live, readiness, and overall T at NOT_RUN", () => {
  const result = runValidator(makeRepo());
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  assert.deepEqual(result.body, { pass: true, violations: [] });
});

test("checkpoint readiness cannot pass before user merge", () => expectFailure(makeRepo(({ state }) => {
  state.checkpoint_readiness = "PASS";
}), "before merge"));
test("overall T cannot pass before user merge", () => expectFailure(makeRepo(({ state }) => {
  state.overall_t = "PASS";
}), "before merge"));
test("CI GREEN cannot substitute for a real PR", () => expectFailure(makeRepo(({ state, outputs, candidate }) => {
  state.ci = { state: "GREEN", head_sha: candidate, checks: [{ name: "verify", conclusion: "SUCCESS" }], ...proof("evidence/ci.txt", outputs.ci, candidate) };
}), "PR"));
test("CI with zero checks is rejected", () => expectFailure(makeRepo(({ state, outputs, candidate }) => {
  state.pr = { state: "OPEN", number: 17, url: "https://github.com/example/valuehire/pull/17", head_sha: candidate };
  state.ci = { state: "GREEN", head_sha: candidate, checks: [], ...proof("evidence/ci.txt", outputs.ci, candidate) };
}), "zero"));
test("CI for a stale hash is rejected", () => expectFailure(makeRepo(({ state, outputs, candidate }) => {
  state.pr = { state: "OPEN", number: 17, url: "https://github.com/example/valuehire/pull/17", head_sha: candidate };
  state.ci = { state: "GREEN", head_sha: "0".repeat(40), checks: [{ name: "verify", conclusion: "SUCCESS" }], ...proof("evidence/ci.txt", outputs.ci, candidate) };
}), "candidate"));
test("CI evidence must come from a GitHub PR statusCheckRollup command", () => expectFailure(makeRepo(({ state, merged: markMerged }) => {
  markMerged();
  state.ci.source_kind = "local-test-output";
  state.ci.source_command = "node --test";
}), "GitHub"));
test("merge without CI GREEN is rejected", () => expectFailure(makeRepo(({ state, outputs }) => {
  state.merge = { state: "MERGED", actor: "USER", pr_number: 17, merge_sha: "a".repeat(40), ...proof("evidence/merge.txt", outputs.merge, "a".repeat(40)) };
}), "CI GREEN"));
test("a nonexistent merge object cannot promote readiness", () => expectFailure(makeRepo(({ state, outputs, merged: markMerged }) => {
  markMerged();
  const missing = "f".repeat(40);
  outputs.merge = `merge=${missing}\nUSER MERGED\n`;
  state.merge = { ...state.merge, merge_sha: missing, ...proof("evidence/merge.txt", outputs.merge, missing) };
}), "object"));
test("a merge object unrelated to the candidate cannot promote readiness", () => expectFailure(makeRepo(({ state, outputs, unrelated, merged: markMerged }) => {
  markMerged();
  outputs.merge = `merge=${unrelated}\nUSER MERGED\n`;
  state.merge = { ...state.merge, merge_sha: unrelated, ...proof("evidence/merge.txt", outputs.merge, unrelated) };
}), "descended"));
test("deploy before merge is rejected", () => expectFailure(makeRepo(({ state, outputs }) => {
  state.deploy = { state: "GREEN", merge_sha: "a".repeat(40), ...proof("evidence/deploy.txt", outputs.deploy, "a".repeat(40)) };
}), "after merge"));
test("live verify before deploy is rejected", () => expectFailure(makeRepo(({ state, outputs }) => {
  state.live_verify = { state: "GREEN", merge_sha: "a".repeat(40), ...proof("evidence/live.txt", outputs.live, "a".repeat(40)) };
}), "after deploy"));
test("post-merge deploy and live verify use separate evidence", () => {
  const result = runValidator(makeRepo(({ state, outputs, merged: markMerged }) => {
    markMerged();
    state.deploy = { state: "GREEN", merge_sha: state.merge.merge_sha, ...proof("evidence/deploy.txt", outputs.deploy, state.merge.merge_sha) };
    state.live_verify = { state: "GREEN", merge_sha: state.merge.merge_sha, ...proof("evidence/live.txt", outputs.live, state.merge.merge_sha) };
  }));
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
});
test("deploy and live verify cannot reuse one output", () => expectFailure(makeRepo(({ state, outputs, merged: markMerged }) => {
  markMerged();
  state.deploy = { state: "GREEN", merge_sha: state.merge.merge_sha, ...proof("evidence/deploy.txt", outputs.deploy, state.merge.merge_sha) };
  state.live_verify = { state: "GREEN", merge_sha: state.merge.merge_sha, ...proof("evidence/deploy.txt", outputs.deploy, state.merge.merge_sha) };
}), "separate"));
test("unknown remote state is rejected", () => expectFailure(makeRepo(({ state }) => {
  state.pr.state = "GREENISH";
}), "state"));
