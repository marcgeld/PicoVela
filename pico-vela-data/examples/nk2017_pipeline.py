#!/usr/bin/env python
"""examples/nk2017_pipeline.py

End-to-end example: download the 2017 North Korean nuclear test waveform,
preprocess it, and export a CSV ready for PicoVela / SwiftNumerica.

Run from inside the pico-vela-data directory::

    uv run python examples/nk2017_pipeline.py

Or step-by-step via the CLI::

    uv run picovela fetch --event nk2017
    uv run picovela preprocess data/raw/nk2017_IU_ANMO_BHZ_20170903T033000.mseed \\
        --normalize
    uv run picovela convert data/raw/nk2017_IU_ANMO_BHZ_20170903T033000.mseed
"""

from pathlib import Path

from obspy import read as obspy_read

from picoveladata.convert import convert_to_csv
from picoveladata.fetch import fetch_event
from picoveladata.preprocess import preprocess

# 1. Download raw miniSEED
print("Step 1: Fetching waveform …")
mseed_path = fetch_event(
    "nk2017",
    raw_dir=Path("data/raw"),
)
print(f"  → {mseed_path}")

# 2. Preprocess (in-memory)
print("Step 2: Preprocessing …")
stream = obspy_read(str(mseed_path))
preprocess(stream, remove_mean=True, detrend=True, normalize=True)
print(f"  → {stream[0].stats.npts} samples, normalised")

# 3. Export preprocessed CSV directly
import numpy as np
import pandas as pd

trace = stream[0]
dt = 1.0 / trace.stats.sampling_rate
times = np.arange(trace.stats.npts) * dt
df = pd.DataFrame({
    "time_seconds": np.round(times, 6),
    "amplitude": trace.data,
})
out_csv = Path("data/processed") / f"{mseed_path.stem}_preprocessed.csv"
out_csv.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out_csv, index=False)
print(f"  → {out_csv.resolve()}  ({len(df)} rows)")

# 4. Alternatively, convert the raw miniSEED without preprocessing
print("Step 3: Converting raw miniSEED to CSV (no preprocessing) …")
raw_csv = convert_to_csv(mseed_path, processed_dir=Path("data/processed"))
print(f"  → {raw_csv}")

print("\nDone.  CSV files are ready for PicoVela ingestion.")
