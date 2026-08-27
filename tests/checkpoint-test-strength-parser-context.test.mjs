import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const GATE = join(ROOT, "tools/strict/checkpoint-gate.mjs");
const RUN_ID = "r-1787525327788-6723";
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
      GIT_AUTHOR_NAME: "checkpoint parser context test",
      GIT_AUTHOR_EMAIL: "checkpoint-parser@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint parser context test",
      GIT_COMMITTER_EMAIL: "checkpoint-parser@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function runCase(baseline, after) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-parser-context-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "parser context fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", status: "red", scope: ["tests/**"] }],
    findings_ref: null,
    next_action: "checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  write(cwd, "tests/status.test.mjs", baseline);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "strong baseline");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, "tests/status.test.mjs", after);
  git(cwd, "add", "tests/status.test.mjs");
  return spawnSync(process.execPath, [GATE, "--base", base, "--run-id", RUN_ID, "--json"], { cwd, encoding: "utf8" });
}

for (const [name, after] of [
  ["arrow test callback first-statement try", 'test("status", () => { try { assert.equal(status, 1); } catch {} assert.ok(true); });\n'],
  ["async test callback first-statement try", 'test("status", async () => { try { assert.equal(status, 1); } catch {} assert.ok(true); });\n'],
  ["bare block first-statement try", "{ try { assert.equal(status, 1); } catch {} assert.ok(true); }\n"],
]) {
  test(`rejects exact assertion hidden by ${name}`, () => {
    const result = runCase("assert.equal(status, 1);\n", after);
    assert.equal(result.status, 1, result.stdout);
  });
}

for (const runner of ["test", "it"]) {
  test(`rejects weakening inside ${runner} anonymous function callback`, () => {
    const before = `${runner}("status", function () { assert.equal(status, 1); });\n`;
    const after = `${runner}("status", function () { assert.notEqual(status, 0); assert.ok(true); });\n`;
    const result = runCase(before, after);
    assert.equal(result.status, 1, result.stdout);
  });

  test(`allows preserved exact assertion inside ${runner} anonymous function callback`, () => {
    const after = `${runner}("status", function () { assert.equal(status, 1); });\n`;
    const result = runCase("assert.equal(status, 1);\n", after);
    assert.equal(result.status, 0, result.stdout);
  });
}

test("allows preserved assertion in nested suite and test function callbacks", () => {
  const after = 'describe("suite", function () { it("status", function () { assert.equal(status, 1); }); });\n';
  const result = runCase("assert.equal(status, 1);\n", after);
  assert.equal(result.status, 0, result.stdout);
});
