"""Tests for distances, coordinates and the nearest-language search (explorer/geo.py)."""
import pytest

from explorer.geo import (
    compass_direction,
    estimate_state,
    haversine_km,
    initial_bearing,
    is_in_australia,
    nearest_languages,
    parse_coordinates,
)
from helpers import make_language


# ---- Distance and direction ------------------------------------------------------------

def test_haversine_one_degree_along_the_equator():
    assert haversine_km(0, 0, 0, 1) == pytest.approx(111.195, abs=0.01)


def test_haversine_perth_to_sydney():
    assert haversine_km(-31.95, 115.86, -33.87, 151.21) == pytest.approx(3290.7, abs=1)


def test_haversine_zero_distance_and_symmetry():
    assert haversine_km(-31.95, 115.86, -31.95, 115.86) == 0
    there = haversine_km(-31.95, 115.86, -17.96, 122.24)
    back = haversine_km(-17.96, 122.24, -31.95, 115.86)
    assert there == pytest.approx(back)


@pytest.mark.parametrize("end, bearing, point", [
    ((1, 0), 0, "N"),
    ((0, 1), 90, "E"),
    ((-1, 0), 180, "S"),
    ((0, -1), 270, "W"),
])
def test_bearing_and_compass_point(end, bearing, point):
    result = initial_bearing(0, 0, *end)
    assert result == pytest.approx(bearing)
    assert compass_direction(result) == point


@pytest.mark.parametrize("bearing, point", [
    (22.49, "N"), (22.5, "NE"), (359.9, "N"), (-45, "NW"), (405, "NE"),
])
def test_compass_boundaries(bearing, point):
    assert compass_direction(bearing) == point


# ---- Reading coordinates typed by a user --------------------------------------------

@pytest.mark.parametrize("text", [
    "-31.95, 115.86",
    "-31.95,115.86",
    "-31.95 115.86",
    "(-31.95, 115.86)",
    "\u221231.95; 115.86",
])
def test_parse_coordinates_accepts_common_formats(text):
    assert parse_coordinates(text) == (-31.95, 115.86)


@pytest.mark.parametrize("text", [
    "", "   ", "Perth", "-31.95", "1, 2, 3", "-95, 115", "-31, 200", "nan, 115",
    "31\u00b057\u2032S 115\u00b051\u2032E", "x" * 61,
])
def test_parse_coordinates_rejects_bad_input(text):
    with pytest.raises(ValueError):
        parse_coordinates(text)


# ---- Estimating the state from coordinates ---------------------------------------------

@pytest.mark.parametrize("lat, lon, state", [
    (-31.95, 115.86, "WA"),   # Perth
    (-12.46, 130.84, "NT"),   # Darwin
    (-34.93, 138.60, "SA"),   # Adelaide
    (-27.47, 153.03, "QLD"),  # Brisbane
    (-10.58, 142.22, "QLD"),  # Thursday Island, Torres Strait
    (-33.87, 151.21, "NSW"),  # Sydney
    (-35.28, 149.13, "NSW"),  # Canberra (the ACT is counted with NSW)
    (-37.81, 144.96, "VIC"),  # Melbourne
    (-42.88, 147.33, "TAS"),  # Hobart
])
def test_estimate_state_for_capital_cities(lat, lon, state):
    assert estimate_state(lat, lon) == state


def test_estimate_state_on_the_129_degree_border():
    assert estimate_state(-30.0, 128.99) == "WA"
    assert estimate_state(-30.0, 129.0) == "SA"


def test_estimate_state_outside_australia_or_missing():
    assert estimate_state(0.0, 0.0) is None
    assert estimate_state(None, None) is None


def test_is_in_australia():
    assert is_in_australia(-31.95, 115.86)
    assert not is_in_australia(0, 0)


# ---- Nearest-language search (the second core algorithm) ------------------------------

def test_nearest_languages_are_sorted_by_distance(languages):
    results = nearest_languages(-31.95, 115.86, languages, k=3)
    assert [result.language.code for result in results] == ["TEST01", "TEST15", "TEST02"]
    distances = [result.distance_km for result in results]
    assert distances == sorted(distances)
    assert results[0].distance_km == pytest.approx(0)
    assert results[1].direction == "N"


def test_nearest_languages_can_exclude_the_starting_language(languages):
    results = nearest_languages(-31.95, 115.86, languages, k=1, exclude_code="TEST01")
    assert results[0].language.code == "TEST15"


def test_nearest_languages_respects_the_distance_limit(languages):
    results = nearest_languages(-31.95, 115.86, languages, k=10, max_distance_km=100)
    assert [result.language.code for result in results] == ["TEST01"]


def test_nearest_languages_skips_varieties_without_a_location(languages):
    results = nearest_languages(-31.95, 115.86, languages, k=100)
    assert len(results) == 9  # 12 varieties kept, 3 have no location
    assert all(result.language.has_location for result in results)


def test_ties_are_broken_alphabetically():
    candidates = [make_language("B", "Bravo", -30, 120), make_language("A", "Alpha", -30, 120)]
    results = nearest_languages(-31, 120, candidates, k=2)
    assert [result.language.name for result in results] == ["Alpha", "Bravo"]


def test_empty_dataset_gives_an_empty_result():
    assert nearest_languages(-31.95, 115.86, [], k=5) == []


@pytest.mark.parametrize("settings", [
    {"k": 0}, {"k": -1}, {"k": 2.5}, {"k": True},
    {"max_distance_km": 0}, {"max_distance_km": -5},
])
def test_nearest_languages_rejects_bad_settings(languages, settings):
    with pytest.raises(ValueError):
        nearest_languages(-31.95, 115.86, languages, **settings)


@pytest.mark.parametrize("lat, lon", [(95, 115), (-31, 181), (float("nan"), 115), ("-31", 115)])
def test_nearest_languages_rejects_bad_coordinates(languages, lat, lon):
    with pytest.raises(ValueError):
        nearest_languages(lat, lon, languages)
