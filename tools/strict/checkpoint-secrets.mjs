import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

function indexed(readIndex, path) {
  try {
    return readIndex(path);
  } catch {
    throw new Error(`${path} is not present in the Git index`);
  }
}

function effectivePatterns(text) {
  return text
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.replace(/[\t ]*#.*$/, ""))
    .filter((line) => line.trim().length > 0);
}

function approvedLocalPatterns(expectedSha256) {
  const path = ".secret-patterns";
  if (!existsSync(path)) {
    if (expectedSha256) throw new Error(`${path} is missing but an approval SHA was provided`);
    return "";
  }
  if (!expectedSha256) throw new Error(`${path} exists, so --secret-pattern-sha256 approval SHA is required`);
  if (!/^[0-9a-f]{64}$/.test(expectedSha256)) {
    throw new Error("--secret-pattern-sha256 must be 64 lowercase hexadecimal characters");
  }
  const content = readFileSync(path);
  const actual = createHash("sha256").update(content).digest("hex");
  if (actual !== expectedSha256) throw new Error(`${path} SHA-256 mismatch`);
  return content.toString("utf8");
}

export function runTrustedSecretScan({ readIndex, localPatternSha256, env = process.env }) {
  const verify = indexed(readIndex, "verify.sh");
  const defaults = indexed(readIndex, ".secret-patterns.default");
  const local = approvedLocalPatterns(localPatternSha256);
  const combined = `${defaults.replace(/\n?$/, "\n")}${local}`;
  if (effectivePatterns(combined).length === 0) throw new Error("trusted secret policy has zero effective patterns");

  const directory = mkdtempSync(join(tmpdir(), "checkpoint-secret-authority-"));
  const verifyPath = join(directory, "verify.sh");
  const patternsPath = join(directory, "patterns.ere");
  try {
    writeFileSync(verifyPath, verify, { mode: 0o500 });
    writeFileSync(patternsPath, combined, { mode: 0o400 });
    const result = spawnSync("bash", [verifyPath], {
      encoding: "utf8",
      env: {
        ...env,
        SECRET_PATTERNS_FILE: patternsPath,
        VERIFY_SCAN_SOURCE: "index",
      },
      maxBuffer: 16 * 1024 * 1024,
    });
    if (result.error) throw result.error;
    const output = `${result.stdout ?? ""}${result.stderr ?? ""}`;
    if (result.status === 0 && !/^PASS:\s+.+/m.test(output)) {
      throw new Error("trusted secret scanner exited zero with no verdict output");
    }
    return { status: result.status, stdout: result.stdout ?? "", stderr: result.stderr ?? "" };
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}
