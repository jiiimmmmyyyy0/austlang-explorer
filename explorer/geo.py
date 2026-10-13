"""Geography: distances, directions, typed coordinates and state estimates."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

from .models import AUSTRALIA_BOUNDS, Language

EARTH_RADIUS_KM = 6371.0  # mean radius of the Earth
MAX_COORDINATE_TEXT = 60  # longest coordinate text we accept from a user

COMPASS_POINTS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")
COMPASS_WORDS = {
    "N": "north", "NE": "north-east", "E": "east", "SE": "south-east",
    "S": "south", "SW": "south-west", "W": "west", "NW": "north-west",
}

# Most state borders are straight lines (129°E, 138°E, 141°E, 26°S, 29°S).
# These two are not, so we trace them with a few (longitude, latitude) points.
QLD_NSW_BORDER = (
    (141.0, -29.0), (148.95, -29.0), (150.3, -28.55), (151.2, -28.85),
    (151.95, -28.95), (152.7, -28.35), (153.55, -28.16),
)
NSW_VIC_BORDER = (
    (141.0, -34.0), (142.2, -34.15), (142.8, -34.55), (143.6, -35.3),
    (144.8, -36.1), (146.9, -36.1), (147.9, -36.05), (148.2, -36.8),
    (150.0, -37.5),
)
TASMANIA_NORTH_EDGE = -39.2  # south of this latitude (east of 141°E) is Tasmania


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Raise ValueError with a helpful message if the coordinates are impossible."""
    for value, label in ((latitude, "Latitude"), (longitude, "Longitude")):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{label} must be a number.")
        if not math.isfinite(value):
            raise ValueError(f"{label} must be a real number.")
    if not -90 <= latitude <= 90:
        raise ValueError(
            "Latitude must be between -90 and 90. Places in Australia have negative latitudes."
        )
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")


def is_in_australia(latitude: float, longitude: float) -> bool:
    """True if the point is inside the box around Australia."""
    bounds = AUSTRALIA_BOUNDS
    return (
        bounds["min_lat"] <= latitude <= bounds["max_lat"]
        and bounds["min_lon"] <= longitude <= bounds["max_lon"]
    )


def parse_coordinates(text: str) -> tuple[float, float]:
    """Read 'latitude, longitude' typed by a user, e.g. '-31.95, 115.86'.

    Accepts a comma, semicolon or spaces between the two numbers and optional
    brackets, which covers what Google Maps copies to the clipboard.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Enter a latitude and longitude, for example -31.95, 115.86.")
    if len(text) > MAX_COORDINATE_TEXT:
        raise ValueError("That is too long to be a pair of coordinates.")
    cleaned = text.strip().strip("()[]").replace("\u2212", "-")  # Unicode minus sign
    parts = [part for part in re.split(r"[,;\s]+", cleaned) if part]
    if len(parts) != 2:
        raise ValueError(
            "Enter exactly two numbers, latitude then longitude, for example -31.95, 115.86."
        )
    try:
        latitude, longitude = float(parts[0]), float(parts[1])
    except ValueError:
        raise ValueError(
            "Coordinates must be decimal numbers, for example -31.95, 115.86 "
            "(not degrees and minutes)."
        ) from None
    validate_coordinates(latitude, longitude)
    return latitude, longitude


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on Earth, in km (haversine formula)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    # min() guards against rounding pushing `a` a hair above 1.
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compass bearing (0-360°, 0 = north) for setting off from point 1 towards point 2."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_lambda = math.radians(lon2 - lon1)
    x = math.sin(d_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def compass_direction(bearing: float) -> str:
    """Turn a bearing into one of eight compass points. Each point covers 45°."""
    index = int(((bearing % 360) + 22.5) // 45) % 8
    return COMPASS_POINTS[index]


@dataclass(frozen=True)
class NearbyResult:
    """One language variety and how far away it is."""

    language: Language
    distance_km: float
    bearing: float

    @property
    def direction(self) -> str:
        return compass_direction(self.bearing)


def nearest_languages(
    latitude: float,
    longitude: float,
    languages: Iterable[Language],
    k: int = 10,
    max_distance_km: float | None = None,
    exclude_code: str | None = None,
) -> list[NearbyResult]:
    """Find the k language varieties closest to a point.

    1. Check the inputs.
    2. Measure the distance from the point to every variety that has a
       location, skipping any beyond max_distance_km.
    3. Sort by distance (ties broken alphabetically) and keep the first k.
    """
    validate_coordinates(latitude, longitude)
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("The number of results must be a whole number of at least 1.")
    if max_distance_km is not None and (
        isinstance(max_distance_km, bool)
        or not isinstance(max_distance_km, (int, float))
        or not max_distance_km > 0
    ):
        raise ValueError("The search distance must be a number greater than 0 km.")

    candidates = []
    for language in languages:
        if not language.has_location or language.code == exclude_code:
            continue
        distance = haversine_km(latitude, longitude, language.latitude, language.longitude)
        if max_distance_km is not None and distance > max_distance_km:
            continue
        candidates.append((distance, language.name.casefold(), language))

    candidates.sort(key=lambda item: (item[0], item[1]))
    return [
        NearbyResult(
            language=language,
            distance_km=distance,
            bearing=initial_bearing(latitude, longitude, language.latitude, language.longitude),
        )
        for distance, _, language in candidates[:k]
    ]


def border_latitude(longitude: float, border: tuple[tuple[float, float], ...]) -> float:
    """Latitude of a traced border at this longitude, by straight-line interpolation."""
    if longitude <= border[0][0]:
        return border[0][1]
    for (lon1, lat1), (lon2, lat2) in zip(border, border[1:]):
        if longitude <= lon2:
            fraction = (longitude - lon1) / (lon2 - lon1)
            return lat1 + fraction * (lat2 - lat1)
    return border[-1][1]


def estimate_state(latitude: float | None, longitude: float | None) -> str | None:
    """Estimate which state or territory a point is in, using simplified borders.

    A few comparisons handle the straight borders; the curved QLD-NSW and
    NSW-VIC borders use `border_latitude`. The ACT is counted with NSW.
    Points close to a border can be placed in the wrong state, which is why
    the app always labels this as an estimate.
    """
    if latitude is None or longitude is None or not is_in_australia(latitude, longitude):
        return None
    if longitude < 129.0:
        return "WA"
    if latitude >= -26.0:
        return "NT" if longitude < 138.0 else "QLD"
    if longitude < 141.0:
        return "SA"
    if latitude >= border_latitude(longitude, QLD_NSW_BORDER):
        return "QLD"
    if latitude < TASMANIA_NORTH_EDGE:
        return "TAS"
    if latitude < border_latitude(longitude, NSW_VIC_BORDER):
        return "VIC"
    return "NSW"
