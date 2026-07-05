"""preprocess.py — optional waveform preprocessing helpers.

Applies in-place preprocessing steps to an ObsPy ``Trace`` or the traces of
an ObsPy ``Stream``.  No spectral analysis is performed here; all FFT and
frequency-domain work belongs to PicoVela / SwiftNumerica.

Usage example::

    from obspy import read
    from picoveladata.preprocess import preprocess

    stream = read("data/raw/nk2017_IU_ANMO_BHZ_20170903T033000.mseed")
    preprocess(stream, remove_mean=True, detrend=True, normalize=True)
"""

from __future__ import annotations

import logging
from typing import Union

import numpy as np
from obspy import Stream, Trace

logger = logging.getLogger(__name__)

#: Union type for a single Trace or a full Stream.
WaveformData = Union[Trace, Stream]


def preprocess(
    data: WaveformData,
    *,
    remove_mean: bool = True,
    detrend: bool = True,
    normalize: bool = False,
    trim_start: int | None = None,
    trim_end: int | None = None,
) -> WaveformData:
    """Apply optional preprocessing steps to a Trace or Stream.

    Processing is applied **in-place** and the (modified) object is also
    returned for convenience.

    Parameters
    ----------
    data:
        An :class:`obspy.Trace` or :class:`obspy.Stream` to process.
    remove_mean:
        Subtract the mean of the data array from each sample.
    detrend:
        Remove a linear trend (least-squares fit) from the data.
    normalize:
        Scale each trace so that the maximum absolute amplitude equals 1.0.
        The data array will be cast to float64.
    trim_start:
        If given, discard samples before this zero-based sample index.
    trim_end:
        If given, discard samples from this zero-based sample index onward.

    Returns
    -------
    WaveformData
        The same object that was passed in (modified in-place).

    Raises
    ------
    TypeError
        If *data* is neither a :class:`~obspy.Trace` nor a
        :class:`~obspy.Stream`.
    """
    if isinstance(data, Trace):
        traces = [data]
    elif isinstance(data, Stream):
        traces = list(data)
    else:
        raise TypeError(f"Expected Trace or Stream, got {type(data).__name__!r}")

    for trace in traces:
        _preprocess_trace(
            trace,
            remove_mean=remove_mean,
            detrend=detrend,
            normalize=normalize,
            trim_start=trim_start,
            trim_end=trim_end,
        )

    return data


def _preprocess_trace(
    trace: Trace,
    *,
    remove_mean: bool,
    detrend: bool,
    normalize: bool,
    trim_start: int | None,
    trim_end: int | None,
) -> None:
    """Apply preprocessing steps to a single Trace (in-place)."""
    # --- sample trimming -------------------------------------------------
    if trim_start is not None or trim_end is not None:
        start = trim_start if trim_start is not None else 0
        end = trim_end if trim_end is not None else trace.stats.npts
        trace.data = trace.data[start:end]
        trace.stats.npts = len(trace.data)
        logger.debug(
            "%s  trimmed to samples [%d:%d] → %d samples",
            trace.id, start, end, trace.stats.npts,
        )

    # --- mean removal ----------------------------------------------------
    if remove_mean:
        mean_val = np.mean(trace.data)
        trace.data = trace.data - mean_val
        logger.debug("%s  removed mean (%.4g)", trace.id, mean_val)

    # --- linear detrend --------------------------------------------------
    if detrend:
        n = trace.stats.npts
        if n > 1:
            x = np.arange(n, dtype=np.float64)
            y = trace.data.astype(np.float64)
            slope, intercept = np.polyfit(x, y, 1)
            trace.data = (y - (slope * x + intercept)).astype(trace.data.dtype)
            logger.debug("%s  detrended (slope=%.4g)", trace.id, slope)

    # --- normalise -------------------------------------------------------
    if normalize:
        peak = np.max(np.abs(trace.data))
        if peak > 0:
            trace.data = (trace.data.astype(np.float64) / peak)
            logger.debug("%s  normalised (peak=%.4g)", trace.id, peak)
        else:
            logger.warning("%s  skipping normalise — all-zero data", trace.id)
