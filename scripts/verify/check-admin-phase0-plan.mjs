#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { relativePaths, validate } from "./admin-phase0-plan-structural-contract.mjs";

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

function replaceExactCount(text, from, to, expectedCount) {
  const count = text.split(from).length - 1;
  if (count !== expectedCount) {
    throw new Error(`mutation target count mismatch: expected ${expectedCount}, got ${count}: ${from}`);
  }
  return text.split(from).join(to);
}

function copyBundle(sourceRoot, targetRoot) {
  for (const relativePath of Object.values(relativePaths)) {
    const source = path.join(sourceRoot, relativePath);
    const target = path.join(targetRoot, relativePath);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(source, target);
  }
}

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
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "루트 `package.json`은 존재",
          "`package.json`이 없고",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-registration-removed",
      expected: "CI workflow must include run: bash scripts/acceptance-admin-phase0-plan.sh",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "run: bash scripts/acceptance-admin-phase0-plan.sh",
          "run: echo phase0-plan-check-disabled",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "dependency-skip",
      expected: "P0-03A-node-engine-pin dependencies must be [P0-03-pnpm-version-pin], got [P0-02-node-version-pin]",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.dependencies);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
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
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "overlapping fallback=0",
          "fallback count unchecked",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "artifact-arbitrary-name-contract-removed",
      expected: "P0-04T mutation must include 임의",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.plan);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "임의 이름의 추적 파일",
          "고정 canary 추적 파일",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "unknown-dependency",
      expected: "unknown dependencies: [P0-06-lockfile-resolution->DOES-NOT-EXIST]",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.dependencies);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "  - consumers: [P0-06-lockfile-resolution]\n    requires_micro_ids: [P0-05-admin-exact-package-contract]",
          "  - consumers: [P0-06-lockfile-resolution]\n    requires_micro_ids: [DOES-NOT-EXIST]",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "fake-active-consumer",
      expected: "active micro set mismatch: missing=[AC04-M01] unexpected=[FAKE-MICRO]",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.dependencies);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "  - consumers: [AC04-M01]",
          "  - consumers: [FAKE-MICRO]",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "historical-blocker-removed",
      expected: "required blockers missing: [BLK-HISTORICAL-EVIDENCE-DIFF-CHECK]",
      apply(tempRoot) {
        const planFile = path.join(tempRoot, relativePaths.plan);
        const dependencyFile = path.join(tempRoot, relativePaths.dependencies);
        let plan = fs.readFileSync(planFile, "utf8");
        let dependencies = fs.readFileSync(dependencyFile, "utf8");
        plan = replaceOnce(
          plan,
          "dependencies: [a02a3da, BLK-RUNNER-ONLY-AUDIT-EVIDENCE, BLK-HISTORICAL-EVIDENCE-DIFF-CHECK]",
          "dependencies: [a02a3da, BLK-RUNNER-ONLY-AUDIT-EVIDENCE]",
        );
        dependencies = replaceOnce(dependencies, "  - BLK-HISTORICAL-EVIDENCE-DIFF-CHECK\n", "");
        dependencies = replaceOnce(
          dependencies,
          "requires_blocker_ids: [BLK-RUNNER-ONLY-AUDIT-EVIDENCE, BLK-HISTORICAL-EVIDENCE-DIFF-CHECK]",
          "requires_blocker_ids: [BLK-RUNNER-ONLY-AUDIT-EVIDENCE]",
        );
        fs.writeFileSync(planFile, plan);
        fs.writeFileSync(dependencyFile, dependencies);
      },
    },
    {
      name: "phase-result-gutted",
      expected: "phase contract mismatch: P0-06-lockfile-resolution.single_observable_result",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.plan);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "single_observable_result: 고정 runtime에서 frozen install이 성공하고 lockfile importer/package targetCount가 0보다 크다",
          "single_observable_result: 아무 문장이나 있으면 된다",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-main-only",
      expected: "CI Phase 0 plan step must not contain if",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "      - name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
          "      - name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        if: github.ref == 'refs/heads/main'\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-continue-on-error",
      expected: "CI Phase 0 plan step must not contain continue-on-error",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "        run: bash scripts/acceptance-admin-phase0-plan.sh",
          "        continue-on-error: true\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "replacement-goal-engines-requirement-removed",
      expected: "replacement goal must require engines.node",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.replacementGoal);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "Node는 루트 `.node-version`과 `engines.node`, pnpm은 루트 `packageManager`에 각각 고정한다.",
          "Node는 루트 `.node-version`, pnpm은 루트 `packageManager`에 각각 고정한다.",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "duplicate-phase-field",
      expected: "duplicate phase field: P0-06-lockfile-resolution.single_observable_result",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.plan);
        const value = "  single_observable_result: 고정 runtime에서 frozen install이 성공하고 lockfile importer/package targetCount가 0보다 크다";
        const text = replaceOnce(fs.readFileSync(file, "utf8"), value, `${value}\n${value}`);
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "plan-and-graph-id-renamed-together",
      expected: "active micro set mismatch: missing=[P0-06-lockfile-resolution] unexpected=[P0-06-FAKE-lockfile-resolution]",
      apply(tempRoot) {
        const planFile = path.join(tempRoot, relativePaths.plan);
        const dependencyFile = path.join(tempRoot, relativePaths.dependencies);
        const plan = replaceOnce(
          fs.readFileSync(planFile, "utf8"),
          "  micro_id: P0-06-lockfile-resolution",
          "  micro_id: P0-06-FAKE-lockfile-resolution",
        );
        const dependencies = replaceExactCount(
          fs.readFileSync(dependencyFile, "utf8"),
          "P0-06-lockfile-resolution",
          "P0-06-FAKE-lockfile-resolution",
          2,
        );
        fs.writeFileSync(planFile, plan);
        fs.writeFileSync(dependencyFile, dependencies);
      },
    },
    {
      name: "ci-verify-steps-moved-to-decoy-job",
      expected: "CI verify job must contain steps",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "  verify:\n    runs-on: ubuntu-latest\n    steps:",
          "  verify:\n    runs-on: ubuntu-latest\n\n  decoy:\n    runs-on: ubuntu-latest\n    steps:",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-if-as-first-step-key",
      expected: "CI Phase 0 plan step must not contain if",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "      - name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
          "      - if: github.ref == 'refs/heads/main'\n        name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-continue-on-error-as-first-step-key",
      expected: "CI Phase 0 plan step must not contain continue-on-error",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "      - name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
          "      - continue-on-error: true\n        name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-quoted-if-as-first-step-key",
      expected: "CI Phase 0 plan step must not contain if",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "      - name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
          "      - 'if': github.ref == 'refs/heads/main'\n        name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-quoted-continue-on-error-as-first-step-key",
      expected: "CI Phase 0 plan step must not contain continue-on-error",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "      - name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
          "      - 'continue-on-error': true\n        name: 관리자 대시보드 Phase 0 계획 복구 계약\n        # 요구 누락·비원자 작업·무효 감사 재사용·SOT/CI 미배선을 같은 판정기로 막는다.\n        run: bash scripts/acceptance-admin-phase0-plan.sh",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "duplicate-requires-micro-field",
      expected: "duplicate dependency field: P0-06-lockfile-resolution.requires_micro_ids",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.dependencies);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "  - consumers: [P0-06-lockfile-resolution]\n    requires_micro_ids: [P0-05-admin-exact-package-contract]",
          "  - consumers: [P0-06-lockfile-resolution]\n    requires_micro_ids: [DOES-NOT-EXIST]\n    requires_micro_ids: [P0-05-admin-exact-package-contract]",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "duplicate-requires-blocker-field",
      expected: "duplicate dependency field: P0-02-node-version-pin.requires_blocker_ids",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.dependencies);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "  - consumers: [P0-02-node-version-pin]\n    requires_micro_ids: [P0-01-baseline-and-audited-plan]\n    requires_blocker_ids: [BLK-NODE-RUNTIME-CONSUMER]",
          "  - consumers: [P0-02-node-version-pin]\n    requires_micro_ids: [P0-01-baseline-and-audited-plan]\n    requires_blocker_ids: [BLK-NOT-DEFINED]\n    requires_blocker_ids: [BLK-NODE-RUNTIME-CONSUMER]",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "zero-consumer-dependency-group",
      expected: "dependency group has zero consumers",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.dependencies);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "groups:\n",
          "groups:\n  - consumers: []\n    requires_micro_ids: []\n",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-verify-job-quoted-if-after-unnamed-step",
      expected: "CI verify job must not contain if",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "        run: bash scripts/acceptance-admin-phase0-plan.sh",
          "        run: bash scripts/acceptance-admin-phase0-plan.sh\n\n      - uses: actions/checkout@v4\n    'if': github.event_name == 'workflow_dispatch'",
        );
        fs.writeFileSync(file, text);
      },
    },
    {
      name: "ci-verify-steps-moved-to-commented-decoy-job",
      expected: "CI verify job must contain steps",
      apply(tempRoot) {
        const file = path.join(tempRoot, relativePaths.workflow);
        const text = replaceOnce(
          fs.readFileSync(file, "utf8"),
          "  verify:\n    runs-on: ubuntu-latest\n    steps:",
          "  verify:\n    runs-on: ubuntu-latest\n\n  decoy: # evade job boundary\n    runs-on: ubuntu-latest\n    steps:",
        );
        fs.writeFileSync(file, text);
      },
    },
  ];

function runSelfTest(root) {
  const baseline = validate(root);
  if (baseline.errors.length > 0) return baseline;

  let caught = 0;
  for (const mutation of mutations) {
    const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "admin-phase0-plan-"));
    try {
      copyBundle(root, tempRoot);
      mutation.apply(tempRoot);
      const result = validate(tempRoot);
      if (!result.errors.includes(mutation.expected)) {
        return {
          errors: [`mutation ${mutation.name} was not caught with expected reason: ${mutation.expected}`],
          phaseRows: baseline.phaseRows,
          consumers: baseline.consumers,
          duplicateConsumers: baseline.duplicateConsumers,
          unknownDependencies: baseline.unknownDependencies,
          dependencyCycles: baseline.dependencyCycles,
          blockersUnknown: baseline.blockersUnknown,
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
    duplicateConsumers: baseline.duplicateConsumers,
    unknownDependencies: baseline.unknownDependencies,
    dependencyCycles: baseline.dependencyCycles,
    blockersUnknown: baseline.blockersUnknown,
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
    `ADMIN_PHASE0_PLAN_CHECK phase0Rows=${result.phaseRows ?? 0} consumers=${result.consumers ?? 0} duplicateConsumers=${result.duplicateConsumers ?? 0} unknownDependencies=${result.unknownDependencies ?? 0} dependencyCycles=${result.dependencyCycles ?? 0} blockersUnknown=${result.blockersUnknown ?? 0} mutationsCaught=${result.mutationsCaught ?? 0} mutationsRequired=${result.mutationsRequired ?? 0} structuralContract=FAIL semanticAuditRequired=true executionPermission=false reason=contract-mismatch`,
  );
  process.exit(1);
}

console.log("PASS: Phase 0 structural contract and CI registration match the pinned candidate");
console.log(
  `ADMIN_PHASE0_PLAN_CHECK phase0Rows=${result.phaseRows} consumers=${result.consumers} duplicateConsumers=${result.duplicateConsumers} unknownDependencies=${result.unknownDependencies} dependencyCycles=${result.dependencyCycles} blockersUnknown=${result.blockersUnknown} mutationsCaught=${result.mutationsCaught ?? 0} mutationsRequired=${result.mutationsRequired ?? 0} structuralContract=PASS semanticAuditRequired=true executionPermission=false reason=null`,
);
