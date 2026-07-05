#if os(macOS)
import Charts
import SwiftUI

struct PlotView: View {
    let document: PlotDocument

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 18) {
                header
                chartSection(title: "Waveform", subtitle: "Time vs normalized amplitude") {
                    Chart(document.waveformPoints) { point in
                        LineMark(
                            x: .value("Seconds", point.timeSeconds),
                            y: .value("Amplitude", point.amplitude)
                        )
                        .foregroundStyle(.blue)
                        .lineStyle(.init(lineWidth: 1.2))
                    }
                    .chartXAxisLabel("Seconds")
                    .chartYAxisLabel("Amplitude")
                }

                chartSection(title: "FFT / Periodogram", subtitle: "Frequency vs power") {
                    Chart(document.spectrumPoints) { point in
                        LineMark(
                            x: .value("Frequency", point.frequencyHz),
                            y: .value("Power", point.power)
                        )
                        .foregroundStyle(.red)
                        .lineStyle(.init(lineWidth: 1.2))
                    }
                    .chartXAxisLabel("Hz")
                    .chartYAxisLabel("Power")
                }

                chartSection(title: "Waterfall / Spectrogram", subtitle: "Time vs frequency power") {
                    SpectrogramCanvas(document: document)
                        .frame(height: 220)
                }

                footer
            }
            .padding(24)
        }
        .frame(minWidth: 980, minHeight: 940)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(document.displayTitle)
                .font(.system(size: 28, weight: .semibold))
            Text(document.stationLine)
                .font(.headline)
                .foregroundStyle(.secondary)
        }
    }

    private func chartSection<Content: View>(
        title: String,
        subtitle: String,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline) {
                Text(title)
                    .font(.headline)
                Text(subtitle)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            content()
                .frame(height: 240)
        }
    }

    private var footer: some View {
        let dominant = document.spectralSummary.dominantBin?.frequencyHz
        let dominantText = dominant.map { String(format: "%.3f Hz", $0) } ?? "unknown"
        let sampleRate = document.analysis.sampleRateHz.map { String(format: "%.2f Hz", $0) } ?? "unknown"

        return HStack(spacing: 18) {
            metric("Samples", "\(document.analysis.sampleCount)")
            metric("Sample rate", sampleRate)
            metric("Peak amplitude", String(format: "%.4f", document.analysis.peakAbsoluteAmplitude))
            metric("Dominant bin", dominantText)
            metric("Peaks", "\(document.spectralSummary.waveformPeakCount)")
            metric(
                "Waterfall",
                "\(document.spectrogram.windowSize)/\(document.spectrogram.hopSize)"
            )
        }
        .font(.subheadline)
    }

    private func metric(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .foregroundStyle(.secondary)
            Text(value)
                .fontWeight(.semibold)
        }
    }
}

struct SpectrogramCanvas: View {
    let document: PlotDocument

    var body: some View {
        Canvas { context, size in
            let points = document.spectrogramPoints
            guard !points.isEmpty else {
                return
            }

            let frameCount = max(1, document.spectrogram.frameCount)
            let binCount = max(1, document.spectrogram.frequencyBinCount)
            let cellWidth = size.width / Double(frameCount)
            let cellHeight = size.height / Double(binCount)

            for point in points {
                let x = Double(point.id / binCount) * cellWidth
                let frequencyIndex = point.id % binCount
                let y = size.height - (Double(frequencyIndex + 1) * cellHeight)
                let rect = CGRect(
                    x: x,
                    y: y,
                    width: max(1, cellWidth),
                    height: max(1, cellHeight)
                )

                context.fill(
                    Path(rect),
                    with: .color(color(for: point.normalizedPower))
                )
            }
        }
        .background(Color.black.opacity(0.88))
        .overlay(alignment: .bottomLeading) {
            Text("time")
                .font(.caption)
                .foregroundStyle(.secondary)
                .padding(6)
        }
        .overlay(alignment: .topLeading) {
            Text("Hz")
                .font(.caption)
                .foregroundStyle(.secondary)
                .padding(6)
        }
    }

    private func color(for normalizedPower: Double) -> Color {
        let value = min(1, max(0, normalizedPower))
        return Color(
            hue: 0.66 - (0.66 * value),
            saturation: 0.88,
            brightness: 0.18 + (0.82 * value)
        )
    }
}
#endif
