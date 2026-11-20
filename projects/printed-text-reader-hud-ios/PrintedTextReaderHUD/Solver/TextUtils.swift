// TextUtils.swift
// Small text helpers my solver shares. Pure Swift, Foundation only —
// this file is also the part I can test on any machine, not just iPhone.

import Foundation

/// Words that carry no meaning for matching. Kept identical to my web
/// prototype so the same questions score the same way.
public let solverStopWords: Set<String> = [
    "the", "a", "an", "of", "to", "in", "is", "that", "or", "and", "by",
    "for", "with", "as", "it", "its", "one", "on", "at", "from", "are",
    "was", "very", "so"
]

/// Normalise text for matching: lowercase, curly quotes straightened,
/// everything that is not a letter, digit or space becomes a space,
/// runs of spaces collapsed. "Pokémon" becomes "pok mon" — and the same
/// rule applies to the keywords, so they still match.
public func normText(_ s: String) -> String {
    var out = s.lowercased()
    out = out.replacingOccurrences(of: "’", with: "'")
    out = out.replacingOccurrences(of: "‘", with: "'")
    let allowed = CharacterSet(charactersIn: "abcdefghijklmnopqrstuvwxyz0123456789 ")
    out = out.unicodeScalars.map { allowed.contains($0) ? Character($0) : " " }.reduce("") { $0 + String($1) }
    return out.split(separator: " ").joined(separator: " ")
}

/// Significant words of a string: lowercase letters only, longer than
/// two characters, stop words dropped.
public func tokens(_ s: String) -> [String] {
    let lower = s.lowercased()
    var words: [String] = []
    var current = ""
    for ch in lower {
        if ch.isLetter {
            current.append(ch)
        } else if !current.isEmpty {
            if current.count > 2 && !solverStopWords.contains(current) { words.append(current) }
            current = ""
        }
    }
    if !current.isEmpty && current.count > 2 && !solverStopWords.contains(current) { words.append(current) }
    return words
}

/// How many of `a`'s tokens appear in `bText`.
public func overlapScore(_ aTokens: [String], _ bText: String) -> Int {
    let b = Set(tokens(bText))
    return aTokens.reduce(0) { $0 + (b.contains($1) ? 1 : 0) }
}

// MARK: - Numbers

/// Format a number the way I show it in a reason: integers get thousands
/// commas (1,242), other values are shown as-is, trimmed.
public func fmtNum(_ v: Double) -> String {
    guard v.isFinite else { return "—" }
    let r = (v * 10000).rounded() / 10000
    if r == r.rounded() && abs(r) < 1e15 {
        let n = Int(r)
        let negative = n < 0
        var digits = String(abs(n))
        var out = ""
        while digits.count > 3 {
            out = "," + digits.suffix(3) + out
            digits = String(digits.dropLast(3))
        }
        out = digits + out
        return negative ? "-" + out : out
    }
    return String(r)
}

/// A worked answer that is a clean fraction reads as a fraction —
/// "1/4 + 1/4 = 1/2", not "= 0.5" — because the printed choices are
/// fractions too, and 0.5 does not look like the 1/2 on the page.
public func fmtMathValue(_ v: Double) -> String {
    if v.isFinite && v != v.rounded() {
        for dn in 2...16 {
            let num = v * Double(dn)
            if abs(num - num.rounded()) < 1e-9 {
                return "\(Int(num.rounded()))/\(dn)"
            }
        }
    }
    return fmtNum(v)
}

/// Show an expression with proper symbols: "12 * 6" becomes "12 × 6".
public func prettyExpr(_ expr: String) -> String {
    expr.replacingOccurrences(of: "*", with: " × ")
        .replacingOccurrences(of: "/", with: " ÷ ")
        .replacingOccurrences(of: "-", with: " − ")
        .split(separator: " ").joined(separator: " ")
        .trimmingCharacters(in: .whitespaces)
}

/// Two numbers are "close" when they agree to a rounding error.
public func closeNum(_ a: Double, _ b: Double) -> Bool {
    abs(a - b) <= max(0.011, abs(b) * 0.001)
}

/// The number a printed choice carries: "$72" -> 72, "1/2" -> 0.5,
/// "12 km/h" -> 12. Nil when the choice carries no number.
public func optionNumber(_ txt: String) -> Double? {
    let clean = txt.replacingOccurrences(of: "$", with: "").replacingOccurrences(of: ",", with: "")
    if let frac = firstMatch(#"(-?\d+)\s*/\s*(\d+)"#, in: clean),
       let num = Double(frac[1]), let den = Double(frac[2]), den != 0 {
        return num / den
    }
    if let m = firstMatch(#"-?\d+(?:\.\d+)?"#, in: clean), let v = Double(m[0]) {
        return v
    }
    return nil
}

// MARK: - Regular expressions (NSRegularExpression, so the same patterns
// run on Linux Swift and on iOS)

/// The captures of the first match, or nil. Index 0 is the whole match,
/// 1... are the capture groups. Unmatched groups come back as "".
public func firstMatch(_ pattern: String, in text: String, options: NSRegularExpression.Options = []) -> [String]? {
    guard let re = try? NSRegularExpression(pattern: pattern, options: options) else { return nil }
    let range = NSRange(text.startIndex..., in: text)
    guard let m = re.firstMatch(in: text, options: [], range: range) else { return nil }
    return (0..<m.numberOfRanges).map { i in
        let r = m.range(at: i)
        guard r.location != NSNotFound, let sr = Range(r, in: text) else { return "" }
        return String(text[sr])
    }
}

/// All matches of a pattern, each as its captures (index 0 = whole match).
public func allMatches(_ pattern: String, in text: String, options: NSRegularExpression.Options = []) -> [[String]] {
    guard let re = try? NSRegularExpression(pattern: pattern, options: options) else { return [] }
    let range = NSRange(text.startIndex..., in: text)
    return re.matches(in: text, options: [], range: range).map { m in
        (0..<m.numberOfRanges).map { i in
            let r = m.range(at: i)
            guard r.location != NSNotFound, let sr = Range(r, in: text) else { return "" }
            return String(text[sr])
        }
    }
}

/// Replace using a pattern and a template ("$1", "$2"...).
public func regexReplace(_ pattern: String, in text: String, with template: String, options: NSRegularExpression.Options = []) -> String {
    guard let re = try? NSRegularExpression(pattern: pattern, options: options) else { return text }
    let range = NSRange(text.startIndex..., in: text)
    return re.stringByReplacingMatches(in: text, options: [], range: range, withTemplate: template)
}

/// All matches of a pattern with their ranges: each entry is the whole
/// match range plus its captures, as (location, length) character
/// offsets into the text.
public func allMatchRanges(_ pattern: String, in text: String, options: NSRegularExpression.Options = []) -> [(range: (Int, Int), captures: [String])] {
    guard let re = try? NSRegularExpression(pattern: pattern, options: options) else { return [] }
    let nsRange = NSRange(text.startIndex..., in: text)
    return re.matches(in: text, options: [], range: nsRange).map { m in
        let loc = text.distance(from: text.startIndex, to: String.Index(utf16Offset: m.range.location, in: text))
        let len = text.distance(from: String.Index(utf16Offset: m.range.location, in: text),
                                to: String.Index(utf16Offset: m.range.location + m.range.length, in: text))
        let caps = (0..<m.numberOfRanges).map { i -> String in
            let r = m.range(at: i)
            guard r.location != NSNotFound, let sr = Range(r, in: text) else { return "" }
            return String(text[sr])
        }
        return ((loc, len), caps)
    }
}

/// Does the pattern match anywhere in the text?
public func regexContains(_ pattern: String, in text: String, options: NSRegularExpression.Options = []) -> Bool {
    firstMatch(pattern, in: text, options: options) != nil
}

// MARK: - Edit distance (for the fill-in repair)

/// Plain Levenshtein distance between two lowercase words.
public func levenshtein(_ a: String, _ b: String) -> Int {
    let aChars = Array(a), bChars = Array(b)
    if aChars.isEmpty { return bChars.count }
    if bChars.isEmpty { return aChars.count }
    var prev = Array(0...bChars.count)
    var cur = [Int](repeating: 0, count: bChars.count + 1)
    for i in 1...aChars.count {
        cur[0] = i
        for j in 1...bChars.count {
            let cost = aChars[i - 1] == bChars[j - 1] ? 0 : 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        }
        swap(&prev, &cur)
    }
    return prev[bChars.count]
}

/// How many leading characters two lowercase words share.
/// Used to break edit-distance ties in the fill-in repair
/// ("Whig" -> "Which", not "Big").
public func commonPrefixLength(_ a: String, _ b: String) -> Int {
    var n = 0
    for (x, y) in zip(a, b) {
        if x == y { n += 1 } else { break }
    }
    return n
}
