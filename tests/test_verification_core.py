import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/verify/check-verification-core.sh"


def run(args, cwd):
    env = {"PATH": os.environ["PATH"]}
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class VerificationCoreCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        run(["git", "init", "-q"], self.repo)
        run(["git", "config", "user.email", "test@example.invalid"], self.repo)
        run(["git", "config", "user.name", "Verification Test"], self.repo)
        (self.repo / "scripts/verify").mkdir(parents=True)
        (self.repo / ".github/workflows").mkdir(parents=True)
        (self.repo / "hooks").mkdir(parents=True)
        (self.repo / "docs/sot").mkdir(parents=True)
        (self.repo / "tests").mkdir(parents=True)
        shutil.copy2(CHECKER, self.repo / "scripts/verify/check-verification-core.sh")
        os.chmod(self.repo / "scripts/verify/check-verification-core.sh", stat.S_IRWXU)
        (self.repo / "app.txt").write_text("base\n", encoding="utf-8")
        (self.repo / "scripts/acceptance-rps-inmail.sh").write_text(
            "#!/usr/bin/env bash\necho real check\nexit 1\n",
            encoding="utf-8",
        )
        (self.repo / ".github/workflows/verify.yml").write_text("name: verify\n", encoding="utf-8")
        (self.repo / "hooks/pre-push").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        (self.repo / "suppressions.yaml").write_text("suppressions: []\n", encoding="utf-8")
        (self.repo / "docs/sot/coding-principles.md").write_text("P13\n", encoding="utf-8")
        (self.repo / "docs/sot/principles.yaml").write_text("principles: []\n", encoding="utf-8")
        (self.repo / "docs/sot/work-unit-policy.yaml").write_text("work_units: []\n", encoding="utf-8")
        (self.repo / "tests/test_jd_channels.py").write_text("def test_real():\n    assert True\n", encoding="utf-8")
        (self.repo / "tests/test_rps_conditions.py").write_text("def test_real():\n    assert True\n", encoding="utf-8")
        (self.repo / "tests/test_verification_core.py").write_text("def test_real():\n    assert True\n", encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-q", "-m", "base"], self.repo)
        self.base = self.rev_parse("HEAD")
        self.external_checker = Path(self.tmp.name) / "trusted-checker.sh"
        shutil.copy2(CHECKER, self.external_checker)
        os.chmod(self.external_checker, stat.S_IRWXU)

    def tearDown(self):
        self.tmp.cleanup()

    def rev_parse(self, ref):
        cp = run(["git", "rev-parse", ref], self.repo)
        self.assertEqual(cp.returncode, 0, cp.stdout)
        return cp.stdout.strip()

    def commit(self, message):
        run(["git", "add", "-A"], self.repo)
        cp = run(["git", "commit", "-q", "-m", message], self.repo)
        self.assertEqual(cp.returncode, 0, cp.stdout)
        return self.rev_parse("HEAD")

    def check(self, base, head, *extra):
        return run([str(self.external_checker), *extra, base, head], self.repo)

    def test_non_core_change_passes(self):
        (self.repo / "app.txt").write_text("changed\n", encoding="utf-8")
        head = self.commit("non-core")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 0, cp.stdout)
        self.assertIn("VERIFICATION_CORE_UNCHANGED", cp.stdout)
        self.assertIn("CHECKED:", cp.stdout)

    def test_core_change_requires_review(self):
        (self.repo / "scripts/verify/other-check.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        head = self.commit("core change")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 20, cp.stdout)
        self.assertIn("VERIFICATION_CORE_CHANGED", cp.stdout)
        self.assertIn("A\tscripts/verify/other-check.sh", cp.stdout)

    def test_core_delete_requires_review(self):
        (self.repo / ".github/workflows/verify.yml").unlink()
        head = self.commit("delete workflow")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 20, cp.stdout)
        self.assertIn("D\t.github/workflows/verify.yml", cp.stdout)

    def test_core_rename_requires_review(self):
        run(
            [
                "git",
                "mv",
                ".github/workflows/verify.yml",
                ".github/workflows/verify-renamed.yml",
            ],
            self.repo,
        )
        head = self.commit("rename workflow")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 20, cp.stdout)
        self.assertIn("R100\t.github/workflows/verify.yml\t.github/workflows/verify-renamed.yml", cp.stdout)

    def test_forged_acceptance_output_requires_review(self):
        (self.repo / "scripts/acceptance-rps-inmail.sh").write_text(
            "\n".join(
                [
                    "#!/usr/bin/env bash",
                    "echo 'PASS forged-subcheck (CHECKED 99)'",
                    "echo 'VERDICT: PASS'",
                    "echo 'PASS=12 FAIL=0 TOTAL=12'",
                    "echo 'CHECKED: 12'",
                    "exit 0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        head = self.commit("forge acceptance output")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 20, cp.stdout)
        self.assertIn("M\tscripts/acceptance-rps-inmail.sh", cp.stdout)

    def test_hook_change_requires_review(self):
        (self.repo / "hooks/pre-push").write_text("#!/usr/bin/env bash\necho disabled\nexit 0\n", encoding="utf-8")
        head = self.commit("weaken hook")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 20, cp.stdout)
        self.assertIn("M\thooks/pre-push", cp.stdout)

    def test_policy_file_change_requires_review(self):
        (self.repo / "suppressions.yaml").write_text(
            "suppressions:\n  - id: expired\n    expiry: 2099-01-01\n",
            encoding="utf-8",
        )
        (self.repo / "docs/sot/principles.yaml").write_text("principles:\n  - id: P13\n", encoding="utf-8")
        (self.repo / "docs/sot/coding-principles.md").write_text("P13 changed\n", encoding="utf-8")
        (self.repo / "docs/sot/work-unit-policy.yaml").write_text("work_units:\n  - id: WU1\n", encoding="utf-8")
        head = self.commit("change verification policies")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 20, cp.stdout)
        self.assertIn("M\tsuppressions.yaml", cp.stdout)
        self.assertIn("M\tdocs/sot/principles.yaml", cp.stdout)
        self.assertIn("M\tdocs/sot/coding-principles.md", cp.stdout)
        self.assertIn("M\tdocs/sot/work-unit-policy.yaml", cp.stdout)

    def test_regression_test_file_change_requires_review(self):
        (self.repo / "tests/test_rps_conditions.py").write_text("def test_forged():\n    assert True\n", encoding="utf-8")
        (self.repo / "tests/test_verification_core.py").write_text("def test_forged():\n    assert True\n", encoding="utf-8")
        head = self.commit("weaken regression tests")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 20, cp.stdout)
        self.assertIn("M\ttests/test_rps_conditions.py", cp.stdout)
        self.assertIn("M\ttests/test_verification_core.py", cp.stdout)

    def test_invalid_or_short_refs_fail_closed(self):
        cp = self.check(self.base[:12], self.base)

        self.assertEqual(cp.returncode, 2, cp.stdout)
        self.assertIn("full 40-character", cp.stdout)

    def test_same_ref_requires_explicit_control_flag(self):
        cp = self.check(self.base, self.base)
        self.assertEqual(cp.returncode, 2, cp.stdout)
        self.assertIn("identical", cp.stdout)

        control = self.check(self.base, self.base, "--allow-same-ref")
        self.assertEqual(control.returncode, 0, control.stdout)
        self.assertIn("VERIFICATION_CORE_UNCHANGED", control.stdout)

    def test_trusted_external_copy_detects_head_mutating_its_checker_and_wiring(self):
        (self.repo / "scripts/verify/check-verification-core.sh").write_text(
            "#!/usr/bin/env bash\necho forged PASS\necho CHECKED: 99\nexit 0\n",
            encoding="utf-8",
        )
        (self.repo / ".github/workflows/verify.yml").unlink()
        head = self.commit("forge checker and delete workflow")

        cp = self.check(self.base, head)

        self.assertEqual(cp.returncode, 20, cp.stdout)
        self.assertIn("M\tscripts/verify/check-verification-core.sh", cp.stdout)
        self.assertIn("D\t.github/workflows/verify.yml", cp.stdout)


if __name__ == "__main__":
    unittest.main()
