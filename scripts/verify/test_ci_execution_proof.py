"""Synthetic regression checks for same-run CI execution evidence."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[2]


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ruby/Psych is already the repository's workflow YAML parser.
        parsed = subprocess.run(
            ["ruby", "-rpsych", "-rdate", "-rjson", "-e",
             "puts JSON.generate(Psych.safe_load(File.read(ARGV[0]), "
             "aliases: true, permitted_classes: [Date, Time]))",
             str(SOURCE / ".github/workflows/verify.yml")],
            check=True, capture_output=True, text=True, timeout=20)
        cls.job = json.loads(parsed.stdout)["jobs"]["verify"]

    def test_job_environment_uses_only_available_contexts(self):
        # GitHub's context availability table excludes runner at jobs.<job_id>.env.
        # https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#context-availability
        allowed = {"github", "needs", "strategy", "matrix", "vars", "secrets", "inputs"}
        references = r"\b([A-Za-z_]\w*)(?:\s*\.\s*(?:[A-Za-z_]\w*|\*)|\s*\[[^]]*\])+"
        self.assertEqual(set(re.findall(references, "github.event.repository.name + vars['mail']")),
                         {"github", "vars"})
        for key, value in self.job.get("env", {}).items():
            if not isinstance(value, str):
                continue
            for expression in re.findall(r"\$\{\{(.*?)\}\}", value, re.S):
                expression = re.sub(r"'(?:[^']|'')*'|\"(?:[^\"\\]|\\.)*\"", "", expression)
                contexts = set(re.findall(references, expression))
                self.assertLessEqual(contexts, allowed, f"unavailable job env context in {key}")

    def marker_initialization(self):
        steps = self.job["steps"]
        selected = [(index, step) for index, step in enumerate(steps)
                    if step.get("id") == "acceptance-marker-init"]
        self.assertEqual(len(selected), 1, "one runner-side marker initialization step is required")
        index, step = selected[0]
        first_wrapper = next(i for i, item in enumerate(steps)
                             if "run-acceptance.sh" in item.get("run", ""))
        self.assertLess(index, first_wrapper, "marker environment must exist before any wrapper")
        self.assertNotIn("if", step)
        self.assertFalse(step.get("continue-on-error", False))
        return step["run"]

    def initialize(self, script, root, attempt):
        environment_file = root / f"environment-{attempt}"
        environment_file.touch()
        env = dict(os.environ, RUNNER_TEMP=str(root / "runner temp"),
                   GITHUB_RUN_ID="12345", GITHUB_RUN_ATTEMPT=str(attempt),
                   GITHUB_ENV=str(environment_file))
        result = subprocess.run(["bash", "-eo", "pipefail", "-c", script], env=env,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        exported = dict(line.split("=", 1) for line in environment_file.read_text().splitlines())
        marker = Path(exported["ACCEPTANCE_MARKER_DIR"])
        self.assertEqual(marker, root / "runner temp" / f"acceptance-markers-12345-{attempt}")
        self.assertTrue(marker.is_dir())
        return marker

    def test_runner_initialization_exports_marker_to_following_steps(self):
        script = self.marker_initialization()
        with tempfile.TemporaryDirectory() as temporary:
            self.initialize(script, Path(temporary), 2)

    def test_new_attempt_does_not_reuse_previous_marker_file(self):
        script = self.marker_initialization()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            previous = self.initialize(script, root, 2)
            (previous / "markers.tsv").write_text("stale evidence\n")
            current = self.initialize(script, root, 3)
            self.assertNotEqual(previous, current)
            self.assertFalse((current / "markers.tsv").exists())


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
