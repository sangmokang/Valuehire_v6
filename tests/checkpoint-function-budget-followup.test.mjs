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
      GIT_AUTHOR_NAME: "checkpoint function test",
      GIT_AUTHOR_EMAIL: "checkpoint-function@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint function test",
      GIT_COMMITTER_EMAIL: "checkpoint-function@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo() {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-function-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC, function hard 100 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "function fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", ac: "function budget", status: "red", scope: ["src/**"] }],
    findings_ref: null,
    next_action: "run checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  write(cwd, "README.md", "baseline\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "function baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function javascriptFunction(lines) {
  return `export function boundary() {\n${"  void 0;\n".repeat(lines - 2)}}\n`;
}

function pythonFunction(lines) {
  return `def boundary():\n${"    pass\n".repeat(lines - 1)}`;
}

function shellFunction(lines) {
  return `boundary() {\n${"  :\n".repeat(lines - 2)}}\n`;
}

function evaluate(path, content) {
  const { cwd, base } = makeRepo();
  write(cwd, path, content);
  git(cwd, "add", path);
  const result = spawnSync(
    process.execPath,
    [GATE, "--base", base, "--run-id", RUN_ID, "--json"],
    { cwd, encoding: "utf8" },
  );
  return { ...result, body: JSON.parse(result.stdout) };
}

function expectBoundary(path, builder) {
  const allowed = evaluate(path, builder(100));
  assert.equal(allowed.status, 0, JSON.stringify(allowed.body, null, 2));
  const blocked = evaluate(path, builder(101));
  assert.equal(blocked.status, 1, JSON.stringify(blocked.body, null, 2));
  assert.ok(
    blocked.body.violations.some(
      (violation) => violation.check === "size-limit" && /function.+101 LOC.+100/.test(violation.detail),
    ),
    JSON.stringify(blocked.body, null, 2),
  );
}

test("JavaScript functions enforce the 100/101 LOC boundary", () => {
  expectBoundary("src/boundary.mjs", javascriptFunction);
});

test("Python functions enforce the 100/101 LOC boundary", () => {
  expectBoundary("src/boundary.py", pythonFunction);
});

test("shell functions enforce the 100/101 LOC boundary", () => {
  expectBoundary("src/boundary.sh", shellFunction);
});
