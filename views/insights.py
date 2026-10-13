"""Insights: patterns across the whole dataset that are hard to see in a table."""
import altair as alt
import pandas as pd
import streamlit as st

from explorer.analysis import (
    alternative_name_stats,
    cells_needed_for_share,
    cross_border_summary,
    density_grid,
    state_profiles,
)
from ui_common import get_data, grid_layer, show_map, state_name

BAR_COLOUR = "#1D5C63"

data = get_data()
languages = data.languages
mapped = sum(1 for language in languages if language.has_location)

st.title("Insights")
st.markdown(
    f"Patterns across all {len(languages):,} AUSTLANG records that are hard to see in a table."
)

# ---- 1. Where varieties are concentrated --------------------------------------------
st.header("Where language varieties are concentrated")
cell_size = st.select_slider(
    "Grid square size",
    options=[1, 2, 3, 5],
    value=2,
    format_func=lambda degrees: f"{degrees}° × {degrees}°",
    help="One degree of latitude is about 111 km.",
)
cells = density_grid(languages, cell_size)
if not cells:
    st.info("No varieties have a location, so the grid can't be drawn.")
else:
    show_map([grid_layer(cells)])
    busiest = cells[0]
    half = cells_needed_for_share(cells, 0.5)
    st.markdown(
        f"Darker squares hold more varieties. The busiest square ({busiest.label()}) holds "
        f"**{busiest.count}** of the {mapped:,} mapped varieties ({busiest.count / mapped:.0%}). "
        f"Half of all mapped varieties sit in just **{half}** of the {len(cells)} squares "
        "that contain any."
    )
    busiest_table = pd.DataFrame(
        [
            {
                "Grid square": cell.label(),
                "Varieties": cell.count,
                "Share of mapped varieties (%)": round(100 * cell.count / mapped, 1),
            }
            for cell in cells[:10]
        ]
    )
    st.dataframe(busiest_table, hide_index=True)

# ---- 2. States and territories ------------------------------------------------------
st.header("Varieties in each state and territory")
profiles = state_profiles(languages)
if not profiles:
    st.info("No state or territory information is available.")
else:
    counts = pd.DataFrame(
        [{"State or territory": state_name(p.state), "Varieties": p.varieties} for p in profiles]
    )
    chart = (
        alt.Chart(counts)
        .mark_bar(color=BAR_COLOUR)
        .encode(
            x=alt.X("Varieties:Q", title="Number of language varieties"),
            y=alt.Y("State or territory:N", sort="-x", title=None),
            tooltip=["State or territory", "Varieties"],
        )
    )
    st.altair_chart(chart)
    if data.report.has_state_column:
        st.caption(
            "States come from AUSTLANG's state_territory field. Where a record has none, the "
            "state is estimated from its coordinates. A variety listed in two states counts in both."
        )
    else:
        st.caption(
            "This data file has no state column, so each state is estimated from the "
            "variety's coordinates using simplified borders. The ACT is counted with NSW."
        )

    crossing = cross_border_summary(languages)
    if crossing.with_state_info:
        st.markdown(
            f"**{crossing.in_several:,}** of the {crossing.with_state_info:,} varieties with "
            f"AUSTLANG state information ({crossing.share:.0%}) are recorded in more than one "
            "state or territory."
        )

    comparison = pd.DataFrame(
        [
            {
                "State or territory": state_name(p.state),
                "Varieties": p.varieties,
                "Share of all varieties (%)": round(100 * p.varieties / len(languages), 1),
                "Average alternative names": round(p.average_alternative_names, 2),
            }
            for p in profiles
        ]
    )
    st.dataframe(comparison, hide_index=True)

# ---- 3. Alternative names and spellings ----------------------------------------------
st.header("How many alternative names each variety has")
stats = alternative_name_stats(languages)
st.markdown(
    f"**{stats.share_with_any:.0%}** of varieties have at least one alternative name or "
    f"spelling recorded. The median is {stats.median:g} and the most for one variety is "
    f"{stats.maximum}. That is why the search screen accepts spelling differences."
)
distribution = pd.DataFrame(
    [{"Alternative names": bucket, "Varieties": number} for bucket, number in stats.distribution]
)
histogram = (
    alt.Chart(distribution)
    .mark_bar(color=BAR_COLOUR)
    .encode(
        x=alt.X(
            "Alternative names:N",
            sort=[bucket for bucket, _ in stats.distribution],
            title="Number of alternative names recorded",
            axis=alt.Axis(labelAngle=0),
        ),
        y=alt.Y("Varieties:Q", title="Number of language varieties"),
        tooltip=["Alternative names", "Varieties"],
    )
)
st.altair_chart(histogram)

st.markdown("**Varieties with the most recorded alternative names**")
most_table = pd.DataFrame(
    [
        {
            "Language variety": language.name,
            "Code": language.code,
            "Alternative names": len(language.alternative_names),
        }
        for language in stats.most_names
    ]
)
st.dataframe(most_table, hide_index=True)
