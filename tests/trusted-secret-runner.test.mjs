import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const RUNNER = join(ROOT, "tools/strict/trusted-secret-scan.mjs");
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
      GIT_AUTHOR_NAME: "trusted secret runner test",
      GIT_AUTHOR_EMAIL: "trusted-secret@example.invalid",
      GIT_COMMITTER_NAME: "trusted secret runner test",
      GIT_COMMITTER_EMAIL: "trusted-secret@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo(content) {
  const cwd = mkdtempSync(join(tmpdir(), "trusted-secret-runner-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q", "-b", "task/trusted-secret-runner");
  write(cwd, "verify.sh", readFileSync(join(ROOT, "verify.sh"), "utf8"));
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "src/value.mjs", 'export const value = "safe";\n');
  git(cwd, "add", "verify.sh", ".secret-patterns.default", "src/value.mjs");
  git(cwd, "commit", "-qm", "fixture authority");
  write(cwd, "src/value.mjs", content);
  git(cwd, "add", "src/value.mjs");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\necho 'PASS: decoy'\nexit 0\n");
  write(cwd, ".secret-patterns.default", "WEAK_PATTERN\n");
  return cwd;
}

function run(cwd) {
  return spawnSync(process.execPath, [RUNNER], { cwd, encoding: "utf8" });
}

test("trusted runner rejects a staged secret despite worktree verify and pattern decoys", () => {
  const canary = ["CHECKPOINT", "CANARY", "ABCDEFGHIJKL"].join("_");
  const result = run(makeRepo(`export const credential = ${JSON.stringify(canary)};\n`));
  assert.equal(result.status, 1, `${result.stdout}\n${result.stderr}`);
  assert.match(result.stdout, /^FAIL: trusted secret scan/m);
});

test("trusted runner passes a clean staged blob and emits a verdict", () => {
  const result = run(makeRepo('export const value = "still-safe";\n'));
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  assert.match(result.stdout, /^PASS: trusted secret scan/m);
});

test("pre-push and GitHub CI execute the trusted runner", () => {
  const hook = readFileSync(join(ROOT, "hooks/pre-push"), "utf8");
  const workflow = readFileSync(join(ROOT, ".github/workflows/verify.yml"), "utf8");
  assert.match(hook, /node tools\/strict\/trusted-secret-scan\.mjs/);
  assert.match(workflow, /run: node tools\/strict\/trusted-secret-scan\.mjs/);
});
