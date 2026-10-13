"""Shared building blocks for the Streamlit screens.

Streamlit-specific code (caching, maps, safe text) lives here so the screens in
views/ stay short. The core logic lives in the explorer/ package.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pydeck as pdk
import streamlit as st

from explorer.analysis import GridCell
from explorer.data_loader import load_languages
from explorer.models import MIN_RECORDS, STATE_NAMES, CleaningReport, Language
from explorer.text_search import IndexEntry, build_search_index

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_FILE = PROJECT_ROOT / "data" / "austlang.csv"
SOURCE_INFO_FILE = PROJECT_ROOT / "data" / "austlang_source.json"
DATASET_PAGE = "https://data.gov.au/data/dataset/austlang-dataset-001"
LICENCE_URL = "https://creativecommons.org/licenses/by/4.0/"

# To show UWA's Acknowledgement of Country in the sidebar, paste the official
# wording between the quotes. Copy it from UWA rather than having AI write it.
ACKNOWLEDGEMENT = "The University of Western Australia acknowledges that its Crawley campus is situated on Whadjuk Noongar land, and that the Whadjuk Noongar people remain the spiritual and cultural custodians of their land, and continue to practise their values, languages, beliefs and knowledge."

# Map colours as [red, green, blue, opacity]; they match .streamlit/config.toml.
TEAL = [29, 92, 99, 200]
GOLD = [201, 137, 26, 255]
LIGHT_TEAL = (213, 232, 229)
DARK_TEAL = (16, 64, 70)
AUSTRALIA_VIEW = {"latitude": -26.5, "longitude": 134.0, "zoom": 3.1}

# Characters that Streamlit's Markdown would treat as formatting, links, maths or icons.
_MARKDOWN_SPECIALS = set("\\`*_{}[]()#+-.!|<>~$:")


@dataclass(frozen=True)
class AppData:
    """Everything the screens need, loaded once and shared between them."""

    languages: tuple[Language, ...]
    report: CleaningReport
    index: tuple[IndexEntry, ...]
    by_code: dict[str, Language]


def data_file() -> Path:
    """The CSV to load. Set the AUSTLANG_DATA_FILE environment variable to use another file."""
    return Path(os.environ.get("AUSTLANG_DATA_FILE", DEFAULT_DATA_FILE))


@st.cache_resource(show_spinner="Loading the AUSTLANG data…")
def _load_app_data(path_text: str, modified: float) -> AppData:
    # `modified` is only part of the cache key, so editing the file reloads it.
    languages, report = load_languages(path_text)
    return AppData(
        languages=tuple(languages),
        report=report,
        index=tuple(build_search_index(languages)),
        by_code={language.code: language for language in languages},
    )


def get_data() -> AppData:
    """Load the data (from the cache after the first time) or stop with a clear message."""
    path = data_file()
    if not path.is_file():
        st.error(
            f"The data file `{path.name}` is missing from the `data` folder. "
            "Run `python scripts/download_data.py` (see the README), then refresh this page."
        )
        st.stop()
    try:
        data = _load_app_data(str(path), path.stat().st_mtime)
    except ValueError as error:
        st.error(f"The data file could not be used: {escape_markdown(error)}")
        st.stop()
    if not data.report.meets_minimum:
        st.warning(
            f"Only {data.report.rows_kept} usable records were found. "
            f"The app is designed for at least {MIN_RECORDS}."
        )
    return data


def source_info() -> dict:
    """Download details saved by scripts/download_data.py, or {} if there are none."""
    try:
        info = json.loads(SOURCE_INFO_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return info if isinstance(info, dict) else {}


def escape_markdown(text: object) -> str:
    """Show data exactly as written: stop it being read as formatting, links, maths or icons."""
    return "".join("\\" + char if char in _MARKDOWN_SPECIALS else char for char in str(text))


def state_name(abbreviation: str) -> str:
    return STATE_NAMES.get(abbreviation, abbreviation)


def describe_regions(language: Language) -> str:
    """e.g. 'Western Australia' or 'Queensland (estimated from location)'."""
    if not language.regions:
        return "Not recorded"
    names = ", ".join(state_name(state) for state in language.regions)
    if language.region_source == "estimated":
        return f"{names} (estimated from location)"
    return names


def state_options(languages: Iterable[Language]) -> list[str]:
    """States/territories present in the data, in the usual order, unknown values last."""
    present = {state for language in languages for state in language.regions}
    known = [abbreviation for abbreviation in STATE_NAMES if abbreviation in present]
    return known + sorted(present - set(STATE_NAMES))


def zoom_for_distance(km: float) -> float:
    """A map zoom level that fits points up to `km` away from the centre."""
    for limit, zoom in ((25, 9.0), (75, 8.0), (150, 7.0), (300, 6.0), (600, 5.0), (1200, 4.0)):
        if km <= limit:
            return zoom
    return 3.1


def points_layer(languages: Iterable[Language], colour: list[int], layer_id: str) -> pdk.Layer:
    """A layer of dots, one for each language variety that has a location."""
    records = [
        {"position": [language.longitude, language.latitude], "tooltip": language.label()}
        for language in languages
        if language.has_location
    ]
    return pdk.Layer(
        "ScatterplotLayer",
        id=layer_id,
        data=records,
        get_position="position",
        get_fill_color=colour,
        get_radius=12000,
        radius_min_pixels=3,
        radius_max_pixels=9,
        pickable=True,
    )


def marker_layer(latitude: float, longitude: float, label: str, layer_id: str = "marker") -> pdk.Layer:
    """One highlighted point: the chosen language, or the place the user typed."""
    return pdk.Layer(
        "ScatterplotLayer",
        id=layer_id,
        data=[{"position": [longitude, latitude], "tooltip": label}],
        get_position="position",
        get_fill_color=GOLD,
        get_line_color=[255, 255, 255],
        stroked=True,
        line_width_min_pixels=2,
        get_radius=20000,
        radius_min_pixels=7,
        radius_max_pixels=14,
        pickable=True,
    )


def ramp_colour(count: int, largest: int) -> list[int]:
    """Light teal for few varieties, dark teal for many (square-root scale)."""
    share = math.sqrt(count / largest) if largest > 0 else 0.0
    rgb = [round(low + (high - low) * share) for low, high in zip(LIGHT_TEAL, DARK_TEAL)]
    return rgb + [190]


def grid_layer(cells: list[GridCell]) -> pdk.Layer:
    """Coloured squares for the density grid on the Insights screen."""
    largest = max((cell.count for cell in cells), default=0)
    records = [
        {
            "polygon": [
                [cell.west, cell.south], [cell.east, cell.south],
                [cell.east, cell.north], [cell.west, cell.north],
            ],
            "fill": ramp_colour(cell.count, largest),
            "tooltip": f"{cell.label()}: {cell.count} varieties",
        }
        for cell in cells
    ]
    return pdk.Layer(
        "PolygonLayer",
        id="density-grid",
        data=records,
        get_polygon="polygon",
        get_fill_color="fill",
        get_line_color=[255, 255, 255, 140],
        line_width_min_pixels=1,
        stroked=True,
        filled=True,
        pickable=True,
    )


def show_map(layers: list[pdk.Layer], latitude: float | None = None,
             longitude: float | None = None, zoom: float | None = None) -> None:
    """Draw a map. Tooltips use plain text (not HTML), so data can't inject code."""
    view = pdk.ViewState(
        latitude=AUSTRALIA_VIEW["latitude"] if latitude is None else latitude,
        longitude=AUSTRALIA_VIEW["longitude"] if longitude is None else longitude,
        zoom=AUSTRALIA_VIEW["zoom"] if zoom is None else zoom,
    )
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style=None,  # Streamlit's default basemap, which needs no API key
        tooltip={"text": "{tooltip}"},
    )
    st.pydeck_chart(deck)


def show_sidebar_notes() -> None:
    """Source line (and the Acknowledgement of Country, once added) under the menu."""
    with st.sidebar:
        st.caption(
            "Language data: AUSTLANG, Australian Institute of Aboriginal and Torres Strait "
            "Islander Studies (AIATSIS), CC BY 4.0. Locations are approximate."
        )
        if ACKNOWLEDGEMENT:
            st.caption(ACKNOWLEDGEMENT)
