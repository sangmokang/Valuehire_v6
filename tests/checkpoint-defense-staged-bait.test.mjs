import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const cleanups = [];

test.after(() => {
  for (const directory of cleanups) rmSync(directory, { recursive: true, force: true });
});

function git(cwd, ...args) {
  return execFileSync("git", args, {
    cwd,
    encoding: "utf8",
    env: { ...process.env, GIT_CONFIG_NOSYSTEM: "1" },
  }).trim();
}

function cloneHead() {
  const parent = mkdtempSync(join(tmpdir(), "checkpoint-staged-bait-"));
  cleanups.push(parent);
  const cwd = join(parent, "repo");
  execFileSync("git", ["clone", "-q", "--no-local", ROOT, cwd]);
  git(cwd, "checkout", "-q", git(ROOT, "rev-parse", "HEAD"));
  return cwd;
}

test("blocks staged gate and checkpoint-test bait that differs from the candidate blobs", () => {
  const cwd = cloneHead();
  writeFileSync(join(cwd, "tools/strict/checkpoint-gate.mjs"), "process.exit(0);\n");
  writeFileSync(join(cwd, "tests/checkpoint-gate.test.mjs"), "");
  git(cwd, "add", "tools/strict/checkpoint-gate.mjs", "tests/checkpoint-gate.test.mjs");
  const result = spawnSync(
    "bash",
    ["scripts/verify/run-acceptance.sh", "scripts/acceptance-checkpoint-defense.sh", "HEAD"],
    { cwd, encoding: "utf8", timeout: 120_000 },
  );
  assert.notEqual(result.status, 0, `staged bait survived\nstdout=${result.stdout}\nstderr=${result.stderr}`);
});
