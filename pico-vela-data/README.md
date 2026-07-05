# pico-vela-data

A tiny seismic waveform data-preparation pipeline for the Swift project
[PicoVela](../README.md), which performs all numerical analysis using
SwiftNumerica.

This project is **intentionally small**.  Think of it as:

> "A tiny data preparation pipeline for a tiny homage to Project Vela."

---

## Responsibilities

| ✅ This project does … | ❌ This project does NOT … |
|---|---|
| Download historical waveform data from public FDSN archives | FFT / spectral analysis |
| Extract samples from miniSEED files | Classification |
| Optional minimal preprocessing (mean removal, detrend, normalise, trim) | Visualisation |
| Export simple timestamped CSV files for Swift ingestion | Any analysis belonging to PicoVela / SwiftNumerica |

---

## Project structure

```
pico-vela-data/
├── pyproject.toml          # uv project manifest
├── uv.lock                 # locked dependency graph
├── event_pipeline.py       # run curated event pipelines
├── src/
│   └── picoveladata/
│       ├── __init__.py
│       ├── fetch.py        # download waveforms via ObsPy FDSN clients
│       ├── convert.py      # miniSEED → CSV
│       ├── preprocess.py   # mean removal, detrend, normalise, trim
│       ├── pipeline.py     # reusable fetch/preprocess/convert pipeline
│       ├── event_sets.py   # curated event groups
│       ├── stations.py     # observing-station metadata
│       └── cli.py          # Typer CLI  (uv run picovela …)
├── data/
│   ├── raw/                # downloaded miniSEED files
│   └── processed/          # exported CSV files
```

---

## Requirements

- Python ≥ 3.14
- [uv](https://docs.astral.sh/uv/) for dependency management

---

## Quick start

```bash
# install dependencies
cd pico-vela-data
uv sync

# list known event presets
uv run picovela events

# remove generated raw/processed data, keeping the data directories
uv run python event_pipeline.py --clean

# download the 2017 North Korean nuclear test waveform
uv run picovela fetch \
    --event nk2017 \
    --network IU \
    --station ANMO \
    --channel BHZ

# convert the miniSEED to CSV
uv run picovela convert \
    data/raw/nk2017_IU_ANMO_BHZ_20170903T033000.mseed

# preprocess and convert in one step (mean removal + detrend + normalise)
uv run picovela preprocess \
    data/raw/nk2017_IU_ANMO_BHZ_20170903T033000.mseed \
    --normalize

# run the full curated event list
uv run python event_pipeline.py

# run every known event preset
uv run python event_pipeline.py --group all

# or run a subset
uv run python event_pipeline.py --group nuclear
uv run python event_pipeline.py tohoku2011 haiti2010
```

---

## CSV format

```
event,trace_id,network,station,location,channel,source_file,sample_time_utc,date_utc,time_utc,time_seconds,amplitude
nk2017,IU.ANMO.00.BHZ,IU,ANMO,00,BHZ,nk2017_IU_ANMO_BHZ_20170903T033000.mseed,2017-09-03T03:30:00.000000Z,2017-09-03,03:30:00.000000,0.000000,1234
nk2017,IU.ANMO.00.BHZ,IU,ANMO,00,BHZ,nk2017_IU_ANMO_BHZ_20170903T033000.mseed,2017-09-03T03:30:00.010000Z,2017-09-03,03:30:00.010000,0.010000,1228
```

Each waveform CSV includes absolute UTC sample time plus elapsed seconds, so
all processed CSV files can be concatenated and sorted by `sample_time_utc`.
`time_seconds` and `amplitude` remain available for numerical ingestion.

`event_pipeline.py` also writes `data/processed/timeline.csv` for the selected
run:

```
event,event_type,network,station,station_code,station_name,country,channel,client,event_time
nk2017,nuclear,IU,ANMO,IU.ANMO,Albuquerque Seismological Laboratory,USA,BHZ,EARTHSCOPE,2017-09-03T03:30:00Z
```

---

## Station metadata

PicoVela stores a small typed database of observing stations in
`picoveladata.stations`. The Python side still only acquires and prepares
waveform data, but the generated `timeline.csv` now records where each
successful event was observed: network, station code, station name, country,
channel, client, event type, and UTC event time.

That extra context lets the Swift application present both sides of a Vela-like
report: what happened, and which monitoring station saw it. This mirrors the
historical flavor of nuclear-test monitoring systems without moving scientific
analysis out of Swift/SwiftNumerica.

---

## Known event presets

| Label | Description |
|---|---|
| `nk2006` | North Korean nuclear test 2006-10-09 |
| `nk2009` | North Korean nuclear test 2009-05-25 |
| `nk2013` | North Korean nuclear test 2013-02-12 |
| `nk2016a` | North Korean nuclear test 2016-01-06 |
| `nk2016b` | North Korean nuclear test 2016-09-09 |
| `nk2017` | North Korean nuclear test 2017-09-03 |
| `tohoku2011` | Tohoku-Oki Mw 9.0 earthquake 2011-03-11 |
| `haiti2010` | Haiti Mw 7.0 earthquake 2010-01-12 |
| `indian_ocean2004` | Sumatra-Andaman / Indian Ocean Mw 9.1 earthquake and tsunami 2004-12-26 |
| `chile2010` | Maule, Chile Mw 8.8 earthquake 2010-02-27 |
| `spacex_starship_ift4` | SpaceX Starship integrated flight test 4 launch 2024-06-06 |
| `spacex_starship_ift5` | SpaceX Starship integrated flight test 5 launch 2024-10-13 |
| `ariane6_maiden2024` | Ariane 6 maiden flight from Guiana Space Centre 2024-07-09 |
| `ariane5_juice2023` | Ariane 5 VA260 / JUICE launch from Guiana Space Centre 2023-04-14 |
| `eyjafjallajokull2010` | Eyjafjallajokull 2010 explosive eruption phase |
| `hunga_tonga2022` | Hunga Tonga-Hunga Ha'apai eruption and tsunami 2022-01-15 |
| `pokhran2_1998_05_11` | Pokhran-II / Operation Shakti nuclear tests 1998-05-11 |
| `pokhran2_1998_05_13` | Pokhran-II / Operation Shakti sub-kiloton tests 1998-05-13 |
| `chagai1_1998_05_28` | Pakistan Chagai-I nuclear tests 1998-05-28 |
| `chagai2_1998_05_30` | Pakistan Chagai-II nuclear test 1998-05-30 |

Event groups available through `event_pipeline.py`:

| Group | Contents |
|---|---|
| `all` | Every known event preset |
| `requested` | The earthquake, launch, volcanic, North Korean, Indian and Pakistani event set above |
| `earthquakes` | Tohoku, Haiti, Indian Ocean, Chile |
| `volcanic` | Eyjafjallajokull, Hunga Tonga-Hunga Ha'apai |
| `launches` | SpaceX Starship and Ariane launches |
| `north_korea` | North Korean nuclear tests from 2006 through 2017 |
| `nuclear` | North Korean, Pokhran-II and Chagai tests |

Launch presets are best-effort FDSN windows rather than guaranteed strong
seismic detections. The runner continues after individual event failures by
default and reports which downloads succeeded.

---

## Data sources

Waveform data is fetched from public FDSN-compatible seismic services:

- **EarthScope** — `Client("EARTHSCOPE")`
- **GEOFON** — `Client("GEOFON")`
- Any other FDSN-compatible service supported by ObsPy

---

## CLI reference

```
uv run picovela --help
uv run picovela fetch --help
uv run picovela convert --help
uv run picovela preprocess --help
uv run picovela events
uv run python event_pipeline.py --list
```

---

## Programmatic API

```python
from picoveladata.fetch import fetch_event
from picoveladata.convert import convert_to_csv
from picoveladata.pipeline import run_event_pipeline
from picoveladata.preprocess import preprocess
from obspy import read

# fetch
mseed = fetch_event("nk2017")

# preprocess in-memory
stream = read(str(mseed))
preprocess(stream, remove_mean=True, detrend=True, normalize=True)

# export CSV
csv_path = convert_to_csv(mseed)

# or run the reusable pipeline
result = run_event_pipeline("tohoku2011")
```
