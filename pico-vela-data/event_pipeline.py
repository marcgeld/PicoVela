#!/usr/bin/env python
"""Run PicoVela waveform data pipelines for curated events.

Run from inside the pico-vela-data directory:

    uv run python event_pipeline.py
    uv run python event_pipeline.py --group nuclear
    uv run python event_pipeline.py tohoku2011 haiti2010
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from picoveladata.event_sets import EVENT_GROUPS
from picoveladata.fetch import KNOWN_EVENTS
from picoveladata.pipeline import run_event_pipelines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch seismic waveform data and export PicoVela CSV files.",
    )
    parser.add_argument(
        "events",
        nargs="*",
        help="Event labels to run. Defaults to the selected group.",
    )
    parser.add_argument(
        "--group",
        choices=sorted(EVENT_GROUPS),
        default="requested",
        help="Curated event group to run when no explicit event labels are given.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory for downloaded miniSEED files.",
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory for exported CSV files.",
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Skip amplitude normalization in preprocessed CSV files.",
    )
    parser.add_argument(
        "--no-raw-convert",
        action="store_true",
        help="Skip the raw miniSEED-to-CSV export.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop at the first failed event instead of continuing.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available event groups and known event labels.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete generated files from raw and processed data directories, then exit.",
    )
    return parser.parse_args()


def print_catalog() -> None:
    print("Event groups:")
    for group, labels in EVENT_GROUPS.items():
        print(f"  {group}: {', '.join(labels)}")

    print("\nKnown events:")
    for label, info in KNOWN_EVENTS.items():
        print(f"  {label:<24} {info['description']}")


def clean_data_dirs(*directories: Path) -> list[Path]:
    """Remove generated data while keeping directories and .gitkeep files."""
    removed: list[Path] = []

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

        for child in directory.iterdir():
            if child.name == ".gitkeep":
                continue

            removed.append(child)
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    return removed


def print_progress(event: str, step: str) -> None:
    labels = {
        "start": "START",
        "fetch": "  fetching miniSEED",
        "preprocess": "  preprocessing",
        "convert": "  converting raw CSV",
        "done": "OK",
        "failed": "FAILED",
        "skipped": "SKIPPED",
    }
    label = labels.get(step, step)

    if step in {"start", "done", "failed", "skipped"}:
        print(f"{label} {event}", flush=True)
    else:
        print(f"{label} ...", flush=True)


def main() -> int:
    args = parse_args()

    if args.list:
        print_catalog()
        return 0

    if args.clean:
        removed = clean_data_dirs(args.raw_dir, args.processed_dir)
        print(f"Cleaned {args.raw_dir} and {args.processed_dir}.")
        print(f"Removed {len(removed)} item(s).")
        return 0

    events = tuple(args.events) if args.events else EVENT_GROUPS[args.group]
    print(f"Running {len(events)} event pipeline(s): {', '.join(events)}")

    run = run_event_pipelines(
        events,
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
        normalize=not args.no_normalize,
        convert_raw=not args.no_raw_convert,
        continue_on_error=not args.stop_on_error,
        progress=print_progress,
    )

    if run.timeline_csv is not None:
        print(f"\nTimeline: {run.timeline_csv}")

    for result in run.results:
        print(f"\nOK {result.event}")
        print(f"  miniSEED:       {result.mseed_path}")
        print(f"  preprocessed:   {result.preprocessed_csv}")
        if result.raw_csv is not None:
            print(f"  raw CSV:        {result.raw_csv}")

    for failure in run.failures:
        print(f"\nFAILED {failure.event}")
        print(f"  {failure.error}")

    for skipped in run.skipped:
        print(f"\nSKIPPED {skipped.event}")
        print("  No FDSN waveform data was available for this best-effort event.")

    print(
        f"\nDone. {len(run.results)} succeeded, "
        f"{len(run.failures)} failed, "
        f"{len(run.skipped)} skipped."
    )
    return 1 if run.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
