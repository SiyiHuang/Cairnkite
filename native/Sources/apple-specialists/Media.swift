import AVFoundation
import CoreImage
import Foundation
import ImageIO
import SoundAnalysis
import UniformTypeIdentifiers
import Vision

func inspectImage(_ source: URL, _ comparison: URL?, _ limit: Int) async throws {
    let image = try singleImage(source)
    var result: [String: Any] = ["backend": "apple_vision_media", "source": source.path]
    if let comparison {
        let request = GenerateImageFeaturePrintRequest()
        let reference = try await request.perform(on: image)
        let other = try await request.perform(on: singleImage(comparison))
        result["comparison"] = comparison.path
        result["distance"] = try reference.distance(to: other)
    } else {
        let classifications = try await ClassifyImageRequest().perform(on: image)
        let aesthetics = try await CalculateImageAestheticsScoresRequest().perform(on: image)
        result["classifications"] = classifications.sorted { $0.confidence > $1.confidence }.prefix(limit).map {
            ["label": $0.identifier, "confidence": $0.confidence]
        }
        result["aesthetics"] = ["overall_score": aesthetics.overallScore, "is_utility": aesthetics.isUtility]
    }
    try emit(result)
}

func extractForeground(_ source: URL, _ output: URL) throws {
    let image = try singleImage(source)
    let request = VNGenerateForegroundInstanceMaskRequest()
    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    try handler.perform([request])
    var result: [String: Any] = ["backend": "apple_vision_foreground", "source": source.path,
                                 "width": image.width, "height": image.height, "instances": 0]
    if let observation = request.results?.first, !observation.allInstances.isEmpty {
        let masked = try observation.generateMaskedImage(
            ofInstances: observation.allInstances, from: handler, croppedToInstancesExtent: false)
        let foreground = CIImage(cvPixelBuffer: masked)
        guard let rendered = CIContext().createCGImage(foreground, from: foreground.extent),
              let writer = CGImageDestinationCreateWithURL(output as CFURL, UTType.png.identifier as CFString, 1, nil) else {
            throw CommandError("Cannot prepare the foreground PNG.")
        }
        CGImageDestinationAddImage(writer, rendered, nil)
        guard CGImageDestinationFinalize(writer) else { throw CommandError("Cannot write the foreground PNG.") }
        result["instances"] = observation.allInstances.count
        result["foreground_png"] = output.path
    }
    try emit(result)
}

private final class SoundObserver: NSObject, SNResultsObserving {
    private let lock = NSLock()
    private var results: [SNClassificationResult] = []
    private var failure: Error?

    func request(_ request: any SNRequest, didProduce result: any SNResult) {
        guard let result = result as? SNClassificationResult else { return }
        lock.withLock { results.append(result) }
    }

    func request(_ request: any SNRequest, didFailWithError error: Error) {
        lock.withLock { failure = error }
    }

    func observations() throws -> [SNClassificationResult] {
        try lock.withLock {
            if let failure { throw failure }
            return results
        }
    }
}

func classifySound(_ source: URL, _ limit: Int, _ threshold: Double) throws {
    let audio = try AVAudioFile(forReading: source)
    let duration = Double(audio.length) / audio.processingFormat.sampleRate
    guard duration.isFinite, duration > 0, duration <= 600 else {
        throw CommandError("Use an audio file up to 10 minutes long.")
    }
    let analyzer = try SNAudioFileAnalyzer(url: source)
    let request = try SNClassifySoundRequest(classifierIdentifier: .version1)
    let observer = SoundObserver()
    try analyzer.add(request, withObserver: observer)
    analyzer.analyze()
    let observations = try observer.observations()
    let windows: [[String: Any]] = observations.compactMap { result in
        let start = max(0, result.timeRange.start.seconds)
        let end = min(duration, result.timeRange.end.seconds)
        let labels = result.classifications.filter { $0.confidence >= threshold }.prefix(limit).map {
            ["label": $0.identifier, "confidence": $0.confidence]
        }
        guard start.isFinite, end.isFinite, start < end, !labels.isEmpty else { return nil }
        return ["start_s": start, "end_s": end, "classifications": labels]
    }
    try emit(["backend": "apple_sound_analysis", "source": source.path, "duration_s": duration,
              "windows": windows, "observation_count": observations.count])
}
