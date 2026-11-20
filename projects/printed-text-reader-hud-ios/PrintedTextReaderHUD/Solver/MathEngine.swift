// MathEngine.swift
// My maths engine: a safe recursive-descent parser (never eval), a
// printed-expression finder, sentence-form maths ("twelve divided by
// three", "subtract 3 from 10"), and story problems (equal sharing,
// packing into groups, profit, speed, change from a bill).
// Ported from my web prototype's engine — same rules, same order:
// percent, solve-for-x, word maths, strong story shapes, printed
// expression, then the weaker story fallback. Maths is computed, never
// guessed: a worked answer that matches no printed choice is
// re-analysed against the choices, never force-fit.

import Foundation

// MARK: - Safe expression parser (no eval)

/// Recursive-descent parser for + − × ÷ ^ ( ) and %. Throws on bad input.
public struct ExprParser {
    private let chars: [Character]
    private var i = 0

    public init(_ s: String) { chars = Array(s) }

    public mutating func run() throws -> Double {
        let v = try parseExpression()
        skipSpaces()
        guard i >= chars.count else { throw MathError.trailing }
        return v
    }

    private mutating func skipSpaces() { while i < chars.count && chars[i] == " " { i += 1 } }
    private func peek() -> Character? { i < chars.count ? chars[i] : nil }

    private mutating func parseExpression() throws -> Double {
        var v = try parseTerm()
        while true {
            skipSpaces()
            if peek() == "+" { i += 1; v += try parseTerm() }
            else if peek() == "-" { i += 1; v -= try parseTerm() }
            else { return v }
        }
    }

    private mutating func parseTerm() throws -> Double {
        var v = try parsePower()
        while true {
            skipSpaces()
            if peek() == "*" { i += 1; v *= try parsePower() }
            else if peek() == "/" { i += 1; v /= try parsePower() }
            else { return v }
        }
    }

    private mutating func parsePower() throws -> Double {
        var v = try parseUnary()
        skipSpaces()
        if peek() == "^" { i += 1; v = pow(v, try parsePower()) }
        return v
    }

    private mutating func parseUnary() throws -> Double {
        skipSpaces()
        if peek() == "-" { i += 1; return -(try parseUnary()) }
        if peek() == "+" { i += 1; return try parseUnary() }
        var v = try parsePrimary()
        while true {
            skipSpaces()
            if peek() == "%" { i += 1; v = v / 100 } else { break }
        }
        return v
    }

    private mutating func parsePrimary() throws -> Double {
        skipSpaces()
        if peek() == "(" {
            i += 1
            let v = try parseExpression()
            skipSpaces()
            if peek() == ")" { i += 1 }
            return v
        }
        var num = ""
        while let c = peek(), c.isNumber || c == "." { num.append(c); i += 1 }
        guard let v = Double(num) else { throw MathError.badToken }
        return v
    }

    public enum MathError: Error { case badToken, trailing }
}

/// The result of working a maths question: its value, where it came
/// from, and how to show the working.
public struct MathWork {
    public let value: Double
    /// "expr" | "word" | "pct" | "linear"
    public let source: String
    public let reason: String
    /// "12 ÷ 3" style label for the READ AS line.
    public let readAs: String?
    /// (a, operator words, b) for highlighting the calculation words.
    public let highlight: HighlightOperands?
    public let isX: Bool
    /// The operator between fractions was lost in the read — flag it.
    public let suspect: Bool

    public struct HighlightOperands {
        public let a: Double
        public let op: String?
        public let b: Double?
    }
}

// MARK: - Printed expressions

/// Find the longest printed calculation in the text ("12x6", "50 − 4 ×
/// (3 + 5) + 12", "1/4 + 1/4"). A letter x between digits, a number or
/// bracket against a bracket, and × ÷ − are all normalised first.
public func findExpression(_ text: String) -> (expr: String, value: Double)? {
    var norm = text.replacingOccurrences(of: ",", with: "")
    norm = regexReplace(#"(\d)\s*[xX]\s*(?=[\d(])"#, in: norm, with: "$1*")
    norm = regexReplace(#"\)\s*[xX]\s*(?=[\d(])"#, in: norm, with: ")*")
    norm = regexReplace(#"(\d)\s*[·•]\s*(?=[\d(])"#, in: norm, with: "$1*")
    norm = regexReplace(#"(\d)\s*(?=\()"#, in: norm, with: "$1*")
    norm = regexReplace(#"\)\s*(?=\()"#, in: norm, with: ")*")
    let t = " " + norm.replacingOccurrences(of: "×", with: "*").replacingOccurrences(of: "✕", with: "*")
        .replacingOccurrences(of: "÷", with: "/")
        .replacingOccurrences(of: "−", with: "-").replacingOccurrences(of: "–", with: "-")
        .replacingOccurrences(of: "—", with: "-") + " "
    let pattern = #"\(?\s*\d+(?:\.\d+)?\s*(?:[+\-*/^]\s*\(?\s*\d+(?:\.\d+)?\s*\)?\s*)+"#
    var best: String?
    for m in allMatches(pattern, in: t) {
        let cand = m[0].trimmingCharacters(in: .whitespaces)
        if regexContains(#"[+\-*/^]"#, in: cand) && (best == nil || cand.count > best!.count) {
            best = cand
        }
    }
    guard var cand = best else { return nil }
    var open = 0, close = 0
    for c in cand { if c == "(" { open += 1 }; if c == ")" { close += 1 } }
    while close > open && cand.hasSuffix(")") { cand = String(cand.dropLast()); close -= 1 }
    while let last = cand.last, "+-*/^.( ".contains(last) { cand = String(cand.dropLast()) }
    var parser = ExprParser(cand)
    guard let v = try? parser.run(), v.isFinite else { return nil }
    return (cand, v)
}

private func percentOf(_ text: String) -> (pct: Double, n: Double, value: Double)? {
    guard let m = firstMatch(#"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)"#, in: text.replacingOccurrences(of: ",", with: ""), options: [.caseInsensitive]),
          let p = Double(m[1]), let n = Double(m[2]) else { return nil }
    return (p, n, p / 100 * n)
}

private func solveLinear(_ text: String) -> (a: Double, b: Double, c: Double, value: Double, form: String)? {
    let t = text.replacingOccurrences(of: ",", with: "")
        .replacingOccurrences(of: "−", with: "-").replacingOccurrences(of: "–", with: "-")
        .replacingOccurrences(of: "—", with: "-")
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\s*x\s*([+\-])\s*(\d+(?:\.\d+)?)\s*=\s*(-?\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let a = Double(m[1]), let bMag = Double(m[3]), let c = Double(m[4]), a != 0 {
        let b = bMag * (m[2] == "-" ? -1 : 1)
        return (a, b, c, (c - b) / a, "ab")
    }
    if let m = firstMatch(#"x\s*([+\-])\s*(\d+(?:\.\d+)?)\s*=\s*(-?\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let bMag = Double(m[2]), let c = Double(m[3]) {
        let b = bMag * (m[1] == "-" ? -1 : 1)
        return (1, b, c, c - b, "b")
    }
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\s*x\s*=\s*(-?\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let a = Double(m[1]), let c = Double(m[2]), a != 0 {
        return (a, 0, c, c / a, "a")
    }
    return nil
}

// MARK: - Number words

public let numberWords: [String: Double] = [
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90
]

/// "twenty-one" and "twenty one" both become 21; single number words
/// become their digits.
public func wordsToDigits(_ t: String) -> String {
    var out = t
    // NSRegularExpression templates cannot add numbers, so the compound
    // forms ("twenty-one" -> 21) are scanned explicitly.
    out = replaceCompoundNumberWords(out)
    for word in numberWords.keys.sorted(by: { $0.count > $1.count }) {
        let pattern = "\\b" + NSRegularExpression.escapedPattern(for: word) + "\\b"
        out = regexReplace(pattern, in: out, with: "\(Int(numberWords[word]!))", options: [.caseInsensitive])
    }
    return out
}

private func replaceCompoundNumberWords(_ t: String) -> String {
    var result = t
    let tens = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    let ones = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    for ten in tens {
        for one in ones {
            for sep in ["-", " "] {
                let needle = ten + sep + one
                let value = Int(numberWords[ten]! + numberWords[one]!)
                result = regexReplace("\\b" + NSRegularExpression.escapedPattern(for: needle) + "\\b",
                                      in: result, with: "\(value)", options: [.caseInsensitive])
            }
        }
    }
    return result
}

private func tokenValue(_ tok: String) -> Double? {
    if tok.first?.isNumber == true { return Double(tok) }
    let parts = tok.lowercased().split(separator: "-")
    var sum = 0.0
    for p in parts {
        guard let v = numberWords[String(p)] else { return nil }
        sum += v
    }
    return parts.isEmpty ? nil : sum
}

/// Pin down the calculation inside a sentence-form stem: the span from
/// the first operand through the operator words to the second operand.
/// Returns character offsets into the stem, or nil.
public func findHighlightSpan(in text: String, a: Double, op: String?, b: Double?) -> (Int, Int)? {
    let chars = Array(text)
    // Tokenise: words (possibly hyphenated) and numbers, with offsets.
    struct Tok { let s: Int; let e: Int; let v: Double? }
    var toks: [Tok] = []
    var idx = 0
    while idx < chars.count {
        let c = chars[idx]
        if c.isLetter || c.isNumber {
            var j = idx
            while j < chars.count && (chars[j].isLetter || chars[j].isNumber || chars[j] == "." || chars[j] == "-") {
                // A hyphen only counts inside a word, not as a minus sign.
                if chars[j] == "-" && (j == idx || !(chars[j - 1].isLetter)) { break }
                if chars[j] == "." && (j + 1 >= chars.count || !chars[j + 1].isNumber) { break }
                j += 1
            }
            let word = String(chars[idx..<j])
            toks.append(Tok(s: idx, e: j, v: tokenValue(word)))
            idx = j
        } else {
            idx += 1
        }
    }
    guard let ia = toks.firstIndex(where: { $0.v != nil && abs($0.v! - a) < 1e-9 }) else { return nil }
    var start = toks[ia].s
    var end = toks[ia].e
    if let op = op, !op.isEmpty {
        let esc = NSRegularExpression.escapedPattern(for: op).replacingOccurrences(of: " ", with: "\\s+")
        if let re = try? NSRegularExpression(pattern: esc, options: [.caseInsensitive]) {
            let range = NSRange(text.startIndex..., in: text)
            if let m = re.firstMatch(in: text, options: [], range: range) {
                let os = text.distance(from: text.startIndex, to: String.Index(utf16Offset: m.range.location, in: text))
                let oe = os + text.distance(from: String.Index(utf16Offset: m.range.location, in: text),
                                            to: String.Index(utf16Offset: m.range.location + m.range.length, in: text))
                if os < start && oe >= start - 2 { start = os }
                if os >= toks[ia].s && oe > end { end = oe }
            }
        }
    }
    if let b = b {
        var foundB = false
        for j in (ia + 1)..<toks.count where toks[j].v != nil && abs(toks[j].v! - b) < 1e-9 {
            end = toks[j].e; foundB = true; break
        }
        if !foundB {
            // "Subtract 3 from 10": the second operand is named first.
            for j in (0..<ia).reversed() where toks[j].v != nil && abs(toks[j].v! - b) < 1e-9 {
                start = min(start, toks[j].s); break
            }
        }
    }
    return end > start ? (start, end) : nil
}

// MARK: - Maths in words

private struct WordPattern {
    let pattern: String
    let symbol: String
    let compute: (Double, Double) -> Double
    /// True for "subtract A from B", where the calculation runs B − A.
    let swap: Bool
}

private func wordMath(_ text: String) -> MathWork? {
    let t = wordsToDigits(text.replacingOccurrences(of: ",", with: ""))
    let pats: [WordPattern] = [
        WordPattern(pattern: #"sum of\s+(-?\d+(?:\.\d+)?)\s+(and)\s+(-?\d+(?:\.\d+)?)"#, symbol: "+", compute: +, swap: false),
        WordPattern(pattern: #"product of\s+(-?\d+(?:\.\d+)?)\s+(and)\s+(-?\d+(?:\.\d+)?)"#, symbol: "×", compute: *, swap: false),
        WordPattern(pattern: #"difference between\s+(-?\d+(?:\.\d+)?)\s+(and)\s+(-?\d+(?:\.\d+)?)"#, symbol: "−", compute: -, swap: false),
        WordPattern(pattern: #"quotient of\s+(-?\d+(?:\.\d+)?)\s+(and)\s+(-?\d+(?:\.\d+)?)"#, symbol: "÷", compute: /, swap: false),
        WordPattern(pattern: #"(\d+(?:\.\d+)?)\s+(divided\s+by)\s+(\d+(?:\.\d+)?)"#, symbol: "÷", compute: /, swap: false),
        WordPattern(pattern: #"(?:divide|dividing)\s+(\d+(?:\.\d+)?)\s+(by)\s+(\d+(?:\.\d+)?)"#, symbol: "÷", compute: /, swap: false),
        WordPattern(pattern: #"(\d+(?:\.\d+)?)\s+(plus)\s+(\d+(?:\.\d+)?)"#, symbol: "+", compute: +, swap: false),
        WordPattern(pattern: #"(?:add|adding)\s+(\d+(?:\.\d+)?)\s+(and|to)\s+(\d+(?:\.\d+)?)"#, symbol: "+", compute: +, swap: false),
        WordPattern(pattern: #"(\d+(?:\.\d+)?)\s+(minus)\s+(\d+(?:\.\d+)?)"#, symbol: "−", compute: -, swap: false),
        WordPattern(pattern: #"(\d+(?:\.\d+)?)\s+(take\s+away)\s+(\d+(?:\.\d+)?)"#, symbol: "−", compute: -, swap: false),
        WordPattern(pattern: #"(?:subtract|subtracting)\s+(\d+(?:\.\d+)?)\s+(from)\s+(\d+(?:\.\d+)?)"#, symbol: "−", compute: { a, b in b - a }, swap: true),
        WordPattern(pattern: #"(\d+(?:\.\d+)?)\s+(times)\s+(\d+(?:\.\d+)?)"#, symbol: "×", compute: *, swap: false),
        WordPattern(pattern: #"(\d+(?:\.\d+)?)\s+(multiplied\s+by)\s+(\d+(?:\.\d+)?)"#, symbol: "×", compute: *, swap: false),
        WordPattern(pattern: #"(?:multiply|multiplying)\s+(\d+(?:\.\d+)?)\s+(by)\s+(\d+(?:\.\d+)?)"#, symbol: "×", compute: *, swap: false),
    ]
    for p in pats {
        guard let m = firstMatch(p.pattern, in: t, options: [.caseInsensitive]),
              let a = Double(m[1]), let b = Double(m[3]) else { continue }
        let v = p.compute(a, b)
        guard v.isFinite else { continue }
        let first = p.swap ? b : a, second = p.swap ? a : b
        let label = "\(fmtNum(first)) \(p.symbol) \(fmtNum(second))"
        return MathWork(value: v, source: "word",
                        reason: "In words: \(label) = \(fmtMathValue(v)).",
                        readAs: "\(label) = \(fmtMathValue(v))",
                        highlight: .init(a: first, op: m[2], b: second),
                        isX: false, suspect: false)
    }
    if let hf = firstMatch(#"\b(half)\s+of\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let n = Double(hf[2]) {
        return MathWork(value: n / 2, source: "word",
                        reason: "In words: \(fmtNum(n)) ÷ 2 = \(fmtMathValue(n / 2)).",
                        readAs: "\(fmtNum(n)) ÷ 2 = \(fmtMathValue(n / 2))",
                        highlight: .init(a: n, op: "half of", b: nil), isX: false, suspect: false)
    }
    if let qt = firstMatch(#"\b(quarter)\s+of\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let n = Double(qt[2]) {
        return MathWork(value: n / 4, source: "word",
                        reason: "In words: \(fmtNum(n)) ÷ 4 = \(fmtMathValue(n / 4)).",
                        readAs: "\(fmtNum(n)) ÷ 4 = \(fmtMathValue(n / 4))",
                        highlight: .init(a: n, op: "quarter of", b: nil), isX: false, suspect: false)
    }
    if let sq = firstMatch(#"(\d+(?:\.\d+)?)\s+squared"#, in: t, options: [.caseInsensitive]),
       let n = Double(sq[1]) {
        return MathWork(value: n * n, source: "word",
                        reason: "In words: \(fmtNum(n))² = \(fmtMathValue(n * n)).",
                        readAs: "\(fmtNum(n))² = \(fmtMathValue(n * n))",
                        highlight: .init(a: n, op: "squared", b: nil), isX: false, suspect: false)
    }
    if let sr = firstMatch(#"square root of\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let n = Double(sr[1]) {
        return MathWork(value: n.squareRoot(), source: "word",
                        reason: "In words: √\(fmtNum(n)) = \(fmtMathValue(n.squareRoot())).",
                        readAs: "√\(fmtNum(n)) = \(fmtMathValue(n.squareRoot()))",
                        highlight: .init(a: n, op: "square root of", b: nil), isX: false, suspect: false)
    }
    return nil
}

// MARK: - Story problems

/// Story problems: the numbers and the operation are spread across
/// sentences. The strong shapes (unmistakable wording) run before the
/// printed-expression scan; the weak two-number fallback only runs after
/// it, and only when the text holds exactly two numbers.
public func wordProblemMath(_ text: String, strongOnly: Bool = false) -> MathWork? {
    var t = wordsToDigits(text.replacingOccurrences(of: ",", with: ""))
    // A leading question number ("4. A farmer harvested 168…") is not
    // one of the problem's numbers.
    t = regexReplace(#"(^|\n)\s*(?:question\s*)?\d{1,3}\s*[\)\.\:]\s*"#, in: t, with: "$1", options: [.caseInsensitive])

    func story(_ label: String, _ value: Double, a: Double, op: String, b: Double?) -> MathWork {
        MathWork(value: value, source: "word",
                 reason: "In words: \(label) = \(fmtMathValue(value)).",
                 readAs: "\(label) = \(fmtMathValue(value))",
                 highlight: .init(a: a, op: op, b: b), isX: false, suspect: false)
    }

    // Equal sharing, named verb: "shares them equally among 4 friends".
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\b((?:shared|shares|sharing|split|divided|distribute|distributed)\b[^?]*?\b(?:equally|evenly)\b[^?]*?\b(?:among|between|into|across))\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let total = Double(m[1]), let count = Double(m[3]), count != 0 {
        return story("\(fmtNum(total)) ÷ \(fmtNum(count))", total / count, a: total, op: m[2], b: count)
    }
    // Equal sharing with ANY verb: "packed them equally into 7
    // baskets", "sell evenly across 27 performances".
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\b(?:equally|evenly)\b[^?]*?\b(?:into|among|between|across)\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let total = Double(m[1]), let count = Double(m[2]), count != 0 {
        return story("\(fmtNum(total)) ÷ \(fmtNum(count))", total / count, a: total, op: "equally", b: count)
    }
    // Packing: "packs 480 juice boxes into packs of 24" is 480 ÷ 24.
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\binto\s+(packs|groups|boxes|baskets|bags|bundles|rows|teams|piles|trays)\s+of\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let total = Double(m[1]), let size = Double(m[3]), size != 0 {
        return story("\(fmtNum(total)) ÷ \(fmtNum(size))", total / size, a: total, op: m[2] + " of", b: size)
    }
    // Profit: cost vs revenue, all four figures must be present.
    if regexContains(#"\bprofit\b"#, in: t, options: [.caseInsensitive]),
       let buyN = firstMatch(#"\bbuys?\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let costEach = firstMatch(#"\bfor\s+\$?\s*(\d+(?:\.\d+)?)\s+each\b"#, in: t, options: [.caseInsensitive]),
       let perBox = firstMatch(#"\b(?:contains|holds|has)\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let sellEach = firstMatch(#"\bsells?\b[^.]*?\$?\s*(\d+(?:\.\d+)?)\s+each\b"#, in: t, options: [.caseInsensitive]),
       let bn = Double(buyN[1]), let ce = Double(costEach[1]),
       let pb = Double(perBox[1]), let se = Double(sellEach[1]) {
        let rev = bn * pb * se, cost = bn * ce
        return story("\(fmtNum(bn)) × \(fmtNum(pb)) × $\(fmtNum(se)) − \(fmtNum(bn)) × $\(fmtNum(ce))", rev - cost, a: bn, op: "profit", b: pb)
    }
    // Change from a bill: "pays with a $50 bill" minus every
    // "N items for $P each" group.
    if regexContains(#"\bchange\b"#, in: t, options: [.caseInsensitive]),
       let paidM = firstMatch(#"\bpays?\s+with\s+(?:a\s+)?\$?\s*(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let paidV = Double(paidM[1]) {
        var totalCost = 0.0, pairCount = 0
        for pm in allMatches(#"(\d+(?:\.\d+)?)\s+[a-z][^$]*?\$(\d+(?:\.\d+)?)\s+each\b"#, in: t, options: [.caseInsensitive]) {
            if let q = Double(pm[1]), let p = Double(pm[2]) { totalCost += q * p; pairCount += 1 }
        }
        if pairCount > 0 {
            return story("$\(fmtNum(paidV)) − $\(fmtNum(totalCost))", paidV - totalCost, a: paidV, op: "pays with", b: nil)
        }
    }
    // Speed: distance ÷ time, time folded into hours.
    if regexContains(#"\b(average\s+)?speed\b|\bper\s+hour\b"#, in: t, options: [.caseInsensitive]),
       let distM = firstMatch(#"(\d+(?:\.\d+)?)\s*(?:-\s*|\s)?(?:kilometers?|kilometres?|km|miles?|mi)\b"#, in: t, options: [.caseInsensitive]),
       let dist = Double(distM[1]) {
        var hrs: Double?
        if let hm = firstMatch(#"(\d+(?:\.\d+)?)\s*hours?\s+and\s+(\d+(?:\.\d+)?)\s*minutes?"#, in: t, options: [.caseInsensitive]),
           let h = Double(hm[1]), let m = Double(hm[2]) {
            hrs = h + m / 60
        } else if let hOnly = firstMatch(#"(\d+(?:\.\d+)?)\s*hours?"#, in: t, options: [.caseInsensitive]),
                  let h = Double(hOnly[1]) {
            hrs = h
        } else if let mOnly = firstMatch(#"(\d+(?:\.\d+)?)\s*minutes?"#, in: t, options: [.caseInsensitive]),
                  let m = Double(mOnly[1]) {
            hrs = m / 60
        }
        if let hrs = hrs, hrs != 0 {
            return story("\(fmtNum(dist)) ÷ \(fmtNum(hrs))", dist / hrs, a: dist, op: "in", b: hrs)
        }
    }
    // Per-container multiplication: "8 shelves, each holds 45 books".
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\beach\b[^?\d]*?\b(?:holds|contains|has|carries|fits)\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let n1 = Double(m[1]), let n2 = Double(m[2]) {
        return story("\(fmtNum(n1)) × \(fmtNum(n2))", n1 * n2, a: n1, op: "each", b: n2)
    }
    // "puts 168 apples into 7 baskets" (no "equally", no "of").
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\binto\s+(\d+(?:\.\d+)?)\s*(?:baskets|boxes|bags|groups|packs|rows|teams|piles|trays|shelves)\b"#, in: t, options: [.caseInsensitive]),
       let total = Double(m[1]), let count = Double(m[2]), count != 0 {
        return story("\(fmtNum(total)) ÷ \(fmtNum(count))", total / count, a: total, op: "into", b: count)
    }
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\b((?:groups|piles|rows|baskets|boxes)\s+of)\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let total = Double(m[1]), let size = Double(m[3]), size != 0 {
        return story("\(fmtNum(total)) ÷ \(fmtNum(size))", total / size, a: total, op: m[2], b: size)
    }
    // "buys 88 more" / "gives away 5" / "returned 157".
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\b(buys|bought|gets|got|receives|received|finds|found|picks|picked|earns|earned|wins|won|collects|collected)\s+(\d+(?:\.\d+)?)\s+more\b"#, in: t, options: [.caseInsensitive]),
       let n1 = Double(m[1]), let n2 = Double(m[3]) {
        return story("\(fmtNum(n1)) + \(fmtNum(n2))", n1 + n2, a: n1, op: m[2], b: n2)
    }
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\b(gives away|gave away|gives|gave|loses|lost|eats|ate|sells|sold|uses|used|drops|dropped|returned|returns)\s+(\d+(?:\.\d+)?)"#, in: t, options: [.caseInsensitive]),
       let n1 = Double(m[1]), let n2 = Double(m[3]) {
        return story("\(fmtNum(n1)) − \(fmtNum(n2))", n1 - n2, a: n1, op: m[2], b: n2)
    }
    // "How many are left?" — a total with some taken away.
    if let m = firstMatch(#"(\d+(?:\.\d+)?)\b[^?]*?\b(left|remaining|remains|still)\b"#, in: t, options: [.caseInsensitive]),
       let n1 = Double(m[1]) {
        let nums = (allMatches(#"\d+(?:\.\d+)?"#, in: t).compactMap { Double($0[0]) })
        if nums.count == 2 {
            let other = nums[0] == n1 ? nums[1] : nums[0]
            return story("\(fmtNum(max(n1, other))) − \(fmtNum(min(n1, other)))", max(n1, other) - min(n1, other), a: max(n1, other), op: m[2], b: min(n1, other))
        }
    }
    if strongOnly { return nil }
    // Last-resort two-number story shapes. Only fires when the text
    // holds exactly two numbers.
    let nums = allMatches(#"\d+(?:\.\d+)?"#, in: t).compactMap { Double($0[0]) }
    if nums.count == 2 {
        let a = nums[0], b = nums[1]
        if regexContains(#"\b(each|per|every)\b"#, in: t, options: [.caseInsensitive]) &&
           regexContains(#"\b(total|altogether|in all)\b"#, in: t, options: [.caseInsensitive]) {
            return story("\(fmtNum(a)) × \(fmtNum(b))", a * b, a: a, op: "each", b: b)
        }
        if regexContains(#"\bin each\b|\bper\b"#, in: t, options: [.caseInsensitive]) && a != b {
            let big = max(a, b), small = min(a, b)
            if small != 0 {
                return story("\(fmtNum(big)) ÷ \(fmtNum(small))", big / small, a: big, op: "each", b: small)
            }
        }
        if regexContains(#"\b(total|altogether|in all)\b"#, in: t, options: [.caseInsensitive]) {
            return story("\(fmtNum(a)) + \(fmtNum(b))", a + b, a: a, op: "and", b: b)
        }
    }
    return nil
}

// MARK: - Top-level maths entry

/// Work a maths question from its stem, or nil when it is not maths.
/// Order: percent, solve-for-x, word maths, strong story shapes,
/// printed expression, weak story fallback.
public func mathAnswer(_ text: String) -> MathWork? {
    if let po = percentOf(text) {
        return MathWork(value: po.value, source: "pct",
                        reason: "\(fmtNum(po.pct))% of \(fmtNum(po.n)) = \(fmtNum(po.pct)) ÷ 100 × \(fmtNum(po.n)) = \(fmtNum(po.value)).",
                        readAs: nil, highlight: nil, isX: false, suspect: false)
    }
    if let lin = solveLinear(text) {
        let steps: String
        if lin.form == "a" {
            steps = "x = \(fmtNum(lin.c)) ÷ \(fmtNum(lin.a)) = \(fmtNum(lin.value))."
        } else {
            steps = "\(fmtNum(lin.a))x = \(fmtNum(lin.c))" + (lin.b >= 0 ? " − \(fmtNum(lin.b))" : " + \(fmtNum(-lin.b))") +
                " = \(fmtNum(lin.c - lin.b)), so x = \(fmtNum(lin.value))."
        }
        return MathWork(value: lin.value, source: "linear",
                        reason: "Solving for x: \(steps)",
                        readAs: nil, highlight: nil, isX: true, suspect: false)
    }
    if let wm = wordMath(text) { return wm }
    if let wpS = wordProblemMath(text, strongOnly: true) { return wpS }
    if let ex = findExpression(text) {
        // More fractions in the question than in the expression, with no
        // + or − in it, means the operator between the fractions was lost
        // in the read — flag it instead of solving a single fraction.
        let fracInText = allMatches(#"\d+\s*/\s*\d+"#, in: text.replacingOccurrences(of: ",", with: "")).count
        let fracInExpr = allMatches(#"\d+\s*/\s*\d+"#, in: ex.expr).count
        if fracInText >= 2 && fracInExpr < fracInText && !ex.expr.contains("+") && !ex.expr.contains("-") {
            return MathWork(value: ex.value, source: "expr",
                            reason: "The read shows more than one fraction with no + or − between them, so part of the question was lost in the scan.",
                            readAs: nil, highlight: nil, isX: false, suspect: true)
        }
        let isFrac = regexContains(#"\d+\s*/\s*\d+"#, in: ex.expr) && regexContains(#"[+\-]"#, in: ex.expr)
        if isFrac {
            let shown = ex.expr.replacingOccurrences(of: "*", with: " × ").replacingOccurrences(of: "-", with: " − ")
                .split(separator: " ").joined(separator: " ").trimmingCharacters(in: .whitespaces)
            return MathWork(value: ex.value, source: "expr",
                            reason: "\(shown) = \(fmtMathValue(ex.value)).",
                            readAs: nil, highlight: nil, isX: false, suspect: false)
        }
        return MathWork(value: ex.value, source: "expr",
                        reason: "\(prettyExpr(ex.expr)) = \(fmtNum(ex.value)) — division and multiplication before addition and subtraction.",
                        readAs: nil, highlight: nil, isX: false, suspect: false)
    }
    if let wp = wordProblemMath(text) { return wp }
    return nil
}
