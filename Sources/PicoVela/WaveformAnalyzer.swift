import Foundation
import SwiftNumerica

/// First-pass seismic waveform analysis powered by SwiftNumerica tensors.
public struct WaveformAnalyzer {
    public init() {}

    public func analyze(_ waveform: SeismicWaveform) throws -> WaveformAnalysis {
        guard !waveform.samples.isEmpty else {
            throw PicoVelaError.emptyWaveform(waveform.event)
        }

        let amplitudes = waveform.samples.map(\.amplitude)
        let tensor = Tensor.vector(amplitudes)
        let sampleCount = amplitudes.count
        let minimum = tensor.min() ?? 0
        let maximum = tensor.max() ?? 0
        let mean = tensor.mean() ?? 0
        let median = tensor.median() ?? 0
        let standardDeviation = tensor.standardDeviation() ?? 0
        let percentile95 = tensor.percentile(95) ?? 0
        let squareMean = amplitudes.reduce(0) { $0 + ($1 * $1) } / Double(sampleCount)
        let duration = waveform.samples.last?.timeSeconds ?? 0
        let sampleRate = duration > 0 && sampleCount > 1
            ? Double(sampleCount - 1) / duration
            : nil
        guard let signal = Signal(samples: tensor, sampleRate: sampleRate) else {
            throw PicoVelaError.invalidSignal(waveform.event)
        }

        return WaveformAnalysis(
            event: waveform.event,
            stationCode: "\(waveform.network).\(waveform.station)",
            sampleCount: sampleCount,
            durationSeconds: duration,
            sampleRateHz: sampleRate,
            minimumAmplitude: minimum,
            maximumAmplitude: maximum,
            meanAmplitude: mean,
            medianAmplitude: median,
            standardDeviation: standardDeviation,
            percentile95Amplitude: percentile95,
            rootMeanSquare: squareMean.squareRoot(),
            peakAbsoluteAmplitude: max(abs(minimum), abs(maximum)),
            amplitudes: tensor,
            signal: signal
        )
    }
}
