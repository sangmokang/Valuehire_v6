#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { countJavaScriptWeakening } from "./checkpoint-js-scan.mjs";

let secureLedgerScopes;
let runTrustedSecretScan;

async function loadSecurePolicy() {
  ({ secureLedgerScopes } = await import("./checkpoint-policy.mjs"));
  ({ runTrustedSecretScan } = await import("./checkpoint-secrets.mjs"));
}

const CHECKS = {
  INPUT: "input",
  SCOPE: "scope",
  LEAKS: "secrets",
  TEST_WEAKENING: "test-weakening",
  SIZE_LIMIT: "size-limit",
};

function parseArgs(argv) {
  const args = {
    base: null,
    json: false,
    scopes: [],
    runId: null,
    wuId: null,
    secretPatternSha256: null,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") {
      args.json = true;
    } else if (arg === "--base") {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error("--base requires a value");
      args.base = value;
      index += 1;
    } else if (arg === "--scope") {
      const scope = argv[index + 1];
      if (!scope || scope.startsWith("--")) throw new Error("--scope requires a value");
      args.scopes.push(scope);
      index += 1;
    } else if (arg === "--run-id") {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error("--run-id requires a value");
      args.runId = value;
      index += 1;
    } else if (arg === "--wu-id") {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error("--wu-id requires a value");
      args.wuId = value;
      index += 1;
    } else if (arg === "--secret-pattern-sha256") {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error("--secret-pattern-sha256 requires a value");
      args.secretPatternSha256 = value;
      index += 1;
    } else {
      throw new Error(`unknown argument: ${arg}`);
    }
  }
  return args;
}

function git(args, options = {}) {
  const result = spawnSync("git", args, {
    encoding: options.encoding ?? "utf8",
    env: process.env,
    maxBuffer: 16 * 1024 * 1024,
  });
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || `git ${args.join(" ")} failed`).trim();
    throw new Error(detail);
  }
  return result.stdout;
}

function splitZ(output) {
  return output.split("\0").filter((part) => part.length > 0);
}

function stagedChanges(base) {
  const parts = splitZ(git(["diff", "--cached", "--name-status", "-z", base, "--"]));
  const changes = [];
  for (let index = 0; index < parts.length; index += 1) {
    const status = parts[index];
    if (/^[RC]/.test(status)) {
      changes.push({ status: status[0], oldPath: parts[++index], path: parts[++index] });
    } else {
      changes.push({ status: status[0], oldPath: null, path: parts[++index] });
    }
  }
  return changes;
}

function stagedPathsForPolicy(changes) {
  const paths = [];
  for (const change of changes) {
    if (change.oldPath) paths.push(change.oldPath);
    if (change.path) paths.push(change.path);
  }
  return [...new Set(paths)];
}

function readIndex(path) {
  return git(["show", `:${path}`]);
}

function readBase(base, path) {
  return git(["show", `${base}:${path}`]);
}

function escapeRegex(text) {
  return text.replace(/[|\\{}()[\]^$+*?.]/g, "\\$&");
}

function globToRegex(glob) {
  let source = "^";
  for (let index = 0; index < glob.length; index += 1) {
    const char = glob[index];
    if (char === "*") {
      if (glob[index + 1] === "*") {
        index += 1;
        if (glob[index + 1] === "/") {
          index += 1;
          source += "(?:.*/)?";
        } else {
          source += ".*";
        }
      } else {
        source += "[^/]*";
      }
    } else if (char === "?") {
      source += "[^/]";
    } else {
      source += escapeRegex(char);
    }
  }
  return new RegExp(`${source}$`);
}

function matchesAny(path, scopes) {
  return scopes.some((scope) => globToRegex(scope).test(path));
}

function checkScope(changes, fallbackScopes, authority) {
  const violations = [];
  if (changes.length === 0) {
    return [{ check: CHECKS.SCOPE, file: "", detail: "zero staged targets are not checkpoint evidence" }];
  }
  let scopes;
  try {
    if (authority.runId) {
      scopes = secureLedgerScopes({
        runId: authority.runId,
        wuId: authority.wuId,
        cliScopes: fallbackScopes,
        readIndex,
      }).scopes;
    } else scopes = fallbackScopes;
    if (scopes.length === 0) {
      return stagedPathsForPolicy(changes).map((file) => ({
          check: CHECKS.SCOPE,
          file,
          detail: "run ledger scope not found and --scope was not provided",
      }));
    }
  } catch (error) {
    return [{ check: CHECKS.SCOPE, file: ".strict/run-ledger", detail: error.message }];
  }
  for (const file of stagedPathsForPolicy(changes)) {
    if (!matchesAny(file, scopes)) {
      violations.push({
        check: CHECKS.SCOPE,
        file,
        detail: `staged file is outside declared scope: ${scopes.join(", ")}`,
      });
    }
  }
  return violations;
}

function parseScannerFiles(output, stagedFiles) {
  const files = new Set();
  for (const line of output.split(/\r?\n/)) {
    const match = line.match(/^\s*-\s+(.+)$/);
    if (match) files.add(match[1].trim());
  }
  if (files.size === 0) {
    for (const file of stagedFiles) files.add(file);
  }
  return [...files].filter((file) => stagedFiles.has(file));
}

function checkSecrets(changes, authority) {
  const stagedFiles = new Set(changes.filter((change) => change.status !== "D").map((change) => change.path));
  let result;
  try {
    result = runTrustedSecretScan({
      readIndex,
      localPatternSha256: authority.secretPatternSha256,
    });
  } catch (error) {
    return ([...stagedFiles].length > 0 ? [...stagedFiles] : [""]).map((file) => ({
      check: CHECKS.LEAKS,
      file,
      detail: error.message,
    }));
  }
  if (result.status === 0) return [];
  const output = `${result.stdout}\n${result.stderr}`;
  const files = parseScannerFiles(output, stagedFiles);
  return (files.length > 0 ? files : [""]).map((file) => ({
    check: CHECKS.LEAKS,
    file,
    detail: `trusted repository secret scanner failed with exit ${result.status}`,
  }));
}

function normalizeExtension(path) {
  return path.replace(/\.[^./]+$/, (extension) => extension.toLowerCase());
}

function isTestFile(path) {
  path = normalizeExtension(path);
  return (
    /(^|\/)(tests?|__tests__)\/.*\.(?:[cm]?[jt]sx?|py|sh|bash|zsh)$/.test(path) ||
    /\.(?:test|spec)\.[cm]?[jt]sx?$/.test(path) ||
    /(^|\/)test_[^/]+\.py$/.test(path) ||
    /(^|\/)[^/]+_test\.py$/.test(path) ||
    /^scripts\/acceptance-[^/]+\.sh$/.test(path)
  );
}

function stripLineComments(content, path) {
  return content
    .split(/\r?\n/)
    .map((line) => {
      if (/\.(?:py|sh|bash|zsh)$/.test(path)) return line.replace(/(^|\s)#.*$/, "");
      return line.replace(/(^|\s)\/\/.*$/, "");
    })
    .join("\n");
}

function countWeakeningMarkersForFile(path, content) {
  path = normalizeExtension(path);
  const isJavaScript = /\.[cm]?[jt]sx?$/.test(path);
  const stripped = isJavaScript ? content : stripLineComments(content, path);
  const counts = isJavaScript
    ? countJavaScriptWeakening(stripped)
    : { skip: 0, only: 0, todo: 0, assertions: 0 };
  if (/\.py$/.test(path)) {
    counts.skip +=
      (stripped.match(/@(?:pytest\.mark\.)?skip(?:if)?\b/g) ?? []).length +
      (stripped.match(/\bpytest\.skip\s*\(/g) ?? []).length +
      (stripped.match(/@unittest\.skip(?:If|Unless)?\b/g) ?? []).length;
    counts.assertions +=
      (stripped.match(/^\s*assert\b/gm) ?? []).length +
      (stripped.match(/\bself\.assert[A-Za-z_]*\s*\(/g) ?? []).length;
  }
  if (/\.(?:sh|bash|zsh)$/.test(path)) {
    counts.assertions +=
      (stripped.match(/^\s*(?:test|\[\[?)(?:\s|$)/gm) ?? []).length +
      (stripped.match(/\bgrep\s+(?:-[A-Za-z]*q[A-Za-z]*|-[A-Za-z]+\s+-q|-q)\b/g) ?? []).length +
      (stripped.match(/^\s*assert_[A-Za-z0-9_]+\b/gm) ?? []).length;
  }
  return counts;
}

function compareTestStrength(base, basePath, currentPath, currentContent) {
  const before = basePath
    ? countWeakeningMarkersForFile(basePath, readBase(base, basePath))
    : countJavaScriptWeakening("");
  const after = countWeakeningMarkersForFile(currentPath, currentContent);
  const details = [];
  for (const marker of ["skip", "only", "todo"]) {
    if (after[marker] > before[marker]) {
      details.push(`${marker} increased ${before[marker]} -> ${after[marker]}`);
    }
  }
  if (after.assertions < before.assertions) {
    details.push(`assertions decreased ${before.assertions} -> ${after.assertions}`);
  }
  return details;
}

function checkTestWeakening(base, changes) {
  const violations = [];
  for (const change of changes) {
    const paths = [change.oldPath, change.path].filter(Boolean);
    if (!paths.some(isTestFile)) continue;
    if (change.oldPath && isTestFile(change.oldPath) && !isTestFile(change.path)) {
      violations.push({
        check: CHECKS.TEST_WEAKENING,
        file: change.oldPath,
        detail: "test file rename to non-test path is not allowed",
      });
      continue;
    }
    if (change.status === "D") {
      violations.push({
        check: CHECKS.TEST_WEAKENING,
        file: change.path,
        detail: "test file deletion is not allowed",
      });
      continue;
    }
    const basePath = change.oldPath ?? change.path;
    let details;
    try {
      details = compareTestStrength(
        base,
        change.status === "A" ? null : basePath,
        change.path,
        readIndex(change.path),
      );
    } catch (error) {
      violations.push({ check: CHECKS.TEST_WEAKENING, file: change.path, detail: error.message });
      continue;
    }
    if (details.length > 0) {
      violations.push({
        check: CHECKS.TEST_WEAKENING,
        file: change.path,
        detail: details.join("; "),
      });
    }
  }
  return violations;
}

function parseHardLimit() {
  const fallback = 500;
  const sotPath = "docs/sot/coding-principles.md";
  if (splitZ(git(["ls-files", "-z", "--", sotPath])).length === 0) return fallback;
  const text = readIndex(sotPath);
  const p11 = text.match(/P11[\s\S]*?(?=\n\| \*\*P\d+|\n### |\n## |$)/);
  if (!p11) return fallback;
  const haystack = p11[0];
  const patterns = [
    /hard\s+(\d+)\s*(?:LOC|lines?|줄)?/i,
    /hard\s*[:=]\s*(\d+)/i,
    /하드\s*(?:한도|제한)?\s*(\d+)/i,
  ];
  for (const pattern of patterns) {
    const match = haystack.match(pattern);
    if (match) return Number.parseInt(match[1], 10);
  }
  return fallback;
}

function isSizeCheckedCode(path) {
  path = normalizeExtension(path);
  if (/(^|\/)(node_modules|vendor|vendors|dist|build|coverage|fixtures?|migrations?|artifacts?|private-reviews)\//.test(path)) {
    return false;
  }
  return /\.(?:mjs|cjs|js|jsx|ts|tsx|py|rb|go|rs|java|kt|swift|php|cs|sh|bash|zsh)$/.test(path);
}

function loc(content) {
  if (content.length === 0) return 0;
  return content.endsWith("\n") ? content.split("\n").length - 1 : content.split("\n").length;
}

function checkSizeLimit(changes) {
  let hardLimit;
  try {
    hardLimit = parseHardLimit();
  } catch (error) {
    return [
      {
        check: CHECKS.SIZE_LIMIT,
        file: "docs/sot/coding-principles.md",
        detail: error.message,
      },
    ];
  }
  const violations = [];
  for (const change of changes) {
    if (change.status === "D" || !isSizeCheckedCode(change.path)) continue;
    const lines = loc(readIndex(change.path));
    if (lines > hardLimit) {
      violations.push({
        check: CHECKS.SIZE_LIMIT,
        file: change.path,
        detail: `file has ${lines} LOC, hard limit is ${hardLimit}`,
      });
    }
  }
  return violations;
}

function runCheck(check, file, callback) {
  try {
    return callback();
  } catch (error) {
    return [{ check, file, detail: error.message }];
  }
}

function emit(result, json) {
  if (json) {
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } else if (result.pass) {
    process.stdout.write("PASS checkpoint gate\n");
  } else {
    for (const violation of result.violations) {
      process.stdout.write(`${violation.check}: ${violation.file} ${violation.detail}\n`);
    }
  }
}

async function main() {
  let args;
  const violations = [];
  try {
    args = parseArgs(process.argv.slice(2));
    process.chdir(git(["rev-parse", "--show-toplevel"]).trim());
    if (!args.base) {
      violations.push({ check: CHECKS.INPUT, file: "", detail: "--base is required" });
    } else {
      git(["rev-parse", "--verify", `${args.base}^{commit}`]);
      await loadSecurePolicy();
    }
  } catch (error) {
    violations.push({ check: CHECKS.INPUT, file: "", detail: error.message });
    args ??= {
      json: process.argv.includes("--json"),
      scopes: [],
      runId: null,
      wuId: null,
      secretPatternSha256: null,
    };
  }

  if (violations.length === 0) {
    let changes;
    try {
      changes = stagedChanges(args.base);
    } catch (error) {
      violations.push({ check: CHECKS.INPUT, file: "", detail: `cannot read staged diff: ${error.message}` });
    }
    if (violations.length === 0) {
      violations.push(
        ...runCheck(CHECKS.SCOPE, ".strict/run-ledger", () => checkScope(changes, args.scopes, args)),
        ...runCheck(CHECKS.LEAKS, "", () => checkSecrets(changes, args)),
        ...runCheck(CHECKS.TEST_WEAKENING, "", () => checkTestWeakening(args.base, changes)),
        ...runCheck(CHECKS.SIZE_LIMIT, "docs/sot/coding-principles.md", () => checkSizeLimit(changes)),
      );
    }
  }

  const result = { pass: violations.length === 0, violations };
  emit(result, args?.json ?? process.argv.includes("--json"));
  process.exit(result.pass ? 0 : 1);
}

await main();
