// FillInRepair.swift
// When a question reads garbled — "Whig ib the rote Mhcramon is NOT
// a Dragon-type?" — I fill in the blanks to make it make sense: each
// unrecognised word is swapped for the closest known word from the
// question's own choices and my built-in banks. Words with no close
// match are left untouched rather than rewritten wrong, and a clean
// read is never rewritten at all. The filled-in question is shown as
// "FILLED IN AS: …" so the repair is visible, not silent.

import Foundation

/// Everyday words that are known on sight, so they are never "repaired".
private let commonWords: Set<String> = [
    "what", "which", "who", "whom", "whose", "where", "when", "why", "how",
    "many", "much", "more", "most", "few", "less", "least", "first", "second",
    "third", "does", "did", "is", "are", "was", "were", "be", "been", "being",
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "with", "from",
    "by", "and", "or", "not", "no", "this", "that", "these", "those", "it",
    "its", "as", "if", "then", "than", "so", "such", "into", "each", "every",
    "all", "any", "some", "following", "question", "answer", "answers",
    "choose", "best", "describes", "means", "mean", "called", "known",
    "episode", "anime", "legendary", "catch", "glimpse", "flying", "across",
    "rainbow", "famous", "famously", "nicknamed", "nickname", "president",
    "during", "civil", "war", "following", "among", "between", "about",
    "have", "has", "had", "will", "would", "can", "could", "should",
    "there", "here", "out", "over", "under", "after", "before", "while",
    "find", "give", "gives", "make", "makes", "take", "takes", "total",
    "altogether", "left", "still", "each", "per", "hour", "hours", "minutes",
    "days", "years", "people", "person", "group", "team", "game", "show",
    "story", "book", "books", "school", "class", "student", "students",
    "child", "children", "man", "woman", "boy", "girl", "friend", "friends",
    "home", "house", "room", "water", "food", "money", "price", "cost",
    "buy", "buys", "sell", "sells", "pay", "pays", "change", "bill",
    "box", "boxes", "bag", "bags", "basket", "baskets", "pack", "packs",
    "shelf", "shelves", "row", "rows", "ticket", "tickets", "apple",
    "apples", "tree", "trees", "flower", "flowers", "animal", "animals",
    "dog", "cat", "bird", "fish", "red", "blue", "green", "big", "small",
    "long", "short", "high", "low", "fast", "slow", "new", "old", "good",
    "bad", "right", "wrong", "true", "false", "correct", "incorrect"
]

/// All the words I know: the fact banks (keywords, answers, reasons),
/// the cybersecurity definitions, the common words, and the words of
/// the question's own printed choices.
public func knownWords(choices: [ChoiceOption] = []) -> Set<String> {
    var known = commonWords
    for f in FactBank.generalFacts + FactBank.cyberFacts {
        for kw in f.keywords { known.formUnion(tokens(kw)) }
        known.formUnion(tokens(f.answer))
        known.formUnion(tokens(f.reason))
    }
    for d in FactBank.cyberDefinitions {
        known.formUnion(tokens(d.term))
        known.formUnion(tokens(d.definition))
    }
    for o in choices {
        known.formUnion(tokens(o.text))
        // Choice words are known even when short ("Au", "Fe", "H2O").
        for w in o.text.lowercased().split(separator: " ") { known.insert(String(w)) }
    }
    // Number words are known too.
    known.formUnion(numberWords.keys)
    return known
}

/// Repair a garbled stem. Returns the repaired stem, or nil when nothing
/// needed repairing (a clean read is never rewritten).
public func fillInQuestion(_ stem: String, choices: [ChoiceOption] = []) -> String? {
    let known = knownWords(choices: choices)
    var repaired = stem
    var changed = false
    // Walk the words, keeping every separator and capital exactly as read.
    // The pattern is Unicode-aware (\p{L}) so "Pokémon" is one word,
    // not "Pok" + "mon" to be "repaired" into nonsense.
    let pattern = #"[\p{L}][\p{L}'-]*"#
    guard let re = try? NSRegularExpression(pattern: pattern) else { return nil }
    let nsRange = NSRange(stem.startIndex..., in: stem)
    let matches = re.matches(in: stem, options: [], range: nsRange)
    // Rebuild from the end so earlier ranges stay valid.
    for m in matches.reversed() {
        guard let sr = Range(m.range, in: stem) else { continue }
        let word = String(stem[sr])
        let lower = word.lowercased()
        if lower.count < 3 || known.contains(lower) { continue }
        // Closest known word, by edit distance. Short words get a
        // stricter bar — a 3-letter word is one typo from anything.
        // Ties go to the candidate sharing the longest prefix with the
        // garbled word ("Whig" -> "Which", not "Big").
        let limit = lower.count >= 4 ? 2 : 1
        var best: String?
        var bestDist = Int.max
        var bestPrefix = -1
        // Sorted, so ties resolve the same way every run.
        for cand in known.sorted() where abs(cand.count - lower.count) <= 2 {
            let d = levenshtein(lower, cand)
            let prefix = commonPrefixLength(lower, cand)
            if d < bestDist || (d == bestDist && prefix > bestPrefix) {
                bestDist = d
                bestPrefix = prefix
                best = cand
            }
        }
        guard let fix = best, bestDist <= limit else { continue }
        var replacement = fix
        if let first = word.first, first.isUppercase {
            replacement = fix.prefix(1).uppercased() + fix.dropFirst()
        }
        repaired.replaceSubrange(sr, with: replacement)
        changed = true
    }
    return changed ? repaired : nil
}
