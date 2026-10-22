"""The mutation checker must distinguish assertion kills from broken mutants."""
import unittest

from tools.mail_governance.mutation_check import invalid_result


def result_with(problem=None, **counts):
    result = dict(skipped=0, expected_failures=0, unexpected_successes=0,
                  problems=[] if problem is None else [problem])
    return dict(result, **counts)


class RunnerEvidenceTests(unittest.TestCase):
    def test_runtime_errors_are_invalid_even_in_designated_test(self):
        designated = self.id()
        for exception in ("NameError", "TypeError", "ValueError"):
            with self.subTest(exception=exception):
                problem = dict(test=designated, kind="error", exception=exception,
                               message="synthetic runtime failure")
                self.assertTrue(invalid_result(result_with(problem)))

    def test_legitimate_assertion_failure_is_valid_kill_evidence(self):
        problem = dict(test=self.id(), kind="failure", exception="AssertionError",
                       message="intended guard deletion changed behavior")
        self.assertFalse(invalid_result(result_with(problem)))
        self.assertFalse(invalid_result(result_with()))

    def test_import_syntax_and_skipped_checks_remain_invalid(self):
        for exception in ("ImportError", "ModuleNotFoundError", "SyntaxError", "IndentationError", "TabError"):
            with self.subTest(exception=exception):
                problem = dict(test=self.id(), kind="error", exception=exception,
                               message="synthetic invalid test execution")
                self.assertTrue(invalid_result(result_with(problem)))
        for count in ("skipped", "expected_failures", "unexpected_successes"):
            with self.subTest(count=count):
                self.assertTrue(invalid_result(result_with(**{count: 1})))
        problem = dict(test="unittest.loader._FailedTest.synthetic", kind="failure",
                       exception="AssertionError", message="discovery failed")
        self.assertTrue(invalid_result(result_with(problem)))


if __name__ == "__main__":
    unittest.main()
