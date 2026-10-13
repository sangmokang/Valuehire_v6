import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { countJavaScriptWeakening } from "../tools/strict/checkpoint-js-scan.mjs";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SELF = fileURLToPath(import.meta.url);
const VALIDATE_ROOT = process.env.CHECKPOINT_MUTATION_VALIDATE_ROOT;
const cleanups = [];

function isolatedEnv(extra = {}) {
  const env = { ...process.env, ...extra, GIT_CONFIG_NOSYSTEM: "1" };
  for (const name of ["GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"]) delete env[name];
  return env;
}

function git(cwd, ...args) {
  return execFileSync("git", args, {
    cwd,
    encoding: "utf8",
    env: isolatedEnv({
      GIT_AUTHOR_NAME: "checkpoint mutation test",
      GIT_AUTHOR_EMAIL: "checkpoint-mutation@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint mutation test",
      GIT_COMMITTER_EMAIL: "checkpoint-mutation@example.invalid",
    }),
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function installBundle(cwd, bundle) {
  mkdirSync(join(cwd, "tools/strict"), { recursive: true });
  for (const path of ["verify.sh", "tools/strict/checkpoint-gate.mjs", "tools/strict/checkpoint-js-scan.mjs"]) {
    copyFileSync(join(bundle, path), join(cwd, path));
  }
}

function makeRepo(bundle, { baseSecret = false } = {}) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-mutation-repo-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  installBundle(cwd, bundle);
  write(cwd, "docs/sot/coding-principles.md", "| **P11** | budget | soft 300 / hard 600 LOC |\n");
  write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  write(cwd, "src/app.mjs", "export const value = 1;\n");
  write(
    cwd,
    "tests/unit.test.mjs",
    'import assert from "node:assert/strict";\n' +
      'import test from "node:test";\n' +
      'test("value", () => { assert.equal(1, 1); assert.ok(true); });\n',
  );
  if (baseSecret) write(cwd, "src/legacy.mjs", 'export const legacy = "CHECKPOINT_CANARY_ABCDEFGHIJKL";\n');
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function runGate(cwd, base, ...extraScopes) {
  const result = spawnSync(
    process.execPath,
    [join(cwd, "tools/strict/checkpoint-gate.mjs"), "--base", base, "--json", "--scope", "src/**", "--scope", "tests/**", ...extraScopes.flatMap((scope) => ["--scope", scope])],
    { cwd, encoding: "utf8", env: isolatedEnv() },
  );
  let body;
  try {
    body = JSON.parse(result.stdout);
  } catch (error) {
    throw new Error(`gate output is not one JSON object (exit=${result.status}): ${error.message}`);
  }
  assert.deepEqual(Object.keys(body).sort(), ["pass", "violations"]);
  assert.ok(Array.isArray(body.violations));
  assert.equal(result.status, body.pass ? 0 : 1);
  return { ...result, body };
}

function expectViolation(result, check, file) {
  assert.equal(result.status, 1);
  assert.equal(result.body.pass, false);
  assert.ok(result.body.violations.some((item) => item.check === check && item.file === file));
}

function validateBundle(bundle) {
  {
    const { cwd, base } = makeRepo(bundle);
    write(cwd, "src/app.mjs", 'export const credential = "CHECKPOINT_CANARY_ABCDEFGHIJKL";\n');
    git(cwd, "add", "src/app.mjs");
    expectViolation(runGate(cwd, base), "secrets", "src/app.mjs");
  }
  {
    const { cwd, base } = makeRepo(bundle);
    write(
      cwd,
      "tests/unit.test.mjs",
      'import assert from "node:assert/strict";\n' +
        'import test from "node:test";\n' +
        'test("value", () => { assert.equal(1, 1); });\n',
    );
    git(cwd, "add", "tests/unit.test.mjs");
    expectViolation(runGate(cwd, base), "test-weakening", "tests/unit.test.mjs");
  }
  {
    const { cwd, base } = makeRepo(bundle, { baseSecret: true });
    write(cwd, "src/app.mjs", "export const value = 2;\n");
    git(cwd, "add", "src/app.mjs");
    expectViolation(runGate(cwd, base), "secrets", "");
  }
  {
    const { cwd, base } = makeRepo(bundle);
    write(cwd, "src/app.mjs", "export const value = 2;\n");
    git(cwd, "add", "src/app.mjs");
    assert.deepEqual(runGate(cwd, base).body, { pass: true, violations: [] });
  }
}

function makeBundle(mutation) {
  const bundle = mkdtempSync(join(tmpdir(), "checkpoint-mutation-bundle-"));
  cleanups.push(bundle);
  mkdirSync(join(bundle, "tools/strict"), { recursive: true });
  copyFileSync(join(ROOT, "verify.sh"), join(bundle, "verify.sh"));
  copyFileSync(join(ROOT, "tools/strict/checkpoint-gate.mjs"), join(bundle, "tools/strict/checkpoint-gate.mjs"));
  copyFileSync(join(ROOT, "tools/strict/checkpoint-js-scan.mjs"), join(bundle, "tools/strict/checkpoint-js-scan.mjs"));
  if (mutation === "verify-exit-zero") write(bundle, "verify.sh", "#!/usr/bin/env bash\nexit 0\n");
  if (mutation === "scanner-always-zero") {
    write(bundle, "tools/strict/checkpoint-js-scan.mjs", "export function countJavaScriptWeakening() { return { skip: 0, only: 0, todo: 0, assertions: 0 }; }\n");
  }
  if (mutation === "gate-exit-zero") write(bundle, "tools/strict/checkpoint-gate.mjs", "process.exit(0);\n");
  if (mutation === "gate-fixed-pass") {
    write(bundle, "tools/strict/checkpoint-gate.mjs", 'process.stdout.write("{\\"pass\\":true,\\"violations\\":[]}\\n");\n');
  }
  if (mutation === "gate-empty") write(bundle, "tools/strict/checkpoint-gate.mjs", "");
  return bundle;
}

function runIndependentValidation(bundle) {
  return spawnSync(process.execPath, [SELF], {
    cwd: ROOT,
    encoding: "utf8",
    env: isolatedEnv({ CHECKPOINT_MUTATION_VALIDATE_ROOT: bundle }),
  });
}

if (VALIDATE_ROOT) {
  try {
    validateBundle(VALIDATE_ROOT);
    process.exitCode = 0;
  } catch (error) {
    process.stderr.write(`${error.stack ?? error}\n`);
    process.exitCode = 1;
  } finally {
    for (const directory of cleanups) rmSync(directory, { recursive: true, force: true });
  }
} else {
  test.after(() => {
    for (const directory of cleanups) rmSync(directory, { recursive: true, force: true });
  });

  test("shell acceptance cannot bypass unchanged assertions", () => {
    const { cwd, base } = makeRepo(makeBundle("original"));
    write(cwd, "scripts/acceptance-check.sh", 'grep -q "value" src/app.mjs\ntest -s src/app.mjs\n');
    git(cwd, "add", "scripts/acceptance-check.sh");
    git(cwd, "commit", "-qm", "add acceptance check");
    const before = git(cwd, "rev-parse", "HEAD");
    for (const bypass of ['exit 0\n', 'grep -q "value" src/app.mjs || true\n']) {
      write(cwd, "scripts/acceptance-check.sh", `${bypass}grep -q "value" src/app.mjs\ntest -s src/app.mjs\n`);
      git(cwd, "add", "scripts/acceptance-check.sh");
      expectViolation(runGate(cwd, before, "scripts/**"), "test-weakening", "scripts/acceptance-check.sh");
    }
    assert.ok(base);
  });

  test("Python module skip and xfail are rejected", () => {
    const { cwd } = makeRepo(makeBundle("original"));
    write(cwd, "tests/test_gate.py", "def test_gate():\n    assert True\n");
    git(cwd, "add", "tests/test_gate.py");
    git(cwd, "commit", "-qm", "add python check");
    const base = git(cwd, "rev-parse", "HEAD");
    for (const marker of ["skip", "xfail"]) {
      write(cwd, "tests/test_gate.py", `import pytest\npytestmark = pytest.mark.${marker}(reason="later")\ndef test_gate():\n    assert True\n`);
      git(cwd, "add", "tests/test_gate.py");
      expectViolation(runGate(cwd, base), "test-weakening", "tests/test_gate.py");
    }
  });

  test("trusted assertion member chain is counted without shadowing", () => {
    const counts = countJavaScriptWeakening('import assert from "node:assert/strict"; assert.strict.equal(1, 1); assert.ok(true);');
    assert.equal(counts.assertions, 2);
  });

  test("an existing assertion reference cannot hide later assertion deletion", () => {
    const { cwd } = makeRepo(makeBundle("original"));
    const baseBody = 'import assert from "node:assert/strict"; helper(assert); assert.ok(true); assert.equal(1, 1);\n';
    write(cwd, "tests/unit.test.mjs", baseBody);
    git(cwd, "add", "tests/unit.test.mjs");
    git(cwd, "commit", "-qm", "add assertion reference");
    const base = git(cwd, "rev-parse", "HEAD");
    write(cwd, "tests/unit.test.mjs", baseBody.replace(" assert.equal(1, 1);", ""));
    git(cwd, "add", "tests/unit.test.mjs");
    expectViolation(runGate(cwd, base), "test-weakening", "tests/unit.test.mjs");
  });

  test("overwriting an assertion method remains a weakening marker", () => {
    const counts = countJavaScriptWeakening('import assert from "node:assert/strict"; assert.ok = () => {}; assert.ok(true);');
    assert.equal(counts.skip, 1);
  });

  test("early return in a JavaScript test is treated as weakening", () => {
    const counts = countJavaScriptWeakening('test("value", () => { return; assert.ok(true); });');
    assert.equal(counts.skip, 1);
  });

  test("staged SOT cannot raise its own size limit", () => {
    const { cwd, base } = makeRepo(makeBundle("original"));
    write(cwd, "docs/sot/coding-principles.md", "| **P11** | budget | hard 9999 LOC |\n");
    write(cwd, "src/app.mjs", `${"export const value = 1;\n".repeat(601)}`);
    git(cwd, "add", "docs/sot/coding-principles.md", "src/app.mjs");
    expectViolation(runGate(cwd, base, "docs/**"), "size-limit", "src/app.mjs");
  });

  test("trusted original bundle makes independent validation exit zero", () => {
    const result = runIndependentValidation(makeBundle("original"));
    assert.equal(result.status, 0, result.stderr);
  });

  for (const mutation of [
    "verify-exit-zero",
    "scanner-always-zero",
    "gate-exit-zero",
    "gate-fixed-pass",
    "gate-empty",
  ]) {
    test(`${mutation} makes independent validation exit one`, () => {
      const result = runIndependentValidation(makeBundle(mutation));
      assert.equal(result.status, 1, `stdout=${result.stdout}\nstderr=${result.stderr}`);
    });
  }
}
