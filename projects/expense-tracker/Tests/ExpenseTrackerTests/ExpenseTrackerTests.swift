import XCTest
@testable import ExpenseTrackerLib

final class ExpenseTrackerTests: XCTestCase {

    private func makeExpense(
        amount: String = "10.00",
        category: String = "Food",
        note: String = "Test",
        day: String = "2026-11-05"
    ) -> Expense {
        Expense(
            amount: Decimal(string: amount)!,
            category: category,
            note: note,
            date: ExpenseDate.parseDay(day)!
        )
    }

    private func tempURL() -> URL {
        FileManager.default.temporaryDirectory
            .appendingPathComponent("expense-tracker-test-\(UUID().uuidString).json")
    }

    // MARK: - Adding

    func testAddExpenseIncreasesCount() {
        var store = ExpenseStore(fileURL: tempURL())
        XCTAssertEqual(store.expenses.count, 0)
        store.add(makeExpense())
        XCTAssertEqual(store.expenses.count, 1)
        XCTAssertEqual(store.expenses[0].note, "Test")
    }

    func testAddKeepsExpensesSortedByDate() {
        var store = ExpenseStore(fileURL: tempURL())
        store.add(makeExpense(day: "2026-11-09"))
        store.add(makeExpense(day: "2026-11-02"))
        XCTAssertEqual(ExpenseDate.dayString(store.expenses[0].date), "2026-11-02")
        XCTAssertEqual(ExpenseDate.dayString(store.expenses[1].date), "2026-11-09")
    }

    // MARK: - Totals

    func testTotalsByCategory() {
        var store = ExpenseStore(fileURL: tempURL())
        store.add(makeExpense(amount: "10.00", category: "Food"))
        store.add(makeExpense(amount: "5.00", category: "Food"))
        store.add(makeExpense(amount: "7.50", category: "Transport"))
        let totals = Dictionary(uniqueKeysWithValues: store.totalsByCategory().map { ($0.category, $0.total) })
        XCTAssertEqual(totals["Food"], Decimal(string: "15.00"))
        XCTAssertEqual(totals["Transport"], Decimal(string: "7.50"))
    }

    func testTotalsByMonth() {
        var store = ExpenseStore(fileURL: tempURL())
        store.add(makeExpense(amount: "10.00", day: "2026-10-31"))
        store.add(makeExpense(amount: "20.00", day: "2026-11-02"))
        store.add(makeExpense(amount: "5.00", day: "2026-11-15"))
        let totals = Dictionary(uniqueKeysWithValues: store.totalsByMonth().map { ($0.month, $0.total) })
        XCTAssertEqual(totals["2026-10"], Decimal(string: "10.00"))
        XCTAssertEqual(totals["2026-11"], Decimal(string: "25.00"))
    }

    func testEmptyStoreTotalsAreZero() {
        let store = ExpenseStore(fileURL: tempURL())
        XCTAssertEqual(store.total(), Decimal(0))
        XCTAssertTrue(store.totalsByCategory().isEmpty)
        XCTAssertTrue(store.totalsByMonth().isEmpty)
    }

    func testTotalsAreExactDecimals() {
        // 0.10 + 0.20 must be exactly 0.30 — the reason money is Decimal,
        // not Double.
        var store = ExpenseStore(fileURL: tempURL())
        store.add(makeExpense(amount: "0.10"))
        store.add(makeExpense(amount: "0.20"))
        XCTAssertEqual(store.total(), Decimal(string: "0.30"))
    }

    // MARK: - Filtering

    func testFilterByCategoryAndMonth() {
        var store = ExpenseStore(fileURL: tempURL())
        store.add(makeExpense(category: "Food", day: "2026-11-05"))
        store.add(makeExpense(category: "Transport", day: "2026-11-05"))
        store.add(makeExpense(category: "Food", day: "2026-10-20"))
        XCTAssertEqual(store.filtered(category: "Food").count, 2)
        XCTAssertEqual(store.filtered(month: "2026-11").count, 2)
        XCTAssertEqual(store.filtered(category: "Food", month: "2026-11").count, 1)
    }

    // MARK: - JSON persistence

    func testJSONRoundTrip() throws {
        let original = [makeExpense(), makeExpense(amount: "3.25", category: "Transport", day: "2026-11-06")]
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(original)
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let decoded = try decoder.decode([Expense].self, from: data)
        XCTAssertEqual(decoded, original)
    }

    func testStoreSaveLoadRoundTrip() throws {
        let url = tempURL()
        var store = ExpenseStore(fileURL: url)
        store.add(makeExpense())
        store.add(makeExpense(amount: "3.25", category: "Transport", day: "2026-11-06"))
        try store.save()
        let loaded = try ExpenseStore.load(from: url)
        XCTAssertEqual(loaded.expenses, store.expenses)
        try? FileManager.default.removeItem(at: url)
    }

    func testLoadMissingFileIsEmptyStore() throws {
        let loaded = try ExpenseStore.load(from: tempURL())
        XCTAssertTrue(loaded.expenses.isEmpty)
    }

    // MARK: - Dates and money

    func testDayParsingValidAndInvalid() {
        XCTAssertNotNil(ExpenseDate.parseDay("2026-11-05"))
        XCTAssertNil(ExpenseDate.parseDay("not-a-date"))
        XCTAssertNil(ExpenseDate.parseDay("11/05/2026"))
        XCTAssertEqual(ExpenseDate.dayString(ExpenseDate.parseDay("2026-11-05")!), "2026-11-05")
        XCTAssertEqual(ExpenseDate.monthString(ExpenseDate.parseDay("2026-11-05")!), "2026-11")
    }

    func testMoneyFormatting() {
        XCTAssertEqual(Money.format(Decimal(string: "12.50")!), "$12.50")
        XCTAssertEqual(Money.format(Decimal(string: "0")!), "$0.00")
    }

    // MARK: - Demo mode

    func testDemoModeHasFictionalSamples() {
        let demo = ExpenseStore.demoExpenses()
        XCTAssertEqual(demo.count, 6)
        let store = ExpenseStore(fileURL: tempURL(), expenses: demo)
        XCTAssertEqual(store.total(), Decimal(string: "96.55"))
        let byCategory = Dictionary(uniqueKeysWithValues: store.totalsByCategory().map { ($0.category, $0.total) })
        XCTAssertEqual(byCategory["Food"], Decimal(string: "67.55"))
        XCTAssertEqual(byCategory["Transport"], Decimal(string: "17.00"))
        XCTAssertEqual(byCategory["Entertainment"], Decimal(string: "12.00"))
    }

    func testReportContainsTotals() {
        let store = ExpenseStore(fileURL: tempURL(), expenses: ExpenseStore.demoExpenses())
        let report = store.fullReport()
        XCTAssertTrue(report.contains("Food: $67.55"))
        XCTAssertTrue(report.contains("2026-11: $96.55"))
        XCTAssertTrue(report.contains("Total: $96.55"))
    }
}
