import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const VALIDATOR = join(ROOT, "tools/strict/delivery-state.mjs");
const RUN_ID = "delivery-wiring-fixture";
const STATE_PATH = `.strict/delivery-state/${RUN_ID}.json`;
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
      GIT_AUTHOR_NAME: "delivery wiring test",
      GIT_AUTHOR_EMAIL: "delivery-wiring@example.invalid",
      GIT_COMMITTER_NAME: "delivery wiring test",
      GIT_COMMITTER_EMAIL: "delivery-wiring@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function makeRepo(field, invalidState) {
  const cwd = mkdtempSync(join(tmpdir(), "delivery-wiring-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q", "-b", "task/delivery-wiring");
  write(cwd, "src/value.mjs", "export const value = 1;\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "candidate");
  const candidate = git(cwd, "rev-parse", "HEAD");
  const state = {
    schema_version: "valuehire.delivery-state/v1",
    run_id: RUN_ID,
    candidate_sha: candidate,
    local: { full_strict: "PASS", codeaudit: "PASS", adversarial: "PASS" },
    pr: { state: "NOT_RUN" },
    ci: { state: "NOT_RUN" },
    merge: { state: "NOT_RUN" },
    checkpoint_readiness: "NOT_RUN",
    overall_t: "NOT_RUN",
    deploy: { state: "NOT_RUN" },
    live_verify: { state: "NOT_RUN" },
  };
  state[field].state = invalidState;
  write(cwd, STATE_PATH, `${JSON.stringify(state)}\n`);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "pin invalid delivery state");
  const stateCommit = git(cwd, "rev-parse", "HEAD");
  const stateBlob = git(cwd, "rev-parse", `${stateCommit}:${STATE_PATH}`);
  return { cwd, candidate, stateCommit, stateBlob };
}

function runValidator(fixture) {
  const result = spawnSync(process.execPath, [
    VALIDATOR,
    "--run-id", RUN_ID,
    "--state-commit", fixture.stateCommit,
    "--state-blob", fixture.stateBlob,
    "--candidate", fixture.candidate,
    "--json",
  ], { cwd: fixture.cwd, encoding: "utf8" });
  return { ...result, body: JSON.parse(result.stdout) };
}

for (const [field, invalidState] of [
  ["pr", "GREEN"],
  ["ci", "OPEN"],
  ["merge", "GREEN"],
  ["deploy", "FAIL"],
  ["live_verify", "FAIL"],
]) {
  test(`${field} rejects the cross-stage state ${invalidState}`, () => {
    const result = runValidator(makeRepo(field, invalidState));
    assert.equal(result.status, 1, JSON.stringify(result.body));
    assert.ok(result.body.violations.some((item) => item.detail.includes("state")), JSON.stringify(result.body));
  });
}

test("verification command SOT lists every named CI step", () => {
  const workflow = readFileSync(join(ROOT, ".github/workflows/verify.yml"), "utf8");
  const sot = readFileSync(join(ROOT, "docs/sot/verification-commands.md"), "utf8");
  const names = [...workflow.matchAll(/^\s+- name:\s+(.+)$/gm)].map((match) => match[1].trim());
  assert.equal(names.length, 24);
  assert.match(sot, /\*\*워크플로 스텝 24개 전부\*\*/);
  for (const name of names) assert.ok(sot.includes(name), `missing CI step in SOT: ${name}`);
});
