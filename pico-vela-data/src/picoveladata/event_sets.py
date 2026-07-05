"""Curated event groups for PicoVela waveform collection."""

from __future__ import annotations

from picoveladata.fetch import KNOWN_EVENTS


ALL_EVENTS: tuple[str, ...] = tuple(KNOWN_EVENTS)

REQUESTED_EVENTS: tuple[str, ...] = (
    "tohoku2011",
    "haiti2010",
    "indian_ocean2004",
    "spacex_starship_ift4",
    "spacex_starship_ift5",
    "ariane6_maiden2024",
    "ariane5_juice2023",
    "eyjafjallajokull2010",
    "hunga_tonga2022",
    "nk2006",
    "nk2009",
    "nk2013",
    "nk2016a",
    "nk2016b",
    "nk2017",
    "pokhran2_1998_05_11",
    "pokhran2_1998_05_13",
    "chagai1_1998_05_28",
    "chagai2_1998_05_30",
)

EARTHQUAKE_EVENTS: tuple[str, ...] = (
    "tohoku2011",
    "haiti2010",
    "indian_ocean2004",
    "chile2010",
)

VOLCANIC_EVENTS: tuple[str, ...] = (
    "eyjafjallajokull2010",
    "hunga_tonga2022",
)

LAUNCH_EVENTS: tuple[str, ...] = (
    "spacex_starship_ift4",
    "spacex_starship_ift5",
    "ariane6_maiden2024",
    "ariane5_juice2023",
)

NORTH_KOREAN_NUCLEAR_TEST_EVENTS: tuple[str, ...] = (
    "nk2006",
    "nk2009",
    "nk2013",
    "nk2016a",
    "nk2016b",
    "nk2017",
)

NUCLEAR_TEST_EVENTS: tuple[str, ...] = (
    *NORTH_KOREAN_NUCLEAR_TEST_EVENTS,
    "pokhran2_1998_05_11",
    "pokhran2_1998_05_13",
    "chagai1_1998_05_28",
    "chagai2_1998_05_30",
)

EVENT_GROUPS: dict[str, tuple[str, ...]] = {
    "all": ALL_EVENTS,
    "requested": REQUESTED_EVENTS,
    "earthquakes": EARTHQUAKE_EVENTS,
    "volcanic": VOLCANIC_EVENTS,
    "launches": LAUNCH_EVENTS,
    "north_korea": NORTH_KOREAN_NUCLEAR_TEST_EVENTS,
    "nuclear": NUCLEAR_TEST_EVENTS,
}


def event_type(event: str) -> str:
    """Return the broad PicoVela event type for an event label."""
    if event in NUCLEAR_TEST_EVENTS:
        return "nuclear"
    if event in EARTHQUAKE_EVENTS:
        return "earthquake"
    if event in VOLCANIC_EVENTS:
        return "volcanic"
    if event in LAUNCH_EVENTS:
        return "launch"
    return "event"
