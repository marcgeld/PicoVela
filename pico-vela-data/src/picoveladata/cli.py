"""cli.py — Typer command-line interface for picoveladata.

Usage::

    uv run picovela fetch --event nk2017 --network IU --station ANMO --channel BHZ
    uv run picovela convert data/raw/nk2017_IU_ANMO_BHZ_20170903T033000.mseed
    uv run picovela preprocess data/raw/nk2017_IU_ANMO_BHZ_20170903T033000.mseed
    uv run picovela events
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from picoveladata.convert import convert_to_csv, list_traces
from picoveladata.fetch import KNOWN_EVENTS, fetch_event
from picoveladata.preprocess import preprocess as preprocess_waveform

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="picovela",
    help=(
        "PicoVela data pipeline — download seismic waveform data and export "
        "CSV files for Swift ingestion."
    ),
    add_completion=False,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(name)s  %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Common option types
# ---------------------------------------------------------------------------

_raw_dir_option = Annotated[
    Path,
    typer.Option("--raw-dir", help="Directory for raw miniSEED files."),
]
_processed_dir_option = Annotated[
    Path,
    typer.Option("--processed-dir", help="Directory for processed CSV files."),
]

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def fetch(
    event: Annotated[str, typer.Option("--event", "-e", help="Known event label (e.g. nk2017) or a descriptive name.")] = "",
    network: Annotated[Optional[str], typer.Option("--network", "-N", help="SEED network code.")] = None,
    station: Annotated[Optional[str], typer.Option("--station", "-S", help="SEED station code.")] = None,
    channel: Annotated[Optional[str], typer.Option("--channel", "-C", help="SEED channel code.")] = None,
    starttime: Annotated[Optional[str], typer.Option("--starttime", help="UTC start time (ISO-8601).")] = None,
    endtime: Annotated[Optional[str], typer.Option("--endtime", help="UTC end time (ISO-8601).")] = None,
    client: Annotated[str, typer.Option("--client", help="FDSN client name (e.g. IRIS, GEOFON).")] = "IRIS",
    raw_dir: _raw_dir_option = Path("data/raw"),
) -> None:
    """Download waveform data for a known event or an explicit time window.

    If --event names a known preset (see ``picovela events``), network /
    station / channel / time defaults are applied automatically.
    """
    if not event:
        typer.echo("ERROR: --event is required.", err=True)
        raise typer.Exit(code=1)

    try:
        out = fetch_event(
            event,
            network=network,
            station=station,
            channel=channel,
            starttime=starttime,
            endtime=endtime,
            client_name=client,
            raw_dir=raw_dir,
        )
        typer.echo(f"miniSEED saved → {out}")
    except Exception as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def convert(
    mseed: Annotated[Path, typer.Argument(help="Path to a miniSEED file.")],
    processed_dir: _processed_dir_option = Path("data/processed"),
    trace_index: Annotated[int, typer.Option("--trace-index", "-t", help="Index of the trace to export.")] = 0,
    list_only: Annotated[bool, typer.Option("--list-traces", help="Print trace IDs and exit without converting.")] = False,
) -> None:
    """Convert a miniSEED file to a two-column CSV (time_seconds, amplitude)."""
    if list_only:
        ids = list_traces(mseed)
        for i, tid in enumerate(ids):
            typer.echo(f"  [{i}] {tid}")
        return

    try:
        out = convert_to_csv(mseed, processed_dir=processed_dir, trace_index=trace_index)
        typer.echo(f"CSV saved → {out}")
    except Exception as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def preprocess(
    mseed: Annotated[Path, typer.Argument(help="Path to a miniSEED file to preprocess.")],
    processed_dir: _processed_dir_option = Path("data/processed"),
    no_mean: Annotated[bool, typer.Option("--no-mean", help="Skip mean removal.")] = False,
    no_detrend: Annotated[bool, typer.Option("--no-detrend", help="Skip linear detrend.")] = False,
    normalize: Annotated[bool, typer.Option("--normalize", help="Normalize amplitude to [-1, 1].")] = False,
    trim_start: Annotated[Optional[int], typer.Option("--trim-start", help="Discard samples before this index.")] = None,
    trim_end: Annotated[Optional[int], typer.Option("--trim-end", help="Discard samples from this index onward.")] = None,
) -> None:
    """Preprocess a miniSEED file and export a CSV.

    Applies mean removal, linear detrend, optional normalisation, and/or
    sample trimming before writing the CSV.  No spectral analysis is performed.
    """
    from obspy import read as obspy_read

    try:
        stream = obspy_read(str(mseed))
        preprocess_waveform(
            stream,
            remove_mean=not no_mean,
            detrend=not no_detrend,
            normalize=normalize,
            trim_start=trim_start,
            trim_end=trim_end,
        )

        processed_dir = Path(processed_dir)
        processed_dir.mkdir(parents=True, exist_ok=True)

        import numpy as np
        import pandas as pd

        trace = stream[0]
        dt = 1.0 / trace.stats.sampling_rate
        times = np.arange(trace.stats.npts) * dt
        df = pd.DataFrame({
            "time_seconds": np.round(times, 6),
            "amplitude": trace.data,
        })

        stem = mseed.stem
        out_path = processed_dir / f"{stem}_preprocessed.csv"
        df.to_csv(out_path, index=False)
        typer.echo(f"CSV saved → {out_path.resolve()}")
    except Exception as exc:
        typer.echo(f"ERROR: {exc}", err=True)
        raise typer.Exit(code=1)


@app.command()
def events() -> None:
    """List all known event presets."""
    typer.echo("Known event presets:\n")
    for label, info in KNOWN_EVENTS.items():
        typer.echo(f"  {label:<12}  {info['description']}")
        typer.echo(
            f"               {info['network']}.{info['station']} "
            f"{info['channel']}  {info['starttime']} → {info['endtime']}"
        )
        typer.echo()
