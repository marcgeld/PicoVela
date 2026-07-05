#if os(macOS)
import Foundation
import PicoVela

struct WaveformPoint: Identifiable {
    let id: Int
    let timeSeconds: Double
    let amplitude: Double
}

struct SpectrumPoint: Identifiable {
    let id: Int
    let frequencyHz: Double
    let magnitude: Double
    let power: Double
}

struct SpectrogramPoint: Identifiable {
    let id: Int
    let timeSeconds: Double
    let frequencyHz: Double
    let normalizedPower: Double
}

struct PlotDocument {
    let waveform: SeismicWaveform
    let observedEvent: ObservedEvent?
    let analysis: WaveformAnalysis
    let spectralSummary: SpectralSummary
    let spectrogram: Spectrogram
    let waveformPoints: [WaveformPoint]
    let spectrumPoints: [SpectrumPoint]
    let spectrogramPoints: [SpectrogramPoint]

    var displayTitle: String {
        observedEvent?.event ?? waveform.event
    }

    var stationLine: String {
        guard let station = observedEvent?.station else {
            return "\(waveform.network).\(waveform.station) \(waveform.channel)"
        }

        return "\(station.code) \(station.name), \(station.country) \(station.channel)"
    }
}
#endif
