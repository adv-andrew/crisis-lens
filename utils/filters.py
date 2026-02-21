"""
CrisisLens Shared Sidebar Filters
==================================
Consistent filter widgets used across all Streamlit pages.
"""

import pandas as pd
import streamlit as st


def render_year_filter(df: pd.DataFrame, default_latest: bool = True) -> list:
    """Render year multiselect in sidebar. Returns list of selected years."""
    if "year" not in df.columns or df["year"].dropna().empty:
        return []
    years = sorted(df["year"].dropna().unique().tolist(), reverse=True)
    default = [years[0]] if default_latest and years else years
    return st.sidebar.multiselect("Year", years, default=default, key="filter_year")


def render_country_filter(df: pd.DataFrame, label: str = "Country") -> str | None:
    """Render country selectbox in sidebar, pre-selected from session state."""
    if "country_iso3" not in df.columns or df.empty:
        return None
    all_iso3 = sorted(df["country_iso3"].dropna().unique().tolist())
    if not all_iso3:
        return None

    preselected = st.session_state.get("selected_iso3")
    idx = all_iso3.index(preselected) if preselected and preselected in all_iso3 else 0

    # Build display labels
    if "country_name" in df.columns:
        name_map = (
            df.dropna(subset=["country_name"])
            .drop_duplicates("country_iso3")
            .set_index("country_iso3")["country_name"]
            .to_dict()
        )
        def format_func(iso3):
            return f"{name_map.get(iso3, iso3)} ({iso3})"
    else:
        def format_func(iso3):
            return iso3

    selected = st.sidebar.selectbox(label, all_iso3, index=idx, format_func=format_func)
    st.session_state["selected_iso3"] = selected
    return selected


def render_cluster_filter(df: pd.DataFrame) -> list:
    """Render cluster multiselect in sidebar. Returns list of selected clusters."""
    if "cluster_name" not in df.columns or df.empty:
        return []
    clusters = sorted(df["cluster_name"].dropna().unique().tolist())
    return st.sidebar.multiselect("Cluster", clusters, default=clusters, key="filter_cluster")
