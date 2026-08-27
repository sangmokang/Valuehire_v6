import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

test("pre-push wrapper executes the candidate checker blob instead of worktree bait", () => {
  const parent = mkdtempSync(join(tmpdir(), "checkpoint-checker-bait-"));
  const cwd = join(parent, "repo");
  try {
    execFileSync("git", ["clone", "-q", "--no-local", ROOT, cwd]);
    execFileSync("git", ["checkout", "-q", execFileSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8" }).trim()], { cwd });
    writeFileSync(
      join(cwd, "tools/strict/checkpoint-defense.mjs"),
      'process.stdout.write(JSON.stringify({pass:true,checked:77}) + "\\n");\n',
    );
    const result = spawnSync("bash", ["scripts/acceptance-checkpoint-defense.sh", "HEAD"], {
      cwd,
      encoding: "utf8",
      timeout: 120_000,
    });
    assert.notEqual(result.status, 0, `${result.stdout}\n${result.stderr}`);
  } finally {
    rmSync(parent, { recursive: true, force: true });
  }
});
