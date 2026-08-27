#!/usr/bin/env node
import { createHash } from "node:crypto";
import { mkdtempSync, rmSync, writeFileSync, mkdirSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { spawnSync } from "node:child_process";

const DEFAULT_CONTRACT = "contracts/checkpoint-defense.json";
const FIXED_TEST_COUNT = 67;
const REQUIRED_PATHS = [
  "tools/strict/checkpoint-gate.mjs",
  "tests/checkpoint-gate.test.mjs",
  "tools/strict/checkpoint-defense.mjs",
];
const RUN_ID = "r-1787525327788-6723";

function parseArgs(argv) {
  const args = { candidate: "HEAD", contract: DEFAULT_CONTRACT, json: false };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") args.json = true;
    else if (arg === "--candidate") args.candidate = argv[++index];
    else if (arg === "--contract") args.contract = argv[++index];
    else throw new Error(`unknown argument: ${arg}`);
    if (args.candidate === undefined || args.contract === undefined) throw new Error(`${arg} requires a value`);
  }
  return args;
}

function git(args, options = {}) {
  const result = spawnSync("git", args, {
    cwd: options.cwd,
    encoding: options.encoding ?? "utf8",
    env: {
      ...process.env,
      GIT_CONFIG_NOSYSTEM: "1",
      GIT_AUTHOR_NAME: "checkpoint defense",
      GIT_AUTHOR_EMAIL: "checkpoint-defense@example.invalid",
      GIT_COMMITTER_NAME: "checkpoint defense",
      GIT_COMMITTER_EMAIL: "checkpoint-defense@example.invalid",
    },
    input: options.input,
    maxBuffer: 32 * 1024 * 1024,
  });
  if (result.status !== 0) throw new Error((result.stderr || result.stdout || "git failed").trim());
  return result.stdout;
}

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

function jsonResult(pass, fields) {
  return { pass, ...fields };
}

async function loadContract(path) {
  const contract = JSON.parse(await readFile(path, "utf8"));
  if (contract.version !== 1 || !contract.fingerprints || typeof contract.fingerprints !== "object") {
    throw new Error("checkpoint defense contract version/fingerprints are invalid");
  }
  if (contract.expected_tests !== FIXED_TEST_COUNT || contract.minimum_tests !== FIXED_TEST_COUNT) {
    throw new Error(`checkpoint defense contract must pin ${FIXED_TEST_COUNT} tests`);
  }
  if (Object.keys(contract.fingerprints).length < 6) throw new Error("checkpoint defense contract fingerprints fewer than 6 files");
  for (const pathName of REQUIRED_PATHS) {
    if (!/^[a-f0-9]{64}$/.test(contract.fingerprints[pathName] ?? "")) {
      throw new Error(`checkpoint defense contract fingerprint missing: ${pathName}`);
    }
  }
  return contract;
}

function candidateBlob(candidate, path) {
  return git(["show", `${candidate}:${path}`], { encoding: "buffer" });
}

function verifyFingerprints(candidate, contract) {
  const violations = [];
  let checked = 0;
  for (const [path, expected] of Object.entries(contract.fingerprints)) {
    checked += 1;
    try {
      const actual = sha256(candidateBlob(candidate, path));
      if (actual !== expected) {
        violations.push({ check: "fingerprint", file: path, detail: `${actual} != ${expected}` });
      }
    } catch (error) {
      violations.push({ check: "fingerprint", file: path, detail: error.message });
    }
  }
  return { violations, checked };
}

function archiveCandidate(candidate) {
  const directory = mkdtempSync(join(tmpdir(), "checkpoint-defense-tree-"));
  const archive = spawnSync("git", ["archive", "--format=tar", candidate], {
    encoding: "buffer",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (archive.status !== 0) throw new Error((archive.stderr || archive.stdout).toString().trim());
  const tar = spawnSync("tar", ["-xf", "-", "-C", directory], { input: archive.stdout, encoding: "utf8" });
  if (tar.status !== 0) throw new Error((tar.stderr || tar.stdout || "tar failed").trim());
  return directory;
}

function parseTap(output) {
  const summary = { tests: null, pass: null, fail: null, cancelled: null, skipped: null, todo: null };
  for (const line of output.split(/\r?\n/)) {
    const match = line.match(/^#\s+(tests|pass|fail|cancelled|skipped|todo)\s+(\d+)\s*$/);
    if (match) summary[match[1]] = Number.parseInt(match[2], 10);
  }
  return summary;
}

function runCheckpointTests(tree, contract) {
  const result = spawnSync(process.execPath, ["--test", "tests/checkpoint-gate.test.mjs"], {
    cwd: tree,
    encoding: "utf8",
    timeout: 120_000,
    maxBuffer: 32 * 1024 * 1024,
  });
  const tests = parseTap(`${result.stdout}\n${result.stderr}`);
  const expected = contract.expected_tests;
  const minimum = contract.minimum_tests;
  const violations = [];
  if (result.status !== 0) violations.push({ check: "checkpoint-tests", file: "tests/checkpoint-gate.test.mjs", detail: `exit ${result.status}` });
  if (tests.tests !== expected) violations.push({ check: "checkpoint-tests", file: "tests/checkpoint-gate.test.mjs", detail: `tests ${tests.tests} != ${expected}` });
  if ((tests.tests ?? 0) < minimum) violations.push({ check: "checkpoint-tests", file: "tests/checkpoint-gate.test.mjs", detail: `tests ${tests.tests ?? 0} < ${minimum}` });
  for (const key of ["fail", "cancelled", "skipped", "todo"]) {
    if (tests[key] !== 0) violations.push({ check: "checkpoint-tests", file: "tests/checkpoint-gate.test.mjs", detail: `${key} ${tests[key]} != 0` });
  }
  if (tests.pass !== expected) violations.push({ check: "checkpoint-tests", file: "tests/checkpoint-gate.test.mjs", detail: `pass ${tests.pass} != ${expected}` });
  return { tests, violations };
}

function fixtureRepo() {
  const cwd = mkdtempSync(join(tmpdir(), "checkpoint-defense-fixture-"));
  const run = (args) => git(args, { cwd }).trim();
  run(["init", "-q"]);
  mkdirSync(join(cwd, "docs/sot"), { recursive: true });
  mkdirSync(join(cwd, ".strict/run-ledger"), { recursive: true });
  writeFileSync(join(cwd, "docs/sot/coding-principles.md"), "| P11 | budget | hard 600 LOC, function hard 100 LOC |\n");
  writeFileSync(join(cwd, ".secret-patterns.default"), "CHECKPOINT_CANARY_[A-Z0-9]{12}\n");
  writeFileSync(join(cwd, "verify.sh"), "#!/usr/bin/env bash\nexit 0\n");
  mkdirSync(join(cwd, "tests"), { recursive: true });
  writeFileSync(join(cwd, "tests/value.test.mjs"), 'import assert from "node:assert/strict";\nassert.equal(status, 1);\n');
  writeFileSync(join(cwd, `.strict/run-ledger/${RUN_ID}.json`), `${JSON.stringify({
    run_id: RUN_ID,
    task: "checkpoint defense fixture",
    state: "BUILD",
    contract_sha256: "0".repeat(64),
    approvals: [],
    wus: [{ id: "WU-3c", status: "green", scope: ["tests/**"] }],
    findings_ref: null,
    next_action: "checkpoint",
    updated_at: "2026-08-27T00:00:00.000Z",
  })}\n`);
  run(["add", "-A"]);
  run(["commit", "-qm", "fixture baseline"]);
  return { cwd, base: run(["rev-parse", "HEAD"]) };
}

function runGate(tree, cwd, base) {
  return spawnSync(process.execPath, [join(tree, "tools/strict/checkpoint-gate.mjs"), "--base", base, "--run-id", RUN_ID, "--json"], {
    cwd,
    encoding: "utf8",
    timeout: 60_000,
  });
}

function runDirectFixtures(tree) {
  const normal = fixtureRepo();
  writeFileSync(join(normal.cwd, "tests/value.test.mjs"), 'import assert from "node:assert/strict";\nassert.equal(status, 1);\nassert.ok(true);\n');
  git(["add", "tests/value.test.mjs"], { cwd: normal.cwd });
  const normalResult = runGate(tree, normal.cwd, normal.base);
  const blocked = fixtureRepo();
  writeFileSync(join(blocked.cwd, "tests/value.test.mjs"), "");
  git(["add", "tests/value.test.mjs"], { cwd: blocked.cwd });
  const blockedResult = runGate(tree, blocked.cwd, blocked.base);
  rmSync(normal.cwd, { recursive: true, force: true });
  rmSync(blocked.cwd, { recursive: true, force: true });
  return { normal: normalResult.status === 0, blocked: blockedResult.status !== 0 };
}

async function main() {
  let tree = null;
  try {
    const args = parseArgs(process.argv.slice(2));
    const candidate = git(["rev-parse", "--verify", `${args.candidate}^{commit}`]).trim();
    const contract = await loadContract(args.contract);
    const fingerprint = verifyFingerprints(candidate, contract);
    tree = archiveCandidate(candidate);
    const checkpoint = runCheckpointTests(tree, contract);
    const direct = runDirectFixtures(tree);
    const violations = [...fingerprint.violations, ...checkpoint.violations];
    if (!direct.normal) violations.push({ check: "direct-fixture", file: "tools/strict/checkpoint-gate.mjs", detail: "normal fixture failed" });
    if (!direct.blocked) violations.push({ check: "direct-fixture", file: "tools/strict/checkpoint-gate.mjs", detail: "blocked fixture passed" });
    const checked = fingerprint.checked + (checkpoint.tests.tests ?? 0) + 2;
    const result = jsonResult(violations.length === 0, { candidate, checked, tests: checkpoint.tests, direct, violations });
    if (args.json) process.stdout.write(`${JSON.stringify(result)}\n`);
    else {
      for (const violation of violations) process.stdout.write(`FAIL: ${violation.check} ${violation.file} — ${violation.detail}\n`);
      if (result.pass) process.stdout.write(`PASS: checkpoint defense candidate=${candidate} tests=${checkpoint.tests.tests}\n`);
      process.stdout.write(`CHECKED: ${checked}\nVERDICT: ${result.pass ? "PASS" : "FAIL"}\n`);
    }
    process.exit(result.pass ? 0 : 1);
  } catch (error) {
    const result = jsonResult(false, { candidate: null, checked: 0, tests: null, direct: null, violations: [{ check: "input", file: "", detail: error.message }] });
    process.stdout.write(`${JSON.stringify(result)}\n`);
    process.exit(2);
  } finally {
    if (tree) rmSync(tree, { recursive: true, force: true });
  }
}

main();
