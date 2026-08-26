#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const BUNDLE = [
  "tools/strict/checkpoint-gate.mjs",
  "tools/strict/checkpoint-js-scan.mjs",
  "tools/strict/checkpoint-policy.mjs",
  "tools/strict/checkpoint-secrets.mjs",
];

function git(args, options = {}) {
  const result = spawnSync("git", args, {
    encoding: options.encoding ?? "utf8",
    maxBuffer: 32 * 1024 * 1024,
    env: process.env,
  });
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || `git ${args.join(" ")} failed`).toString().trim();
    throw new Error(detail);
  }
  return result.stdout;
}

function emitFailure(message) {
  const json = process.argv.includes("--json");
  if (json) {
    process.stdout.write(`${JSON.stringify({
      pass: false,
      violations: [{ check: "input", file: "tools/strict/index-checkpoint-gate.mjs", detail: message }],
    })}\n`);
  } else process.stdout.write(`input: tools/strict/index-checkpoint-gate.mjs ${message}\n`);
}

function main() {
  let directory;
  try {
    const root = git(["rev-parse", "--show-toplevel"]).trim();
    process.chdir(root);
    directory = mkdtempSync(join(tmpdir(), "valuehire-index-checkpoint-gate-"));
    mkdirSync(join(directory, "tools/strict"), { recursive: true });
    for (const path of BUNDLE) {
      const content = git(["show", `:${path}`], { encoding: null });
      writeFileSync(join(directory, path), content, { mode: 0o500 });
    }
    for (const args of [["init", "-q"], ["add", ...BUNDLE]]) {
      const prepared = spawnSync("git", args, { cwd: directory, encoding: "utf8", env: process.env });
      if (prepared.status !== 0) {
        throw new Error((prepared.stderr || prepared.stdout || `git ${args[0]} failed`).trim());
      }
    }
    const result = spawnSync(process.execPath, [join(directory, BUNDLE[0]), ...process.argv.slice(2)], {
      cwd: root,
      encoding: "utf8",
      env: process.env,
      maxBuffer: 64 * 1024 * 1024,
    });
    if (result.error) throw result.error;
    process.stdout.write(result.stdout ?? "");
    process.stderr.write(result.stderr ?? "");
    return Number.isInteger(result.status) ? result.status : 1;
  } catch (error) {
    emitFailure(`cannot execute approved index bundle: ${error.message}`);
    return 1;
  } finally {
    if (directory) rmSync(directory, { recursive: true, force: true });
  }
}

process.exit(main());
