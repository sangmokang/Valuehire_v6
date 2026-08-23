import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

const TEST_DIR = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(TEST_DIR, "..");
const FIXTURE_DIR = path.join(TEST_DIR, "fixtures", "finding-runner");
const RUNNER = process.env.FINDING_RUNNER
  ? path.resolve(process.env.FINDING_RUNNER)
  : path.join(REPO_ROOT, "tools", "strict", "finding-runner.mjs");

function invoke(file, ...extraArgs) {
  return spawnSync(process.execPath, [RUNNER, "run", file, ...extraArgs], {
    cwd: REPO_ROOT,
    encoding: "utf8",
  });
}

async function tempFixture(t, name) {
  const dir = await mkdtemp(path.join(os.tmpdir(), "finding-runner-test-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const target = path.join(dir, name);
  const source = await readFile(path.join(FIXTURE_DIR, name), "utf8");
  await writeFile(target, source);
  return target;
}

async function readFinding(file, index = 0) {
  const data = JSON.parse(await readFile(file, "utf8"));
  return data.findings[index];
}

function finding({ id, cmd, expect, severity = "low", status = "NOT_TESTED" }) {
  return {
    id,
    source: "adversarial",
    claim: "기존 status나 모델 설명을 실행 증거로 믿지 않는다",
    severity,
    repro: { cmd, cwd: ".", expect },
    status,
  };
}

test("재현되는 결함은 REPRODUCED이고 high이면 병합을 차단한다", async (t) => {
  const file = await tempFixture(t, "reproduced.json");
  const result = invoke(file);

  assert.equal(result.status, 1, result.stderr);
  assert.equal((await readFinding(file)).status, "REPRODUCED");
  assert.match(result.stdout, /defect reproduced/);
  assert.match(result.stdout, /지적 1건 \/ 재현 1건 \/ 반증 0건 \/ 차단 0건 \/ 미실행 0건/);
  assert.match(result.stdout, /병합 차단: 예/);
});

test("재현되지 않는 주장은 NOT_REPRODUCIBLE이다", async (t) => {
  const file = await tempFixture(t, "not-reproducible.json");
  const result = invoke(file);

  assert.equal(result.status, 0, result.stderr);
  assert.equal((await readFinding(file)).status, "NOT_REPRODUCIBLE");
  assert.match(result.stdout, /지적 1건 \/ 재현 0건 \/ 반증 1건 \/ 차단 0건 \/ 미실행 0건/);
  assert.match(result.stdout, /병합 차단: 아니오/);
});

test("실행할 수 없는 명령은 NOT_REPRODUCIBLE이 아니라 BLOCKED이다", async (t) => {
  const file = await tempFixture(t, "blocked.json");
  const result = invoke(file);

  assert.equal(result.status, 0, result.stderr);
  assert.equal((await readFinding(file)).status, "BLOCKED");
  assert.match(result.stdout, /지적 1건 \/ 재현 0건 \/ 반증 0건 \/ 차단 1건 \/ 미실행 0건/);
  assert.match(result.stdout, /병합 차단: 아니오/);
});

test("기존 status를 믿지 않고 명령을 실행한 뒤 덮어쓴다", async (t) => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "finding-runner-counter-ac-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const marker = path.join(dir, "executed.marker");
  const file = path.join(dir, "counter-ac.json");
  const script = `require('node:fs').writeFileSync(${JSON.stringify(marker)}, 'ran'); process.stdout.write('healthy')`;
  const data = {
    findings: [finding({
      id: "F-4",
      cmd: `node -e ${JSON.stringify(script)}`,
      expect: { stdout_contains: "defect" },
      severity: "high",
      status: "REPRODUCED",
    })],
  };
  await writeFile(file, `${JSON.stringify(data, null, 2)}\n`);

  const result = invoke(file);

  assert.equal(result.status, 0, result.stderr);
  assert.equal(await readFile(marker, "utf8"), "ran");
  assert.equal((await readFinding(file)).status, "NOT_REPRODUCIBLE");
});

test("--only는 선택한 finding만 실행하고 나머지는 NOT_TESTED로 둔다", async (t) => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "finding-runner-only-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const file = path.join(dir, "only.json");
  const data = {
    findings: [
      finding({ id: "F-5", cmd: "node -e \"process.exit(9)\"", expect: { exit_not: 0 } }),
      finding({ id: "F-6", cmd: "node -e \"process.stdout.write('ok')\"", expect: { stdout_contains: "missing" } }),
    ],
  };
  await writeFile(file, `${JSON.stringify(data, null, 2)}\n`);

  const result = invoke(file, "--only", "F-6");
  const saved = JSON.parse(await readFile(file, "utf8"));

  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(saved.findings.map(({ status }) => status), ["NOT_TESTED", "NOT_REPRODUCIBLE"]);
  assert.match(result.stdout, /지적 2건 \/ 재현 0건 \/ 반증 1건 \/ 차단 0건 \/ 미실행 1건/);
});

test("선택 밖 high UNRESOLVED도 병합 차단으로 계산한다", async (t) => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "finding-runner-unresolved-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const file = path.join(dir, "unresolved.json");
  const data = {
    findings: [
      finding({ id: "F-7", cmd: "node -e \"process.exit(0)\"", expect: { exit_not: 0 }, severity: "high", status: "UNRESOLVED" }),
      finding({ id: "F-8", cmd: "node -e \"process.exit(0)\"", expect: { exit_not: 1 } }),
    ],
  };
  await writeFile(file, `${JSON.stringify(data, null, 2)}\n`);

  const result = invoke(file, "--only", "F-8");

  assert.equal(result.status, 1, result.stderr);
  assert.match(result.stdout, /병합 차단: 예/);
});

test("계약 오류나 없는 --only ID는 파일을 수정하지 않고 exit 2이다", async (t) => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "finding-runner-invalid-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const file = path.join(dir, "invalid.json");
  const data = { findings: [finding({ id: "F-9", cmd: "node -e \"process.exit(0)\"", expect: { exit_not: 0 } })] };
  const original = `${JSON.stringify(data, null, 2)}\n`;
  await writeFile(file, original);

  const result = invoke(file, "--only", "F-404");

  assert.equal(result.status, 2);
  assert.equal(await readFile(file, "utf8"), original);
  assert.match(result.stderr, /F-404/);
});
