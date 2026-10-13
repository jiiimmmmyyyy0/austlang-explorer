"""Shared data classes and constants for AUSTLANG Explorer."""
from __future__ import annotations

from dataclasses import dataclass, field

# The project brief requires a dataset with at least 200 records.
MIN_RECORDS = 200

# A box around mainland Australia, Tasmania and the Torres Strait Islands.
# Coordinates outside it are treated as mistakes in the data.
AUSTRALIA_BOUNDS = {
    "min_lat": -44.5,
    "max_lat": -9.0,
    "min_lon": 112.0,
    "max_lon": 154.5,
}

# Standard abbreviations used everywhere in the app, in display order.
STATE_NAMES = {
    "WA": "Western Australia",
    "NT": "Northern Territory",
    "SA": "South Australia",
    "QLD": "Queensland",
    "NSW": "New South Wales",
    "ACT": "Australian Capital Territory",
    "VIC": "Victoria",
    "TAS": "Tasmania",
}


@dataclass(frozen=True)
class Language:
    """One language variety from AUSTLANG, after cleaning."""

    code: str
    name: str
    alternative_names: tuple[str, ...] = ()
    latitude: float | None = None
    longitude: float | None = None
    states: tuple[str, ...] = ()          # from AUSTLANG's state_territory column
    estimated_state: str | None = None    # worked out from the coordinates
    uri: str | None = None

    @property
    def has_location(self) -> bool:
        """True when the variety has a usable approximate location."""
        return self.latitude is not None and self.longitude is not None

    @property
    def regions(self) -> tuple[str, ...]:
        """States/territories used for filtering and counting.

        AUSTLANG's own state_territory values win when the file has them;
        otherwise we fall back to the state estimated from the coordinates.
        """
        if self.states:
            return self.states
        if self.estimated_state:
            return (self.estimated_state,)
        return ()

    @property
    def region_source(self) -> str:
        """Where `regions` came from: 'AUSTLANG', 'estimated' or 'none'."""
        if self.states:
            return "AUSTLANG"
        if self.estimated_state:
            return "estimated"
        return "none"

    def label(self) -> str:
        """Name and code together, for drop-down lists and map tooltips."""
        return f"{self.name} ({self.code})"


@dataclass
class CleaningReport:
    """What happened while the data file was cleaned (shown on the About screen)."""

    source: str
    encoding: str = "utf-8-sig"
    rows_read: int = 0
    rows_kept: int = 0
    missing_code_or_name: int = 0
    duplicate_codes: int = 0
    no_coordinates: int = 0
    invalid_coordinates: int = 0
    alternative_names_found: int = 0
    unsafe_links_removed: int = 0
    has_state_column: bool = False
    columns_used: dict[str, str] = field(default_factory=dict)
    columns_ignored: list[str] = field(default_factory=list)

    @property
    def rows_removed(self) -> int:
        return self.rows_read - self.rows_kept

    @property
    def meets_minimum(self) -> bool:
        """True when enough records survive cleaning (project requirement)."""
        return self.rows_kept >= MIN_RECORDS
