import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const CHECKER = join(ROOT, "tools/strict/checkpoint-defense.mjs");
const CONTRACT = join(ROOT, "contracts/checkpoint-defense.json");

test("independent checker removes every temporary candidate and fixture directory", () => {
  const temporaryRoot = mkdtempSync(join(tmpdir(), "checkpoint-cleanup-contract-"));
  try {
    const env = { ...process.env, TMPDIR: temporaryRoot, TMP: temporaryRoot, TEMP: temporaryRoot };
    delete env.NODE_TEST_CONTEXT;
    const result = spawnSync(
      process.execPath,
      [CHECKER, "--candidate", "HEAD", "--contract", CONTRACT, "--json"],
      { cwd: ROOT, encoding: "utf8", env, timeout: 120_000 },
    );
    assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
    assert.deepEqual(readdirSync(temporaryRoot), [], "checker leaked temporary repository content");
  } finally {
    rmSync(temporaryRoot, { recursive: true, force: true });
  }
});
