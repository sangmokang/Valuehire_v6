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
      GIT_AUTHOR_NAME: "checkpoint ignored-source test",
      GIT_AUTHOR_EMAIL: "checkpoint-ignored@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint ignored-source test",
      GIT_COMMITTER_EMAIL: "checkpoint-ignored@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo() {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-ignored-source-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "ignored source fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", ac: "ignored source", status: "red", scope: ["tests/**"] }],
    findings_ref: null,
    next_action: "run checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  write(cwd, "tests/status.test.mjs", "assert.equal(status, 1);\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "strong baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function runAttack(after) {
  const { cwd, base } = makeRepo();
  write(cwd, "tests/status.test.mjs", after);
  git(cwd, "add", "tests/status.test.mjs");
  const result = spawnSync(
    process.execPath,
    [GATE, "--base", base, "--run-id", RUN_ID, "--json"],
    { cwd, encoding: "utf8" },
  );
  const body = JSON.parse(result.stdout);
  assert.equal(result.status, 1, JSON.stringify(body, null, 2));
  assert.ok(body.violations.some((item) => item.check === "test-weakening"));
}

for (const [name, source] of [
  ["line comment", "// assert.equal(status, 1);\nassert.ok(true);\n"],
  ["block comment", "/* assert.equal(status, 1); */\nassert.ok(true);\n"],
  ["string literal", 'const hidden = "assert.equal(status, 1);";\nassert.ok(true);\n'],
  ["template literal", "const hidden = `assert.equal(status, 1);`;\nassert.ok(true);\n"],
]) {
  test(`rejects an exact assertion hidden in a ${name} despite padding`, () => runAttack(source));
}
