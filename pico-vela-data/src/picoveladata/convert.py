"""convert.py — read miniSEED files and export simple CSV files.

The CSV format is intentionally minimal so it can be loaded directly by Swift::

    time_seconds,amplitude
    0.000,1234
    0.010,1228
    0.020,1219

Usage example::

    from picoveladata.convert import convert_to_csv
    csv_path = convert_to_csv("data/raw/nk2017_IU_ANMO_BHZ_20170903T033000.mseed")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from obspy import read as obspy_read

logger = logging.getLogger(__name__)


def convert_to_csv(
    mseed_path: str | Path,
    *,
    processed_dir: Path = Path("data/processed"),
    trace_index: int = 0,
    time_precision: int = 6,
) -> Path:
    """Convert a miniSEED file to a two-column CSV file.

    Only the first trace (or the trace selected by ``trace_index``) is
    exported.  Time is expressed as seconds elapsed from the trace start.

    Parameters
    ----------
    mseed_path:
        Path to the miniSEED file to read.
    processed_dir:
        Directory where the CSV file will be written.
    trace_index:
        Index of the trace within the Stream to export (default 0).
    time_precision:
        Number of decimal places for the ``time_seconds`` column.

    Returns
    -------
    Path
        Absolute path to the written CSV file.

    Raises
    ------
    IndexError
        If ``trace_index`` is out of range for the Stream.
    """
    mseed_path = Path(mseed_path)
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Reading miniSEED: %s", mseed_path)
    stream = obspy_read(str(mseed_path))

    if trace_index >= len(stream):
        raise IndexError(
            f"trace_index {trace_index} is out of range; "
            f"stream contains {len(stream)} trace(s)."
        )

    trace = stream[trace_index]
    logger.info(
        "Exporting trace %s (sampling rate %.1f Hz, %d samples)",
        trace.id, trace.stats.sampling_rate, trace.stats.npts,
    )

    df = trace_to_dataframe(trace, time_precision=time_precision)

    stem = mseed_path.stem
    out_path = processed_dir / f"{stem}.csv"
    df.to_csv(out_path, index=False)

    logger.info("Saved CSV → %s  (%d rows)", out_path, len(df))
    return out_path.resolve()


def trace_to_dataframe(trace: "obspy.Trace", time_precision: int = 6) -> pd.DataFrame:  # type: ignore[name-defined]
    """Convert an ObsPy Trace to a two-column DataFrame.

    This is the shared helper used by both :func:`convert_to_csv` and the
    ``preprocess`` CLI command to ensure consistent output format.

    Parameters
    ----------
    trace:
        An :class:`obspy.Trace` whose data will be exported.
    time_precision:
        Number of decimal places for the ``time_seconds`` column.

    Returns
    -------
    pandas.DataFrame
        DataFrame with columns ``time_seconds`` and ``amplitude``.
        The ``amplitude`` column preserves the original ``trace.data`` dtype.
    """
    dt = 1.0 / trace.stats.sampling_rate
    times = np.arange(trace.stats.npts) * dt
    return pd.DataFrame({
        "time_seconds": np.round(times, time_precision),
        "amplitude": trace.data,
    })


def list_traces(mseed_path: str | Path) -> list[str]:
    """Return a list of trace IDs contained in a miniSEED file.

    Useful for inspecting multi-trace files before conversion.

    Parameters
    ----------
    mseed_path:
        Path to the miniSEED file.

    Returns
    -------
    list[str]
        SEED trace identifiers (``"NET.STA.LOC.CHA"``).
    """
    stream = obspy_read(str(mseed_path))
    return [tr.id for tr in stream]
