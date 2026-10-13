"""AUSTLANG Explorer: entry point.

Run locally with:   streamlit run app.py
This file only sets up the page and the navigation menu; each screen lives in views/.
"""
import streamlit as st

from ui_common import show_sidebar_notes

st.set_page_config(page_title="AUSTLANG Explorer", page_icon="🗺️", layout="wide")

PAGES = [
    st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("views/search.py", title="Find a language", icon=":material/search:"),
    st.Page("views/nearby.py", title="Languages near a place", icon=":material/near_me:"),
    st.Page("views/insights.py", title="Insights", icon=":material/insights:"),
    st.Page("views/about_data.py", title="About the data", icon=":material/info:"),
]

navigation = st.navigation(PAGES)
show_sidebar_notes()
navigation.run()
