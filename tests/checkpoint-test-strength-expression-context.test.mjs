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
      GIT_AUTHOR_NAME: "checkpoint expression test",
      GIT_AUTHOR_EMAIL: "checkpoint-expression@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint expression test",
      GIT_COMMITTER_EMAIL: "checkpoint-expression@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function runCase(after) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-expression-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "expression context fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", ac: "expression context", status: "red", scope: ["tests/**"] }],
    findings_ref: null,
    next_action: "run checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  write(cwd, "tests/status.test.mjs", "assert.equal(status, 1);\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "strong baseline");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, "tests/status.test.mjs", after);
  git(cwd, "add", "tests/status.test.mjs");
  return spawnSync(process.execPath, [GATE, "--base", base, "--run-id", RUN_ID, "--json"], { cwd, encoding: "utf8" });
}

for (const [name, source] of [
  ["braceless false conditional", "if (false) assert.equal(status, 1);\nassert.ok(true);\n"],
  ["uncalled expression arrow", "const hidden = () => assert.equal(status, 1);\nassert.ok(true);\n"],
  ["uninvoked anonymous arrow", "(() => assert.equal(status, 1));\nassert.ok(true);\n"],
  ["statically empty iteration", "[].forEach(() => assert.equal(status, 1));\nassert.ok(true);\n"],
  ["deferred timer callback", "setTimeout(() => assert.equal(status, 1), 2147483647).unref();\nassert.ok(true);\n"],
]) {
  test(`rejects exact assertion moved into ${name}`, () => {
    const result = runCase(source);
    assert.equal(result.status, 1, result.stdout);
  });
}

test("allows an exact assertion in an expression-bodied test callback", () => {
  const result = runCase('test("status", () => assert.equal(status, 1));\n');
  assert.equal(result.status, 0, result.stdout);
});
