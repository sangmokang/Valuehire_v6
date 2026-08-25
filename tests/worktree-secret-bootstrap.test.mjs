import assert from "node:assert/strict";
import {
  chmodSync,
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readlinkSync,
  realpathSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
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
  writeFileSync(path.join(main, ".secret-patterns.default"), "Z9_NEVER_MATCH_[0-9]{9}\n");
  writeFileSync(path.join(main, "README.md"), "fixture\n");
  copyFileSync(path.join(repoRoot, "scripts/install-hooks.sh"), path.join(main, "scripts/install-hooks.sh"));
  chmodSync(path.join(main, "scripts/install-hooks.sh"), 0o755);
  copyFileSync(path.join(repoRoot, "verify.sh"), path.join(main, "verify.sh"));
  chmodSync(path.join(main, "verify.sh"), 0o755);
  const hookSource = path.join(repoRoot, "hooks/post-checkout");
  if (existsSync(hookSource)) {
    copyFileSync(hookSource, path.join(main, "hooks/post-checkout"));
    chmodSync(path.join(main, "hooks/post-checkout"), 0o755);
  }
  if (realSecret) writeFileSync(path.join(main, ".secret-patterns"), "LOCAL_ONLY\n");
  git(main, ["add", ".gitignore", ".secret-patterns.default", "README.md", "hooks", "scripts", "verify.sh"]);
  git(main, ["commit", "-m", "fixture"]);
  return { root, main, linked: path.join(root, "linked") };
}

test("git worktree add automatically links the real main secret and preserves hooksPath", () => {
  const fixture = createFixture({ realSecret: true });
  git(fixture.main, ["worktree", "add", "-b", "task/linked", fixture.linked]);
  const link = path.join(fixture.linked, ".secret-patterns");
  assert.ok(existsSync(link));
  assert.equal(realpathSync(readlinkSync(link)), realpathSync(path.join(fixture.main, ".secret-patterns")));
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

test("a linked worktree with a wrong secret symlink fails closed", () => {
  const fixture = createFixture({ realSecret: true });
  git(fixture.main, ["worktree", "add", "--no-checkout", "-b", "task/wrong-link", fixture.linked]);
  symlinkSync(path.join(fixture.main, "missing-secret"), path.join(fixture.linked, ".secret-patterns"));
  const result = spawnSync("git", ["checkout", "-f"], { cwd: fixture.linked, encoding: "utf8" });
  assert.notEqual(result.status, 0);
});

test("a linked worktree with a regular secret file fails closed", () => {
  const fixture = createFixture({ realSecret: true });
  git(fixture.main, ["worktree", "add", "--no-checkout", "-b", "task/regular-file", fixture.linked]);
  writeFileSync(path.join(fixture.linked, ".secret-patterns"), "WORKTREE_LOCAL\n");
  const result = spawnSync("git", ["checkout", "-f"], { cwd: fixture.linked, encoding: "utf8" });
  assert.notEqual(result.status, 0);
});

test("verify fails closed in a residue worktree when only the default patterns remain", () => {
  const fixture = createFixture({ realSecret: false });
  const add = spawnSync("git", ["worktree", "add", "-b", "task/residue", fixture.linked], {
    cwd: fixture.main,
    encoding: "utf8",
  });
  assert.notEqual(add.status, 0);
  assert.ok(existsSync(path.join(fixture.linked, ".git")));
  const verify = spawnSync("bash", ["verify.sh"], { cwd: fixture.linked, encoding: "utf8" });
  assert.notEqual(verify.status, 0, `${verify.stdout}\n${verify.stderr}`);
  assert.match(`${verify.stdout}\n${verify.stderr}`, /linked worktree.*\.secret-patterns/i);
});

test("a functionally equivalent relative secret symlink is accepted", () => {
  const fixture = createFixture({ realSecret: true });
  git(fixture.main, ["worktree", "add", "--no-checkout", "-b", "task/relative-link", fixture.linked]);
  const expected = path.join(fixture.main, ".secret-patterns");
  symlinkSync(path.relative(fixture.linked, expected), path.join(fixture.linked, ".secret-patterns"));
  git(fixture.linked, ["checkout", "-f"]);
  assert.equal(realpathSync(path.join(fixture.linked, ".secret-patterns")), realpathSync(expected));
});
