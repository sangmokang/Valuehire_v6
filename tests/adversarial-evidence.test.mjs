import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const VALIDATOR = join(ROOT, "tools/strict/adversarial-evidence.mjs");
const RUN_ID = "adversarial-fixture";
const MANIFEST_PATH = `.strict/adversarial-evidence/${RUN_ID}.json`;
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
      GIT_AUTHOR_NAME: "adversarial evidence test",
      GIT_AUTHOR_EMAIL: "adversarial-evidence@example.invalid",
      GIT_COMMITTER_NAME: "adversarial evidence test",
      GIT_COMMITTER_EMAIL: "adversarial-evidence@example.invalid",
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

function reviewer(id, candidate, output) {
  const commands = {
    G: "node --test tests/checkpoint-gate.test.mjs",
    V1: "env -u ANTHROPIC_API_KEY claude -p",
    V2: "codex native fresh-context verifier",
  };
  return {
    engine: id === "V1" ? "claude" : "codex",
    session_id: `${id.toLowerCase()}-session-1`,
    command: commands[id],
    candidate_sha: candidate,
    verdict: "PASS",
    attacks: Object.fromEntries(ATTACKS.map((attack) => [attack, "PASS"])),
    output_path: `evidence/${id.toLowerCase()}.txt`,
    output_sha256: sha256(output),
    output_bytes: Buffer.byteLength(output),
    output_lines: output.split("\n").length - 1,
    output_complete: true,
  };
}

function makeRepo(mutate = () => {}) {
  const cwd = mkdtempSync(join(tmpdir(), "adversarial-evidence-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q", "-b", "task/adversarial-fixture");
  write(cwd, "src/value.mjs", "export const value = 1;\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "candidate");
  const candidate = git(cwd, "rev-parse", "HEAD");
  const outputs = {
    G: `candidate=${candidate}\nFINAL: PASS\n`,
    V1: `candidate=${candidate}\nFINAL: PASS\n`,
    V2: `candidate=${candidate}\nFINAL: PASS\n`,
  };
  const manifest = {
    schema_version: "valuehire.adversarial-evidence/v1",
    run_id: RUN_ID,
    candidate_sha: candidate,
    t_contract_sha256: sha256("T fixture contract\n"),
    reviewers: Object.fromEntries(["G", "V1", "V2"].map((id) => [id, reviewer(id, candidate, outputs[id])])),
    v2_reproduced_v1_attacks: [...ATTACKS],
    disagreements: [],
    logic_verdict: "PASS",
  };
  mutate({ manifest, outputs, candidate });
  for (const [id, output] of Object.entries(outputs)) write(cwd, `evidence/${id.toLowerCase()}.txt`, output);
  write(cwd, MANIFEST_PATH, `${JSON.stringify(manifest, null, 2)}\n`);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "pin adversarial evidence");
  const evidenceCommit = git(cwd, "rev-parse", "HEAD");
  const manifestBlob = git(cwd, "rev-parse", `${evidenceCommit}:${MANIFEST_PATH}`);
  return { cwd, candidate, evidenceCommit, manifestBlob };
}

function runValidator(fixture) {
  const result = spawnSync(process.execPath, [
    VALIDATOR,
    "--run-id", RUN_ID,
    "--evidence-commit", fixture.evidenceCommit,
    "--manifest-blob", fixture.manifestBlob,
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

test("G, Claude V1, and fresh-context Codex V2 evidence binds to one candidate and T", () => {
  const result = runValidator(makeRepo());
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  assert.deepEqual(result.body, { pass: true, violations: [] });
});

test("Claude JSON envelope result text is validated as the authoritative raw output", () => {
  const result = runValidator(makeRepo(({ manifest, outputs }) => {
    const resultText = `candidate=${manifest.candidate_sha}\nFINAL: PASS\n`;
    outputs.V1 = `${JSON.stringify({
      type: "result",
      session_id: "v1-session-1",
      result: resultText,
    })}\n`;
    manifest.reviewers.V1.output_sha256 = sha256(outputs.V1);
    manifest.reviewers.V1.output_bytes = Buffer.byteLength(outputs.V1);
    manifest.reviewers.V1.output_lines = outputs.V1.split("\n").length - 1;
  }));
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  assert.deepEqual(result.body, { pass: true, violations: [] });
});

test("delivery acceptance runs the V1 wiring and goal current-state regressions", () => {
  const body = readFileSync(join(ROOT, "scripts/acceptance-checkpoint-delivery.sh"), "utf8");
  assert.match(body, /tests\/v1-regression-wiring\.test\.mjs/);
  assert.match(body, /tests\/goal-current-state\.test\.mjs/);
});

test("a stale reviewer candidate is rejected", () => expectFailure(makeRepo(({ manifest }) => {
  manifest.reviewers.V1.candidate_sha = "0".repeat(40);
}), "candidate"));
test("a missing required attack is rejected", () => expectFailure(makeRepo(({ manifest }) => {
  delete manifest.reviewers.V1.attacks[ATTACKS[0]];
}), "attack"));
test("Claude V1 FAIL forbids a PASS logic verdict", () => expectFailure(makeRepo(({ manifest }) => {
  manifest.reviewers.V1.verdict = "FAIL";
}), "verdict"));
test("a later raw FAIL marker overrides an earlier PASS marker", () => expectFailure(makeRepo(({ manifest, outputs }) => {
  outputs.V1 = `candidate=${manifest.candidate_sha}\nFINAL: PASS\nFINAL: FAIL\n`;
  manifest.reviewers.V1.output_sha256 = sha256(outputs.V1);
  manifest.reviewers.V1.output_bytes = Buffer.byteLength(outputs.V1);
  manifest.reviewers.V1.output_lines = outputs.V1.split("\n").length - 1;
}), "final PASS"));
test("an indented FAIL marker cannot hide before a final PASS", () => expectFailure(makeRepo(({ manifest, outputs }) => {
  outputs.V1 = `candidate=${manifest.candidate_sha}\n  FINAL: FAIL\nFINAL: PASS\n`;
  manifest.reviewers.V1.output_sha256 = sha256(outputs.V1);
  manifest.reviewers.V1.output_bytes = Buffer.byteLength(outputs.V1);
  manifest.reviewers.V1.output_lines = outputs.V1.split("\n").length - 1;
}), "final PASS"));
test("a Claude error envelope cannot authorize its embedded PASS text", () => expectFailure(makeRepo(({ manifest, outputs }) => {
  outputs.V1 = `${JSON.stringify({
    type: "result",
    is_error: true,
    session_id: "v1-session-1",
    result: `candidate=${manifest.candidate_sha}\nFINAL: PASS\n`,
  })}\n`;
  manifest.reviewers.V1.output_sha256 = sha256(outputs.V1);
  manifest.reviewers.V1.output_bytes = Buffer.byteLength(outputs.V1);
  manifest.reviewers.V1.output_lines = outputs.V1.split("\n").length - 1;
}), "envelope"));
test("G V1 V2 disagreement is rejected", () => expectFailure(makeRepo(({ manifest }) => {
  manifest.reviewers.V2.verdict = "FAIL";
  manifest.disagreements = ["V1 says PASS, V2 says FAIL"];
}), "disagreement"));
test("zero output is rejected", () => expectFailure(makeRepo(({ manifest, outputs }) => {
  outputs.V1 = "";
  manifest.reviewers.V1.output_sha256 = sha256("");
  manifest.reviewers.V1.output_bytes = 0;
  manifest.reviewers.V1.output_lines = 0;
}), "empty"));
test("partial output is rejected", () => expectFailure(makeRepo(({ manifest }) => {
  manifest.reviewers.V2.output_complete = false;
}), "complete"));
test("raw output hash mismatch is rejected", () => expectFailure(makeRepo(({ manifest }) => {
  manifest.reviewers.G.output_sha256 = "0".repeat(64);
}), "SHA-256"));
test("missing session ID is rejected", () => expectFailure(makeRepo(({ manifest }) => {
  manifest.reviewers.V1.session_id = "";
}), "session"));
test("Claude V1 command must remove the inherited API key", () => expectFailure(makeRepo(({ manifest }) => {
  manifest.reviewers.V1.command = "claude -p";
}), "ANTHROPIC_API_KEY"));
test("V2 must reproduce every V1 attack", () => expectFailure(makeRepo(({ manifest }) => {
  manifest.v2_reproduced_v1_attacks.pop();
}), "reproduce"));
test("a substituted manifest blob is rejected", () => {
  const fixture = makeRepo();
  fixture.manifestBlob = "0".repeat(40);
  expectFailure(fixture, "blob");
});
