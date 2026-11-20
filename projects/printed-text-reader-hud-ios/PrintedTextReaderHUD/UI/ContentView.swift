// ContentView.swift
// My main screen: the camera on top with the scan frame, the answer
// banner, and the per-question cards below — no scrolling to see an
// answer. Everything reads on this phone; the camera image is never
// uploaded. Maths never leaves the phone either — only a general
// knowledge question I cannot solve on-device goes to Wikipedia.

import SwiftUI
import PhotosUI
import UIKit

@MainActor
final class ScanModel: ObservableObject {
    // My camera, my reader, my solver.
    let camera = CameraManager()
    let recognizer = TextRecognizer()
    let solver = Solver()

    @Published var status = "Ready — point the camera at a printed question."
    @Published var results: [BlockResult] = []
    @Published var rawText = ""
    @Published var selectedText = ""
    @Published var isScanning = false
    @Published var tapToFocus = false
    @Published var autoScan = false
    @Published var overlayBoxes: [CameraOverlayBox] = []
    @Published var bannerLines: [(text: String, suggested: Bool)] = []
    @Published var choicesSeen: [String] = []
    @Published var tapStep: TapStep = .question

    var currentRead: RecognizedText?
    private var tapQuestionRead: RecognizedText?
    private var tapMarkers: [CameraOverlayBox] = []

    enum TapStep { case question, choices }

    private let taughtKey = "PrintedTextReaderHUD.taughtAnswers"

    init() {
        solver.wikiFetcher = { query in await fetchWikiCorpus(query) }
        solver.dictionaryFetcher = { word in await fetchDictionaryWord(word) }
        loadTaughtAnswers()
    }

    // MARK: - Lifecycle

    func start() async {
        _ = await camera.requestAccessAndStart()
        if camera.accessDenied {
            status = "Camera access is off — turn it on in Settings, then come back."
        }
    }

    func stopCamera() {
        camera.stop()
    }

    // MARK: - Full-frame scan

    func scan() async {
        guard camera.isRunning, !isScanning else { return }
        isScanning = true
        defer { isScanning = false }
        tapMarkers = []
        status = "Reading…"
        let frames = await camera.captureBurst()
        guard !frames.isEmpty else {
            status = "No frame yet — hold the camera steady and try again."
            return
        }
        // Burst of frames: read each, keep the sharpest.
        var bestRead: RecognizedText?
        var bestImage: CGImage?
        for img in frames {
            let read = await recognizer.recognizeWithPolarityRetry(img)
            let col = read.mainColumn()
            if bestRead == nil || col.qualityScore() > bestRead!.qualityScore() {
                bestRead = col
                bestImage = img
            }
        }
        guard var read = bestRead, let image = bestImage else {
            status = "Nothing readable in this frame."
            return
        }
        // The choices are the faint part — white text on dark pills. If
        // the whole-frame read found fewer than three, re-read just the
        // choice rows, enlarged, and merge them back in.
        if read.choiceBoxes().count < 3, let band = choiceBand(in: read) {
            let strip = await recognizer.recognizeBand(image, band: band)
            let merged = RecognizedText(lines: read.lines + strip.lines)
            let col = merged.mainColumn()
            if col.choiceBoxes().count > read.choiceBoxes().count { read = col }
        }
        guard !read.lines.isEmpty else {
            status = "Nothing readable in this frame."
            return
        }
        await process(read: read)
        if read.qualityScore() < 8 {
            status += " The read was shaky — brace the phone and scan again."
        }
    }

    /// The band the choice rows sit in (or, when no choices were found,
    /// the area below the question) — for the enlarged choice re-read.
    private func choiceBand(in read: RecognizedText) -> TextBox? {
        let boxes = read.choiceBoxes()
        if !boxes.isEmpty {
            let y0 = max(0, boxes.map { $0.box.y0 }.min()! - 0.02)
            let y1 = min(1, boxes.map { $0.box.y1 }.max()! + 0.02)
            return TextBox(x0: 0, y0: y0, x1: 1, y1: y1)
        }
        if let stem = read.stemBox() {
            return TextBox(x0: 0, y0: stem.y1, x1: 1, y1: 0.95)
        }
        return nil
    }

    /// A read (from the camera, a tap, or a photo) becomes cards,
    /// overlay boxes and a banner.
    func process(read: RecognizedText) async {
        currentRead = read
        rawText = read.text
        results = await solver.solve(read.text)
        updateOverlay()
        let solved = results.filter { $0.result.status == .solved }.count
        let total = results.count
        if total == 0 {
            status = "Read it, but found no question — check the text below."
        } else if total == 1 {
            status = solved == 1 ? "Read complete — 1 solved." : "Read complete — needs a check."
        } else {
            status = "Read complete — \(solved) of \(total) solved."
        }
    }

    func processPhoto(_ image: UIImage) async {
        guard let cg = image.cgImage else { return }
        isScanning = true
        defer { isScanning = false }
        status = "Reading your photo…"
        let read = await recognizer.recognizeWithPolarityRetry(cg)
        let col = read.mainColumn()
        guard !col.lines.isEmpty else {
            status = "Nothing readable in this photo."
            return
        }
        await process(read: col)
    }

    // MARK: - Tap to focus

    func handleTap(at point: CGPoint) async {
        guard tapToFocus, camera.isRunning, !isScanning else { return }
        guard let frame = camera.latestFrameImage() else {
            status = "The camera hasn't delivered a frame yet — wait a second and tap again."
            return
        }
        isScanning = true
        defer { isScanning = false }
        switch tapStep {
        case .question:
            let band = TextBox(x0: 0, y0: max(0, point.y - 0.11), x1: 1, y1: min(1, point.y + 0.11))
            let read = await recognizer.recognizeBand(frame, band: band)
            tapQuestionRead = read
            tapMarkers = [CameraOverlayBox(rect: band, style: .tapQuestion, label: "TAP · QUESTION", dot: point)]
            tapStep = .choices
            status = "Got the question — now tap the middle of the choices."
            updateOverlay()
        case .choices:
            let band = TextBox(x0: 0, y0: max(0, point.y - 0.11), x1: 1, y1: min(1, point.y + 0.11))
            var read = await recognizer.recognizeBand(frame, band: band)
            if read.choiceBoxes().count < 3 {
                read = await recognizer.recognizeBandBlackAndWhite(frame, band: band)
            }
            tapMarkers.append(CameraOverlayBox(rect: band, style: .tapChoice, label: "TAP · CHOICES", dot: point))
            let combined = RecognizedText(lines: (tapQuestionRead?.lines ?? []) + read.lines)
            await process(read: combined)
            tapStep = .question
            status = "Tap the next question, or turn Tap to focus off."
        }
    }

    func restartTap() {
        tapMarkers = []
        tapQuestionRead = nil
        tapStep = .question
        updateOverlay()
        status = "Tap the question, then tap the choices."
    }

    func solveQuestionOnly() async {
        guard let read = tapQuestionRead, !read.lines.isEmpty else { return }
        await process(read: read)
    }

    // MARK: - Overlay, banner, pills

    private func updateOverlay() {
        var boxes: [CameraOverlayBox] = []
        if let read = currentRead {
            for (letter, box) in read.choiceBoxes() {
                boxes.append(CameraOverlayBox(rect: box, style: .choice, label: letter))
            }
            if let stemBox = read.stemBox() {
                boxes.append(CameraOverlayBox(rect: stemBox, style: .question, label: "QUESTION"))
            }
            for result in results where result.result.status == .solved {
                if let letter = result.result.letter,
                   let box = read.optionBox(letter: letter, answerText: result.result.answerText) {
                    let style: CameraOverlayBox.Style = result.result.suggested ? .suggested : .answer
                    boxes.append(CameraOverlayBox(rect: box, style: style, label: letter))
                }
            }
            choicesSeen = read.choiceBoxes().map { $0.0 }.sorted()
        } else {
            choicesSeen = results.flatMap { $0.block.options.map { $0.letter } }.sorted()
        }
        overlayBoxes = boxes + tapMarkers
        bannerLines = results.enumerated().compactMap { idx, r in
            guard r.result.status == .solved else { return nil }
            let prefix = results.count > 1 ? "Q\(idx + 1) · " : ""
            let sugg = r.result.suggested ? "SUGGESTED · " : ""
            let letter = r.result.letter.map { $0 + " · " } ?? ""
            return (text: "\(prefix)\(sugg)\(letter)\(r.result.headline)", suggested: r.result.suggested)
        }
    }

    // MARK: - Teach / correct

    func teach(answer: String, for blockIndex: Int) {
        guard blockIndex < results.count else { return }
        let stem = normText(cutToQuestion(results[blockIndex].block.stem))
        solver.taughtAnswers[stem] = answer
        saveTaughtAnswers()
        status = "Taught — I'll answer \"\(answer)\" for this question from now on, whatever letter it sits under."
    }

    func markSelectionAsQuestion() async {
        guard !selectedText.isEmpty, let first = results.first else { return }
        let choiceLines = first.block.options.map { "\($0.letter). \($0.text)" }.joined(separator: "\n")
        let corrected = selectedText.trimmingCharacters(in: .whitespacesAndNewlines) + "\n" + choiceLines
        let solved = await solver.solve(corrected)
        if let one = solved.first {
            results[0] = one
            rawText = corrected
            updateOverlay()
            status = "Question marked from your selection — re-solved from your correction."
        }
    }

    func markSelectionAsChoices() async {
        guard !selectedText.isEmpty, let first = results.first else { return }
        let corrected = first.block.stem + "\n" + selectedText.trimmingCharacters(in: .whitespacesAndNewlines)
        let solved = await solver.solve(corrected)
        if let one = solved.first {
            results[0] = one
            rawText = corrected
            updateOverlay()
            status = "Choices marked from your selection — re-solved from your correction."
        }
    }

    func resolveFromEditedText() async {
        guard !rawText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        currentRead = nil
        results = await solver.solve(rawText)
        updateOverlay()
        status = "Re-solved from the corrected text."
    }

    // MARK: - Taught answers, persisted on this phone

    private func loadTaughtAnswers() {
        guard let data = UserDefaults.standard.data(forKey: taughtKey),
              let saved = try? JSONDecoder().decode([String: String].self, from: data) else { return }
        solver.taughtAnswers = saved
    }

    private func saveTaughtAnswers() {
        guard let data = try? JSONEncoder().encode(solver.taughtAnswers) else { return }
        UserDefaults.standard.set(data, forKey: taughtKey)
    }
}

// MARK: - The screen

public struct ContentView: View {
    @StateObject private var model = ScanModel()
    @State private var showingPhotoPicker = false

    public init() {}

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    cameraSection
                    controlsSection
                    if model.tapToFocus { tapHelpSection }
                    resultsSection
                    rawTextSection
                    aboutSection
                }
                .padding()
            }
            .navigationTitle("Printed Text Reader HUD")
            .navigationBarTitleDisplayMode(.inline)
        }
        .onAppear { Task { await model.start() } }
        .sheet(isPresented: $showingPhotoPicker) {
            PhotoPicker { image in
                Task { await model.processPhoto(image) }
            }
        }
        .onReceive(Timer.publish(every: 2.5, on: .main, in: .common).autoconnect()) { _ in
            if model.autoScan { Task { await model.scan() } }
        }
    }

    // MARK: Camera

    private var cameraSection: some View {
        ZStack(alignment: .top) {
            if model.camera.isRunning {
                CameraPreviewView(session: model.camera.session, boxes: model.overlayBoxes) { point in
                    Task { await model.handleTap(at: point) }
                }
                .frame(height: 380)
                .cornerRadius(14)
            } else {
                RoundedRectangle(cornerRadius: 14)
                    .fill(Color(.secondarySystemBackground))
                    .frame(height: 380)
                    .overlay(
                        VStack(spacing: 10) {
                            Image(systemName: "camera.fill")
                                .font(.largeTitle)
                                .foregroundColor(.secondary)
                            Text(model.camera.accessDenied
                                 ? "Camera access is off. Turn it on in Settings, then come back."
                                 : "Starting the camera…")
                                .multilineTextAlignment(.center)
                                .foregroundColor(.secondary)
                        }
                        .padding()
                    )
            }
            // Status pills.
            VStack(spacing: 8) {
                HStack(spacing: 8) {
                    pill("●  QUESTION SOLVER", color: .green)
                    pill(model.isScanning ? "READING…" : "READER READY", color: .white)
                    if !model.choicesSeen.isEmpty {
                        pill("CHOICES SEEN · " + model.choicesSeen.joined(separator: " "), color: .blue)
                    }
                    Spacer()
                }
                HStack {
                    Text("ONLY TEXT INSIDE THIS FRAME IS READ")
                        .font(.caption2.bold())
                        .padding(.horizontal, 10)
                        .padding(.vertical, 5)
                        .background(Color.black.opacity(0.6))
                        .foregroundColor(.white)
                        .cornerRadius(8)
                    Spacer()
                }
                Spacer()
                if !model.bannerLines.isEmpty {
                    VStack(alignment: .leading, spacing: 6) {
                        ForEach(model.bannerLines.indices, id: \.self) { i in
                            HStack(alignment: .top, spacing: 8) {
                                Image(systemName: model.bannerLines[i].suggested ? "lightbulb" : "checkmark.circle.fill")
                                    .foregroundColor(model.bannerLines[i].suggested ? .orange : .green)
                                Text(model.bannerLines[i].text)
                                    .font(.subheadline.bold())
                                    .foregroundColor(.white)
                            }
                        }
                    }
                    .padding(10)
                    .background(Color.black.opacity(0.65))
                    .cornerRadius(10)
                }
            }
            .padding(10)
        }
    }

    private func pill(_ text: String, color: Color) -> some View {
        Text(text)
            .font(.caption2.bold())
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .background(Color.black.opacity(0.6))
            .foregroundColor(color)
            .cornerRadius(8)
    }

    // MARK: Controls

    private var controlsSection: some View {
        VStack(spacing: 10) {
            Text(model.status)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
            HStack(spacing: 10) {
                Button(model.camera.isRunning ? "Stop camera" : "Start camera") {
                    if model.camera.isRunning {
                        model.stopCamera()
                    } else {
                        Task { await model.start() }
                    }
                }
                .buttonStyle(.bordered)
                Button("Scan & solve") {
                    Task { await model.scan() }
                }
                .buttonStyle(.borderedProminent)
                .tint(.green)
                .disabled(!model.camera.isRunning || model.isScanning)
            }
            HStack(spacing: 10) {
                toggleButton("Tap to focus", isOn: model.tapToFocus) {
                    model.tapToFocus.toggle()
                    if model.tapToFocus {
                        model.status = "Tap the question, then tap the choices."
                    }
                }
                toggleButton("Auto-scan", isOn: model.autoScan) {
                    model.autoScan.toggle()
                }
                Button("Photo") { showingPhotoPicker = true }
                    .buttonStyle(.bordered)
            }
            Text("Reading happens on this device — the camera image is never uploaded.")
                .font(.caption)
                .foregroundColor(.secondary)
        }
    }

    private func toggleButton(_ title: String, isOn: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .padding(.horizontal, 4)
        }
        .buttonStyle(.bordered)
        .tint(isOn ? .green : nil)
    }

    private var tapHelpSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Tap to focus: turn it on, then tap the question on the camera (finger or mouse) to read only that area, then tap the choices to read only those — the two reads are combined and solved, with the answer highlighted on the camera.")
                .font(.caption)
                .foregroundColor(.secondary)
            HStack(spacing: 10) {
                Button("Restart") { model.restartTap() }
                    .buttonStyle(.bordered)
                Button("Solve question only") { Task { await model.solveQuestionOnly() } }
                    .buttonStyle(.bordered)
                Button("Exit") { model.tapToFocus = false }
                    .buttonStyle(.bordered)
            }
        }
    }

    // MARK: Results

    private var resultsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            if !model.results.isEmpty {
                let solved = model.results.filter { $0.result.status == .solved }.count
                let pending = model.results.count - solved
                Text("\(model.results.count) question\(model.results.count == 1 ? "" : "s") in this frame · \(solved) solved" + (pending > 0 ? " · \(pending) need\(pending == 1 ? "s" : "") a check" : ""))
                    .font(.subheadline.bold())
                ForEach(model.results.indices, id: \.self) { i in
                    QuestionCardView(index: i, total: model.results.count, blockResult: model.results[i]) { answer in
                        model.teach(answer: answer, for: i)
                    }
                }
            }
        }
    }

    // MARK: Raw text + teach

    private var rawTextSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            if !model.rawText.isEmpty {
                Text("TEXT IT READ — CORRECT IT & RE-SOLVE")
                    .font(.caption.bold())
                    .foregroundColor(.secondary)
                Text("Scanner found: \(model.results.count) question\(model.results.count == 1 ? "" : "s") · \(model.choicesSeen.count) choices seen. If the question or choices are wrong above, select those lines and mark them, or fix the text and re-solve.")
                    .font(.caption)
                    .foregroundColor(.secondary)
                SelectableTextView(text: $model.rawText, selectedText: $model.selectedText)
                    .frame(height: 140)
                HStack(spacing: 10) {
                    Button("Mark selection as the question") {
                        Task { await model.markSelectionAsQuestion() }
                    }
                    .buttonStyle(.bordered)
                    .disabled(model.selectedText.isEmpty)
                    Button("Mark selection as choices A–D") {
                        Task { await model.markSelectionAsChoices() }
                    }
                    .buttonStyle(.bordered)
                    .disabled(model.selectedText.isEmpty)
                }
                Button("Re-solve from this text") {
                    Task { await model.resolveFromEditedText() }
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }

    // MARK: About

    private var aboutSection: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("I read printed questions with your camera and work out the answer — maths, multiple choice, and word definitions — right on your phone. A green box is a confirmed answer; an amber box is my best guess, not a confirmation. I am a prototype, not a full AI: my cybersecurity bank is study knowledge only. I hold CompTIA Security+, not CISSP.")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding(.top, 4)
    }
}

// MARK: - Photo picker

public struct PhotoPicker: UIViewControllerRepresentable {
    public var onPick: (UIImage) -> Void

    public init(onPick: @escaping (UIImage) -> Void) {
        self.onPick = onPick
    }

    public func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration()
        config.filter = .images
        config.selectionLimit = 1
        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    public func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {}

    public func makeCoordinator() -> Coordinator {
        Coordinator(onPick: onPick)
    }

    public final class Coordinator: NSObject, PHPickerViewControllerDelegate {
        var onPick: (UIImage) -> Void
        init(onPick: @escaping (UIImage) -> Void) { self.onPick = onPick }

        public func picker(_ picker: PHPickerViewController, didFinishPicking results: [PHPickerResult]) {
            picker.dismiss(animated: true)
            guard let item = results.first else { return }
            item.itemProvider.loadObject(ofClass: UIImage.self) { [weak self] object, _ in
                guard let image = object as? UIImage else { return }
                Task { @MainActor in self?.onPick(image) }
            }
        }
    }
}
