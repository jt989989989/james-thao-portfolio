import Foundation

/// A single expense. Money is stored as `Decimal` so totals are exact —
/// floating point is the wrong tool for money.
public struct Expense: Codable, Equatable, Identifiable {
    public var id: UUID
    public var amount: Decimal
    public var category: String
    public var note: String
    public var date: Date

    public init(
        id: UUID = UUID(),
        amount: Decimal,
        category: String,
        note: String,
        date: Date = Date()
    ) {
        self.id = id
        self.amount = amount
        self.category = category
        self.note = note
        self.date = date
    }
}

/// Date helpers. Dates are stored as ISO 8601 in JSON; users type
/// `yyyy-MM-dd` (and `yyyy-MM` for month filters).
public enum ExpenseDate {
    public static let dayFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    public static let monthFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM"
        return formatter
    }()

    /// Parses a `yyyy-MM-dd` date, or returns nil for anything else.
    public static func parseDay(_ string: String) -> Date? {
        dayFormatter.date(from: string)
    }

    public static func dayString(_ date: Date) -> String {
        dayFormatter.string(from: date)
    }

    public static func monthString(_ date: Date) -> String {
        monthFormatter.string(from: date)
    }
}

/// Money formatting — always US dollars, two decimal places, no space
/// between the symbol and the digits. (Built from a decimal formatter
/// plus "$" rather than `.currency`: the currency pattern varies by
/// platform and on Linux it renders "$ 12.50" with a space.)
public enum Money {
    public static func format(_ amount: Decimal) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.minimumFractionDigits = 2
        formatter.maximumFractionDigits = 2
        formatter.locale = Locale(identifier: "en_US_POSIX")
        let number = formatter.string(from: amount as NSDecimalNumber) ?? "\(amount)"
        return "$" + number
    }
}
