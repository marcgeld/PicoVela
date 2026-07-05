"""convert.py — read miniSEED files and export CSV files.

The CSV format keeps elapsed seconds and amplitude, and also includes UTC
timestamps so multiple event CSV files can be merged and sorted together::

    event,trace_id,network,station,location,channel,source_file,sample_time_utc,date_utc,time_utc,time_seconds,amplitude
    nk2017,IU.ANMO.00.BHZ,IU,ANMO,00,BHZ,nk2017.mseed,2017-09-03T03:30:00.000000Z,2017-09-03,03:30:00.000000,0.000,1234

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
    event: str | None = None,
) -> Path:
    """Convert a miniSEED file to a timestamped CSV file.

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
    event:
        Optional event label to include in each row.

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

    df = trace_to_dataframe(
        trace,
        time_precision=time_precision,
        event=event,
        source_file=mseed_path.name,
    )

    stem = mseed_path.stem
    out_path = processed_dir / f"{stem}.csv"
    df.to_csv(out_path, index=False)

    logger.info("Saved CSV → %s  (%d rows)", out_path, len(df))
    return out_path.resolve()


def trace_to_dataframe(
    trace: "obspy.Trace",  # type: ignore[name-defined]
    time_precision: int = 6,
    *,
    event: str | None = None,
    source_file: str | None = None,
) -> pd.DataFrame:
    """Convert an ObsPy Trace to a timestamped DataFrame.

    This is the shared helper used by both :func:`convert_to_csv` and the
    ``preprocess`` CLI command to ensure consistent output format.

    Parameters
    ----------
    trace:
        An :class:`obspy.Trace` whose data will be exported.
    time_precision:
        Number of decimal places for the ``time_seconds`` column.
    event:
        Optional event label to include in each row.
    source_file:
        Optional source file name to include in each row.

    Returns
    -------
    pandas.DataFrame
        DataFrame with UTC timestamp columns, ``time_seconds``, and ``amplitude``.
        The ``amplitude`` column preserves the original ``trace.data`` dtype.
    """
    dt = 1.0 / trace.stats.sampling_rate
    times = np.arange(trace.stats.npts) * dt
    sample_times = pd.to_datetime(
        trace.stats.starttime.timestamp + times,
        unit="s",
        utc=True,
    )

    return pd.DataFrame({
        "event": event or "",
        "trace_id": trace.id,
        "network": trace.stats.network,
        "station": trace.stats.station,
        "location": trace.stats.location,
        "channel": trace.stats.channel,
        "source_file": source_file or "",
        "sample_time_utc": sample_times.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "date_utc": sample_times.strftime("%Y-%m-%d"),
        "time_utc": sample_times.strftime("%H:%M:%S.%f"),
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
