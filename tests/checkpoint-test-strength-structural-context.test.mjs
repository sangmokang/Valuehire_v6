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
      GIT_AUTHOR_NAME: "checkpoint structural test",
      GIT_AUTHOR_EMAIL: "checkpoint-structural@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint structural test",
      GIT_COMMITTER_EMAIL: "checkpoint-structural@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function runCase(path, baseline, after) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-structural-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "structural strength fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", ac: "structural strength", status: "red", scope: ["tests/**"] }],
    findings_ref: null,
    next_action: "run checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  write(cwd, path, baseline);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "strong baseline");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, path, after);
  git(cwd, "add", path);
  return spawnSync(process.execPath, [GATE, "--base", base, "--run-id", RUN_ID, "--json"], { cwd, encoding: "utf8" });
}

for (const [name, source] of [
  ["while body", "while (false) { assert.equal(status, 1); }\nassert.ok(true);\n"],
  ["short-circuited true branch", "true || assert.equal(status, 1);\nassert.ok(true);\n"],
  ["ternary branch", "false ? assert.equal(status, 1) : 0;\nassert.ok(true);\n"],
  ["uncalled function expression", "const hidden = function() { assert.equal(status, 1); };\nassert.ok(true);\n"],
  ["else branch", "if (true) {} else { assert.equal(status, 1); }\nassert.ok(true);\n"],
  ["IIFE after return", "(function() { return; assert.equal(status, 1); })();\nassert.ok(true);\n"],
  ["dynamic conditional", "if (process.env.RUN_ASSERT) { assert.equal(status, 1); }\nassert.ok(true);\n"],
]) {
  test(`rejects exact assertion moved into ${name}`, () => {
    const result = runCase("tests/status.test.mjs", "assert.equal(status, 1);\n", source);
    assert.equal(result.status, 1, result.stdout);
  });
}

test("rejects Python exact assertion moved under a conditional", () => {
  const result = runCase("tests/test_status.py", "assert status == 1\n", "if False:\n    assert status == 1\nassert True\n");
  assert.equal(result.status, 1, result.stdout);
});

test("allows an exact assertion inside an executed test callback", () => {
  const result = runCase(
    "tests/status.test.mjs",
    "assert.equal(status, 1);\n",
    'test("status", () => { assert.equal(status, 1); });\n',
  );
  assert.equal(result.status, 0, result.stdout);
});
