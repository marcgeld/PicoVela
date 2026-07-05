#if os(macOS)
import Foundation

struct PlotCommand {
    let processedDirectory: URL
    let event: String?
    let maximumSamples: Int
    let spectrogramWindowSize: Int
    let spectrogramHopSize: Int?

    static func parse(arguments: [String] = Array(CommandLine.arguments.dropFirst())) throws -> PlotCommand {
        var processedDirectory = URL(filePath: "pico-vela-data/data/processed")
        var event: String?
        var maximumSamples = 5_000
        var spectrogramWindowSize = 256
        var spectrogramHopSize: Int?
        var iterator = arguments.makeIterator()

        while let argument = iterator.next() {
            switch argument {
            case "--processed-dir":
                guard let value = iterator.next() else {
                    throw PlotCommandError.missingValue(argument)
                }
                processedDirectory = URL(filePath: value)
            case "--event":
                guard let value = iterator.next() else {
                    throw PlotCommandError.missingValue(argument)
                }
                event = value
            case "--max-samples":
                guard let value = iterator.next() else {
                    throw PlotCommandError.missingValue(argument)
                }
                guard let parsed = Int(value), parsed > 0 else {
                    throw PlotCommandError.invalidValue(argument: argument, value: value)
                }
                maximumSamples = parsed
            case "--spectrogram-window":
                guard let value = iterator.next() else {
                    throw PlotCommandError.missingValue(argument)
                }
                guard let parsed = Int(value), parsed > 1 else {
                    throw PlotCommandError.invalidValue(argument: argument, value: value)
                }
                spectrogramWindowSize = parsed
            case "--spectrogram-hop":
                guard let value = iterator.next() else {
                    throw PlotCommandError.missingValue(argument)
                }
                guard let parsed = Int(value), parsed > 0 else {
                    throw PlotCommandError.invalidValue(argument: argument, value: value)
                }
                spectrogramHopSize = parsed
            case "--help", "-h":
                throw PlotCommandError.helpRequested
            default:
                throw PlotCommandError.unknownArgument(argument)
            }
        }

        return PlotCommand(
            processedDirectory: processedDirectory,
            event: event,
            maximumSamples: maximumSamples,
            spectrogramWindowSize: spectrogramWindowSize,
            spectrogramHopSize: spectrogramHopSize
        )
    }

    static let help = """
    Usage:
      swift run picovela-plot [--processed-dir PATH] [--event LABEL] [--max-samples COUNT]
                            [--spectrogram-window COUNT] [--spectrogram-hop COUNT]

    Opens a small macOS plotting window for Python-prepared PicoVela waveform data.
    """
}

enum PlotCommandError: Error, CustomStringConvertible {
    case helpRequested
    case missingValue(String)
    case invalidValue(argument: String, value: String)
    case unknownArgument(String)

    var description: String {
        switch self {
        case .helpRequested:
            PlotCommand.help
        case .missingValue(let argument):
            "Missing value for \(argument)\n\n\(PlotCommand.help)"
        case .invalidValue(let argument, let value):
            "Invalid value for \(argument): \(value)\n\n\(PlotCommand.help)"
        case .unknownArgument(let argument):
            "Unknown argument: \(argument)\n\n\(PlotCommand.help)"
        }
    }
}
#endif
