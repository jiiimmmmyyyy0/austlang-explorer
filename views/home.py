"""Home screen: what the app is for, a map of every variety, and where to go next."""
import streamlit as st

from explorer.analysis import overview
from ui_common import TEAL, get_data, points_layer, show_map

data = get_data()
summary = overview(data.languages)

st.title("AUSTLANG Explorer")
st.markdown(
    "Find Aboriginal and Torres Strait Islander languages by name or by place. "
    "Every name and location in this app comes from AUSTLANG, a database of "
    "Indigenous Australian languages published by AIATSIS."
)
st.markdown(
    f"The dataset lists **{summary.total:,}** language varieties. "
    f"**{summary.with_location:,}** have an approximate location, shown below, and "
    f"**{summary.in_wa:,}** are recorded in Western Australia."
)

show_map([points_layer(data.languages, TEAL, "all-languages")])
st.caption(
    "Each dot is the approximate location AUSTLANG gives for one language variety. "
    "Dots are not boundaries. Hover over a dot to see its name and code."
)

st.subheader("Where to start")
search_column, nearby_column, insights_column = st.columns(3)
with search_column:
    st.page_link("views/search.py", label="Find a language", icon=":material/search:")
    st.caption("Search any spelling of a name. Small spelling differences are fine.")
with nearby_column:
    st.page_link("views/nearby.py", label="Languages near a place", icon=":material/near_me:")
    st.caption("Paste coordinates to list the closest recorded varieties.")
with insights_column:
    st.page_link("views/insights.py", label="Insights", icon=":material/insights:")
    st.caption("See where varieties are concentrated and how names vary.")

st.page_link(
    "views/about_data.py",
    label="About the data: source, licence and how it was cleaned",
    icon=":material/info:",
)
