"""Tests for the Financial Modeling Lab.

I verify two things:
  1. My plain-Python replay of the model ties out (balance sheet balances,
     free cash flow and DCF match my hand-checked numbers).
  2. The workbook I generate actually recalculates in a real spreadsheet
     engine (LibreOffice headless) with the same numbers and zero error cells.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

from financial_model import compute_model, load_inputs  # noqa: E402

EXPECTED_VALUE_PER_SHARE = 94.60
EXPECTED_FCF = [59100, 66892, 73907.36, 81253.00, 87376.18]


class TestModelMath(unittest.TestCase):
    def setUp(self):
        self.data, self.years = load_inputs(HERE / "sample_inputs.json")
        self.result = compute_model(self.data)

    def test_balance_sheet_balances_every_year(self):
        for chk in self.result["balance_check"]:
            self.assertAlmostEqual(chk, 0, places=2)

    def test_free_cash_flow(self):
        for got, want in zip(self.result["fcf"], EXPECTED_FCF):
            self.assertAlmostEqual(got, want, places=1)

    def test_value_per_share(self):
        self.assertAlmostEqual(
            self.result["value_per_share"], EXPECTED_VALUE_PER_SHARE, places=2)

    def test_revenue_grows(self):
        rev = self.result["revenue"]
        self.assertEqual(rev[0], 500000)
        self.assertAlmostEqual(rev[-1], 720811.87, places=1)
        self.assertTrue(all(b > a for a, b in zip(rev, rev[1:])))


class TestWorkbook(unittest.TestCase):
    def test_generated_workbook_recalculates(self):
        from openpyxl import load_workbook
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "model.xlsx"
            subprocess.run(
                [sys.executable, str(HERE / "financial_model.py"),
                 "-o", str(out), "--verify"],
                cwd=HERE, check=True, capture_output=True, text=True)
            recalc = Path(tmp) / "recalc"
            recalc.mkdir()
            subprocess.run(
                ["soffice", "--headless", "--calc", "--convert-to", "xlsx",
                 "--outdir", str(recalc), str(out)],
                check=True, capture_output=True, text=True)
            wb = load_workbook(recalc / "model.xlsx", data_only=True)
            self.assertEqual(
                wb.sheetnames,
                ["Inputs", "Income Statement", "Balance Sheet",
                 "Cash Flow", "DCF", "Forecast"])
            bs = wb["Balance Sheet"]
            checks = [bs.cell(row=18, column=c).value for c in range(2, 8)]
            self.assertTrue(all(v == 0 for v in checks),
                            f"balance-sheet check row not all zero: {checks}")
            # Cash on the balance sheet must equal closing cash on the
            # cash-flow statement, year by year.
            cf = wb["Cash Flow"]
            for i in range(5):
                self.assertAlmostEqual(
                    bs.cell(row=4, column=3 + i).value,
                    cf.cell(row=13, column=2 + i).value, places=2)
            dcf = wb["DCF"]
            self.assertAlmostEqual(dcf["B22"].value,
                                   EXPECTED_VALUE_PER_SHARE, places=2)
            # No formula errors anywhere in the workbook.
            errors = [(ws.title, c.coordinate, c.value)
                      for ws in wb.worksheets for row in ws.iter_rows()
                      for c in row
                      if isinstance(c.value, str) and c.value.startswith("#")]
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
