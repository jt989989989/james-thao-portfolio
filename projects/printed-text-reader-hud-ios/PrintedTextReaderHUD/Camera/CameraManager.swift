// CameraManager.swift
// My camera: AVFoundation. The back camera feeds a preview and, on a
// scan, a burst of frames — up to 3 grabs, 240 ms apart — so I can
// pick the sharpest read instead of trusting a single shaky frame.

import Foundation
import AVFoundation
import CoreImage

/// Not @MainActor: the capture delegate runs on its own queue, and the
/// frame buffer is guarded by a lock, so this class stays plain.
public final class CameraManager: NSObject, ObservableObject {
    public let session = AVCaptureSession()
    @Published public private(set) var isRunning = false
    @Published public private(set) var accessDenied = false

    private let output = AVCaptureVideoDataOutput()
    private let sessionQueue = DispatchQueue(label: "hud.camera.session")
    private let bufferLock = NSLock()
    private var latestBuffer: CVPixelBuffer?
    private var latestSequence = 0
    private let ciContext = CIContext()

    override public init() {
        super.init()
        output.setSampleBufferDelegate(self, queue: DispatchQueue(label: "hud.camera.frames"))
    }

    /// Ask for the camera and start it. Returns false when access is
    /// denied — the UI then explains how to turn it on in Settings.
    public func requestAccessAndStart() async -> Bool {
        let granted = await withCheckedContinuation { cont in
            AVCaptureDevice.requestAccess(for: .video) { cont.resume(returning: $0) }
        }
        guard granted else {
            accessDenied = true
            return false
        }
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            self.session.beginConfiguration()
            self.session.sessionPreset = .hd1920x1080
            if let device = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back),
               let input = try? AVCaptureDeviceInput(device: device),
               self.session.canAddInput(input) {
                self.session.addInput(input)
            }
            self.output.videoSettings = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA]
            self.output.alwaysDiscardsLateVideoFrames = true
            if self.session.canAddOutput(self.output) {
                self.session.addOutput(self.output)
            }
            self.session.commitConfiguration()
            self.session.startRunning()
            DispatchQueue.main.async { self.isRunning = true }
        }
        return true
    }

    public func stop() {
        sessionQueue.async { [weak self] in
            self?.session.stopRunning()
            DispatchQueue.main.async { self?.isRunning = false }
        }
    }

    /// The most recent frame as a CGImage, or nil when the camera has
    /// not delivered one yet.
    public func latestFrameImage() -> CGImage? {
        bufferLock.lock()
        defer { bufferLock.unlock() }
        guard let pb = latestBuffer else { return nil }
        return makeCGImage(from: pb)
    }

    /// A burst of frames: up to `count` grabs, `interval` apart, each
    /// a fresh frame from the camera. The solver reads each and keeps
    /// the best.
    public func captureBurst(count: Int = 3, interval: TimeInterval = 0.24) async -> [CGImage] {
        var images: [CGImage] = []
        var lastSeq = -1
        for _ in 0..<count {
            let deadline = Date().addingTimeInterval(1.0)
            while Date() < deadline {
                bufferLock.lock()
                let seq = latestSequence
                let pb = latestBuffer
                bufferLock.unlock()
                if seq != lastSeq, let pb = pb, let img = makeCGImage(from: pb) {
                    lastSeq = seq
                    images.append(img)
                    break
                }
                try? await Task.sleep(nanoseconds: 20_000_000)
            }
            try? await Task.sleep(nanoseconds: UInt64(interval * 1_000_000_000))
        }
        return images
    }

    private func makeCGImage(from pixelBuffer: CVPixelBuffer) -> CGImage? {
        let ci = CIImage(cvPixelBuffer: pixelBuffer)
        return ciContext.createCGImage(ci, from: ci.extent)
    }
}

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    public func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        guard let pb = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
        bufferLock.lock()
        latestBuffer = pb
        latestSequence += 1
        bufferLock.unlock()
    }
}
