# PicoVela

PicoVela is a small educational exploration inspired by Project Vela, the Cold
War effort to detect clandestine nuclear weapons tests. It uses Python only to
acquire and prepare seismic waveform data, then lets Swift and
[SwiftNumerica](https://github.com/marcgeld/SwiftNumerica) do the numerical
analysis and presentation.

The guiding idea is simple:

- Python answers: what data should we fetch, and how do we turn it into clean
  CSV files?
- Swift answers: what happened, where was it observed, and what does the signal
  look like in time and frequency?
- SwiftNumerica should shine: tensors, signals, descriptive statistics, FFT,
  periodograms, peak detection, and spectrograms sit at the center of the
  analysis path.

## Project Shape

```
PicoVela/
├── Package.swift                 # Swift package: library + plotting executable
├── Sources/
│   ├── PicoVela/                 # Pure Swift analysis library
│   └── PicoVelaPlot/             # macOS plotting executable
├── Tests/
│   └── PicoVelaTests/            # Swift tests
└── pico-vela-data/               # Python data-preparation project
```

The boundary is intentional. `pico-vela-data` downloads and prepares waveform
CSV files; `PicoVela` loads those files into Swift models and converts
amplitudes into SwiftNumerica tensors and signals.

## Requirements

- Swift 6.2 or newer
- macOS 14 or newer for the plotting executable
- Python 3.14 and `uv` for the data-preparation project

## Data Preparation

The Python project lives under `pico-vela-data/`. It fetches waveform data from
public FDSN services, preprocesses miniSEED traces, writes timestamped waveform
CSV files, and writes a station-aware `timeline.csv`.

```bash
cd pico-vela-data
uv sync

# List known event presets and groups
uv run python event_pipeline.py --list

# Remove generated raw/processed files but keep the data directories
uv run python event_pipeline.py --clean

# Fetch and process the curated requested set
uv run python event_pipeline.py

# Or run a focused group
uv run python event_pipeline.py --group nuclear
```

Processed waveform CSV files contain absolute UTC sample timestamps plus
elapsed seconds:

```csv
event,trace_id,network,station,location,channel,source_file,sample_time_utc,date_utc,time_utc,time_seconds,amplitude
nk2017,IU.ANMO.00.BHZ,IU,ANMO,00,BHZ,nk2017_IU_ANMO_BHZ_20170903T033000.mseed,2017-09-03T03:30:00.000000Z,2017-09-03,03:30:00.000000,0.000000,1234
```

`timeline.csv` records what happened and where it was observed:

```csv
event,event_type,network,station,station_code,station_name,country,channel,client,event_time
nk2017,nuclear,IU,ANMO,IU.ANMO,Albuquerque Seismological Laboratory,USA,BHZ,EARTHSCOPE,2017-09-03T03:30:00Z
```

See [pico-vela-data/README.md](pico-vela-data/README.md) for the full Python
pipeline, event groups, station metadata, and FDSN notes.

## Event Sets

The curated catalog currently includes:

- North Korean nuclear tests from 2006 through 2017
- Pokhran-II and Chagai nuclear tests
- Tohoku 2011, Haiti 2010, Indian Ocean 2004, and Chile 2010 earthquakes
- Eyjafjallajokull 2010 and Hunga Tonga-Hunga Ha'apai 2022 volcanic events
- SpaceX Starship and Ariane launch windows

Older events without reliable FDSN waveform availability were intentionally
removed from the runnable catalog, including Apollo 11, the Vela incident, and
the Nevada underground tests. The project favors events that can be fetched and
processed through the normal data pipeline.

## Swift Library

The `PicoVela` library is intentionally small and domain-focused. It provides:

- `PicoVelaDataLoader` for `timeline.csv` and `*_preprocessed.csv`
- `ObservedEvent`, `ObservingStation`, `SeismicWaveform`, and `WaveformSample`
- `WaveformAnalyzer` for first-pass signal analysis
- `WaveformAnalysis` with SwiftNumerica `Tensor<Double>` and `Signal`
- `SpectralSummary` for FFT/periodogram-derived frequency information
- `Spectrogram` for Hann-windowed waterfall data

Example:

```swift
import Foundation
import PicoVela

let loader = PicoVelaDataLoader(
    processedDirectory: URL(filePath: "pico-vela-data/data/processed")
)

let timeline = try loader.loadTimeline()
let waveforms = try loader.loadPreprocessedWaveforms()
let analysis = try WaveformAnalyzer().analyze(waveforms[0])
let spectrum = analysis.spectralSummary()
let spectrogram = analysis.spectrogram(windowSize: 512, hopSize: 128)

print(timeline[0].station.name)
print(analysis.peakAbsoluteAmplitude)
print(spectrum?.dominantBin?.frequencyHz ?? 0)
print(spectrogram?.frameCount ?? 0)
```

The analysis path uses SwiftNumerica for tensor statistics, signal
representation, FFT, periodograms, peak detection, Hann windows, and
spectrogram frame transforms.

## Plotting

Plotting is deliberately separate from the core library. The macOS executable
target `PicoVelaPlot` owns SwiftUI, Charts, AppKit window management, scrolling,
and the `Command-Q` quit menu item. The `PicoVela` library remains clean,
testable, and free of GUI concerns.

Open a plotting window:

```bash
swift run picovela-plot --event nk2017
```

Choose data directory, waveform downsampling, and spectrogram parameters:

```bash
swift run picovela-plot \
  --processed-dir pico-vela-data/data/processed \
  --event nk2017 \
  --max-samples 5000 \
  --spectrogram-window 512 \
  --spectrogram-hop 128
```

The plotting window shows:

- waveform: time vs amplitude
- FFT / periodogram: frequency vs power
- waterfall / spectrogram: time vs frequency power
- event and observing-station context
- summary metrics such as sample count, sample rate, peak amplitude, dominant
  frequency bin, peak count, and spectrogram window/hop settings

The content is scrollable so the full report remains usable on smaller
screens.

## Build And Test

```bash
swift build
swift build --product picovela-plot
swift test
swift run picovela-plot --help
```

## Current Philosophy

PicoVela is not trying to be a full seismology workbench. It is a compact,
educational Project Vela-inspired toolkit:

- Python prepares historical waveform data and station context.
- Swift models events, stations, waveforms, and reports.
- SwiftNumerica performs the numerical work.
- The plotting executable provides a lightweight window into the results
  without turning the project into a full GUI application.
