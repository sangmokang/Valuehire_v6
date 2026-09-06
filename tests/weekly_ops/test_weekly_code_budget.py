"""The Weekly acceptance shell is authored code and shares the 600-line limit."""

import unittest
from pathlib import Path


FILE_HARD_LIMIT = 600
REPOSITORY = Path(__file__).resolve().parents[2]
ACCEPTANCE_SCRIPT = REPOSITORY / "scripts" / "acceptance-weekly-ops-skill.sh"


class WeeklyCodeBudgetTest(unittest.TestCase):
    def test_acceptance_shell_is_not_excluded_from_file_budget(self):
        self.assertTrue(ACCEPTANCE_SCRIPT.is_file())
        line_count = len(ACCEPTANCE_SCRIPT.read_text(encoding="utf-8").splitlines())
        self.assertLessEqual(line_count, FILE_HARD_LIMIT)


if __name__ == "__main__":
    unittest.main()
