import assert from "node:assert/strict";
import { chmodSync, copyFileSync, existsSync, mkdirSync, mkdtempSync, readlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function git(cwd, args, expected = 0) {
  const result = spawnSync("git", args, { cwd, encoding: "utf8" });
  assert.equal(result.status, expected, `git ${args.join(" ")}\n${result.stderr}`);
  return result;
}

function createFixture({ realSecret }) {
  const root = mkdtempSync(path.join(tmpdir(), "valuehire-secret-bootstrap-"));
  const main = path.join(root, "main");
  mkdirSync(path.join(main, "hooks"), { recursive: true });
  mkdirSync(path.join(main, "scripts"), { recursive: true });
  git(root, ["init", "main"]);
  git(main, ["config", "user.name", "Bootstrap Test"]);
  git(main, ["config", "user.email", "bootstrap@example.invalid"]);
  git(main, ["config", "core.hooksPath", "hooks"]);
  writeFileSync(path.join(main, ".gitignore"), ".secret-patterns\n");
  writeFileSync(path.join(main, ".secret-patterns.default"), "DEFAULT_ONLY\n");
  writeFileSync(path.join(main, "README.md"), "fixture\n");
  copyFileSync(path.join(repoRoot, "scripts/install-hooks.sh"), path.join(main, "scripts/install-hooks.sh"));
  chmodSync(path.join(main, "scripts/install-hooks.sh"), 0o755);
  const hookSource = path.join(repoRoot, "hooks/post-checkout");
  if (existsSync(hookSource)) {
    copyFileSync(hookSource, path.join(main, "hooks/post-checkout"));
    chmodSync(path.join(main, "hooks/post-checkout"), 0o755);
  }
  if (realSecret) writeFileSync(path.join(main, ".secret-patterns"), "LOCAL_ONLY\n");
  git(main, ["add", ".gitignore", ".secret-patterns.default", "README.md", "hooks", "scripts"]);
  git(main, ["commit", "-m", "fixture"]);
  return { root, main, linked: path.join(root, "linked") };
}

test("git worktree add automatically links the real main secret and preserves hooksPath", () => {
  const fixture = createFixture({ realSecret: true });
  git(fixture.main, ["worktree", "add", "-b", "task/linked", fixture.linked]);
  const link = path.join(fixture.linked, ".secret-patterns");
  assert.ok(existsSync(link));
  assert.equal(readlinkSync(link), path.join(fixture.main, ".secret-patterns"));
  assert.equal(git(fixture.linked, ["config", "--get", "core.hooksPath"]).stdout.trim(), "hooks");
});

test("missing real secret fails closed and never links the default file", () => {
  const fixture = createFixture({ realSecret: false });
  const result = spawnSync("git", ["worktree", "add", "-b", "task/missing", fixture.linked], {
    cwd: fixture.main,
    encoding: "utf8",
  });
  assert.notEqual(result.status, 0);
  const link = path.join(fixture.linked, ".secret-patterns");
  assert.equal(existsSync(link), false);
});
