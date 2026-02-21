"""
CrisisLens — Efficiency Outliers
=================================
Project-level beneficiary-to-budget analysis.
Flags high-efficiency benchmarks and low-efficiency outliers.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --- Data loading ---
@st.cache_data(ttl=3600, show_spinner="Loading project data...")
def _load_projects():
    path = Path("data/processed/projects_clean.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=3600, show_spinner="Running outlier detection...")
def _run_outliers(projects_hash):
    """Run outlier detection. Hash param forces cache invalidation on data change."""
    df = _load_projects()
    if df.empty:
        return pd.DataFrame()
    from utils.outlier_detector import detect_efficiency_outliers
    return detect_efficiency_outliers(df)


df_projects = _load_projects()

if df_projects.empty:
    st.warning("No project data available. Run `python utils/data_loader.py` first.")
    st.stop()

# Use hash of shape as cache key
df_outliers = _run_outliers(len(df_projects))

if df_outliers.empty:
    st.warning("Outlier detection returned no results.")
    st.stop()

# --- Sidebar filters ---
st.sidebar.header("Outlier Filters")

# Year filter
available_years = sorted(df_outliers["year"].dropna().unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect(
    "Year", available_years, default=available_years[:2] if len(available_years) >= 2 else available_years
)

# Cluster filter
available_clusters = sorted(df_outliers["cluster_name"].dropna().unique().tolist())
selected_clusters = st.sidebar.multiselect("Cluster", available_clusters, default=available_clusters)

# Country filter
available_countries = sorted(df_outliers["country_iso3"].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect("Country", available_countries, default=[])

# Flag filter
flag_options = ["All", "High Efficiency (Benchmarks)", "Low Efficiency", "Normal", "Insufficient Data"]
selected_flag = st.sidebar.radio("Show", flag_options, index=0)

# --- Apply filters ---
df_display = df_outliers.copy()

if selected_years:
    df_display = df_display[df_display["year"].isin(selected_years)]
if selected_clusters:
    df_display = df_display[df_display["cluster_name"].isin(selected_clusters)]
if selected_countries:
    df_display = df_display[df_display["country_iso3"].isin(selected_countries)]

flag_map = {
    "High Efficiency (Benchmarks)": "high_efficiency",
    "Low Efficiency": "low_efficiency",
    "Normal": "normal",
    "Insufficient Data": "insufficient_data",
}
if selected_flag != "All":
    df_display = df_display[df_display["efficiency_flag"] == flag_map[selected_flag]]

# --- Header ---
st.header("Project Efficiency Outlier Analysis")
st.caption("Z-score analysis of beneficiary-to-budget ratios within each cluster")

# --- Summary metrics ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    n_bench = (df_display["efficiency_flag"] == "high_efficiency").sum()
    st.metric("Benchmark Projects", n_bench)
with c2:
    n_low = (df_display["efficiency_flag"] == "low_efficiency").sum()
    st.metric("Low Efficiency", n_low)
with c3:
    n_normal = (df_display["efficiency_flag"] == "normal").sum()
    st.metric("Normal", n_normal)
with c4:
    n_insuf = (df_display["efficiency_flag"] == "insufficient_data").sum()
    st.metric("Insufficient Data", n_insuf)

st.markdown("---")

# --- Scatter plot ---
st.subheader("Budget vs. Beneficiaries")

df_scatter = df_display[
    df_display["budget_usd"].notna()
    & (df_display["budget_usd"] > 0)
    & df_display["beneficiaries_total"].notna()
    & (df_display["beneficiaries_total"] > 0)
].copy()

if not df_scatter.empty:
    color_map = {
        "high_efficiency": "#2ecc71",
        "low_efficiency": "#e74c3c",
        "normal": "#95a5a6",
        "insufficient_data": "#bdc3c7",
    }

    fig_scatter = px.scatter(
        df_scatter,
        x="budget_usd",
        y="beneficiaries_total",
        color="efficiency_flag",
        color_discrete_map=color_map,
        hover_data={
            "project_code": True,
            "country_iso3": True,
            "cluster_name": True,
            "zscore_efficiency": ":.2f",
            "efficiency_flag": True,
        },
        log_x=True,
        log_y=True,
        labels={
            "budget_usd": "Budget (USD, log scale)",
            "beneficiaries_total": "Beneficiaries (log scale)",
            "efficiency_flag": "Flag",
        },
        category_orders={"efficiency_flag": ["high_efficiency", "normal", "low_efficiency", "insufficient_data"]},
    )
    fig_scatter.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.info("No projects with both budget and beneficiary data to plot.")

# --- Data table ---
st.markdown("---")
st.subheader("Project Details")

table_cols = [
    "project_code", "country_iso3", "cluster_name", "year",
    "budget_usd", "beneficiaries_total", "efficiency_ratio",
    "zscore_efficiency", "efficiency_flag", "project_title",
]
df_table = df_display[
    [c for c in table_cols if c in df_display.columns]
].sort_values("zscore_efficiency", ascending=False, na_position="last")

st.dataframe(
    df_table.head(100),
    use_container_width=True,
    hide_index=True,
    column_config={
        "budget_usd": st.column_config.NumberColumn("Budget (USD)", format="$%,.0f"),
        "beneficiaries_total": st.column_config.NumberColumn("Beneficiaries", format="%,.0f"),
        "efficiency_ratio": st.column_config.NumberColumn("Efficiency", format="%.6f"),
        "zscore_efficiency": st.column_config.NumberColumn("Z-Score", format="%.2f"),
    },
)

st.caption(f"Showing {min(100, len(df_table))} of {len(df_table)} projects matching filters.")

# --- Methodology ---
with st.expander("How are outliers detected?"):
    st.markdown("""
    **Efficiency Ratio** = Beneficiaries / Budget (USD)

    Z-scores are computed **within each (cluster, year) group** — a WASH project
    is compared to other WASH projects, not to Food Security projects.

    - **Log-transform** applied before z-score (ratios are right-skewed)
    - **Threshold: |z| > 2.0** flags outliers
    - Groups with fewer than 3 projects are marked "insufficient data"
    - **High efficiency** (z > 2.0): Benchmark projects doing a lot with a little
    - **Low efficiency** (z < -2.0): Worth investigating — could be data quality or genuinely expensive context
    """)
