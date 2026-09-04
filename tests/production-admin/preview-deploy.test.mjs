import assert from "node:assert/strict";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const script = fileURLToPath(new URL("../../scripts/deploy-preview.sh", import.meta.url));
const goodSha = "a".repeat(40);
const expectedLink = {
  projectId: "prj_isTeytMDr2EiXW5hg5rv4wPdyBW5",
  orgId: "team_NB0uDciuQYLf5akFKK7Sb3pU",
  projectName: "valuehire-v6",
};

function executable(path, source) {
  writeFileSync(path, source, { mode: 0o700 });
  chmodSync(path, 0o700);
}

function runDeploy({
  sha = goodSha,
  configuredSha = goodSha,
  status = "",
  environment = "preview",
  scope = "sangmokangs-projects",
  contractStatus = 0,
  projectLink = expectedLink,
} = {}) {
  const root = mkdtempSync(join(tmpdir(), "valuehire-preview-deploy-"));
  const bin = join(root, "bin");
  const capture = join(root, "vercel-args");
  const contractCapture = join(root, "contract-args");
  mkdirSync(bin, { recursive: true });
  mkdirSync(join(root, "scripts"), { recursive: true });
  mkdirSync(join(root, ".vercel"), { recursive: true });
  writeFileSync(join(root, "scripts", "deploy-preview.sh"), readFileSync(script));
  chmodSync(join(root, "scripts", "deploy-preview.sh"), 0o700);
  writeFileSync(join(root, ".vercel", "project.json"), JSON.stringify(projectLink));
  writeFileSync(join(root, "scripts", "check-deployment-contract.mjs"), `
import { writeFileSync } from "node:fs";
writeFileSync(process.env.FAKE_CONTRACT_CAPTURE, process.argv.slice(2).join("\\n"));
process.exit(Number(process.env.FAKE_CONTRACT_STATUS));
`);
  executable(join(bin, "git"), `#!/usr/bin/env bash
if [[ "$1" == "status" ]]; then printf '%s' "\${FAKE_GIT_STATUS:-}"; exit 0; fi
if [[ "$1" == "rev-parse" && "$2" == "HEAD" ]]; then printf '%s\\n' "\${FAKE_GIT_SHA}"; exit 0; fi
exit 91
`);
  executable(join(bin, "vercel"), "#!/usr/bin/env bash\nprintf '%s\\n' \"$@\" > \"$FAKE_VERCEL_CAPTURE\"\n");
  const result = spawnSync("/bin/bash", [join(root, "scripts", "deploy-preview.sh")], {
    encoding: "utf8",
    env: {
      ...process.env,
      PATH: `${bin}:${process.env.PATH}`,
      FAKE_GIT_SHA: sha,
      FAKE_GIT_STATUS: status,
      FAKE_VERCEL_CAPTURE: capture,
      FAKE_CONTRACT_CAPTURE: contractCapture,
      FAKE_CONTRACT_STATUS: String(contractStatus),
      VALUEHIRE_ENV: environment,
      VALUEHIRE_VERCEL_SCOPE: scope,
      VALUEHIRE_DEPLOY_SHA: configuredSha,
      VALUEHIRE_SCHEMA_DIGEST: "14e3755595b5804f5059dd0a455f0c8a38ef3106d18b53555fa0c56e47868089",
      VALUEHIRE_PUBLIC_URL: "https://preview.example.test",
      VALUEHIRE_SUPABASE_URL: "https://preview.supabase.co",
      VALUEHIRE_SUPABASE_ANON_KEY: "test-anon-key",
      VALUEHIRE_SUPABASE_SERVICE_ROLE_KEY: "test-service-key",
      VALUEHIRE_ADMIN_EMAIL_SHA256: "b".repeat(64),
      VALUEHIRE_TENANT_ID: "E2E-TEST-deploy-contract",
    },
  });
  const args = result.status === 0 ? readFileSync(capture, "utf8").trim().split("\n") : [];
  let contractArgs = [];
  try {
    contractArgs = readFileSync(contractCapture, "utf8").trim().split("\n").filter(Boolean);
  } catch {
    contractArgs = [];
  }
  rmSync(root, { recursive: true, force: true });
  return { ...result, args, contractArgs };
}

test("Preview deploy pins the clean HEAD into the application SHA without overriding Vercel system provenance", () => {
  const result = runDeploy();
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(result.args, [
    "deploy",
    "--target",
    "preview",
    "--yes",
    "--scope",
    "sangmokangs-projects",
    "--env",
    `VALUEHIRE_DEPLOY_SHA=${goodSha}`,
  ]);
  assert.equal(result.args.some((arg) => arg.startsWith("VERCEL_GIT_COMMIT_SHA=")), false);
  assert.equal(result.args.includes("--prod"), false);
  assert.deepEqual(result.contractArgs, ["--require-current-env"]);
});

test("Preview deploy rejects a configured SHA that differs from HEAD", () => {
  const result = runDeploy({ configuredSha: "b".repeat(40) });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /VALUEHIRE_DEPLOY_SHA differs from HEAD/);
  assert.deepEqual(result.args, []);
});

test("Preview deploy rejects a dirty worktree", () => {
  const result = runDeploy({ status: " M server/admin/config.js" });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /worktree must be clean/);
  assert.deepEqual(result.args, []);
});

test("Preview deploy rejects a different Vercel scope", () => {
  const result = runDeploy({ scope: "different-scope" });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /unexpected Vercel scope/);
  assert.deepEqual(result.args, []);
});

test("Preview deploy rejects a Production environment before Vercel runs", () => {
  const result = runDeploy({ environment: "production" });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /VALUEHIRE_ENV must be preview/);
  assert.deepEqual(result.args, []);
});

test("Preview deploy stops when the current environment contract fails", () => {
  const result = runDeploy({ contractStatus: 23 });
  assert.equal(result.status, 23);
  assert.deepEqual(result.contractArgs, ["--require-current-env"]);
  assert.deepEqual(result.args, []);
});

test("Preview deploy rejects a different linked Vercel project", () => {
  const result = runDeploy({ projectLink: { ...expectedLink, projectId: "prj_wrong" } });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Vercel project link differs/);
  assert.deepEqual(result.contractArgs, []);
  assert.deepEqual(result.args, []);
});
