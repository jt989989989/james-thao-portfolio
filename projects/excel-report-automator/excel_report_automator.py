#!/usr/bin/env python3
"""Excel Report Automator — turn a messy spreadsheet export into a clean,
presentation-ready workbook, with pivot summaries.

Usage:
    python excel_report_automator.py messy_export.xlsx
    python excel_report_automator.py messy_export.xlsx -o cleaned.xlsx
    python excel_report_automator.py data.csv --pivot-rows Category \
        --pivot-cols Month --pivot-values Amount
    python excel_report_automator.py --demo

Needs openpyxl and pandas (pip install -r requirements.txt).
"""

import argparse
import sys
from pathlib import Path

try:
    import openpyxl
    import pandas as pd
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:
    print("Excel Report Automator needs openpyxl and pandas.", file=sys.stderr)
    print("Install them with:  pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

HEADER_FILL = "1D4ED8"  # blue, matches my portfolio

# Fictional demo data: a small-business expense export, deliberately messy.
DEMO_COLUMNS = ["Date", "Category", "Vendor", "Description", "Amount"]
DEMO_ROWS = [
    ["2026-01-05", "Office Supplies", "  Staples  ", "Printer paper", 24.99],
    ["01/06/2026", "Travel", "Uber", "Airport ride", 38.50],
    ["Jan 7, 2026", "Meals", "Chipotle", "Team lunch", 46.20],
    ["2026/01/08", "Office Supplies", "Amazon", "Cables", 18.75],
    # Exact duplicate of the first row once whitespace is trimmed.
    ["2026-01-05", "Office Supplies", "Staples", "Printer paper", 24.99],
    [None, None, None, None, None],  # fully blank row
    ["2026-01-12", " Software ", "Microsoft", "Subscription", 12.00],
    ["01/13/2026", "Travel", "Delta", "Flight to Chicago", 214.00],
    ["Jan 14, 2026", "Meals", "Starbucks", "Coffee run", 15.40],
    ["2026-01-15", "Office Supplies", "Amazon", "  Monitor stand  ", 32.99],
    ["2026/01/16", "Travel", "Uber", "Downtown ride", 21.75],
    ["01/17/2026", "Meals", "Chipotle", "Working lunch", 28.60],
    ["2026-01-18", "Software", "Microsoft", "Subscription", 12.00],
    ["2026-01-19", "Office Supplies", "Staples", "Notebooks", 9.50],
]


def _looks_like_date_column(df, col):
    """True if a column is a date column: by name, or because most of its
    text values parse as dates."""
    if "date" in str(col).lower():
        return True
    series = df[col].dropna()
    strings = series[series.map(lambda v: isinstance(v, str))]
    if len(strings) == 0 or len(strings) < len(series) * 0.5:
        return False
    parsed = pd.to_datetime(strings, errors="coerce", format="mixed")
    return parsed.notna().mean() >= 0.7


def clean_dataframe(df):
    """Clean a messy export. Returns (cleaned_df, stats dict)."""
    stats = {"rows_in": len(df)}
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    # Trim whitespace in text cells (before dedupe, so padded dupes match).
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(lambda v: v.strip() if isinstance(v, str) else v)

    # Drop fully blank rows, then exact duplicates.
    before = len(df)
    df = df.dropna(how="all")
    stats["blanks_removed"] = before - len(df)
    before = len(df)
    df = df.drop_duplicates()
    stats["duplicates_removed"] = before - len(df)

    # Parse date columns from mixed formats into real dates.
    dates_fixed = 0
    for col in list(df.columns):
        if df[col].dtype == object and _looks_like_date_column(df, col):
            original = df[col]
            parsed = pd.to_datetime(original, errors="coerce", format="mixed")
            fixed = (parsed.notna()
                     & original.map(lambda v: isinstance(v, str))).sum()
            if parsed.notna().any():
                df[col] = parsed
                dates_fixed += int(fixed)
    stats["dates_fixed"] = dates_fixed

    # Derive a Month (YYYY-MM) column from the first real date column, so
    # pivots can group by month without extra work.
    date_cols = [c for c in df.columns
                 if pd.api.types.is_datetime64_any_dtype(df[c])]
    if date_cols and "Month" not in df.columns:
        month = df[date_cols[0]].dt.strftime("%Y-%m")
        pos = df.columns.get_loc(date_cols[0]) + 1
        df.insert(pos, "Month", month)

    df = df.reset_index(drop=True)
    stats["rows_out"] = len(df)
    return df, stats


def build_pivot(df, rows=None, cols=None, values=None, aggfunc="sum"):
    """Build a pivot-style summary table with pandas pivot_table.

    Defaults: rows = first text column, cols = the Month column when one
    exists, values = first numeric column (or a count when there is none).
    """
    df = df.copy()
    for field, label in ((rows, "rows"), (cols, "cols"), (values, "values")):
        if field is not None and field not in df.columns:
            raise ValueError(
                f"Pivot {label} field {field!r} is not a column. "
                f"Columns are: {', '.join(str(c) for c in df.columns)}")
    if rows is None:
        text_cols = [c for c in df.columns
                     if df[c].dtype == object and c != "Month"]
        rows = text_cols[0] if text_cols else df.columns[0]
    if cols is None and "Month" in df.columns and rows != "Month":
        cols = "Month"
    if values is None:
        num_cols = [c for c in df.columns
                    if pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            values = num_cols[0]
        else:
            df["_count"] = 1
            values = "_count"
    pivot = pd.pivot_table(df, index=rows, columns=cols, values=values,
                           aggfunc=aggfunc, margins=True,
                           margins_name="Total", fill_value=0)
    return pivot


def _flatten_pivot(pivot):
    """Reset the index and flatten tuple column labels to plain strings."""
    pivot = pivot.reset_index()
    new_cols = []
    for c in pivot.columns:
        if isinstance(c, tuple):
            new_cols.append(" | ".join(str(x) for x in c if str(x) != ""))
        else:
            new_cols.append(str(c))
    pivot.columns = new_cols
    return pivot


def _format_sheet(ws):
    """Bold blue headers, frozen top row, autofilter, sensible widths."""
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=HEADER_FILL)
    for col_cells in ws.columns:
        letter = get_column_letter(col_cells[0].column)
        longest = max((len(str(c.value))
                       for c in col_cells if c.value is not None), default=0)
        ws.column_dimensions[letter].width = min(max(longest + 2, 10), 40)


def write_workbook(cleaned, pivots, output, stats, source_name):
    """Write the cleaned sheet, one sheet per pivot, and a Summary sheet."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Cleaned"
    ws.append(list(cleaned.columns))
    for row in cleaned.itertuples(index=False, name=None):
        ws.append(list(row))
    num_cols = [i for i, c in enumerate(cleaned.columns)
                if pd.api.types.is_numeric_dtype(cleaned[c])]
    if num_cols:
        total_row = ["TOTAL"] + ["" for _ in range(len(cleaned.columns) - 1)]
        for i in num_cols:
            total_row[i] = float(cleaned.iloc[:, i].sum())
        ws.append(total_row)
        for cell in ws[ws.max_row]:
            cell.font = Font(bold=True)
    for j, col in enumerate(cleaned.columns, start=1):
        if pd.api.types.is_datetime64_any_dtype(cleaned[col]):
            for row_cells in ws.iter_rows(min_row=2, max_row=ws.max_row,
                                         min_col=j, max_col=j):
                for cell in row_cells:
                    cell.number_format = "yyyy-mm-dd"
    _format_sheet(ws)

    for name, pivot in pivots:
        pws = wb.create_sheet(title=name[:31])
        flat = _flatten_pivot(pivot)
        pws.append(list(flat.columns))
        for row in flat.itertuples(index=False, name=None):
            pws.append(list(row))
        _format_sheet(pws)

    sws = wb.create_sheet(title="Summary")
    sws.append(["Excel Report Automator — run summary"])
    sws["A1"].font = Font(bold=True, size=14)
    for key, value in [
        ("Source file", source_name),
        ("Rows before cleaning", stats["rows_in"]),
        ("Rows after cleaning", stats["rows_out"]),
        ("Exact duplicates removed", stats["duplicates_removed"]),
        ("Fully blank rows removed", stats["blanks_removed"]),
        ("Date cells fixed", stats["dates_fixed"]),
        ("Pivot sheets", ", ".join(n for n, _ in pivots) or "none"),
        ("Output file", str(output)),
    ]:
        sws.append([key, value])
    sws.column_dimensions["A"].width = 30
    sws.column_dimensions["B"].width = 50
    wb.save(output)


def load_input(path):
    """Load a .xlsx (first sheet, or --sheet) or .csv file into a DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        return pd.read_excel(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file type: {suffix} (use .xlsx or .csv)")


def make_demo_workbook(path):
    """Write the messy fictional demo export (expenses with dupes, blanks,
    and dates in mixed formats)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Expenses"
    ws.append(DEMO_COLUMNS)
    for row in DEMO_ROWS:
        ws.append(row)
    wb.save(path)


def run(input_path, output_path, pivot_rows=None, pivot_cols=None,
        pivot_values=None, pivot_agg="sum"):
    """Full pipeline: load, clean, pivot, write. Returns the stats dict."""
    df = load_input(input_path)
    if df.empty:
        raise ValueError(f"Nothing to clean: {input_path} has no rows")
    cleaned, stats = clean_dataframe(df)
    if cleaned.empty:
        raise ValueError("Nothing left after cleaning — every row was "
                         "blank or a duplicate")
    pivot = build_pivot(cleaned, rows=pivot_rows, cols=pivot_cols,
                        values=pivot_values, aggfunc=pivot_agg)
    pivots = [("Pivot", pivot)]
    write_workbook(cleaned, pivots, output_path, stats, str(input_path))
    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Turn a messy spreadsheet export into a clean, "
                    "presentation-ready workbook with a pivot summary.")
    parser.add_argument("input", nargs="?",
                        help="Messy .xlsx or .csv file to clean")
    parser.add_argument("--output", "-o", default=None,
                        help="Output .xlsx file (default: <input>_cleaned.xlsx)")
    parser.add_argument("--pivot-rows", default=None,
                        help="Pivot row field, e.g. Category")
    parser.add_argument("--pivot-cols", default=None,
                        help="Pivot column field, e.g. Month")
    parser.add_argument("--pivot-values", default=None,
                        help="Pivot value field, e.g. Amount")
    parser.add_argument("--pivot-agg", default="sum",
                        choices=["sum", "count", "mean", "min", "max"],
                        help="How to aggregate pivot values (default: sum)")
    parser.add_argument("--demo", action="store_true",
                        help="Generate a messy fictional sample workbook "
                             "and run the full clean + pivot on it")
    args = parser.parse_args(argv)

    try:
        if args.demo:
            demo_in = Path("demo_messy_expenses.xlsx")
            demo_out = (Path(args.output) if args.output
                        else Path("demo_cleaned.xlsx"))
            make_demo_workbook(demo_in)
            stats = run(demo_in, demo_out, args.pivot_rows, args.pivot_cols,
                        args.pivot_values, args.pivot_agg)
            print(f"Demo input:  {demo_in}")
        else:
            if not args.input:
                parser.error("give an input file or use --demo")
            input_path = Path(args.input)
            demo_out = (Path(args.output) if args.output else
                        input_path.with_stem(input_path.stem + "_cleaned"))
            if demo_out.suffix.lower() != ".xlsx":
                demo_out = demo_out.with_suffix(".xlsx")
            stats = run(input_path, demo_out, args.pivot_rows,
                        args.pivot_cols, args.pivot_values, args.pivot_agg)
        print(f"Cleaned {stats['rows_in']} rows -> {stats['rows_out']} rows "
              f"({stats['duplicates_removed']} duplicate(s) removed, "
              f"{stats['blanks_removed']} blank row(s) removed, "
              f"{stats['dates_fixed']} date(s) fixed).")
        print(f"Wrote {demo_out} (sheets: Cleaned, Pivot, Summary).")
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
