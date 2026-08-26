#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { runTrustedSecretScan } from "./checkpoint-secrets.mjs";

function parseArgs(argv) {
  let localPatternSha256 = process.env.STRICT_SECRET_PATTERN_SHA256 || null;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg !== "--secret-pattern-sha256") throw new Error(`unknown argument: ${arg}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${arg} requires a value`);
    localPatternSha256 = value;
    index += 1;
  }
  return { localPatternSha256 };
}

function git(args, options = {}) {
  return execFileSync("git", args, { encoding: "utf8", ...options });
}

function readIndex(path) {
  return git(["show", `:${path}`]);
}

function emit(text) {
  if (text) process.stdout.write(text.endsWith("\n") ? text : `${text}\n`);
}

function main() {
  try {
    const args = parseArgs(process.argv.slice(2));
    process.chdir(git(["rev-parse", "--show-toplevel"]).trim());
    const result = runTrustedSecretScan({ readIndex, localPatternSha256: args.localPatternSha256 });
    if (result.status !== 0) {
      emit(`FAIL: trusted secret scan (scanner exit ${result.status})`);
      emit(result.stdout);
      emit(result.stderr);
      return 1;
    }
    emit("PASS: trusted secret scan");
    return 0;
  } catch (error) {
    emit(`FAIL: trusted secret scan (${error.message})`);
    return 1;
  }
}

process.exit(main());
