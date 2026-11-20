// TextRecognizer.swift
// My reader: Apple's Vision framework, on this phone. VNRecognizeTextRequest
// gives me the text AND the exact word positions, which is what the web
// version's Tesseract could never do reliably on a photographed screen.
// Dark screens are auto-inverted and re-read; a cropped band (tap to
// focus, or the choice rows alone) is read enlarged and mapped back
// into frame coordinates.

import Foundation
import Vision
import CoreImage

public final class TextRecognizer {
    private let ciContext = CIContext()

    public init() {}

    /// Read one image with Vision (accurate recognition, language
    /// correction on). Returns lines in reading order with normalised
    /// boxes, origin top-left.
    public func recognize(_ cgImage: CGImage) async -> RecognizedText {
        await Task.detached(priority: .userInitiated) {
            let request = VNRecognizeTextRequest()
            request.recognitionLevel = .accurate
            request.usesLanguageCorrection = true
            request.recognitionLanguages = ["en-US"]
            let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
            try? handler.perform([request])
            let lines: [RecognizedLine] = (request.results ?? []).compactMap { result in
                guard let obs = result as? VNRecognizedTextObservation,
                      let candidate = obs.topCandidates(1).first else { return nil }
                let bb = obs.boundingBox
                // Vision's origin is bottom-left; mine is top-left.
                let box = TextBox(x0: Double(bb.minX), y0: Double(1 - bb.maxY),
                                  x1: Double(bb.maxX), y1: Double(1 - bb.minY))
                return RecognizedLine(text: candidate.string, box: box, confidence: obs.confidence)
            }
            return RecognizedText(lines: lines)
        }.value
    }

    /// Read, and if the frame is a dark screen (light text on dark),
    /// also read an inverted copy and keep whichever reads better.
    /// Dark-mode quiz apps are the common case for a bad first read.
    public func recognizeWithPolarityRetry(_ cgImage: CGImage) async -> RecognizedText {
        let normal = await recognize(cgImage)
        guard meanLuminance(of: cgImage) < 0.4,
              let inverted = invertedImage(cgImage) else { return normal }
        let inv = await recognize(inverted)
        return inv.qualityScore() > normal.qualityScore() ? inv : normal
    }

    /// Read only a band of the image (tap to focus, or the choice rows
    /// on their own), enlarged, with every box mapped back into frame
    /// coordinates so the camera overlay still lands in the right place.
    public func recognizeBand(_ cgImage: CGImage, band: TextBox) async -> RecognizedText {
        let w = cgImage.width, h = cgImage.height
        let rect = CGRect(x: Int(band.x0 * Double(w)), y: Int(band.y0 * Double(h)),
                          width: max(1, Int(band.width * Double(w))),
                          height: max(1, Int(band.height * Double(h))))
        guard let cropped = cgImage.cropping(to: rect) else { return RecognizedText(lines: []) }
        let read = await recognizeWithPolarityRetry(cropped)
        return mapBand(read, band: band)
    }

    /// The same band, in black-and-white with boosted contrast — the
    /// retry when a choices band comes back with fewer than three
    /// choices (white text on dark pills reads better this way).
    public func recognizeBandBlackAndWhite(_ cgImage: CGImage, band: TextBox) async -> RecognizedText {
        let w = cgImage.width, h = cgImage.height
        let rect = CGRect(x: Int(band.x0 * Double(w)), y: Int(band.y0 * Double(h)),
                          width: max(1, Int(band.width * Double(w))),
                          height: max(1, Int(band.height * Double(h))))
        guard let cropped = cgImage.cropping(to: rect) else { return RecognizedText(lines: []) }
        let ci = CIImage(cgImage: cropped)
        guard let bw = CIFilter(name: "CIColorControls", parameters: [
            kCIInputImageKey: ci,
            kCIInputSaturationKey: 0,
            kCIInputContrastKey: 1.35,
            kCIInputBrightnessKey: 0.05
        ])?.outputImage,
        let bwCG = ciContext.createCGImage(bw, from: bw.extent) else {
            return await recognizeBand(cgImage, band: band)
        }
        let read = await recognize(bwCG)
        return mapBand(read, band: band)
    }

    private func mapBand(_ read: RecognizedText, band: TextBox) -> RecognizedText {
        let mapped = read.lines.map { line in
            let b = line.box
            return RecognizedLine(
                text: line.text,
                box: TextBox(x0: band.x0 + b.x0 * band.width,
                             y0: band.y0 + b.y0 * band.height,
                             x1: band.x0 + b.x1 * band.width,
                             y1: band.y0 + b.y1 * band.height),
                confidence: line.confidence)
        }
        return RecognizedText(lines: mapped)
    }

    // MARK: - Image helpers

    private func meanLuminance(of cgImage: CGImage) -> Double {
        let ci = CIImage(cgImage: cgImage)
        guard let filter = CIFilter(name: "CIAreaAverage", parameters: [
            kCIInputImageKey: ci,
            kCIInputExtentKey: CIVector(cgRect: ci.extent)
        ]), let out = filter.outputImage else { return 0.5 }
        var pixel = [UInt8](repeating: 0, count: 4)
        ciContext.render(out, toBitmap: &pixel, rowBytes: 4,
                         bounds: CGRect(x: 0, y: 0, width: 1, height: 1),
                         format: .RGBA8, colorSpace: CGColorSpaceCreateDeviceRGB())
        return Double(pixel[0]) / 255 * 0.299 + Double(pixel[1]) / 255 * 0.587 + Double(pixel[2]) / 255 * 0.114
    }

    private func invertedImage(_ cgImage: CGImage) -> CGImage? {
        let ci = CIImage(cgImage: cgImage)
        guard let inverted = CIFilter(name: "CIColorInvert", parameters: [kCIInputImageKey: ci])?.outputImage else {
            return nil
        }
        return ciContext.createCGImage(inverted, from: inverted.extent)
    }
}
