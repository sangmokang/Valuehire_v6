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

function git(cwd, ...args) {
  return execFileSync("git", args, {
    cwd,
    encoding: "utf8",
    env: {
      ...process.env,
      GIT_CONFIG_NOSYSTEM: "1",
      GIT_AUTHOR_NAME: "checkpoint return ASI test",
      GIT_AUTHOR_EMAIL: "checkpoint-return-asi@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint return ASI test",
      GIT_COMMITTER_EMAIL: "checkpoint-return-asi@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function runCase(after) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-return-asi-"));
  try {
    git(cwd, "init", "-q");
    write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
    write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
    write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
    write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
      run_id: RUN_ID,
      task: "return ASI assertion fixture",
      state: "BUILD",
      contract_sha256: "0".repeat(64),
      approvals: [],
      wus: [{ id: "WU-3c", status: "red", scope: ["tests/**"] }],
      findings_ref: null,
      next_action: "checkpoint",
      updated_at: "2026-08-27T00:00:00.000Z",
    })}\n`);
    write(cwd, "tests/status.test.mjs", "assert.equal(status, 1);\n");
    git(cwd, "add", "-A");
    git(cwd, "commit", "-qm", "strong baseline");
    const base = git(cwd, "rev-parse", "HEAD");
    write(cwd, "tests/status.test.mjs", after);
    git(cwd, "add", "tests/status.test.mjs");
    return spawnSync(process.execPath, [GATE, "--base", base, "--run-id", RUN_ID, "--json"], { cwd, encoding: "utf8" });
  } finally {
    rmSync(cwd, { recursive: true, force: true });
  }
}

test("rejects an exact assertion moved after an ASI-terminated return", () => {
  const after = 'test("status", () => {\n  return\n  assert.equal(status, 1);\n  assert.ok(true);\n});\n';
  const result = runCase(after);
  assert.equal(result.status, 1, result.stdout);
});
