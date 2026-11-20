// QuestionCardView.swift
// One card per question in the frame: the question as I read it (with
// the calculation words highlighted for sentence-form maths), the
// printed choices with the answer marked, the one-line reason, and the
// source label — "WORKED OUT ON THIS PHONE" or "ANSWER FROM A WEB
// LOOKUP". A suggested answer is amber and says so plainly; a
// confirmed answer is green.

import SwiftUI

public struct QuestionCardView: View {
    public let index: Int
    public let total: Int
    public let blockResult: BlockResult
    public var onTeach: ((String) -> Void)?

    public init(index: Int, total: Int, blockResult: BlockResult, onTeach: ((String) -> Void)? = nil) {
        self.index = index
        self.total = total
        self.blockResult = blockResult
        self.onTeach = onTeach
    }

    public var body: some View {
        let res = blockResult.result
        VStack(alignment: .leading, spacing: 10) {
            if total > 1 {
                Text("Question \(index + 1) of \(total)")
                    .font(.caption.bold())
                    .foregroundColor(.secondary)
            }
            if let filled = res.filledInQuestion {
                Text(filled)
                    .font(.caption)
                    .foregroundColor(.orange)
            }
            questionText
            if let readAs = res.readAs {
                Text("READ AS: \(readAs)")
                    .font(.caption.monospaced())
                    .foregroundColor(.secondary)
            }
            if !blockResult.block.options.isEmpty {
                VStack(alignment: .leading, spacing: 6) {
                    ForEach(blockResult.block.options.indices, id: \.self) { i in
                        optionRow(blockResult.block.options[i], res: res)
                    }
                }
            }
            answerLine(res: res)
            if let flag = res.flag {
                Text(flag)
                    .font(.caption)
                    .foregroundColor(.orange)
            }
            HStack {
                Text(res.sourceLabel)
                    .font(.caption2.bold())
                    .foregroundColor(.secondary)
                Spacer()
                if res.status == .solved, let answer = res.answerText {
                    Button("Teach this answer") { onTeach?(answer) }
                        .font(.caption)
                }
            }
        }
        .padding(12)
        .background(Color(.secondarySystemBackground))
        .cornerRadius(12)
    }

    private var questionText: some View {
        let stem = blockResult.block.stem
        if let span = blockResult.result.highlight,
           span.0 >= 0, span.1 <= stem.count, span.0 < span.1 {
            let chars = Array(stem)
            let before = String(chars[0..<span.0])
            let marked = String(chars[span.0..<span.1])
            let after = String(chars[span.1...])
            return Text(before) + Text(marked).background(Color.yellow.opacity(0.45)) + Text(after)
        }
        return Text(stem.isEmpty ? blockResult.raw : stem)
    }

    private func optionRow(_ opt: ChoiceOption, res: SolveResult) -> some View {
        let isAnswer = res.letter == opt.letter && res.status == .solved
        let isMaybe = res.maybeLetters.contains(opt.letter)
        return HStack(alignment: .top, spacing: 8) {
            Text(opt.letter)
                .font(.subheadline.bold())
                .frame(width: 22, height: 22)
                .background(isAnswer ? (res.suggested ? Color.orange : Color.green) : Color(.tertiarySystemFill))
                .foregroundColor(isAnswer ? .white : .primary)
                .clipShape(Circle())
            Text(opt.text)
                .font(.subheadline)
            Spacer()
            if isAnswer {
                Text(res.suggested ? "SUGGESTED" : "✓ CORRECT")
                    .font(.caption2.bold())
                    .foregroundColor(res.suggested ? .orange : .green)
            } else if isMaybe {
                Text("POSSIBLE")
                    .font(.caption2.bold())
                    .foregroundColor(.orange)
            }
        }
        .padding(.vertical, 2)
    }

    private func answerLine(res: SolveResult) -> some View {
        Group {
            if res.status == .solved {
                HStack(alignment: .top, spacing: 6) {
                    if res.suggested {
                        Text("SUGGESTED · \(res.letter.map { $0 + " · " } ?? "")\(res.headline)")
                            .font(.headline)
                            .foregroundColor(.orange)
                    } else {
                        Text("\(res.letter.map { $0 + " · " } ?? "")\(res.headline)")
                            .font(.headline)
                            .foregroundColor(.primary)
                    }
                }
                if !res.detail.isEmpty {
                    Text(res.detail)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
            } else if res.status == .uncertain {
                VStack(alignment: .leading, spacing: 4) {
                    Text(res.headline)
                        .font(.headline)
                        .foregroundColor(.orange)
                    if !res.detail.isEmpty {
                        Text(res.detail)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
            } else {
                VStack(alignment: .leading, spacing: 4) {
                    Text(res.headline)
                        .font(.headline)
                    if !res.detail.isEmpty {
                        Text(res.detail)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
    }
}
