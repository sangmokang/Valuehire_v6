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


def mutation(name, file, before, after, expected, *additional):
    return dict(name=name, file=file, before=before, after=after, expected=expected,
                additional=additional)


HIDDEN_TAGS_DECLARATION = ('INVISIBLE_TAGS = {"script", "style", "template", "head", "title", "noscript",\n'
                           '                  "datalist", "rp", "noembed", "noframes", "iframe"}')

GLOBAL_DELIVERY_COLLISION = (
    '            require((source_account != normalize_address(row["account"]) or sender != other_sender)\n'
    '                    and receiver != other_receiver, "historical delivery message ID collision")')


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
    mutation("checker_runtime_error_rejection", "mutation_check.py",
             '            or any(problem["kind"] == "error" for problem in result["problems"])\n', '',
             "test_runtime_errors_are_invalid_even_in_designated_test"),
    mutation("complete_html_visibility_context", "quality.py",
             '        parser = VisibleBlocks(source, evidence["start"], evidence["end"])',
             '        parser = VisibleBlocks(evidence["quote"], 0, len(evidence["quote"]))',
             "test_hidden_ancestor_cannot_be_omitted_from_all_html_citations"),
    mutation("zero_effect_recovery_history", "recovery.py",
             '    require(history == expected, "provider result history contradicts zero-effect preflight failure")\n',
             '    require(True, "provider result history contradicts zero-effect preflight failure")\n',
             "test_failed_after_provider_result_cannot_claim_zero_effect"),
    mutation("html_parser_ambiguity", "quality.py",
             '        blocks = [] if parser.ambiguous_structure else parser.blocks',
             '        blocks = parser.blocks',
             "test_nested_crossing_closes_cannot_release_hidden_inline_context"),
    mutation("historical_recorded_source_hash", "historical_delivery.py",
             '                require(sha256(intent[field]) and intent[field] == original_sha, "recorded intent source bytes mismatch")',
             '                require(sha256(intent[field]), "recorded intent source bytes mismatch")',
             "test_matching_new_hash_claims_cannot_override_recorded_legacy_source_bytes"),
    mutation("historical_recorded_receiver_identity", "historical_delivery.py",
             '    require(normalize_address(observation["account"]) == DESTINATION\n'
             '            and observation["message_id"] == delivery["receiver"], "observed receiver identity mismatch")',
             '    require(normalize_address(observation["account"]) == DESTINATION, "observed receiver identity mismatch")',
             "test_each_identity_hash_marker_label_and_recorded_delivery_binding_is_required"),
    mutation("historical_resolution_duplicate_insert", "journal.py",
             '            self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_INSERT BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {table} WHERE rowid=NEW.rowid OR ({keys})) BEGIN SELECT RAISE(ABORT,\'append-only journal\'); END")\n',
             '            if table != "delivery_resolutions":\n'
             '                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_INSERT BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {table} WHERE rowid=NEW.rowid OR ({keys})) BEGIN SELECT RAISE(ABORT,\'append-only journal\'); END")\n',
             "test_resolution_survives_reopen_and_rejects_replace_on_fresh_sqlite_connection"),
    mutation("historical_repair_confirmed_outcome", "historical_delivery.py",
             '        require(row is not None and row["outcome"] == ARCHIVE_CONFIRMED, "repair archive must be confirmed first")',
             '        require(row is not None, "repair archive must be confirmed first")',
             "test_existing_nonarchive_repair_resolution_cannot_confirm_original"),
    mutation("closed_details_visibility", "quality.py",
             '            or (tag == "details" and "open" not in attrs)\n', '',
             "test_closed_details_body_is_not_visible_including_nested_disclosures"),
    # The global scan now also protects parent IDs. Delete both comparisons to
    # model the sender invariant; deleting only the parent check is redundant.
    mutation("historical_distinct_repair_sender_parent_and_global", "historical_delivery.py",
             '    require(repair["sender"] != parent["sender"] and repair["receiver"] != parent["receiver"],\n'
             '            "repair must have distinct sender and receiver")',
             '    require(repair["receiver"] != parent["receiver"],\n'
             '            "repair must have distinct sender and receiver")',
             "test_repair_cannot_reuse_original_sender_message_id",
             (GLOBAL_DELIVERY_COLLISION,
              '            require(receiver != other_receiver, "historical delivery message ID collision")')),
    mutation("historical_distinct_repair_receiver_parent_and_global", "historical_delivery.py",
             '    require(repair["sender"] != parent["sender"] and repair["receiver"] != parent["receiver"],\n'
             '            "repair must have distinct sender and receiver")',
             '    require(repair["sender"] != parent["sender"],\n'
             '            "repair must have distinct sender and receiver")',
             "test_repair_cannot_reuse_original_receiver_message_id",
             (GLOBAL_DELIVERY_COLLISION,
              '            require(source_account != normalize_address(row["account"]) or sender != other_sender,\n'
              '                    "historical delivery message ID collision")')),
    mutation("closed_dialog_visibility", "quality.py",
             '            or (tag == "dialog" and "open" not in attrs)\n', '',
             "test_default_hidden_html_elements_cannot_establish_visible_evidence"),
    mutation("hidden_datalist_visibility", "quality.py", HIDDEN_TAGS_DECLARATION,
             HIDDEN_TAGS_DECLARATION.replace('"datalist", ', ''),
             "test_default_hidden_html_elements_cannot_establish_visible_evidence"),
    mutation("hidden_rp_visibility", "quality.py", HIDDEN_TAGS_DECLARATION,
             HIDDEN_TAGS_DECLARATION.replace('"rp", ', ''),
             "test_default_hidden_html_elements_cannot_establish_visible_evidence"),
    mutation("hidden_noembed_visibility", "quality.py", HIDDEN_TAGS_DECLARATION,
             HIDDEN_TAGS_DECLARATION.replace('"noembed", ', ''),
             "test_hidden_raw_text_citations_reject_even_with_visible_duplicate_layout"),
    mutation("hidden_noframes_visibility", "quality.py", HIDDEN_TAGS_DECLARATION,
             HIDDEN_TAGS_DECLARATION.replace('"noframes", ', ''),
             "test_hidden_raw_text_citations_reject_even_with_visible_duplicate_layout"),
    mutation("hidden_iframe_visibility", "quality.py", HIDDEN_TAGS_DECLARATION,
             HIDDEN_TAGS_DECLARATION.replace(', "iframe"', ''),
             "test_hidden_raw_text_citations_reject_even_with_visible_duplicate_layout"),
    mutation("historical_global_sender_collision", "historical_delivery.py", GLOBAL_DELIVERY_COLLISION,
             '            require(receiver != other_receiver, "historical delivery message ID collision")',
             "test_originals_cannot_share_sender_message_id_in_same_normalized_account"),
    mutation("historical_global_receiver_collision", "historical_delivery.py", GLOBAL_DELIVERY_COLLISION,
             '            require(source_account != normalize_address(row["account"]) or sender != other_sender,\n'
             '                    "historical delivery message ID collision")',
             "test_originals_cannot_share_dev_receiver_even_from_different_sender_accounts"),
    mutation("historical_all_prior_receipts", "historical_delivery.py",
             '        "WHERE operations.kind IN (\'share\',\'share_repair\') AND receipts.state=\'SENT_UNVERIFIED\'").fetchall()',
             '        "WHERE operations.kind IN (\'share\',\'share_repair\') AND receipts.state=\'SENT_UNVERIFIED\' "\n'
             '        "AND receipts.rowid IN (SELECT MAX(rowid) FROM receipts WHERE state=\'SENT_UNVERIFIED\' GROUP BY operation_id)").fetchall()',
             "test_older_foreign_receiver_receipt_cannot_be_hidden_by_latest_result"),
    mutation("historical_own_receipt_consistency", "historical_delivery.py",
             '    require(len(set(own)) == 1, "conflicting historical send results")\n', '',
             "test_own_sender_receipt_contradiction_is_rejected"),
    mutation("historical_foreign_legacy_alias_coverage", "historical_delivery.py",
             '        if row["operation_id"] != operation_id:\n',
             '        if row["operation_id"] != operation_id and "receiver_message_id" in json.loads(row["payload_json"]):\n',
             "test_foreign_legacy_dev_message_id_alias_is_checked_for_collision"),
    mutation("supported_html_open_and_close_context", "quality.py",
             '    def handle_starttag(self, tag, attrs):\n'
             '        if tag not in SUPPORTED_TAGS:\n            self.ambiguous_structure = True\n',
             '    def handle_starttag(self, tag, attrs):\n',
             "test_unsupported_media_foreign_and_custom_elements_are_not_golden_evidence",
             ('    def handle_endtag(self, tag):\n'
              '        if tag not in SUPPORTED_TAGS:\n            self.ambiguous_structure = True\n',
              '    def handle_endtag(self, tag):\n')),
    mutation("unsupported_html_closing_context", "quality.py",
             '    def handle_endtag(self, tag):\n'
             '        if tag not in SUPPORTED_TAGS:\n            self.ambiguous_structure = True\n',
             '    def handle_endtag(self, tag):\n',
             "test_unsupported_elements_outside_citations_make_source_ambiguous"),
    mutation("table_child_relationship", "quality.py",
             '        if parent in TABLE_CHILDREN and tag not in TABLE_CHILDREN[parent]:\n'
             '            self.ambiguous_structure = True\n', '',
             "test_table_foster_parenting_cannot_move_intro_below_the_jd"),
    mutation("table_parent_relationship", "quality.py",
             '        if tag in TABLE_PARENTS and parent not in TABLE_PARENTS[tag]:\n'
             '            self.ambiguous_structure = True\n', '',
             "test_table_elements_require_supported_parent_child_relationships"),
    mutation("table_direct_text_path", "quality.py", '        self.check_table_text(data)\n', '',
             "test_nonwhitespace_data_directly_inside_table_cannot_be_fostered"),
    mutation("table_entity_text_path", "quality.py", '        self.check_table_text(text)\n', '',
             "test_direct_table_entities_and_non_ascii_spaces_are_not_html_whitespace"),
    mutation("table_html_whitespace_definition", "quality.py",
             '        if self.stack and self.stack[-1][0] in TABLE_CHILDREN and data.strip(" \\t\\n\\r\\f"):',
             '        if self.stack and self.stack[-1][0] in TABLE_CHILDREN and data.strip():',
             "test_direct_table_entities_and_non_ascii_spaces_are_not_html_whitespace"),
    mutation("late_or_repeated_document_wrapper", "quality.py",
             '            if tag in self.document_tags or self.body_started or parent not in DOCUMENT_PARENTS[tag]:\n'
             '                self.ambiguous_structure = True\n', '',
             "test_late_or_repeated_document_tags_cannot_retroactively_hide_evidence"),
    mutation("script_double_escape_ambiguity", "quality.py",
             '            if "<!--" in raw:\n                self.ambiguous_structure = True\n', '',
             "test_script_double_escape_cannot_release_hidden_script_body"),
)

REDUNDANCY_CHECKS = (
    mutation("redundancy_parent_sender_check_only", "historical_delivery.py",
             '    require(repair["sender"] != parent["sender"] and repair["receiver"] != parent["receiver"],\n'
             '            "repair must have distinct sender and receiver")',
             '    require(repair["receiver"] != parent["receiver"],\n'
             '            "repair must have distinct sender and receiver")',
             "test_repair_cannot_reuse_original_sender_message_id"),
    mutation("redundancy_parent_receiver_check_only", "historical_delivery.py",
             '    require(repair["sender"] != parent["sender"] and repair["receiver"] != parent["receiver"],\n'
             '            "repair must have distinct sender and receiver")',
             '    require(repair["sender"] != parent["sender"],\n'
             '            "repair must have distinct sender and receiver")',
             "test_repair_cannot_reuse_original_receiver_message_id"),
)

POSITIVE_CONTROLS = {
    "core.py": ("test_rich_plaintext_and_structured_html_remain_golden",),
    "quality.py": ("test_rich_plaintext_and_structured_html_remain_golden",
                   "test_visible_partial_html_citations_preserve_parent_context_and_entities",
                   "test_explicitly_open_details_body_remains_visible",
                   "test_explicitly_open_dialog_and_ordinary_content_remain_visible",
                   "test_normal_table_body_preserves_intro_order_and_partial_entity_citations",
                   "test_normal_document_wrappers_and_leading_metadata_remain_visible",
                   "test_normal_nonempty_script_style_and_table_remain_visible"),
    "journal.py": ("test_journal_append_only_idempotent_and_private",
                   "test_rich_plaintext_and_structured_html_remain_golden"),
    "recovery.py": ("test_recovery_appends_failure_and_distinct_label_intent_without_rewriting",),
    "historical_delivery.py": (
        "test_confirmed_archive_is_separate_immutable_resolution_not_a_rewritten_intent",
        "test_repair_requires_confirmed_archive_and_exact_prior_delivery_links",
        "test_sender_message_ids_are_local_to_source_account",
        "test_repeated_identical_delivery_ids_with_legacy_alias_are_idempotent_observations"),
    "mutation_check.py": ("test_legitimate_assertion_failure_is_valid_kill_evidence",),
}


# Execute in a new interpreter after removing the project from its import path.
# Capture structured unittest evidence instead of treating any nonzero exit as a
# kill: a syntax/import/setup failure must never credit an unrelated regression.
HARNESS = r'''
import io
import json
import socket
import sys
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

suite = (unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:]) if sys.argv[1:]
         else unittest.defaultTestLoader.discover("tools/mail_governance", pattern="test_*.py", top_level_dir="."))
names = methods(suite)
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, resultclass=Evidence, verbosity=0).run(suite)
print(json.dumps(dict(success=result.wasSuccessful(), tests_run=result.testsRun,
                     methods=names, problems=result.problems, skipped=len(result.skipped),
                     expected_failures=len(result.expectedFailures),
                     unexpected_successes=len(result.unexpectedSuccesses))))
'''


def run_tests(directory, selected=()):
    environment = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT") if key in os.environ}
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH="", TMPDIR=str(directory))
    run = subprocess.run([sys.executable, "-c", HARNESS, *selected], cwd=directory,
                         env=environment, text=True, capture_output=True, timeout=120)
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
            or any(problem["kind"] == "error" for problem in result["problems"])
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
    summary = dict(status="invalid", scope=f"{len(MUTATIONS)} explicit guard bypasses, including named compound removals; not exhaustive mutation coverage",
                   execution="Full discovered baseline once; fresh designated regression and positive controls per mutant",
                   baseline=None, mutants=[], killed=0, survived=0, invalid=0,
                   redundancy_controls=[],
                   redundancy_reason="Parent-only ID guards may be removed without a bypass because the global ledger scan independently rejects reused delivery IDs.")
    with tempfile.TemporaryDirectory(prefix="mail-guard-mutations-") as temporary:
        directory = Path(temporary)
        baseline_directory = directory / "baseline"
        baseline_package = copy_package(source, baseline_directory)
        baseline = run_tests(baseline_directory)
        summary["baseline"] = baseline
        if (not baseline["success"] or not baseline["tests_run"] or invalid_result(baseline)):
            summary["status"] = "baseline_failed"
            return summary
        for item in (*MUTATIONS, *REDUNDANCY_CHECKS):
            redundant = item in REDUNDANCY_CHECKS
            evidence = dict(name=item["name"], file=item["file"], expected_test=item["expected"], status="invalid")
            evidence["expected_status"] = "survived" if redundant else "killed"
            summary["redundancy_controls" if redundant else "mutants"].append(evidence)
            try:
                original = (baseline_package / item["file"]).read_text(encoding="utf-8")
                changed = original
                edits = ((item["before"], item["after"]), *item["additional"])
                evidence["guard_edits"] = len(edits)
                for before, after in edits:
                    matches = changed.count(before)
                    if matches != 1:
                        raise ValueError("anchor must match exactly once; found " + str(matches))
                    changed = changed.replace(before, after, 1)
                ast.parse(changed, filename=item["file"])
                compile(changed, item["file"], "exec")
                controls = POSITIVE_CONTROLS[item["file"]]
                selected = []
                for method in (item["expected"], *controls):
                    names = [name for name in baseline["methods"] if test_matches(name, method)]
                    if len(names) != 1:
                        raise ValueError("selected regression/control must occur exactly once: " + method)
                    selected.extend(names)
                selected = sorted(set(selected))
                evidence["selected_methods"] = selected
                evidence["positive_controls"] = list(controls)
                mutant_directory = directory / item["name"]
                package = copy_package(baseline_package, mutant_directory)
                (package / item["file"]).write_text(changed, encoding="utf-8")
                result = run_tests(mutant_directory, selected)
                evidence["tests_run"] = result["tests_run"]
                evidence["problems"] = result["problems"]
                matching = [problem for problem in result["problems"]
                            if test_matches(problem["test"], item["expected"])
                            and problem["kind"] == "failure" and problem["exception"] == "AssertionError"]
                if invalid_result(result) or result["methods"] != selected:
                    raise ValueError("invalid mutant test run: runtime error, skipped, or changed discovery")
                if any(test_matches(problem["test"], method)
                       for problem in result["problems"] for method in controls):
                    raise ValueError("mutant broke a required normal positive control")
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
            if not redundant:
                summary[evidence["status"]] += 1
        summary["status"] = "pass" if (summary["killed"] == len(MUTATIONS)
            and all(item["status"] == "survived" for item in summary["redundancy_controls"])) else "fail"
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
