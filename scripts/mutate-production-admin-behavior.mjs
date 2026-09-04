#!/usr/bin/env node

import { cpSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const MUTANTS = [
  {
    name: "candidate_route_auth_gate_removed",
    file: "api/admin/candidates/index.js",
    pattern: "    await requireAdmin(req, config);",
    replacement: "    // mutant: authentication gate removed",
    killedBy: "candidate list requires auth and does not hide auth failure as empty list",
  },
  {
    name: "auth_allowlist_bypass",
    file: "server/admin/auth.js",
    pattern: "if (!config.adminEmailHashes.has(hashEmail(body.user.email))) {",
    replacement: "if (false) {",
    killedBy: "login rejects valid non-allowlisted user as AUTH_FORBIDDEN",
  },
  {
    name: "session_local_lifetime_guard_removed",
    file: "server/admin/auth.js",
    pattern: "    enforceLocalLifetime(session.accessToken);",
    replacement: "    // mutant: local 15-minute lifetime guard removed",
    killedBy: "session rejects a valid provider token after the local 15-minute window",
  },
  {
    name: "candidate_list_tenant_filter_removed",
    file: "server/admin/candidates.js",
    pattern: "?tenant_id=eq.${tenant}&select=id,position_id,external_key,display_name,review_status,version,updated_at&order=created_at.asc",
    replacement: "?select=id,position_id,external_key,display_name,review_status,version,updated_at&order=created_at.asc",
    killedBy: "candidate list queries candidates and positions within the configured tenant",
  },
  {
    name: "review_update_version_guard_removed",
    file: "server/admin/candidates.js",
    pattern: "&version=eq.${expectedVersion}&review_status=neq.${nextStatus}&select=id,review_status,version,updated_at",
    replacement: "&review_status=neq.${nextStatus}&select=id,review_status,version,updated_at",
    killedBy: "candidate state update persists by version and reports stale writes",
  },
  {
    name: "review_update_status_guard_removed",
    file: "server/admin/candidates.js",
    pattern: "&review_status=neq.${nextStatus}&select=id,review_status,version,updated_at",
    replacement: "&select=id,review_status,version,updated_at",
    killedBy: "review update rejects an unchanged status without surfacing a dependency error",
  },
  {
    name: "review_update_actor_audit_input_removed",
    file: "server/admin/candidates.js",
    pattern: "        pending_review_actor_email_sha256: actorEmailHash,",
    replacement: "        // mutant: audit actor input removed",
    killedBy: "candidate state update persists by version and reports stale writes",
  },
];

const COPY_PATHS = [
  "api",
  "server",
  "supabase",
  "scripts/check-admin-schema.mjs",
  "tests/production-admin",
  "package.json",
];

function mutateText(source, mutant) {
  if (!source.includes(mutant.pattern)) {
    throw new Error(`${mutant.name}: mutation pattern not found`);
  }
  return source.replace(mutant.pattern, mutant.replacement);
}

function copyHarness(tmpRoot) {
  for (const path of COPY_PATHS) {
    cpSync(path, join(tmpRoot, path), { recursive: true });
  }
}

function runMutant(mutant) {
  const tmpRoot = mkdtempSync(join(tmpdir(), `valuehire-admin-mutant-${mutant.name}-`));
  try {
    copyHarness(tmpRoot);
    const target = join(tmpRoot, mutant.file);
    writeFileSync(target, mutateText(readFileSync(target, "utf8"), mutant));
    return spawnSync(process.execPath, ["--test", "tests/production-admin/server.test.mjs"], {
      cwd: tmpRoot,
      encoding: "utf8",
    });
  } finally {
    rmSync(tmpRoot, { recursive: true, force: true });
  }
}

function escaped(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function runBaseline() {
  const result = spawnSync(process.execPath, ["--test", "tests/production-admin/server.test.mjs"], {
    cwd: process.cwd(),
    encoding: "utf8",
  });
  if (result.status !== 0) {
    process.stdout.write(`VERDICT: FAIL\nBASELINE: FAIL\nMUTANTS: ${MUTANTS.length}\nKILLED: 0\nSURVIVORS: ${MUTANTS.length}\n`);
    process.exit(1);
  }
}

let killed = 0;
const survivors = [];
runBaseline();
for (const mutant of MUTANTS) {
  const result = runMutant(mutant);
  const output = `${result.stdout || ""}\n${result.stderr || ""}`;
  const namedFailure = new RegExp(`not ok \\d+ - ${escaped(mutant.killedBy)}(?:\\n|\\r|$)`).test(output);
  if (result.status !== 0 && namedFailure) {
    killed += 1;
    process.stdout.write(`KILLED ${mutant.name} by "${mutant.killedBy}"\n`);
  } else {
    survivors.push(`${mutant.name}: exit=${result.status} expected="${mutant.killedBy}"`);
  }
}

if (survivors.length > 0) {
  process.stdout.write(`VERDICT: FAIL\nMUTANTS: ${MUTANTS.length}\nKILLED: ${killed}\nSURVIVORS: ${survivors.length}\n${survivors.join("\n")}\n`);
  process.exit(1);
}

process.stdout.write(`VERDICT: PASS\nBASELINE: PASS\nMUTANTS: ${MUTANTS.length}\nKILLED: ${killed}\nSURVIVORS: 0\n`);
