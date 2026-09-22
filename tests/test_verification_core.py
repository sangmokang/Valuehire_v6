import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/verify/check-verification-core.sh"
WORKFLOW = ROOT / ".github/workflows/verification-integrity.yml"
REAL_RUN = subprocess.run
REAL_CHECK_OUTPUT = subprocess.check_output


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

    def workflow_main(self):
        lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
        start = next(i for i, line in enumerate(lines) if "python3 - <<'PY'" in line) + 1
        stop = next(i for i in range(start, len(lines)) if lines[i].strip() == "PY")
        block = lines[start:stop]
        indent = min(len(line) - len(line.lstrip(" ")) for line in block if line.strip())
        source = "\n".join(line[indent:] for line in block)
        compile(source, str(WORKFLOW), "exec")
        namespace = {"__name__": "verification_integrity_under_test"}
        exec(source, namespace)
        return namespace["main"]

    def workflow_check(
        self,
        base,
        head,
        *,
        review_decision="REVIEW_REQUIRED",
        policy=None,
        graph_base=None,
        graph_head=None,
        author="author",
        current=None,
        event=None,
        env=None,
    ):
        main = self.workflow_main()
        repo_name = "owner/repo"
        number = 104
        event_doc = event or {
            "number": number,
            "repository": {"full_name": repo_name},
            "pull_request": {
                "base": {"sha": base, "ref": "main", "repo": {"full_name": repo_name}},
                "head": {"sha": head},
            },
        }
        current_doc = current or {
            "state": "open",
            "base": {"sha": base, "ref": "main", "repo": {"full_name": repo_name}},
            "head": {"sha": head},
            "user": {"login": author},
        }
        policy_doc = {
            "requiresApprovingReviews": True,
            "requiredApprovingReviewCount": 1,
            "dismissesStaleReviews": True,
            "requireLastPushApproval": True,
            "isAdminEnforced": True,
        }
        if policy == "__none__":
            policy_doc = None
        elif policy is not None:
            policy_doc.update(policy)
        graphql_doc = {
            "data": {
                "repository": {
                    "pullRequest": {
                        "headRefOid": graph_head or head,
                        "baseRefOid": graph_base or base,
                        "reviewDecision": review_decision,
                        "baseRef": {"branchProtectionRule": policy_doc},
                    }
                }
            }
        }

        event_file = Path(self.tmp.name) / "event.json"
        event_file.write_text(json.dumps(event_doc), encoding="utf-8")

        def fake_output(args, **kwargs):
            if args[:3] == ["gh", "api", "--hostname"]:
                path = args[4]
                if path == "graphql":
                    return json.dumps(graphql_doc)
                if path == f"repos/{repo_name}/pulls/{number}":
                    return json.dumps(current_doc)
                raise AssertionError(f"unexpected gh api path: {path}")
            return REAL_CHECK_OUTPUT(args, **kwargs)

        def fake_run(args, **kwargs):
            if args[:5] == ["git", "fetch", "--quiet", "--no-tags", "--depth=1"]:
                rewritten = [*args]
                rewritten[5] = str(self.repo)
                return REAL_RUN(rewritten, **kwargs)
            if args[:1] == ["bash"] and str(args[1]).endswith("trusted-checker.sh"):
                result = REAL_RUN(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs)
                print(result.stdout, end="")
                return result
            return REAL_RUN(args, **kwargs)

        patch_env = {
            "PATH": os.environ["PATH"],
            "GITHUB_EVENT_NAME": "pull_request_target",
            "GITHUB_EVENT_PATH": str(event_file),
            "GITHUB_REPOSITORY": repo_name,
        }
        if env:
            patch_env.update(env)
        output = io.StringIO()
        with mock.patch.dict(os.environ, patch_env, clear=True), mock.patch(
            "subprocess.check_output", fake_output
        ), mock.patch("subprocess.run", fake_run), contextlib.redirect_stdout(output):
            try:
                rc = main()
            except Exception as exc:  # fail-closed paths are tested as workflow failure.
                rc = getattr(exc, "returncode", 1)
                print(type(exc).__name__ + ": " + str(exc))
        return rc, output.getvalue()

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

    def test_workflow_non_core_change_passes_without_review(self):
        (self.repo / "app.txt").write_text("changed\n", encoding="utf-8")
        head = self.commit("non-core for workflow")

        rc, out = self.workflow_check(self.base, head)

        self.assertEqual(rc, 0, out)
        self.assertIn("TRUSTED_EVENT", out)
        self.assertIn("VERIFICATION_CORE_UNCHANGED", out)

    def test_workflow_normal_core_change_requires_review(self):
        (self.repo / ".github/workflows/verify.yml").write_text("name: verify\n# core edit\n", encoding="utf-8")
        head = self.commit("normal core edit")

        rc, out = self.workflow_check(self.base, head)

        self.assertEqual(rc, 20, out)
        self.assertIn("VERIFICATION_CORE_CHANGED", out)
        self.assertIn("GitHub required review pending", out)

    def test_workflow_helper_removal_requires_review(self):
        (self.repo / ".github/workflows/verify.yml").write_text(
            "name: verify\njobs:\n  verify:\n    steps:\n      - run: echo PASS\n",
            encoding="utf-8",
        )
        head = self.commit("remove local helper call")

        rc, out = self.workflow_check(self.base, head)

        self.assertEqual(rc, 20, out)
        self.assertIn("M\t.github/workflows/verify.yml", out)

    def test_workflow_ignores_attacker_base_override(self):
        (self.repo / "scripts/acceptance-rps-inmail.sh").write_text(
            "#!/usr/bin/env bash\necho 'VERDICT: PASS'\necho 'CHECKED: 12'\nexit 0\n",
            encoding="utf-8",
        )
        head = self.commit("try attacker base override")

        rc, out = self.workflow_check(self.base, head, env={"BASE_SHA": head, "HEAD_SHA": head})

        self.assertEqual(rc, 20, out)
        self.assertIn("M\tscripts/acceptance-rps-inmail.sh", out)

    def test_workflow_rejects_non_main_base(self):
        (self.repo / "app.txt").write_text("changed\n", encoding="utf-8")
        head = self.commit("non-main base event")
        event = {
            "number": 104,
            "repository": {"full_name": "owner/repo"},
            "pull_request": {
                "base": {"sha": self.base, "ref": "dev", "repo": {"full_name": "owner/repo"}},
                "head": {"sha": head},
            },
        }

        rc, out = self.workflow_check(self.base, head, event=event)

        self.assertNotEqual(rc, 0, out)
        self.assertIn("Only the protected main base is trusted", out)

    def test_workflow_detects_combined_checker_acceptance_string_and_wiring_tamper(self):
        (self.repo / "scripts/verify/check-verification-core.sh").write_text(
            "#!/usr/bin/env bash\n"
            "echo 'PASS forged checker'\n"
            "echo 'VERDICT: PASS'\n"
            "echo 'CHECKED: 999'\n"
            "exit 0\n",
            encoding="utf-8",
        )
        (self.repo / "scripts/acceptance-rps-inmail.sh").write_text(
            "#!/usr/bin/env bash\n"
            "echo 'PASS forged acceptance (CHECKED 12)'\n"
            "echo 'VERDICT: PASS'\n"
            "exit 0\n",
            encoding="utf-8",
        )
        (self.repo / ".github/workflows/verify.yml").write_text(
            "name: verify\njobs:\n  verify:\n    steps:\n      - run: echo PASS\n",
            encoding="utf-8",
        )
        (self.repo / ".github/workflows/verification-integrity.yml").write_text(
            "name: verification-integrity\njobs:\n  verification-integrity:\n    steps:\n      - run: echo PASS\n",
            encoding="utf-8",
        )
        head = self.commit("forge all local gates")

        rc, out = self.workflow_check(self.base, head, env={"BASE_SHA": head, "HEAD_SHA": head})

        self.assertEqual(rc, 20, out)
        self.assertIn("VERIFICATION_CORE_CHANGED", out)
        self.assertIn("M\tscripts/verify/check-verification-core.sh", out)
        self.assertIn("M\tscripts/acceptance-rps-inmail.sh", out)
        self.assertIn("M\t.github/workflows/verify.yml", out)
        self.assertIn("A\t.github/workflows/verification-integrity.yml", out)

    def test_workflow_detects_candidate_core_list_shrink(self):
        script = (self.repo / "scripts/verify/check-verification-core.sh").read_text(encoding="utf-8")
        script = script.replace('  "scripts/acceptance-*"\n', "")
        (self.repo / "scripts/verify/check-verification-core.sh").write_text(script, encoding="utf-8")
        (self.repo / "scripts/acceptance-rps-inmail.sh").write_text(
            "#!/usr/bin/env bash\necho forged\nexit 0\n",
            encoding="utf-8",
        )
        head = self.commit("shrink candidate core list")

        rc, out = self.workflow_check(self.base, head)

        self.assertEqual(rc, 20, out)
        self.assertIn("M\tscripts/verify/check-verification-core.sh", out)
        self.assertIn("M\tscripts/acceptance-rps-inmail.sh", out)

    def test_workflow_requires_trusted_base_checker(self):
        run(["git", "rm", "-q", "scripts/verify/check-verification-core.sh"], self.repo)
        base_without_checker = self.commit("remove checker from base")
        (self.repo / "scripts/verify").mkdir(parents=True, exist_ok=True)
        shutil.copy2(CHECKER, self.repo / "scripts/verify/check-verification-core.sh")
        head = self.commit("candidate re-adds checker")

        rc, out = self.workflow_check(base_without_checker, head)

        self.assertNotEqual(rc, 0, out)
        self.assertIn("CalledProcessError", out)

    def test_workflow_fails_when_event_is_stale(self):
        (self.repo / "app.txt").write_text("first\n", encoding="utf-8")
        event_head = self.commit("event head")
        (self.repo / "app.txt").write_text("second\n", encoding="utf-8")
        current_head = self.commit("current head")

        rc, out = self.workflow_check(
            self.base,
            event_head,
            current={"state": "open", "base": {"sha": self.base, "ref": "main",
                                                "repo": {"full_name": "owner/repo"}},
                     "head": {"sha": current_head}, "user": {"login": "author"}},
        )

        self.assertNotEqual(rc, 0, out)
        self.assertIn("PR moved since this event", out)

    def test_workflow_allows_core_change_after_current_native_review_approval(self):
        (self.repo / ".github/workflows/verify.yml").write_text("name: verify\n# reviewed\n", encoding="utf-8")
        head = self.commit("reviewed core change")

        rc, out = self.workflow_check(
            self.base,
            head,
            review_decision="APPROVED",
        )

        self.assertEqual(rc, 0, out)
        self.assertIn("VERIFICATION_CORE_REVIEWED", out)

    def test_workflow_rejects_unapproved_or_untrusted_native_review_state(self):
        (self.repo / ".github/workflows/verify.yml").write_text("name: verify\n# needs review\n", encoding="utf-8")
        head = self.commit("core change review failures")
        old = self.base
        cases = {
            "review-required": {"review_decision": "REVIEW_REQUIRED"},
            "changes-requested": {"review_decision": "CHANGES_REQUESTED"},
            "missing-decision": {"review_decision": None},
            "stale-head": {"review_decision": "APPROVED", "graph_head": old},
            "stale-base": {"review_decision": "APPROVED", "graph_base": head},
            "missing-policy": {"review_decision": "APPROVED", "policy": "__none__"},
            "approval-count-zero": {"review_decision": "APPROVED",
                                    "policy": {"requiredApprovingReviewCount": 0}},
            "stale-reviews-not-dismissed": {"review_decision": "APPROVED",
                                            "policy": {"dismissesStaleReviews": False}},
            "relaxed-last-push-rule": {"review_decision": "APPROVED",
                                       "policy": {"requireLastPushApproval": False}},
        }
        for name, kwargs in cases.items():
            with self.subTest(name=name):
                rc, out = self.workflow_check(self.base, head, **kwargs)
                self.assertEqual(rc, 20, out)
                self.assertIn("GitHub required review pending", out)


if __name__ == "__main__":
    unittest.main()
