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
      GIT_AUTHOR_NAME: "checkpoint async boundary test",
      GIT_AUTHOR_EMAIL: "checkpoint-async-boundary@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint async boundary test",
      GIT_COMMITTER_EMAIL: "checkpoint-async-boundary@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function runCase(path, baseline, after) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-async-boundary-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "async execution boundary fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", ac: "async execution boundary", status: "red", scope: ["tests/**"] }],
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

for (const [name, after] of [
  ["unref timer block", "setTimeout(() => { assert.equal(status, 1); }, 1e9).unref();\nassert.ok(true);\n"],
  ["swallowed Promise callback", "Promise.resolve().then(() => { assert.equal(status, 1); }).catch(() => {});\nassert.ok(true);\n"],
  ["uncalled async block arrow", "const hidden = async () => { assert.equal(status, 1); };\nvoid hidden;\nassert.ok(true);\n"],
]) {
  test(`rejects exact assertion hidden by ${name}`, () => {
    const result = runCase("tests/status.test.mjs", "assert.equal(status, 1);\n", after);
    assert.equal(result.status, 1, result.stdout);
  });
}

test("rejects Python equality weakened inside a pytest-discovered test", () => {
  const baseline = "def test_status():\n    assert status == 1\n";
  const weakened = "def test_status():\n    assert status != 0\n    assert True\n";
  const result = runCase("tests/test_status.py", baseline, weakened);
  assert.equal(result.status, 1, result.stdout);
});
