import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const goal = readFileSync(join(ROOT, "docs/engineering/valuehire-delivery-chain-goal-2026-08-27.md"), "utf8");

test("goal separates the repaired local boundary from unrun remote delivery", () => {
  assert.match(goal, /현재 후보는 로컬 검사 경계를 닫았지만.*원격 PR.*CI.*merge.*미실행/s);
  assert.match(goal, /## 변경 전 판단 근거/);
  assert.doesNotMatch(goal, /현재 후보는.*검사 입력을 작업 폴더에서 바꿀 수 있고.*장부가 없/s);
});
