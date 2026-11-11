"""Tests for the Excel Report Automator."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import openpyxl
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import excel_report_automator as era


def sample_df():
    return pd.DataFrame({
        " Date ": ["2026-01-05", "01/06/2026", "Jan 7, 2026",
                   "2026-01-05", "2026/01/08", None],
        "Category": ["  Office ", "Travel", "Meals",
                     "Office", "Travel", None],
        "Amount": [10.0, 20.0, 30.0, 10.0, 40.0, None],
    })


class TestCleaning(unittest.TestCase):
    def test_dedupe_removes_exact_duplicates_after_trim(self):
        cleaned, stats = era.clean_dataframe(sample_df())
        self.assertEqual(stats["duplicates_removed"], 1)
        self.assertEqual(len(cleaned), 4)  # 6 - 1 blank - 1 dupe

    def test_blank_rows_removed(self):
        cleaned, stats = era.clean_dataframe(sample_df())
        self.assertEqual(stats["blanks_removed"], 1)
        self.assertFalse(cleaned.isna().all(axis=1).any())

    def test_whitespace_trimmed_in_text_cells(self):
        cleaned, _ = era.clean_dataframe(sample_df())
        self.assertEqual(cleaned["Category"].iloc[0], "Office")

    def test_column_names_trimmed(self):
        cleaned, _ = era.clean_dataframe(sample_df())
        self.assertIn("Date", cleaned.columns)
        self.assertNotIn(" Date ", cleaned.columns)

    def test_dates_parsed_from_multiple_formats(self):
        cleaned, stats = era.clean_dataframe(sample_df())
        self.assertTrue(
            pd.api.types.is_datetime64_any_dtype(cleaned["Date"]))
        self.assertEqual(stats["dates_fixed"], 4)
        self.assertEqual(str(cleaned["Date"].iloc[0])[:10], "2026-01-05")
        self.assertEqual(str(cleaned["Date"].iloc[1])[:10], "2026-01-06")
        self.assertEqual(str(cleaned["Date"].iloc[2])[:10], "2026-01-07")
        self.assertEqual(str(cleaned["Date"].iloc[3])[:10], "2026-01-08")

    def test_month_column_derived(self):
        cleaned, _ = era.clean_dataframe(sample_df())
        self.assertIn("Month", cleaned.columns)
        self.assertTrue((cleaned["Month"] == "2026-01").all())


class TestPivot(unittest.TestCase):
    def test_pivot_totals_match_expected(self):
        cleaned, _ = era.clean_dataframe(sample_df())
        pivot = era.build_pivot(cleaned, rows="Category", cols="Month",
                                values="Amount", aggfunc="sum")
        self.assertEqual(pivot.loc["Office", "2026-01"], 10.0)
        self.assertEqual(pivot.loc["Travel", "2026-01"], 60.0)
        self.assertEqual(pivot.loc["Total", "Total"], 100.0)

    def test_default_pivot_uses_category_and_month(self):
        cleaned, _ = era.clean_dataframe(sample_df())
        pivot = era.build_pivot(cleaned)
        self.assertIn("Office", pivot.index)
        self.assertIn("2026-01", [str(c) for c in pivot.columns])

    def test_unknown_pivot_field_errors(self):
        cleaned, _ = era.clean_dataframe(sample_df())
        with self.assertRaises(ValueError):
            era.build_pivot(cleaned, rows="NoSuchColumn")


class TestWorkbookAndCli(unittest.TestCase):
    def test_output_workbook_reopens_with_sheets_and_format(self):
        cleaned, stats = era.clean_dataframe(sample_df())
        pivot = era.build_pivot(cleaned)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.xlsx"
            era.write_workbook(cleaned, [("Pivot", pivot)], out, stats,
                               "input.xlsx")
            wb = openpyxl.load_workbook(out)
            self.assertEqual(wb.sheetnames, ["Cleaned", "Pivot", "Summary"])
            ws = wb["Cleaned"]
            self.assertTrue(ws["A1"].font.bold)  # header formatting
            self.assertEqual(ws["A1"].value, "Date")
            self.assertEqual(ws["A2"].value, pd.Timestamp("2026-01-05"))
            self.assertEqual(ws.cell(row=ws.max_row, column=1).value, "TOTAL")
            summary = wb["Summary"]
            text = "\n".join(str(c.value) for row in summary.iter_rows()
                             for c in row if c.value is not None)
            self.assertIn("1", text)  # duplicates removed shows up

    def test_summary_counts_match(self):
        _, stats = era.clean_dataframe(sample_df())
        self.assertEqual(stats["rows_in"], 6)
        self.assertEqual(stats["rows_out"], 4)
        self.assertEqual(stats["duplicates_removed"], 1)
        self.assertEqual(stats["blanks_removed"], 1)
        self.assertEqual(stats["dates_fixed"], 4)

    def test_demo_mode_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                self.assertEqual(era.main(["--demo"]), 0)
                self.assertTrue(Path("demo_messy_expenses.xlsx").exists())
                out = Path("demo_cleaned.xlsx")
                self.assertTrue(out.exists())
                wb = openpyxl.load_workbook(out)
                self.assertEqual(wb.sheetnames,
                                 ["Cleaned", "Pivot", "Summary"])
                cleaned = wb["Cleaned"]
                # 14 rows in, 12 out (1 blank + 1 dupe removed)
                self.assertEqual(cleaned.max_row, 14)  # header + 12 + TOTAL
            finally:
                os.chdir(cwd)

    def test_missing_input_file_exits_1(self):
        self.assertEqual(era.main(["no_such_file.xlsx"]), 1)


if __name__ == "__main__":
    unittest.main()
