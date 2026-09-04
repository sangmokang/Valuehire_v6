#!/usr/bin/env node

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { spawnSync } from "node:child_process";
import { checkAdminSchemaContract } from "./check-admin-schema.mjs";

const expectedSchemaDigest = "14e3755595b5804f5059dd0a455f0c8a38ef3106d18b53555fa0c56e47868089";
const outputDirectory = "apps/production-admin";
const expectedIgnoreRules = [
  "/*",
  "!api",
  "!api/**",
  "!apps",
  "apps/*",
  "!apps/production-admin",
  "!apps/production-admin/**",
  "apps/production-admin/package.json",
  "!server",
  "server/*",
  "!server/admin",
  "!server/admin/**",
  "!package.json",
  "!package-lock.json",
  "!vercel.json",
];
const publicFiles = [
  "apps/production-admin/index.html",
  "apps/production-admin/styles.css",
  "apps/production-admin/ui.js",
];
const deploymentRoots = ["api", "server/admin"];
const forbidden = /(smtp|sendgrid|twilio|mailgun|resend|sendSms|portal[_-]?send|eyJ[A-Za-z0-9_-]{20,}|sb_secret_[A-Za-z0-9_-]+)/i;

function walk(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) return walk(path);
    return [relative(process.cwd(), path)];
  }).sort();
}

function readText(path) {
  return readFileSync(path, "utf8");
}

function failIf(condition, message) {
  if (condition) throw new Error(message);
}

function gitPaths(args, label) {
  const result = spawnSync("git", args, { encoding: "utf8" });
  failIf(result.status !== 0, `${label} failed`);
  return (result.stdout || "").split(/\r?\n/).filter(Boolean);
}

function verifyChangedFileBudgets() {
  const candidates = new Set([
    ...gitPaths(["diff-tree", "--no-commit-id", "--name-only", "--diff-filter=ACMR", "-r", "-m", "HEAD"], "committed file discovery"),
    ...gitPaths(["diff", "--name-only", "--diff-filter=ACMR", "HEAD"], "working-tree file discovery"),
    ...gitPaths(["diff", "--cached", "--name-only", "--diff-filter=ACMR", "HEAD"], "index file discovery"),
    ...gitPaths(["ls-files", "--others", "--exclude-standard"], "untracked file discovery"),
  ]);
  const files = [...candidates].filter((path) => {
    try {
      return statSync(path).isFile();
    } catch {
      return false;
    }
  }).sort();
  failIf(files.length === 0, "changed-file budget target is empty");
  for (const file of files) {
    const contents = readFileSync(file);
    failIf(contents.includes(0), `changed binary file has no line budget: ${file}`);
    const lineCount = contents.toString("utf8").split(/\r?\n/).length;
    failIf(lineCount > 600, `changed file exceeds 600-line budget: ${file} ${lineCount}`);
  }
  return files.length;
}

function verifyVercelConfig() {
  const config = JSON.parse(readText("vercel.json"));
  failIf(config.outputDirectory !== outputDirectory, `outputDirectory must be ${outputDirectory}`);
  failIf(!Array.isArray(config.rewrites), "vercel rewrites must be explicit");
  failIf(!Array.isArray(config.headers), "vercel headers must be explicit");
  const rewrites = JSON.stringify(config.rewrites).replace(/\s+/g, "");
  for (const fragment of ['"source":"/admin"', '"destination":"/index.html"', '"destination":"/ui.js"', '"destination":"/styles.css"']) {
    failIf(!rewrites.includes(fragment), `missing rewrite fragment ${fragment}`);
  }
  failIf(rewrites.includes("/api/(.*)"), "vercel must not rewrite API routes into static output");
  const globalHeaders = config.headers.find((entry) => entry.source === "/(.*)")?.headers;
  failIf(!Array.isArray(globalHeaders), "global response headers missing");
  const csp = globalHeaders.find((entry) => entry.key === "Content-Security-Policy")?.value || "";
  for (const directive of [
    "default-src 'self'",
    "connect-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "frame-ancestors 'none'",
    "form-action 'self'",
  ]) {
    failIf(!csp.includes(directive), `global CSP directive missing: ${directive}`);
  }
  failIf(/unsafe-inline|unsafe-eval/i.test(csp), "global CSP permits unsafe script or style execution");
  const hsts = globalHeaders.find((entry) => entry.key === "Strict-Transport-Security")?.value;
  failIf(hsts !== "max-age=31536000; includeSubDomains", "global HSTS contract drifted");
}

function verifyVercelIgnore() {
  const actual = readText(".vercelignore").split(/\r?\n/).filter(Boolean);
  failIf(actual.join("\n") !== expectedIgnoreRules.join("\n"), ".vercelignore allowlist drifted");
}

function verifyScannedFile(path) {
  const text = readText(path);
  failIf(forbidden.test(text), `forbidden outbound, PII, or secret literal in ${path}`);
  const lines = text.split(/\r?\n/).length;
  failIf(lines > 600, `file exceeds hard LOC limit: ${path} ${lines}`);
}

try {
  verifyVercelConfig();
  verifyVercelIgnore();
  const budgetFileCount = verifyChangedFileBudgets();

  const outputFiles = walk(outputDirectory).filter((file) => file !== "apps/production-admin/package.json");
  failIf(outputFiles.join(",") !== publicFiles.join(","), `unexpected public output files: ${outputFiles.join(",")}`);
  const files = [
    ...deploymentRoots.flatMap((directory) => walk(directory)),
    ...outputFiles,
    "package-lock.json",
    "package.json",
    "vercel.json",
  ].sort();
  failIf(files.length < 17, `scan target count too low: ${files.length}`);
  for (const file of files) {
    failIf(!statSync(file).isFile(), `not a file: ${file}`);
    verifyScannedFile(file);
  }

  const schema = checkAdminSchemaContract();
  failIf(schema.checkedMigrations !== 6, `expected six migrations, found ${schema.checkedMigrations}`);
  failIf(schema.combinedDigest !== expectedSchemaDigest, `schema digest mismatch: ${schema.combinedDigest}`);
  failIf(!schema.ok, `schema contract failed: ${schema.errors.join("; ")}`);

  process.stdout.write(`VERDICT: PASS\nFILES_SCANNED: ${files.length}\nBUDGET_FILES: ${budgetFileCount}\nPUBLIC_FILES: ${outputFiles.length}\nMIGRATIONS: ${schema.checkedMigrations}\nSCHEMA_DIGEST: ${schema.combinedDigest}\nEXTERNAL_SENDS: 0\n`);
} catch (error) {
  process.stdout.write(`VERDICT: FAIL\nERROR: ${error.message}\nEXTERNAL_SENDS: 0\n`);
  process.exit(1);
}
