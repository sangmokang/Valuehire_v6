import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const GATE = join(ROOT, "tools/strict/checkpoint-gate.mjs");
const RUN_ID = "strict-secret-fixture";
const WU_ID = "WU-3b-2";
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
      GIT_AUTHOR_NAME: "secret trust test",
      GIT_AUTHOR_EMAIL: "secret-trust@example.invalid",
      GIT_COMMITTER_NAME: "secret trust test",
      GIT_COMMITTER_EMAIL: "secret-trust@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function sha256(text) {
  return createHash("sha256").update(text).digest("hex");
}

function makeRepo({ defaultPatterns = "CHECKPOINT_INDEX_[A-Z0-9]{12}\n", verify = "real" } = {}) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-secret-trust-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  write(cwd, "docs/sot/coding-principles.md", "| P11 | budget | soft 300 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", defaultPatterns);
  if (verify === "real") copyFileSync(join(ROOT, "verify.sh"), join(cwd, "verify.sh"));
  else write(cwd, "verify.sh", verify);
  write(cwd, "src/app.mjs", "export const value = 1;\n");
  write(
    cwd,
    `.strict/run-ledger/${RUN_ID}.json`,
    `${JSON.stringify({
      schema_version: "valuehire.strict-run/v2",
      run_id: RUN_ID,
      wus: [{ id: WU_ID, status: "open", scope: ["src/**"] }],
      updated_at: "2026-08-27T00:00:00.000Z",
    })}\n`,
  );
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function stage(cwd, content) {
  write(cwd, "src/app.mjs", content);
  git(cwd, "add", "src/app.mjs");
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

function expectSecretFailure(result, detail) {
  assert.equal(result.status, 1, result.stderr);
  assert.equal(result.body.pass, false);
  assert.ok(
    result.body.violations.some(
      (violation) => violation.check === "secrets" && (!detail || violation.detail.includes(detail)),
    ),
    JSON.stringify(result.body, null, 2),
  );
}

test("secure secrets ignore an unstaged weakened default pattern", () => {
  const { cwd, base } = makeRepo();
  write(cwd, ".secret-patterns.default", "WILL_NOT_MATCH\n");
  stage(cwd, 'export const value = "CHECKPOINT_INDEX_ABCDEFGHIJKL";\n');
  expectSecretFailure(runGate(cwd, base), "scanner failed");
});

test("secure secrets ignore an unstaged verify.sh exit-zero decoy", () => {
  const { cwd, base } = makeRepo();
  write(cwd, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  stage(cwd, 'export const value = "CHECKPOINT_INDEX_ABCDEFGHIJKL";\n');
  expectSecretFailure(runGate(cwd, base), "scanner failed");
});

test("secure secrets require an approval SHA when a local pattern file exists", () => {
  const { cwd, base } = makeRepo();
  write(cwd, ".secret-patterns", "CHECKPOINT_LOCAL_[A-Z0-9]{12}\n");
  stage(cwd, "export const value = 2;\n");
  expectSecretFailure(runGate(cwd, base), "approval SHA is required");
});

test("secure secrets reject a local pattern whose bytes do not match the approved SHA", () => {
  const { cwd, base } = makeRepo();
  write(cwd, ".secret-patterns", "WEAK_PATTERN\n");
  stage(cwd, "export const value = 2;\n");
  expectSecretFailure(
    runGate(cwd, base, "--secret-pattern-sha256", sha256("CHECKPOINT_LOCAL_[A-Z0-9]{12}\n")),
    "SHA-256 mismatch",
  );
});

test("secure secrets use a local pattern only after its SHA is approved", () => {
  const { cwd, base } = makeRepo();
  const local = "CHECKPOINT_LOCAL_[A-Z0-9]{12}\n";
  write(cwd, ".secret-patterns", local);
  stage(cwd, 'export const value = "CHECKPOINT_LOCAL_ABCDEFGHIJKL";\n');
  expectSecretFailure(
    runGate(cwd, base, "--secret-pattern-sha256", sha256(local)),
    "scanner failed",
  );
});

test("secure secrets fail when the indexed default pattern is missing", () => {
  const { cwd } = makeRepo();
  git(cwd, "rm", "-q", ".secret-patterns.default");
  git(cwd, "commit", "-qm", "remove pattern authority");
  const base = git(cwd, "rev-parse", "HEAD");
  stage(cwd, "export const value = 2;\n");
  expectSecretFailure(runGate(cwd, base), "not present in the Git index");
});

test("secure secrets fail when indexed patterns have zero effective entries", () => {
  const { cwd, base } = makeRepo({ defaultPatterns: "# comments only\n\n" });
  stage(cwd, "export const value = 2;\n");
  expectSecretFailure(runGate(cwd, base), "zero effective patterns");
});

test("secure secrets reject a trusted scanner that exits zero without output", () => {
  const { cwd, base } = makeRepo({ verify: "#!/usr/bin/env bash\nexit 0\n" });
  stage(cwd, "export const value = 2;\n");
  expectSecretFailure(runGate(cwd, base), "no verdict output");
});

test("secure secrets pass a clean staged blob with trusted indexed inputs", () => {
  const { cwd, base } = makeRepo();
  write(cwd, ".secret-patterns.default", "UNSTAGED_DECOY_[A-Z0-9]{12}\n");
  stage(cwd, "export const value = 2;\n");
  const result = runGate(cwd, base);
  assert.equal(result.status, 0, JSON.stringify(result.body));
  assert.deepEqual(result.body, { pass: true, violations: [] });
});
