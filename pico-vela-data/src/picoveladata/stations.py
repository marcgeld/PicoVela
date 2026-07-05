"""Station metadata used by PicoVela data-preparation outputs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    """Human-readable metadata for one seismic observing station."""

    code: str
    network: str
    station: str
    name: str
    country: str
    description: str


STATIONS: dict[str, Station] = {
    "II.NIL": Station(
        code="II.NIL",
        network="II",
        station="NIL",
        name="Nilore",
        country="Pakistan",
        description="Station useful for South Asian nuclear tests",
    ),
    "IU.CHTO": Station(
        code="IU.CHTO",
        network="IU",
        station="CHTO",
        name="Chiang Mai",
        country="Thailand",
        description="Station useful for Indian Ocean events",
    ),
    "II.KIV": Station(
        code="II.KIV",
        network="II",
        station="KIV",
        name="Kislovodsk",
        country="Russia",
        description="Eurasian seismic reference station",
    ),
    "IU.ANMO": Station(
        code="IU.ANMO",
        network="IU",
        station="ANMO",
        name="Albuquerque Seismological Laboratory",
        country="USA",
        description="Classic GSN reference station",
    ),
    "IU.MAJO": Station(
        code="IU.MAJO",
        network="IU",
        station="MAJO",
        name="Matsushiro",
        country="Japan",
        description="Important station for Japanese earthquakes",
    ),
    "IU.RAR": Station(
        code="IU.RAR",
        network="IU",
        station="RAR",
        name="Rarotonga",
        country="Cook Islands",
        description="Useful Pacific monitoring station",
    ),
    "II.BORG": Station(
        code="II.BORG",
        network="II",
        station="BORG",
        name="Borgarfjordur",
        country="Iceland",
        description="Useful for Icelandic volcanic events",
    ),
    "IU.INCN": Station(
        code="IU.INCN",
        network="IU",
        station="INCN",
        name="Incheon",
        country="South Korea",
        description="Useful for North Korean nuclear tests",
    ),
}


def get_station(code: str) -> Station | None:
    """Return station metadata for a ``NETWORK.STATION`` code, if known."""
    return STATIONS.get(code.upper())


def station_name(code: str) -> str:
    """Return the station's display name, or the code for unknown stations."""
    station = get_station(code)
    return station.name if station is not None else code.upper()


def station_country(code: str) -> str:
    """Return the station country, or an empty string for unknown stations."""
    station = get_station(code)
    return station.country if station is not None else ""
