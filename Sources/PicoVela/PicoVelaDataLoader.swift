import Foundation

/// Loads Python-prepared PicoVela CSV files into Swift domain models.
public struct PicoVelaDataLoader {
    public let processedDirectory: URL

    public init(processedDirectory: URL) {
        self.processedDirectory = processedDirectory
    }

    public func loadTimeline(filename: String = "timeline.csv") throws -> [ObservedEvent] {
        let url = processedDirectory.appending(path: filename)
        let table = try CSVTable(contentsOf: url)

        return try table.rows.map { row in
            let station = ObservingStation(
                network: try table.require("network", in: row),
                station: try table.require("station", in: row),
                code: try table.require("station_code", in: row),
                name: try table.require("station_name", in: row),
                country: try table.require("country", in: row),
                channel: try table.require("channel", in: row),
                client: try table.require("client", in: row)
            )

            return ObservedEvent(
                event: try table.require("event", in: row),
                eventType: EventType(rawValue: try table.require("event_type", in: row)) ?? .event,
                station: station,
                eventTime: Self.parseUTC(row["event_time"] ?? "")
            )
        }
    }

    public func loadWaveform(from url: URL) throws -> SeismicWaveform {
        let table = try CSVTable(contentsOf: url)
        guard let first = table.rows.first else {
            throw PicoVelaError.emptyWaveform(url.lastPathComponent)
        }

        let samples = try table.rows.map { row in
            WaveformSample(
                sampleTimeUTC: try table.require("sample_time_utc", in: row),
                timeSeconds: try parseDouble(column: "time_seconds", row: row, table: table),
                amplitude: try parseDouble(column: "amplitude", row: row, table: table)
            )
        }

        return SeismicWaveform(
            event: try table.require("event", in: first),
            traceID: try table.require("trace_id", in: first),
            network: try table.require("network", in: first),
            station: try table.require("station", in: first),
            channel: try table.require("channel", in: first),
            sourceFile: try table.require("source_file", in: first),
            samples: samples
        )
    }

    public func loadPreprocessedWaveforms() throws -> [SeismicWaveform] {
        let files = try FileManager.default.contentsOfDirectory(
            at: processedDirectory,
            includingPropertiesForKeys: nil
        )

        return try files
            .filter { $0.lastPathComponent.hasSuffix("_preprocessed.csv") }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
            .map(loadWaveform)
    }

    private func parseDouble(
        column: String,
        row: [String: String],
        table: CSVTable
    ) throws -> Double {
        let value = try table.require(column, in: row)
        guard let number = Double(value) else {
            throw PicoVelaError.invalidNumber(column: column, value: value)
        }
        return number
    }

    private static func parseUTC(_ value: String) -> Date? {
        guard !value.isEmpty else {
            return nil
        }

        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: value) {
            return date
        }

        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: value)
    }
}
