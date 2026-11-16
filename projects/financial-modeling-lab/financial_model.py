#!/usr/bin/env python3
"""Financial Modeling Lab — build a linked three-statement model + DCF in Excel.

I built this to learn financial modeling by doing it: I feed in a few simple
assumptions and I get back a real .xlsx workbook where every number is a live
Excel formula, so I can change an input and watch the whole model move.

What the workbook contains (all fictional numbers for a made-up company,
"North Star Coffee Co."):
  * Inputs            — every assumption in one place (yellow cells = change me)
  * Income Statement  — revenue, costs, EBIT, tax, net income (2025-2030)
  * Balance Sheet     — cash, receivables, inventory, PP&E, debt, equity
  * Cash Flow         — net income + depreciation - working-capital moves
                        - capex - dividends = change in cash (2026-2030)
  * DCF               — free cash flow, discounted at WACC, terminal value,
                        enterprise value, equity value, value per share
  * Forecast          — one-page summary: revenue growth, margins, free cash flow

The three statements are LINKED, not typed-in numbers: the balance sheet's
cash comes from the cash-flow statement, retained earnings come from net
income, and the cash-flow statement starts from net income. If the model is
right, the balance sheet balances (Assets = Liabilities + Equity) in every
year — the Balance Sheet has a Check row that must read 0, and --verify
prints the same tie-outs from a plain-Python replay of the model.

Usage:
    pip install -r requirements.txt
    python financial_model.py                    # uses sample_inputs.json
    python financial_model.py -o my_model.xlsx
    python financial_model.py --inputs my_inputs.json -o my_model.xlsx
    python financial_model.py --verify           # print the tie-out checks

This is a LEARNING project. I am not a finance professional and this is not
professional experience — it is a model I built to understand how the
three statements connect and how a DCF valuation works.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("openpyxl is missing. Install it first:")
    print("    pip install -r requirements.txt")
    sys.exit(1)

HERE = Path(__file__).resolve().parent
DEFAULT_INPUTS = HERE / "sample_inputs.json"

# --- Input cell addresses on the Inputs sheet (single source of truth) ---
IN = {
    "revenue": "B4", "cogs_pct": "B5", "opex_pct": "B6", "depreciation": "B7",
    "interest_rate": "B8", "tax_rate": "B9", "capex": "B10", "dividends": "B11",
    "growth_first": 14,                       # growth rows B14..B18, one per year
    "wacc": "B21", "terminal_growth": "B22", "shares": "B23",
    "ar_pct": "B27", "inv_pct": "B28", "ap_pct": "B29",
}

TITLE_FONT = Font(bold=True, size=14)
HEADER_FONT = Font(bold=True, color="FFFFFF")
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")   # yellow = change me
TOTAL_FONT = Font(bold=True)
CHECK_FONT = Font(bold=True, color="006100")
CHECK_FILL = PatternFill("solid", fgColor="C6EFCE")
THIN = Side(style="thin", color="BFBFBF")
BORDER_TOP = Border(top=Side(style="thin", color="000000"))


def load_inputs(path):
    with open(path) as f:
        data = json.load(f)
    years = [data["base_year"]] + list(data["forecast_years"])
    if len(data["revenue_growth"]) != len(data["forecast_years"]):
        raise ValueError("revenue_growth must have one entry per forecast year")
    return data, years


# ---------------------------------------------------------------- model math
# A plain-Python replay of the same model, used by --verify and the tests.
# If the Excel formulas are right, these numbers match the recalculated
# workbook exactly.
def compute_model(data):
    n = len(data["forecast_years"])
    rev = [data["base_revenue"]]
    for g in data["revenue_growth"]:
        rev.append(rev[-1] * (1 + g))
    ebit, net_income = [], []
    for r in rev:
        e = r * (1 - data["cogs_pct_of_revenue"] - data["opex_pct_of_revenue"]) \
            - data["depreciation_per_year"]
        ebit.append(e)
        ebt = e - data["base_balance_sheet"]["debt"] * data["interest_rate_on_debt"]
        net_income.append(ebt * (1 - data["tax_rate"]))

    bs0 = data["base_balance_sheet"]
    ar = [bs0["accounts_receivable"]]
    inv = [bs0["inventory"]]
    ap = [bs0["accounts_payable"]]
    ppe = [bs0["ppe_net"]]
    cash = [bs0["cash"]]
    re_ = [bs0["retained_earnings"]]
    for i in range(1, n + 1):
        ar.append(rev[i] * data["ar_pct_of_revenue"])
        inv.append(rev[i] * data["inventory_pct_of_revenue"])
        ap.append(rev[i] * data["ap_pct_of_revenue"])
        ppe.append(ppe[-1] + data["capex_per_year"] - data["depreciation_per_year"])
        # Cash flow: net income + depreciation - dAR - dInv + dAP - capex - dividends
        d_cash = (net_income[i] + data["depreciation_per_year"]
                  - (ar[i] - ar[i - 1]) - (inv[i] - inv[i - 1])
                  + (ap[i] - ap[i - 1])
                  - data["capex_per_year"] - data["dividends_per_year"])
        cash.append(cash[-1] + d_cash)
        re_.append(re_[-1] + net_income[i] - data["dividends_per_year"])

    assets, liab_equity = [], []
    for i in range(n + 1):
        assets.append(cash[i] + ar[i] + inv[i] + ppe[i])
        liab_equity.append(ap[i] + bs0["debt"] + bs0["share_capital"] + re_[i])

    nwc = [ar[i] + inv[i] - ap[i] for i in range(n + 1)]
    fcf = []
    for i in range(1, n + 1):
        fcf.append(ebit[i] * (1 - data["tax_rate"]) + data["depreciation_per_year"]
                   - data["capex_per_year"] - (nwc[i] - nwc[i - 1]))
    wacc, tg = data["wacc"], data["terminal_growth"]
    dfs = [1 / (1 + wacc) ** (i + 1) for i in range(n)]
    pv_fcf = sum(f * d for f, d in zip(fcf, dfs))
    tv = fcf[-1] * (1 + tg) / (wacc - tg)
    pv_tv = tv * dfs[-1]
    ev = pv_fcf + pv_tv
    equity = ev - bs0["debt"] + bs0["cash"]
    return {
        "revenue": rev, "ebit": ebit, "net_income": net_income,
        "cash": cash, "assets": assets, "liab_equity": liab_equity,
        "balance_check": [a - l for a, l in zip(assets, liab_equity)],
        "fcf": fcf, "pv_fcf": pv_fcf, "terminal_value": tv,
        "pv_terminal_value": pv_tv, "enterprise_value": ev,
        "equity_value": equity,
        "value_per_share": equity / data["shares_outstanding"],
    }


# ---------------------------------------------------------------- formatting
def money(cell):
    cell.number_format = '#,##0'
    return cell


def pct(cell):
    cell.number_format = '0.0%'
    return cell


def sheet_title(ws, title, subtitle, ncols):
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = subtitle
    ws["A2"].font = Font(italic=True, color="595959")
    ws.merge_cells(start_row=2, start_column=2, end_row=2, end_column=ncols)


def header_row(ws, row, years):
    ws.cell(row=row, column=1, value="").font = HEADER_FONT
    for i, y in enumerate(years):
        c = ws.cell(row=row, column=2 + i, value=y)
        c.font = HEADER_FONT
        c.fill = HEADER_FILL
        c.alignment = Alignment(horizontal="center")
    ws.cell(row=row, column=1).fill = HEADER_FILL


def label(ws, row, text, bold=False, indent=0):
    c = ws.cell(row=row, column=1, value=text)
    c.font = TOTAL_FONT if bold else Font()
    c.alignment = Alignment(indent=indent)
    return c


def formula_row(ws, row, formulas, fmt=money):
    for i, f in enumerate(formulas):
        fmt(ws.cell(row=row, column=2 + i, value=f))


def value_row(ws, row, values, fmt=money):
    for i, v in enumerate(values):
        fmt(ws.cell(row=row, column=2 + i, value=v))


def style_sheet(ws, width_a=38, width_b=16):
    ws.column_dimensions["A"].width = width_a
    for col in range(2, 9):
        ws.column_dimensions[get_column_letter(col)].width = width_b
    ws.freeze_panes = "B4"
    ws.sheet_properties.pageSetUpPr.fitToPage = True


# ---------------------------------------------------------------- builders
def build_inputs(wb, data, years):
    ws = wb.active
    ws.title = "Inputs"
    ws["A1"] = f"Inputs — {data['company']}"
    ws["A1"].font = TITLE_FONT
    ws["A2"] = ("Yellow cells are the assumptions. Change one and the whole "
                "model recalculates — that is the point of the exercise.")
    ws["A2"].font = Font(italic=True, color="595959")
    bs = data["base_balance_sheet"]

    rows = [
        (3, "Base year (actuals)", None, None),
        (4, "Revenue (base year)", data["base_revenue"], "Total sales in the base year."),
        (5, "COGS (% of revenue)", data["cogs_pct_of_revenue"], "Cost of goods sold — what it costs to make/sell."),
        (6, "Operating expenses (% of revenue)", data["opex_pct_of_revenue"], "Rent, wages, marketing, admin."),
        (7, "Depreciation (per year)", data["depreciation_per_year"], "Non-cash cost of equipment wearing out."),
        (8, "Interest rate on debt", data["interest_rate_on_debt"], "Debt is fixed; interest = rate x debt."),
        (9, "Tax rate", data["tax_rate"], "Applied to earnings before tax."),
        (10, "Capital expenditure (per year)", data["capex_per_year"], "Cash spent on new equipment."),
        (11, "Dividends (per year)", data["dividends_per_year"], "Cash paid out to shareholders."),
        (13, "Forecast revenue growth", None, None),
    ]
    for r, text, val, note in rows:
        if val is None:
            label(ws, r, text, bold=True)
        else:
            label(ws, r, text)
            c = ws.cell(row=r, column=2, value=val)
            c.fill = INPUT_FILL
            if isinstance(val, float) and val < 1:
                pct(c)
            else:
                money(c)
            if note:
                ws.cell(row=r, column=3, value=note).font = Font(color="595959")
    for i, (y, g) in enumerate(zip(data["forecast_years"], data["revenue_growth"])):
        label(ws, 14 + i, f"  Revenue growth {y}")
        c = ws.cell(row=14 + i, column=2, value=g)
        c.fill = INPUT_FILL
        pct(c)

    label(ws, 20, "Valuation", bold=True)
    for r, text, val in [
        (21, "WACC (discount rate)", data["wacc"]),
        (22, "Terminal growth rate", data["terminal_growth"]),
        (23, "Shares outstanding", data["shares_outstanding"]),
    ]:
        label(ws, r, text)
        c = ws.cell(row=r, column=2, value=val)
        c.fill = INPUT_FILL
        pct(c) if isinstance(val, float) and val < 1 else money(c)

    label(ws, 26, "Balance-sheet ratios (forecast years)", bold=True)
    for r, text, val in [
        (27, "Accounts receivable (% of revenue)", data["ar_pct_of_revenue"]),
        (28, "Inventory (% of revenue)", data["inventory_pct_of_revenue"]),
        (29, "Accounts payable (% of revenue)", data["ap_pct_of_revenue"]),
    ]:
        label(ws, r, text)
        c = ws.cell(row=r, column=2, value=val)
        c.fill = INPUT_FILL
        pct(c)

    label(ws, 31, "Base-year balance sheet (actuals)", bold=True)
    for r, text, val in [
        (32, "Cash", bs["cash"]), (33, "Accounts receivable", bs["accounts_receivable"]),
        (34, "Inventory", bs["inventory"]), (35, "PP&E, net", bs["ppe_net"]),
        (36, "Accounts payable", bs["accounts_payable"]), (37, "Debt", bs["debt"]),
        (38, "Share capital", bs["share_capital"]),
        (39, "Retained earnings", bs["retained_earnings"]),
    ]:
        label(ws, r, text)
        c = ws.cell(row=r, column=2, value=val)
        c.fill = INPUT_FILL
        money(c)
    ws.column_dimensions["A"].width = 42
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 60
    ws.freeze_panes = "A3"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    return ws


def build_income_statement(wb, data, years):
    ws = wb.create_sheet("Income Statement")
    sheet_title(ws, "Income Statement",
                "Revenue grows by the Inputs growth rates; COGS and operating "
                "expenses are % of revenue; tax is applied to earnings before tax.",
                len(years) + 1)
    header_row(ws, 3, years)
    n = len(years)
    cols = [get_column_letter(2 + i) for i in range(n)]
    I = "Inputs!"
    # Revenue: base year = input; forecast = prior year x (1 + growth)
    rev = [f"={I}${IN['revenue']}"]
    for i in range(1, n):
        g_row = IN["growth_first"] + i - 1
        rev.append(f"={cols[i-1]}4*(1+{I}$B${g_row})")
    formula_row(ws, 4, rev)
    formula_row(ws, 5, [f"=-{c}4*{I}${IN['cogs_pct']}" for c in cols])
    formula_row(ws, 6, [f"={c}4+{c}5" for c in cols], fmt=money)
    formula_row(ws, 7, [f"=-{c}4*{I}${IN['opex_pct']}" for c in cols])
    formula_row(ws, 8, [f"={c}6+{c}7" for c in cols])
    formula_row(ws, 9, [f"=-{I}${IN['depreciation']}" for _ in cols])
    formula_row(ws, 10, [f"={c}8+{c}9" for c in cols])
    formula_row(ws, 11, [f"=-'Balance Sheet'!{c}11*{I}${IN['interest_rate']}"
                          for c in cols])
    formula_row(ws, 12, [f"={c}10+{c}11" for c in cols])
    formula_row(ws, 13, [f"=-{c}12*{I}${IN['tax_rate']}" for c in cols])
    formula_row(ws, 14, [f"={c}12+{c}13" for c in cols])
    for r, text, bold in [
        (4, "Revenue", False), (5, "Cost of goods sold (COGS)", False),
        (6, "Gross profit", True), (7, "Operating expenses", False),
        (8, "EBITDA", True), (9, "Depreciation", False), (10, "EBIT", True),
        (11, "Interest expense", False), (12, "Earnings before tax (EBT)", True),
        (13, "Income tax", False), (14, "Net income", True),
    ]:
        label(ws, r, text, bold=bold)
    style_sheet(ws)
    return ws


def build_balance_sheet(wb, data, years):
    ws = wb.create_sheet("Balance Sheet")
    sheet_title(ws, "Balance Sheet",
                "Cash comes from the Cash Flow sheet, retained earnings from "
                "net income. The Check row must be 0 in every year — if it "
                "is not, the model does not tie out.", len(years) + 1)
    header_row(ws, 3, years)
    n = len(years)
    cols = [get_column_letter(2 + i) for i in range(n)]
    I, IS, CF = "Inputs!", "'Income Statement'!", "'Cash Flow'!"
    bs = data["base_balance_sheet"]
    # Year 0 (base year) = literal actuals; forecast years = formulas.
    value_row(ws, 4, [bs["cash"]] + [None] * (n - 1))
    value_row(ws, 5, [bs["accounts_receivable"]] + [None] * (n - 1))
    value_row(ws, 6, [bs["inventory"]] + [None] * (n - 1))
    value_row(ws, 7, [bs["ppe_net"]] + [None] * (n - 1))
    value_row(ws, 10, [bs["accounts_payable"]] + [None] * (n - 1))
    value_row(ws, 11, [bs["debt"]] + [None] * (n - 1))
    value_row(ws, 14, [bs["share_capital"]] + [None] * (n - 1))
    value_row(ws, 15, [bs["retained_earnings"]] + [None] * (n - 1))
    for i in range(1, n):
        c, p = cols[i], cols[i - 1]
        cf_col = get_column_letter(1 + i)  # CF cols B..F map to the same years
        ws.cell(row=4, column=2 + i, value=f"={CF}{cf_col}13").number_format = '#,##0'
        ws.cell(row=5, column=2 + i, value=f"={IS}{c}4*{I}${IN['ar_pct']}").number_format = '#,##0'
        ws.cell(row=6, column=2 + i, value=f"={IS}{c}4*{I}${IN['inv_pct']}").number_format = '#,##0'
        ws.cell(row=7, column=2 + i,
               value=f"={p}7+{I}${IN['capex']}+{IS}{c}9").number_format = '#,##0'
        ws.cell(row=10, column=2 + i, value=f"={IS}{c}4*{I}${IN['ap_pct']}").number_format = '#,##0'
        ws.cell(row=11, column=2 + i, value=f"={p}11").number_format = '#,##0'
        ws.cell(row=14, column=2 + i, value=f"={p}14").number_format = '#,##0'
        ws.cell(row=15, column=2 + i,
               value=f"={p}15+{IS}{c}14-{I}${IN['dividends']}").number_format = '#,##0'
    formula_row(ws, 8, [f"=SUM({c}4:{c}7)" for c in cols])
    formula_row(ws, 12, [f"={c}10+{c}11" for c in cols])
    formula_row(ws, 16, [f"={c}14+{c}15" for c in cols])
    formula_row(ws, 17, [f"={c}12+{c}16" for c in cols])
    for r, text, bold in [
        (4, "Cash and equivalents", False), (5, "Accounts receivable", False),
        (6, "Inventory", False), (7, "PP&E, net", False),
        (8, "Total assets", True),
        (10, "Accounts payable", False), (11, "Debt", False),
        (12, "Total liabilities", True),
        (14, "Share capital", False), (15, "Retained earnings", False),
        (16, "Total equity", True),
        (17, "Total liabilities & equity", True),
        (18, "CHECK: Assets - (Liabilities + Equity)  — must be 0", True),
    ]:
        label(ws, r, text, bold=bold)
    # Check row: recompute with the right row (17 is L&E total, so check is row 8 - row 17)
    for i, c in enumerate(cols):
        cell = ws.cell(row=18, column=2 + i, value=f"={c}8-{c}17")
        cell.number_format = '#,##0'
        cell.font = CHECK_FONT
        cell.fill = CHECK_FILL
    style_sheet(ws)
    return ws


def build_cash_flow(wb, data, years):
    ws = wb.create_sheet("Cash Flow")
    fy = years[1:]
    sheet_title(ws, "Cash Flow Statement",
                "Starts from net income, adds back non-cash depreciation, "
                "then adjusts for working capital, capex and dividends. "
                "Closing cash must equal the Balance Sheet cash.", len(fy) + 1)
    header_row(ws, 3, fy)
    n = len(fy)
    # CF col i (0-based) maps to IS/BS col i+1 (forecast years start at col C).
    cf_cols = [get_column_letter(2 + i) for i in range(n)]
    is_cols = [get_column_letter(3 + i) for i in range(n)]
    bs_prev = [get_column_letter(2 + i) for i in range(n)]
    IS, BS = "'Income Statement'!", "'Balance Sheet'!"
    I = "Inputs!"
    formula_row(ws, 4, [f"={IS}{c}14" for c in is_cols])
    formula_row(ws, 5, [f"=-{IS}{c}9" for c in is_cols])
    formula_row(ws, 6, [f"=-({BS}{c}5-{BS}{p}5)" for c, p in zip(is_cols, bs_prev)])
    formula_row(ws, 7, [f"=-({BS}{c}6-{BS}{p}6)" for c, p in zip(is_cols, bs_prev)])
    formula_row(ws, 8, [f"={BS}{c}10-{BS}{p}10" for c, p in zip(is_cols, bs_prev)])
    formula_row(ws, 9, [f"=-{I}${IN['capex']}" for _ in cf_cols])
    formula_row(ws, 10, [f"=-{I}${IN['dividends']}" for _ in cf_cols])
    formula_row(ws, 11, [f"=SUM({c}4:{c}10)" for c in cf_cols])
    formula_row(ws, 12, [f"={BS}{p}4" for p in bs_prev])
    formula_row(ws, 13, [f"={c}11+{c}12" for c in cf_cols])
    for r, text, bold in [
        (4, "Net income", False), (5, "Add: Depreciation (non-cash)", False),
        (6, "Less: Increase in accounts receivable", False),
        (7, "Less: Increase in inventory", False),
        (8, "Add: Increase in accounts payable", False),
        (9, "Less: Capital expenditure", False),
        (10, "Less: Dividends paid", False),
        (11, "Net change in cash", True),
        (12, "Opening cash", False), (13, "Closing cash", True),
    ]:
        label(ws, r, text, bold=bold)
    style_sheet(ws)
    return ws


def build_dcf(wb, data, years):
    ws = wb.create_sheet("DCF")
    fy = years[1:]
    sheet_title(ws, "DCF Valuation",
                "Free cash flow = EBIT after tax + depreciation - capex - "
                "change in working capital. Each year's FCF is discounted at "
                "WACC; the terminal value uses the Gordon growth formula.",
                len(fy) + 1)
    header_row(ws, 3, fy)
    n = len(fy)
    cf_cols = [get_column_letter(2 + i) for i in range(n)]
    is_cols = [get_column_letter(3 + i) for i in range(n)]
    bs_prev = [get_column_letter(2 + i) for i in range(n)]
    IS, BS = "'Income Statement'!", "'Balance Sheet'!"
    I = "Inputs!"
    formula_row(ws, 4, [f"={IS}{c}10" for c in is_cols])
    formula_row(ws, 5, [f"=-{c}4*{I}${IN['tax_rate']}" for c in cf_cols])
    formula_row(ws, 6, [f"={c}4+{c}5" for c in cf_cols])
    formula_row(ws, 7, [f"=-{IS}{c}9" for c in is_cols])
    formula_row(ws, 8, [f"=-{I}${IN['capex']}" for _ in cf_cols])
    formula_row(ws, 9, [f"=-(({BS}{c}5+{BS}{c}6-{BS}{c}10)"
                         f"-({BS}{p}5+{BS}{p}6-{BS}{p}10))"
                         for c, p in zip(is_cols, bs_prev)])
    formula_row(ws, 10, [f"={c}6+{c}7+{c}8+{c}9" for c in cf_cols])
    formula_row(ws, 11, [f"=1/(1+{I}${IN['wacc']})^{i+1}" for i in range(n)],
                fmt=lambda c: setattr(c, "number_format", "0.0000"))
    formula_row(ws, 12, [f"={c}10*{c}11" for c in cf_cols])
    for r, text, bold in [
        (4, "EBIT", False), (5, "Tax on EBIT", False),
        (6, "NOPAT (EBIT after tax)", True),
        (7, "Add: Depreciation", False), (8, "Less: Capital expenditure", False),
        (9, "Less: Increase in net working capital", False),
        (10, "Free cash flow (FCF)", True),
        (11, "Discount factor", False), (12, "Present value of FCF", False),
    ]:
        label(ws, r, text, bold=bold)
    last = cf_cols[-1]
    summary = [
        (14, "Present value of FCF (2026-2030)",
         f"=SUM(B12:{last}12)"),
        (15, "Terminal value (FCF 2030 x (1+g) / (WACC - g))",
         f"={last}10*(1+{I}${IN['terminal_growth']})"
         f"/({I}${IN['wacc']}-{I}${IN['terminal_growth']})"),
        (16, "Present value of terminal value",
         f"=B15*{last}11"),
        (17, "Enterprise value", "=B14+B16"),
        (18, "Less: Debt (2025)", "='Balance Sheet'!B11"),
        (19, "Plus: Cash (2025)", "='Balance Sheet'!B4"),
        (20, "Equity value", "=B17-B18+B19"),
        (21, "Shares outstanding", f"={I}${IN['shares']}"),
        (22, "Value per share", "=B20/B21"),
    ]
    for r, text, f in summary:
        label(ws, r, text, bold=(r in (17, 20, 22)))
        c = ws.cell(row=r, column=2, value=f)
        money(c)
        if r == 22:
            c.number_format = '"$"#,##0.00'
    ws.cell(row=14, column=2).font = TOTAL_FONT
    ws.cell(row=17, column=2).font = TOTAL_FONT
    ws.cell(row=20, column=2).font = TOTAL_FONT
    ws.cell(row=22, column=2).font = TOTAL_FONT
    style_sheet(ws)
    return ws


def build_forecast(wb, data, years):
    ws = wb.create_sheet("Forecast")
    sheet_title(ws, "Forecast Summary",
                "One page to watch: change a growth rate on Inputs and see "
                "revenue, margins and free cash flow move here.",
                len(years) + 1)
    header_row(ws, 3, years)
    n = len(years)
    cols = [get_column_letter(2 + i) for i in range(n)]
    IS, BS, DCF = "'Income Statement'!", "'Balance Sheet'!", "'DCF'!"
    formula_row(ws, 4, [f"={IS}{c}4" for c in cols])
    growth = ["—"] + [f"={cols[i]}4/{cols[i-1]}4-1" for i in range(1, n)]
    for i, f in enumerate(growth):
        c = ws.cell(row=5, column=2 + i, value=f)
        if isinstance(f, str) and f.startswith("="):
            pct(c)
    formula_row(ws, 6, [f"={IS}{c}10/{IS}{c}4" for c in cols], fmt=pct)
    formula_row(ws, 7, [f"={IS}{c}14/{IS}{c}4" for c in cols], fmt=pct)
    fcf = ["—"] + [f"={DCF}{get_column_letter(2 + i)}10" for i in range(n - 1)]
    for i, f in enumerate(fcf):
        c = ws.cell(row=8, column=2 + i, value=f)
        if isinstance(f, str) and f.startswith("="):
            money(c)
    formula_row(ws, 9, [f"={BS}{c}4" for c in cols])
    for r, text, bold in [
        (4, "Revenue", False), (5, "Revenue growth", False),
        (6, "EBIT margin", False), (7, "Net income margin", False),
        (8, "Free cash flow", False), (9, "Cash", False),
    ]:
        label(ws, r, text, bold=bold)
    ws["A11"] = "Try this:"
    ws["A11"].font = TOTAL_FONT
    for i, tip in enumerate([
        "Change 2026 revenue growth on Inputs (B14) from 10% to 20% — "
        "revenue, net income, cash and the DCF value per share all rise.",
        "Raise COGS % (Inputs B5) from 55% to 65% — margins fall and the "
        "value per share drops. That is operating leverage in action.",
        "Raise WACC (Inputs B21) from 10% to 12% — future cash flows are "
        "worth less today, so the value per share falls.",
    ]):
        ws.cell(row=12 + i, column=1, value=f"{i+1}. {tip}")
        ws.merge_cells(start_row=12 + i, start_column=1,
                       end_row=12 + i, end_column=len(years) + 1)
    style_sheet(ws)
    return ws


def build_workbook(data, years):
    wb = Workbook()
    build_inputs(wb, data, years)
    build_income_statement(wb, data, years)
    build_balance_sheet(wb, data, years)
    build_cash_flow(wb, data, years)
    build_dcf(wb, data, years)
    build_forecast(wb, data, years)
    wb["Inputs"].sheet_properties.tabColor = "FFF2CC"
    wb["Income Statement"].sheet_properties.tabColor = "1F4E79"
    wb["Balance Sheet"].sheet_properties.tabColor = "1F4E79"
    wb["Cash Flow"].sheet_properties.tabColor = "1F4E79"
    wb["DCF"].sheet_properties.tabColor = "548235"
    wb["Forecast"].sheet_properties.tabColor = "548235"
    wb.active = wb["Inputs"]
    return wb


def verify(data, result):
    print("Tie-out checks (plain-Python replay of the model):")
    bad = False
    for i, chk in enumerate(result["balance_check"]):
        ok = abs(chk) < 0.01
        bad = bad or not ok
        print(f"  Balance sheet balances, year {data['base_year'] + i}: "
              f"Assets - (Liab. + Equity) = {chk:,.2f}  {'OK' if ok else 'FAIL'}")
    for i, f in enumerate(result["fcf"]):
        print(f"  Free cash flow {data['forecast_years'][i]}: ${f:,.0f}")
    print(f"  PV of FCF (2026-2030):        ${result['pv_fcf']:,.0f}")
    print(f"  Terminal value:               ${result['terminal_value']:,.0f}")
    print(f"  Enterprise value:             ${result['enterprise_value']:,.0f}")
    print(f"  Equity value:                 ${result['equity_value']:,.0f}")
    print(f"  Value per share:              ${result['value_per_share']:,.2f}")
    print("  RESULT:", "ALL CHECKS PASS" if not bad else "CHECKS FAILED")
    return not bad


def main():
    parser = argparse.ArgumentParser(
        description="Build a linked three-statement + DCF model as an Excel workbook.")
    parser.add_argument("--inputs", default=str(DEFAULT_INPUTS),
                        help="JSON assumptions file (default: sample_inputs.json)")
    parser.add_argument("-o", "--output", default="sample_financial_model.xlsx",
                        help="Output .xlsx file")
    parser.add_argument("--verify", action="store_true",
                        help="Print the balance-sheet and DCF tie-out checks")
    args = parser.parse_args()

    data, years = load_inputs(args.inputs)
    result = compute_model(data)
    wb = build_workbook(data, years)
    out = Path(args.output)
    wb.save(out)
    print(f"Wrote {out} ({data['company']}, {years[0]}-{years[-1]})")
    print("Sheets: Inputs, Income Statement, Balance Sheet, Cash Flow, DCF, Forecast")
    if args.verify:
        ok = verify(data, result)
        sys.exit(0 if ok else 1)
    print("Run with --verify to see the tie-out checks.")


if __name__ == "__main__":
    main()
