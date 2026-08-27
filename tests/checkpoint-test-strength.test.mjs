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
      GIT_AUTHOR_NAME: "checkpoint strength test",
      GIT_AUTHOR_EMAIL: "checkpoint-strength@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint strength test",
      GIT_COMMITTER_EMAIL: "checkpoint-strength@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo(path, before) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-strength-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 500 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  write(cwd, `.strict/run-ledger/${RUN_ID}.json`, `${JSON.stringify({
    run_id: RUN_ID,
    task: "strength fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", ac: "assertion strength", status: "red", scope: ["tests/**"] }],
    findings_ref: null,
    next_action: "run checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  write(cwd, path, before);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "strict baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function evaluate(path, before, after) {
  const { cwd, base } = makeRepo(path, before);
  write(cwd, path, after);
  git(cwd, "add", path);
  const result = spawnSync(
    process.execPath,
    [GATE, "--base", base, "--run-id", RUN_ID, "--json"],
    { cwd, encoding: "utf8" },
  );
  let body;
  try {
    body = JSON.parse(result.stdout);
  } catch {
    assert.fail(`gate did not emit JSON\nstatus=${result.status}\nstdout=${result.stdout}\nstderr=${result.stderr}`);
  }
  return { ...result, body };
}

function expectWeakening(path, before, after) {
  const result = evaluate(path, before, after);
  assert.equal(result.status, 1, JSON.stringify(result.body, null, 2));
  assert.equal(result.body.pass, false);
  assert.ok(
    result.body.violations.some(
      (violation) => violation.check === "test-weakening" && violation.file === path,
    ),
    JSON.stringify(result.body, null, 2),
  );
}

function expectPass(path, before, after) {
  const result = evaluate(path, before, after);
  assert.equal(result.status, 0, JSON.stringify(result.body, null, 2));
  assert.deepEqual(result.body, { pass: true, violations: [] });
}

test("rejects exact equality weakened to inequality despite an added assertion", () => {
  expectWeakening(
    "tests/status.test.mjs",
    "assert.equal(status, 1);\n",
    "assert.notEqual(status, 0);\nassert.ok(true);\n",
  );
});

test("rejects anchored message match weakened to a partial match despite an added assertion", () => {
  expectWeakening(
    "tests/message.test.mjs",
    "assert.match(message, /^input violation$/);\n",
    "assert.match(message, /input/);\nassert.ok(true);\n",
  );
});

test("rejects an anchored match replaced by a match-all expression and padding", () => {
  expectWeakening(
    "tests/wildcard.test.mjs",
    "assert.match(message, /^input violation$/);\n",
    "assert.match(message, /^.*$/);\nassert.ok(true);\n",
  );
});

test("rejects Python equality weakened to inequality despite assert True padding", () => {
  expectWeakening(
    "tests/test_status.py",
    "assert status == 1\n",
    "assert status != 0\nassert True\n",
  );
});

test("rejects two strong assertions weakened behind several meaningless assertions", () => {
  expectWeakening(
    "tests/two-strong.test.mjs",
    "assert.equal(status, 1);\nassert.match(message, /^input violation$/);\n",
    "assert.notEqual(status, 0);\nassert.match(message, /input/);\nassert.ok(true);\nassert.ok(1);\nassert.ok({});\n",
  );
});

test("allows an independent assertion while preserving exact and anchored expectations", () => {
  expectPass(
    "tests/stronger.test.mjs",
    "assert.equal(status, 1);\nassert.match(message, /^input violation$/);\n",
    "assert.equal(status, 1);\nassert.match(message, /^input violation$/);\nassert.equal(reason, \"scope\");\n",
  );
});

test("allows a broad assertion to be strengthened to exact equality", () => {
  expectPass(
    "tests/broad-to-exact.test.mjs",
    "assert.ok(status);\n",
    "assert.equal(status, 1);\n",
  );
});

for (const [path, content] of [
  ["tests/new-valid.test.mjs", "assert.equal(status, 1);\n"],
  ["tests/test_new_valid.py", "assert status == 1\n"],
  ["tests/new-valid.sh", "#!/usr/bin/env bash\ntest \"$status\" -eq 1\n"],
]) {
  test(`allows a new valid test file: ${path}`, () => {
    expectPass(path, "", content);
  });
}
