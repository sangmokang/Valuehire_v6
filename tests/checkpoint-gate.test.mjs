import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const GATE = join(ROOT, "tools/strict/checkpoint-gate.mjs");
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
      GIT_AUTHOR_NAME: "checkpoint test",
      GIT_AUTHOR_EMAIL: "checkpoint@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint test",
      GIT_COMMITTER_EMAIL: "checkpoint@example.invalid",
    },
  }).trim();
}
function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}
function makeRepo({ hardLimit = 600, ledgerScopes, scanner = true, sot = true } = {}) {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-gate-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  if (sot) {
    write(
      cwd,
      "docs/sot/coding-principles.md",
      `# fixture SOT\n| P11 | file budget | soft 2 / hard ${hardLimit} LOC |\n`,
    );
  }
  if (scanner) {
    copyFileSync(join(ROOT, "verify.sh"), join(cwd, "verify.sh"));
    write(cwd, ".secret-patterns.default", "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  }
  if (ledgerScopes !== undefined) {
    const wu = { id: "WU-3a", ac: "checkpoint gate", status: "red", commit: null };
    if (ledgerScopes.length > 0) wu.scope = ledgerScopes;
    write(
      cwd,
      ".strict/run-ledger/r-1787525327788-6723.json",
      `${JSON.stringify({
        run_id: "r-1787525327788-6723",
        task: "checkpoint fixture",
        state: "BUILD",
        contract_sha256: "0".repeat(64),
        approvals: [],
        wus: [wu],
        findings_ref: null,
        next_action: "run checkpoint",
        updated_at: "2026-08-24T00:00:00.000Z",
      })}\n`,
    );
  }
  write(cwd, "src/app.mjs", "export const value = 1;\n");
  write(
    cwd,
    "tests/unit.test.mjs",
    'import assert from "node:assert/strict";\n' +
      'import test from "node:test";\n' +
      'test("value", () => {\n' +
      "  assert.equal(1, 1);\n" +
      "  assert.ok(true);\n" +
      "});\n",
  );
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "baseline");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}
function runGate(cwd, base, ...extra) {
  const result = spawnSync(process.execPath, [GATE, "--base", base, "--json", ...extra], {
    cwd,
    encoding: "utf8",
  });
  let body;
  try {
    body = JSON.parse(result.stdout);
  } catch (error) {
    assert.fail(
      `checkpoint gate did not emit JSON (exit=${result.status})\nstdout=${result.stdout}\nstderr=${result.stderr}\n${error}`,
    );
  }
  assert.deepEqual(Object.keys(body).sort(), ["pass", "violations"]);
  assert.ok(Array.isArray(body.violations));
  return { ...result, body };
}
function runRawGate(cwd, ...args) {
  const result = spawnSync(process.execPath, [GATE, ...args], { cwd, encoding: "utf8" });
  return { ...result, body: JSON.parse(result.stdout) };
}
function runRawGateWithEnv(cwd, env, ...args) {
  const result = spawnSync(process.execPath, [GATE, ...args], {
    cwd,
    encoding: "utf8",
    env: { ...process.env, ...env },
  });
  return { ...result, body: JSON.parse(result.stdout) };
}
function expectViolation(result, check, file) {
  assert.equal(result.status, 1, result.stderr);
  assert.equal(result.body.pass, false);
  assert.ok(
    result.body.violations.some(
      (violation) => violation.check === check && (!file || violation.file === file),
    ),
    JSON.stringify(result.body, null, 2),
  );
}
function expectPass(result) {
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.body, { pass: true, violations: [] });
}
test("scope: active wus ledger rejects a staged file outside its declared scope", () => {
  const { cwd, base } = makeRepo({ ledgerScopes: ["src/**"] });
  write(cwd, "docs/unrelated.md", "unrelated\n");
  git(cwd, "add", "docs/unrelated.md");
  expectViolation(runGate(cwd, base), "scope", "docs/unrelated.md");
});
test("scope: --scope fallback accepts a matching staged file when run ledger is absent", () => {
  const { cwd, base } = makeRepo();
  expectPass(runGate(cwd, base));
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectPass(runGate(cwd, base, "--scope", "src/**"));
});
test("scope: current A ledger without file declarations falls back to --scope", () => {
  const { cwd, base } = makeRepo({ ledgerScopes: [] });
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectPass(runGate(cwd, base, "--scope", "src/**"));
});
test("scope: a scope-less current open WU overrides an older green WU scope", () => {
  const { cwd, base } = makeRepo();
  write(
    cwd,
    ".strict/run-ledger/r-1787525327788-6723.json",
    `${JSON.stringify({
      updated_at: "2026-08-24T00:00:00.000Z",
      wus: [
        { id: "WU-old", status: "green", scope: ["docs/**"] },
        { id: "WU-current", status: "open" },
      ],
    })}\n`,
  );
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectPass(runGate(cwd, base, "--scope", "src/**"));
});
test("scope: the latest scope-less run ledger overrides an older scoped run ledger", () => {
  const { cwd, base } = makeRepo();
  write(
    cwd,
    ".strict/run-ledger/r-old.json",
    `${JSON.stringify({
      updated_at: "2026-08-23T00:00:00.000Z",
      wus: [{ id: "WU-old", status: "green", scope: ["docs/**"] }],
    })}\n`,
  );
  write(
    cwd,
    ".strict/run-ledger/r-current.json",
    `${JSON.stringify({
      updated_at: "2026-08-24T00:00:00.000Z",
      wus: [{ id: "WU-current", status: "red" }],
    })}\n`,
  );
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectPass(runGate(cwd, base, "--scope", "src/**"));
});
test("scope: checkpoint uses the latest green WU declaration in one run ledger", () => {
  const { cwd, base } = makeRepo();
  write(
    cwd,
    ".strict/run-ledger/r-1787525327788-6723.json",
    `${JSON.stringify({
      updated_at: "2026-08-24T00:00:00.000Z",
      wus: [
        { id: "WU-old", status: "green", scope: ["docs/**"] },
        { id: "WU-3a", status: "green", scope: ["src/**"] },
      ],
    })}\n`,
  );
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectPass(runGate(cwd, base));
});
test("scope: missing run ledger and missing --scope fails closed", () => {
  const { cwd, base } = makeRepo();
  write(cwd, "src/app.mjs", "export const value = 2;\n");
  git(cwd, "add", "src/app.mjs");
  expectViolation(runGate(cwd, base), "scope");
});
test("size limit reads the index SOT when the worktree path cannot be read", () => {
  const { cwd, base } = makeRepo({ ledgerScopes: ["src/**"] });
  write(cwd, "docs/unrelated.md", "outside\n");
  git(cwd, "add", "docs/unrelated.md");
  rmSync(join(cwd, "docs/sot/coding-principles.md"));
  mkdirSync(join(cwd, "docs/sot/coding-principles.md"));
  const result = runGate(cwd, base);
  expectViolation(result, "scope", "docs/unrelated.md");
  assert.ok(!result.body.violations.some((violation) => violation.check === "size-limit"));
});
test("CLI emits JSON input violation when --base has no value before --json", () => {
  const { cwd } = makeRepo();
  const result = runRawGate(cwd, "--base", "--json");
  expectViolation(result, "input");
});
test("CLI emits JSON when the git index cannot be read", () => {
  const { cwd, base } = makeRepo();
  write(cwd, "corrupt-index", "not a git index\n");
  const result = runRawGateWithEnv(
    cwd,
    { GIT_INDEX_FILE: join(cwd, "corrupt-index") },
    "--base",
    base,
    "--json",
    "--scope",
    "src/**",
  );
  expectViolation(result, "input");
});
test("secrets: delegates staged content to the existing repository scanner", () => {
  const { cwd, base } = makeRepo();
  const canary = ["CHECKPOINT", "CANARY", "ABCDEFGHIJKL"].join("_");
  write(cwd, "src/app.mjs", `export const credential = ${JSON.stringify(canary)};\n`);
  git(cwd, "add", "src/app.mjs");
  mkdirSync(join(cwd, "nested"));
  expectViolation(runGate(join(cwd, "nested"), base, "--scope", "src/**"), "secrets", "src/app.mjs");
});
test("secrets: existing repository scanner allows a clean staged blob", () => {
  const { cwd, base } = makeRepo();
  write(cwd, "src/app.mjs", 'export const message = "safe";\n');
  git(cwd, "add", "src/app.mjs");
  expectPass(runGate(cwd, base, "--scope", "src/**"));
});
test("secrets: checkpoint sources pass real scanner patterns without fake weakening markers", () => {
  const { cwd, base } = makeRepo();
  copyFileSync(join(ROOT, ".secret-patterns.default"), join(cwd, ".secret-patterns.default"));
  mkdirSync(join(cwd, "tools/strict"), { recursive: true });
  copyFileSync(GATE, join(cwd, "tools/strict/checkpoint-gate.mjs"));
  copyFileSync(join(ROOT, "tools/strict/checkpoint-js-scan.mjs"), join(cwd, "tools/strict/checkpoint-js-scan.mjs"));
  copyFileSync(join(ROOT, "tests/checkpoint-gate.test.mjs"), join(cwd, "tests/checkpoint-gate.test.mjs"));
  git(cwd, "add", "tools/strict/checkpoint-gate.mjs", "tools/strict/checkpoint-js-scan.mjs", "tests/checkpoint-gate.test.mjs");
  expectPass(runGate(cwd, base, "--scope", "tools/strict/**", "--scope", "tests/**"));
});
test("secrets: conservative fallback rejects a credential when verify.sh is absent", () => {
  const { cwd, base } = makeRepo({ scanner: false });
  const canary = ["AKIA", "0123456789ABCDEF"].join("");
  write(cwd, "src/app.mjs", `export const credential = ${JSON.stringify(canary)};\n`);
  git(cwd, "add", "src/app.mjs");
  expectViolation(runGate(cwd, base, "--scope", "src/**"), "secrets", "src/app.mjs");
});
for (const modifier of ["skip", "only", "todo"]) {
  test(`test weakening: ${modifier} increase is rejected`, () => {
    const { cwd, base } = makeRepo();
    const extra =
      modifier === "todo"
        ? 'test.todo("later");\n'
        : modifier === "only"
          ? 'fit("later", () => { assert.ok(true); });\n'
          : 'test.\\u0073kip("later", () => { assert.ok(true); });\n';
    write(
      cwd,
      "tests/unit.test.mjs",
      'import assert from "node:assert/strict";\n' +
        'import test from "node:test";\n' +
        'test("value", () => { assert.equal(1, 1); assert.ok(true); });\n' +
        extra,
    );
    git(cwd, "add", "tests/unit.test.mjs");
    expectViolation(
      runGate(cwd, base, "--scope", "tests/**"),
      "test-weakening",
      "tests/unit.test.mjs",
    );
  });
}
for (const fixture of [
  {
    name: "node:test skip boolean option",
    body: 'test("value", { ["skip"]: !0 }, () => { assert.equal(1, 1); assert.ok(true); });\n',
  },
  {
    name: "node:test numeric skip option",
    body: 'test("value", { skip: 1 }, () => { assert.equal(1, 1); assert.ok(true); });\n',
  },
  {
    name: "node:test only option",
    body: 'test["\\u{6f}nly"]("later", () => { assert.equal(1, 1); assert.ok(true); });\n',
  },
  {
    name: "node:test todo option",
    body: 'test("value", { todo: "later" }, () => { assert.equal(1, 1); assert.ok(true); });\n',
  },
  {
    name: "destructured skip alias inside template interpolation",
    body: 'const { skip } = test; `${skip("later", () => {})}`;\ntest("value", () => { assert.equal(1, 1); assert.ok(true); });\n',
  },
  { name: "static string concatenation key", body: 'test["sk" + "ip"]("later", () => { assert.equal(1, 1); assert.ok(true); });\n' },
  {
    name: "static template key skip after division",
    body:
      'test("value", () => { assert.equal(1, 1); assert.ok(true); });\n' +
      'function marker() { return /"/; }\n' +
      'const of = 2; const half = of / 2, hidden = test[`sk${"i"}p`]("later", () => {}), tail = 2 / 1;\n',
  },
]) {
  test(`test weakening: ${fixture.name} is rejected`, () => {
    const { cwd, base } = makeRepo();
    write(
      cwd,
      "tests/unit.test.mjs",
      'import assert from "node:assert/strict";\n' +
        'import test from "node:test";\n' +
        fixture.body,
    );
    git(cwd, "add", "tests/unit.test.mjs");
    expectViolation(
      runGate(cwd, base, "--scope", "tests/**"),
      "test-weakening",
      "tests/unit.test.mjs",
    );
  });
}
test("test weakening: assertion decrease after a quote regex is rejected", () => {
  const { cwd } = makeRepo();
  write(
    cwd,
    "tests/unit.test.mjs",
    'import assert from "node:assert/strict";\n' +
      'import test from "node:test";\n' +
      'test("value", () => { assert.equal(1, 1); assert(true); });\n',
  );
  git(cwd, "add", "tests/unit.test.mjs");
  git(cwd, "commit", "-qm", "add quote regex assertions");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, "tests/unit.test.mjs", 'import test from "node:test";\nfunction marker() { return /assert.ok(1) assert.ok(2)/; }\ntest("value", () => {});\n');
  git(cwd, "add", "tests/unit.test.mjs");
  expectViolation(
    runGate(cwd, base, "--scope", "tests/**"),
    "test-weakening",
    "tests/unit.test.mjs",
  );
});
for (const fixture of [
  ["commenting out", "// assert.ok(true);"],
  ["block-commenting", "/* assert.ok(true); */"],
  ["replacing with a string literal", 'const disabled = "assert.ok(true)";'],
  ["destructuring with no-op methods", "const noop = { equal() {}, ok() {} }; ({ assert } = { assert: noop }); assert.ok(true);"],
  ["array-destructuring a no-op assertion", "const noop = { equal() {}, ok() {} }; [assert] = [noop]; assert.ok(true);"],
  ["shadowing with a function parameter", "const noop = { equal() {}, ok() {} }; function run(assert) { assert.equal(1, 2); assert.ok(false); } run(noop);"],
  ["shadowing with an arrow parameter", "const noop = { equal() {}, ok() {} }; [noop].forEach((assert) => { assert.equal(1, 2); assert.ok(false); });"],
  ["shadowing with a method parameter", "const noop = { equal() {}, ok() {} }; const runner = { run(assert) { assert.equal(1, 2); assert.ok(false); } }; runner.run(noop);"],
  ["shadowing with a catch parameter", "const noop = { equal() {}, ok() {} }; try { throw noop; } catch (assert) { assert.equal(1, 2); assert.ok(false); }"],
  ["overwriting methods with Object.assign", "Object.assign(assert, { equal() {}, ok() {} }); assert.equal(1, 2); assert.ok(false);"],
  ["overwriting methods with Reflect.set", "Reflect.set(assert, 'equal', () => {}); Reflect.set(assert, 'ok', () => {}); assert.equal(1, 2); assert.ok(false);"],
  ["shadowing with an object rest binding", "const noop = { equal() {}, ok() {} }; const { ...assert } = noop; assert.equal(1, 2); assert.ok(false);"],
  ["shadowing with an array rest binding", "const noop = { equal() {}, ok() {} }; const [ ...assert ] = [noop]; assert.equal(1, 2); assert.ok(false);"],
  ["shadowing with a rest parameter binding", "const noop = { equal() {}, ok() {} }; function run(...[assert]) { assert.equal(1, 2); assert.ok(false); } run(noop);"],
  ["overwriting a global assertion binding", "globalThis.expect = () => ({ toBe() {} }); expect(1).toBe(2); expect(false).toBe(true);"],
  ["overwriting a computed global assertion binding", "globalThis['ex' + 'pect'] = () => ({ toBe() {} }); expect(1).toBe(2); expect(false).toBe(true);"],
]) {
  test(`test weakening: ${fixture[0]} an assertion is rejected`, () => {
    const { cwd, base } = makeRepo();
    write(
      cwd,
      "tests/unit.test.mjs",
      'import assert from "node:assert/strict";\n' +
        'import test from "node:test";\n' +
        `test("value", () => { assert.equal(1, 1); ${fixture[1]} });\n`,
    );
    git(cwd, "add", "tests/unit.test.mjs");
    expectViolation(runGate(cwd, base, "--scope", "tests/**"), "test-weakening", "tests/unit.test.mjs");
  });
}
test("test weakening: a local no-op assertion import is rejected", () => {
  const { cwd, base } = makeRepo();
  write(cwd, "src/fake-assert.mjs", "export default { equal() {}, ok() {} };\n");
  write(cwd, "tests/unit.test.mjs", 'import assert from "../src/fake-assert.mjs";\nimport test from "node:test";\ntest("value", () => { assert.equal(1, 2); assert.ok(false); });\n');
  git(cwd, "add", "src/fake-assert.mjs", "tests/unit.test.mjs");
  expectViolation(runGate(cwd, base, "--scope", "src/**", "--scope", "tests/**"), "test-weakening", "tests/unit.test.mjs");
});
for (const [label, assertionImport, calls] of [
  ["default alias", 'import strictAssert from "node:assert/strict";', "strictAssert.equal(1, 1); strictAssert.ok(true);"],
  ["namespace alias", 'import * as strictAssert from "node:assert/strict";', "strictAssert.equal(1, 1); strictAssert.ok(true);"],
  ["named imports", 'import { equal, ok } from "node:assert/strict";', "equal(1, 1); ok(true);"],
  ["require alias", 'import { createRequire } from "node:module"; const require = createRequire(import.meta.url); const strictAssert = require("node:assert/strict");', "strictAssert.equal(1, 1); strictAssert.ok(true);"],
  ["destructured require", 'import { createRequire } from "node:module"; const require = createRequire(import.meta.url); const { equal, ok } = require("node:assert/strict");', "equal(1, 1); ok(true);"],
]) test(`test weakening: trusted assertion ${label} passes`, () => {
  const { cwd, base } = makeRepo();
  write(cwd, "tests/unit.test.mjs", `${assertionImport}\nimport test from "node:test";\ntest("value", () => { ${calls} });\n`);
  git(cwd, "add", "tests/unit.test.mjs");
  expectPass(runGate(cwd, base, "--scope", "tests/**"));
});
test("test weakening: a newly added skipped test is rejected against a zero baseline", () => {
  const { cwd, base } = makeRepo();
  write(
    cwd,
    "tests/new.test.mjs",
    'import test from "node:test";\n' + 'test?.skip("disabled at birth", () => {});\n',
  );
  git(cwd, "add", "tests/new.test.mjs");
  expectViolation(
    runGate(cwd, base, "--scope", "tests/**"),
    "test-weakening",
    "tests/new.test.mjs",
  );
});
test("counter-AC: deleting a Python test file must never exit zero", () => {
  const { cwd, base: initialBase } = makeRepo();
  write(cwd, "humansearch/tests/test_gate.py", "def test_gate():\n    assert True\n");
  git(cwd, "add", "humansearch/tests/test_gate.py");
  git(cwd, "commit", "-qm", "add python test");
  const base = git(cwd, "rev-parse", "HEAD");
  assert.notEqual(base, initialBase);
  git(cwd, "rm", "-q", "humansearch/tests/test_gate.py");
  expectViolation(
    runGate(cwd, base, "--scope", "humansearch/tests/**"),
    "test-weakening",
    "humansearch/tests/test_gate.py",
  );
});
test("test weakening: Python assertion decrease is rejected", () => {
  const { cwd } = makeRepo();
  write(
    cwd,
    "humansearch/tests/test_gate.py",
    "def test_gate():\n    assert True\n    assert 1 == 1\n",
  );
  git(cwd, "add", "humansearch/tests/test_gate.py");
  git(cwd, "commit", "-qm", "add python assertions");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, "humansearch/tests/test_gate.py", "def test_gate():\n    assert True\n");
  git(cwd, "add", "humansearch/tests/test_gate.py");
  expectViolation(
    runGate(cwd, base, "--scope", "humansearch/tests/**"),
    "test-weakening",
    "humansearch/tests/test_gate.py",
  );
});
test("test weakening: Python skip increase is rejected", () => {
  const { cwd } = makeRepo();
  write(cwd, "humansearch/tests/test_gate.py", "def test_gate():\n    assert True\n");
  git(cwd, "add", "humansearch/tests/test_gate.py");
  git(cwd, "commit", "-qm", "add python test");
  const base = git(cwd, "rev-parse", "HEAD");
  write(
    cwd,
    "humansearch/tests/test_gate.py",
    "import pytest\n\n@pytest.mark.skip(reason=\"later\")\ndef test_gate():\n    assert True\n",
  );
  git(cwd, "add", "humansearch/tests/test_gate.py");
  expectViolation(
    runGate(cwd, base, "--scope", "humansearch/tests/**"),
    "test-weakening",
    "humansearch/tests/test_gate.py",
  );
});
test("counter-AC: deleting a shell acceptance test must never exit zero", () => {
  const { cwd, base: initialBase } = makeRepo();
  write(cwd, "scripts/acceptance-fixture.sh", "#!/usr/bin/env bash\nexit 0\n");
  git(cwd, "add", "scripts/acceptance-fixture.sh");
  git(cwd, "commit", "-qm", "add shell acceptance");
  const base = git(cwd, "rev-parse", "HEAD");
  assert.notEqual(base, initialBase);
  git(cwd, "rm", "-q", "scripts/acceptance-fixture.sh");
  expectViolation(
    runGate(cwd, base, "--scope", "scripts/acceptance-*"),
    "test-weakening",
    "scripts/acceptance-fixture.sh",
  );
});
test("test weakening: replacing shell assertions with exit zero is rejected", () => {
  const { cwd } = makeRepo();
  write(
    cwd,
    "scripts/acceptance-fixture.sh",
    '#!/usr/bin/env bash\nset -euo pipefail\ngrep -q "value" src/app.mjs\ntest -s src/app.mjs\n',
  );
  git(cwd, "add", "scripts/acceptance-fixture.sh");
  git(cwd, "commit", "-qm", "add shell acceptance");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, "scripts/acceptance-fixture.sh", "#!/usr/bin/env bash\nexit 0\n");
  git(cwd, "add", "scripts/acceptance-fixture.sh");
  expectViolation(
    runGate(cwd, base, "--scope", "scripts/acceptance-*"),
    "test-weakening",
    "scripts/acceptance-fixture.sh",
  );
});
test("counter-AC: deleting a test file must never exit zero", () => {
  const { cwd, base } = makeRepo();
  git(cwd, "rm", "-q", "tests/unit.test.mjs");
  expectViolation(
    runGate(cwd, base, "--scope", "tests/**"),
    "test-weakening",
    "tests/unit.test.mjs",
  );
});
test("counter-AC: moving a test outside recognized test paths must never exit zero", () => {
  const { cwd, base } = makeRepo();
  mkdirSync(join(cwd, "src"), { recursive: true });
  git(cwd, "mv", "tests/unit.test.mjs", "src/retired.mjs");
  expectViolation(
    runGate(cwd, base, "--scope", "tests/**", "--scope", "src/**"),
    "test-weakening",
    "tests/unit.test.mjs",
  );
});
test("test weakening: clean test and an unrelated skip property pass", () => {
  const { cwd, base } = makeRepo();
  write(
    cwd,
    "tests/unit.test.mjs",
    'import assert from "node:assert/strict";\n' +
      'import test from "node:test";\n' +
      'const options = { skip: false }; const paging = { skip: 1, limit: 20 };\n' +
      'test("view", () => { const view = { hello: true }; assert.ok(view)\nconst { value: copiedView } = { value: view }; assert.equal(Boolean(copiedView), true); });\n',
  );
    git(cwd, "add", "tests/unit.test.mjs");
  expectPass(runGate(cwd, base, "--scope", "tests/**"));
});
test("size limit: a code file one line above the parsed SOT hard limit is rejected", () => {
  const { cwd, base } = makeRepo({ hardLimit: 3 });
  write(cwd, "docs/sot/coding-principles.md", "| P11 | worktree decoy | hard 9999 LOC |\n");
  write(cwd, "src/app.mjs", "one\ntwo\nthree\nfour\n");
  git(cwd, "add", "src/app.mjs");
  expectViolation(runGate(cwd, base, "--scope", "src/**"), "size-limit", "src/app.mjs");
});
test("size limit: a code file exactly at the parsed SOT hard limit passes", () => {
  const { cwd, base } = makeRepo({ hardLimit: 3 });
  write(cwd, "src/app.mjs", "one\ntwo\nthree\n");
  git(cwd, "add", "src/app.mjs");
  expectPass(runGate(cwd, base, "--scope", "src/**"));
});
test("size limit: directly authored test code is not exempt from the hard limit", () => {
  const { cwd, base } = makeRepo({ hardLimit: 3 });
  write(cwd, "tests/oversized.test.mjs", "one\ntwo\nthree\nfour\n");
  git(cwd, "add", "tests/oversized.test.mjs");
  expectViolation(runGate(cwd, base, "--scope", "tests/**"), "size-limit", "tests/oversized.test.mjs");
});
test("size limit: missing SOT falls back to 500 lines", () => {
  const { cwd, base } = makeRepo({ sot: false });
  write(cwd, "src/app.mjs", `${Array.from({ length: 501 }, (_, index) => `line${index}`).join("\n")}\n`);
  git(cwd, "add", "src/app.mjs");
  const result = runGate(cwd, base, "--scope", "src/**");
  expectViolation(result, "size-limit", "src/app.mjs");
  assert.match(result.body.violations.find((item) => item.check === "size-limit").detail, /500/);
});
test("size limit: missing P11 ignores unrelated hard numbers and falls back to 500", () => {
  const { cwd } = makeRepo();
  write(cwd, "docs/sot/coding-principles.md", "| P10 | unrelated | hard 9999 LOC |\n");
  git(cwd, "add", "docs/sot/coding-principles.md");
  git(cwd, "commit", "-qm", "remove P11 fixture");
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, "src/app.mjs", `${Array.from({ length: 501 }, (_, index) => `line${index}`).join("\n")}\n`);
  git(cwd, "add", "src/app.mjs");
  const result = runGate(cwd, base, "--scope", "src/**");
  expectViolation(result, "size-limit", "src/app.mjs");
  assert.match(result.body.violations.find((item) => item.check === "size-limit").detail, /500/);
});
test("size limit: missing SOT allows exactly the 500-line fallback boundary", () => {
  const { cwd, base } = makeRepo({ sot: false });
  write(cwd, "src/app.mjs", `${Array.from({ length: 500 }, (_, index) => `line${index}`).join("\n")}\n`);
  git(cwd, "add", "src/app.mjs");
  expectPass(runGate(cwd, base, "--scope", "src/**"));
});
for (const extension of ["JS", "TSX"]) test(`size limit: uppercase .${extension} uses the P11 boundary`, () => {
  const { cwd, base } = makeRepo();
  const file = `src/oversized.${extension}`;
  write(cwd, file, `${Array.from({ length: 601 }, (_, index) => `line${index}`).join("\n")}\n`); git(cwd, "add", file);
  expectViolation(runGate(cwd, base, "--scope", "src/**"), "size-limit", file);
  write(cwd, file, `${Array.from({ length: 600 }, (_, index) => `line${index}`).join("\n")}\n`); git(cwd, "add", file);
  expectPass(runGate(cwd, base, "--scope", "src/**"));
});
for (const extension of ["JS", "TSX"]) test(`test weakening: uppercase .${extension} assertion decrease is rejected`, () => {
  const { cwd } = makeRepo();
  const file = `tests/unit.${extension}`;
  const strong = 'import assert from "node:assert/strict";\nassert.equal(1, 1);\nassert.ok(true);\n';
  write(cwd, file, strong); git(cwd, "add", file); git(cwd, "commit", "-qm", `add uppercase ${extension} test`);
  const base = git(cwd, "rev-parse", "HEAD");
  write(cwd, file, 'import assert from "node:assert/strict";\nassert.equal(1, 1);\n'); git(cwd, "add", file);
  expectViolation(runGate(cwd, base, "--scope", "tests/**"), "test-weakening", file);
  write(cwd, file, `${strong}assert.notEqual(1, 2);\n`); git(cwd, "add", file);
  assert.equal(git(cwd, "diff", "--cached", "--name-only", base, "--"), file);
  expectPass(runGate(cwd, base, "--scope", "tests/**"));
});
