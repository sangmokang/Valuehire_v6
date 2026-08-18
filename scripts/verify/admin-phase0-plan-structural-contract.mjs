import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";

export const relativePaths = {
  replacementGoal: "docs/engineering/admin-weekly-dashboard-v6-replacement-goal-2026-08-16.md",
  plan: "docs/engineering/admin-weekly-dashboard-v6-atomic-plan-phase0-2026-08-17.md",
  dependencies: "docs/engineering/admin-weekly-dashboard-v6-canonical-dependencies-2026-08-17.md",
  controller: "docs/engineering/admin-weekly-dashboard-v6-controller-goal-2026-08-17.md",
  invalidation: "docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-invalidation-2026-08-17.md",
  oldAudit: "docs/engineering/admin-weekly-dashboard-v6-plan-audit-v2-2026-08-17.md",
  sot: "docs/sot/verification-commands.md",
  registry: "docs/sot/mechanism-registry.yaml",
  workflow: ".github/workflows/verify.yml",
  packageJson: "package.json",
  contract: "scripts/verify/fixtures/admin-phase0-plan-structural-contract.json",
};

const expectedContractSha256 = "b1a6a4a890ec7f2b6c1e1d18f0926a4e58d49bc83e1007be7b796b152977fcb5";

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
  const duplicateFields = [];
  const unexpectedFields = [];
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
    if (field) {
      const [fieldName, value] = [field[1], field[2].trim()];
      if (Object.prototype.hasOwnProperty.call(row, fieldName)) {
        duplicateFields.push(`${row.micro_id ?? "UNKNOWN"}.${fieldName}`);
      } else if (!requiredFields.includes(fieldName)) {
        unexpectedFields.push(`${row.micro_id ?? "UNKNOWN"}.${fieldName}`);
      } else {
        row[fieldName] = value;
      }
    }
  }
  if (row) rows.push(row);
  return { rows, duplicateFields, unexpectedFields };
}

function parseDependencyGraph(text, errors) {
  const graph = new Map();
  const blockerGraph = new Map();
  const duplicateConsumers = [];
  const duplicateMicroDependencies = [];
  const duplicateBlockerDependencies = [];
  const lines = text.split(/\r?\n/);

  for (let index = 0; index < lines.length; index += 1) {
    const match = lines[index].match(/^\s*- consumers:\s*(\[.*])$/);
    if (!match) continue;
    const consumers = parseList(match[1]);
    if (consumers.length === 0) errors.push("dependency group has zero consumers");
    let required = null;
    let blockers = null;
    for (let cursor = index + 1; cursor < lines.length; cursor += 1) {
      if (/^\s*- consumers:/.test(lines[cursor])) break;
      const requiredMatch = lines[cursor].match(/^\s+requires_micro_ids:\s*(\[.*])$/);
      if (requiredMatch) {
        if (required !== null) {
          errors.push(`duplicate dependency field: ${consumers.join(",")}.requires_micro_ids`);
        } else {
          required = parseList(requiredMatch[1]);
        }
      }
      const blockerMatch = lines[cursor].match(/^\s+requires_blocker_ids:\s*(\[.*])$/);
      if (blockerMatch) {
        if (blockers !== null) {
          errors.push(`duplicate dependency field: ${consumers.join(",")}.requires_blocker_ids`);
        } else {
          blockers = parseList(blockerMatch[1]);
        }
      }
    }
    if (required === null) {
      errors.push(`dependency group has no requires_micro_ids: ${consumers.join(",")}`);
      continue;
    }
    const blockerList = blockers ?? [];
    const repeatedMicroDependencies = required.filter((value, position) => required.indexOf(value) !== position);
    const repeatedBlockerDependencies = blockerList.filter((value, position) => blockerList.indexOf(value) !== position);
    for (const consumer of consumers) {
      if (graph.has(consumer)) duplicateConsumers.push(consumer);
      for (const dependency of repeatedMicroDependencies) {
        duplicateMicroDependencies.push(`${consumer}->${dependency}`);
      }
      for (const blocker of repeatedBlockerDependencies) {
        duplicateBlockerDependencies.push(`${consumer}->${blocker}`);
      }
      graph.set(consumer, required);
      blockerGraph.set(consumer, blockerList);
    }
  }
  return {
    graph,
    blockerGraph,
    duplicateConsumers,
    duplicateMicroDependencies,
    duplicateBlockerDependencies,
  };
}

function sameMembers(actual, expected) {
  const actualSorted = sorted(actual);
  const expectedSorted = sorted(expected);
  return actualSorted.length === expectedSorted.length
    && actualSorted.every((value, index) => value === expectedSorted[index]);
}

function sorted(values) {
  return [...values].sort((left, right) => left.localeCompare(right));
}

function formatList(values) {
  return `[${values.join(", ")}]`;
}

function parseBlockerDeclarations(text) {
  const section = text.match(/^blockers:\s*\n([\s\S]*?)^groups:\s*$/m)?.[1] ?? "";
  const blockers = [];
  for (const line of section.split(/\r?\n/)) {
    const match = line.match(/^  - (BLK-[A-Z0-9-]+)$/);
    if (match) blockers.push(match[1]);
  }
  return blockers;
}

function parseVerifySteps(workflow) {
  const lines = workflow.split(/\r?\n/);
  const verifyIndex = lines.findIndex((line) => /^  verify:\s*$/.test(line));
  if (verifyIndex < 0) return { steps: [], verifyFound: false, stepsFound: false, jobIfFound: false };
  const nextJobIndex = lines.findIndex(
    (line, index) => index > verifyIndex && /^  [A-Za-z0-9_-]+:\s*(?:#.*)?$/.test(line),
  );
  const verifyEnd = nextJobIndex < 0 ? lines.length : nextJobIndex;
  const jobIfFound = lines
    .slice(verifyIndex + 1, verifyEnd)
    .some((line) => /^    (?:if|"if"|'if')\s*:/.test(line));
  const stepsIndex = lines.findIndex(
    (line, index) => index > verifyIndex && index < verifyEnd && /^    steps:\s*$/.test(line),
  );
  if (stepsIndex < 0) return { steps: [], verifyFound: true, stepsFound: false, jobIfFound };

  const steps = [];
  let step = null;
  for (let index = stepsIndex + 1; index < verifyEnd; index += 1) {
    const line = lines[index];
    if (/^      -\s+/.test(line)) {
      if (step) steps.push(step);
      step = { lines: [line] };
    } else if (step) {
      step.lines.push(line);
    }
  }
  if (step) steps.push(step);

  return {
    verifyFound: true,
    stepsFound: true,
    jobIfFound,
    steps: steps.map((entry) => {
    const activeLines = entry.lines.filter((line) => !/^\s*#/.test(line));
    const name = activeLines.map((line) => line.match(/^\s*(?:-\s+)?name:\s*(.*)$/)?.[1]).find(Boolean) ?? null;
    const run = activeLines.map((line) => line.match(/^\s*(?:-\s+)?run:\s*(.*)$/)?.[1]).find(Boolean) ?? null;
    return { activeLines, name, run };
    }),
  };
}

function parseSotCiRowCount(text) {
  const section = text.match(/^### CI\([^\n]*\)[^\n]*\n([\s\S]*?)(?=^### |^## |\Z)/m)?.[1] ?? "";
  return (section.match(/^\|\s*\d+\s*\|/gm) ?? []).length;
}

function dependencyCycleCount(graph) {
  const state = new Map();
  let cycles = 0;
  const visit = (id) => {
    if (state.get(id) === "visiting") {
      cycles += 1;
      return;
    }
    if (state.get(id) === "visited") return;
    state.set(id, "visiting");
    for (const dependency of graph.get(id) ?? []) {
      if (graph.has(dependency)) visit(dependency);
    }
    state.set(id, "visited");
  };
  for (const id of graph.keys()) visit(id);
  return cycles;
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


function loadBundle(root, errors) {
  const files = {};
  for (const [key, relativePath] of Object.entries(relativePaths)) {
    files[key] = read(root, relativePath);
    if (files[key] === null) {
      errors.push(`missing file: ${relativePath}`);
      files[key] = "";
    }
  }
  if (sha256(files.contract) !== expectedContractSha256) {
    errors.push("structural contract SHA-256 does not match the pinned checker contract");
  }
  let contract = null;
  try {
    contract = JSON.parse(files.contract);
  } catch {
    errors.push("structural contract must be valid JSON");
  }
  contract ??= {
    activeMicroIds: [], blockers: [], dependencyGraph: {}, phase0Rows: [],
    replacementGoal: { parentAcIds: [], requiredAnchors: [] }, ci: {},
  };
  if (contract.schemaVersion !== "admin-phase0-plan-structural-contract/v1") {
    errors.push("structural contract schemaVersion mismatch");
  }
  if (contract.pinnedBaseSha !== "7c038bea1025937ff34b5161320d74e9468ac089") {
    errors.push("structural contract pinnedBaseSha mismatch");
  }
  if (contract.semanticAuditRequired !== true) {
    errors.push("structural contract must preserve semanticAuditRequired=true");
  }
  if (contract.executionPermission !== false) {
    errors.push("structural contract must preserve executionPermission=false");
  }
  return { files, contract };
}

function validateReplacementGoal(text, contract, errors) {
  const anchors = contract.replacementGoal?.requiredAnchors ?? [];
  for (const anchor of anchors) {
    if (text.includes(anchor)) continue;
    if (anchor.includes("engines.node")) errors.push("replacement goal must require engines.node");
    else if (anchor.includes("Phase 0")) errors.push("replacement goal must define the Phase 0 boundary");
    else errors.push("replacement goal must preserve the Phase 0 exit contract");
  }
  if (anchors.length !== 3) errors.push(`replacement goal anchor count must be 3, got ${anchors.length}`);
  const section = text.match(/^## 20\. 기계 인수 기준\s*$([\s\S]*?)(?=^## 21\.)/m)?.[1] ?? "";
  const matches = [...section.matchAll(/^\d+\. (AC-\d{2}):/gm)].map((match) => match[1]);
  const distinct = sorted(new Set(matches));
  const expected = contract.replacementGoal?.parentAcIds ?? [];
  if (matches.length !== distinct.length) {
    errors.push("replacement goal parent AC IDs must not contain duplicates");
  }
  if (!sameMembers(distinct, expected) || distinct.length !== 40) {
    errors.push(`replacement goal parent AC set mismatch: expected=40 actual=${distinct.length}`);
  }
}

function collectPhaseRows(text, errors) {
  const parsed = parsePhaseRows(text);
  for (const field of parsed.duplicateFields) errors.push(`duplicate phase field: ${field}`);
  for (const field of parsed.unexpectedFields) errors.push(`unexpected phase field: ${field}`);
  const rowById = new Map();
  for (const row of parsed.rows) {
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
  if (parsed.rows.length !== 26) errors.push(`phase0 row count must be 26, got ${parsed.rows.length}`);
  if (parsed.rows.length === 0) errors.push("phase0 row target count must be greater than 0");
  return { rows: parsed.rows, rowById };
}

function validatePinnedPhaseRows(rowById, errors) {
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
  if (rowById.has("P0-04-root-private-workspace")) errors.push("superseded combined P0-04 row must not remain active");
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
}

function validatePhaseContract(rowById, contract, errors) {
  const expectedRows = new Map((contract.phase0Rows ?? []).map((row) => [row.micro_id, row]));
  if (expectedRows.size !== 26) {
    errors.push(`structural contract phase0 row count must be 26, got ${expectedRows.size}`);
  }
  for (const [microId, expectedRow] of expectedRows) {
    const actualRow = rowById.get(microId);
    if (!actualRow) continue;
    for (const field of requiredFields) {
      if (actualRow[field] !== expectedRow[field]) errors.push(`phase contract mismatch: ${microId}.${field}`);
    }
  }
  const unexpected = sorted([...rowById.keys()].filter((id) => !expectedRows.has(id)));
  if (unexpected.length > 0) errors.push(`unexpected Phase 0 micro IDs: ${formatList(unexpected)}`);
}

function validateDependencyEdges(graph, rowById, contract, errors) {
  if (graph.size !== 135) errors.push(`active dependency consumer count must be 135, got ${graph.size}`);
  if (graph.size === 0) errors.push("active dependency consumer target count must be greater than 0");
  for (const id of rowById.keys()) {
    if (!graph.has(id)) errors.push(`phase micro missing from dependency graph: ${id}`);
  }
  const activeIds = contract.activeMicroIds ?? [];
  if (activeIds.length === 0) errors.push("canonical active micro target count must be greater than 0");
  if (new Set(activeIds).size !== activeIds.length) errors.push("canonical active micro IDs must not contain duplicates");
  const activeSet = new Set(activeIds);
  const missing = sorted(activeIds.filter((id) => !graph.has(id)));
  const unexpected = sorted([...graph.keys()].filter((id) => !activeSet.has(id)));
  if (missing.length > 0 || unexpected.length > 0) {
    errors.push(`active micro set mismatch: missing=${formatList(missing)} unexpected=${formatList(unexpected)}`);
  }
  const unknown = [];
  for (const [consumer, dependencies] of graph) {
    for (const dependency of dependencies) {
      if (!activeSet.has(dependency)) unknown.push(`${consumer}->${dependency}`);
    }
  }
  if (unknown.length > 0) errors.push(`unknown dependencies: ${formatList(sorted(unknown))}`);
  const expectedGraph = contract.dependencyGraph ?? {};
  if (Object.keys(expectedGraph).length !== 135) {
    errors.push(`structural contract dependency consumer count must be 135, got ${Object.keys(expectedGraph).length}`);
  }
  for (const consumer of activeIds) {
    const actual = graph.get(consumer) ?? [];
    const expected = expectedGraph[consumer]?.requires_micro_ids ?? [];
    if (!sameMembers(actual, expected)) {
      errors.push(`${consumer} dependencies must be ${formatList(expected)}, got ${formatList(actual)}`);
    }
  }
  return unknown;
}

function validateBlockerEdges(blockerGraph, contract, dependencyText, errors) {
  const blockers = parseBlockerDeclarations(dependencyText);
  const blockerSet = new Set(blockers);
  const expected = contract.blockers ?? [];
  const duplicates = sorted(new Set(blockers.filter((value, index) => blockers.indexOf(value) !== index)));
  for (const blocker of duplicates) errors.push(`duplicate blocker declaration: ${blocker}`);
  const missing = sorted(expected.filter((blocker) => !blockerSet.has(blocker)));
  const unexpected = sorted(blockers.filter((blocker) => !expected.includes(blocker)));
  if (missing.length > 0) errors.push(`required blockers missing: ${formatList(missing)}`);
  if (unexpected.length > 0) errors.push(`unknown blocker declarations: ${formatList(unexpected)}`);
  if (blockers.length === 0) errors.push("canonical blocker target count must be greater than 0");
  const referenced = new Set();
  const unknown = [];
  for (const [consumer, consumerBlockers] of blockerGraph) {
    for (const blocker of consumerBlockers) {
      referenced.add(blocker);
      if (!blockerSet.has(blocker)) unknown.push(`${consumer}->${blocker}`);
    }
  }
  if (unknown.length > 0) errors.push(`unknown blocker dependencies: ${formatList(sorted(unknown))}`);
  const unused = sorted(blockers.filter((blocker) => !referenced.has(blocker)));
  if (unused.length > 0) errors.push(`unused blockers: ${formatList(unused)}`);
  for (const consumer of contract.activeMicroIds ?? []) {
    const actual = blockerGraph.get(consumer) ?? [];
    const wanted = contract.dependencyGraph?.[consumer]?.requires_blocker_ids ?? [];
    if (!sameMembers(actual, wanted)) {
      errors.push(`${consumer} blockers must be ${formatList(wanted)}, got ${formatList(actual)}`);
    }
  }
  return unknown.length + unexpected.length;
}

function validateGraph(files, rowById, contract, errors) {
  const parsed = parseDependencyGraph(files.dependencies, errors);
  for (const consumer of sorted(new Set(parsed.duplicateConsumers))) {
    errors.push(`duplicate dependency consumer: ${consumer}`);
  }
  for (const edge of sorted(new Set(parsed.duplicateMicroDependencies))) {
    errors.push(`duplicate micro dependency: ${edge}`);
  }
  for (const edge of sorted(new Set(parsed.duplicateBlockerDependencies))) {
    errors.push(`duplicate blocker dependency: ${edge}`);
  }
  const unknownDependencies = validateDependencyEdges(parsed.graph, rowById, contract, errors);
  const blockersUnknown = validateBlockerEdges(parsed.blockerGraph, contract, files.dependencies, errors);
  const dependencyCycles = dependencyCycleCount(parsed.graph);
  if (dependencyCycles > 0) errors.push(`dependency cycles detected: ${dependencyCycles}`);
  return {
    graph: parsed.graph,
    duplicateConsumers: parsed.duplicateConsumers.length,
    unknownDependencies: unknownDependencies.length,
    dependencyCycles,
    blockersUnknown,
  };
}

function validateEvidenceBindings(files, errors) {
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
  const auditHash = files.invalidation.match(/invalidated_audit_sha256:\s*([a-f0-9]{64})/)?.[1];
  if (auditHash !== sha256(files.oldAudit)) {
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
}

function validateCi(files, contract, errors) {
  const parsed = parseVerifySteps(files.workflow);
  const { steps } = parsed;
  const activeWorkflowLines = files.workflow.split(/\r?\n/).filter((line) => !/^\s*#/.test(line));
  if (!parsed.verifyFound) errors.push("CI workflow must define jobs.verify");
  if (!parsed.stepsFound) errors.push("CI verify job must contain steps");
  if (parsed.jobIfFound) errors.push("CI verify job must not contain if");
  if (activeWorkflowLines.some((line) => /(?:^|[\s{,])(?:BASH_ENV|"BASH_ENV"|'BASH_ENV')\s*:/.test(line))) {
    errors.push("CI workflow must not define BASH_ENV");
  }
  const stepName = contract.ci?.phase0StepName;
  const run = contract.ci?.run;
  const candidates = steps.filter((step) => step.name === stepName || step.run === run);
  if (candidates.length === 0) {
    errors.push("CI workflow must include run: bash scripts/acceptance-admin-phase0-plan.sh");
  } else if (candidates.length !== 1) {
    errors.push(`CI Phase 0 plan step count must be 1, got ${candidates.length}`);
  }
  if (candidates.length === 1) {
    const [step] = candidates;
    if (step.name !== stepName || step.run !== run) {
      errors.push("CI workflow must include run: bash scripts/acceptance-admin-phase0-plan.sh");
    }
    if (step.activeLines.some((line) => /^\s*(?:-\s+)?(?:if|"if"|'if')\s*:/.test(line))) {
      errors.push("CI Phase 0 plan step must not contain if");
    }
    if (step.activeLines.some((line) => /^\s*(?:-\s+)?(?:continue-on-error|"continue-on-error"|'continue-on-error')\s*:/.test(line))) {
      errors.push("CI Phase 0 plan step must not contain continue-on-error");
    }
    if (step.activeLines.some((line) => /\|\|\s*true(?:\s|$)/.test(line))) {
      errors.push("CI Phase 0 plan step must not ignore errors with || true");
    }
  }
  const namedCount = steps.filter((step) => step.name !== null).length;
  if (namedCount !== contract.ci?.namedStepCount) {
    errors.push(`CI named step count must be ${contract.ci?.namedStepCount}, got ${namedCount}`);
  }
  const sotCount = parseSotCiRowCount(files.sot);
  if (sotCount !== contract.ci?.namedStepCount) {
    errors.push(`verification SOT CI row count must be ${contract.ci?.namedStepCount}, got ${sotCount}`);
  }
  if (candidates.length === 0) errors.push("CI Phase 0 plan target count must be greater than 0");
  requireIncludes(errors, files.registry, 'id: "admin-phase0-plan-ci"', "mechanism registry");
  requireIncludes(errors, files.registry, 'target: "run: bash scripts/acceptance-admin-phase0-plan.sh"', "mechanism registry");
}

export function validate(root) {
  const errors = [];
  const { files, contract } = loadBundle(root, errors);
  validateReplacementGoal(files.replacementGoal, contract, errors);
  const { rows, rowById } = collectPhaseRows(files.plan, errors);
  validatePinnedPhaseRows(rowById, errors);
  validatePhaseContract(rowById, contract, errors);
  const graphResult = validateGraph(files, rowById, contract, errors);
  validateEvidenceBindings(files, errors);
  validateCi(files, contract, errors);
  return {
    errors,
    phaseRows: rows.length,
    consumers: graphResult.graph.size,
    duplicateConsumers: graphResult.duplicateConsumers,
    unknownDependencies: graphResult.unknownDependencies,
    dependencyCycles: graphResult.dependencyCycles,
    blockersUnknown: graphResult.blockersUnknown,
  };
}
