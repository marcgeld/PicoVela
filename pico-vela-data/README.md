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
| Export simple two-column CSV files for Swift ingestion | Any analysis belonging to PicoVela / SwiftNumerica |

---

## Project structure

```
pico-vela-data/
├── pyproject.toml          # uv project manifest
├── uv.lock                 # locked dependency graph
├── src/
│   └── picoveladata/
│       ├── __init__.py
│       ├── fetch.py        # download waveforms via ObsPy FDSN clients
│       ├── convert.py      # miniSEED → CSV
│       ├── preprocess.py   # mean removal, detrend, normalise, trim
│       └── cli.py          # Typer CLI  (uv run picovela …)
├── data/
│   ├── raw/                # downloaded miniSEED files
│   └── processed/          # exported CSV files
└── examples/
    └── nk2017_pipeline.py  # end-to-end example
```

---

## Requirements

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) for dependency management

---

## Quick start

```bash
# install dependencies
cd pico-vela-data
uv sync

# list known event presets
uv run picovela events

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
```

---

## CSV format

```
time_seconds,amplitude
0.000000,1234
0.010000,1228
0.020000,1219
```

The format is intentionally minimal so it can be read directly by the Swift
project using standard CSV parsing.

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
| `chile2010` | Maule, Chile Mw 8.8 earthquake 2010-02-27 |

---

## Data sources

Waveform data is fetched from public FDSN-compatible seismic services:

- **IRIS / EarthScope** — `Client("IRIS")`
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
```

---

## Programmatic API

```python
from picoveladata.fetch import fetch_event
from picoveladata.convert import convert_to_csv
from picoveladata.preprocess import preprocess
from obspy import read

# fetch
mseed = fetch_event("nk2017")

# preprocess in-memory
stream = read(str(mseed))
preprocess(stream, remove_mean=True, detrend=True, normalize=True)

# export CSV
csv_path = convert_to_csv(mseed)
```
