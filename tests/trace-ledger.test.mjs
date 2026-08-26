import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const VALIDATOR = join(ROOT, "tools/strict/trace-ledger.mjs");
const RUN_ID = "trace-fixture";
const LEDGER_PATH = `.strict/trace-ledger/${RUN_ID}.json`;
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
      GIT_AUTHOR_NAME: "trace ledger test",
      GIT_AUTHOR_EMAIL: "trace-ledger@example.invalid",
      GIT_COMMITTER_NAME: "trace ledger test",
      GIT_COMMITTER_EMAIL: "trace-ledger@example.invalid",
    },
  }).trim();
}

function write(cwd, path, content) {
  const target = join(cwd, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, content);
}

function sha256(content) {
  return createHash("sha256").update(content).digest("hex");
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sealRecord(record) {
  const unsigned = { ...record };
  delete unsigned.record_sha256;
  return { ...unsigned, record_sha256: sha256(canonical(unsigned)) };
}

function commit(cwd, subject, wu, phase) {
  write(cwd, "src/value.mjs", `export const value = ${JSON.stringify(subject)};\n`);
  git(cwd, "add", "src/value.mjs");
  git(cwd, "commit", "-qm", subject, "-m", `WU: ${wu}\nPhase: ${phase}`);
  return git(cwd, "rev-parse", "HEAD");
}

function evidence(path, output, startedAt, finishedAt) {
  return {
    command: `node --test ${path}.test.mjs`,
    cwd: "${WORKTREE}",
    environment: { CI: "false", NODE_ENV: "test" },
    started_at: startedAt,
    finished_at: finishedAt,
    exit: 0,
    expected_exit: 0,
    output_path: path,
    output_sha256: sha256(output),
    output_bytes: Buffer.byteLength(output),
    output_lines: output.split("\n").length - 1,
    output_complete: true,
  };
}

function makeRepo(mutate = () => {}) {
  const cwd = mkdtempSync(join(tmpdir(), "trace-ledger-"));
  cleanups.push(cwd);
  git(cwd, "init", "-q", "-b", "task/trace-fixture");
  write(cwd, "docs/engineering/issue.md", "# LOCAL-TRACE-1\n");
  write(cwd, "src/value.mjs", "export const value = 0;\n");
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "baseline");
  const base = git(cwd, "rev-parse", "HEAD");
  const red1 = commit(cwd, "red one", "WU-1", "RED");
  const green1 = commit(cwd, "green one", "WU-1", "GREEN");
  const red2 = commit(cwd, "red two", "WU-2", "RED");
  const green2 = commit(cwd, "green two", "WU-2", "GREEN");
  const output1 = "PASS WU-1 complete\n";
  const output2 = "PASS WU-2 complete\n";
  const issue = readFileSync(join(cwd, "docs/engineering/issue.md"));
  const first = sealRecord({
    sequence: 1,
    wu_id: "WU-1",
    red_commit: red1,
    implementation_commit: green1,
    previous_record_sha256: null,
    evidence: [evidence("evidence/wu-1.tap", output1, "2026-08-27T01:00:00Z", "2026-08-27T01:01:00Z")],
  });
  const second = sealRecord({
    sequence: 2,
    wu_id: "WU-2",
    red_commit: red2,
    implementation_commit: green2,
    previous_record_sha256: first.record_sha256,
    evidence: [evidence("evidence/wu-2.tap", output2, "2026-08-27T01:02:00Z", "2026-08-27T01:03:00Z")],
  });
  const ledger = {
    schema_version: "valuehire.strict-trace/v1",
    run_id: RUN_ID,
    issue: {
      id: "LOCAL-TRACE-1",
      contract_path: "docs/engineering/issue.md",
      contract_sha256: sha256(issue),
      opened_at: "2026-08-27T00:00:00Z",
    },
    base_commit: base,
    candidate_commit: green2,
    branch: "task/trace-fixture",
    worktree: cwd,
    records: [first, second],
  };
  mutate({ cwd, ledger, output1, output2, commits: { red1, green1, red2, green2 } });
  write(cwd, "evidence/wu-1.tap", output1);
  write(cwd, "evidence/wu-2.tap", output2);
  write(cwd, LEDGER_PATH, `${JSON.stringify(ledger, null, 2)}\n`);
  git(cwd, "add", "-A");
  git(cwd, "commit", "-qm", "seal trace ledger");
  const ledgerCommit = git(cwd, "rev-parse", "HEAD");
  const ledgerBlob = git(cwd, "rev-parse", `${ledgerCommit}:${LEDGER_PATH}`);
  return { cwd, ledger, ledgerCommit, ledgerBlob, candidate: green2 };
}

function runValidator(fixture, ...extra) {
  const result = spawnSync(process.execPath, [
    VALIDATOR,
    "--run-id", RUN_ID,
    "--ledger-commit", fixture.ledgerCommit,
    "--ledger-blob", fixture.ledgerBlob,
    "--candidate", fixture.candidate,
    "--json",
    ...extra,
  ], { cwd: fixture.cwd, encoding: "utf8" });
  let body = null;
  try { body = JSON.parse(result.stdout); } catch {}
  return { ...result, body };
}

function expectFailure(fixture, detail) {
  const result = runValidator(fixture);
  assert.equal(result.status, 1, result.stderr);
  assert.equal(result.body?.pass, false, result.stdout);
  assert.ok(result.body.violations.some((item) => item.detail.includes(detail)), JSON.stringify(result.body));
}

test("a pinned trace ledger connects issue, branch, worktree, WU commits, and full evidence", () => {
  const result = runValidator(makeRepo());
  assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  assert.deepEqual(result.body, { pass: true, violations: [] });
});

for (const [name, tamper] of [
  ["deletion", ({ cwd }) => unlinkSync(join(cwd, LEDGER_PATH))],
  ["copy decoy", ({ cwd, ledger }) => write(cwd, ".strict/trace-ledger/newer.json", `${JSON.stringify({ ...ledger, run_id: "decoy" })}\n`)],
  ["reorder", ({ cwd, ledger }) => write(cwd, LEDGER_PATH, `${JSON.stringify({ ...ledger, records: [...ledger.records].reverse() })}\n`)],
  ["past timestamp", ({ cwd, ledger }) => {
    ledger.records[1].evidence[0].started_at = "2020-01-01T00:00:00Z";
    write(cwd, LEDGER_PATH, `${JSON.stringify(ledger)}\n`);
  }],
]) {
  test(`worktree ledger ${name} cannot forge the pinned result`, () => {
    const fixture = makeRepo();
    tamper({ cwd: fixture.cwd, ledger: fixture.ledger });
    assert.equal(runValidator(fixture).status, 0);
  });
}

test("a substituted ledger blob is rejected", () => {
  const fixture = makeRepo();
  fixture.ledgerBlob = "0".repeat(40);
  expectFailure(fixture, "blob");
});

test("record deletion is rejected", () => expectFailure(makeRepo(({ ledger }) => ledger.records.shift()), "sequence"));
test("record duplication is rejected", () => expectFailure(makeRepo(({ ledger }) => ledger.records.push(ledger.records[0])), "sequence"));
test("record reordering is rejected", () => expectFailure(makeRepo(({ ledger }) => ledger.records.reverse()), "sequence"));
test("a timestamp before the issue contract is rejected", () => expectFailure(makeRepo(({ ledger }) => {
  ledger.records[0].evidence[0].started_at = "2020-01-01T00:00:00Z";
  ledger.records[0] = sealRecord(ledger.records[0]);
}), "timestamp"));
test("a WU ID that disagrees with commit trailers is rejected", () => expectFailure(makeRepo(({ ledger }) => {
  ledger.records[0].wu_id = "WU-X";
  ledger.records[0] = sealRecord(ledger.records[0]);
}), "trailer"));
test("a WU implementation commit mismatch is rejected", () => expectFailure(makeRepo(({ ledger, commits }) => {
  ledger.records[0].implementation_commit = commits.green2;
  ledger.records[0] = sealRecord(ledger.records[0]);
}), "trailer"));
test("a stale branch is rejected", () => expectFailure(makeRepo(({ ledger }) => { ledger.branch = "task/stale"; }), "branch"));
test("a stale worktree is rejected", () => expectFailure(makeRepo(({ ledger }) => { ledger.worktree = "/tmp/stale"; }), "worktree"));
test("zero evidence is rejected", () => expectFailure(makeRepo(({ ledger }) => {
  ledger.records[0].evidence = [];
  ledger.records[0] = sealRecord(ledger.records[0]);
}), "evidence"));
test("partial output is rejected", () => expectFailure(makeRepo(({ ledger }) => {
  ledger.records[0].evidence[0].output_complete = false;
  ledger.records[0] = sealRecord(ledger.records[0]);
}), "complete"));
