import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const SCRIPT = "scripts/acceptance-principles-mutations.sh";

function runMutationSuite() {
  return new Promise((resolve) => {
    const child = spawn("bash", [SCRIPT], { cwd: ROOT });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("close", (status, signal) => resolve({ status, signal, stdout, stderr }));
  });
}

test("captured verdict matching does not use an early-closing printf pipeline", () => {
  const body = readFileSync(join(ROOT, SCRIPT), "utf8");
  assert.doesNotMatch(body, /printf\s+'%s\\n'\s+"\$output"\s*\|\s*grep\s+-q/);
});

test("two concurrent principle mutation suites both finish GREEN", { timeout: 240_000 }, async () => {
  const results = await Promise.all([runMutationSuite(), runMutationSuite()]);
  for (const result of results) {
    assert.equal(result.signal, null, result.stderr);
    assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
    assert.match(result.stdout, /^VERDICT: PASS$/m);
    assert.match(result.stdout, /^CHECKED: [1-9][0-9]*$/m);
  }
});
