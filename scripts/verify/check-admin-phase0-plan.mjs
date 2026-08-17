#!/usr/bin/env node

import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const relativePaths = {
  plan: "docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md",
  dependencies: "docs/engineering/admin-weekly-dashboard-v6-canonical-dependencies-2026-08-17.md",
  controller: "docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md",
  invalidation: "docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-invalidation-2026-08-17.md",
  oldAudit: "docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-2026-08-17.md",
  sot: "docs/sot/verification-commands.md",
  registry: "docs/sot/mechanism-registry.yaml",
  workflow: ".github/workflows/verify.yml",
  packageJson: "package.json",
};

const requiredFields = [
  "parent_ac",
  "micro_id",
  "single_observable_result",
  "single_failure_reason",
  "rollback_unit",
  "dependencies",
  "allowed_files",
  "forbidden_scope",
  "red_command",
  "green_command",
  "mutation_method",
  "production_call_path",
  "target_count_method",
  "cannot_split_reason",
  "external_side_effect_count_expected",
];

const expectedChain = new Map([
  ["P0-01-baseline-and-audited-plan", []],
  ["P0-02-node-version-pin", ["P0-01-baseline-and-audited-plan"]],
  ["P0-03-pnpm-version-pin", ["P0-02-node-version-pin"]],
  ["P0-03A-node-engine-pin", ["P0-03-pnpm-version-pin"]],
  ["P0-04-root-private", ["P0-03A-node-engine-pin"]],
  ["P0-04-workspace-declaration", ["P0-04-root-private"]],
  ["P0-04A-generated-artifact-ignore", ["P0-04-workspace-declaration"]],
  ["P0-04T-tracked-generated-artifact-guard", ["P0-04A-generated-artifact-ignore"]],
  ["P0-05-admin-exact-package-contract", ["P0-04T-tracked-generated-artifact-guard"]],
]);

function read(root, relativePath) {
  const absolutePath = path.join(root, relativePath);
  if (!fs.existsSync(absolutePath)) {
    return null;
  }
  return fs.readFileSync(absolutePath, "utf8");
}

function parseList(value) {
  const match = value?.match(/^\[(.*)]$/);
  if (!match) {
    return [];
  }
  return match[1]
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function parsePhaseRows(text) {
  const rows = [];
  let row = null;

  for (const line of text.split(/\r?\n/)) {
    const start = line.match(/^- parent_ac:\s*(.*)$/);
    if (start) {
      if (row) rows.push(row);
      row = { parent_ac: start[1].trim() };
      continue;
    }
    if (!row) continue;
    const field = line.match(/^  ([a-z_]+):\s*(.*)$/);
    if (field) row[field[1]] = field[2].trim();
  }
  if (row) rows.push(row);
  return rows;
}

function parseDependencyGraph(text, errors) {
  const graph = new Map();
  const blockerGraph = new Map();
  const lines = text.split(/\r?\n/);

  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(/^\s*- consumers:\s*(\[.*])$/);
    if (!match) continue;
    const consumers = parseList(match[1]);
    let required = null;
    let blockers = [];
    for (let cursor = index + 1; cursor < lines.length; cursor += 1) {
      if (/^\s*- consumers:/.test(lines[cursor])) break;
      const requiredMatch = lines[cursor].match(/^\s+requires_micro_ids:\s*(\[.*])$/);
      if (requiredMatch) required = parseList(requiredMatch[1]);
      const blockerMatch = lines[cursor].match(/^\s+requires_blocker_ids:\s*(\[.*])$/);
      if (blockerMatch) blockers = parseList(blockerMatch[1]);
    }
    if (required === null) {
      errors.push(`dependency group has no requires_micro_ids: ${consumers.join(",")}`);
      continue;
    }
    for (const consumer of consumers) {
      if (graph.has(consumer)) errors.push(`duplicate dependency consumer: ${consumer}`);
      graph.set(consumer, required);
      blockerGraph.set(consumer, blockers);
    }
  }
  return { graph, blockerGraph };
}

function sameMembers(actual, expected) {
  return actual.length === expected.length && actual.every((value, index) => value === expected[index]);
}

function requireIncludes(errors, value, needle, label) {
  if (!value?.includes(needle)) errors.push(`${label} must include ${needle}`);
}

function requireExcludes(errors, value, needle, label) {
  if (value?.includes(needle)) errors.push(`${label} must not include ${needle}`);
}

function sha256(text) {
  return crypto.createHash("sha256").update(text).digest("hex");
}

function validate(root) {
  const errors = [];
  const files = {};
  for (const [key, relativePath] of Object.entries(relativePaths)) {
    files[key] = read(root, relativePath);
    if (files[key] === null) {
      errors.push(`missing file: ${relativePath}`);
      files[key] = "";
    }
  }

  const rows = parsePhaseRows(files.plan);
  const rowById = new Map();
  for (const row of rows) {
    if (!row.micro_id) {
      errors.push("phase row missing micro_id");
      continue;
    }
    if (rowById.has(row.micro_id)) errors.push(`duplicate phase micro_id: ${row.micro_id}`);
    rowById.set(row.micro_id, row);
    for (const field of requiredFields) {
      if (!(field in row) || row[field] === "") errors.push(`${row.micro_id} missing required field: ${field}`);
    }
  }
  if (rows.length !== 26) errors.push(`phase0 row count must be 26, got ${rows.length}`);

  const requireRow = (id) => {
    const row = rowById.get(id);
    if (!row) errors.push(`required phase row missing: ${id}`);
    return row ?? {};
  };

  const p001 = requireRow("P0-01-baseline-and-audited-plan");
  requireIncludes(errors, p001.single_observable_result, "fresh", "P0-01 result");
  requireIncludes(errors, p001.single_failure_reason, "무효", "P0-01 failure reason");
  requireIncludes(errors, p001.dependencies, "BLK-RUNNER-ONLY-AUDIT-EVIDENCE", "P0-01 dependencies");

  const p002 = requireRow("P0-02-node-version-pin");
  requireIncludes(errors, p002.single_observable_result, ".node-version", "P0-02 result");
  requireIncludes(errors, p002.single_observable_result, "실제", "P0-02 result");
  requireIncludes(errors, p002.mutation_method, "symlink", "P0-02 mutation");
  requireIncludes(errors, p002.dependencies, "BLK-NODE-RUNTIME-CONSUMER", "P0-02 dependencies");

  const p003 = requireRow("P0-03-pnpm-version-pin");
  requireIncludes(errors, p003.single_observable_result, "Corepack", "P0-03 result");
  requireIncludes(errors, p003.mutation_method, "\\n", "P0-03 mutation");
  requireIncludes(errors, p003.production_call_path, "Corepack", "P0-03 production path");

  const p003a = requireRow("P0-03A-node-engine-pin");
  requireIncludes(errors, p003a.single_observable_result, "engines.node", "P0-03A result");
  requireIncludes(errors, p003a.single_observable_result, "24.19.0", "P0-03A result");
  requireExcludes(errors, p003a.allowed_files, ".node-version", "P0-03A allowed files");

  const p004 = requireRow("P0-04-root-private");
  requireIncludes(errors, p004.single_observable_result, "private=true", "P0-04 result");
  requireExcludes(errors, p004.single_observable_result, "workspace", "P0-04 result");
  requireExcludes(errors, p004.allowed_files, "pnpm-workspace.yaml", "P0-04 allowed files");

  const p004w = requireRow("P0-04-workspace-declaration");
  requireIncludes(errors, p004w.single_observable_result, "pnpm-workspace.yaml", "P0-04 workspace result");
  requireExcludes(errors, p004w.single_observable_result, "private=true", "P0-04 workspace result");
  requireIncludes(errors, p004w.production_call_path, "pnpm", "P0-04 workspace production path");

  if (rowById.has("P0-04-root-private-workspace")) {
    errors.push("superseded combined P0-04 row must not remain active");
  }

  const p004a = requireRow("P0-04A-generated-artifact-ignore");
  requireIncludes(errors, p004a.single_observable_result, "git check-ignore -v", "P0-04A result");
  requireIncludes(errors, p004a.single_observable_result, "overlapping fallback=0", "P0-04A result");
  requireExcludes(errors, p004a.single_observable_result, "추적", "P0-04A result");
  requireIncludes(errors, p004a.mutation_method, "중복", "P0-04A mutation");

  const p004t = requireRow("P0-04T-tracked-generated-artifact-guard");
  requireIncludes(errors, p004t.single_observable_result, "모든", "P0-04T result");
  requireIncludes(errors, p004t.single_observable_result, "추적", "P0-04T result");
  requireExcludes(errors, p004t.single_observable_result, "ignore", "P0-04T result");
  requireIncludes(errors, p004t.mutation_method, "임의", "P0-04T mutation");
  requireIncludes(errors, p004t.target_count_method, "prefix", "P0-04T target count");
  requireIncludes(errors, p004t.production_call_path, "CI", "P0-04T production path");

  const { graph, blockerGraph } = parseDependencyGraph(files.dependencies, errors);
  if (graph.size !== 135) errors.push(`active dependency consumer count must be 135, got ${graph.size}`);
  for (const id of rowById.keys()) {
    if (!graph.has(id)) errors.push(`phase micro missing from dependency graph: ${id}`);
  }
  for (const [consumer, expected] of expectedChain.entries()) {
    const actual = graph.get(consumer) ?? [];
    if (!sameMembers(actual, expected)) {
      errors.push(`${consumer} dependencies must be [${expected.join(", ")}], got [${actual.join(", ")}]`);
    }
  }
  const dependencyBlockers = files.dependencies.match(/^  - BLK-[A-Z0-9-]+$/gm) ?? [];
  const blockerNames = new Set(dependencyBlockers.map((line) => line.trim().slice(2)));
  for (const blocker of ["BLK-RUNNER-ONLY-AUDIT-EVIDENCE", "BLK-NODE-RUNTIME-CONSUMER"]) {
    if (!blockerNames.has(blocker)) errors.push(`required blocker missing: ${blocker}`);
  }
  if (!(blockerGraph.get("P0-01-baseline-and-audited-plan") ?? []).includes("BLK-RUNNER-ONLY-AUDIT-EVIDENCE")) {
    errors.push("P0-01 must be blocked by runner-only audit evidence");
  }
  if (!(blockerGraph.get("P0-02-node-version-pin") ?? []).includes("BLK-NODE-RUNTIME-CONSUMER")) {
    errors.push("P0-02 must be blocked until the runtime consumer is selected");
  }

  const visiting = new Set();
  const visited = new Set();
  const visit = (id) => {
    if (visiting.has(id)) {
      errors.push(`dependency cycle detected at ${id}`);
      return;
    }
    if (visited.has(id)) return;
    visiting.add(id);
    for (const dependency of graph.get(id) ?? []) {
      if (graph.has(dependency)) visit(dependency);
    }
    visiting.delete(id);
    visited.add(id);
  };
  for (const id of graph.keys()) visit(id);

  requireIncludes(errors, files.controller, "P0-03A-node-engine-pin", "controller");
  requireIncludes(errors, files.controller, "P0-04-workspace-declaration", "controller");
  requireIncludes(errors, files.controller, "P0-04T-tracked-generated-artifact-guard", "controller");
  requireIncludes(errors, files.controller, "실행 허가가 없다", "controller invalidation rule");

  requireIncludes(errors, files.invalidation, "VERDICT: INVALIDATED", "audit invalidation");
  requireIncludes(errors, files.invalidation, "execution_permission: false", "audit invalidation");
  requireIncludes(errors, files.invalidation, "strict_micro_pass_count: 0", "audit invalidation");
  requireIncludes(errors, files.invalidation, "active_micro_count: 135", "audit invalidation");
  requireIncludes(errors, files.invalidation, "engines.node", "audit invalidation");
  requireIncludes(errors, files.invalidation, "P0-04", "audit invalidation");
  const auditHashMatch = files.invalidation.match(/invalidated_audit_sha256:\s*([a-f0-9]{64})/);
  if (!auditHashMatch || auditHashMatch[1] !== sha256(files.oldAudit)) {
    errors.push("audit invalidation must preserve the exact SHA-256 of the old audit");
  }

  requireIncludes(errors, files.sot, "루트 `package.json`은 존재", "verification SOT");
  requireIncludes(errors, files.sot, "npm harness 레포는 아니다", "verification SOT");
  requireExcludes(errors, files.sot, "`package.json`이 없고", "verification SOT");

  let packageData = null;
  try {
    packageData = JSON.parse(files.packageJson);
  } catch {
    errors.push("root package.json must be valid JSON for SOT fact checking");
  }
  if (packageData && Object.prototype.hasOwnProperty.call(packageData, "scripts")) {
    errors.push("verification SOT assumes the root package.json still has no harness scripts");
  }

  const activeWorkflow = files.workflow
    .split(/\r?\n/)
    .filter((line) => !/^\s*#/.test(line))
    .join("\n");
  requireIncludes(
    errors,
    activeWorkflow,
    "run: bash scripts/acceptance-admin-phase0-plan.sh",
    "CI workflow",
  );
  if (/^\s*if:\s*(false|'false'|"false")\s*$/m.test(activeWorkflow)) {
    errors.push("CI workflow contains a disabled step");
  }
  requireIncludes(errors, files.registry, 'id: "admin-phase0-plan-ci"', "mechanism registry");
  requireIncludes(
    errors,
    files.registry,
    'target: "run: bash scripts/acceptance-admin-phase0-plan.sh"',
    "mechanism registry",
  );

  return { errors, phaseRows: rows.length, consumers: graph.size };
}

function removeRow(text, id) {
  const lines = text.split("\n");
  const idIndex = lines.findIndex((line) => line === `  micro_id: ${id}`);
  if (idIndex < 1) throw new Error(`cannot find row ${id}`);
  let start = idIndex - 1;
  while (start >= 0 && !lines[start].startsWith("- parent_ac:")) start -= 1;
  let end = idIndex + 1;
  while (end < lines.length && !lines[end].startsWith("- parent_ac:")) end += 1;
  lines.splice(start, end - start);
  return lines.join("\n");
}

function replaceOnce(text, from, to) {
  const index = text.indexOf(from);
  if (index < 0) throw new Error(`mutation target not found: ${from}`);
  return `${text.slice(0, index)}${to}${text.slice(index + from.length)}`;
}

function copyBundle(sourceRoot, targetRoot) {
  for (const relativePath of Object.values(relativePaths)) {
    const source = path.join(sourceRoot, relativePath);
    const target = path.join(targetRoot, relativePath);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(source, target);
  }
}

function runSelfTest(root) {
  const baseline = validate(root);
  if (baseline.errors.length > 0) return baseline;

  const mutations = [
    {
      name: "missing-engines-row",
      expected: "required phase row missing: P0-03A-node-engine-pin",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.plan);
        fs.writeFileSync(file, removeRow(fs.readFileSync(file, "utf8"), "P0-03A-node-engine-pin"));
      },
    },
    {
      name: "recombined-private-workspace",
      expected: "P0-04 result must not include workspace",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.plan);
        let text = fs.readFileSync(file, "utf8");
        text = removeRow(text, "P0-04-workspace-declaration");
        text = replaceOnce(text, "root package.json이 private=true라서", "root package.json이 private=true이고 workspace가 선언돼서");
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "missing-invalidation",
      expected: "audit invalidation must include VERDICT: INVALIDATED",
      apply(tempRoot) {
        fs.writeFileSync(path.join(tempRoot, relativePaths.invalidation), "VERDICT: PASS\n");
      },
    },
    {
      name: "stale-sot-fact",
      expected: "verification SOT must include 루트 `package.json`은 존재",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.sot);
        const text = fs.readFileSync(file, "utf8").replace("루트 `package.json`은 존재", "`package.json`이 없고");
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-registration-removed",
      expected: "CI workflow must include run: bash scripts/acceptance-admin-phase0-plan.sh",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = fs.readFileSync(file, "utf8").replace("run: bash scripts/acceptance-admin-phase0-plan.sh", "run: echo phase0-plan-check-disabled");
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "dependency-skip",
      expected: "P0-03A-node-engine-pin dependencies must be [P0-03-pnpm-version-pin]",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.dependencies);
        const text = fs.readFileSync(file, "utf8").replace(
          "  - consumers: [P0-03A-node-engine-pin]\n    requires_micro_ids: [P0-03-pnpm-version-pin]",
          "  - consumers: [P0-03A-node-engine-pin]\n    requires_micro_ids: [P0-02-node-version-pin]",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "recombined-artifact-boundaries",
      expected: "P0-04A result must not include 추적",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.plan);
        let text = fs.readFileSync(file, "utf8");
        text = removeRow(text, "P0-04T-tracked-generated-artifact-guard");
        text = replaceOnce(
          text,
          "각 required artifact root의 canary를 git check-ignore -v로 확인했을 때 canonical root rule이 owner이고 overlapping fallback=0이다",
          "각 required artifact root의 ignore와 추적 검사가 함께 통과하고 overlapping fallback=0이다",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "artifact-ignore-owner-contract-removed",
      expected: "P0-04A result must include overlapping fallback=0",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.plan);
        const text = fs.readFileSync(file, "utf8").replace("overlapping fallback=0", "fallback count unchecked");
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "artifact-arbitrary-name-contract-removed",
      expected: "P0-04T mutation must include 임의",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.plan);
        const text = fs.readFileSync(file, "utf8").replace("임의 이름의 추적 파일", "고정 canary 추적 파일");
        fs.writeFileSync(file, text);
      },
    },
  ];

  let caught = 0;
  for (const mutation of mutations) {
    const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "admin-phase0-plan-"));
    try {
      copyBundle(root, tempRoot);
      mutation.apply(tempRoot);
      const result = validate(tempRoot);
      if (!result.errors.some((error) => error.includes(mutation.expected))) {
        return {
          errors: [`mutation ${mutation.name} was not caught with expected reason: ${mutation.expected}`],
          phaseRows: baseline.phaseRows,
          consumers: baseline.consumers,
          mutationsCaught: caught,
          mutationsRequired: mutations.length,
        };
      }
      caught += 1;
    } finally {
      fs.rmSync(tempRoot, { recursive: true, force: true });
    }
  }
  return {
    errors: [],
    phaseRows: baseline.phaseRows,
    consumers: baseline.consumers,
    mutationsCaught: caught,
    mutationsRequired: mutations.length,
  };
}

const args = process.argv.slice(2);
const selfTest = args.includes("--self-test");
const rootArg = args.find((arg) => arg !== "--self-test") ?? process.cwd();
const root = path.resolve(rootArg);
const result = selfTest ? runSelfTest(root) : validate(root);

if (result.errors.length > 0) {
  for (const error of result.errors) console.error(`FAIL: ${error}`);
  console.error(
    `ADMIN_PHASE0_PLAN_CHECK phase0Rows=${result.phaseRows} consumers=${result.consumers} mutationsCaught=${result.mutationsCaught ?? 0} mutationsRequired=${result.mutationsRequired ?? 0} reason=contract-mismatch`,
  );
  process.exit(1);
}

console.log("PASS: repaired Phase 0 plan, invalidation, dependency graph, SOT, and CI registration agree");
console.log(
  `ADMIN_PHASE0_PLAN_CHECK phase0Rows=${result.phaseRows} consumers=${result.consumers} mutationsCaught=${result.mutationsCaught ?? 0} mutationsRequired=${result.mutationsRequired ?? 0} reason=null`,
);
