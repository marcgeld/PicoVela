import XCTest
@testable import PicoVela

final class PicoVelaTests: XCTestCase {
    func testLoadsStationAwareTimeline() throws {
        let directory = try makeTemporaryDirectory()
        let timeline = """
        event,event_type,network,station,station_code,station_name,country,channel,client,event_time
        nk2017,nuclear,IU,ANMO,IU.ANMO,Albuquerque Seismological Laboratory,USA,BHZ,EARTHSCOPE,2017-09-03T03:30:00Z
        """
        try timeline.write(
            to: directory.appending(path: "timeline.csv"),
            atomically: true,
            encoding: .utf8
        )

        let loader = PicoVelaDataLoader(processedDirectory: directory)
        let events = try loader.loadTimeline()

        XCTAssertEqual(events.count, 1)
        XCTAssertEqual(events[0].event, "nk2017")
        XCTAssertEqual(events[0].eventType, .nuclear)
        XCTAssertEqual(events[0].station.code, "IU.ANMO")
        XCTAssertEqual(events[0].station.name, "Albuquerque Seismological Laboratory")
        XCTAssertEqual(events[0].station.country, "USA")
        XCTAssertNotNil(events[0].eventTime)
    }

    func testLoadsWaveformAndAnalyzesAmplitudes() throws {
        let directory = try makeTemporaryDirectory()
        let waveformCSV = """
        event,trace_id,network,station,location,channel,source_file,sample_time_utc,date_utc,time_utc,time_seconds,amplitude
        nk2017,IU.ANMO.00.BHZ,IU,ANMO,00,BHZ,nk2017.mseed,2017-09-03T03:30:00.000000Z,2017-09-03,03:30:00.000000,0.0,-1.0
        nk2017,IU.ANMO.00.BHZ,IU,ANMO,00,BHZ,nk2017.mseed,2017-09-03T03:30:00.050000Z,2017-09-03,03:30:00.050000,0.05,0.0
        nk2017,IU.ANMO.00.BHZ,IU,ANMO,00,BHZ,nk2017.mseed,2017-09-03T03:30:00.100000Z,2017-09-03,03:30:00.100000,0.1,1.0
        """
        let url = directory.appending(path: "nk2017_IU_ANMO_BHZ_preprocessed.csv")
        try waveformCSV.write(to: url, atomically: true, encoding: .utf8)

        let loader = PicoVelaDataLoader(processedDirectory: directory)
        let waveform = try loader.loadWaveform(from: url)
        let analysis = try WaveformAnalyzer().analyze(waveform)

        XCTAssertEqual(waveform.samples.count, 3)
        XCTAssertEqual(analysis.event, "nk2017")
        XCTAssertEqual(analysis.stationCode, "IU.ANMO")
        XCTAssertEqual(analysis.sampleCount, 3)
        XCTAssertEqual(analysis.durationSeconds, 0.1, accuracy: 1e-12)
        XCTAssertEqual(analysis.sampleRateHz ?? 0, 20.0, accuracy: 1e-12)
        XCTAssertEqual(analysis.minimumAmplitude, -1.0, accuracy: 1e-12)
        XCTAssertEqual(analysis.maximumAmplitude, 1.0, accuracy: 1e-12)
        XCTAssertEqual(analysis.meanAmplitude, 0.0, accuracy: 1e-12)
        XCTAssertEqual(analysis.medianAmplitude, 0.0, accuracy: 1e-12)
        XCTAssertEqual(analysis.standardDeviation, 1.0, accuracy: 1e-12)
        XCTAssertEqual(analysis.percentile95Amplitude, 0.9, accuracy: 1e-12)
        XCTAssertEqual(analysis.rootMeanSquare, (2.0 / 3.0).squareRoot(), accuracy: 1e-12)
        XCTAssertEqual(analysis.peakAbsoluteAmplitude, 1.0, accuracy: 1e-12)
        XCTAssertNotNil(analysis.fft())
        XCTAssertNotNil(analysis.periodogram())
    }

    func testBuildsSpectralSummaryWithDominantBin() throws {
        let waveform = SeismicWaveform(
            event: "synthetic",
            traceID: "XX.TEST.00.BHZ",
            network: "XX",
            station: "TEST",
            channel: "BHZ",
            sourceFile: "synthetic.mseed",
            samples: [
                WaveformSample(sampleTimeUTC: "", timeSeconds: 0.0, amplitude: 0.0),
                WaveformSample(sampleTimeUTC: "", timeSeconds: 0.25, amplitude: 1.0),
                WaveformSample(sampleTimeUTC: "", timeSeconds: 0.5, amplitude: 0.0),
                WaveformSample(sampleTimeUTC: "", timeSeconds: 0.75, amplitude: -1.0),
            ]
        )

        let analysis = try WaveformAnalyzer().analyze(waveform)
        let summary = try XCTUnwrap(analysis.spectralSummary())

        XCTAssertEqual(summary.bins.count, 3)
        XCTAssertEqual(summary.dominantBin?.index, 1)
        XCTAssertEqual(summary.dominantBin?.frequencyHz ?? 0, 1.0, accuracy: 1e-12)
        XCTAssertEqual(summary.waveformPeakCount, 1)
    }

    func testBuildsSwiftNumericaSpectrogram() throws {
        let samples = (0..<16).map { index in
            WaveformSample(
                sampleTimeUTC: "",
                timeSeconds: Double(index) / 8.0,
                amplitude: sin(2.0 * .pi * Double(index) / 4.0)
            )
        }
        let waveform = SeismicWaveform(
            event: "synthetic",
            traceID: "XX.TEST.00.BHZ",
            network: "XX",
            station: "TEST",
            channel: "BHZ",
            sourceFile: "synthetic.mseed",
            samples: samples
        )

        let analysis = try WaveformAnalyzer().analyze(waveform)
        let spectrogram = try XCTUnwrap(
            analysis.spectrogram(windowSize: 8, hopSize: 4)
        )

        XCTAssertEqual(spectrogram.windowSize, 8)
        XCTAssertEqual(spectrogram.hopSize, 4)
        XCTAssertEqual(spectrogram.frameCount, 3)
        XCTAssertEqual(spectrogram.frequencyBinCount, 5)
        XCTAssertEqual(spectrogram.cells.count, 15)
        XCTAssertGreaterThan(spectrogram.maximumPower, 0)
    }

    func testDiscoversPreprocessedWaveforms() throws {
        let directory = try makeTemporaryDirectory()
        let waveformCSV = """
        event,trace_id,network,station,location,channel,source_file,sample_time_utc,date_utc,time_utc,time_seconds,amplitude
        nk2017,IU.ANMO.00.BHZ,IU,ANMO,00,BHZ,nk2017.mseed,2017-09-03T03:30:00.000000Z,2017-09-03,03:30:00.000000,0.0,1.0
        """
        try waveformCSV.write(
            to: directory.appending(path: "nk2017_preprocessed.csv"),
            atomically: true,
            encoding: .utf8
        )
        try waveformCSV.write(
            to: directory.appending(path: "nk2017_raw.csv"),
            atomically: true,
            encoding: .utf8
        )

        let loader = PicoVelaDataLoader(processedDirectory: directory)
        let waveforms = try loader.loadPreprocessedWaveforms()

        XCTAssertEqual(waveforms.map(\.event), ["nk2017"])
    }

    private func makeTemporaryDirectory() throws -> URL {
        let url = FileManager.default.temporaryDirectory
            .appending(path: "PicoVelaTests-\(UUID().uuidString)")
        try FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }
}
