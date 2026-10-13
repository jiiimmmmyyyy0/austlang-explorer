"""Analysis behind the Home and Insights screens.

Plain Python (loops, dictionaries and Counter) so every calculation can be
followed step by step and tested.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from statistics import mean, median
from typing import Iterable

from .models import Language

# Groups for the "how many alternative names" chart, in display order.
NAME_COUNT_BUCKETS = ("0", "1", "2", "3", "4", "5-9", "10+")


@dataclass(frozen=True)
class Overview:
    """Headline figures for the Home screen."""

    total: int
    with_location: int
    in_wa: int
    alternative_names: int


def overview(languages: Iterable[Language]) -> Overview:
    languages = list(languages)
    return Overview(
        total=len(languages),
        with_location=sum(1 for language in languages if language.has_location),
        in_wa=sum(1 for language in languages if "WA" in language.regions),
        alternative_names=sum(len(language.alternative_names) for language in languages),
    )


@dataclass(frozen=True)
class GridCell:
    """One square of the density grid and how many varieties fall inside it."""

    south: float  # latitude of the southern edge
    west: float   # longitude of the western edge
    size: float   # width and height in degrees
    count: int

    @property
    def north(self) -> float:
        return self.south + self.size

    @property
    def east(self) -> float:
        return self.west + self.size

    def label(self) -> str:
        """e.g. '30-32°S, 114-116°E'."""
        return f"{abs(self.north):g}-{abs(self.south):g}°S, {self.west:g}-{self.east:g}°E"


def density_grid(languages: Iterable[Language], cell_size: float = 2.0) -> list[GridCell]:
    """Count varieties in a grid of squares `cell_size` degrees wide.

    Each location is turned into a (row, column) pair with floor division, so a
    square includes its southern and western edges. Squares with no varieties
    are left out. Busiest squares come first.
    """
    if isinstance(cell_size, bool) or not isinstance(cell_size, (int, float)) or not cell_size > 0:
        raise ValueError("cell_size must be a number of degrees greater than 0.")
    counts: Counter = Counter()
    for language in languages:
        if language.has_location:
            row = math.floor(language.latitude / cell_size)
            column = math.floor(language.longitude / cell_size)
            counts[(row, column)] += 1
    cells = [
        GridCell(south=row * cell_size, west=column * cell_size, size=cell_size, count=count)
        for (row, column), count in counts.items()
    ]
    cells.sort(key=lambda cell: (-cell.count, -cell.south, cell.west))
    return cells


def cells_needed_for_share(cells: list[GridCell], share: float = 0.5) -> int:
    """How many of the busiest squares hold at least `share` of all mapped varieties.

    A small number means the varieties are concentrated in a few places.
    `cells` must be sorted busiest first, as `density_grid` returns them.
    """
    if not 0 < share <= 1:
        raise ValueError("share must be greater than 0 and at most 1.")
    total = sum(cell.count for cell in cells)
    if total == 0:
        return 0
    running = 0
    for number, cell in enumerate(cells, start=1):
        running += cell.count
        if running >= share * total:
            return number
    return len(cells)


@dataclass(frozen=True)
class StateProfile:
    """Figures for one state or territory."""

    state: str
    varieties: int
    average_alternative_names: float


def state_profiles(languages: Iterable[Language]) -> list[StateProfile]:
    """Number of varieties and average alternative names in each state/territory.

    A variety recorded in two states counts in both, so the counts can add up
    to more than the number of varieties. Largest first.
    """
    groups: dict[str, list[Language]] = defaultdict(list)
    for language in languages:
        for state in language.regions:
            groups[state].append(language)
    profiles = [
        StateProfile(
            state=state,
            varieties=len(members),
            average_alternative_names=mean(len(member.alternative_names) for member in members),
        )
        for state, members in groups.items()
    ]
    profiles.sort(key=lambda profile: (-profile.varieties, profile.state))
    return profiles


@dataclass(frozen=True)
class CrossBorderSummary:
    """How many varieties AUSTLANG records in more than one state or territory."""

    with_state_info: int
    in_several: int

    @property
    def share(self) -> float:
        return self.in_several / self.with_state_info if self.with_state_info else 0.0


def cross_border_summary(languages: Iterable[Language]) -> CrossBorderSummary:
    """Only uses AUSTLANG's own state column (estimates are always a single state)."""
    with_info = [language for language in languages if language.states]
    return CrossBorderSummary(
        with_state_info=len(with_info),
        in_several=sum(1 for language in with_info if len(language.states) > 1),
    )


def name_count_bucket(count: int) -> str:
    """Put a number of alternative names into one of NAME_COUNT_BUCKETS."""
    if count >= 10:
        return "10+"
    if count >= 5:
        return "5-9"
    return str(count)


@dataclass(frozen=True)
class AlternativeNameStats:
    """How many alternative names and spellings the varieties have."""

    total_languages: int
    with_any: int
    mean: float
    median: float
    maximum: int
    distribution: tuple[tuple[str, int], ...]
    most_names: tuple[Language, ...]

    @property
    def share_with_any(self) -> float:
        return self.with_any / self.total_languages if self.total_languages else 0.0


def alternative_name_stats(languages: Iterable[Language], top_n: int = 10) -> AlternativeNameStats:
    """Summary statistics, a grouped distribution and the varieties with the most names."""
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 1:
        raise ValueError("top_n must be a whole number of at least 1.")
    languages = list(languages)
    counts = [len(language.alternative_names) for language in languages]
    if not counts:
        empty = tuple((bucket, 0) for bucket in NAME_COUNT_BUCKETS)
        return AlternativeNameStats(0, 0, 0.0, 0.0, 0, empty, ())

    buckets = Counter(name_count_bucket(count) for count in counts)
    most = sorted(languages, key=lambda language: (-len(language.alternative_names), language.name.casefold()))
    return AlternativeNameStats(
        total_languages=len(languages),
        with_any=sum(1 for count in counts if count > 0),
        mean=mean(counts),
        median=median(counts),
        maximum=max(counts),
        distribution=tuple((bucket, buckets.get(bucket, 0)) for bucket in NAME_COUNT_BUCKETS),
        most_names=tuple(most[:top_n]),
    )
