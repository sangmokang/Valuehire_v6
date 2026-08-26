import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const DRAFT = join(ROOT, "docs/engineering/valuehire-delivery-chain-pr-draft-2026-08-27.md");
const RUN_LEDGER = join(ROOT, ".strict/run-ledger/strict-wu3b-20260827-472c276.json");

test("PR draft preserves the approval and remote-evidence boundary", () => {
  const body = readFileSync(DRAFT, "utf8");
  assert.match(body, /PR: `NOT_RUN`/);
  assert.match(body, /CI: `NOT_RUN`/);
  assert.match(body, /Merge: `NOT_RUN`/);
  assert.match(body, /Deploy: `NOT_RUN`/);
  assert.match(body, /Live Verify: `NOT_RUN`/);
  assert.match(body, /checkpoint readiness: `NOT_RUN`/);
  assert.match(body, /overall T: `NOT_RUN`/);
  assert.match(body, /사용자 승인 전 실행 금지/);
});

test("PR draft exposes the divergent base instead of presenting a runnable create command", () => {
  const body = readFileSync(DRAFT, "utf8");
  assert.match(body, /git rev-list --left-right --count origin\/main\.\.\.HEAD/);
  assert.match(body, /정확한 좌우 커밋 수는 아직 `NOT_RUN`/);
  assert.doesNotMatch(body, /origin\/main.*\d+커밋 (?:뒤|앞)/);
  assert.match(body, /PR 생성 명령: `BLOCKED`/);
  assert.match(body, /git push -u origin task\/wu3b-delivery-chain-20260827/);
  assert.match(body, /gh pr create --base main --head task\/wu3b-delivery-chain-20260827/);
});

test("WU-3b-6 scope covers the RED test that defines its PR boundary", () => {
  const ledger = JSON.parse(readFileSync(RUN_LEDGER, "utf8"));
  const wu = ledger.wus.find(({ id }) => id === "WU-3b-6");
  assert.ok(wu, "WU-3b-6 must exist");
  assert.ok(wu.scope.includes("tests/pr-draft.test.mjs"));
});
