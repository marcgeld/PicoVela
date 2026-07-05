"""fetch.py — download seismic waveform data from public FDSN services.

Usage example::

    from picoveladata.fetch import fetch_event, KNOWN_EVENTS
    path = fetch_event("nk2017", network="IU", station="ANMO", channel="BHZ")
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from obspy import UTCDateTime
from obspy.clients.fdsn import Client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Well-known event presets
# ---------------------------------------------------------------------------

#: Mapping of short event labels to (description, starttime, endtime, preferred_network, preferred_station).
#: Times are UTC strings accepted by ``obspy.UTCDateTime``.
KNOWN_EVENTS: dict[str, dict] = {
    # North Korean nuclear tests (seismic detections at IRIS/ANMO)
    "nk2006": {
        "description": "North Korean nuclear test 2006-10-09",
        "starttime": "2006-10-09T01:35:00",
        "endtime": "2006-10-09T01:55:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "IRIS",
    },
    "nk2009": {
        "description": "North Korean nuclear test 2009-05-25",
        "starttime": "2009-05-25T00:54:00",
        "endtime": "2009-05-25T01:14:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "IRIS",
    },
    "nk2013": {
        "description": "North Korean nuclear test 2013-02-12",
        "starttime": "2013-02-12T02:57:00",
        "endtime": "2013-02-12T03:17:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "IRIS",
    },
    "nk2016a": {
        "description": "North Korean nuclear test 2016-01-06",
        "starttime": "2016-01-06T01:30:00",
        "endtime": "2016-01-06T01:50:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "IRIS",
    },
    "nk2016b": {
        "description": "North Korean nuclear test 2016-09-09",
        "starttime": "2016-09-09T00:30:00",
        "endtime": "2016-09-09T00:50:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "IRIS",
    },
    "nk2017": {
        "description": "North Korean nuclear test 2017-09-03",
        "starttime": "2017-09-03T03:30:00",
        "endtime": "2017-09-03T03:50:00",
        "network": "IU",
        "station": "ANMO",
        "channel": "BHZ",
        "client": "IRIS",
    },
    # Historical earthquakes
    "tohoku2011": {
        "description": "Tohoku-Oki Mw 9.0 earthquake 2011-03-11",
        "starttime": "2011-03-11T05:46:00",
        "endtime": "2011-03-11T06:16:00",
        "network": "IU",
        "station": "ANMO",
        "channel": "BHZ",
        "client": "IRIS",
    },
    "chile2010": {
        "description": "Maule, Chile Mw 8.8 earthquake 2010-02-27",
        "starttime": "2010-02-27T06:34:00",
        "endtime": "2010-02-27T07:04:00",
        "network": "IU",
        "station": "ANMO",
        "channel": "BHZ",
        "client": "IRIS",
    },
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_event(
    event: str,
    *,
    network: Optional[str] = None,
    station: Optional[str] = None,
    channel: Optional[str] = None,
    starttime: Optional[str] = None,
    endtime: Optional[str] = None,
    client_name: str = "IRIS",
    raw_dir: Path = Path("data/raw"),
) -> Path:
    """Download waveform data for a named event or explicit time window.

    Parameters
    ----------
    event:
        Short label for a known event (e.g. ``"nk2017"``) **or** any
        descriptive string used to name the output file when explicit
        ``starttime``/``endtime`` are supplied.
    network:
        SEED network code.  Defaults to the preset value for known events.
    station:
        SEED station code.  Defaults to the preset value for known events.
    channel:
        SEED channel code.  Defaults to the preset value for known events.
    starttime:
        ISO-8601 UTC start time string (overrides preset).
    endtime:
        ISO-8601 UTC end time string (overrides preset).
    client_name:
        FDSN client identifier (e.g. ``"IRIS"``, ``"GEOFON"``).
        Overridden by preset if event is known and ``client_name`` is not
        explicitly set.
    raw_dir:
        Directory under which the miniSEED file is saved.

    Returns
    -------
    Path
        Absolute path to the downloaded miniSEED file.

    Raises
    ------
    ValueError
        If required parameters are missing and the event is not in
        :data:`KNOWN_EVENTS`.
    """
    preset = KNOWN_EVENTS.get(event, {})

    net = network or preset.get("network")
    sta = station or preset.get("station")
    cha = channel or preset.get("channel")
    t_start = UTCDateTime(starttime) if starttime else UTCDateTime(preset.get("starttime", ""))
    t_end = UTCDateTime(endtime) if endtime else UTCDateTime(preset.get("endtime", ""))
    client_id = preset.get("client", client_name) if not network and not starttime else client_name

    missing = [name for name, val in [("network", net), ("station", sta), ("channel", cha)] if not val]
    if missing:
        raise ValueError(
            f"Missing required parameters: {', '.join(missing)}. "
            "Provide them explicitly or use a known event label."
        )

    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    stem = f"{event}_{net}_{sta}_{cha}_{t_start.strftime('%Y%m%dT%H%M%S')}"
    out_path = raw_dir / f"{stem}.mseed"

    if out_path.exists():
        logger.info("miniSEED already cached: %s", out_path)
        return out_path.resolve()

    logger.info(
        "Fetching %s %s %s.%s from %s to %s via %s",
        event, cha, net, sta, t_start, t_end, client_id,
    )

    client = Client(client_id)
    stream = client.get_waveforms(
        network=net,
        station=sta,
        location="*",
        channel=cha,
        starttime=t_start,
        endtime=t_end,
    )

    stream.write(str(out_path), format="MSEED")
    logger.info("Saved miniSEED → %s", out_path)
    return out_path.resolve()
