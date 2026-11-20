// RecognizedText.swift
// What the reader saw: lines of text with their positions in the frame.
// Positions are normalised 0...1 with the origin at the TOP-LEFT, so
// the camera overlay, the question box and the choice boxes all speak
// the same coordinates. Pure Swift — no Vision types here — so the
// layout rules can be tested anywhere.
//
// The key rule: the reader returns every word inside the frame,
// including papers on the desk beside the phone. I rebuild the read
// from the words' positions and keep only the column the question and
// its choice rows sit in, so desk print and symbol scraps never reach
// the text box, the question, or the on-camera boxes.

import Foundation

/// A box in the frame, normalised 0...1, origin top-left.
public struct TextBox: Sendable, Equatable {
    public var x0: Double
    public var y0: Double
    public var x1: Double
    public var y1: Double

    public init(x0: Double, y0: Double, x1: Double, y1: Double) {
        self.x0 = x0; self.y0 = y0; self.x1 = x1; self.y1 = y1
    }

    public var width: Double { x1 - x0 }
    public var height: Double { y1 - y0 }
    public var centerX: Double { (x0 + x1) / 2 }
    public var centerY: Double { (y0 + y1) / 2 }

    public func union(_ other: TextBox) -> TextBox {
        TextBox(x0: min(x0, other.x0), y0: min(y0, other.y0),
                x1: max(x1, other.x1), y1: max(y1, other.y1))
    }

    public func insetBy(dx: Double, dy: Double) -> TextBox {
        TextBox(x0: max(0, x0 - dx), y0: max(0, y0 - dy),
                x1: min(1, x1 + dx), y1: min(1, y1 + dy))
    }
}

/// One line the reader found, with its position and confidence.
public struct RecognizedLine: Sendable {
    public let text: String
    public let box: TextBox
    public let confidence: Float
    public init(text: String, box: TextBox, confidence: Float) {
        self.text = text; self.box = box; self.confidence = confidence
    }
}

/// A whole read of one frame (or one cropped band).
public struct RecognizedText: Sendable {
    public let lines: [RecognizedLine]

    public init(lines: [RecognizedLine]) { self.lines = lines }

    /// The read as plain text, one line per row, top to bottom.
    public var text: String {
        lines.sorted { $0.box.centerY < $1.box.centerY }
            .map { $0.text }.joined(separator: "\n")
    }

    /// How good this read is: average confidence weighted by words,
    /// plus a bonus when it carries choices and a question mark. Used
    /// to pick the sharpest frame out of a burst.
    public func qualityScore() -> Double {
        guard !lines.isEmpty else { return 0 }
        let words = lines.reduce(0) { $0 + $1.text.split(separator: " ").count }
        let avgConf = lines.reduce(0.0) { $0 + Double($1.confidence) } / Double(lines.count)
        var score = avgConf * Double(words)
        let choiceLines = lines.filter { isChoiceLine($0.text) }.count
        if choiceLines >= 3 { score += 10 }
        if lines.contains(where: { $0.text.contains("?") }) { score += 2 }
        return score
    }

    /// Keep only the column the question and choices sit in. The column
    /// is defined by the lettered choice lines (and the question line);
    /// anything whose centre sits outside it — desk papers, symbol
    /// scraps — is dropped. With no anchors, the read is returned as-is.
    public func mainColumn() -> RecognizedText {
        let anchors = lines.filter { isChoiceLine($0.text) || isQuestionLine($0.text) }
        guard !anchors.isEmpty else { return self }
        var lo = anchors.map { $0.box.x0 }.min() ?? 0
        var hi = anchors.map { $0.box.x1 }.max() ?? 1
        lo = max(0, lo - 0.05)
        hi = min(1, hi + 0.05)
        let kept = lines.filter { line in
            guard line.box.centerX >= lo && line.box.centerX <= hi else { return false }
            // Symbol scraps: a lone "%" or "¢" the reader invented out
            // of screen texture.
            let trimmed = line.text.trimmingCharacters(in: .whitespaces)
            if trimmed.count < 2 && line.confidence < 0.6 { return false }
            return true
        }
        return RecognizedText(lines: kept)
    }

    /// The box covering the question's lines — the stem lines before
    /// the first choice line — for the amber QUESTION box on camera.
    public func stemBox() -> TextBox? {
        let sorted = lines.sorted { $0.box.centerY < $1.box.centerY }
        var stem: [RecognizedLine] = []
        for line in sorted {
            if isChoiceLine(line.text) { break }
            stem.append(line)
        }
        guard !stem.isEmpty else { return nil }
        return stem.map { $0.box }.reduce(stem[0].box) { $0.union($1) }
    }

    /// The box of the choice whose text matches `answerText` (by text,
    /// never by letter), or the choice under `letter` as a fallback.
    public func optionBox(letter: String, answerText: String?) -> TextBox? {
        let sorted = lines.sorted { $0.box.centerY < $1.box.centerY }
        if let answerText = answerText, !answerText.isEmpty {
            let norm = normText(answerText)
            // Full text match first.
            for line in sorted where isChoiceLine(line.text) {
                if normText(choiceText(of: line.text)) == norm { return line.box }
            }
            // Then a strong token match.
            let aToks = Set(norm.split(separator: " ").map(String.init).filter { $0.count >= 3 })
            if !aToks.isEmpty {
                var best: (TextBox, Int)?
                for line in sorted where isChoiceLine(line.text) {
                    let toks = Set(normText(choiceText(of: line.text)).split(separator: " ").map(String.init))
                    let hits = aToks.intersection(toks).count
                    if hits == aToks.count && (best == nil || hits > best!.1) { best = (line.box, hits) }
                }
                if let best = best { return best.0 }
            }
        }
        for line in sorted where choiceLetter(of: line.text) == letter.uppercased() {
            return line.box
        }
        return nil
    }

    /// The boxes of every choice found, in letter order.
    public func choiceBoxes() -> [(letter: String, box: TextBox)] {
        lines.filter { isChoiceLine($0.text) }
            .compactMap { line -> (String, TextBox)? in
                guard let l = choiceLetter(of: line.text) else { return nil }
                return (l, line.box)
            }
            .sorted { $0.0 < $1.0 }
    }

    // MARK: - Line shapes

    private func isChoiceLine(_ text: String) -> Bool {
        regexContains(#"^\s*\(?[A-Ea-e]\s*[\)\.\:\-]\s*\S"#, in: text)
    }

    private func isQuestionLine(_ text: String) -> Bool {
        text.contains("?") || regexContains(#"^\s*(?:question\s*)?\d{1,3}\s*[\)\.\:]\s+\S"#, in: text, options: [.caseInsensitive])
    }

    private func choiceLetter(of text: String) -> String? {
        firstMatch(#"^\s*\(?([A-Ea-e])\s*[\)\.\:\-]"#, in: text).map { $0[1].uppercased() }
    }

    private func choiceText(of text: String) -> String {
        if let m = firstMatch(#"^\s*\(?[A-Ea-e]\s*[\)\.\:\-]\s*(.+)$"#, in: text) { return m[1] }
        return text
    }
}
