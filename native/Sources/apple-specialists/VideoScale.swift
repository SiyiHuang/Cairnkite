import AVFoundation
import CoreVideo
import Foundation
import VideoToolbox

func videoScaleStatus(_ width: Int?, _ height: Int?) throws {
    let supported = VTLowLatencySuperResolutionScalerConfiguration.isSupported
    var result: [String: Any] = ["supported": supported]
    if let width, let height {
        result["scale_factors"] = supported ? VTLowLatencySuperResolutionScalerConfiguration.supportedScaleFactors(
            frameWidth: width, frameHeight: height
        ) : []
    }
    try emit(result)
}

func upscaleVideo(_ source: URL, _ output: URL, start: Double, limit: Int, scale: Int) async throws {
    let asset = AVURLAsset(url: source)
    guard let track = try await asset.loadTracks(withMediaType: .video).first else {
        throw CommandError("Use a file with a decodable video track.")
    }
    let size = try await track.load(.naturalSize)
    let width = Int(size.width.rounded()), height = Int(size.height.rounded())
    let supported = VTLowLatencySuperResolutionScalerConfiguration.isSupported
    let factors = supported ? VTLowLatencySuperResolutionScalerConfiguration.supportedScaleFactors(
        frameWidth: width, frameHeight: height
    ) : []
    guard factors.contains(Float(scale)) else {
        throw CommandError("VideoToolbox cannot scale \(width) × \(height) by \(scale)x on this Mac. Supported factors: \(factors).")
    }
    let formats = try await track.load(.formatDescriptions)
    let hdr = formats.contains { format in
        let transfer = CMFormatDescriptionGetExtension(format, extensionKey: kCMFormatDescriptionExtension_TransferFunction) as? String
        return transfer == (kCMFormatDescriptionTransferFunction_SMPTE_ST_2084_PQ as String)
            || transfer == (kCMFormatDescriptionTransferFunction_ITU_R_2100_HLG as String)
    }
    guard !hdr else { throw CommandError("Use SDR input for this 8-bit VideoToolbox workflow.") }
    let configuration = VTLowLatencySuperResolutionScalerConfiguration(frameWidth: width, frameHeight: height, scaleFactor: Float(scale))

    let pixelFormat = kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange
    let reader = try AVAssetReader(asset: asset)
    let decoder = AVAssetReaderTrackOutput(track: track, outputSettings: [
        kCVPixelBufferPixelFormatTypeKey as String: pixelFormat,
        kCVPixelBufferIOSurfacePropertiesKey as String: [:],
    ])
    decoder.alwaysCopiesSampleData = false
    guard reader.canAdd(decoder) else { throw CommandError("Cannot configure the video decoder.") }
    reader.add(decoder)
    if start > 0 {
        let time = CMTime(seconds: start, preferredTimescale: 60_000)
        let duration = try await asset.load(.duration)
        guard time.isNumeric, duration.isNumeric, time < duration else {
            throw CommandError("The excerpt start must be within the video.")
        }
        reader.timeRange = CMTimeRange(start: time, duration: CMTimeSubtract(duration, time))
    }
    let sampleRate = try await track.load(.nominalFrameRate)
    let fallbackDuration = CMTime(seconds: sampleRate > 0 ? 1 / Double(sampleRate) : 1 / 30.0, preferredTimescale: 60_000)

    let writer = try AVAssetWriter(url: output, fileType: .mp4)
    let encoder = AVAssetWriterInput(mediaType: .video, outputSettings: [
        AVVideoCodecKey: AVVideoCodecType.h264,
        AVVideoWidthKey: width * scale,
        AVVideoHeightKey: height * scale,
    ])
    var transform = try await track.load(.preferredTransform)
    transform.tx *= CGFloat(scale)
    transform.ty *= CGFloat(scale)
    encoder.transform = transform
    guard writer.canAdd(encoder) else { throw CommandError("Cannot configure the video encoder.") }
    writer.add(encoder)
    let pixelAttributes: [String: Any] = [
        kCVPixelBufferPixelFormatTypeKey as String: pixelFormat,
        kCVPixelBufferWidthKey as String: width * scale,
        kCVPixelBufferHeightKey as String: height * scale,
        kCVPixelBufferIOSurfacePropertiesKey as String: [:],
    ]
    var pixelPool: CVPixelBufferPool?
    guard CVPixelBufferPoolCreate(nil, nil, pixelAttributes as CFDictionary, &pixelPool) == kCVReturnSuccess,
          let pool = pixelPool else { throw CommandError("Cannot allocate scaled video buffers.") }

    let processor = VTFrameProcessor()
    try processor.startSession(configuration: configuration)
    defer { processor.endSession() }
    guard reader.startReading() else { throw reader.error ?? CommandError("Cannot start the video decoder.") }
    defer { if reader.status == .reading { reader.cancelReading() } }
    guard writer.startWriting() else { throw writer.error ?? CommandError("Cannot start the video encoder.") }
    defer { if writer.status == .writing { writer.cancelWriting() } }
    writer.startSession(atSourceTime: .zero)

    var first: CMTime?
    var end = CMTime.zero
    var count = 0
    while count < limit, let sample = decoder.copyNextSampleBuffer() {
        let stamp = sample.presentationTimeStamp
        guard stamp.isNumeric else { throw CommandError("The decoded frame has no valid presentation timestamp.") }
        if first == nil { first = stamp }
        let relative = CMTimeSubtract(stamp, first ?? stamp)
        while !encoder.isReadyForMoreMediaData {
            guard writer.status == .writing else { throw writer.error ?? CommandError("Video encoding stopped.") }
            try await Task.sleep(for: .milliseconds(5))
        }
        var buffer: CVPixelBuffer?
        guard let input = sample.imageBuffer,
              CVPixelBufferPoolCreatePixelBuffer(nil, pool, &buffer) == kCVReturnSuccess,
              let buffer,
              let inputFrame = VTFrameProcessorFrame(buffer: input, presentationTimeStamp: relative),
              let outputFrame = VTFrameProcessorFrame(buffer: buffer, presentationTimeStamp: relative)
        else { throw CommandError("Cannot prepare VideoToolbox input or output buffers.") }
        CVBufferPropagateAttachments(input, buffer)
        _ = try await processor.process(parameters: VTLowLatencySuperResolutionScalerParameters(
            sourceFrame: inputFrame, destinationFrame: outputFrame
        ))
        let duration = sample.duration.isNumeric && sample.duration.seconds > 0 ? sample.duration : fallbackDuration
        var format: CMVideoFormatDescription?
        var presentation = CMSampleTimingInfo(duration: duration, presentationTimeStamp: relative, decodeTimeStamp: .invalid)
        var scaledSample: CMSampleBuffer?
        guard CMVideoFormatDescriptionCreateForImageBuffer(allocator: nil, imageBuffer: buffer, formatDescriptionOut: &format) == noErr,
              let format,
              CMSampleBufferCreateReadyWithImageBuffer(allocator: nil, imageBuffer: buffer, formatDescription: format,
                                                      sampleTiming: &presentation, sampleBufferOut: &scaledSample) == noErr,
              let scaledSample, encoder.append(scaledSample)
        else { throw writer.error ?? CommandError("Cannot encode a scaled frame.") }
        end = CMTimeAdd(relative, duration)
        count += 1
    }
    if reader.status == .failed { throw reader.error ?? CommandError("Video decoding failed.") }
    guard let first, count > 0 else { throw CommandError("The selected excerpt contains no video frames.") }
    writer.endSession(atSourceTime: end)
    encoder.markAsFinished()
    await writer.finishWriting()
    guard writer.status == .completed else { throw writer.error ?? CommandError("Video encoding did not finish.") }
    try emit(["frames": count, "source_start_s": first.seconds, "duration_s": end.seconds])
}
