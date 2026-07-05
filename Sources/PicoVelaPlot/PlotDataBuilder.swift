#if os(macOS)
import Foundation
import PicoVela

struct PlotDataBuilder {
    let command: PlotCommand

    func build() throws -> PlotDocument {
        let loader = PicoVelaDataLoader(processedDirectory: command.processedDirectory)
        let observedEvents = (try? loader.loadTimeline()) ?? []
        let waveforms = try loader.loadPreprocessedWaveforms()
        let waveform = try selectWaveform(from: waveforms)
        let observedEvent = observedEvents.first { $0.event == waveform.event }
        let analysis = try WaveformAnalyzer().analyze(waveform)

        guard let spectralSummary = analysis.spectralSummary() else {
            throw PlotDataError.spectralAnalysisUnavailable(waveform.event)
        }
        guard let spectrogram = analysis.spectrogram(
            windowSize: command.spectrogramWindowSize,
            hopSize: command.spectrogramHopSize
        ) else {
            throw PlotDataError.spectrogramUnavailable(waveform.event)
        }

        return PlotDocument(
            waveform: waveform,
            observedEvent: observedEvent,
            analysis: analysis,
            spectralSummary: spectralSummary,
            spectrogram: spectrogram,
            waveformPoints: downsample(waveform.samples, maximumCount: command.maximumSamples),
            spectrumPoints: spectralSummary.bins.map { bin in
                SpectrumPoint(
                    id: bin.index,
                    frequencyHz: bin.frequencyHz ?? Double(bin.index),
                    magnitude: bin.magnitude,
                    power: bin.power
                )
            },
            spectrogramPoints: spectrogram.cells.map { cell in
                SpectrogramPoint(
                    id: (cell.frameIndex * spectrogram.frequencyBinCount) + cell.frequencyBin,
                    timeSeconds: cell.timeSeconds,
                    frequencyHz: cell.frequencyHz ?? Double(cell.frequencyBin),
                    normalizedPower: spectrogram.maximumPower > 0
                        ? cell.power / spectrogram.maximumPower
                        : 0
                )
            }
        )
    }

    private func selectWaveform(from waveforms: [SeismicWaveform]) throws -> SeismicWaveform {
        guard !waveforms.isEmpty else {
            throw PlotDataError.noWaveforms(command.processedDirectory.path())
        }

        guard let event = command.event else {
            return waveforms[0]
        }

        guard let waveform = waveforms.first(where: { $0.event == event }) else {
            throw PlotDataError.eventNotFound(event)
        }

        return waveform
    }

    private func downsample(
        _ samples: [WaveformSample],
        maximumCount: Int
    ) -> [WaveformPoint] {
        guard samples.count > maximumCount else {
            return samples.enumerated().map { index, sample in
                WaveformPoint(
                    id: index,
                    timeSeconds: sample.timeSeconds,
                    amplitude: sample.amplitude
                )
            }
        }

        let stride = max(1, samples.count / maximumCount)
        return samples.enumerated().compactMap { index, sample in
            guard index.isMultiple(of: stride) else {
                return nil
            }
            return WaveformPoint(
                id: index,
                timeSeconds: sample.timeSeconds,
                amplitude: sample.amplitude
            )
        }
    }
}

enum PlotDataError: Error, CustomStringConvertible {
    case noWaveforms(String)
    case eventNotFound(String)
    case spectralAnalysisUnavailable(String)
    case spectrogramUnavailable(String)

    var description: String {
        switch self {
        case .noWaveforms(let directory):
            "No *_preprocessed.csv files found in \(directory)."
        case .eventNotFound(let event):
            "No preprocessed waveform found for event \(event)."
        case .spectralAnalysisUnavailable(let event):
            "Could not compute spectral analysis for event \(event)."
        case .spectrogramUnavailable(let event):
            "Could not compute spectrogram for event \(event)."
        }
    }
}
#endif
