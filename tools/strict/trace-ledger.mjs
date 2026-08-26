#!/usr/bin/env node
import { createHash } from "node:crypto";
import { realpathSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { countJavaScriptWeakening } from "./checkpoint-js-scan.mjs";

const LEDGER_VERSION = "valuehire.strict-trace/v1";
const OID = /^(?:[0-9a-f]{40}|[0-9a-f]{64})$/;
const SHA256 = /^[0-9a-f]{64}$/;

function parseArgs(argv) {
  const args = { runId: null, ledgerCommit: null, ledgerBlob: null, candidate: null, json: false };
  const values = new Map([
    ["--run-id", "runId"],
    ["--ledger-commit", "ledgerCommit"],
    ["--ledger-blob", "ledgerBlob"],
    ["--candidate", "candidate"],
  ]);
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    if (flag === "--json") args.json = true;
    else if (values.has(flag)) {
      const value = argv[++index];
      if (!value || value.startsWith("--")) throw new Error(`${flag} requires a value`);
      args[values.get(flag)] = value;
    } else throw new Error(`unknown argument: ${flag}`);
  }
  for (const [flag, key] of values) if (!args[key]) throw new Error(`${flag} is required`);
  if (!/^[A-Za-z0-9._-]+$/.test(args.runId)) throw new Error("--run-id has invalid characters");
  for (const key of ["ledgerCommit", "ledgerBlob", "candidate"]) {
    if (!OID.test(args[key])) throw new Error(`--${key.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`)} requires a full Git object ID`);
  }
  return args;
}

function git(args, { buffer = false, allowFailure = false } = {}) {
  const result = spawnSync("git", args, {
    encoding: buffer ? null : "utf8",
    maxBuffer: 32 * 1024 * 1024,
    env: process.env,
  });
  if (!allowFailure && result.status !== 0) {
    const output = buffer ? result.stderr.toString("utf8") : result.stderr;
    throw new Error((output || `git ${args.join(" ")} failed`).trim());
  }
  return result;
}

function gitText(args) {
  return git(args).stdout.trim();
}

function gitBuffer(args) {
  return git(args, { buffer: true }).stdout;
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    const body = Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`);
    return `{${body.join(",")}}`;
  }
  return JSON.stringify(value);
}

function safePath(path) {
  return typeof path === "string" && path.length > 0 && !path.startsWith("/") && !path.split("/").includes("..");
}

function time(value) {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}T/.test(value)) return null;
  const epoch = Date.parse(value);
  return Number.isFinite(epoch) ? epoch : null;
}

function lines(buffer) {
  if (buffer.length === 0) return 0;
  const text = buffer.toString("utf8");
  return text.endsWith("\n") ? text.split("\n").length - 1 : text.split("\n").length;
}

function isAncestor(older, newer) {
  return git(["merge-base", "--is-ancestor", older, newer], { allowFailure: true }).status === 0;
}

function commitTrailers(commit) {
  return gitText(["show", "-s", "--format=%B", commit]);
}

function commitTime(commit) {
  return time(gitText(["show", "-s", "--format=%cI", commit]));
}

function changedPaths(commit) {
  const output = gitText(["diff-tree", "--no-commit-id", "--name-only", "-r", commit]);
  return output ? output.split("\n") : [];
}

function commitFile(commit, path) {
  const result = git(["show", `${commit}:${path}`], { allowFailure: true });
  return result.status === 0 ? result.stdout : "";
}

function recordedRedWeakens(commit, path) {
  const before = commitFile(`${commit}^`, path);
  const after = commitFile(commit, path);
  if (/\.(?:[cm]?[jt]sx?)$/i.test(path)) {
    const oldCounts = countJavaScriptWeakening(before);
    const newCounts = countJavaScriptWeakening(after);
    return newCounts.assertions < oldCounts.assertions ||
      newCounts.skip > oldCounts.skip || newCounts.only > oldCounts.only || newCounts.todo > oldCounts.todo;
  }
  const summary = gitText(["diff", "--numstat", `${commit}^`, commit, "--", path]).split("\t");
  const additions = Number(summary[0]);
  const deletions = Number(summary[1]);
  return !Number.isFinite(additions) || !Number.isFinite(deletions) || additions <= deletions;
}

function isTestPath(path) {
  return /(^|\/)(?:tests?|__tests__)(\/|$)/.test(path) || /\.(?:test|spec)\.[^/]+$/.test(path);
}

function validateRedTestImmutability(violations, record, field, candidate, recordedRedCommits, invalidatedCommits) {
  if (!OID.test(record.red_commit ?? "") || !OID.test(record.implementation_commit ?? "")) return;
  const redTests = new Set(changedPaths(record.red_commit).filter(isTestPath));
  if (redTests.size === 0) return;
  const range = gitText(["rev-list", "--reverse", `${record.red_commit}..${record.implementation_commit}`]);
  for (const commit of range ? range.split("\n") : []) {
    for (const path of changedPaths(commit)) {
      if (redTests.has(path)) add(violations, field, `GREEN commit modifies RED test: ${path}`);
    }
  }
  const later = gitText(["rev-list", "--reverse", `${record.implementation_commit}..${candidate}`]);
  for (const commit of later ? later.split("\n") : []) {
    for (const path of changedPaths(commit)) {
      if (!redTests.has(path)) continue;
      if (recordedRedCommits.has(commit)) {
        if (recordedRedWeakens(commit, path)) add(violations, field, `later recorded RED weakens protected RED test: ${path}`);
      } else if (invalidatedCommits.has(commit)) {
        if (recordedRedWeakens(commit, path)) add(violations, field, `later invalidated commit weakens protected RED test: ${path}`);
      } else add(violations, field, `later non-RED commit modifies protected RED test: ${path}`);
    }
  }
}

function add(violations, field, detail) {
  violations.push({ field, detail });
}

function outputCompletionError(command, output) {
  const text = output.toString("utf8");
  const nonempty = text.split(/\r?\n/).filter((line) => line.trim().length > 0);
  if (command.startsWith("node --test ")) {
    const tests = Number(text.match(/^# tests (\d+)$/m)?.[1]);
    const passed = Number(text.match(/^# pass (\d+)$/m)?.[1]);
    const failed = Number(text.match(/^# fail (\d+)$/m)?.[1]);
    if (!Number.isInteger(tests) || tests < 1 || passed !== tests || failed !== 0 ||
        !/^# duration_ms /.test(nonempty.at(-1) ?? "")) return "node test completion summary is missing or partial";
    return null;
  }
  if (command.startsWith("bash scripts/acceptance-")) {
    const checked = Number((nonempty.at(-1) ?? "").match(/^CHECKED: (\d+)$/)?.[1]);
    if (!/^PASS:/m.test(text) || !Number.isInteger(checked) || checked < 1) {
      return "acceptance completion summary is missing or partial";
    }
    return null;
  }
  return "command has no supported completion contract";
}

function validateCommit(violations, commit, field, wuId, phase, candidate) {
  if (!OID.test(commit ?? "")) {
    add(violations, field, `${field} must be a full Git object ID`);
    return;
  }
  if (git(["cat-file", "-e", `${commit}^{commit}`], { allowFailure: true }).status !== 0) {
    add(violations, field, `${field} commit does not exist`);
    return;
  }
  if (!isAncestor(commit, candidate)) add(violations, field, `${field} is not an ancestor of candidate`);
  const message = commitTrailers(commit);
  if (!new RegExp(`^WU: ${wuId.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`, "m").test(message)) {
    add(violations, field, `${field} WU trailer does not match ${wuId}`);
  }
  if (!new RegExp(`^Phase: ${phase}$`, "m").test(message)) {
    add(violations, field, `${field} Phase trailer is not ${phase}`);
  }
}

function validateEvidence(violations, ledger, ledgerCommit, ledgerCommitTime, record, issueTime, clock, usedPaths) {
  const expected = Array.isArray(record.expected_commands) ? record.expected_commands : [];
  if (expected.length === 0 || expected.some((command) => typeof command !== "string" || command.trim() === "")) {
    add(violations, `records[${record.sequence}].expected_commands`, "expected_commands must contain at least one non-empty command");
  }
  if (new Set(expected).size !== expected.length) {
    add(violations, `records[${record.sequence}].expected_commands`, "expected_commands must be unique");
  }
  const seenCommands = new Set();
  const implementationTime = OID.test(record.implementation_commit ?? "") &&
    git(["cat-file", "-e", `${record.implementation_commit}^{commit}`], { allowFailure: true }).status === 0
    ? commitTime(record.implementation_commit)
    : null;
  if (!Array.isArray(record.evidence) || record.evidence.length === 0) {
    add(violations, `records[${record.sequence}].evidence`, "evidence must contain at least one result");
    return clock;
  }
  for (const [index, evidence] of record.evidence.entries()) {
    const field = `records[${record.sequence}].evidence[${index}]`;
    if (!evidence || typeof evidence !== "object") {
      add(violations, field, "evidence entry must be an object");
      continue;
    }
    if (typeof evidence.command !== "string" || evidence.command.trim() === "") add(violations, field, "command is empty");
    else {
      seenCommands.add(evidence.command);
      if (!expected.includes(evidence.command)) add(violations, field, "command is not approved for WU");
    }
    if (evidence.cwd !== ledger.worktree && evidence.cwd !== "${WORKTREE}") add(violations, field, "evidence cwd does not match worktree");
    if (!evidence.environment || typeof evidence.environment !== "object" || Array.isArray(evidence.environment)) {
      add(violations, field, "environment must be recorded");
    }
    const started = time(evidence.started_at);
    const finished = time(evidence.finished_at);
    if (started === null || finished === null || started < issueTime || finished < started || started < clock) {
      add(violations, field, "timestamp order is invalid or predates the issue contract");
    }
    if (started !== null && implementationTime !== null && started < implementationTime) {
      add(violations, field, "timestamp predates implementation commit");
    }
    if (finished !== null && ledgerCommitTime !== null && finished > ledgerCommitTime) {
      add(violations, field, "timestamp is after ledger commit");
    }
    if (finished !== null) clock = Math.max(clock, finished);
    if (!Number.isInteger(evidence.exit) || !Number.isInteger(evidence.expected_exit)) add(violations, field, "exit values must be integers");
    if (evidence.exit !== 0 || evidence.expected_exit !== 0) add(violations, field, "GREEN evidence exit must be zero");
    if (evidence.output_complete !== true) add(violations, field, "output_complete must be true");
    if (!safePath(evidence.output_path)) {
      add(violations, field, "output_path is unsafe or empty");
      continue;
    }
    if (usedPaths.has(evidence.output_path)) add(violations, field, "output_path is duplicated");
    usedPaths.add(evidence.output_path);
    let output;
    try { output = gitBuffer(["show", `${ledgerCommit}:${evidence.output_path}`]); }
    catch (error) {
      add(violations, field, `output blob is missing: ${error.message}`);
      continue;
    }
    if (output.length === 0) add(violations, field, "output blob is empty");
    if (!SHA256.test(evidence.output_sha256 ?? "") || sha256(output) !== evidence.output_sha256) {
      add(violations, field, "output SHA-256 mismatch");
    }
    if (output.length !== evidence.output_bytes) add(violations, field, "output byte count mismatch");
    if (lines(output) !== evidence.output_lines || evidence.output_lines < 1) add(violations, field, "output line count mismatch");
    const completionError = typeof evidence.command === "string" ? outputCompletionError(evidence.command, output) : null;
    if (completionError) add(violations, field, completionError);
  }
  for (const command of expected) {
    if (!seenCommands.has(command)) add(violations, `records[${record.sequence}].expected_commands`, `approved command has no evidence: ${command}`);
  }
  return clock;
}

function validateLedger(args, ledger, ledgerCommit) {
  const violations = [];
  if (!ledger || typeof ledger !== "object" || Array.isArray(ledger)) {
    add(violations, "ledger", "ledger must be a JSON object");
    return violations;
  }
  if (ledger.schema_version !== LEDGER_VERSION) add(violations, "schema_version", "unsupported schema version");
  if (ledger.run_id !== args.runId) add(violations, "run_id", "run_id does not match CLI authority");
  if (!ledger.issue || typeof ledger.issue !== "object") add(violations, "issue", "issue contract is missing");
  if (!OID.test(ledger.base_commit ?? "")) add(violations, "base_commit", "base_commit must be a full Git object ID");
  if (ledger.candidate_commit !== args.candidate) add(violations, "candidate_commit", "candidate does not match CLI authority");
  if (!isAncestor(args.candidate, ledgerCommit)) add(violations, "ledger_commit", "ledger commit is not descended from candidate");
  if (OID.test(ledger.base_commit ?? "") && !isAncestor(ledger.base_commit, args.candidate)) {
    add(violations, "base_commit", "base commit is not an ancestor of candidate");
  }
  const currentBranch = gitText(["symbolic-ref", "--short", "HEAD"]);
  if (ledger.branch !== currentBranch) add(violations, "branch", `branch is stale; current branch is ${currentBranch}`);
  const currentWorktree = realpathSync(gitText(["rev-parse", "--show-toplevel"]));
  if (ledger.worktree !== "${WORKTREE}") {
    let ledgerWorktree = null;
    try { ledgerWorktree = realpathSync(ledger.worktree); } catch {}
    if (ledgerWorktree !== currentWorktree) add(violations, "worktree", "worktree is stale or does not resolve to the current root");
  }

  let issueTime = null;
  if (ledger.issue && typeof ledger.issue === "object") {
    issueTime = time(ledger.issue.opened_at);
    if (issueTime === null) add(violations, "issue.opened_at", "issue timestamp is invalid");
    if (!safePath(ledger.issue.contract_path)) add(violations, "issue.contract_path", "issue contract path is unsafe");
    else {
      try {
        const contract = gitBuffer(["show", `${ledgerCommit}:${ledger.issue.contract_path}`]);
        if (!SHA256.test(ledger.issue.contract_sha256 ?? "") || sha256(contract) !== ledger.issue.contract_sha256) {
          add(violations, "issue.contract_sha256", "issue contract SHA-256 mismatch");
        }
      } catch (error) { add(violations, "issue.contract_path", `issue contract is missing: ${error.message}`); }
    }
  }

  if (!Array.isArray(ledger.records) || ledger.records.length === 0) {
    add(violations, "records", "records must contain at least one WU sequence");
    return violations;
  }
  const usedWus = new Set();
  const usedPaths = new Set();
  const recordedRedCommits = new Set(ledger.records.map((record) => record?.red_commit).filter((commit) => OID.test(commit ?? "")));
  const invalidatedCommits = new Set(
    (Array.isArray(ledger.excluded_commits) ? ledger.excluded_commits : [])
      .filter((excluded) => excluded?.status === "invalidated" && OID.test(excluded?.commit ?? ""))
      .map((excluded) => excluded.commit),
  );
  const ledgerCommitTime = commitTime(ledgerCommit);
  let previous = null;
  let clock = issueTime ?? Number.NEGATIVE_INFINITY;
  for (const [index, record] of ledger.records.entries()) {
    const field = `records[${index}]`;
    if (!record || typeof record !== "object") {
      add(violations, field, "record must be an object");
      continue;
    }
    if (record.sequence !== index + 1) add(violations, field, `sequence must be ${index + 1}`);
    if (typeof record.wu_id !== "string" || record.wu_id.length === 0) add(violations, field, "WU ID is empty");
    if (usedWus.has(record.wu_id)) add(violations, field, "WU ID is duplicated");
    usedWus.add(record.wu_id);
    if (record.previous_record_sha256 !== previous) add(violations, field, "previous record hash does not match");
    const unsigned = { ...record };
    delete unsigned.record_sha256;
    const expectedHash = sha256(canonical(unsigned));
    if (!SHA256.test(record.record_sha256 ?? "") || record.record_sha256 !== expectedHash) {
      add(violations, field, "record SHA-256 mismatch");
    }
    validateCommit(violations, record.red_commit, `${field}.red_commit`, record.wu_id, "RED", args.candidate);
    validateCommit(violations, record.implementation_commit, `${field}.implementation_commit`, record.wu_id, "GREEN", args.candidate);
    if (OID.test(record.red_commit ?? "") && OID.test(record.implementation_commit ?? "") &&
        !isAncestor(record.red_commit, record.implementation_commit)) {
      add(violations, field, "RED commit is not an ancestor of GREEN commit");
    }
    validateRedTestImmutability(violations, record, field, args.candidate, recordedRedCommits, invalidatedCommits);
    clock = validateEvidence(
      violations,
      ledger,
      ledgerCommit,
      ledgerCommitTime,
      record,
      issueTime ?? Number.NEGATIVE_INFINITY,
      clock,
      usedPaths,
    );
    previous = record.record_sha256;
  }
  if (ledger.records.at(-1)?.implementation_commit !== args.candidate) {
    add(violations, "candidate_commit", "last WU implementation commit does not equal candidate");
  }
  const classified = new Set();
  for (const record of ledger.records) {
    if (OID.test(record?.red_commit ?? "")) classified.add(record.red_commit);
    if (OID.test(record?.implementation_commit ?? "")) classified.add(record.implementation_commit);
  }
  const excludedCommits = ledger.excluded_commits === undefined ? [] : ledger.excluded_commits;
  if (!Array.isArray(excludedCommits)) add(violations, "excluded_commits", "excluded_commits must be an array");
  else for (const [index, excluded] of excludedCommits.entries()) {
    const field = `excluded_commits[${index}]`;
    if (!excluded || typeof excluded !== "object" || !OID.test(excluded.commit ?? "")) {
      add(violations, field, "excluded commit must use a full Git object ID");
      continue;
    }
    if (classified.has(excluded.commit)) add(violations, field, "commit is classified more than once");
    classified.add(excluded.commit);
    if (!["administrative", "invalidated"].includes(excluded.status)) add(violations, field, "excluded status is invalid");
    if (typeof excluded.reason !== "string" || excluded.reason.trim() === "") add(violations, field, "excluded reason is missing");
    const actualPaths = changedPaths(excluded.commit).sort();
    const declaredPaths = Array.isArray(excluded.paths) ? [...excluded.paths].sort() : [];
    if (JSON.stringify(actualPaths) !== JSON.stringify(declaredPaths)) add(violations, field, "excluded changed paths do not match Git");
  }
  const historyText = gitText(["rev-list", "--reverse", `${ledger.base_commit}..${args.candidate}`]);
  const history = historyText ? historyText.split("\n") : [];
  for (const commit of history) if (!classified.has(commit)) add(violations, "history", `unclassified commit: ${commit}`);
  for (const commit of classified) if (!history.includes(commit)) add(violations, "history", `classified commit is outside base..candidate: ${commit}`);
  return violations;
}

function emit(result, json) {
  if (json) process.stdout.write(`${JSON.stringify(result)}\n`);
  else if (result.pass) process.stdout.write("PASS strict trace ledger\n");
  else for (const violation of result.violations) process.stdout.write(`${violation.field}: ${violation.detail}\n`);
}

function main() {
  let args;
  const violations = [];
  try {
    args = parseArgs(process.argv.slice(2));
    process.chdir(gitText(["rev-parse", "--show-toplevel"]));
    gitText(["rev-parse", "--verify", `${args.ledgerCommit}^{commit}`]);
    gitText(["rev-parse", "--verify", `${args.candidate}^{commit}`]);
    const path = `.strict/trace-ledger/${args.runId}.json`;
    const actualBlob = gitText(["rev-parse", `${args.ledgerCommit}:${path}`]);
    if (actualBlob !== args.ledgerBlob) add(violations, "ledger_blob", "ledger blob does not match the approved blob pin");
    const ledger = JSON.parse(gitBuffer(["show", `${args.ledgerCommit}:${path}`]).toString("utf8"));
    violations.push(...validateLedger(args, ledger, args.ledgerCommit));
  } catch (error) {
    add(violations, "input", error.message);
  }
  const result = { pass: violations.length === 0, violations };
  emit(result, args?.json ?? process.argv.includes("--json"));
  process.exit(result.pass ? 0 : 1);
}

main();
