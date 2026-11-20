// TextSegmentation.swift
// Splitting a raw read into questions and choices. The rules come from
// what the quiz apps actually print:
//  - A question starts at a "number then a period" anchor ("2.").
//  - Choices are lettered A–D lines (also bare sequential letters, and
//    pill-button choices whose "A." markers the reader dropped).
//  - Quiz chrome ("Correct!/Incorrect.", "Show hint", "Back", "Next",
//    progress markers) is stripped from the choices.
//  - Choices can arrive two-to-a-row, all on one line, or in columns
//    (A,C down one side, then B,D) — they are put back in letter order.

import Foundation

// MARK: - Option lines

/// Choices are often printed two-to-a-row or all on one line
/// ("A. 24  B. 36  C. 48"). Split a fresh line before every marker that
/// follows other content on the same line.
public func expandOptionLines(_ text: String) -> String {
    regexReplace(#"([^\n\s])\s+(\(?[A-Ea-e]\s*[\)\.\:\-]\s+)"#, in: text, with: "$1\n$2")
}

/// Parse one question block into its stem and its A–D options, or nil
/// when fewer than two options were found.
public func parseOptions(_ text: String) -> ParsedQuestion? {
    let expanded = expandOptionLines(text)
    let lines = expanded.components(separatedBy: "\n")
    var opts: [ChoiceOption] = []
    var stemLines: [String] = []
    var current: ChoiceOption?
    var usedNum = false
    let optRe = #"^\s*\(?([A-Ea-e])\s*[\)\.\:\-]\s*(.+)$"#
    let numRe = #"^\s*\(?([1-5])\s*[\)\.\:\-]\s*(.+)$"#

    for line in lines {
        // Page chrome trailing the choices is not part of any choice.
        if !opts.isEmpty && regexContains(#"^\s*(show hint|back|next|ask anything|text view)\b"#, in: line, options: [.caseInsensitive]) {
            continue
        }
        // The quiz app's own grading lines under a choice are not part
        // of that choice either.
        if current != nil && regexContains(#"^\s*(correct|incorrect)\s*[!.]"#, in: line, options: [.caseInsensitive]) {
            continue
        }
        if let m = firstMatch(optRe, in: line) {
            current = ChoiceOption(letter: m[1].uppercased(), text: m[2].trimmingCharacters(in: .whitespaces))
            opts.append(current!)
            continue
        }
        if let nm = firstMatch(numRe, in: line) {
            // Numbered options (1. 2. 3. 4.) only count once a question
            // stem exists, and only in order — a lone "4." line after
            // some stem text is the next question's anchor, not D.
            let stemSoFar = stemLines.joined(separator: " ").trimmingCharacters(in: .whitespaces)
            if stemSoFar.count > 3 && ( !opts.isEmpty || stemSoFar.hasSuffix("?") || !stemLines.isEmpty ) {
                if let idx = Int(nm[1]), idx - 1 == opts.count, idx <= 5 {
                    usedNum = true
                    let letters = ["A", "B", "C", "D", "E"]
                    current = ChoiceOption(letter: letters[idx - 1], text: nm[2].trimmingCharacters(in: .whitespaces))
                    opts.append(current!)
                    continue
                }
            }
        }
        if let cur = current, !line.trimmingCharacters(in: .whitespaces).isEmpty {
            let updated = ChoiceOption(letter: cur.letter, text: cur.text + " " + line.trimmingCharacters(in: .whitespaces))
            current = updated
            opts[opts.count - 1] = updated
        } else if current == nil {
            stemLines.append(line)
        }
    }
    _ = usedNum
    if opts.count >= 2 {
        // Chrome glued to a choice on the same line ("$48 Show hint").
        opts = opts.map { o in
            var t = o.text
            t = regexReplace(#"\s+(show hint|ask anything)\b.*$"#, in: t, with: "", options: [.caseInsensitive])
            t = regexReplace(#"\s+(correct|incorrect)\s*[!.].*$"#, in: t, with: "", options: [.caseInsensitive])
            return ChoiceOption(letter: o.letter, text: t.trimmingCharacters(in: .whitespaces))
        }
        // Column layouts can read A,C down one side then B,D — put the
        // choices back in letter order when each letter appears once.
        var seen = Set<String>()
        var dup = false
        for o in opts { if seen.contains(o.letter) { dup = true }; seen.insert(o.letter) }
        if !dup { opts.sort { $0.letter < $1.letter } }
        return ParsedQuestion(stem: stemLines.joined(separator: " ").trimmingCharacters(in: .whitespaces), options: opts)
    }
    // Inline fallback: "Question? A. 24 B. 36 C. 48"
    let marker = #"(?:^|\s)([A-E])[\)\.]\s+"#
    var hits: [(letter: String, start: Int, contentStart: Int)] = []
    for r in allMatchRanges(marker, in: text) {
        // r.captures[1] is the letter; contentStart is the end of the match.
        hits.append((letter: r.captures[1].uppercased(), start: r.range.0, contentStart: r.range.0 + r.range.1))
    }
    if hits.count >= 3 && hits[0].letter == "A" {
        var inline: [ChoiceOption] = []
        let chars = Array(text)
        for i in hits.indices {
            let end = i + 1 < hits.count ? hits[i + 1].start : chars.count
            let slice = String(chars[hits[i].contentStart..<end]).trimmingCharacters(in: .whitespaces)
            inline.append(ChoiceOption(letter: hits[i].letter, text: slice))
        }
        let stem = String(chars[0..<hits[0].start]).trimmingCharacters(in: .whitespaces)
        return ParsedQuestion(stem: stem, options: inline)
    }
    return nil
}

// MARK: - Splitting a frame into question blocks

/// Split a raw read into one block per question. A numbered line starts
/// a fresh block once the previous block is a complete question, and a
/// fresh "A." after choices belong to the next question.
public func splitQuestions(_ text: String) -> [String] {
    let lines = text.components(separatedBy: "\n")
    var blocks: [[String]] = []
    var cur: [String]? = nil
    var curHasOpts = false
    var pending: [String] = []
    let optRe = #"^\s*\(?([A-Ea-e])\s*[\)\.\:\-]\s*(.+)$"#

    func startBlock(_ initial: [String]) {
        cur = initial
        blocks.append(initial)
        curHasOpts = false
        pending = []
    }
    func flushPending() {
        if cur != nil && !pending.isEmpty {
            blocks[blocks.count - 1] = blocks[blocks.count - 1] + pending
            cur = blocks[blocks.count - 1]
        }
        pending = []
    }

    for line in lines {
        let t = line.trimmingCharacters(in: .whitespaces)
        if t.isEmpty { continue }
        let optM = firstMatch(optRe, in: line)
        let isExplicitQ = regexContains(#"^\s*question\s*\d+"#, in: line, options: [.caseInsensitive])
        var qNumM = firstMatch(#"^\s*(?:question\s*)?(\d{1,3})\s*[\)\.\:]\s*(.+)$"#, in: line, options: [.caseInsensitive])
        // "3.5" or a bare "12. 350" line is a number, not a question
        // start — a question anchor's text carries letters or a "?".
        if let q = qNumM, !regexContains("[A-Za-z?]", in: q[2]) { qNumM = nil }

        let curJoined = (cur ?? []).joined(separator: " ").trimmingCharacters(in: .whitespaces)
        let prevDone = cur != nil && !curHasOpts && curJoined.hasSuffix("?")
        if optM == nil && cur != nil && (curHasOpts || prevDone) && (isExplicitQ || qNumM != nil) {
            let after: String
            if isExplicitQ {
                after = regexReplace(#"^\s*question\s*\d+\s*[\)\.\:\-]?\s*"#, in: t, with: "", options: [.caseInsensitive])
            } else {
                after = qNumM![2].trimmingCharacters(in: .whitespaces)
            }
            if isExplicitQ || after.contains("?") || after.split(separator: " ").count >= 4 {
                flushPending()
                startBlock([after])
                continue
            }
        }
        if let opt = optM {
            let letter = opt[1].uppercased()
            if cur == nil { startBlock([]) }
            if curHasOpts && letter == "A" {
                // Choices are starting over: the pending lines are the
                // stem of the next question.
                let stemLines = pending
                startBlock(stemLines)
                blocks[blocks.count - 1].append(line)
                cur = blocks[blocks.count - 1]
                curHasOpts = true
                continue
            }
            flushPending()
            blocks[blocks.count - 1].append(line)
            cur = blocks[blocks.count - 1]
            curHasOpts = true
            continue
        }
        if cur == nil { startBlock([]) }
        if curHasOpts {
            pending.append(line)
        } else {
            if (cur ?? []).isEmpty, let q = qNumM {
                let first = isExplicitQ
                    ? regexReplace(#"^\s*question\s*\d+\s*[\)\.\:\-]?\s*"#, in: t, with: "", options: [.caseInsensitive])
                    : q[2].trimmingCharacters(in: .whitespaces)
                blocks[blocks.count - 1].append(first)
                cur = blocks[blocks.count - 1]
            } else {
                blocks[blocks.count - 1].append(line)
                cur = blocks[blocks.count - 1]
            }
        }
    }
    if !pending.isEmpty {
        if cur != nil && curHasOpts && pending.joined(separator: " ").contains("?") {
            startBlock(pending)
        } else {
            flushPending()
        }
    }
    var out = blocks.map { $0.joined(separator: "\n").trimmingCharacters(in: .whitespaces) }.filter { !$0.isEmpty }
    if out.isEmpty && !text.trimmingCharacters(in: .whitespaces).isEmpty { out = [text.trimmingCharacters(in: .whitespaces)] }
    return out
}

// MARK: - Stems

/// Drop a leading "Question 1" / "1." marker from a stem.
public func cleanStem(_ stem: String) -> String {
    regexReplace(#"^\s*(?:question\s*)?\d{1,3}\s*[\)\.\:]\s+"#, in: stem, with: "", options: [.caseInsensitive])
        .trimmingCharacters(in: .whitespaces)
}

/// Cut a stem to its question anchor. Everything before the anchor is
/// page furniture — the quiz title, the "4/5" progress marker, chat
/// chrome — and left in, it breaks solving twice over: the progress
/// fraction is itself a solvable expression, and the question number
/// becomes a spurious operand. A decimal ("3.5 hours") is never an
/// anchor: its point is followed by a digit, not a capitalised word.
public func cutToQuestion(_ stem: String) -> String {
    let s = stem
    let anchor = #"(?:^|\s)(?:question\s+)?(\d{1,3})\s*[\)\.]\s*(?=[A-Z"“])"#
    for r in allMatchRanges(anchor, in: s, options: [.caseInsensitive]) {
        let rest = String(s.dropFirst(r.range.0 + r.range.1))
        let prefix = String(s.prefix(r.range.0))
        if prefix.contains("?") { continue }
        let prefixDigits = regexReplace(#"\b\d{1,3}\s*/\s*\d{1,3}\b"#, in: prefix, with: " ")
        if prefix.count > 40 && regexContains(#"\d"#, in: prefixDigits) { continue }
        if rest.split(separator: " ").count >= 4 || rest.contains("?") {
            return rest.trimmingCharacters(in: .whitespaces)
        }
    }
    // No anchor: still remove a progress marker ("4/5") sitting in the
    // leading furniture, and a leading question number.
    var head = String(s.prefix(60))
    let tail = String(s.dropFirst(min(60, s.count)))
    if !head.contains("?") {
        head = regexReplace(#"\b\d{1,3}\s*/\s*\d{1,3}\b"#, in: head, with: " ")
    }
    var out = (head + tail)
    out = regexReplace(#"^\s*\d{1,3}\s*/\s*\d{1,3}\s+"#, in: out, with: "")
    out = regexReplace(#"^\s*(?:question\s+)?\d{1,3}\s*[\)\.\:]\s*(?=[A-Za-z"“])"#, in: out, with: "", options: [.caseInsensitive])
    out = regexReplace(#"\s+"#, in: out, with: " ").trimmingCharacters(in: .whitespaces)
    return out.isEmpty ? s.trimmingCharacters(in: .whitespaces) : out
}

// MARK: - OCR clean-up

/// The reader often returns "V4" for "1/4" (the 1 reads as a V) and
/// "12" for "1/2" in a choice. Repair those before solving.
public func repairFractionOcr(_ text: String) -> String {
    var t = text
    var fixed = 0
    t = regexReplace(#"\b[VvUu](\d)\b"#, in: t, with: "1/$1")
    // Count how many choices carry a fraction, to know whether the
    // repair below is safe.
    let lines = t.components(separatedBy: "\n")
    var fracOpts = 0
    for l in lines where regexContains(#"^\s*\(?[A-Ea-e]\s*[\)\.\:\-]"#, in: l) && regexContains(#"\d+\s*/\s*\d+"#, in: l) {
        fracOpts += 1
    }
    var outLines = lines
    for (idx, l) in lines.enumerated() where regexContains(#"^\s*\(?[A-Ea-e]\s*[\)\.\:\-]\s*\d\d\s*$"#, in: l) {
        // "A. 12" at the end of a fraction question is really "A. 1/2".
        if fracOpts > 0 {
            outLines[idx] = regexReplace(#"^(\s*\(?[A-Ea-e]\s*[\)\.\:\-]\s*)(\d)(\d)\s*$"#, in: l, with: "$1$2/$3")
            fixed += 1
        }
    }
    if fixed == 0 {
        // A fraction in the stem lost its slash and its "?" ("1/4 1/4").
        if let firstOpt = lines.firstIndex(where: { regexContains(#"^\s*\(?[A-Ea-e]\s*[\)\.\:\-]"#, in: $0) }), firstOpt > 0 {
            outLines[firstOpt - 1] = regexReplace(#"(\d+)\s*/\s*(\d)\d\s*$"#, in: outLines[firstOpt - 1], with: "$1/$2?")
        }
    }
    return outLines.joined(separator: "\n")
}

/// The question to show at the top of a card: drop the quiz title,
/// chrome and noise lines, then drop leading sentences that carry
/// neither a number nor the question itself.
public func questionFocus(_ text: String) -> String {
    let chrome = ["show hint", "back", "next", "ask anything", "text view", "correct!", "incorrect."]
    let lines = text.components(separatedBy: "\n").map { $0.trimmingCharacters(in: .whitespaces) }
        .filter { !$0.isEmpty }
        .filter { line in !chrome.contains { line.lowercased().hasPrefix($0) } }
    guard !lines.isEmpty else { return text }
    // Drop leading lines that are neither the question nor carry a number.
    var start = 0
    while start < lines.count - 1 {
        let l = lines[start]
        if l.contains("?") || regexContains(#"\d"#, in: l) { break }
        start += 1
    }
    return lines[start...].joined(separator: " ")
}
