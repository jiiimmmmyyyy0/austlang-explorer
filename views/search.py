"""Find a language: spelling-tolerant search over names and alternative names."""
import pandas as pd
import streamlit as st

from explorer.geo import nearest_languages
from explorer.text_search import MAX_QUERY_LENGTH, SIMILAR, search_languages
from ui_common import (
    TEAL,
    describe_regions,
    escape_markdown,
    get_data,
    marker_layer,
    points_layer,
    show_map,
    state_name,
    state_options,
    zoom_for_distance,
)

TOLERANCE = {"Strict": 0.85, "Balanced": 0.7, "Relaxed": 0.55}
ALL_STATES = "All of Australia"
NEARBY_COUNT = 8
MAX_RESULTS = 50

data = get_data()

st.title("Find a language")
st.markdown(
    "Type a language name, or just part of one. The search also checks every "
    "alternative name and spelling recorded in AUSTLANG, and allows for small "
    "spelling differences."
)

query_column, state_column = st.columns([3, 2])
with query_column:
    query = st.text_input(
        "Language name or spelling", max_chars=MAX_QUERY_LENGTH, placeholder="Type a name"
    )
with state_column:
    state_choice = st.selectbox(
        "State or territory",
        [ALL_STATES] + state_options(data.languages),
        format_func=lambda option: option if option == ALL_STATES else state_name(option),
    )
tolerance = st.select_slider(
    "Spelling tolerance",
    options=list(TOLERANCE),
    value="Balanced",
    help="Strict finds near-identical spellings only. Relaxed also finds spellings "
         "that differ by several letters.",
)

if not query.strip():
    st.info("Start typing a name above. You can search part of a name, such as its first few letters.")
    st.stop()

try:
    results = search_languages(
        query,
        data.index,
        data.by_code,
        min_similarity=TOLERANCE[tolerance],
        max_results=MAX_RESULTS,
        state=None if state_choice == ALL_STATES else state_choice,
    )
except ValueError as error:
    st.warning(str(error))
    st.stop()

place = "" if state_choice == ALL_STATES else f" in {state_name(state_choice)}"
if not results:
    st.info(
        f"No names{place} match “{escape_markdown(query.strip())}”. Try fewer letters, "
        "check the spelling, or set the spelling tolerance to Relaxed."
    )
    st.stop()

noun = "variety" if len(results) == 1 else "varieties"
capped = f" (showing the best {MAX_RESULTS})" if len(results) == MAX_RESULTS else ""
st.success(f"{len(results)} matching language {noun}{place}, best matches first{capped}.")

table = pd.DataFrame(
    [
        {
            "Language variety": result.language.name,
            "Code": result.language.code,
            "Matched spelling": result.matched_spelling
            + ("" if result.matched_main_name else " (alternative name)"),
            "Match": f"{SIMILAR} ({result.similarity:.0%})"
            if result.match_type == SIMILAR else result.match_type,
            "State or territory": describe_regions(result.language),
        }
        for result in results
    ]
)
st.dataframe(table, hide_index=True)

st.subheader("Details")
codes = [result.language.code for result in results]
chosen_code = st.selectbox(
    "Choose a result to see its details",
    codes,
    format_func=lambda code: data.by_code[code].label(),
)
language = data.by_code[chosen_code]

with st.container(border=True):
    st.markdown(f"### {escape_markdown(language.name)}")
    left, right = st.columns(2)
    with left:
        st.markdown(f"**AUSTLANG code:** {escape_markdown(language.code)}")
        st.markdown(f"**State or territory:** {escape_markdown(describe_regions(language))}")
    with right:
        if language.has_location:
            st.markdown(
                f"**Approximate location:** {language.latitude:.3f}, {language.longitude:.3f}"
            )
        else:
            st.markdown("**Approximate location:** not recorded")
        st.markdown(f"**Alternative names recorded:** {len(language.alternative_names)}")
    if language.alternative_names:
        st.markdown(
            "**Alternative names and spellings:** "
            + escape_markdown(", ".join(language.alternative_names))
        )
    if language.uri:
        st.link_button("Open this record on the AUSTLANG website", language.uri)

if not language.has_location:
    st.info("AUSTLANG gives no location for this variety, so it can't be shown on the map.")
    st.stop()

nearby = nearest_languages(
    language.latitude, language.longitude, data.languages,
    k=NEARBY_COUNT, exclude_code=language.code,
)
if not nearby:
    st.info("No other varieties have a recorded location to compare with.")
    st.stop()

st.markdown(f"**The {len(nearby)} closest other recorded varieties**")
nearby_table = pd.DataFrame(
    [
        {
            "Language variety": item.language.name,
            "Code": item.language.code,
            "Distance (km)": round(item.distance_km),
            "Direction": item.direction,
        }
        for item in nearby
    ]
)
st.dataframe(nearby_table, hide_index=True)
show_map(
    [
        points_layer([item.language for item in nearby], TEAL, "nearby-languages"),
        marker_layer(language.latitude, language.longitude, language.label(), "chosen-language"),
    ],
    latitude=language.latitude,
    longitude=language.longitude,
    zoom=zoom_for_distance(nearby[-1].distance_km),
)
st.caption("Gold: the chosen variety. Teal: the closest other varieties. Distances are straight-line.")
