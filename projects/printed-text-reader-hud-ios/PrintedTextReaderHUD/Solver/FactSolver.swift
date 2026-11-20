// FactSolver.swift
// Answering from my built-in banks and from definitions: the fact bank
// (general + cybersecurity), the "term named, options are definitions"
// reverse style, and vocabulary questions ("What does X mean?").
// Answers are matched against the printed choices by TEXT, never by
// letter — the choices can shuffle.

import Foundation

// MARK: - Fact bank

/// The best banked fact whose keywords all appear in the text. When
/// several match, the one with the longest keywords wins.
public func findFact(_ text: String) -> Fact? {
    let t = " " + normText(text) + " "
    let normed = normText(text)
    var best: Fact?
    for f in FactBank.generalFacts + FactBank.cyberFacts {
        var ok = true
        for kw in f.keywords {
            let nk = normText(kw)
            if t.contains(" " + nk) || t.contains(nk + " ") || t.contains(" " + nk + " ") {
                continue
            }
            if !normed.contains(nk) { ok = false; break }
        }
        if ok && (best == nil || f.keywords.joined(separator: " ").count > best!.keywords.joined(separator: " ").count) {
            best = f
        }
    }
    return best
}

/// Does a printed option carry the banked answer? Exact text, substring,
/// numeric, or token-set match — so "Confidentiality, Integrity, and
/// Availability" matches "Confidentiality Integrity Availability".
public func optionMatchesAnswer(_ optText: String, _ answer: String) -> Bool {
    let o = normText(optText), a = normText(answer)
    guard !o.isEmpty, !a.isEmpty else { return false }
    if o == a { return true }
    if (" " + o + " ").contains(" " + a + " ") { return true }
    if (" " + a + " ").contains(" " + o + " ") && o.count >= 3 { return true }
    // Numeric answers: 206, 100, 366, 50 …
    if let an = optionNumber(answer), let on = optionNumber(optText), answer.trimmingCharacters(in: .whitespaces).first?.isNumber == true {
        let optDigits = normText(optText).filter { $0.isNumber }
        if optDigits == String(Int(an.rounded())) || (closeNum(on, an) && optText.filter { "0123456789.,°cf ".contains($0) }.trimmingCharacters(in: .whitespaces).count >= String(Int(an.rounded())).count) {
            return closeNum(on, an)
        }
    }
    // Chemical symbols: H2O vs H₂O.
    if o.replacingOccurrences(of: " ", with: "") == a.replacingOccurrences(of: " ", with: "") { return true }
    // Formula answers ("SLE x ARO") differ from wrong options only by
    // the operator — require a multiplication sign and no "+".
    if regexContains(#"^[a-z]+\s+x\s+[a-z]+$"#, in: answer.trimmingCharacters(in: .whitespaces), options: [.caseInsensitive]) {
        let hasMul = regexContains("[×✕*]", in: optText) || regexContains(#"\bx\b"#, in: optText, options: [.caseInsensitive])
        if !hasMul || optText.contains("+") { return false }
    }
    // Token-set match: every significant word of the answer appears in
    // the option (or vice versa).
    let aToks = a.split(separator: " ").map(String.init).filter { $0.count >= 2 }
    let oToks = o.split(separator: " ").map(String.init).filter { $0.count >= 2 }
    if aToks.count >= 2 && aToks.allSatisfy({ oToks.contains($0) }) { return true }
    if oToks.count >= 2 && oToks.allSatisfy({ aToks.contains($0) }) { return true }
    return false
}

/// Solve a multiple-choice question from the fact bank, or nil.
public func solveMcFact(_ stem: String, _ opts: [ChoiceOption], fullText: String? = nil) -> SolveResult? {
    guard let fact = findFact(stem) ?? (fullText.map { findFact($0) } ?? nil) else { return nil }
    let hits = opts.filter { optionMatchesAnswer($0.text, fact.answer) }
    if hits.count == 1 {
        return SolveResult(status: .solved, letter: hits[0].letter, answerText: hits[0].text,
                           headline: hits[0].text, detail: fact.reason, flag: nil,
                           suggested: false, source: .onPhone, maybeLetters: [],
                           sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
    }
    if hits.count > 1 {
        return SolveResult(status: .uncertain, letter: nil, answerText: nil,
                           headline: "Not certain between \(hits[0].letter) and \(hits[1].letter)",
                           detail: fact.reason,
                           flag: "⚠ More than one printed option matches the known answer — flagged instead of guessed. Check the options in the text box.",
                           suggested: false, source: .onPhone, maybeLetters: [hits[0].letter, hits[1].letter],
                           sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
    }
    return nil
}

// MARK: - Cybersecurity definitions (reverse style)

/// The cybersecurity term named in the question, if any — longest match wins.
public func findCyberDefTerm(_ text: String) -> CyberDefinition? {
    let t = normText(text)
    var best: CyberDefinition?
    for e in FactBank.cyberDefinitions {
        if (" " + t + " ").contains(" " + normText(e.term) + " ") && (best == nil || e.term.count > best!.term.count) {
            best = e
        }
    }
    return best
}

/// The question names a term and the options are definitions of it:
/// score each option against the definition's words.
public func solveMcCyberDef(_ stem: String, _ opts: [ChoiceOption]) -> SolveResult? {
    guard let entry = findCyberDefTerm(stem) else { return nil }
    let phraseOpts = opts.filter { $0.text.trimmingCharacters(in: .whitespaces).split(separator: " ").count >= 3 }
    guard phraseOpts.count >= 2 else { return nil }
    let defTokens = tokens(entry.definition)
    let scored = opts.map { o in (o, overlapScore(defTokens, o.text)) }.sorted { $0.1 > $1.1 }
    guard let top = scored.first else { return nil }
    let second = scored.count > 1 ? scored[1] : nil
    if top.1 >= 2 && top.1 > (second?.1 ?? 0) {
        return SolveResult(status: .solved, letter: top.0.letter, answerText: top.0.text,
                           headline: top.0.text, detail: "\"\(entry.term)\" — \(entry.definition)", flag: nil,
                           suggested: false, source: .onPhone, maybeLetters: [],
                           sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
    }
    if top.1 >= 2, let second = second {
        return SolveResult(status: .uncertain, letter: nil, answerText: nil,
                           headline: "Not certain between \(top.0.letter) and \(second.0.letter)",
                           detail: "\"\(entry.term)\" — \(entry.definition)",
                           flag: "⚠ Two options overlap the definition of \"\(entry.term)\" — flagged instead of guessed.",
                           suggested: false, source: .onPhone, maybeLetters: [top.0.letter, second.0.letter],
                           sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
    }
    return nil
}

// MARK: - Vocabulary / definitions

/// A few definitions built in, so common words work with no network.
public let builtinDefinitions: [String: (pos: String, def: String)] = [
    "photosynthesis": ("noun", "The process by which green plants use sunlight, water, and carbon dioxide to make their own food and release oxygen."),
    "gravity": ("noun", "The force that pulls objects toward each other, and toward the center of a planet."),
    "evaporation": ("noun", "The process by which a liquid slowly changes into a gas or vapor."),
    "fraction": ("noun", "A part of a whole, written as one number over another, such as 1/2."),
    "habitat": ("noun", "The natural home or environment of a plant or animal."),
    "ancient": ("adjective", "Belonging to a very long time ago; very old."),
    "rapid": ("adjective", "Happening in a short time, or at a fast pace."),
    "serene": ("adjective", "Calm, peaceful, and untroubled."),
    "enormous": ("adjective", "Very large in size or amount."),
    "journey": ("noun", "A trip from one place to another, especially a long one."),
    "observe": ("verb", "To watch something carefully in order to learn about it."),
    "predict": ("verb", "To say what you think will happen in the future."),
    "energy": ("noun", "The power to do work, move things, or produce heat and light."),
    "liquid": ("noun", "A substance that flows freely, like water, and takes the shape of its container."),
    "magnet": ("noun", "A piece of metal that attracts iron and some other metals."),
    "orbit": ("noun", "The curved path an object follows as it travels around a planet or star."),
    "climate": ("noun", "The usual weather conditions of a place over a long period."),
    "multiply": ("verb", "To increase a number by a given amount of times, such as 3 × 4 = 12."),
    "brave": ("adjective", "Ready to face danger or pain without showing fear."),
    "compare": ("verb", "To examine two or more things to see how they are alike or different.")
]

public struct WordInfo: Sendable {
    public let word: String
    public let pos: String
    public let definition: String
    public let synonyms: [String]
}

/// Look a word up: the built-in dictionary first (works offline), then
/// the free dictionary API when a fetcher is provided.
public func lookupWord(_ word: String, fetcher: DictionaryFetcher? = nil) async -> WordInfo? {
    let w = word.lowercased().filter { $0.isLetter || $0 == "'" || $0 == "-" }
    guard !w.isEmpty else { return nil }
    if let b = builtinDefinitions[w] {
        return WordInfo(word: w, pos: b.pos, definition: b.def, synonyms: [])
    }
    return await fetcher?(w)
}

/// The word a "what does X mean?" question is asking about.
public func extractDefineWord(_ stem: String) -> String? {
    if let m = firstMatch(#"["“”']([A-Za-z][A-Za-z'-]*)["“”']"#, in: stem) { return m[1] }
    if let m = firstMatch(#"(?:word|term)\s+([A-Za-z][A-Za-z'-]*)"#, in: stem, options: [.caseInsensitive]),
       !["is", "means", "mean", "does"].contains(m[1].lowercased()) { return m[1] }
    if let m = firstMatch(#"(?:define|meaning of|does)\s+([A-Za-z][A-Za-z'-]*)"#, in: stem, options: [.caseInsensitive]),
       !["the", "a", "an"].contains(m[1].lowercased()) { return m[1] }
    return nil
}

/// Vocabulary questions: "What does X mean?" (score the options
/// against the definition) and "Which word means '…'?" (score each
/// single-word option's definition against the phrase).
public func solveMcVocabulary(_ stem: String, _ opts: [ChoiceOption], dictionary: DictionaryFetcher? = nil) async -> SolveResult? {
    let word = extractDefineWord(stem)
    let meansAsk = regexContains(#"mean|definition|define"#, in: stem, options: [.caseInsensitive])
    if let word = word, meansAsk, let info = await lookupWord(word, fetcher: dictionary) {
        let defTokens = tokens(info.definition) + info.synonyms.map { $0.lowercased() }
        let scored = opts.map { o in (o, overlapScore(defTokens, o.text)) }.sorted { $0.1 > $1.1 }
        guard let top = scored.first, top.1 > 0 else { return nil }
        let second = scored.count > 1 ? scored[1] : nil
        if top.1 > (second?.1 ?? 0) {
            return SolveResult(status: .solved, letter: top.0.letter, answerText: top.0.text,
                               headline: top.0.text, detail: "\"\(info.word)\" (\(info.pos)) — \(info.definition)", flag: nil,
                               suggested: false, source: .onPhone, maybeLetters: [],
                               sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
        }
        if let second = second {
            return SolveResult(status: .uncertain, letter: nil, answerText: nil,
                               headline: "Not certain between \(top.0.letter) and \(second.0.letter)",
                               detail: "\"\(info.word)\" means: \(info.definition)",
                               flag: "⚠ Two options overlap the definition of \"\(info.word)\" — flagged instead of guessed.",
                               suggested: false, source: .onPhone, maybeLetters: [top.0.letter, second.0.letter],
                               sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
        }
        return nil
    }
    var phrase: String?
    if let qm = firstMatch(#"["“”']([^"“”']{3,})["“”']"#, in: stem) {
        phrase = qm[1]
    } else if let mm = firstMatch(#"means\s+(.+)$"#, in: stem, options: [.caseInsensitive]) {
        phrase = mm[1]
    }
    let singleWordOpts = opts.filter { regexContains(#"^[A-Za-z][A-Za-z'-]*$"#, in: $0.text.trimmingCharacters(in: .whitespaces)) }
    if let phrase = phrase, singleWordOpts.count >= 2 {
        let phraseTokens = tokens(phrase)
        var scored: [(ChoiceOption, Int, WordInfo?)] = []
        for o in singleWordOpts {
            let info = await lookupWord(o.text.trimmingCharacters(in: .whitespaces), fetcher: dictionary)
            if let info = info {
                let hay = info.definition + " " + info.synonyms.joined(separator: " ")
                scored.append((o, overlapScore(phraseTokens, hay), info))
            } else {
                scored.append((o, -1, nil))
            }
        }
        scored.sort { $0.1 > $1.1 }
        guard let top = scored.first, top.1 > 0, let topInfo = top.2 else { return nil }
        let second = scored.count > 1 ? scored[1] : nil
        if top.1 > (second?.1 ?? 0) {
            return SolveResult(status: .solved, letter: top.0.letter, answerText: top.0.text,
                               headline: top.0.text, detail: "\"\(topInfo.word)\" — \(topInfo.definition)", flag: nil,
                               suggested: false, source: .onPhone, maybeLetters: [],
                               sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
        }
        if let second = second {
            return SolveResult(status: .uncertain, letter: nil, answerText: nil,
                               headline: "Not certain between \(top.0.letter) and \(second.0.letter)",
                               detail: "Both definitions overlap \"\(phrase)\" — check the wording on the page.",
                               flag: "⚠ Two options could fit — flagged instead of guessed.",
                               suggested: false, source: .onPhone, maybeLetters: [top.0.letter, second.0.letter],
                               sentenceForm: false, readAs: nil, highlight: nil, filledInQuestion: nil)
        }
    }
    return nil
}
