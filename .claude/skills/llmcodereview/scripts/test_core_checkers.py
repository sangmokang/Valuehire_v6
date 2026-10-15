#!/usr/bin/env python3
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SHA = "abc123"


class CoreCheckerTests(unittest.TestCase):
    def run_script(self, script, *args, env=None):
        cmd = ["python3", str(SCRIPT_DIR / script), *map(str, args)]
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            env=(os.environ | {"LCR_SHA": SHA} | (env or {})),
        )

    def test_check_coverage_rejects_empty_inventory(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            raw = p / "planner.txt"
            raw.write_text('<<<PLANNER_JSON\n{"head_sha_checked":"abc123","coverage_ledger":[],"wus":[]}\nPLANNER_JSON>>>')
            inv = p / "empty.tsv"
            inv.write_text("")

            r = self.run_script("check_coverage.py", raw, inv, p / "out.json")

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("EMPTY_INVENTORY", r.stdout)

    def test_check_coverage_rejects_primary_wu_file_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            raw = p / "planner.txt"
            raw.write_text(
                "<<<PLANNER_JSON\n"
                + json.dumps(
                    {
                        "head_sha_checked": SHA,
                        "coverage_ledger": [{"file": "a.py", "primary_wu": "WU02", "added": 2, "deleted": 1}],
                        "wus": [
                            {"id": "WU01", "files": ["a.py"], "risk": "S1", "changed_lines": 3, "needs_auditor": False, "title": "x"},
                            {"id": "WU02", "files": [], "risk": "S1", "changed_lines": 0, "needs_auditor": False, "title": "y"},
                        ],
                    }
                )
                + "\nPLANNER_JSON>>>"
            )
            inv = p / "inv.tsv"
            inv.write_text("a.py\t2\t1\n")

            r = self.run_script("check_coverage.py", raw, inv, p / "out.json")

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("PRIMARY_WU_FILE_MISMATCH a.py WU02", r.stdout)

    def test_check_coverage_accepts_matching_primary_wu(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            raw = p / "planner.txt"
            raw.write_text(
                "<<<PLANNER_JSON\n"
                + json.dumps(
                    {
                        "head_sha_checked": SHA,
                        "coverage_ledger": [{"file": "a.py", "primary_wu": "WU01", "added": 2, "deleted": 1}],
                        "wus": [{"id": "WU01", "files": ["a.py"], "risk": "S1", "changed_lines": 3, "needs_auditor": False, "title": "x"}],
                    }
                )
                + "\nPLANNER_JSON>>>"
            )
            inv = p / "inv.tsv"
            inv.write_text("a.py\t2\t1\n")

            r = self.run_script("check_coverage.py", raw, inv, p / "out.json")

            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_check_wu_rejects_not_checked_integ_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "plan.json").write_text(json.dumps({"cross_wu_boundaries": [{"id": "B1"}]}))
            raw = p / "integ.txt"
            raw.write_text('<<<INTEG_JSON\n{"head_sha_checked":"abc123","boundaries":[{"id":"B1","status":"NOT_CHECKED"}]}\nINTEG_JSON>>>')

            r = self.run_script("check_wu.py", raw, p / "plan.json", p / "inv.tsv", "INTEG", p / "out.json", "INTEG_JSON")

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("BOUNDARY_NOT_CHECKED B1", r.stdout)

    def test_check_wu_rejects_empty_audit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            raw = p / "audit.txt"
            raw.write_text('<<<AUDIT_JSON\n{"head_sha_checked":"abc123"}\nAUDIT_JSON>>>')

            r = self.run_script("check_wu.py", raw, p / "plan.json", p / "inv.tsv", "AUDIT", p / "out.json", "AUDIT_JSON")

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("REVIEWER_RESULT_MISSING", r.stdout)
            self.assertIn("AUDIT_ATTEMPTS_INCOMPLETE", r.stdout)

    def test_check_wu_accepts_verified_integ_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "plan.json").write_text(json.dumps({"cross_wu_boundaries": [{"id": "B1"}]}))
            raw = p / "integ.txt"
            raw.write_text('<<<INTEG_JSON\n{"head_sha_checked":"abc123","boundaries":[{"id":"B1","status":"VERIFIED","evidence":"a.py:1 ↔ b.py:2"}]}\nINTEG_JSON>>>')

            r = self.run_script("check_wu.py", raw, p / "plan.json", p / "inv.tsv", "INTEG", p / "out.json", "INTEG_JSON")

            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("COVERAGE_OK", r.stdout)

    def test_check_wu_rejects_omitted_planned_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "plan.json").write_text(json.dumps({"cross_wu_boundaries": [{"id": "B1"}, {"id": "B2"}]}))
            raw = p / "integ.txt"
            raw.write_text('<<<INTEG_JSON\n{"head_sha_checked":"abc123","boundaries":[{"id":"B1","status":"VERIFIED","evidence":"a.py:1 ↔ b.py:2"}]}\nINTEG_JSON>>>')

            r = self.run_script("check_wu.py", raw, p / "plan.json", p / "inv.tsv", "INTEG", p / "out.json", "INTEG_JSON")

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("MISSING_BOUNDARY B2", r.stdout)

    def test_check_wu_rejects_unusable_integration_finding(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "plan.json").write_text(json.dumps({"cross_wu_boundaries": [{"id": "B1"}]}))
            raw = p / "integ.txt"
            raw.write_text('<<<INTEG_JSON\n' + json.dumps({
                "head_sha_checked": SHA,
                "boundaries": [{"id": "B1", "status": "ISSUE", "evidence": "a.py:1 ↔ b.py:2"}],
                "new_findings": [{"id": "NF1"}],
            }) + '\nINTEG_JSON>>>')

            r = self.run_script("check_wu.py", raw, p / "plan.json", p / "inv.tsv", "INTEG", p / "out.json", "INTEG_JSON")

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("FINDING_INVALID NF1", r.stdout)

    def test_check_wu_audit_requires_reclassification_and_attacks(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "WU01.json").write_text(json.dumps({"head_sha_checked": SHA, "findings": [{"id": "F1"}]}))
            raw = p / "audit.txt"
            raw.write_text('<<<AUDIT_JSON\n{"head_sha_checked":"abc123","reclassified":[],"attempts":[{"attack":"one","result":"failed"}]}\nAUDIT_JSON>>>')

            r = self.run_script("check_wu.py", raw, p / "plan.json", p / "inv.tsv", "WU01", p / "WU01-audit.json", "AUDIT_JSON")

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("MISSING_RECLASSIFIED F1", r.stdout)
            self.assertIn("AUDIT_ATTEMPTS_INCOMPLETE", r.stdout)

    def test_check_wu_accepts_complete_audit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "WU01.json").write_text(json.dumps({"head_sha_checked": SHA, "findings": [{"id": "F1"}]}))
            raw = p / "audit.txt"
            raw.write_text('<<<AUDIT_JSON\n' + json.dumps({
                "head_sha_checked": SHA,
                "reclassified": [{"id": "F1", "status": "CONFIRMED", "reason": "a.py:5"}],
                "attempts": [{"attack": str(i), "result": "blocked"} for i in range(3)],
            }) + '\nAUDIT_JSON>>>')

            r = self.run_script("check_wu.py", raw, p / "plan.json", p / "inv.tsv", "WU01", p / "WU01-audit.json", "AUDIT_JSON")

            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("COVERAGE_OK", r.stdout)

    def test_check_wu_rejects_stale_reviewer_result(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "WU01.json").write_text(json.dumps({"head_sha_checked": "old", "findings": []}))
            raw = p / "audit.txt"
            raw.write_text('<<<AUDIT_JSON\n' + json.dumps({
                "head_sha_checked": SHA,
                "reclassified": [],
                "attempts": [{"attack": str(i), "result": "blocked"} for i in range(3)],
            }) + '\nAUDIT_JSON>>>')

            r = self.run_script("check_wu.py", raw, p / "plan.json", p / "inv.tsv", "WU01", p / "WU01-audit.json", "AUDIT_JSON")

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("REVIEWER_SHA_MISMATCH", r.stdout)

    def test_check_seen_rejects_zero_bundle_files(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            prompt = p / "prompt.txt"
            prompt.write_text("no attached files here")
            result = p / "result.json"
            result.write_text('{"bundle_files_seen":[]}')

            r = self.run_script("check_seen.py", prompt, result)

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("NO_BUNDLE_FILES", r.stdout)

    def test_check_seen_rejects_extra_seen_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            prompt = p / "prompt.txt"
            prompt.write_text("===== END FILE: a.py (last line 3) =====")
            result = p / "result.json"
            result.write_text('{"bundle_files_seen":[{"file":"a.py","last_line_seen":3},{"file":"b.py","last_line_seen":1}]}')

            r = self.run_script("check_seen.py", prompt, result)

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("EXTRA_SEEN b.py", r.stdout)

    def test_check_seen_rejects_nonpositive_last_line(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            prompt = p / "prompt.txt"
            prompt.write_text("===== END FILE: a.py (last line 0) =====")
            result = p / "result.json"
            result.write_text('{"bundle_files_seen":[{"file":"a.py","last_line_seen":0}]}')

            r = self.run_script("check_seen.py", prompt, result)

            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("nonpositive_last_line=0", r.stdout)

    def test_check_seen_accepts_exact_file_accounting(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            prompt = p / "prompt.txt"
            prompt.write_text("===== END FILE: a.py (last line 3) =====")
            result = p / "result.json"
            result.write_text('{"bundle_files_seen":[{"file":"a.py","last_line_seen":3}]}')

            r = self.run_script("check_seen.py", prompt, result)

            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("SEEN_OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
