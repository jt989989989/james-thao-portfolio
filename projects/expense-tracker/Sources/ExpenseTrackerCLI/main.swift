import Foundation
import ExpenseTrackerLib

func printHelp() {
    print("""
    expense-tracker — a simple expense tracker (Swift, local JSON storage)

    Usage:
      expense-tracker add <amount> --category <name> [--note <text>] [--date YYYY-MM-DD]
      expense-tracker list [--category <name>] [--month YYYY-MM]
      expense-tracker totals [--by category|month]
      expense-tracker --demo
      expense-tracker --help

    Options:
      --data <path>   JSON data file to use (default: expenses.json in the current directory)

    Examples:
      expense-tracker add 12.50 --category Food --note "Lunch"
      expense-tracker add 2.75 --category Transport --date 2026-11-03
      expense-tracker list --month 2026-11
      expense-tracker totals --by category

    All data stays in a local JSON file. No network, no accounts.
    """)
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data("Error: \(message)\n".utf8))
    exit(1)
}

/// Pulls `--flag value` pairs out of the argument list, returning the
/// values and the remaining positional arguments.
func takeFlags(_ args: [String], flags: Set<String>) -> (values: [String: String], rest: [String]) {
    var values: [String: String] = [:]
    var rest: [String] = []
    var index = 0
    while index < args.count {
        let arg = args[index]
        if flags.contains(arg) {
            guard index + 1 < args.count else { fail("missing value for \(arg)") }
            values[arg] = args[index + 1]
            index += 2
        } else {
            rest.append(arg)
            index += 1
        }
    }
    return (values, rest)
}

var args = Array(CommandLine.arguments.dropFirst())

// Global option: --data <path> may appear anywhere.
let (globals, remaining) = takeFlags(args, flags: ["--data"])
args = remaining
let dataPath = globals["--data"] ?? "expenses.json"
let dataURL = URL(fileURLWithPath: dataPath)

guard let command = args.first else {
    printHelp()
    exit(0)
}

switch command {
case "--help", "-h", "help":
    printHelp()

case "--demo":
    // Demo runs fully in memory from fictional samples — it never
    // touches your real expenses.json.
    let demo = ExpenseStore(fileURL: dataURL, expenses: ExpenseStore.demoExpenses())
    print(demo.fullReport())

case "add":
    let positional = Array(args.dropFirst())
    let (flags, rest) = takeFlags(positional, flags: ["--category", "--note", "--date"])
    guard let amountText = rest.first else {
        fail("usage: add <amount> --category <name> [--note <text>] [--date YYYY-MM-DD]")
    }
    guard let amount = Decimal(string: amountText), amount > 0 else {
        fail("'\(amountText)' is not a positive amount (example: 12.50)")
    }
    guard let category = flags["--category"], !category.isEmpty else {
        fail("add needs --category <name>")
    }
    let date: Date
    if let dateText = flags["--date"] {
        guard let parsed = ExpenseDate.parseDay(dateText) else {
            fail("'\(dateText)' is not a valid date (use YYYY-MM-DD)")
        }
        date = parsed
    } else {
        date = Date()
    }
    do {
        var store = try ExpenseStore.load(from: dataURL)
        store.add(Expense(amount: amount, category: category, note: flags["--note"] ?? "", date: date))
        try store.save()
        print("Added \(Money.format(amount)) [\(category)] on \(ExpenseDate.dayString(date))")
    } catch {
        fail("could not save to \(dataPath): \(error.localizedDescription)")
    }

case "list":
    let (flags, _) = takeFlags(Array(args.dropFirst()), flags: ["--category", "--month"])
    do {
        let store = try ExpenseStore.load(from: dataURL)
        let shown = store.filtered(category: flags["--category"], month: flags["--month"])
        print(store.listText(shown))
        if !shown.isEmpty {
            print("\nTotal: \(Money.format(shown.reduce(Decimal(0)) { $0 + $1.amount }))")
        }
    } catch {
        fail("could not read \(dataPath): \(error.localizedDescription)")
    }

case "totals":
    let (flags, _) = takeFlags(Array(args.dropFirst()), flags: ["--by"])
    let by = flags["--by"] ?? "category"
    guard by == "category" || by == "month" else {
        fail("--by must be category or month")
    }
    do {
        let store = try ExpenseStore.load(from: dataURL)
        if by == "category" {
            for (category, total) in store.totalsByCategory() {
                print("\(category): \(Money.format(total))")
            }
        } else {
            for (month, total) in store.totalsByMonth() {
                print("\(month): \(Money.format(total))")
            }
        }
        print("Total: \(Money.format(store.total()))")
    } catch {
        fail("could not read \(dataPath): \(error.localizedDescription)")
    }

default:
    fail("unknown command '\(command)' — run with --help to see the usage")
}
