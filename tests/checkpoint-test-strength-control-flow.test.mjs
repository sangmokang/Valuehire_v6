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
      GIT_AUTHOR_NAME: "checkpoint control-flow test",
      GIT_AUTHOR_EMAIL: "checkpoint-control@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint control-flow test",
      GIT_COMMITTER_EMAIL: "checkpoint-control@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo(baseline) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-control-flow-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "control-flow strength fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", ac: "control-flow strength", status: "red", scope: ["tests/**"] }],
    findings_ref: null,
    next_action: "run checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  write(cwd, "tests/status.test.mjs", baseline);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "strong baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function runCase(baseline, after) {
  const { cwd, base } = makeRepo(baseline);
  write(cwd, "tests/status.test.mjs", after);
  git(cwd, "add", "tests/status.test.mjs");
  return spawnSync(process.execPath, [GATE, "--base", base, "--run-id", RUN_ID, "--json"], { cwd, encoding: "utf8" });
}

for (const [name, baseline, after] of [
  ["static false branch", "assert.equal(status, 1);\n", "if (false) { assert.equal(status, 1); }\nassert.ok(true);\n"],
  ["swallowed try block", "assert.equal(status, 1);\n", "try { assert.equal(status, 1); } catch {}\nassert.ok(true);\n"],
  ["case-insensitive anchored regex", "assert.match(message, /^input violation$/);\n", "assert.match(message, /^input violation$/i);\nassert.ok(true);\n"],
]) {
  test(`rejects strong assertion weakening through ${name}`, () => {
    const result = runCase(baseline, after);
    const body = JSON.parse(result.stdout);
    assert.equal(result.status, 1, JSON.stringify(body, null, 2));
    assert.ok(body.violations.some((item) => item.check === "test-weakening"));
  });
}

test("allows removal of a case-insensitive flag as an anchored-regex strengthening", () => {
  const result = runCase("assert.match(message, /^input violation$/i);\n", "assert.match(message, /^input violation$/);\n");
  assert.equal(result.status, 0, result.stdout);
});
