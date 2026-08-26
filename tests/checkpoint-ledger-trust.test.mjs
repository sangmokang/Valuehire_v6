import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync, spawnSync } from "node:child_process";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const GATE = join(ROOT, "tools/strict/checkpoint-gate.mjs");
const RUN_ID = "strict-fixture-run";
const WU_ID = "WU-3b-1";
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
      GIT_AUTHOR_NAME: "ledger trust test",
      GIT_AUTHOR_EMAIL: "ledger-trust@example.invalid",
      GIT_COMMITTER_NAME: "ledger trust test",
      GIT_COMMITTER_EMAIL: "ledger-trust@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function ledger({ runId = RUN_ID, wus } = {}) {
  return `${JSON.stringify({
    schema_version: "valuehire.strict-run/v2",
    run_id: runId,
    issue_id: "LOCAL-TEST",
    branch: "fixture",
    worktree: "/tmp/fixture",
    base_sha: "0".repeat(40),
    wus: wus ?? [{ id: WU_ID, status: "open", scope: ["src/**"] }],
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`;
}

function makeRepo(options = {}) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-ledger-trust-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 300 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\necho 'PASS: fixture scanner'\n");
  write(cwd, "src/app.mjs", "export const value = 1;\n");
  if (options.ledger !== false) {
    write(cwd, `.strict/run-ledger/${RUN_ID}.json`, options.ledger ?? ledger());
  }
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function runGate(cwd, base, ...extra) {
  const result = spawnSync(
    process.execPath,
    [GATE, "--base", base, "--json", "--run-id", RUN_ID, "--wu-id", WU_ID, ...extra],
    { cwd, encoding: "utf8" },
  );
  let body;
  try {
    body = JSON.parse(result.stdout);
  } catch (error) {
    assert.fail(`gate emitted invalid JSON: ${error}\nstdout=${result.stdout}\nstderr=${result.stderr}`);
  }
  return { ...result, body };
}

function runLegacyGate(cwd, base) {
  const result = spawnSync(process.execPath, [GATE, "--base", base, "--json", "--scope", "src/**"], {
    cwd,
    encoding: "utf8",
  });
  return { ...result, body: JSON.parse(result.stdout) };
}

function expectViolation(result, detail) {
  assert.equal(result.status, 1, result.stderr);
  assert.equal(result.body.pass, false);
  assert.ok(
    result.body.violations.some(
      (violation) => violation.check === "scope" && (!detail || violation.detail.includes(detail)),
    ),
    JSON.stringify(result.body, null, 2),
  );
}

test("secure scope reads the exact ledger from the index, not an unstaged broad decoy", () => {
  const { cwd, base } = makeRepo();
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, ledger({
    wus: [{ id: WU_ID, status: "open", scope: ["**"] }],
  }));
  write(cwd, "docs/outside.md", "outside\n");
  git(cwd, "add", "docs/outside.md");
  expectViolation(runGate(cwd, base), "outside declared scope");
});

test("secure scope ignores a newer worktree ledger with another run id", () => {
  const { cwd, base } = makeRepo();
  write(cwd, ".strict/run-ledger/decoy.json", ledger({
    runId: "decoy",
    wus: [{ id: WU_ID, status: "open", scope: ["**"] }],
  }).replace("2026-08-27T00:00:00.000Z", "2099-01-01T00:00:00.000Z"));
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  const result = runGate(cwd, base);
  assert.equal(result.status, 0, JSON.stringify(result.body));
  assert.deepEqual(result.body, { pass: true, violations: [] });
});

test("secure scope rejects CLI scopes that disagree with the indexed ledger", () => {
  const { cwd, base } = makeRepo();
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectViolation(runGate(cwd, base, "--scope", "**"), "CLI scope does not match");
});

test("secure scope accepts an identical CLI and indexed ledger scope", () => {
  const { cwd, base } = makeRepo();
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  const result = runGate(cwd, base, "--scope", "src/**");
  assert.equal(result.status, 0, JSON.stringify(result.body));
});

test("secure scope fails when the exact indexed ledger is missing", () => {
  const { cwd, base } = makeRepo({ ledger: false });
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectViolation(runGate(cwd, base), "not present in the Git index");
});

test("secure scope rejects duplicate WU ids", () => {
  const duplicate = ledger({
    wus: [
      { id: WU_ID, status: "open", scope: ["src/**"] },
      { id: WU_ID, status: "open", scope: ["**"] },
    ],
  });
  const { cwd, base } = makeRepo({ ledger: duplicate });
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectViolation(runGate(cwd, base), "duplicate WU id");
});

test("secure scope rejects a ledger whose embedded run id differs from the requested id", () => {
  const { cwd, base } = makeRepo({ ledger: ledger({ runId: "other-run" }) });
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectViolation(runGate(cwd, base), "run_id mismatch");
});

test("secure scope rejects zero staged targets", () => {
  const { cwd, base } = makeRepo();
  expectViolation(runGate(cwd, base), "zero staged targets");
});

test("explicit legacy scope also rejects zero staged targets", () => {
  const { cwd, base } = makeRepo();
  expectViolation(runLegacyGate(cwd, base), "zero staged targets");
});
