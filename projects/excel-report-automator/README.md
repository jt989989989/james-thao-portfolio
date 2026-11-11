# Excel Report Automator

I built this to turn messy spreadsheet exports into clean, presentation-ready
workbooks — the cleanup I used to do by hand in Excel, now in one command.
I drop in a rough export, and I get back a tidy workbook with a pivot
summary I can actually show someone.

## What I do with it

- **I clean messy exports.** I drop exact duplicate rows and fully blank
  rows, I trim whitespace from text cells and column names, and I parse
  dates from mixed formats ("2026-01-05", "01/06/2026", "Jan 7, 2026")
  into real Excel dates. I also add a Month (YYYY-MM) column from the
  first date column, so my pivots can group by month.
- **I build pivot summaries.** I build a pivot-style summary table from
  the cleaned data — pick the row, column, and value fields yourself, or
  let me pick sensible defaults (first text column by rows, Month by
  columns, first number column as the values, summed with a Total row).
  Each pivot gets its own formatted sheet.
- **I format the workbook.** My headers are bold white on blue, the top
  row is frozen, autofilter is on, column widths fit the content, and I
  add a TOTAL row to the cleaned sheet.
- **I keep a Summary sheet.** I record the before/after row counts, how
  many duplicates and blank rows I removed, and how many dates I fixed —
  so I can prove what changed.

## One honest limitation: my pivots are summaries, not native PivotTables

My pivot sheets are pivot summaries — values I computed with pandas and
wrote into the workbook. They are **not** native Excel PivotTable objects
(the drag-and-drop kind inside Excel). openpyxl and pandas cannot create
those, and I won't pretend otherwise. If I want a native PivotTable, I use
my Cleaned sheet as the source: in Excel, Insert → PivotTable, and point
it at my cleaned table — which is exactly what I built this tool to
prepare.

## Install

Python 3.10+. Unlike most of my Python projects, this one needs two
packages (they are not in the standard library):

```bash
pip install -r requirements.txt
```

## Run it

```bash
# Clean a messy export (writes <input>_cleaned.xlsx)
python excel_report_automator.py messy_export.xlsx

# Choose the output file
python excel_report_automator.py messy_export.xlsx -o cleaned.xlsx

# Pick my own pivot fields (rows, columns, values)
python excel_report_automator.py expenses.xlsx \
    --pivot-rows Category --pivot-cols Month --pivot-values Amount

# Count instead of sum, or average instead
python excel_report_automator.py expenses.xlsx --pivot-agg count
python excel_report_automator.py expenses.xlsx --pivot-agg mean

# CSV input works too
python excel_report_automator.py export.csv -o cleaned.xlsx

# Try it with my built-in demo (a messy fictional expense export)
python excel_report_automator.py --demo
```

If openpyxl or pandas is missing, I print a clear install hint and exit
instead of crashing with a traceback.

## What the demo shows

My `--demo` generates a messy fictional small-business expense export
(`demo_messy_expenses.xlsx`) — duplicates, a blank row, padded
whitespace, and dates in four different formats — then runs the full
clean + pivot and writes `demo_cleaned.xlsx`. It prints the before/after
counts: 14 rows in, 12 out, 1 duplicate removed, 1 blank row removed,
12 dates fixed, and a Category × Month pivot of Amount.

## Tests

```bash
python -m unittest discover -s tests -v
```

13 tests: dedupe, blank-row removal, whitespace trimming, date parsing
across formats, Month derivation, pivot totals, default pivot fields,
the output workbook reopening with openpyxl (sheets, headers, totals),
summary counts, the demo end to end, missing-file handling, and unknown
pivot-field handling.
