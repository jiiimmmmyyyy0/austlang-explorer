"""Tests for the analysis behind the Home and Insights screens (explorer/analysis.py)."""
import pytest

from explorer.analysis import (
    GridCell,
    alternative_name_stats,
    cells_needed_for_share,
    cross_border_summary,
    density_grid,
    name_count_bucket,
    overview,
    state_profiles,
)
from helpers import make_language


def test_overview_counts(languages):
    summary = overview(languages)
    assert summary.total == 12
    assert summary.with_location == 9
    assert summary.in_wa == 5
    assert summary.alternative_names == 11


def test_density_grid_puts_points_on_edges_in_the_right_square():
    candidates = [
        make_language("A", "A", lat=-32.0, lon=116.0),  # exactly on a corner
        make_language("B", "B", lat=-31.5, lon=117.9),  # same square
        make_language("C", "C", lat=-30.0, lon=116.0),  # on the next square's southern edge
        make_language("D", "D"),                        # no location: ignored
    ]
    cells = density_grid(candidates, cell_size=2.0)
    assert cells == [
        GridCell(south=-32.0, west=116.0, size=2.0, count=2),
        GridCell(south=-30.0, west=116.0, size=2.0, count=1),
    ]


def test_density_grid_counts_every_mapped_variety_once(languages):
    cells = density_grid(languages, cell_size=5)
    assert sum(cell.count for cell in cells) == 9
    counts = [cell.count for cell in cells]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.parametrize("size", [0, -2, "2", True])
def test_density_grid_rejects_a_bad_cell_size(languages, size):
    with pytest.raises(ValueError):
        density_grid(languages, cell_size=size)


def test_grid_cell_label():
    assert GridCell(south=-32.0, west=114.0, size=2.0, count=1).label() == "30-32\u00b0S, 114-116\u00b0E"


def test_cells_needed_for_share():
    cells = [GridCell(0, 0, 1, count) for count in (5, 3, 1, 1)]
    assert cells_needed_for_share(cells, 0.5) == 1  # 5 of 10 is exactly half
    assert cells_needed_for_share(cells, 0.6) == 2
    assert cells_needed_for_share(cells, 1.0) == 4
    assert cells_needed_for_share([], 0.5) == 0
    with pytest.raises(ValueError):
        cells_needed_for_share(cells, 0)


def test_state_profiles(languages):
    profiles = state_profiles(languages)
    assert [(profile.state, profile.varieties) for profile in profiles] == [
        ("WA", 5), ("NSW", 2), ("NT", 1), ("QLD", 1), ("SA", 1), ("TAS", 1), ("VIC", 1),
    ]
    assert profiles[0].average_alternative_names == pytest.approx(7 / 5)


def test_cross_border_summary(languages):
    summary = cross_border_summary(languages)
    assert summary.with_state_info == 10
    assert summary.in_several == 1
    assert summary.share == pytest.approx(0.1)


@pytest.mark.parametrize("count, bucket", [
    (0, "0"), (4, "4"), (5, "5-9"), (9, "5-9"), (10, "10+"), (57, "10+"),
])
def test_name_count_buckets(count, bucket):
    assert name_count_bucket(count) == bucket


def test_alternative_name_stats(languages):
    stats = alternative_name_stats(languages, top_n=3)
    assert stats.total_languages == 12
    assert stats.with_any == 8
    assert stats.mean == pytest.approx(11 / 12)
    assert stats.median == 1
    assert stats.maximum == 3
    assert dict(stats.distribution) == {"0": 4, "1": 6, "2": 1, "3": 1, "4": 0, "5-9": 0, "10+": 0}
    assert stats.most_names[0].code == "TEST01"
    assert len(stats.most_names) == 3


def test_alternative_name_stats_with_no_languages():
    stats = alternative_name_stats([])
    assert stats.total_languages == 0
    assert stats.share_with_any == 0.0
