"""Reopen synthetic recurring reports and reconcile their cohort denominator."""
import json
import unittest
from contextlib import redirect_stdout
from datetime import date
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from openpyxl import load_workbook
from pptx import Presentation

from narrative import prior_window, prior_year, source_reference
from schedule import run


class PeriodNarrativeTest(unittest.TestCase):
    def test_closed_periods_and_journal_revisions(self):
        with TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            root = Path(tmp)
            snapshot = root / "2023-12-31"
            snapshot.mkdir()
            (snapshot / "events.csv").write_text(
                "date,case,stage,source,client,role\n"
                "2022-12-31,z,offer,last-year,Example,Developer\n"
                "2023-12-15,early,referral,early-source,Example,Analyst\n"
                "2023-12-27,a,offer,example@example.invalid,Example,Developer\n"
                "2023-12-28,a,referral,referral-A,Example,Developer\n"
                "2023-12-28,a,referral,referral-A,Example,Developer\n"
                "2023-12-29,b,offer,proposal-B,Example,Designer\n"
                "2024-01-01,b,referral,future-row,Example,Designer\n", encoding="utf-8")
            (snapshot / "coverage.json").write_text(json.dumps({
                "scope": "Synthetic", "verified_through": "2023-12-31",
                "joins_complete": True, "complete": {"offer": True, "referral": True}
            }), encoding="utf-8")
            journal = snapshot / "journal.csv"
            journal.write_text("date,topic,finding,limit,source\n"
                               "2023-12-15,Plan,Earlier,Partial,mid-month-note\n"
                               "2024-01-01,Future,Future,Partial,future-note\n", encoding="utf-8")
            output = root / "bundles"
            args = root, output, date(2023, 12, 31), date(2024, 1, 1)
            run(*args)
            starts = {"week": "2023-12-25", "month": "2023-12-01", "quarter": "2023-10-01",
                      "half": "2023-07-01", "year": "2023-01-01"}
            for kind, start in starts.items():
                path, = (output / kind).glob("*/*/report.md")
                body = path.read_text(encoding="utf-8")
                self.assertIn(f"{start}~2023-12-31", body)
                self.assertNotIn(source_reference("future-row"), body)
                self.assertNotIn("example@example.invalid", body)
                self.assertNotIn(source_reference("future-note"), body)
                self.assertEqual(source_reference("mid-month-note") in body, kind != "week")
                self.assertIn(source_reference("proposal-B"), body)
                self.assertIn(source_reference("referral-A"), body)
                self.assertIn("1 / 2 | 50.0%", body)
                self.assertIn("미산정 | 관측 범위 제한", body)
                book = load_workbook(path.with_name("periods.xlsx"), read_only=True)
                key = path.parent.parent.name
                matches = [row[3:6] for row in book["전환 지표"].values
                           if row[:3] == (kind, key, "제안→추천")]
                self.assertEqual(matches, [(1, 2, .5)])
                self.assertIn((source_reference("example@example.invalid"), "example@example.invalid"),
                              list(book["보고서 근거"].values))
                book.close()
                self.assertTrue(Presentation(path.with_name("report.pptx")).slides)
            run(*args)
            self.assertEqual(5, len(list(output.glob("*/*/*/report.md"))))
            with journal.open("a", encoding="utf-8") as handle:
                handle.write("2023-12-31,Update,Finding,Partial,closing-note\n")
            run(*args)
            self.assertEqual(10, len(list(output.glob("*/*/*/report.md"))))
            self.assertEqual(prior_window(date(2024, 2, 26), date(2024, 3, 3), "week"),
                             (date(2023, 2, 27), date(2023, 3, 5)))
            self.assertEqual(prior_year(date(2024, 2, 29)), date(2023, 2, 28))
