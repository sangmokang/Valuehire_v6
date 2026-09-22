import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "verify.sh"


class VerifySymlinkScanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.git_env = os.environ.copy()
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            self.git_env.pop(key, None)
        self.patterns = self.repo / ".patterns"
        self.patterns.write_text("SECRET_TOKEN\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.repo, env=self.git_env, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, env=self.git_env, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.repo, env=self.git_env, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_verify(self, scan_source=None):
        env = self.git_env.copy()
        env["SECRET_PATTERNS_FILE"] = str(self.patterns)
        if scan_source is not None:
            env["VERIFY_SCAN_SOURCE"] = scan_source
        return subprocess.run(
            ["bash", str(VERIFY)],
            cwd=self.repo,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def git_add(self, *paths):
        subprocess.run(["git", "add", *paths], cwd=self.repo, env=self.git_env, check=True)

    def test_clean_directory_symlink_passes(self):
        canonical = self.repo / ".agents" / "skills" / "jd"
        canonical.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("clean\n", encoding="utf-8")

        link_parent = self.repo / ".codex" / "skills"
        link_parent.mkdir(parents=True)
        os.symlink("../../.agents/skills/jd", link_parent / "jd")
        self.git_add(".agents/skills/jd/SKILL.md", ".codex/skills/jd")

        result = self.run_verify()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)
        self.assertNotIn("Is a directory", result.stdout + result.stderr)

    def test_directory_symlink_does_not_hide_tracked_canonical_secret(self):
        canonical = self.repo / ".agents" / "skills" / "jd"
        canonical.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("contains SECRET_TOKEN\n", encoding="utf-8")

        link_parent = self.repo / ".codex" / "skills"
        link_parent.mkdir(parents=True)
        os.symlink("../../.agents/skills/jd", link_parent / "jd")
        self.git_add(".agents/skills/jd/SKILL.md", ".codex/skills/jd")

        result = self.run_verify()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(".agents/skills/jd/SKILL.md", result.stdout)
        self.assertNotIn("Is a directory", result.stdout + result.stderr)
        self.assertNotIn(".codex/skills/jd", result.stdout)

    def test_symlink_target_text_is_scanned(self):
        target = self.repo / "safe-target"
        target.write_text("clean\n", encoding="utf-8")
        os.symlink("SECRET_TOKEN-target", self.repo / "tracked-link")
        self.git_add("tracked-link")

        result = self.run_verify()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("tracked-link", result.stdout)

    def test_missing_regular_tracked_file_fails_closed(self):
        missing = self.repo / "tracked.txt"
        missing.write_text("clean\n", encoding="utf-8")
        self.git_add("tracked.txt")
        missing.unlink()

        result = self.run_verify()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("scanner error", result.stdout)
        self.assertIn("tracked file missing/not-a-file/unreadable: tracked.txt", result.stdout)

    def test_index_scan_catches_staged_secret_after_worktree_cleanup(self):
        tracked = self.repo / "tracked.txt"
        tracked.write_text("SECRET_TOKEN\n", encoding="utf-8")
        self.git_add("tracked.txt")
        tracked.write_text("clean\n", encoding="utf-8")

        result = self.run_verify(scan_source="index")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("tracked.txt", result.stdout)


if __name__ == "__main__":
    unittest.main()
