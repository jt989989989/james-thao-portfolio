// SelectableTextView.swift
// An editable text view that reports what I selected in it — the
// teach mode needs the selection, so I can mark it as the question or
// as the choices A–D and re-solve from the correction.

import SwiftUI
import UIKit

public struct SelectableTextView: UIViewRepresentable {
    @Binding public var text: String
    @Binding public var selectedText: String

    public init(text: Binding<String>, selectedText: Binding<String>) {
        self._text = text
        self._selectedText = selectedText
    }

    public func makeUIView(context: Context) -> UITextView {
        let view = UITextView()
        view.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        view.backgroundColor = UIColor.secondarySystemBackground
        view.layer.cornerRadius = 10
        view.textContainerInset = UIEdgeInsets(top: 10, left: 10, bottom: 10, right: 10)
        view.delegate = context.coordinator
        view.text = text
        return view
    }

    public func updateUIView(_ view: UITextView, context: Context) {
        if view.text != text {
            view.text = text
        }
    }

    public func makeCoordinator() -> Coordinator {
        Coordinator(text: $text, selectedText: $selectedText)
    }

    public final class Coordinator: NSObject, UITextViewDelegate {
        var text: Binding<String>
        var selectedText: Binding<String>

        init(text: Binding<String>, selectedText: Binding<String>) {
            self.text = text
            self.selectedText = selectedText
        }

        public func textViewDidChange(_ textView: UITextView) {
            text.wrappedValue = textView.text
        }

        public func textViewDidChangeSelection(_ textView: UITextView) {
            guard let range = textView.selectedTextRange,
                  !range.isEmpty,
                  let selected = textView.text(in: range) else {
                selectedText.wrappedValue = ""
                return
            }
            selectedText.wrappedValue = selected
        }
    }
}
