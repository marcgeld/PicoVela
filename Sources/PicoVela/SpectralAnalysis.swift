import Foundation
import SwiftNumerica

public extension WaveformAnalysis {
    /// Build a compact frequency-domain summary using SwiftNumerica transforms.
    func spectralSummary(
        oneSided: Bool = true,
        minimumPeakProminence: Double = 0
    ) -> SpectralSummary? {
        guard let spectrum = fft(),
              let periodogram = periodogram()
        else {
            return nil
        }

        let binCount = oneSided
            ? max(1, (periodogram.count / 2) + 1)
            : periodogram.count

        let bins = (0..<binCount).map { index in
            SpectrumBin(
                index: index,
                frequencyHz: frequency(forBin: index, totalBins: periodogram.count),
                magnitude: spectrum.values[index].magnitude,
                power: periodogram.values[index]
            )
        }

        return SpectralSummary(
            spectrum: spectrum,
            periodogram: periodogram,
            bins: bins,
            dominantBin: bins.max { $0.power < $1.power },
            waveformPeakCount: peaks(minimumProminence: minimumPeakProminence).count
        )
    }

    private func frequency(forBin index: Int, totalBins: Int) -> Double? {
        guard let sampleRateHz, totalBins > 0 else {
            return nil
        }
        return Double(index) * sampleRateHz / Double(totalBins)
    }

    /// Compute a waterfall/spectrogram using Hann-windowed SwiftNumerica FFT frames.
    func spectrogram(
        windowSize requestedWindowSize: Int = 256,
        hopSize requestedHopSize: Int? = nil,
        oneSided: Bool = true
    ) -> Spectrogram? {
        guard sampleCount > 1 else {
            return nil
        }

        let windowSize = min(max(2, requestedWindowSize), sampleCount)
        let hopSize = max(1, requestedHopSize ?? max(1, windowSize / 2))
        guard let window = Numerica.SignalProcessing.hannWindow(size: windowSize) else {
            return nil
        }

        let values = amplitudes.values
        let starts = Array(stride(from: 0, through: values.count - windowSize, by: hopSize))
        guard !starts.isEmpty else {
            return nil
        }

        let binCount = oneSided ? (windowSize / 2) + 1 : windowSize
        var cells: [SpectrogramCell] = []
        cells.reserveCapacity(starts.count * binCount)
        var maximumPower = 0.0

        for (frameIndex, start) in starts.enumerated() {
            let frameValues = (0..<windowSize).map { offset in
                values[start + offset] * window.values[offset]
            }
            let frameTensor = Tensor.vector(frameValues)
            guard let spectrum = Numerica.SignalProcessing.fft(frameTensor) else {
                return nil
            }

            for frequencyBin in 0..<binCount {
                let magnitude = spectrum.values[frequencyBin].magnitude
                let power = magnitude * magnitude / Double(windowSize)
                maximumPower = max(maximumPower, power)
                cells.append(
                    SpectrogramCell(
                        frameIndex: frameIndex,
                        frequencyBin: frequencyBin,
                        timeSeconds: Double(start) / (sampleRateHz ?? 1),
                        frequencyHz: frequency(forBin: frequencyBin, totalBins: windowSize),
                        power: power
                    )
                )
            }
        }

        return Spectrogram(
            windowSize: windowSize,
            hopSize: hopSize,
            frameCount: starts.count,
            frequencyBinCount: binCount,
            maximumPower: maximumPower,
            cells: cells
        )
    }
}
