import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const goal = readFileSync(join(ROOT, "docs/engineering/valuehire-delivery-chain-goal-2026-08-27.md"), "utf8");
const ledger = JSON.parse(readFileSync(join(ROOT, ".strict/run-ledger/strict-wu3b-20260827-472c276.json"), "utf8"));

test("goal separates the repaired local boundary from unrun remote delivery", () => {
  assert.match(goal, /현재 후보는 로컬 검사 경계를 닫았지만.*원격 PR.*CI.*merge.*미실행/s);
  assert.match(goal, /## 변경 전 판단 근거/);
  assert.doesNotMatch(goal, /현재 후보는.*검사 입력을 작업 폴더에서 바꿀 수 있고.*장부가 없/s);
});

test("goal and run ledger invalidate every known RED-test rewrite", () => {
  assert.match(goal, /WU-3b-2c.*WU-3b-6a.*invalidated/s);
  for (const id of ["WU-3b-2c", "WU-3b-6a"]) {
    assert.equal(ledger.wus.find((wu) => wu.id === id)?.status, "invalidated");
  }
});

test("run ledger records every completed WU implementation hash", () => {
  const expected = new Map([
    ["WU-3b-1", "8949d27d638bda0581274c9a9a560044cf07327f"],
    ["WU-3b-2", "050fff1f60040a64b69b3afa45b84e38d1fe8d80"],
    ["WU-3b-3", "828acbbd8b99f258c05479deacad48f5cec8540a"],
    ["WU-3b-4", "05dafb067f3ed164bbed3bec75aad5c93e760da4"],
    ["WU-3b-5", "95691cfee7a0255ca1a172744b4a9a59bbb70b11"],
    ["WU-3b-5a", "624504b175321e3e46f53ed49bb1d40cd60329b9"],
    ["WU-3b-6", "91836b95a92d130a797ec4def954f1ec6f142f97"],
    ["WU-3b-1a", "35d8c6543d602835f7414206bf62d4b4005d142f"],
    ["WU-3b-2a", "e542b96390cfecf2b84f302b8fa057d46552a783"],
    ["WU-3b-2b", "d7e12c7eb58bf58d774eb081603d24bd6e45f370"],
    ["WU-3b-7", "e58166d0a9403d2d0de112f1e8aa3e9f55c83700"],
    ["WU-3b-9", "edc5145cf60ba41a1c293a2f062511e12507fad0"],
    ["WU-3b-10", "41a6f163dcb2ec394fa53c60070f19640cf2104a"],
    ["WU-3b-11", "5b3c9f4fb3798a23616078e39335f3258a644389"],
    ["WU-3b-12", "3bf8440ce6fa2ca812b1c707577f1c327333e1b7"],
    ["WU-3b-13", "1a6f28f9f85633a1e33bdfb136b39b8fed6276a8"],
    ["WU-3b-14", "d3798dee9e6dd41a89703c8a39c3c6277c0c1bb6"],
    ["WU-3b-15", "581fee500f94f943cbf186d542374b54b31b0dfd"],
    ["WU-3b-16", "e5c2198b8e4bbe139de37ace44563f91a2b4db3b"],
    ["WU-3b-17", "cdca1bb4dfd974167f0c8fbd0fb558a335aa334c"],
  ]);
  for (const [id, implementation] of expected) {
    const wu = ledger.wus.find((entry) => entry.id === id);
    assert.equal(wu?.status, "green", id);
    assert.equal(wu?.implementation_commit, implementation, id);
  }
  assert.equal(ledger.wus.find((wu) => wu.id === "WU-3b-2c")?.implementation_commit, "69896747d43232d4a3936f9988565adb777467b3");
  assert.equal(ledger.wus.find((wu) => wu.id === "WU-3b-6a")?.implementation_commit, "6fb966a8eff5130dedf953a7cc1e7d28247befaf");
  assert.equal(ledger.wus.find((wu) => wu.id === "WU-3b-8")?.status, "invalidated");
  assert.equal(ledger.wus.find((wu) => wu.id === "WU-3b-19")?.status, "green-pending-evidence");
});
