import Foundation

/// Holds the expense list and owns persistence to a local JSON file.
/// Nothing here touches the network — data stays on disk, in one file.
public struct ExpenseStore {
    public var expenses: [Expense]
    public let fileURL: URL

    public init(fileURL: URL, expenses: [Expense] = []) {
        self.fileURL = fileURL
        self.expenses = expenses.sorted { $0.date < $1.date }
    }

    /// Loads the store from disk. A missing file means an empty store —
    /// the first expense creates the file on save.
    public static func load(from fileURL: URL) throws -> ExpenseStore {
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            return ExpenseStore(fileURL: fileURL)
        }
        let data = try Data(contentsOf: fileURL)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let expenses = try decoder.decode([Expense].self, from: data)
        return ExpenseStore(fileURL: fileURL, expenses: expenses)
    }

    /// Writes the whole list back to disk (atomic write, pretty JSON).
    public func save() throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(expenses)
        try data.write(to: fileURL, options: [.atomic])
    }

    public mutating func add(_ expense: Expense) {
        expenses.append(expense)
        expenses.sort { $0.date < $1.date }
    }

    public func total() -> Decimal {
        expenses.reduce(Decimal(0)) { $0 + $1.amount }
    }

    /// Totals per category, biggest first.
    public func totalsByCategory() -> [(category: String, total: Decimal)] {
        var sums: [String: Decimal] = [:]
        for expense in expenses {
            sums[expense.category, default: Decimal(0)] += expense.amount
        }
        return sums.map { ($0.key, $0.value) }.sorted { $0.total > $1.total }
    }

    /// Totals per month (`yyyy-MM`), oldest month first.
    public func totalsByMonth() -> [(month: String, total: Decimal)] {
        var sums: [String: Decimal] = [:]
        for expense in expenses {
            sums[ExpenseDate.monthString(expense.date), default: Decimal(0)] += expense.amount
        }
        return sums.map { ($0.key, $0.value) }.sorted { $0.month < $1.month }
    }

    /// Expenses filtered by category and/or month (`yyyy-MM`).
    public func filtered(category: String? = nil, month: String? = nil) -> [Expense] {
        expenses.filter { expense in
            (category == nil || expense.category == category)
                && (month == nil || ExpenseDate.monthString(expense.date) == month)
        }
    }

    /// One-line-per-expense list, each with date, amount, category, note.
    public func listText(_ expenses: [Expense]) -> String {
        guard !expenses.isEmpty else { return "No expenses yet." }
        return expenses.map { expense in
            "\(ExpenseDate.dayString(expense.date))  \(Money.format(expense.amount))  [\(expense.category)]  \(expense.note)"
        }.joined(separator: "\n")
    }

    /// Full report: the list, totals by category, totals by month, grand total.
    public func fullReport() -> String {
        var lines: [String] = []
        lines.append("== Expenses (\(expenses.count)) ==")
        lines.append(listText(expenses))
        lines.append("")
        lines.append("== Totals by category ==")
        for (category, total) in totalsByCategory() {
            lines.append("\(category): \(Money.format(total))")
        }
        lines.append("")
        lines.append("== Totals by month ==")
        for (month, total) in totalsByMonth() {
            lines.append("\(month): \(Money.format(total))")
        }
        lines.append("")
        lines.append("Total: \(Money.format(total()))")
        return lines.joined(separator: "\n")
    }

    /// Fictional sample expenses for `--demo`. No real spending,
    /// no real personal data — invented amounts, places, and notes.
    public static func demoExpenses() -> [Expense] {
        func make(_ amount: String, _ category: String, _ note: String, _ day: String) -> Expense {
            Expense(
                amount: Decimal(string: amount) ?? 0,
                category: category,
                note: note,
                date: ExpenseDate.parseDay(day) ?? Date()
            )
        }
        return [
            make("6.50", "Food", "Coffee and pastry", "2026-11-02"),
            make("2.75", "Transport", "Bus fare", "2026-11-03"),
            make("42.30", "Food", "Groceries at Corner Mart", "2026-11-05"),
            make("12.00", "Entertainment", "Movie ticket", "2026-11-06"),
            make("14.25", "Transport", "Rideshare downtown", "2026-11-08"),
            make("18.75", "Food", "Lunch with a friend", "2026-11-09"),
        ]
    }
}
