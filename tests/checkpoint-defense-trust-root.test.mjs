import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
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
    env: {
      ...process.env,
      GIT_CONFIG_NOSYSTEM: "1",
      GIT_AUTHOR_NAME: "checkpoint trust root test",
      GIT_AUTHOR_EMAIL: "checkpoint-trust@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint trust root test",
      GIT_COMMITTER_EMAIL: "checkpoint-trust@example.invalid",
    },
  }).trim();
}

function cloneHead() {
  const parent = mkdtempSync(join(tmpdir(), "checkpoint-trust-root-"));
  cleanups.push(parent);
  const cwd = join(parent, "repo");
  execFileSync("git", ["clone", "-q", "--no-local", ROOT, cwd]);
  git(cwd, "checkout", "-q", git(ROOT, "rev-parse", "HEAD"));
  return cwd;
}

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

function commitApprovedMutation(cwd, files) {
  const contractPath = join(cwd, "contracts/checkpoint-defense.json");
  const contract = JSON.parse(readFileSync(contractPath, "utf8"));
  for (const [path, content] of Object.entries(files)) {
    writeFileSync(join(cwd, path), content);
    contract.fingerprints[path] = sha256(content);
  }
  writeFileSync(contractPath, `${JSON.stringify(contract, null, 2)}\n`);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "candidate approves its own mutation");
}

function runWrapper(cwd) {
  return spawnSync("bash", ["scripts/acceptance-checkpoint-defense.sh", "HEAD"], {
    cwd,
    encoding: "utf8",
    timeout: 120_000,
  });
}

test("rejects a no-op checker even when the candidate contract approves it", () => {
  const cwd = cloneHead();
  const checker = [
    'process.stdout.write(JSON.stringify({ pass: true, checked: 78, tests: { tests: 67, pass: 67, fail: 0, cancelled: 0, skipped: 0, todo: 0 }, direct: { normal: true, blocked: true }, violations: [] }) + "\\n");',
    "",
  ].join("\n");
  commitApprovedMutation(cwd, { "tools/strict/checkpoint-defense.mjs": checker });
  const result = runWrapper(cwd);
  assert.notEqual(result.status, 0, `${result.stdout}\n${result.stderr}`);
});

test("rejects 67 meaningless tests even when the candidate contract approves them", () => {
  const cwd = cloneHead();
  const meaningless = [
    'import assert from "node:assert/strict";',
    'import test from "node:test";',
    ...Array.from({ length: 67 }, (_, index) => `test("meaningless ${index + 1}", () => assert.ok(true));`),
    "",
  ].join("\n");
  commitApprovedMutation(cwd, { "tests/checkpoint-gate.test.mjs": meaningless });
  const result = runWrapper(cwd);
  assert.notEqual(result.status, 0, `${result.stdout}\n${result.stderr}`);
});
