"""Reusable waveform fetch/preprocess/convert pipeline."""

from __future__ import annotations

import csv
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from obspy import UTCDateTime
from obspy import read as obspy_read

from picoveladata.convert import convert_to_csv, trace_to_dataframe
from picoveladata.event_sets import event_type
from picoveladata.fetch import KNOWN_EVENTS, fetch_event
from picoveladata.preprocess import preprocess
from picoveladata.stations import station_country, station_name

ProgressCallback = Callable[[str, str], None]


@dataclass(frozen=True)
class PipelineResult:
    """Files produced for one event pipeline run."""

    event: str
    mseed_path: Path
    preprocessed_csv: Path
    raw_csv: Path | None


@dataclass(frozen=True)
class PipelineFailure:
    """Error captured while running one event pipeline."""

    event: str
    error: str


@dataclass(frozen=True)
class PipelineSkipped:
    """Optional event that had no available waveform data."""

    event: str
    reason: str


@dataclass(frozen=True)
class PipelineRun:
    """Summary for a batch of event pipeline runs."""

    results: tuple[PipelineResult, ...]
    failures: tuple[PipelineFailure, ...]
    skipped: tuple[PipelineSkipped, ...]
    timeline_csv: Path | None = None


def preprocess_to_csv(
    mseed_path: Path,
    *,
    processed_dir: Path = Path("data/processed"),
    normalize: bool = True,
    event: str | None = None,
    progress: ProgressCallback | None = None,
) -> Path:
    """Preprocess one miniSEED file and export a PicoVela-ready CSV."""
    if progress is not None and event is not None:
        progress(event, "preprocess")
    stream = obspy_read(str(mseed_path))
    preprocess(stream, remove_mean=True, detrend=True, normalize=normalize)

    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    df = trace_to_dataframe(stream[0], event=event, source_file=mseed_path.name)
    out_csv = processed_dir / f"{mseed_path.stem}_preprocessed.csv"
    df.to_csv(out_csv, index=False)
    return out_csv.resolve()


def run_event_pipeline(
    event: str,
    *,
    raw_dir: Path = Path("data/raw"),
    processed_dir: Path = Path("data/processed"),
    normalize: bool = True,
    convert_raw: bool = True,
    progress: ProgressCallback | None = None,
) -> PipelineResult:
    """Fetch one event and export preprocessed and optional raw CSV files."""
    if progress is not None:
        progress(event, "fetch")
    mseed_path = fetch_event(event, raw_dir=raw_dir)
    preprocessed_csv = preprocess_to_csv(
        mseed_path,
        processed_dir=processed_dir,
        normalize=normalize,
        event=event,
        progress=progress,
    )
    if progress is not None and convert_raw:
        progress(event, "convert")
    raw_csv = (
        convert_to_csv(mseed_path, processed_dir=processed_dir, event=event)
        if convert_raw
        else None
    )

    return PipelineResult(
        event=event,
        mseed_path=mseed_path,
        preprocessed_csv=preprocessed_csv,
        raw_csv=raw_csv,
    )


def run_event_pipelines(
    events: tuple[str, ...] | list[str],
    *,
    raw_dir: Path = Path("data/raw"),
    processed_dir: Path = Path("data/processed"),
    normalize: bool = True,
    convert_raw: bool = True,
    continue_on_error: bool = True,
    write_timeline: bool = True,
    progress: ProgressCallback | None = None,
) -> PipelineRun:
    """Run the waveform pipeline for several events."""
    results: list[PipelineResult] = []
    failures: list[PipelineFailure] = []
    skipped: list[PipelineSkipped] = []
    timeline_csv = None

    for event in events:
        if progress is not None:
            progress(event, "start")
        try:
            result = run_event_pipeline(
                event,
                raw_dir=raw_dir,
                processed_dir=processed_dir,
                normalize=normalize,
                convert_raw=convert_raw,
                progress=progress,
            )
            results.append(result)
            if progress is not None:
                progress(event, "done")
        except Exception as exc:
            if KNOWN_EVENTS.get(event, {}).get("allow_missing"):
                skipped.append(PipelineSkipped(event=event, reason=str(exc)))
                if progress is not None:
                    progress(event, "skipped")
                continue
            if not continue_on_error:
                raise
            failures.append(PipelineFailure(event=event, error=str(exc)))
            if progress is not None:
                progress(event, "failed")

    if write_timeline:
        timeline_csv = write_timeline_csv(results, processed_dir=processed_dir)

    return PipelineRun(
        results=tuple(results),
        failures=tuple(failures),
        skipped=tuple(skipped),
        timeline_csv=timeline_csv,
    )


def write_timeline_csv(
    results: tuple[PipelineResult, ...] | list[PipelineResult],
    *,
    processed_dir: Path = Path("data/processed"),
    filename: str = "timeline.csv",
) -> Path:
    """Write report-style event and observing-station metadata."""
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / filename

    fieldnames = [
        "event",
        "event_type",
        "network",
        "station",
        "station_code",
        "station_name",
        "country",
        "channel",
        "client",
        "event_time",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            info = KNOWN_EVENTS.get(result.event, {})
            network, station, channel = _observed_trace_codes(result, info)
            station_code = f"{network}.{station}" if network and station else ""

            writer.writerow({
                "event": result.event,
                "event_type": event_type(result.event),
                "network": network,
                "station": station,
                "station_code": station_code,
                "station_name": station_name(station_code) if station_code else "",
                "country": station_country(station_code) if station_code else "",
                "channel": channel,
                "client": str(info.get("client", "")),
                "event_time": _format_utc(str(info.get("starttime", ""))),
            })

    return out_path.resolve()


def _observed_trace_codes(
    result: PipelineResult,
    info: dict[str, object],
) -> tuple[str, str, str]:
    """Return network, station, and channel from the produced miniSEED."""
    try:
        trace = obspy_read(str(result.mseed_path))[0]
    except Exception:
        return (
            str(info.get("network", "")),
            str(info.get("station", "")),
            str(info.get("channel", "")),
        )

    return (
        str(trace.stats.network),
        str(trace.stats.station),
        str(trace.stats.channel),
    )


def _format_utc(value: str) -> str:
    """Format an ISO-like UTC value with an explicit trailing ``Z``."""
    if not value:
        return ""
    return UTCDateTime(value).strftime("%Y-%m-%dT%H:%M:%SZ")
