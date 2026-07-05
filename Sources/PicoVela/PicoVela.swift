import Foundation
import SwiftNumerica

/// A historical event category used by PicoVela reports.
public enum EventType: String, Codable, Equatable {
    case nuclear
    case earthquake
    case volcanic
    case launch
    case event
}

/// One observing station entry from `timeline.csv`.
public struct ObservingStation: Codable, Equatable {
    public let network: String
    public let station: String
    public let code: String
    public let name: String
    public let country: String
    public let channel: String
    public let client: String

    public init(
        network: String,
        station: String,
        code: String,
        name: String,
        country: String,
        channel: String,
        client: String
    ) {
        self.network = network
        self.station = station
        self.code = code
        self.name = name
        self.country = country
        self.channel = channel
        self.client = client
    }
}

/// One row from the station-aware `timeline.csv` produced by `pico-vela-data`.
public struct ObservedEvent: Codable, Equatable {
    public let event: String
    public let eventType: EventType
    public let station: ObservingStation
    public let eventTime: Date?

    public init(
        event: String,
        eventType: EventType,
        station: ObservingStation,
        eventTime: Date?
    ) {
        self.event = event
        self.eventType = eventType
        self.station = station
        self.eventTime = eventTime
    }
}

/// One sampled amplitude row from a processed waveform CSV.
public struct WaveformSample: Codable, Equatable {
    public let sampleTimeUTC: String
    public let timeSeconds: Double
    public let amplitude: Double

    public init(sampleTimeUTC: String, timeSeconds: Double, amplitude: Double) {
        self.sampleTimeUTC = sampleTimeUTC
        self.timeSeconds = timeSeconds
        self.amplitude = amplitude
    }
}

/// A processed event waveform ready for numerical analysis.
public struct SeismicWaveform {
    public let event: String
    public let traceID: String
    public let network: String
    public let station: String
    public let channel: String
    public let sourceFile: String
    public let samples: [WaveformSample]

    public init(
        event: String,
        traceID: String,
        network: String,
        station: String,
        channel: String,
        sourceFile: String,
        samples: [WaveformSample]
    ) {
        self.event = event
        self.traceID = traceID
        self.network = network
        self.station = station
        self.channel = channel
        self.sourceFile = sourceFile
        self.samples = samples
    }

    /// Return amplitudes as SwiftNumerica's tensor-first representation.
    public func amplitudeTensor() -> Tensor<Double> {
        Tensor.vector(samples.map(\.amplitude))
    }
}

/// Summary measurements for one waveform.
public struct WaveformAnalysis {
    public let event: String
    public let stationCode: String
    public let sampleCount: Int
    public let durationSeconds: Double
    public let sampleRateHz: Double?
    public let minimumAmplitude: Double
    public let maximumAmplitude: Double
    public let meanAmplitude: Double
    public let medianAmplitude: Double
    public let standardDeviation: Double
    public let percentile95Amplitude: Double
    public let rootMeanSquare: Double
    public let peakAbsoluteAmplitude: Double
    public let amplitudes: Tensor<Double>
    public let signal: Signal

    public init(
        event: String,
        stationCode: String,
        sampleCount: Int,
        durationSeconds: Double,
        sampleRateHz: Double?,
        minimumAmplitude: Double,
        maximumAmplitude: Double,
        meanAmplitude: Double,
        medianAmplitude: Double,
        standardDeviation: Double,
        percentile95Amplitude: Double,
        rootMeanSquare: Double,
        peakAbsoluteAmplitude: Double,
        amplitudes: Tensor<Double>,
        signal: Signal
    ) {
        self.event = event
        self.stationCode = stationCode
        self.sampleCount = sampleCount
        self.durationSeconds = durationSeconds
        self.sampleRateHz = sampleRateHz
        self.minimumAmplitude = minimumAmplitude
        self.maximumAmplitude = maximumAmplitude
        self.meanAmplitude = meanAmplitude
        self.medianAmplitude = medianAmplitude
        self.standardDeviation = standardDeviation
        self.percentile95Amplitude = percentile95Amplitude
        self.rootMeanSquare = rootMeanSquare
        self.peakAbsoluteAmplitude = peakAbsoluteAmplitude
        self.amplitudes = amplitudes
        self.signal = signal
    }

    /// Compute a SwiftNumerica periodogram for this waveform, when possible.
    public func periodogram() -> Tensor<Double>? {
        signal.periodogram()
    }

    /// Compute a SwiftNumerica FFT for this waveform, when possible.
    public func fft() -> Tensor<ComplexNumber>? {
        signal.fft()
    }

    /// Return local waveform peaks detected by SwiftNumerica.
    public func peaks(minimumProminence: Double = 0) -> [Peak] {
        signal.peaks(minimumProminence: minimumProminence)
    }
}

/// One frequency bin from a SwiftNumerica spectral transform.
public struct SpectrumBin: Equatable {
    public let index: Int
    public let frequencyHz: Double?
    public let magnitude: Double
    public let power: Double

    public init(index: Int, frequencyHz: Double?, magnitude: Double, power: Double) {
        self.index = index
        self.frequencyHz = frequencyHz
        self.magnitude = magnitude
        self.power = power
    }
}

/// A compact spectral report derived from SwiftNumerica FFT and periodogram.
public struct SpectralSummary {
    public let spectrum: Tensor<ComplexNumber>
    public let periodogram: Tensor<Double>
    public let bins: [SpectrumBin]
    public let dominantBin: SpectrumBin?
    public let waveformPeakCount: Int

    public init(
        spectrum: Tensor<ComplexNumber>,
        periodogram: Tensor<Double>,
        bins: [SpectrumBin],
        dominantBin: SpectrumBin?,
        waveformPeakCount: Int
    ) {
        self.spectrum = spectrum
        self.periodogram = periodogram
        self.bins = bins
        self.dominantBin = dominantBin
        self.waveformPeakCount = waveformPeakCount
    }
}

/// One time/frequency power cell from a short-time Fourier transform.
public struct SpectrogramCell: Equatable {
    public let frameIndex: Int
    public let frequencyBin: Int
    public let timeSeconds: Double
    public let frequencyHz: Double?
    public let power: Double

    public init(
        frameIndex: Int,
        frequencyBin: Int,
        timeSeconds: Double,
        frequencyHz: Double?,
        power: Double
    ) {
        self.frameIndex = frameIndex
        self.frequencyBin = frequencyBin
        self.timeSeconds = timeSeconds
        self.frequencyHz = frequencyHz
        self.power = power
    }
}

/// A compact waterfall/spectrogram representation for plotting.
public struct Spectrogram: Equatable {
    public let windowSize: Int
    public let hopSize: Int
    public let frameCount: Int
    public let frequencyBinCount: Int
    public let maximumPower: Double
    public let cells: [SpectrogramCell]

    public init(
        windowSize: Int,
        hopSize: Int,
        frameCount: Int,
        frequencyBinCount: Int,
        maximumPower: Double,
        cells: [SpectrogramCell]
    ) {
        self.windowSize = windowSize
        self.hopSize = hopSize
        self.frameCount = frameCount
        self.frequencyBinCount = frequencyBinCount
        self.maximumPower = maximumPower
        self.cells = cells
    }
}

/// Errors thrown while reading or analysing PicoVela prepared data.
public enum PicoVelaError: Error, Equatable {
    case emptyCSV
    case missingColumn(String)
    case invalidNumber(column: String, value: String)
    case emptyWaveform(String)
    case invalidSignal(String)
}
