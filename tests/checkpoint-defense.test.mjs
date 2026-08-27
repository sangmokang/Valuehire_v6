import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const CHECKER = join(ROOT, "tools/strict/checkpoint-defense.mjs");
const CONTRACT = join(ROOT, "contracts/checkpoint-defense.json");
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
      GIT_AUTHOR_NAME: "checkpoint defense test",
      GIT_AUTHOR_EMAIL: "checkpoint-defense@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint defense test",
      GIT_COMMITTER_EMAIL: "checkpoint-defense@example.invalid",
    },
  }).trim();
}

function cloneHead() {
  const parent = mkdtempSync(join(tmpdir(), "checkpoint-defense-"));
  cleanups.push(parent);
  const cwd = join(parent, "repo");
  execFileSync("git", ["clone", "-q", "--no-local", ROOT, cwd]);
  git(cwd, "checkout", "-q", git(ROOT, "rev-parse", "HEAD"));
  return cwd;
}

function run(cwd, contract = join(cwd, "contracts/checkpoint-defense.json")) {
  const result = spawnSync(
    process.execPath,
    [CHECKER, "--candidate", "HEAD", "--contract", contract, "--json"],
    { cwd, encoding: "utf8", timeout: 120_000 },
  );
  let body = null;
  try {
    body = JSON.parse(result.stdout);
  } catch {
    assert.fail(`defense checker did not emit JSON\nstatus=${result.status}\nstdout=${result.stdout}\nstderr=${result.stderr}`);
  }
  return { ...result, body };
}

test("approved candidate blobs run exactly 67 passing checkpoint tests and direct fixtures", () => {
  const cwd = cloneHead();
  const result = run(cwd);
  assert.equal(result.status, 0, JSON.stringify(result.body, null, 2));
  assert.equal(result.body.pass, true);
  assert.deepEqual(result.body.tests, {
    tests: 67,
    pass: 67,
    fail: 0,
    cancelled: 0,
    skipped: 0,
    todo: 0,
  });
  assert.deepEqual(result.body.direct, { normal: true, blocked: true });
});

test("candidate blob verification ignores uncommitted worktree bait", () => {
  const cwd = cloneHead();
  writeFileSync(join(cwd, "tools/strict/checkpoint-gate.mjs"), "process.exit(0);\n");
  writeFileSync(join(cwd, "tests/checkpoint-gate.test.mjs"), "");
  const result = run(cwd);
  assert.equal(result.status, 0, JSON.stringify(result.body, null, 2));
  assert.equal(result.body.pass, true);
  assert.equal(result.body.candidate, git(cwd, "rev-parse", "HEAD"));
});

test("an approved test count cannot be reduced below the fixed 67-test contract", () => {
  const cwd = cloneHead();
  const altered = join(cwd, "reduced-contract.json");
  const contract = JSON.parse(readFileSync(join(cwd, "contracts/checkpoint-defense.json"), "utf8"));
  contract.expected_tests = 66;
  contract.minimum_tests = 66;
  writeFileSync(altered, `${JSON.stringify(contract, null, 2)}\n`);
  const result = run(cwd, altered);
  assert.notEqual(result.status, 0, JSON.stringify(result.body, null, 2));
  assert.equal(result.body.pass, false);
});

test("a candidate commit with a changed gate blob is rejected", () => {
  const cwd = cloneHead();
  writeFileSync(join(cwd, "tools/strict/checkpoint-gate.mjs"), "process.exit(0);\n");
  git(cwd, "add", "tools/strict/checkpoint-gate.mjs");
  git(cwd, "commit", "-qm", "mutate gate");
  const result = run(cwd);
  assert.notEqual(result.status, 0, JSON.stringify(result.body, null, 2));
  assert.equal(result.body.pass, false);
  assert.ok(result.body.violations.some((item) => item.check === "fingerprint"));
});

test("a candidate commit with an empty checkpoint test blob is rejected", () => {
  const cwd = cloneHead();
  writeFileSync(join(cwd, "tests/checkpoint-gate.test.mjs"), "");
  git(cwd, "add", "tests/checkpoint-gate.test.mjs");
  git(cwd, "commit", "-qm", "empty checkpoint test");
  const result = run(cwd);
  assert.notEqual(result.status, 0, JSON.stringify(result.body, null, 2));
  assert.equal(result.body.pass, false);
  assert.ok(result.body.violations.some((item) => item.check === "fingerprint"));
});

test("a repository with no candidate targets fails closed instead of checking zero files", () => {
  const cwd = cloneHead();
  const empty = mkdtempSync(join(tmpdir(), "checkpoint-defense-empty-"));
  cleanups.push(empty);
  git(empty, "init", "-q");
  writeFileSync(join(empty, "README.md"), "empty\n");
  git(empty, "add", "README.md");
  git(empty, "commit", "-qm", "empty candidate");
  cpSync(join(cwd, "contracts"), join(empty, "contracts"), { recursive: true });
  const result = run(empty);
  assert.notEqual(result.status, 0, JSON.stringify(result.body, null, 2));
  assert.equal(result.body.pass, false);
  assert.ok(result.body.checked > 0);
});
