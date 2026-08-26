import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));

for (const script of [
  "scripts/acceptance-principles-mutations.sh",
  "scripts/acceptance-verify-ac-m.sh",
  "scripts/acceptance-hs-cleanroom.sh",
]) {
  test(`${script} remains GREEN after trusted delivery wiring`, () => {
    const result = spawnSync("bash", [script], { cwd: ROOT, encoding: "utf8", timeout: 180_000 });
    assert.equal(result.status, 0, `${result.stdout}\n${result.stderr}`);
  });
}

test("delivery acceptance executes the complete checkpoint gate suite", () => {
  const body = readFileSync(join(ROOT, "scripts/acceptance-checkpoint-delivery.sh"), "utf8");
  assert.match(body, /tests\/checkpoint-gate\.test\.mjs/);
});

test("pre-commit uses the index-pinned trusted secret runner", () => {
  const body = readFileSync(join(ROOT, "hooks/pre-commit"), "utf8");
  assert.match(body, /node tools\/strict\/trusted-secret-scan\.mjs/);
  assert.doesNotMatch(body, /VERIFY_SCAN_SOURCE=index bash verify\.sh/);
});
