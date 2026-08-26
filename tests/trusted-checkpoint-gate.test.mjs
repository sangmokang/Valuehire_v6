import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const RUNNER = join(ROOT, "tools/strict/index-checkpoint-gate.mjs");
const RUN_ID = "trusted-gate-fixture";
const WU_ID = "WU-TRUSTED-GATE";
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
      GIT_AUTHOR_NAME: "trusted gate test",
      GIT_AUTHOR_EMAIL: "trusted-gate@example.invalid",
      GIT_COMMITTER_NAME: "trusted gate test",
      GIT_COMMITTER_EMAIL: "trusted-gate@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo() {
  const cwd = mkdtempSync(join(tmpdir(), "trusted-checkpoint-gate-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  mkdirSync(join(cwd, "tools/strict"), { recursive: true });
  for (const path of [
    "verify.sh",
    ".secret-patterns.default",
    "tools/strict/checkpoint-gate.mjs",
    "tools/strict/checkpoint-js-scan.mjs",
    "tools/strict/checkpoint-policy.mjs",
    "tools/strict/checkpoint-secrets.mjs",
    "tools/strict/index-checkpoint-gate.mjs",
  ]) copyFileSync(join(ROOT, path), join(cwd, path));
  write(cwd, "docs/sot/coding-principles.md", "| **P11** | budget | soft 300 / hard 600 LOC |\n");
  write(cwd, "src/app.mjs", "export const value = 1;\n");
  write(cwd, "tests/unit.test.mjs", 'import assert from "node:assert/strict";\nassert.equal(1, 1);\nassert.ok(true);\n');
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    schema_version: "valuehire.strict-run/v2",
    run_id: RUN_ID,
    wus: [{ id: WU_ID, status: "open", scope: ["src/**", "tests/**"] }],
  })}\n`);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function args(base) {
  return ["--base", base, "--json", "--run-id", RUN_ID, "--wu-id", WU_ID];
}

function direct(cwd, base) {
  return spawnSync(process.execPath, [join(cwd, "tools/strict/checkpoint-gate.mjs"), ...args(base)], {
    cwd,
    encoding: "utf8",
  });
}

function indexed(cwd, base) {
  const runner = git(cwd, "show", ":tools/strict/index-checkpoint-gate.mjs");
  return spawnSync(process.execPath, ["--input-type=module", "-", ...args(base)], {
    cwd,
    encoding: "utf8",
    input: runner,
  });
}

function stage(cwd, path, content) {
  write(cwd, path, content);
  git(cwd, "add", path);
}

test("direct gate rejects an unstaged broad policy stub", () => {
  const { cwd, base } = makeRepo();
  stage(cwd, "outside.txt", "outside\n");
  write(cwd, "tools/strict/checkpoint-policy.mjs", "export function secureLedgerScopes(){return {scopes:[\"**\"]};}\n");
  const result = direct(cwd, base);
  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stdout, /trusted runtime|worktree|index/i);
});

test("direct gate rejects an unstaged secret scanner stub", () => {
  const { cwd, base } = makeRepo();
  stage(cwd, "src/app.mjs", 'export const key = "CHECKPOINT_CANARY_ABCDEFGHIJKL";\n');
  write(cwd, "tools/strict/checkpoint-secrets.mjs", "export function runTrustedSecretScan(){return {status:0,stdout:\"PASS: fake\\n\",stderr:\"\"};}\n");
  const result = direct(cwd, base);
  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stdout, /trusted runtime|worktree|index/i);
});

test("direct gate rejects an unstaged JavaScript weakening stub", () => {
  const { cwd, base } = makeRepo();
  stage(cwd, "tests/unit.test.mjs", 'import assert from "node:assert/strict";\n');
  write(cwd, "tools/strict/checkpoint-js-scan.mjs", "export function countJavaScriptWeakening(){return {skip:0,only:0,todo:0,assertions:0};}\n");
  const result = direct(cwd, base);
  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stdout, /trusted runtime|worktree|index/i);
});

test("index runner executes approved modules despite every unstaged sibling stub", () => {
  const { cwd, base } = makeRepo();
  stage(cwd, "outside.txt", "outside\n");
  write(cwd, "tools/strict/checkpoint-gate.mjs", 'process.stdout.write("{\\"pass\\":true,\\"violations\\":[]}\\n");\n');
  write(cwd, "tools/strict/checkpoint-policy.mjs", "export function secureLedgerScopes(){return {scopes:[\"**\"]};}\n");
  write(cwd, "tools/strict/checkpoint-secrets.mjs", "export function runTrustedSecretScan(){return {status:0,stdout:\"PASS: fake\\n\",stderr:\"\"};}\n");
  write(cwd, "tools/strict/checkpoint-js-scan.mjs", "export function countJavaScriptWeakening(){return {skip:0,only:0,todo:0,assertions:0};}\n");
  const result = indexed(cwd, base);
  assert.equal(result.status, 1, result.stdout);
  const body = JSON.parse(result.stdout);
  assert.ok(body.violations.some((item) => item.check === "scope" && item.file === "outside.txt"));
});

test("verification SOT requires the canonical index runner invocation", () => {
  const sot = readFileSync(join(ROOT, "docs/sot/verification-commands.md"), "utf8");
  assert.match(sot, /git show :tools\/strict\/index-checkpoint-gate\.mjs \| node --input-type=module -/);
  assert.match(sot, /작업 폴더.*직접 실행.*판정 근거.*아니/s);
});
