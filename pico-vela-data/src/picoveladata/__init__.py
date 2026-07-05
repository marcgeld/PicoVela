"""
picoveladata — seismic waveform data pipeline for PicoVela.

Responsibilities:
  - Download historical waveform data from public FDSN archives.
  - Extract samples from miniSEED files.
  - Perform minimal preprocessing (mean removal, detrend, normalise, trim).
  - Export timestamped CSV files and station-aware timelines for Swift ingestion.

All numerical analysis (FFT, spectral analysis, classification) is left to
the Swift project PicoVela / SwiftNumerica.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("picoveladata")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = ["__version__"]
