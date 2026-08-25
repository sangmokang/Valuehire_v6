#!/usr/bin/env node

import { spawn } from "node:child_process";
import { lstat, readFile, rename, unlink, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const RUNNER_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(RUNNER_DIR, "..", "..");
const SOURCES = new Set(["contract", "adversarial", "runtime"]);
const SEVERITIES = new Set(["high", "medium", "low"]);
const STATUSES = new Set([
  "REPRODUCED",
  "BLOCKED",
  "NOT_REPRODUCIBLE",
  "NOT_TESTED",
  "UNRESOLVED",
]);

function fail(message) {
  throw new Error(message);
}

function parseArgs(args) {
  if (args[0] !== "run" || !args[1]) {
    fail("usage: finding-runner.mjs run <file> [--only F-1]");
  }
  if (args.length === 2) {
    return { file: path.resolve(args[1]), only: undefined };
  }
  if (args.length !== 4 || args[2] !== "--only" || !args[3]) {
    fail("usage: finding-runner.mjs run <file> [--only F-1]");
  }
  return { file: path.resolve(args[1]), only: args[3] };
}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function requireExactKeys(value, expected, label) {
  if (!isRecord(value)) {
    fail(`${label} must be an object`);
  }
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    fail(`${label} keys must be exactly: ${wanted.join(", ")}`);
  }
}

function requireOneLine(value, label) {
  if (typeof value !== "string" || value.trim() === "" || /[\r\n]/u.test(value)) {
    fail(`${label} must be a non-empty single-line string`);
  }
}

function resolveWorkingDirectory(value, label) {
  requireOneLine(value, label);
  if (path.isAbsolute(value)) {
    fail(`${label} must be relative to the repository root`);
  }
  const resolved = path.resolve(REPO_ROOT, value);
  const relative = path.relative(REPO_ROOT, resolved);
  if (relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    fail(`${label} escapes the repository root`);
  }
  return resolved;
}

function validateExpect(expect, label) {
  if (!isRecord(expect) || Object.keys(expect).length !== 1) {
    fail(`${label} must contain exactly one expectation`);
  }
  if (Object.hasOwn(expect, "exit_not")) {
    if (!Number.isInteger(expect.exit_not) || expect.exit_not < 0 || expect.exit_not > 255) {
      fail(`${label}.exit_not must be an integer from 0 through 255`);
    }
    return;
  }
  if (Object.hasOwn(expect, "stdout_contains")) {
    requireOneLine(expect.stdout_contains, `${label}.stdout_contains`);
    return;
  }
  fail(`${label} must contain exit_not or stdout_contains`);
}

function validateFinding(finding, index, ids) {
  const label = `findings[${index}]`;
  requireExactKeys(finding, ["id", "source", "claim", "severity", "repro", "status"], label);
  requireOneLine(finding.id, `${label}.id`);
  if (ids.has(finding.id)) fail(`duplicate finding id: ${finding.id}`);
  ids.add(finding.id);
  if (!SOURCES.has(finding.source)) fail(`${label}.source is invalid`);
  requireOneLine(finding.claim, `${label}.claim`);
  if (!SEVERITIES.has(finding.severity)) fail(`${label}.severity is invalid`);
  if (!STATUSES.has(finding.status)) fail(`${label}.status is invalid`);
  requireExactKeys(finding.repro, ["cmd", "cwd", "expect"], `${label}.repro`);
  requireOneLine(finding.repro.cmd, `${label}.repro.cmd`);
  resolveWorkingDirectory(finding.repro.cwd, `${label}.repro.cwd`);
  validateExpect(finding.repro.expect, `${label}.repro.expect`);
}

function validateDocument(data) {
  requireExactKeys(data, ["findings"], "root");
  if (!Array.isArray(data.findings) || data.findings.length === 0) {
    fail("root.findings must be a non-empty array");
  }
  const ids = new Set();
  data.findings.forEach((finding, index) => validateFinding(finding, index, ids));
}

async function loadDocument(file) {
  const metadata = await lstat(file);
  if (!metadata.isFile() || metadata.isSymbolicLink()) {
    fail(`input must be a regular non-symlink file: ${file}`);
  }
  let data;
  try {
    data = JSON.parse(await readFile(file, "utf8"));
  } catch (error) {
    fail(`cannot parse JSON: ${error.message}`);
  }
  validateDocument(data);
  return { data, mode: metadata.mode };
}

function collectProcess(child) {
  return new Promise((resolve) => {
    const stdout = [];
    const stderr = [];
    let spawnError;
    child.stdout.on("data", (chunk) => stdout.push(chunk));
    child.stderr.on("data", (chunk) => stderr.push(chunk));
    child.on("error", (error) => {
      spawnError = error;
    });
    child.on("close", (code, signal) => {
      resolve({
        code,
        signal,
        error: spawnError,
        stdout: Buffer.concat(stdout).toString("utf8"),
        stderr: Buffer.concat(stderr).toString("utf8"),
      });
    });
  });
}

async function executeRepro(finding) {
  const cwd = resolveWorkingDirectory(finding.repro.cwd, `${finding.id}.repro.cwd`);
  process.stdout.write(`[${finding.id}] cwd=${finding.repro.cwd} cmd=${finding.repro.cmd}\n`);
  let child;
  try {
    child = spawn("/bin/sh", ["-c", finding.repro.cmd], {
      cwd,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });
  } catch (error) {
    return { code: null, signal: null, error, stdout: "", stderr: "" };
  }
  return collectProcess(child);
}

function statusFromExecution(finding, execution) {
  if (execution.error || execution.signal || execution.code === 126 || execution.code === 127) {
    return "BLOCKED";
  }
  const { expect } = finding.repro;
  const reproduced = Object.hasOwn(expect, "exit_not")
    ? execution.code !== expect.exit_not
    : execution.stdout.includes(expect.stdout_contains);
  return reproduced ? "REPRODUCED" : "NOT_REPRODUCIBLE";
}

function printExecution(finding, execution, status) {
  if (execution.stdout) process.stdout.write(execution.stdout);
  if (execution.stderr) process.stderr.write(execution.stderr);
  const exit = execution.code === null ? "none" : execution.code;
  const signal = execution.signal ? ` signal=${execution.signal}` : "";
  const error = execution.error ? ` error=${execution.error.code ?? execution.error.message}` : "";
  process.stdout.write(`[${finding.id}] exit=${exit}${signal}${error} status=${status}\n`);
}

async function runSelected(findings, only) {
  const selected = only ? findings.filter(({ id }) => id === only) : findings;
  if (selected.length === 0) fail(`finding id not found: ${only}`);
  for (const finding of selected) {
    const execution = await executeRepro(finding);
    const status = statusFromExecution(finding, execution);
    printExecution(finding, execution, status);
    finding.status = status;
  }
}

async function writeAtomically(file, data, mode) {
  const temp = path.join(path.dirname(file), `.${path.basename(file)}.${process.pid}.${Date.now()}.tmp`);
  try {
    await writeFile(temp, `${JSON.stringify(data, null, 2)}\n`, { flag: "wx", mode });
    await rename(temp, file);
  } catch (error) {
    await unlink(temp).catch(() => {});
    throw error;
  }
}

function summarize(findings) {
  const count = (status) => findings.filter((finding) => finding.status === status).length;
  const mergeBlocked = findings.some((finding) => (
    finding.severity === "high" && ["REPRODUCED", "UNRESOLVED"].includes(finding.status)
  ));
  process.stdout.write(
    `지적 ${findings.length}건 / 재현 ${count("REPRODUCED")}건 / `
    + `반증 ${count("NOT_REPRODUCIBLE")}건 / 차단 ${count("BLOCKED")}건 / `
    + `미실행 ${count("NOT_TESTED")}건\n`,
  );
  process.stdout.write(`병합 차단: ${mergeBlocked ? "예" : "아니오"}\n`);
  return mergeBlocked;
}

async function main() {
  const { file, only } = parseArgs(process.argv.slice(2));
  const { data, mode } = await loadDocument(file);
  await runSelected(data.findings, only);
  await writeAtomically(file, data, mode);
  process.exitCode = summarize(data.findings) ? 1 : 0;
}

main().catch((error) => {
  process.stderr.write(`finding-runner: ${error.message}\n`);
  process.exitCode = 2;
});
