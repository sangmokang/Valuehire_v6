"""Synthetic regression checks for same-run CI execution evidence."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[2]


class ExecutionProofTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True,
                       capture_output=True, text=True)
        tools = self.root / "scripts" / "verify"
        tools.mkdir(parents=True)
        for name in ("run-acceptance.sh", "check-acceptance-markers.sh"):
            source = SOURCE / "scripts" / "verify" / name
            if source.exists():
                shutil.copyfile(source, tools / name)
        self.script = self.root / "verify.sh"
        self.script.write_text('echo "PASS: synthetic check"\necho "CHECKED: 1"\n')
        self.marker_dir = self.root / "markers"
        self.env = dict(os.environ)
        for name in ("ACCEPTANCE_EXPECT_LIST", "GIT_DIR", "GIT_WORK_TREE",
                     "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
            self.env.pop(name, None)
        self.env.update(ACCEPTANCE_MARKER_DIR=str(self.marker_dir),
                        GITHUB_ACTIONS="true", GITHUB_REF="refs/heads/task/synthetic")

    def run_bash(self, *arguments):
        return subprocess.run(["bash", *arguments], cwd=self.root, env=self.env,
                              capture_output=True, text=True, timeout=20)

    def audit(self):
        return self.run_bash("scripts/verify/check-acceptance-markers.sh")

    def test_successful_wrapper_records_executed_script_hash(self):
        result = self.run_bash("scripts/verify/run-acceptance.sh", "verify.sh")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        marker = self.marker_dir / "markers.tsv"
        self.assertTrue(marker.is_file(), "successful execution has no evidence marker")
        expected_hash = hashlib.sha256(self.script.read_bytes()).hexdigest()
        self.assertIn(f"verify.sh\t{expected_hash}", marker.read_text().splitlines())
        audited = self.audit()
        self.assertEqual(audited.returncode, 0, audited.stdout + audited.stderr)

    def test_success_without_execution_cannot_pass_audit(self):
        result = self.run_bash("/dev/null", "verify.sh")
        self.assertEqual(result.returncode, 0, "bypass control must exit successfully")
        audited = self.audit()
        self.assertEqual(audited.returncode, 1, audited.stdout + audited.stderr)
        self.assertIn("FAIL:", audited.stdout)
        self.assertIn("CHECKED: 1", audited.stdout)

    def test_failed_wrapper_does_not_record_success_evidence(self):
        self.script.write_text('echo "PASS: partial synthetic check"\nexit 7\n')
        result = self.run_bash("scripts/verify/run-acceptance.sh", "verify.sh")
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertFalse((self.marker_dir / "markers.tsv").exists())


if __name__ == "__main__":
    unittest.main()
