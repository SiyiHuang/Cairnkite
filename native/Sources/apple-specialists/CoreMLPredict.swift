import CoreImage
import CoreML
import Foundation
import ImageIO
import UniformTypeIdentifiers

struct CoreMLInput: Decodable {
    let image: String?
    let integer: Int64?
    let number: Double?
    let text: String?
    let values: [Double]?
    let shape: [Int]?
}

private func coreMLFeature(_ input: CoreMLInput, _ description: MLFeatureDescription) throws -> MLFeatureValue {
    switch description.type {
    case .image:
        if let path = input.image, let constraint = description.imageConstraint {
            return try MLFeatureValue(imageAt: URL(fileURLWithPath: path), constraint: constraint)
        }
    case .int64:
        if let value = input.integer { return MLFeatureValue(int64: value) }
    case .double:
        if let value = input.number { return MLFeatureValue(double: value) }
    case .string:
        if let value = input.text { return MLFeatureValue(string: value) }
    case .multiArray:
        if let values = input.values, let constraint = description.multiArrayConstraint {
            let shape = input.shape ?? constraint.shape.map(\.intValue)
            var count = 1
            for dimension in shape {
                guard dimension > 0, dimension <= values.count / count else {
                    throw CommandError("Core ML tensor shape exceeds the supplied values.")
                }
                count *= dimension
            }
            guard count == values.count else { throw CommandError("Core ML tensor shape must match its value count.") }
            if constraint.dataType == .int32 && !values.allSatisfy({
                $0 >= Double(Int32.min) && $0 <= Double(Int32.max) && $0.rounded() == $0
            }) {
                throw CommandError("Core ML int32 tensors require 32-bit integer values.")
            }
            let array = try MLMultiArray(shape: shape.map(NSNumber.init(value:)), dataType: constraint.dataType)
            for (index, value) in values.enumerated() { array[index] = NSNumber(value: value) }
            return MLFeatureValue(multiArray: array)
        }
    default: break
    }
    throw CommandError("Unsupported or missing input for Core ML feature \(description.name).")
}

private func coreMLTypeName(_ type: MLFeatureType) -> String {
    switch type {
    case .image: return "image"
    case .int64: return "int64"
    case .double: return "double"
    case .string: return "string"
    case .multiArray: return "multiarray"
    case .dictionary: return "dictionary"
    case .sequence: return "sequence"
    default: return String(describing: type)
    }
}

private func coreMLDescription(_ feature: MLFeatureDescription) -> [String: Any] {
    var description: [String: Any] = ["type": coreMLTypeName(feature.type), "optional": feature.isOptional]
    if let image = feature.imageConstraint {
        description["size"] = [image.pixelsWide, image.pixelsHigh]
    }
    if let array = feature.multiArrayConstraint {
        description["shape"] = array.shape.map(\.intValue)
        switch array.dataType {
        case .int32: description["data_type"] = "int32"
        case .float16: description["data_type"] = "float16"
        case .float32: description["data_type"] = "float32"
        case .double: description["data_type"] = "float64"
        default: description["data_type"] = String(describing: array.dataType)
        }
    }
    return description
}

private func finiteNumber(_ value: Double) -> Any { value.isFinite ? value as Any : NSNull() }

private func coreMLOutput(_ value: MLFeatureValue, _ directory: URL, _ index: Int) throws -> Any {
    switch value.type {
    case .int64: return value.int64Value
    case .double: return finiteNumber(value.doubleValue)
    case .string: return value.stringValue
    case .dictionary:
        let entries = value.dictionaryValue.sorted { $0.value.doubleValue > $1.value.doubleValue }
        return [
            "scores": entries.prefix(128).map { ["key": String(describing: $0.key), "score": finiteNumber($0.value.doubleValue)] },
            "count": entries.count
        ] as [String: Any]
    case .multiArray:
        if let array = value.multiArrayValue {
            return ["shape": array.shape.map(\.intValue), "values": (0..<min(array.count, 1024)).map {
                finiteNumber(array[$0].doubleValue)
            }, "count": array.count] as [String: Any]
        }
    case .image:
        if let buffer = value.imageBufferValue {
            let image = CIImage(cvPixelBuffer: buffer)
            let output = directory.appendingPathComponent("output-\(index).png")
            guard let rendered = CIContext().createCGImage(image, from: image.extent),
                  let writer = CGImageDestinationCreateWithURL(output as CFURL, UTType.png.identifier as CFString, 1, nil)
            else { throw CommandError("Cannot render Core ML output image.") }
            CGImageDestinationAddImage(writer, rendered, nil)
            guard CGImageDestinationFinalize(writer) else { throw CommandError("Cannot write Core ML output image.") }
            return ["png": output.path, "width": rendered.width, "height": rendered.height] as [String: Any]
        }
    default: break
    }
    return ["type": coreMLTypeName(value.type), "preview_available": false]
}

func predictCoreML(_ package: URL, _ directory: URL, _ compute: String) async throws {
    let compiled = package.pathExtension.lowercased() == "mlmodelc" ? package : try await MLModel.compileModel(at: package)
    defer {
        if compiled != package { try? FileManager.default.removeItem(at: compiled) }
    }
    let model = try MLModel(contentsOf: compiled, configuration: coreMLConfiguration(compute))
    let inputs = model.modelDescription.inputDescriptionsByName
    var result: [String: Any] = [
        "backend": "core_ml", "compute_preference": compute,
        "input_features": inputs.mapValues(coreMLDescription),
        "output_features": model.modelDescription.outputDescriptionsByName.mapValues(coreMLDescription)
    ]
    let supplied = try JSONDecoder().decode([String: CoreMLInput]?.self, from: FileHandle.standardInput.readDataToEndOfFile())
    if let supplied {
        var values: [String: MLFeatureValue] = [:]
        for (name, input) in supplied {
            guard let description = inputs[name] else { throw CommandError("Unknown Core ML feature \(name).") }
            values[name] = try coreMLFeature(input, description)
        }
        let prediction = try await model.prediction(from: MLDictionaryFeatureProvider(dictionary: values))
        var outputs: [String: Any] = [:]
        for (index, name) in prediction.featureNames.sorted().enumerated() {
            if let feature = prediction.featureValue(for: name) {
                outputs[name] = try coreMLOutput(feature, directory, index)
            }
        }
        result["prediction"] = outputs
    }
    try emit(result)
}
