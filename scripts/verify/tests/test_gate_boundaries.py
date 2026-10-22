"""Exercise staged hook boundaries without changing the source repository."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ".github/workflows/check.yml"
BASE_WORKFLOW = """name: synthetic
on: push
jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - name: First decision
        run: python3 scripts/first.py
      - name: Independent decisions
        run: |
          node scripts/second.mjs
          node scripts/third.mjs
"""


class GateBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p13-gate-boundary-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.run_git("init", "-q")
        self.run_git("config", "user.email", "synthetic@example.test")
        self.run_git("config", "user.name", "Synthetic gate regression")
        for name in ("hooks/pre-commit", "verify.sh", ".secret-patterns.default",
                     ".check-weakening-patterns", "scripts/acceptance-silent-failure-lint.sh"):
            self.write(name, (ROOT / name).read_text())
        # Copy helper implementations if present, so the same tests cover the repaired hook.
        for name in ("check-workflow-deletion.py", "check-external-effect-graph.py"):
            source = ROOT / "scripts/verify" / name
            if source.is_file():
                self.write("scripts/verify/" + name, source.read_text())
        self.write(WORKFLOW, BASE_WORKFLOW)
        self.write("scripts/first.py", "print('synthetic')\n")
        self.write("scripts/second.mjs", "console.log('synthetic');\n")
        self.write("scripts/third.mjs", "console.log('synthetic');\n")
        self.write(".claude/skills/verify/local-checks.sh", "#!/usr/bin/env bash\nprintf 'synthetic\\n'\n")
        self.write("README.md", "synthetic fixture\nretained note\n")
        self.run_git("add", ".")
        # This fresh fixture has no installed hook; the real hook is invoked explicitly below.
        self.run_git("commit", "-qm", "Synthetic baseline")

    def run_git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def stage(self):
        self.run_git("add", "-A")

    def hook(self):
        self.stage()
        result = subprocess.run(["bash", "hooks/pre-commit"], cwd=self.repo,
                                capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr

    def blocked(self, reason):
        status, output = self.hook()
        self.assertNotEqual(status, 0, output)
        self.assertIn(reason, output, output)

    def allowed(self):
        status, output = self.hook()
        self.assertEqual(status, 0, output)

    def declare_effect(self, path="src/authenticate.js", export="authenticate"):
        self.write("scripts/verify/external-effect-contract.json", json.dumps({
            "version": 1, "entries": [{"path": path, "export": export}]
        }))

    def test_workflow_step_deletion(self):
        self.write(WORKFLOW, BASE_WORKFLOW.replace(
            "      - name: First decision\n        run: python3 scripts/first.py\n", ""))
        self.blocked("워크플로")

    def test_workflow_file_deletion_only(self):
        (self.repo / WORKFLOW).unlink()
        self.blocked("워크플로")

    def test_workflow_symlink_replacement(self):
        self.write(".github/replacement.yml", BASE_WORKFLOW.replace(
            "      - name: First decision\n        run: python3 scripts/first.py\n", ""))
        (self.repo / WORKFLOW).unlink()
        (self.repo / WORKFLOW).symlink_to("../replacement.yml")
        self.blocked("워크플로")

    def test_workflow_command_deleted_with_step_retained(self):
        self.write(WORKFLOW, BASE_WORKFLOW.replace("          node scripts/third.mjs\n", ""))
        self.blocked("워크플로")

    def test_workflow_noop_replacement_does_not_preserve_a_check(self):
        self.write(WORKFLOW, BASE_WORKFLOW.replace(
            "run: python3 scripts/first.py", "run: echo synthetic"))
        self.blocked("워크플로")

    def test_workflow_renamed_out_of_actions_directory(self):
        (self.repo / WORKFLOW).rename(self.repo / ".github/check.yml")
        self.blocked("워크플로")

    def test_workflow_step_name_change_is_allowed(self):
        self.write(WORKFLOW, BASE_WORKFLOW.replace("First decision", "Renamed decision"))
        self.allowed()

    def test_workflow_file_move_with_same_checks_is_allowed(self):
        (self.repo / WORKFLOW).rename(self.repo / ".github/workflows/renamed.yaml")
        self.allowed()

    def test_non_workflow_deletion_is_allowed(self):
        self.write("README.md", "retained note\n")
        self.allowed()

    def test_workflow_self_exclusion(self):
        self.write(WORKFLOW, BASE_WORKFLOW + "# synthetic self-filter\n" +
                   "# marker below is executable shell in this new step\n" +
                   "      - name: Self filter\n" +
                   "        run: git ls-files | grep -v check.yml\n")
        self.blocked("자기 제외")

    def test_skill_self_exclusion(self):
        self.write(".claude/skills/verify/local-checks.sh",
                   "#!/usr/bin/env bash\ngit ls-files | grep -v local-checks.sh\n")
        self.blocked("자기 제외")

    def test_type_only_api_module_is_not_an_effect(self):
        self.write("src/api/types.ts", "export interface ApiRecord { status: string }\n")
        self.allowed()

    def test_declared_fake_authenticate_is_rejected(self):
        self.declare_effect()
        self.write("src/authenticate.js", "export async function authenticate() { return { ok: true }; }\n")
        self.blocked("외부 효과")

    def test_declared_direct_authenticate_is_allowed(self):
        self.declare_effect()
        self.write("src/authenticate.js", "export async function authenticate() { return fetch('/session'); }\n")
        self.allowed()

    def test_declared_transitive_authenticate_is_allowed(self):
        self.declare_effect()
        self.write("src/authenticate.js", "import { request } from './transport.js';\n"
                   "export async function authenticate() { return request('/session'); }\n")
        self.write("src/transport.js", "export function request(url) { return fetch(url); }\n")
        self.allowed()

    def test_uncalled_network_symbol_does_not_prove_an_effect(self):
        self.declare_effect()
        self.write("src/authenticate.js", "export async function authenticate() { return { ok: true }; }\n"
                   "function unused() { return fetch('/session'); }\n")
        self.blocked("외부 효과")

    def test_dynamic_import_is_not_silent_proof(self):
        self.declare_effect()
        self.write("src/authenticate.js", "export async function authenticate() {\n"
                   "  const target = './transport.js';\n"
                   "  const module = await import(target);\n"
                   "  return module.request('/session');\n}\n")
        self.write("src/transport.js", "export function request(url) { return fetch(url); }\n")
        self.blocked("외부 효과")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GateBoundaries)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("CHECKED:", result.testsRun)
    if result.wasSuccessful():
        print("PASS: staged deletion, self-exclusion and declared effect boundaries")
    raise SystemExit(0 if result.wasSuccessful() else 1)
