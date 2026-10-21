"""Offline guard-deletion checks; each mutant gets an isolated synthetic test run.

This finite list verifies named regression protections, not mutation coverage of
every possible defect. Nothing imports live adapters, existing mail, or journals.
"""
import ast
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def mutation(name, file, before, after, expected):
    return dict(name=name, file=file, before=before, after=after, expected=expected)


MUTATIONS = (
    mutation("subject_mirror_marker", "journal.py",
             'MIRROR_MARKER in message["subject"] or ', '',
             "test_mirror_and_dev_source_do_not_relay"),
    mutation("met_axis_evidence", "core.py",
             '        require(axis["status"] != "met" or axis["evidence"] is not None, "met axis requires evidence")\n', '',
             "test_each_met_axis_requires_its_own_evidence"),
    mutation("planned_to_verified", "journal.py",
             'TRANSITIONS = {"PLANNED": {"SENDING"}',
             'TRANSITIONS = {"PLANNED": {"SENDING", "VERIFIED"}',
             "test_source_labels_require_original_message_id_with_valid_other_observations"),
    mutation("source_message_identity", "journal.py",
             '            require(observed["message_id"] == expected["message_id"], "source message mismatch")',
             '            pass  # deliberately omit source identity guard',
             "test_source_labels_require_original_message_id_with_valid_other_observations"),
    mutation("display_address_normalization", "core.py",
             '    return parsed.addr_spec.casefold()', '    return value.casefold()',
             "test_ce12_display_recipient_prevents_dev_resend"),
    mutation("code_owned_rule_version", "core.py",
             '    require(review["rule_version"] == RULE_VERSION, "unsupported rule_version: use the code-owned version")\n', '',
             "test_ce2_modified_version_cannot_create_a_new_golden_review"),
    mutation("visible_layout_block_count", "quality.py",
             '    if sum(character_count(block) >= 12 for block in blocks) < 3:',
             '    if False:  # deliberately permit one visible block',
             "test_layout_requires_visible_content_in_multiple_readable_blocks"),
    mutation("missing_rfc_no_share", "journal.py",
             '        if message["rfc_message_id"] is None:\n'
             '            return dict(operations=ops, sharing="local_identity_reconciliation_required",\n'
             '                        source_identity=source, duplicate_risk=True)\n', '',
             "test_missing_rfc_stays_local_without_automatic_duplicate_delivery"),
    mutation("append_only_duplicate_insert", "journal.py",
             '            self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_INSERT BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {table} WHERE rowid=NEW.rowid OR ({keys})) BEGIN SELECT RAISE(ABORT,\'append-only journal\'); END")\n', '',
             "test_replace_cannot_overwrite_any_journal_table_even_on_fresh_connection"),
    mutation("golden_quote_minimization", "journal.py",
             '        for axis in payload["review"]["golden_axes"].values():',
             '        for axis in []:  # deliberately retain full Golden quotes',
             "test_internal_full_layout_quote_is_hashed_not_an_extra_body_copy"),
    mutation("substantive_citation_floor", "quality.py",
             '        if character_count(quote) < floor or quote not in visible_layout:',
             '        if quote not in visible_layout:',
             "test_each_content_axis_rejects_a_single_character_independently"),
    mutation("personalization_precedes_jd", "quality.py",
             '    return positions["personalization"] < min(positions["company"], positions["role"])',
             '    return True  # deliberately ignore introduction position',
             "test_personalized_message_must_precede_company_and_role"),
    mutation("required_label_subset", "journal.py",
             '        require(set(expected["labels"]) <= set(labels["labels"]), "required labels not observed")\n', '',
             "test_receipts_fail_closed_and_readback_separate"),
)


# Execute in a new interpreter after removing the project from its import path.
# Capture structured unittest evidence instead of treating any nonzero exit as a
# kill: a syntax/import/setup failure must never credit an unrelated regression.
HARNESS = r'''
import io
import json
import socket
import unittest

def blocked(*args, **kwargs):
    raise RuntimeError("network is forbidden in synthetic mutation checks")

socket.socket.connect = blocked
socket.socket.connect_ex = blocked
socket.create_connection = blocked

def methods(suite):
    found = []
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            found.extend(methods(item))
        else:
            found.append(item.id())
    return found

class Evidence(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.problems = []

    def record(self, test, err, kind):
        self.problems.append(dict(test=test.id(), kind=kind,
                                  exception=err[0].__name__, message=str(err[1])[:500]))

    def addFailure(self, test, err):
        self.record(test, err, "failure")
        super().addFailure(test, err)

    def addError(self, test, err):
        self.record(test, err, "error")
        super().addError(test, err)

    def addSubTest(self, test, subtest, err):
        if err is not None:
            self.record(subtest, err, "failure" if issubclass(err[0], test.failureException) else "error")
        super().addSubTest(test, subtest, err)

suite = unittest.defaultTestLoader.discover("tools/mail_governance", pattern="test_*.py", top_level_dir=".")
names = methods(suite)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, resultclass=Evidence, verbosity=0).run(suite)
print(json.dumps(dict(success=result.wasSuccessful(), tests_run=result.testsRun,
                     methods=names, problems=result.problems, skipped=len(result.skipped),
                     expected_failures=len(result.expectedFailures),
                     unexpected_successes=len(result.unexpectedSuccesses))))
'''


def run_tests(directory):
    environment = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT") if key in os.environ}
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="", TMPDIR=str(directory))
    run = subprocess.run([sys.executable, "-c", HARNESS], cwd=directory,
                         env=environment, text=True, capture_output=True, timeout=60)
    if run.returncode != 0:
        raise RuntimeError("test harness failed: " + run.stderr.strip()[:1000])
    try:
        result = json.loads(run.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("test harness did not emit one JSON object") from exc
    if (not isinstance(result, dict) or not isinstance(result.get("tests_run"), int)
            or not isinstance(result.get("problems"), list)):
        raise RuntimeError("invalid test harness result")
    return result


def test_matches(identifier, method):
    return identifier.endswith("." + method) or ("." + method + " (") in identifier


def invalid_result(result):
    forbidden = {"SyntaxError", "IndentationError", "TabError", "ImportError", "ModuleNotFoundError"}
    return (result["skipped"] or result["expected_failures"] or result["unexpected_successes"]
            or any(problem["exception"] in forbidden or "_FailedTest" in problem["test"]
                   for problem in result["problems"]))


def copy_package(source, destination):
    package = destination / "tools" / "mail_governance"
    package.parent.mkdir(parents=True)
    (package.parent / "__init__.py").write_text("", encoding="utf-8")
    shutil.copytree(source, package,
                    ignore=lambda _, names: [name for name in names if not name.endswith(".py")])
    return package


def check():
    source = Path(__file__).resolve().parent
    summary = dict(status="invalid", scope=f"{len(MUTATIONS)} explicit guard deletions; not exhaustive mutation coverage",
                   baseline=None, mutants=[], killed=0, survived=0, invalid=0)
    with tempfile.TemporaryDirectory(prefix="mail-guard-mutations-") as temporary:
        directory = Path(temporary)
        baseline_directory = directory / "baseline"
        baseline_package = copy_package(source, baseline_directory)
        baseline = run_tests(baseline_directory)
        summary["baseline"] = baseline
        if (not baseline["success"] or not baseline["tests_run"] or invalid_result(baseline)):
            summary["status"] = "baseline_failed"
            return summary
        for item in MUTATIONS:
            evidence = dict(name=item["name"], file=item["file"], expected_test=item["expected"], status="invalid")
            summary["mutants"].append(evidence)
            try:
                original = (baseline_package / item["file"]).read_text(encoding="utf-8")
                matches = original.count(item["before"])
                if matches != 1:
                    raise ValueError("anchor must match exactly once; found " + str(matches))
                changed = original.replace(item["before"], item["after"], 1)
                ast.parse(changed, filename=item["file"])
                compile(changed, item["file"], "exec")
                if not any(test_matches(name, item["expected"]) for name in baseline["methods"]):
                    raise ValueError("expected regression is absent from baseline")
                mutant_directory = directory / item["name"]
                package = copy_package(baseline_package, mutant_directory)
                (package / item["file"]).write_text(changed, encoding="utf-8")
                result = run_tests(mutant_directory)
                evidence["tests_run"] = result["tests_run"]
                evidence["problems"] = result["problems"]
                matching = [problem for problem in result["problems"]
                            if test_matches(problem["test"], item["expected"])]
                if invalid_result(result) or result["methods"] != baseline["methods"]:
                    raise ValueError("invalid mutant test run: import, syntax, skipped, or changed discovery")
                if result["success"]:
                    evidence["status"] = "survived"
                elif matching:
                    evidence["status"] = "killed"
                    evidence["killed_by"] = sorted({problem["test"] for problem in matching})
                else:
                    raise ValueError("failure did not hit the designated regression")
            except (OSError, ValueError, RuntimeError, SyntaxError, subprocess.TimeoutExpired) as exc:
                evidence["status"] = "invalid"
                evidence["error"] = str(exc)
            summary[evidence["status"]] += 1
        summary["status"] = "pass" if summary["killed"] == len(MUTATIONS) else "fail"
    return summary


def main():
    try:
        summary = check()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        summary = dict(status="invalid", error=str(exc))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
