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
    # North Korean nuclear tests (seismic detections at EarthScope/ANMO)
    "nk2006": {
        "description": "North Korean nuclear test 2006-10-09",
        "starttime": "2006-10-09T01:35:00",
        "endtime": "2006-10-09T01:55:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    "nk2009": {
        "description": "North Korean nuclear test 2009-05-25",
        "starttime": "2009-05-25T00:54:00",
        "endtime": "2009-05-25T01:14:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    "nk2013": {
        "description": "North Korean nuclear test 2013-02-12",
        "starttime": "2013-02-12T02:57:00",
        "endtime": "2013-02-12T03:17:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "fallbacks": [
            {"network": "IU", "station": "MAJO"},
            {"network": "IU", "station": "TATO"},
            {"network": "IU", "station": "YSS"},
            {"network": "II", "station": "KIV"},
        ],
    },
    "nk2016a": {
        "description": "North Korean nuclear test 2016-01-06",
        "starttime": "2016-01-06T01:30:00",
        "endtime": "2016-01-06T01:50:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    "nk2016b": {
        "description": "North Korean nuclear test 2016-09-09",
        "starttime": "2016-09-09T00:30:00",
        "endtime": "2016-09-09T00:50:00",
        "network": "IU",
        "station": "INCN",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    "nk2017": {
        "description": "North Korean nuclear test 2017-09-03",
        "starttime": "2017-09-03T03:30:00",
        "endtime": "2017-09-03T03:50:00",
        "network": "IU",
        "station": "ANMO",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    # Historical earthquakes
    "tohoku2011": {
        "description": "Tohoku-Oki Mw 9.0 earthquake 2011-03-11",
        "starttime": "2011-03-11T05:46:24",
        "endtime": "2011-03-11T06:16:24",
        "network": "IU",
        "station": "MAJO",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    "haiti2010": {
        "description": "Haiti Mw 7.0 earthquake 2010-01-12",
        "starttime": "2010-01-12T21:53:10",
        "endtime": "2010-01-12T22:23:10",
        "network": "IU",
        "station": "SJG",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "fallbacks": [
            {"network": "CU", "station": "SDDR"},
            {"network": "CU", "station": "GRTK"},
            {"network": "CU", "station": "MTDJ"},
            {"network": "IU", "station": "ANMO"},
        ],
    },
    "indian_ocean2004": {
        "description": "Sumatra-Andaman / Indian Ocean Mw 9.1 earthquake and tsunami 2004-12-26",
        "starttime": "2004-12-26T00:58:53",
        "endtime": "2004-12-26T01:58:53",
        "network": "IU",
        "station": "CHTO",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    "spacex_starship_ift4": {
        "description": "SpaceX Starship integrated flight test 4 launch 2024-06-06",
        "starttime": "2024-06-06T12:50:00",
        "endtime": "2024-06-06T13:20:00",
        "network": "IU",
        "station": "ANMO",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "notes": "Best-effort regional broadband waveform near the launch window.",
    },
    "spacex_starship_ift5": {
        "description": "SpaceX Starship integrated flight test 5 launch 2024-10-13",
        "starttime": "2024-10-13T12:25:00",
        "endtime": "2024-10-13T12:55:00",
        "network": "IU",
        "station": "ANMO",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "notes": "Best-effort regional broadband waveform near the launch window.",
    },
    "ariane6_maiden2024": {
        "description": "Ariane 6 maiden flight from Guiana Space Centre 2024-07-09",
        "starttime": "2024-07-09T19:00:00",
        "endtime": "2024-07-09T19:30:00",
        "network": "G",
        "station": "MPG",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "fallbacks": [
            {"network": "G", "station": "FDFM"},
            {"network": "CU", "station": "BBGH"},
            {"network": "CU", "station": "GRGR"},
        ],
        "notes": "Best-effort nearby broadband waveform near the launch window.",
    },
    "ariane5_juice2023": {
        "description": "Ariane 5 VA260 / JUICE launch from Guiana Space Centre 2023-04-14",
        "starttime": "2023-04-14T12:14:36",
        "endtime": "2023-04-14T12:44:36",
        "network": "G",
        "station": "MPG",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "fallbacks": [
            {"network": "G", "station": "FDFM"},
            {"network": "CU", "station": "BBGH"},
            {"network": "CU", "station": "GRGR"},
        ],
        "notes": "Best-effort nearby broadband waveform near the launch window.",
    },
    "eyjafjallajokull2010": {
        "description": "Eyjafjallajokull 2010 explosive eruption phase",
        "starttime": "2010-04-14T00:00:00",
        "endtime": "2010-04-14T02:00:00",
        "network": "II",
        "station": "BORG",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    "hunga_tonga2022": {
        "description": "Hunga Tonga-Hunga Ha'apai eruption and tsunami 2022-01-15",
        "starttime": "2022-01-15T04:14:45",
        "endtime": "2022-01-15T05:14:45",
        "network": "IU",
        "station": "RAR",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    # South Asian nuclear tests
    "pokhran2_1998_05_11": {
        "description": "Pokhran-II / Operation Shakti nuclear tests 1998-05-11",
        "starttime": "1998-05-11T10:15:00",
        "endtime": "1998-05-11T10:35:00",
        "network": "II",
        "station": "NIL",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
    },
    "pokhran2_1998_05_13": {
        "description": "Pokhran-II / Operation Shakti sub-kiloton tests 1998-05-13",
        "starttime": "1998-05-13T06:51:00",
        "endtime": "1998-05-13T07:11:00",
        "network": "II",
        "station": "NIL",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "notes": "Low-yield tests; a visible waveform is not guaranteed.",
    },
    "chagai1_1998_05_28": {
        "description": "Pakistan Chagai-I nuclear tests 1998-05-28",
        "starttime": "1998-05-28T10:16:15",
        "endtime": "1998-05-28T10:36:15",
        "network": "II",
        "station": "NIL",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "fallbacks": [
            {"network": "IU", "station": "CHTO"},
            {"network": "II", "station": "KIV"},
            {"network": "IU", "station": "ANMO"},
        ],
    },
    "chagai2_1998_05_30": {
        "description": "Pakistan Chagai-II nuclear test 1998-05-30",
        "starttime": "1998-05-30T08:10:00",
        "endtime": "1998-05-30T08:30:00",
        "network": "II",
        "station": "NIL",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
        "fallbacks": [
            {"network": "IU", "station": "CHTO"},
            {"network": "II", "station": "KIV"},
            {"network": "IU", "station": "ANMO"},
        ],
        "notes": (
            "The nearby II.NIL request may return no data for this window; "
            "fallback stations are tried automatically."
        ),
    },
    "chile2010": {
        "description": "Maule, Chile Mw 8.8 earthquake 2010-02-27",
        "starttime": "2010-02-27T06:34:00",
        "endtime": "2010-02-27T07:04:00",
        "network": "IU",
        "station": "ANMO",
        "channel": "BHZ",
        "client": "EARTHSCOPE",
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
    client_name: str = "EARTHSCOPE",
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
        FDSN client identifier (e.g. ``"EARTHSCOPE"``, ``"GEOFON"``).
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

    explicit_request = any([network, station, channel, starttime, endtime])

    net = network or preset.get("network")
    sta = station or preset.get("station")
    cha = channel or preset.get("channel")
    t_start = UTCDateTime(starttime) if starttime else UTCDateTime(preset.get("starttime", ""))
    t_end = UTCDateTime(endtime) if endtime else UTCDateTime(preset.get("endtime", ""))
    client_id = preset.get("client", client_name) if not explicit_request else client_name

    missing = [name for name, val in [("network", net), ("station", sta), ("channel", cha)] if not val]
    if missing:
        raise ValueError(
            f"Missing required parameters: {', '.join(missing)}. "
            "Provide them explicitly or use a known event label."
        )

    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    candidates = [{
        "network": net,
        "station": sta,
        "channel": cha,
        "client": client_id,
    }]
    if not explicit_request:
        for fallback in preset.get("fallbacks", []):
            candidates.append({
                "network": fallback.get("network", net),
                "station": fallback.get("station", sta),
                "channel": fallback.get("channel", cha),
                "client": fallback.get("client", client_id),
            })

    failures: list[str] = []

    for candidate in candidates:
        cand_net = candidate["network"]
        cand_sta = candidate["station"]
        cand_cha = candidate["channel"]
        cand_client = candidate["client"]

        stem = f"{event}_{cand_net}_{cand_sta}_{cand_cha}_{t_start.strftime('%Y%m%dT%H%M%S')}"
        out_path = raw_dir / f"{stem}.mseed"

        if out_path.exists():
            logger.info("miniSEED already cached: %s", out_path)
            return out_path.resolve()

        logger.info(
            "Fetching %s %s %s.%s from %s to %s via %s",
            event, cand_cha, cand_net, cand_sta, t_start, t_end, cand_client,
        )

        try:
            client = Client(cand_client)
            stream = client.get_waveforms(
                network=cand_net,
                station=cand_sta,
                location="*",
                channel=cand_cha,
                starttime=t_start,
                endtime=t_end,
            )
        except Exception as exc:
            failures.append(f"{cand_client}:{cand_net}.{cand_sta}.{cand_cha}: {exc}")
            logger.info(
                "Waveform fetch failed for %s via %s:%s.%s.%s: %s",
                event, cand_client, cand_net, cand_sta, cand_cha, exc,
            )
            continue

        stream.write(str(out_path), format="MSEED")
        logger.info("Saved miniSEED → %s", out_path)
        return out_path.resolve()

    raise RuntimeError(
        f"No waveform data could be fetched for {event}. Attempts:\n"
        + "\n".join(f"  - {failure}" for failure in failures)
    )
