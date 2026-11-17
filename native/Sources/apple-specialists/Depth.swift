import CoreImage
import CoreML
import Foundation
import ImageIO
import UniformTypeIdentifiers

func compileCoreML(_ package: URL, _ destination: URL) async throws {
    let compiled = try await MLModel.compileModel(at: package)
    defer { try? FileManager.default.removeItem(at: compiled) }
    try FileManager.default.moveItem(at: compiled, to: destination)
    try emit(["compiled_model": destination.path])
}

func coreMLConfiguration(_ compute: String) throws -> MLModelConfiguration {
    let configuration = MLModelConfiguration()
    switch compute {
    case "cpu": configuration.computeUnits = .cpuOnly
    case "cpu-gpu": configuration.computeUnits = .cpuAndGPU
    case "all": configuration.computeUnits = .all
    default: throw CommandError("Invalid Core ML compute preference.")
    }
    return configuration
}

func estimateDepth(_ source: URL, _ checkpoint: URL, _ output: URL, _ compute: String) async throws {
    let model = try MLModel(contentsOf: checkpoint, configuration: coreMLConfiguration(compute))
    guard let inputShape = model.modelDescription.inputDescriptionsByName["image"]?.imageConstraint else {
        throw CommandError("Depth Anything has no image input constraint.")
    }
    let original = CIImage(cgImage: try singleImage(source))
    let input = original.transformed(by: CGAffineTransform(scaleX: CGFloat(inputShape.pixelsWide) / original.extent.width,
                                                           y: CGFloat(inputShape.pixelsHigh) / original.extent.height))
    let context = CIContext()
    var buffer: CVPixelBuffer?
    guard CVPixelBufferCreate(nil, inputShape.pixelsWide, inputShape.pixelsHigh, kCVPixelFormatType_32ARGB, nil, &buffer)
            == kCVReturnSuccess, let buffer else {
        throw CommandError("Cannot allocate the Core ML input image.")
    }
    context.render(input, to: buffer)
    let features = try MLDictionaryFeatureProvider(dictionary: ["image": MLFeatureValue(pixelBuffer: buffer)])
    let prediction = try await model.prediction(from: features)
    guard let depth = prediction.featureValue(for: "depth")?.imageBufferValue else {
        throw CommandError("Depth Anything did not return a depth image.")
    }
    let modelDepth = CIImage(cvPixelBuffer: depth)
    let scaled = modelDepth.transformed(by: CGAffineTransform(scaleX: original.extent.width / modelDepth.extent.width,
                                                              y: original.extent.height / modelDepth.extent.height))
    guard let image = context.createCGImage(scaled, from: original.extent),
          let writer = CGImageDestinationCreateWithURL(output as CFURL, UTType.png.identifier as CFString, 1, nil) else {
        throw CommandError("Cannot prepare the relative-depth PNG.")
    }
    CGImageDestinationAddImage(writer, image, nil)
    guard CGImageDestinationFinalize(writer) else { throw CommandError("Cannot write the relative-depth PNG.") }
    try emit(["backend": "depth_anything_v2_small_coreml", "source": source.path, "relative_depth_png": output.path,
              "width": image.width, "height": image.height, "compute_preference": compute])
}
