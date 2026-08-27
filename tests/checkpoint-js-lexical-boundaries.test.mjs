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
      GIT_AUTHOR_NAME: "checkpoint lexical boundary test",
      GIT_AUTHOR_EMAIL: "checkpoint-lexical-boundary@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint lexical boundary test",
      GIT_COMMITTER_EMAIL: "checkpoint-lexical-boundary@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo(scope) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-lexical-boundary-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC, function hard 100 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "JavaScript lexical boundary fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", ac: "lexical boundary", status: "red", scope }],
    findings_ref: null,
    next_action: "run checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  return cwd;
}

function runGate(cwd, base) {
  return spawnSync(process.execPath, [GATE, "--base", base, "--run-id", RUN_ID, "--json"], { cwd, encoding: "utf8" });
}

function assertionCase(after) {
  const cwd = makeRepo(["tests/**"]);
  write(cwd, "tests/status.test.mjs", "assert.equal(status, 1);\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "strong baseline");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, "tests/status.test.mjs", after);
  git(cwd, "add", "tests/status.test.mjs");
  return runGate(cwd, base);
}

for (const [name, source] of [
  ["void-prefixed regex", "assert.notEqual(status, 0);\nvoid /assert.equal(status, 1)/;\nassert.ok(true);\n"],
  ["returned regex", "assert.notEqual(status, 0);\nfunction verify() { return /assert.equal(status, 1)/; }\nverify();\nassert.ok(true);\n"],
  ["typeof-prefixed regex", "assert.notEqual(status, 0);\ntypeof /assert.equal(status, 1)/;\nassert.ok(true);\n"],
]) {
  test(`rejects assertion text hidden in a ${name}`, () => {
    const result = assertionCase(source);
    assert.equal(result.status, 1, result.stdout);
  });
}

test("allows a preserved assertion after string and numeric division", () => {
  const source = 'const a = "x" / 2;\nassert.equal(status, 1);\nconst b = 1 / 2;\n';
  const result = assertionCase(source);
  assert.equal(result.status, 0, result.stdout);
});

function longFunction(regexLine) {
  return `export function boundary(x) {\n  ${regexLine}\n${"  void 0;\n".repeat(98)}}\n`;
}

function functionCase(content) {
  const cwd = makeRepo(["src/**"]);
  write(cwd, "README.md", "baseline\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "function baseline");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, "src/boundary.mjs", content);
  git(cwd, "add", "src/boundary.mjs");
  return runGate(cwd, base);
}

test("rejects 101-line functions whether regex braces follow return or assignment", () => {
  for (const regexLine of ["if (x) return /}/.test(x);", "const found = /}/.test(x);"]) {
    const result = functionCase(longFunction(regexLine));
    assert.equal(result.status, 1, result.stdout);
  }
});
