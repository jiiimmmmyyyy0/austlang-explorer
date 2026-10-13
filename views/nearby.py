"""Languages near a place: the closest recorded varieties to coordinates the user enters."""
import pandas as pd
import streamlit as st

from explorer.geo import (
    COMPASS_WORDS,
    MAX_COORDINATE_TEXT,
    is_in_australia,
    nearest_languages,
    parse_coordinates,
)
from ui_common import (
    TEAL,
    describe_regions,
    escape_markdown,
    get_data,
    marker_layer,
    points_layer,
    show_map,
    zoom_for_distance,
)

DEFAULT_PLACE = "-31.9523, 115.8613"  # Perth CBD
DISTANCE_OPTIONS = [25, 50, 100, 200, 300, 500, 1000, 2000, 5000]

data = get_data()

st.title("Languages near a place")
st.markdown(
    "Enter the coordinates of any place in Australia to list the language varieties "
    "AUSTLANG records closest to it."
)

place_column, count_column = st.columns([3, 2])
with place_column:
    place_text = st.text_input(
        "Coordinates (latitude, longitude)",
        value=DEFAULT_PLACE,
        max_chars=MAX_COORDINATE_TEXT,
        help="In Google Maps, right-click a place and click the numbers at the top of the "
             "menu to copy them. The starting value is Perth's CBD.",
    )
with count_column:
    count = st.slider("Number of varieties to list", min_value=1, max_value=30, value=10)
max_km = st.select_slider(
    "Only include varieties within",
    options=DISTANCE_OPTIONS,
    value=500,
    format_func=lambda km: f"{km:,} km",
)

try:
    latitude, longitude = parse_coordinates(place_text)
except ValueError as error:
    st.error(str(error))
    st.stop()

if not is_in_australia(latitude, longitude):
    st.warning("That point is outside Australia, so the closest varieties may be a long way away.")

place_label = f"Your place ({latitude:.4f}, {longitude:.4f})"
results = nearest_languages(latitude, longitude, data.languages, k=count, max_distance_km=max_km)

if not results:
    st.info(
        f"No varieties with a recorded location are within {max_km:,} km of this point. "
        "Choose a larger distance."
    )
    show_map(
        [marker_layer(latitude, longitude, place_label)],
        latitude=latitude, longitude=longitude, zoom=zoom_for_distance(max_km),
    )
    st.stop()

closest = results[0]
if closest.distance_km < 1:
    where = "less than 1 km from this point"
else:
    where = f"about {closest.distance_km:,.0f} km {COMPASS_WORDS[closest.direction]} of this point"
st.success(f"The closest recorded variety is **{escape_markdown(closest.language.name)}**, {where}.")
if len(results) < count:
    st.caption(f"Only {len(results)} varieties are within {max_km:,} km. Choose a larger distance to see more.")

table = pd.DataFrame(
    [
        {
            "Rank": rank,
            "Language variety": item.language.name,
            "Code": item.language.code,
            "Distance (km)": round(item.distance_km),
            "Direction": item.direction,
            "State or territory": describe_regions(item.language),
        }
        for rank, item in enumerate(results, start=1)
    ]
)
st.dataframe(table, hide_index=True)

show_map(
    [
        points_layer([item.language for item in results], TEAL, "nearby-languages"),
        marker_layer(latitude, longitude, place_label, "your-place"),
    ],
    latitude=latitude,
    longitude=longitude,
    zoom=zoom_for_distance(results[-1].distance_km),
)
st.caption(
    "Gold: your place. Teal: the listed varieties. Distances are straight-line "
    "(great-circle) distances to each variety's approximate point."
)
