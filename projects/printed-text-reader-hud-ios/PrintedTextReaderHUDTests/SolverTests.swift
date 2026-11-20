import XCTest
@testable import PrintedTextReaderHUD

// My solver's ground-truth tests — the same questions James has run
// through the web prototype, with the answers he confirmed. The solver
// answers by choice TEXT, never by letter, so each case passes the
// options in their printed order and the expected letter is the one
// that text sits under.

final class SolverTests: XCTestCase {
    var solver: Solver!

    override func setUp() {
        super.setUp()
        solver = Solver()
        solver.wikiFetcher = nil
        solver.dictionaryFetcher = nil
    }

    private func mc(_ stem: String, _ options: [String]) -> (String, [ChoiceOption]) {
        let letters = ["A", "B", "C", "D", "E"]
        return (stem, zip(letters, options).map { ChoiceOption(letter: $0, text: $1) })
    }

    private func solveMC(_ stem: String, _ options: [String]) async -> SolveResult {
        let (_, opts) = mc(stem, options)
        let block = ParsedQuestion(stem: stem, options: opts)
        // Solve through the same path the app uses: raw block text.
        let raw = stem + "\n" + zip(["A", "B", "C", "D", "E"], options)
            .map { "\($0). \($1)" }.joined(separator: "\n")
        let results = await solver.solve(raw)
        XCTAssertEqual(results.count, 1, "expected one block for: \(stem)")
        _ = block
        return results.first!.result
    }

    // MARK: - Maths

    func testTwelveTimesSix() async {
        let r = await solveMC("What is 12 × 6?", ["60", "66", "72", "76"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "C")
        XCTAssertEqual(r.answerText, "72")
    }

    func testQuarterPlusQuarter() async {
        let r = await solveMC("What is 1/4 + 1/4?", ["1/8", "1/4", "2/8", "1/2"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "D")
        XCTAssertEqual(r.answerText, "1/2")
    }

    func testRunnerSpeed() async {
        let r = await solveMC(
            "A runner completed a 42-kilometer marathon in 3 hours and 30 minutes. What was her average speed in kilometers per hour?",
            ["10 km/h", "12 km/h", "14 km/h", "16 km/h"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "B")
    }

    func testCandlesProfit() async {
        let r = await solveMC(
            "Mia buys 8 boxes of candles for $15 each. If each box contains 12 candles and she sells all the candles individually for $2 each, what is her total profit?",
            ["$72", "$96", "$120", "$192"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "A")
    }

    func testDivision782() async {
        let r = await solveMC("What is 782 ÷ 23?", ["32", "33", "34", "35"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "C")
    }

    func testOrderOfOperations() async {
        let r = await solveMC("What is 50 − 4 × (3 + 5) + 12?", ["20", "26", "28", "30"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "D")
    }

    func testFactoryPacks() async {
        let r = await solveMC(
            "A factory packs 480 juice boxes into packs of 24. How many packs are there?",
            ["12", "16", "18", "20"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.answerText, "20")
    }

    func testFarmerApples() async {
        let r = await solveMC(
            "A farmer harvested 168 apples and packed them equally into 7 baskets. How many apples are in each basket?",
            ["20", "22", "24", "26"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.answerText, "24")
    }

    func testLibraryShelves() async {
        let r = await solveMC(
            "A library has 8 bookshelves, and each shelf holds 45 books. How many books are there in total?",
            ["320", "340", "360", "380"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "C")
    }

    func testDivision432() async {
        let r = await solveMC("What is 432 ÷ 12?", ["34", "36", "38", "40"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "B")
    }

    func testTwentyFourTimesSixteen() async {
        let r = await solveMC("What is 24 × 16?", ["360", "372", "380", "384"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "D")
    }

    func testSubtraction852() async {
        let r = await solveMC("What is 852 − 397?", ["455", "445", "465", "555"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "A")
    }

    func testAddition348() async {
        let r = await solveMC("What is 348 + 276?", ["614", "616", "624", "634"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "C")
    }

    func testMarkChange() async {
        let r = await solveMC(
            "Mark buys 4 packs of notebooks for $8 each and 3 pens for $2 each. If he pays with a $50 bill, how much change should he receive?",
            ["$12", "$14", "$16", "$38"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "A")
    }

    func testTheaterTickets() async {
        let r = await solveMC(
            "A theater company has 1,242 tickets to sell evenly across 27 performances. How many tickets are sold at each performance?",
            ["42", "44", "45", "46"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "D")
    }

    func testDivision945() async {
        let r = await solveMC("What is 945 ÷ 15?", ["61", "63", "65", "67"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "B")
    }

    func testOrchard() async {
        let r = await solveMC(
            "An orchard has 16 rows of trees with 14 trees in each row. How many trees are there in total?",
            ["224", "216", "228", "230"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "A")
    }

    func testLibraryCheckout() async {
        let r = await solveMC(
            "The library had 420 books. 157 books were returned. How many books are left?",
            ["253", "257", "263", "273"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "C")
    }

    func testSarahCards() async {
        let r = await solveMC(
            "Sarah has 145 cards. She buys 88 more cards. How many cards does she have now?",
            ["223", "233", "243", "253"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "B")
    }

    // MARK: - Sentence-form maths

    func testTwelveDividedByThree() async {
        let r = await solveMC("What is twelve divided by three?", ["3", "4", "5", "6"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "B")
        XCTAssertNotNil(r.readAs)
    }

    func testSubtractFrom() async {
        let r = await solveMC("What is subtract 3 from 10?", ["6", "7", "8", "13"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "B")
    }

    // MARK: - Fact bank

    func testPokemonNotDragon() async {
        let r = await solveMC(
            "Which of the following Pokémon is NOT a Dragon-type?",
            ["Flygon", "Kingdra", "Haxorus", "Charizard"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "D")
        XCTAssertEqual(r.answerText, "Charizard")
    }

    func testPokemonRainbow() async {
        let r = await solveMC(
            "In the very first episode of the anime ('Pokémon, I Choose You!'), which legendary Pokémon does Ash catch a glimpse of flying across the rainbow?",
            ["Lugia", "Articuno", "Ho-Oh", "Zapdos"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "C")
        XCTAssertEqual(r.answerText, "Ho-Oh")
    }

    func testHonestAbe() async {
        let r = await solveMC(
            "Who was famously nicknamed 'Honest Abe'?",
            ["Andrew Jackson", "Ulysses S. Grant", "Theodore Roosevelt", "Abraham Lincoln"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "D")
        XCTAssertEqual(r.answerText, "Abraham Lincoln")
    }

    func testCapitalOfFrance() async {
        let r = await solveMC("What is the capital of France?", ["London", "Madrid", "Paris", "Rome"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "C")
        XCTAssertEqual(r.answerText, "Paris")
    }

    func testResidualRisk() async {
        let r = await solveMC(
            "Who formally accepts residual risk?",
            ["Data custodian", "Data owner", "Senior management", "Security analyst"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "C")
        XCTAssertEqual(r.answerText, "Senior management")
    }

    // MARK: - Shuffle safety: the same answer under a new letter

    func testShuffledPokemonRainbow() async {
        // Ho-Oh moves from C to B — the answer must follow the text.
        let r = await solveMC(
            "In the very first episode of the anime ('Pokémon, I Choose You!'), which legendary Pokémon does Ash catch a glimpse of flying across the rainbow?",
            ["Lugia", "Ho-Oh", "Articuno", "Zapdos"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "B")
        XCTAssertEqual(r.answerText, "Ho-Oh")
    }

    func testShuffledNotDragon() async {
        let r = await solveMC(
            "Which of the following Pokémon is NOT a Dragon-type?",
            ["Charizard", "Flygon", "Kingdra", "Haxorus"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "A")
        XCTAssertEqual(r.answerText, "Charizard")
    }

    // MARK: - Fill-in repair

    func testFillInGarbledDragonQuestion() {
        let stem = "Whig ib the rote Mhcramon is NOT a Dragon-type?"
        let repaired = fillInQuestion(stem, choices: [
            ChoiceOption(letter: "A", text: "Flygon"),
            ChoiceOption(letter: "B", text: "Kingdra"),
            ChoiceOption(letter: "C", text: "Haxorus"),
            ChoiceOption(letter: "D", text: "Charizard"),
        ])
        XCTAssertNotNil(repaired)
        XCTAssertTrue(repaired!.hasPrefix("Which"))
        // Unrecoverable words are left alone, never rewritten wrong.
        XCTAssertTrue(repaired!.contains("Mhcramon"))
    }

    func testFillInNeverRewritesCleanReads() {
        XCTAssertNil(fillInQuestion("Which of the following Pokémon is NOT a Dragon-type?"))
        XCTAssertNil(fillInQuestion("What is 12 × 6?"))
    }

    func testGarbledDragonQuestionStillSolves() async {
        let r = await solveMC(
            "Whig ib the rote Mhcramon is NOT a Dragon-type?",
            ["Flygon", "Kingdra", "Haxorus", "Charizard"])
        XCTAssertEqual(r.status, .solved)
        XCTAssertEqual(r.letter, "D")
        XCTAssertNotNil(r.filledInQuestion)
    }

    // MARK: - Segmentation

    func testSplitTwoQuestions() {
        let blocks = splitQuestions("""
        1. What is 12 × 6?
        A. 60
        B. 66
        C. 72
        D. 76
        2. What is the capital of France?
        A. London
        B. Madrid
        C. Paris
        D. Rome
        """)
        XCTAssertEqual(blocks.count, 2)
    }

    func testCutToQuestionDropsFurniture() {
        let stem = "Multi-digit Division Quiz 3 / 5 4. A farmer harvested 168 apples. How many are in each basket?"
        let cut = cutToQuestion(stem)
        XCTAssertFalse(cut.contains("Quiz"))
        XCTAssertFalse(cut.contains("3 / 5"))
        XCTAssertTrue(cut.hasPrefix("A farmer"))
    }

    func testParseOptionsTwoPerRow() {
        let parsed = parseOptions("What is 12 × 6? A. 60 B. 66 C. 72 D. 76")
        XCTAssertNotNil(parsed)
        XCTAssertEqual(parsed!.options.count, 4)
        XCTAssertEqual(parsed!.options[2].text, "72")
    }
}
