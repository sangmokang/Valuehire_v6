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
      GIT_AUTHOR_NAME: "checkpoint deferred context test",
      GIT_AUTHOR_EMAIL: "checkpoint-deferred@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint deferred context test",
      GIT_COMMITTER_EMAIL: "checkpoint-deferred@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function runCase(path, baseline, after) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-deferred-context-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "deferred assertion fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", status: "red", scope: ["tests/**"] }],
    findings_ref: null,
    next_action: "checkpoint",
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

for (const [name, after] of [
  ["array-held arrow", "const fns = [() => assert.equal(status, 1)];\nassert.ok(true);\n"],
  ["object-held arrow", "const obj = { run: () => assert.equal(status, 1) };\nassert.ok(true);\n"],
  ["registration callback", "function register() {}\nregister(() => assert.equal(status, 1));\nassert.ok(true);\n"],
  ["ignored block callback", "const noop = () => {};\nnoop(() => { assert.equal(status, 1); });\nassert.ok(true);\n"],
  ["unconsumed generator", "function* gen() { assert.equal(status, 1); }\ngen();\nassert.ok(true);\n"],
]) {
  test(`rejects exact assertion moved into ${name}`, () => {
    const result = runCase("tests/status.test.mjs", "assert.equal(status, 1);\n", after);
    assert.equal(result.status, 1, result.stdout);
  });
}

test("rejects Python exact assertion moved after return", () => {
  const after = "def test_status():\n    return\n    assert status == 1\n    assert True\n";
  const result = runCase("tests/test_status.py", "assert status == 1\n", after);
  assert.equal(result.status, 1, result.stdout);
});
