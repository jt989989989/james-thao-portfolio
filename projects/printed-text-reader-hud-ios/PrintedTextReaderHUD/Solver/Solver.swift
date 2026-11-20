// Solver.swift
// My solver: read a question whole, plus its printed choices, and work
// out the answer. Order, same as my web prototype:
//   1. Maths (computed, never guessed) — with re-analysis against the
//      choices when the worked answer matches none of them.
//   2. My built-in fact bank (general + cybersecurity).
//   3. Cybersecurity definitions, then vocabulary.
//   4. The Wikipedia reference lookup (the only step that uses the
//      network; maths never leaves the phone).
// When nothing confirms an answer, I offer a best-guess SUGGESTED
// answer instead of nothing — clearly labelled, never mistaken for a
// confirmed one. Answers are matched by choice TEXT, never by letter,
// so shuffled choices cannot fool me.

import Foundation

// MARK: - Types

/// One printed choice: the letter as printed, and its text.
public struct ChoiceOption: Equatable, Sendable {
    public let letter: String
    public let text: String
    public init(letter: String, text: String) {
        self.letter = letter
        self.text = text
    }
}

/// One question block: its stem and its printed choices.
public struct ParsedQuestion: Sendable {
    public let stem: String
    public let options: [ChoiceOption]
    public init(stem: String, options: [ChoiceOption]) {
        self.stem = stem
        self.options = options
    }
}

public enum SolveStatus: String, Sendable {
    case solved
    case uncertain
    case cant
}

public enum AnswerSource: String, Sendable {
    /// Worked out on this phone.
    case onPhone
    /// Answered from a web lookup.
    case webLookup
}

/// The answer to one question, as I show it on the camera and the card.
public struct SolveResult: Sendable {
    public var status: SolveStatus
    /// The letter as printed in THIS scan (resolved from the answer text).
    public var letter: String?
    /// The answer text itself — what I match by, so shuffles are safe.
    public var answerText: String?
    /// The headline: the answer, or why I could not pick one.
    public var headline: String
    /// One-line reason.
    public var detail: String
    /// A warning flag, shown on the card.
    public var flag: String?
    /// True when this is a best guess, not a confirmed answer.
    public var suggested: Bool
    public var source: AnswerSource
    /// Letters I am torn between, when I flag uncertainty.
    public var maybeLetters: [String]
    public var sentenceForm: Bool
    /// "12 ÷ 3 = 4" style line for sentence-form maths.
    public var readAs: String?
    /// Character offsets into the stem of the words that became the
    /// calculation, for highlighting.
    public var highlight: (Int, Int)?
    /// The filled-in question, when the read was garbled and repaired.
    public var filledInQuestion: String?

    public init(status: SolveStatus, letter: String? = nil, answerText: String? = nil,
                headline: String, detail: String = "", flag: String? = nil,
                suggested: Bool = false, source: AnswerSource = .onPhone,
                maybeLetters: [String] = [], sentenceForm: Bool = false,
                readAs: String? = nil, highlight: (Int, Int)? = nil,
                filledInQuestion: String? = nil) {
        self.status = status
        self.letter = letter
        self.answerText = answerText
        self.headline = headline
        self.detail = detail
        self.flag = flag
        self.suggested = suggested
        self.source = source
        self.maybeLetters = maybeLetters
        self.sentenceForm = sentenceForm
        self.readAs = readAs
        self.highlight = highlight
        self.filledInQuestion = filledInQuestion
    }

    /// The source label I show on the card.
    public var sourceLabel: String {
        source == .webLookup ? "ANSWER FROM A WEB LOOKUP" : "WORKED OUT ON THIS PHONE"
    }
}

/// One solved block: the question as read, and its answer.
public struct BlockResult: Sendable {
    public let block: ParsedQuestion
    public let raw: String
    public let result: SolveResult
    public init(block: ParsedQuestion, raw: String, result: SolveResult) {
        self.block = block
        self.raw = raw
        self.result = result
    }
}

// MARK: - Matching a worked answer against printed choices

/// An exact numeric match wins outright; otherwise the FIRST close
/// match stands.
public func matchMathOption(_ opts: [ChoiceOption], _ value: Double) -> ChoiceOption? {
    var close: ChoiceOption?
    for o in opts {
        guard let n = optionNumber(o.text) else { continue }
        if abs(n - value) < 1e-9 { return o }
        if close == nil && closeNum(n, value) { close = o }
    }
    return close
}

/// The ÷ that read as a +: when the stem is one plain "A + B" and BOTH
/// readings land on different printed choices, flag it with both
/// candidates instead of confidently picking the wrong one.
public func plusDivAmbiguity(stem: String, opts: [ChoiceOption], ma: MathWork, hit: ChoiceOption) -> SolveResult? {
    guard let ex = findExpression(stem), closeNum(ex.value, ma.value) else { return nil }
    let squashed = ex.expr.replacingOccurrences(of: " ", with: "")
    guard let m = firstMatch(#"^\(?(\d+(?:\.\d+)?)\+(\d+(?:\.\d+)?)\)?$"#,
                             in: squashed),
          let a = Double(m[1]), let b = Double(m[2]), b != 0 else { return nil }
    let altVal = a / b
    if abs(altVal - ma.value) < 1e-9 { return nil }
    guard let alt = matchMathOption(opts, altVal), alt.letter != hit.letter else { return nil }
    return SolveResult(
        status: .uncertain,
        headline: "That + might really be a ÷",
        detail: "Worked as +, the answer is \(hit.letter) · \(hit.text) (\(fmtNum(a)) + \(fmtNum(b)) = \(fmtNum(ma.value))). If the symbol on the page is ÷, the answer is \(alt.letter) · \(alt.text) (\(fmtNum(a)) ÷ \(fmtNum(b)) = \(fmtMathValue(altVal))). A ÷ photographed off a screen can lose its dots and read as +.",
        flag: "⚠ Check the symbol in the question on the page — + and ÷ give different answers here, and both are among the choices. If it is ÷, change the + to ÷ in the text box below and tap Solve.",
        maybeLetters: [hit.letter, alt.letter])
}

/// Re-analyse against the choices when the worked answer matches NONE
/// of them. Each operator is swapped in turn, a colon is tried as a
/// division sign, and each number is tried with its last digit dropped
/// (the question's closing "?" reads as a 7 glued onto the last
/// number). A re-reading is only trusted when EXACTLY ONE re-read
/// calculation lands on a printed choice.
public func reanalyzeMath(stem: String, opts: [ChoiceOption], ma: MathWork) -> SolveResult? {
    guard ma.source == "expr",
          let base = findExpression(stem), closeNum(base.value, ma.value) else { return nil }
    let expr = base.expr.replacingOccurrences(of: " ", with: "")
    var found: [(hit: ChoiceOption, expr: String, value: Double)] = []
    var seen = Set<String>()
    func tryValue(_ v: Double, _ e2: String) {
        guard v.isFinite, abs(v - ma.value) >= 1e-9 else { return }
        if let hit = matchMathOption(opts, v), !seen.contains(hit.letter) {
            seen.insert(hit.letter)
            found.append((hit, e2, v))
        }
    }
    func tryExpr(_ e2: String) {
        guard !e2.isEmpty, e2 != expr else { return }
        var p = ExprParser(e2)
        if let v = try? p.run() { tryValue(v, e2) }
    }
    let ops: [Character] = ["+", "-", "*", "/"]
    func swapOps(_ e: String) {
        let chars = Array(e)
        for k in chars.indices where ops.contains(chars[k]) {
            let prev: Character = k > 0 ? chars[k - 1] : " "
            let next: Character = k + 1 < chars.count ? chars[k + 1] : " "
            guard (prev.isNumber || prev == ")") && (next.isNumber || next == "(") else { continue }
            for op in ops where op != chars[k] {
                var copy = chars
                copy[k] = op
                tryExpr(String(copy))
            }
        }
    }
    swapOps(expr)
    if expr.filter({ $0 == "+" }).count > 1 {
        tryExpr(expr.replacingOccurrences(of: "+", with: "/"))
    }
    let toks = allMatches(#"\d+(?:\.\d+)?|[+\-*/()]"#, in: expr).map { $0[0] }
    let numCount = toks.filter { $0.first?.isNumber == true }.count
    if numCount <= 5 {
        for ti in toks.indices where regexContains(#"^\d{2,}$"#, in: toks[ti]) {
            var repaired = toks
            repaired[ti] = String(toks[ti].dropLast())
            let e3 = repaired.joined()
            tryExpr(e3)
            swapOps(e3)
        }
    }
    if let colon = findExpression(regexReplace(#"(\d)\s*:\s*(?=\d)"#, in: stem, with: "$1/")),
       !closeNum(colon.value, ma.value) {
        tryValue(colon.value, colon.expr.replacingOccurrences(of: " ", with: ""))
    }
    guard found.count == 1 else { return nil }
    let f = found[0]
    return SolveResult(
        status: .solved, letter: f.hit.letter, answerText: f.hit.text, headline: f.hit.text,
        detail: "As first read, \(prettyExpr(expr)) = \(fmtNum(ma.value)) — not one of the choices. Re-analysed against the choices: \(prettyExpr(f.expr)) = \(fmtMathValue(f.value)), which is choice \(f.hit.letter). A symbol or a digit was most likely misread in the scan — a ÷ photographed off a screen can lose its dots and read as +, and a question's closing ? can read as an extra 7 on its last number.",
        flag: "⚠ This answer matched only after re-analysing a symbol against the choices. If the symbol on the page really is the first-read one, fix it in the text box below and tap Solve.")
}

/// When the choices were read but the question itself wasn't — fit the
/// stem's own numbers against the choices. Only a UNIQUE fit is
/// offered, and only as a best fit, never as a confident pick.
public func bestFitFromChoices(stem: String, opts: [ChoiceOption]) -> SolveResult? {
    let nums = allMatches(#"\d+(?:\.\d+)?"#, in: stem.replacingOccurrences(of: ",", with: "")).compactMap { Double($0[0]) }
    guard nums.count >= 2 && nums.count <= 4 else { return nil }
    var fits: [(hit: ChoiceOption, label: String, value: Double)] = []
    var seen = Set<String>()
    func tryVal(_ v: Double, _ label: String) {
        guard v.isFinite else { return }
        if let hit = matchMathOption(opts, v), !seen.contains(hit.letter) {
            seen.insert(hit.letter)
            fits.append((hit, label, v))
        }
    }
    for i in nums.indices {
        for j in nums.indices where i != j {
            let a = nums[i], b = nums[j]
            tryVal(a + b, "\(fmtNum(a)) + \(fmtNum(b))")
            tryVal(a - b, "\(fmtNum(a)) − \(fmtNum(b))")
            tryVal(a * b, "\(fmtNum(a)) × \(fmtNum(b))")
            if b != 0 { tryVal(a / b, "\(fmtNum(a)) ÷ \(fmtNum(b))") }
        }
    }
    guard fits.count == 1 else { return nil }
    let f = fits[0]
    return SolveResult(
        status: .uncertain,
        headline: "Best fit: \(f.hit.letter) · \(f.hit.text)",
        detail: "The question itself didn't read clearly, so its numbers were re-analysed against the choices: of every combination of those numbers, only \(f.label) = \(fmtMathValue(f.value)) lands on a printed choice.",
        flag: "⚠ Best fit only — the question text wasn't recognised. Re-scan it (fill the frame, hold steady) or fix its text in the box below and tap Solve to be sure.",
        maybeLetters: [f.hit.letter])
}

/// True when the stem plainly IS arithmetic — digits with an operator
/// (or a fraction) between them — whether or not the maths engine
/// managed to solve it. Stops the reference lookup from "answering" a
/// maths question by whichever printed number its text mentions most.
public func looksLikeArithmetic(_ stem: String) -> Bool {
    let s = stem
    guard regexContains(#"\d"#, in: s) else { return false }
    if regexContains(#"\d\s*[+\-×✕*÷/]\s*\d"#, in: s) || regexContains(#"\d\s*[xX]\s*\d"#, in: s) { return true }
    return regexContains(#"\d\s*[xX](?![a-z])"#, in: s)
}

// MARK: - The solver

/// My solver. Holds the answers I have been taught, keyed by the
/// normalised question — the taught answer is a TEXT, so a shuffled
/// retake still finds it under its new letter.
public final class Solver: @unchecked Sendable {
    public var taughtAnswers: [String: String] = [:]
    public var wikiFetcher: WikiFetcher?
    public var dictionaryFetcher: DictionaryFetcher?

    public init() {}

    /// Solve every question in a raw read. Returns one result per
    /// question block, in frame order.
    public func solve(_ text: String) async -> [BlockResult] {
        let repaired = repairFractionOcr(text)
        let blocks = splitQuestions(repaired)
        var out: [BlockResult] = []
        for raw in blocks {
            let parsed = parseOptions(raw)
            let result = await solveBlock(raw: raw, parsed: parsed)
            let block = parsed ?? ParsedQuestion(stem: questionFocus(raw), options: [])
            out.append(BlockResult(block: block, raw: raw, result: result))
        }
        return out
    }

    private func solveBlock(raw: String, parsed: ParsedQuestion?) async -> SolveResult {
        if let mc = parsed, !mc.options.isEmpty {
            // Taught answers first — matched by text, never by letter.
            let qStem0 = cutToQuestion(mc.stem)
            if let taught = taughtAnswers[normText(qStem0)] {
                let hits = mc.options.filter { optionMatchesAnswer($0.text, taught) }
                if hits.count == 1 {
                    return SolveResult(status: .solved, letter: hits[0].letter, answerText: hits[0].text,
                                       headline: hits[0].text,
                                       detail: "You taught me this one — the answer is \(hits[0].text).",
                                       flag: nil, suggested: false, source: .onPhone)
                }
            }
            // A garbled read gets filled in before solving; the filled-in
            // question is shown on the card. A clean read is untouched.
            let filled = fillInQuestion(qStem0, choices: mc.options)
            let qStem = filled ?? qStem0
            let filledLabel = filled.map { "FILLED IN AS: \($0)" }
            let stemWeak = tokens(qStem).count < 3

            if let ma = mathAnswer(qStem) ?? mathAnswer(cutToQuestion(raw.components(separatedBy: "\n").first ?? "")) {
                if ma.suspect {
                    return SolveResult(status: .uncertain,
                                       headline: "Part of this question was lost in the read",
                                       detail: ma.reason,
                                       flag: "⚠ The operator between the fractions wasn't read, so any answer picked now could be the wrong one. Check the question in the text box — add the missing + or − — and solve again.",
                                       filledInQuestion: filledLabel)
                }
                if let hit = matchMathOption(mc.options, ma.value) {
                    if ma.source == "expr", let amb = plusDivAmbiguity(stem: qStem, opts: mc.options, ma: ma, hit: hit) {
                        var r = amb
                        r.filledInQuestion = filledLabel
                        return r
                    }
                    var hl: (Int, Int)?
                    if let h = ma.highlight {
                        hl = findHighlightSpan(in: qStem, a: h.a, op: h.op, b: h.b)
                    }
                    return SolveResult(status: .solved, letter: hit.letter, answerText: hit.text,
                                       headline: hit.text, detail: ma.reason, flag: nil,
                                       suggested: false, source: .onPhone,
                                       sentenceForm: ma.readAs != nil, readAs: ma.readAs,
                                       highlight: hl, filledInQuestion: filledLabel)
                }
                if let re = reanalyzeMath(stem: qStem, opts: mc.options, ma: ma) {
                    var r = re
                    r.filledInQuestion = filledLabel
                    return r
                }
                if let bf1 = bestFitFromChoices(stem: qStem, opts: mc.options) {
                    var r = bf1
                    r.filledInQuestion = filledLabel
                    return r
                }
                return SolveResult(status: .uncertain,
                                   headline: (ma.isX ? "x = " : "") + fmtMathValue(ma.value) + " — not among the options",
                                   detail: ma.reason,
                                   flag: "⚠ The worked answer doesn't match any printed option, and re-analysing the symbols against the choices found no fit either. The text may have been misread — check the numbers in the text box and solve again.",
                                   filledInQuestion: filledLabel)
            }
            if let factHit = solveMcFact(qStem, mc.options, fullText: qStem) {
                var r = factHit
                r.filledInQuestion = filledLabel
                return r
            }
            if let cyberDefHit = solveMcCyberDef(qStem, mc.options) {
                var r = cyberDefHit
                r.filledInQuestion = filledLabel
                return r
            }
            if let v = await solveMcVocabulary(qStem, mc.options, dictionary: dictionaryFetcher) {
                var r = v
                r.filledInQuestion = filledLabel
                return r
            }
            let bf2 = bestFitFromChoices(stem: qStem, opts: mc.options)
            if let bf2 = bf2, (stemWeak || looksLikeArithmetic(qStem)) {
                var r = bf2
                r.filledInQuestion = filledLabel
                return r
            }
            if looksLikeArithmetic(qStem) {
                return SolveResult(status: .uncertain,
                                   headline: "That is a maths question — but its numbers didn't read cleanly",
                                   detail: "The question and its \(mc.options.count) options were read, but no clean calculation could be made from them, so no answer is picked rather than a guessed one.",
                                   flag: "⚠ Check the numbers in the text box below — fix any misread digit or symbol (× often reads as x, which is fine) — and tap Solve again.",
                                   filledInQuestion: filledLabel)
            }
            if let fetcher = wikiFetcher, let w = await solveMcWiki(qStem, mc.options, fetcher: fetcher) {
                var r = w
                r.filledInQuestion = filledLabel
                return r
            }
            if let bf2 = bf2 {
                var r = bf2
                r.filledInQuestion = filledLabel
                return r
            }
            // Nothing confirmed it — offer a best guess from the
            // reference scores rather than nothing at all.
            if let fetcher = wikiFetcher, let suggestion = await suggestFromWiki(qStem, mc.options, fetcher: fetcher) {
                var r = suggestion
                r.filledInQuestion = filledLabel
                return r
            }
            return SolveResult(status: .cant,
                               headline: "Read it — no confident answer found",
                               detail: "The question and its \(mc.options.count) options were read and are in the text box below. It was checked as math, vocabulary and general knowledge, but no option stood out clearly — check for misread words and tap Solve again.",
                               filledInQuestion: filledLabel)
        }

        // No options in the frame.
        let openText = cutToQuestion(raw)
        if let ma2 = mathAnswer(openText) {
            var res = SolveResult(status: .solved, headline: (ma2.isX ? "x = " : "") + fmtMathValue(ma2.value),
                                  detail: ma2.reason, flag: nil, suggested: false, source: .onPhone,
                                  sentenceForm: ma2.readAs != nil, readAs: ma2.readAs)
            if regexContains(#"\?"#, in: openText) || regexContains(#"^(what|how many|how much|which|calculate|find)\b"#, in: openText.trimmingCharacters(in: .whitespaces), options: [.caseInsensitive]) {
                res.suggested = true
                res.flag = "SUGGESTED ANSWER — the question was read but its choices weren't in this frame, so this is the answer worked from the question alone. Scan again with the choices in frame and it will pick from them instead."
            }
            return res
        }
        if let factOpen = findFact(openText) {
            if let cDef = findCyberDefTerm(openText),
               regexContains(#"what is|define|definition|meaning|describe"#, in: openText, options: [.caseInsensitive]),
               normText(factOpen.answer) == normText(cDef.term) {
                return SolveResult(status: .solved, headline: cDef.term, detail: cDef.definition)
            }
            return SolveResult(status: .solved, headline: factOpen.answer, detail: factOpen.reason)
        }
        if let cDefOpen = findCyberDefTerm(openText),
           regexContains(#"what is|define|definition|meaning|describe"#, in: openText, options: [.caseInsensitive]) {
            return SolveResult(status: .solved, headline: cDefOpen.term, detail: cDefOpen.definition)
        }
        let trimmed = openText.trimmingCharacters(in: .whitespaces)
        if let word = extractDefineWord(trimmed), regexContains(#"mean|define|definition"#, in: trimmed, options: [.caseInsensitive]) {
            if let info = await lookupWord(word, fetcher: dictionaryFetcher) {
                return SolveResult(status: .solved, headline: info.word,
                                   detail: (info.pos.isEmpty ? "" : info.pos + " — ") + info.definition)
            }
            return SolveResult(status: .cant, headline: "No definition found for \"\(word)\"",
                               detail: "The word was read, but the dictionary has no entry for it — check the spelling in the text box.")
        }
        if regexContains(#"^[A-Za-z][A-Za-z'-]*$"#, in: trimmed) {
            if let info = await lookupWord(trimmed, fetcher: dictionaryFetcher) {
                return SolveResult(status: .solved, headline: info.word,
                                   detail: (info.pos.isEmpty ? "" : info.pos + " — ") + info.definition)
            }
            return SolveResult(status: .cant, headline: "No definition found for \"\(trimmed)\"",
                               detail: "A single word was read, but the dictionary has no entry for it — check the spelling in the text box.")
        }
        if regexContains(#"\?\s*$"#, in: trimmed) || regexContains(#"^(what|which|who|where|when|how many|how much)\b"#, in: trimmed, options: [.caseInsensitive]) {
            if let fetcher = wikiFetcher, let w = await solveOpenWiki(trimmed, fetcher: fetcher) {
                return w
            }
            return SolveResult(status: .cant, headline: "Read it — no confident answer found",
                               detail: "The question was read and checked against the fact bank and a reference source, but no clear answer came back. The text is in the box below — fix any misread words and tap Solve again, or add A–D options if it is a multiple-choice question.")
        }
        return SolveResult(status: .cant, headline: "Read it — no confident answer found",
                           detail: "This answers multiple-choice questions in any subject, arithmetic, simple solve-for-x, and word definitions. The text it read is in the box below — if numbers or a word were misread, fix them and tap Solve again.")
    }

    /// A best-guess suggestion from the reference scores: the top option
    /// wins even on a weak score, as long as it beats the runner-up.
    /// Clearly labelled — never mistaken for a confirmed answer.
    private func suggestFromWiki(_ stem: String, _ opts: [ChoiceOption], fetcher: WikiFetcher) async -> SolveResult? {
        let query = stem.split(separator: " ").joined(separator: " ").trimmingCharacters(in: .whitespaces)
        guard query.count >= 8, let corpus = await fetcher(query), !corpus.isEmpty else { return nil }
        let cn = normText(corpus)
        let scored = opts.map { o in (o, scoreOptionInCorpus(o.text, cn)) }.sorted { $0.1 > $1.1 }
        guard let top = scored.first else { return nil }
        let second = scored.count > 1 ? scored[1] : nil
        if isNotQuestion(stem) {
            let lowest = scored.last!
            if top.1 >= 3 && top.1 - lowest.1 >= 2 {
                return SolveResult(status: .solved, letter: lowest.0.letter, answerText: lowest.0.text,
                                   headline: lowest.0.text,
                                   detail: "My best guess from the reference — the other options are the ones the reference backs, and this is a NOT question.",
                                   flag: "SUGGESTED ANSWER — BEST GUESS, NOT CONFIRMED",
                                   suggested: true, source: .webLookup)
            }
            return nil
        }
        guard top.1 >= 3 && top.1 > (second?.1 ?? 0) else { return nil }
        return SolveResult(status: .solved, letter: top.0.letter, answerText: top.0.text,
                           headline: top.0.text,
                           detail: "My best guess from the reference — \"\(top.0.text)\" is the option the reference mentions most for this question.",
                           flag: "SUGGESTED ANSWER — BEST GUESS, NOT CONFIRMED",
                           suggested: true, source: .webLookup)
    }
}
