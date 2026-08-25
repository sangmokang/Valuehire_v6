import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const GATE = join(ROOT, "tools/strict/checkpoint-gate.mjs");
const cleanups = [];

after(() => {
  for (const path of cleanups) rmSync(path, { recursive: true, force: true });
});

function git(cwd, ...args) {
  return execFileSync("git", args, { cwd, encoding: "utf8" }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo() {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-function-budget-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q");
  git(cwd, "config", "user.email", "test@example.com");
  git(cwd, "config", "user.name", "Test User");
  write(
    cwd,
    "docs/sot/coding-principles.md",
    "| **P11** | code budget | file soft 300 / hard 600 LOC; function soft 60 / hard 100 LOC |\n",
  );
  write(cwd, "README.md", "base\n");
  git(cwd, "add", ".");
  git(cwd, "commit", "-qm", "base");
  return { cwd, base: git(cwd, "rev-parse", "HEAD") };
}

function runGate(cwd, base, path, content) {
  write(cwd, path, content);
  git(cwd, "add", path);
  const result = spawnSync(
    process.execPath,
    [GATE, "--base", base, "--json", "--scope", "src/**"],
    { cwd, encoding: "utf8" },
  );
  return { ...result, body: JSON.parse(result.stdout) };
}

function expectPass(result) {
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.body, { pass: true, violations: [] });
}

function expectFunctionLimit(result, path, actual = 101, limit = 100) {
  assert.equal(result.status, 1, result.stderr);
  assert.equal(result.body.pass, false);
  assert.ok(
    result.body.violations.some(
      (item) =>
        item.check === "size-limit" &&
        item.file === path &&
        item.detail.includes(`${actual}`) &&
        item.detail.includes(`${limit}`),
    ),
    JSON.stringify(result.body),
  );
}

function expectUnsupported(result, path) {
  assert.equal(result.status, 1, result.stderr);
  assert.ok(
    result.body.violations.some(
      (item) => item.check === "size-limit" && item.file === path && /unsupported/i.test(item.detail),
    ),
    JSON.stringify(result.body),
  );
}

function expectFileLimit(result, path, actual = 601, limit = 600) {
  assert.equal(result.status, 1, result.stderr);
  assert.ok(
    result.body.violations.some(
      (item) =>
        item.check === "size-limit" &&
        item.file === path &&
        item.detail.includes(`${actual}`) &&
        item.detail.includes(`${limit}`),
    ),
    JSON.stringify(result.body),
  );
}

function javascriptFunction(lines) {
  return [
    "function target() {",
    ...Array.from({ length: lines - 2 }, (_, index) => `  void ${index};`),
    "}",
  ].join("\n") + "\n";
}

function pythonFunction(lines) {
  return [
    "def target():",
    ...Array.from({ length: lines - 1 }, (_, index) => `    value_${index} = ${index}`),
  ].join("\n") + "\n";
}

function shellFunction(lines) {
  return ["target() {", ...Array.from({ length: lines - 2 }, () => "  :"), "}"].join("\n") + "\n";
}

test("JavaScript function at the 100-line hard boundary passes", () => {
  const { cwd, base } = makeRepo();
  expectPass(runGate(cwd, base, "src/app.mjs", javascriptFunction(100)));
});

test("JavaScript function at 101 lines fails", () => {
  const { cwd, base } = makeRepo();
  expectFunctionLimit(runGate(cwd, base, "src/app.mjs", javascriptFunction(101)), "src/app.mjs");
});

test("Python function at the 100-line hard boundary passes", () => {
  const { cwd, base } = makeRepo();
  expectPass(runGate(cwd, base, "src/app.py", pythonFunction(100)));
});

test("Python function at 101 lines fails", () => {
  const { cwd, base } = makeRepo();
  expectFunctionLimit(runGate(cwd, base, "src/app.py", pythonFunction(101)), "src/app.py");
});

test("shell function at the 100-line hard boundary passes", () => {
  const { cwd, base } = makeRepo();
  expectPass(runGate(cwd, base, "src/app.sh", shellFunction(100)));
});

test("shell function at 101 lines fails", () => {
  const { cwd, base } = makeRepo();
  expectFunctionLimit(runGate(cwd, base, "src/app.sh", shellFunction(101)), "src/app.sh");
});

test("an unsupported code extension fails closed instead of reporting zero functions", () => {
  const { cwd, base } = makeRepo();
  const result = runGate(cwd, base, "src/app.go", "package main\nfunc main() {}\n");
  assert.equal(result.status, 1, result.stderr);
  assert.ok(
    result.body.violations.some(
      (item) => item.check === "size-limit" && item.file === "src/app.go" && /unsupported/i.test(item.detail),
    ),
    JSON.stringify(result.body),
  );
});

const previouslyUnclassifiedCode = [
  "c", "h", "cpp", "cc", "hpp", "m", "vue", "svelte", "lua", "pl", "sql", "scala",
];

for (const extension of previouslyUnclassifiedCode) {
  test(`.${extension} source fails closed when no function parser exists`, () => {
    const { cwd, base } = makeRepo();
    const path = `src/app.${extension}`;
    expectUnsupported(runGate(cwd, base, path, "source line\n"), path);
  });

  test(`.${extension} source cannot bypass the 600-line file limit`, () => {
    const { cwd, base } = makeRepo();
    const path = `src/app.${extension}`;
    const content = Array.from({ length: 601 }, (_, index) => `source line ${index}`).join("\n") + "\n";
    expectFileLimit(runGate(cwd, base, path, content), path);
  });
}
