# Expense Tracker CLI

A simple expense tracker for the command line, written in Swift.
Add expenses, list them, and see totals by category and by month.
Data lives in a local JSON file — no accounts, no network, nothing
leaves your machine.

This is my first Swift project (Swift 6.4.1, Swift Package Manager).

## What it does

- `add` — record an expense: amount, category, note, and date
  (defaults to today)
- `list` — show expenses, optionally filtered by category or month
- `totals` — totals by category or by month, plus a grand total
- `--demo` — print a report from fictional sample expenses

Money is stored as `Decimal`, not `Double`, so totals are exact
(`0.10 + 0.20` is exactly `0.30`). The core logic lives in the
`ExpenseTrackerLib` target (structs, `Codable` JSON, optionals handled
explicitly); the `ExpenseTrackerCLI` target is just argument parsing.

## Build and run

Swift 6.4.1+ required. No packages to install — standard library only.

```bash
swift build
swift run expense-tracker --demo
```

Or run the built binary directly:

```bash
.build/debug/expense-tracker --demo
```

## Usage

```bash
# Add expenses (date defaults to today)
expense-tracker add 12.50 --category Food --note "Lunch"
expense-tracker add 2.75 --category Transport --date 2026-11-03

# List them, optionally filtered
expense-tracker list
expense-tracker list --category Food
expense-tracker list --month 2026-11

# Totals
expense-tracker totals --by category
expense-tracker totals --by month

# See the demo report (fictional data, does not touch your file)
expense-tracker --demo

# Use a different data file
expense-tracker --data ~/my-expenses.json list
```

Data is stored in `expenses.json` in the directory you run from
(override with `--data <path>`). The file is plain JSON, so you can
open it in any editor.

## Demo output

```
== Expenses (6) ==
2026-11-02  $6.50  [Food]  Coffee and pastry
2026-11-03  $2.75  [Transport]  Bus fare
2026-11-05  $42.30  [Food]  Groceries at Corner Mart
2026-11-06  $12.00  [Entertainment]  Movie ticket
2026-11-08  $14.25  [Transport]  Rideshare downtown
2026-11-09  $18.75  [Food]  Lunch with a friend

== Totals by category ==
Food: $67.55
Transport: $17.00
Entertainment: $12.00

== Totals by month ==
2026-11: $96.55

Total: $96.55
```

## Tests

```bash
swift test
```

14 tests: adding and date-sorting, totals by category and month,
exact-decimal arithmetic, category/month filtering, JSON round-trip,
save/load round-trip, missing-file handling, date parsing, money
formatting, demo samples, and the report contents.

## Notes

- All sample data is fictional — invented amounts, places, and notes.
  No real spending or personal data is in this repo.
- The `.build/` directory is local build output and is not committed.
