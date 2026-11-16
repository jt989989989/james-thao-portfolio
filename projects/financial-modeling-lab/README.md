# Financial Modeling Lab

I built this to learn financial modeling by actually building a model — the
kind of three-statement model, DCF valuation, and forecasting the Mercor
Excel Expert – Finance role asks for. I don't have professional finance
experience, and this project doesn't claim I do: it's a learning project I
built so I can run a model, change the assumptions, and see how the numbers
move. All figures are fictional, for a made-up company ("North Star Coffee
Co.").

## What I built

I feed in a few simple assumptions and I get back a real Excel workbook
where every number is a **live formula** — not typed-in values. Change a
growth rate on the Inputs sheet and the income statement, balance sheet,
cash flow, DCF, and forecast all recalculate.

| Sheet | What I learn from it |
|---|---|
| **Inputs** | Every assumption in one place. Yellow cells are the ones I change: revenue growth, COGS %, operating expenses %, tax rate, capex, dividends, WACC, terminal growth, and the balance-sheet ratios. |
| **Income Statement** | Revenue grows by my growth rates; COGS and operating expenses are % of revenue; then depreciation, interest, tax, and net income. 2025 actuals + 2026–2030 forecast. |
| **Balance Sheet** | Cash, receivables, inventory, PP&E, payables, debt, share capital, retained earnings. Cash comes from the Cash Flow sheet; retained earnings come from net income. The green Check row must read **0** in every year — Assets = Liabilities + Equity. |
| **Cash Flow** | Starts from net income, adds back non-cash depreciation, adjusts for working-capital moves (receivables, inventory, payables), subtracts capex and dividends. Closing cash must equal the Balance Sheet cash. |
| **DCF** | Free cash flow = EBIT after tax + depreciation − capex − change in working capital. Each year's FCF is discounted at WACC; the terminal value uses the Gordon growth formula (FCF × (1+g) / (WACC − g)). Enterprise value → less debt → plus cash → equity value → value per share. |
| **Forecast** | One-page summary: revenue, revenue growth, EBIT margin, net margin, free cash flow, cash — plus three things to try changing. |

## What the sample model says

With the sample inputs (base revenue $500,000, growth 10% → 6%, COGS 55%,
operating expenses 25%, tax 21%, WACC 10%, terminal growth 2%):

- Revenue grows $500,000 → $720,812 by 2030
- Free cash flow grows $59,100 → $87,376 a year
- Enterprise value: **$966,023** · Equity value: **$946,023** · Value per share: **$94.60**
- The balance sheet balances (Check row = 0) in all six years, and closing
  cash ties to the balance sheet every year — I verified this by
  recalculating the workbook in LibreOffice, not just by trusting the
  formulas.

## Install

Python 3.10+. One package (not in the standard library):

```bash
pip install -r requirements.txt
```

## Run it

```bash
# Build the sample model (writes sample_financial_model.xlsx)
python financial_model.py

# Build it and print the tie-out checks
python financial_model.py --verify

# Use my own assumptions
python financial_model.py --inputs my_inputs.json -o my_model.xlsx
```

Then open the `.xlsx` in Excel (or Google Sheets / LibreOffice) and start
on the **Inputs** sheet. Try changing a yellow cell and watch the Forecast
sheet move.

## My own assumptions file

Copy `sample_inputs.json` and edit the numbers — same keys, same shape:

```json
{
  "base_revenue": 500000,
  "revenue_growth": [0.10, 0.08, 0.08, 0.06, 0.06],
  "cogs_pct_of_revenue": 0.55,
  "tax_rate": 0.21,
  "wacc": 0.10,
  "terminal_growth": 0.02,
  "shares_outstanding": 10000
}
```

## Three things to try

1. Change 2026 revenue growth (Inputs B14) from 10% to 20% — revenue, net
   income, cash, and the DCF value per share all rise.
2. Raise COGS % (Inputs B5) from 55% to 65% — margins fall and the value
   per share drops. That's operating leverage in action.
3. Raise WACC (Inputs B21) from 10% to 12% — future cash flows are worth
   less today, so the value per share falls.

## Tests

```bash
python -m unittest discover -s tests -v
```

5 tests: the balance sheet balances every year, free cash flow and value
per share match my hand-checked numbers, revenue grows, and the generated
workbook recalculates in LibreOffice with the same numbers, cash tying out,
and zero formula-error cells.

## Honest limitations

- This is a **teaching model**, not a professional valuation. Interest is a
  flat rate on fixed debt, tax is a flat rate on earnings, and working
  capital is a fixed % of revenue — real companies are messier.
- I built this to **learn** three-statement modeling, DCF, and forecasting.
  It is not professional finance experience, and I don't present it as such.
