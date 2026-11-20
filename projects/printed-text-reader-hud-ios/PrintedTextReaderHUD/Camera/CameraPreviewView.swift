// CameraPreviewView.swift
// My camera view: the live preview with the green scan frame, the
// question and choice boxes drawn on it, and the answer highlight.
// Taps on the preview are reported back as normalised points
// (origin top-left) for tap-to-focus.

import SwiftUI
import AVFoundation

/// One box to draw on the camera. `rect` is normalised 0...1, origin
/// top-left — the same coordinates my reader uses.
public struct CameraOverlayBox: Equatable {
    public enum Style: Equatable {
        case question
        case choice
        case answer
        case suggested
        case tapQuestion
        case tapChoice
    }
    public let rect: TextBox
    public let style: Style
    public let label: String?
    /// A dot at this normalised point (tap-to-focus markers).
    public let dot: CGPoint?

    public init(rect: TextBox, style: Style, label: String? = nil, dot: CGPoint? = nil) {
        self.rect = rect; self.style = style; self.label = label; self.dot = dot
    }
}

public struct CameraPreviewView: UIViewRepresentable {
    public let session: AVCaptureSession
    public var boxes: [CameraOverlayBox]
    public var onTap: ((CGPoint) -> Void)?

    public init(session: AVCaptureSession, boxes: [CameraOverlayBox] = [], onTap: ((CGPoint) -> Void)? = nil) {
        self.session = session
        self.boxes = boxes
        self.onTap = onTap
    }

    public func makeUIView(context: Context) -> CameraPreviewUIView {
        let view = CameraPreviewUIView()
        view.previewLayer.session = session
        view.previewLayer.videoGravity = .resizeAspectFill
        let tap = UITapGestureRecognizer(target: context.coordinator, action: #selector(Coordinator.tapped(_:)))
        view.addGestureRecognizer(tap)
        return view
    }

    public func updateUIView(_ view: CameraPreviewUIView, context: Context) {
        context.coordinator.onTap = onTap
        view.normalizedBoxes = boxes
        view.refreshOverlay()
    }

    public func makeCoordinator() -> Coordinator {
        Coordinator(onTap: onTap)
    }

    public final class Coordinator: NSObject {
        var onTap: ((CGPoint) -> Void)?
        init(onTap: ((CGPoint) -> Void)?) { self.onTap = onTap }
        @objc func tapped(_ gesture: UITapGestureRecognizer) {
            guard let view = gesture.view as? CameraPreviewUIView else { return }
            let point = gesture.location(in: view)
            let meta = view.previewLayer.metadataOutputRectConverted(
                fromLayerRect: CGRect(x: point.x, y: point.y, width: 1, height: 1))
            onTap?(CGPoint(x: meta.midX, y: meta.midY))
        }
    }
}

/// A UIView whose layer IS the camera preview layer, with an overlay
/// view on top for the boxes.
public final class CameraPreviewUIView: UIView {
    override public class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }

    public var previewLayer: AVCaptureVideoPreviewLayer {
        // swiftlint:disable:next force_cast
        layer as! AVCaptureVideoPreviewLayer
    }

    public let overlay = CameraOverlayView()

    /// The boxes in normalised frame coordinates. They are converted
    /// into view space through the preview layer (which handles the
    /// aspect-fill crop) whenever the view lays out, so a rotation
    /// cannot leave stale boxes behind.
    public var normalizedBoxes: [CameraOverlayBox] = [] {
        didSet { refreshOverlay() }
    }

    override public init(frame: CGRect) {
        super.init(frame: frame)
        overlay.backgroundColor = .clear
        overlay.isUserInteractionEnabled = false
        addSubview(overlay)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override public func layoutSubviews() {
        super.layoutSubviews()
        overlay.frame = bounds
        refreshOverlay()
    }

    public func refreshOverlay() {
        guard bounds.width > 0, bounds.height > 0 else { return }
        let viewBoxes: [(CGRect, CameraOverlayBox)] = normalizedBoxes.compactMap { box in
            let meta = CGRect(x: box.rect.x0, y: box.rect.y0,
                              width: box.rect.width, height: box.rect.height)
            let converted = previewLayer.layerRectConverted(fromMetadataOutputRect: meta)
            guard converted.width > 0, converted.height > 0 else { return nil }
            return (converted, box)
        }
        let viewDots: [(CGPoint, CameraOverlayBox.Style)] = normalizedBoxes.compactMap { box in
            guard let dot = box.dot else { return nil }
            let meta = CGRect(x: dot.x, y: dot.y, width: 0.001, height: 0.001)
            let converted = previewLayer.layerRectConverted(fromMetadataOutputRect: meta)
            return (CGPoint(x: converted.midX, y: converted.midY), box.style)
        }
        overlay.setBoxes(viewBoxes, dots: viewDots)
    }
}

/// Draws the boxes: the green scan frame, the amber question box, blue
/// dashed choice boxes, the green answer box (or amber dashed for a
/// suggestion), and the tap markers.
public final class CameraOverlayView: UIView {
    private var boxes: [(CGRect, CameraOverlayBox)] = []
    private var dots: [(CGPoint, CameraOverlayBox.Style)] = []

    public func setBoxes(_ boxes: [(CGRect, CameraOverlayBox)], dots: [(CGPoint, CameraOverlayBox.Style)]) {
        self.boxes = boxes
        self.dots = dots
        setNeedsDisplay()
    }

    override public func draw(_ rect: CGRect) {
        guard let ctx = UIGraphicsGetCurrentContext() else { return }
        // The green scan frame: the whole camera view is my frame.
        ctx.setStrokeColor(UIColor.systemGreen.cgColor)
        ctx.setLineWidth(3)
        ctx.stroke(bounds.insetBy(dx: 1.5, dy: 1.5))

        for (boxRect, box) in boxes {
            let padded = boxRect.insetBy(dx: -6, dy: -4)
            let path = UIBezierPath(roundedRect: padded, cornerRadius: 8)
            switch box.style {
            case .question:
                UIColor.systemOrange.setStroke()
                UIColor.systemOrange.withAlphaComponent(0.12).setFill()
                ctx.setLineWidth(3)
                path.fill(); path.stroke()
            case .choice:
                UIColor.systemBlue.setStroke()
                ctx.setLineWidth(2)
                ctx.setLineDash(phase: 0, lengths: [6, 4])
                path.stroke()
                ctx.setLineDash(phase: 0, lengths: [])
            case .answer:
                UIColor.systemGreen.setStroke()
                UIColor.systemGreen.withAlphaComponent(0.18).setFill()
                ctx.setLineWidth(4)
                path.fill(); path.stroke()
            case .suggested:
                UIColor.systemOrange.setStroke()
                UIColor.systemOrange.withAlphaComponent(0.12).setFill()
                ctx.setLineWidth(3)
                ctx.setLineDash(phase: 0, lengths: [8, 5])
                path.fill(); path.stroke()
                ctx.setLineDash(phase: 0, lengths: [])
            case .tapQuestion:
                UIColor.systemOrange.setStroke()
                ctx.setLineWidth(2)
                ctx.setLineDash(phase: 0, lengths: [6, 4])
                path.stroke()
                ctx.setLineDash(phase: 0, lengths: [])
            case .tapChoice:
                UIColor.systemBlue.setStroke()
                ctx.setLineWidth(2)
                ctx.setLineDash(phase: 0, lengths: [6, 4])
                path.stroke()
                ctx.setLineDash(phase: 0, lengths: [])
            }
            if let label = box.label {
                drawLabel(label, at: padded, style: box.style)
            }
        }
        for (point, style) in dots {
            let color: UIColor = style == .tapQuestion ? .systemOrange : .systemBlue
            color.setFill()
            ctx.fillEllipse(in: CGRect(x: point.x - 6, y: point.y - 6, width: 12, height: 12))
            UIColor.white.setStroke()
            ctx.setLineWidth(2)
            ctx.strokeEllipse(in: CGRect(x: point.x - 6, y: point.y - 6, width: 12, height: 12))
        }
    }

    private func drawLabel(_ text: String, at rect: CGRect, style: CameraOverlayBox.Style) {
        let color: UIColor
        switch style {
        case .question, .tapQuestion, .suggested: color = .systemOrange
        case .choice, .tapChoice: color = .systemBlue
        case .answer: color = .systemGreen
        }
        let attrs: [NSAttributedString.Key: Any] = [
            .font: UIFont.boldSystemFont(ofSize: 13),
            .foregroundColor: UIColor.white
        ]
        let size = (text as NSString).size(withAttributes: attrs)
        let chip = CGRect(x: rect.minX, y: max(0, rect.minY - 22),
                          width: size.width + 12, height: 20)
        let path = UIBezierPath(roundedRect: chip, cornerRadius: 6)
        color.setFill()
        path.fill()
        (text as NSString).draw(at: CGPoint(x: chip.minX + 6, y: chip.minY + 2), withAttributes: attrs)
    }
}
