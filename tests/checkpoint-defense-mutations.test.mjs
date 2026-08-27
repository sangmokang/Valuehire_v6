import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const CHECKER = join(ROOT, "tools/strict/checkpoint-defense.mjs");
const CONTRACT = join(ROOT, "contracts/checkpoint-defense.json");
const WRAPPER_PATH = "scripts/acceptance-checkpoint-defense.sh";
const RUNNER = join(ROOT, "scripts/verify/run-acceptance.sh");
const CI_CHECKER = join(ROOT, "scripts/verify/check-ci-step-integrity.sh");
const REGISTRY_CHECKER = join(ROOT, "scripts/verify/check-mechanism-registry.sh");
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
      GIT_AUTHOR_NAME: "checkpoint mutation test",
      GIT_AUTHOR_EMAIL: "checkpoint-mutation@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint mutation test",
      GIT_COMMITTER_EMAIL: "checkpoint-mutation@example.invalid",
    },
  }).trim();
}

function cloneHead() {
  const parent = mkdtempSync(join(tmpdir(), "checkpoint-mutations-"));
  cleanups.push(parent);
  const cwd = join(parent, "repo");
  execFileSync("git", ["clone", "-q", "--no-local", ROOT, cwd]);
  git(cwd, "checkout", "-q", git(ROOT, "rev-parse", "HEAD"));
  return cwd;
}

function commitMutation(cwd, files, message) {
  for (const [path, content] of Object.entries(files)) writeFileSync(join(cwd, path), content);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", message);
}

function runChecker(cwd) {
  return spawnSync(
    process.execPath,
    [CHECKER, "--candidate", "HEAD", "--contract", CONTRACT, "--json"],
    { cwd, encoding: "utf8", timeout: 120_000 },
  );
}

function runWrapper(cwd) {
  return spawnSync("bash", [RUNNER, WRAPPER_PATH, "HEAD"], {
    cwd,
    encoding: "utf8",
    timeout: 120_000,
  });
}

function assertBlocked(result, label) {
  assert.notEqual(
    result.status,
    0,
    `${label} survived\nstdout=${result.stdout}\nstderr=${result.stderr}`,
  );
}

for (const [name, gate, checkpointTest] of [
  [
    "always-pass gate plus empty checkpoint test",
    'console.log(JSON.stringify({ pass: true, violations: [] }));\n',
    "",
  ],
  ["process.exit(0) gate plus empty checkpoint test", "process.exit(0);\n", ""],
  [
    "no-op gate plus fully skipped checkpoint test",
    "// no-op\n",
    'import test from "node:test";\ntest.skip("all checkpoint coverage", () => {});\n',
  ],
]) {
  test(`blocks ${name}`, () => {
    const cwd = cloneHead();
    commitMutation(cwd, {
      "tools/strict/checkpoint-gate.mjs": gate,
      "tests/checkpoint-gate.test.mjs": checkpointTest,
    }, name);
    assertBlocked(runChecker(cwd), name);
  });
}

test("blocks a checkpoint suite reduced to 66 tests", () => {
  const cwd = cloneHead();
  const original = readFileSync(join(cwd, "tests/checkpoint-gate.test.mjs"), "utf8");
  const reduced = original.replace(
    /test\("size limit: missing SOT allows exactly the 500-line fallback boundary"[\s\S]*?\n\}\);\n$/,
    "",
  );
  assert.notEqual(reduced, original, "fixture must remove one test declaration");
  commitMutation(cwd, { "tests/checkpoint-gate.test.mjs": reduced }, "reduce checkpoint tests");
  assertBlocked(runChecker(cwd), "66-test suite");
});

test("blocks replacement with 67 meaningless passing assertions", () => {
  const cwd = cloneHead();
  const meaningless = [
    'import assert from "node:assert/strict";',
    'import test from "node:test";',
    ...Array.from({ length: 67 }, (_, index) =>
      `test("meaningless ${index + 1}", () => assert.ok(true));`),
    "",
  ].join("\n");
  commitMutation(cwd, { "tests/checkpoint-gate.test.mjs": meaningless }, "replace with meaningless tests");
  assertBlocked(runChecker(cwd), "67 meaningless assertions");
});

test("blocks five independent-checker no-op forms through the higher acceptance wrapper", () => {
  const cwd = cloneHead();
  const mutants = {
    "exit zero": "process.exit(0);\n",
    true: "true;\n",
    "no-op": "void 0;\n",
    empty: "",
    "output only": 'console.log("PASS: checkpoint defense");\n',
  };
  for (const [name, content] of Object.entries(mutants)) {
    commitMutation(cwd, { "tools/strict/checkpoint-defense.mjs": content }, `checker ${name}`);
    assertBlocked(runWrapper(cwd), `checker ${name}`);
  }
});

test("blocks checkpoint CI step echo, false condition, continue-on-error, and deletion", () => {
  const cwd = cloneHead();
  const workflowPath = join(cwd, ".github/workflows/verify.yml");
  const original = readFileSync(workflowPath, "utf8");
  const command = "run: bash scripts/verify/run-acceptance.sh scripts/acceptance-checkpoint-defense.sh";
  assert.ok(original.includes(command), "checkpoint CI command must exist before mutation");
  const mutants = {
    echo: original.replace(command, "run: echo bash scripts/acceptance-checkpoint-defense.sh"),
    false: original.replace(
      "      - name: 인수 검사 checkpoint-defense",
      "      - name: 인수 검사 checkpoint-defense\n        if: ${{ false }}",
    ),
    continue: original.replace(
      "      - name: 인수 검사 checkpoint-defense",
      "      - name: 인수 검사 checkpoint-defense\n        continue-on-error: true",
    ),
    deletion: original.replace(
      /\n      - name: 인수 검사 checkpoint-defense[^\n]*\n        run: bash scripts\/verify\/run-acceptance\.sh scripts\/acceptance-checkpoint-defense\.sh\n/,
      "\n",
    ),
  };
  for (const [name, content] of Object.entries(mutants)) {
    assert.notEqual(content, original, `${name} mutation must alter workflow`);
    writeFileSync(workflowPath, content);
    const integrity = spawnSync("bash", [CI_CHECKER, workflowPath], { cwd, encoding: "utf8" });
    const registry = spawnSync("bash", [REGISTRY_CHECKER], {
      cwd,
      encoding: "utf8",
      env: { ...process.env, WORKFLOW_FILE: workflowPath },
    });
    assert.ok(
      integrity.status !== 0 || registry.status !== 0,
      `${name} CI mutation survived\nintegrity=${integrity.stdout}\nregistry=${registry.stdout}`,
    );
  }
});

test("blocks a candidate containing zero checkpoint targets", () => {
  const cwd = cloneHead();
  git(cwd, "rm", "-q", "tools/strict/checkpoint-gate.mjs", "tests/checkpoint-gate.test.mjs");
  git(cwd, "commit", "-qm", "remove checkpoint targets");
  assertBlocked(runChecker(cwd), "zero checkpoint targets");
});
