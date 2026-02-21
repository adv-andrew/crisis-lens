"""
CrisisLens — Project Recommender
==================================
Comparable benchmark project search using cosine similarity.
Tries Actian VectorAI first, falls back to sklearn.
"""

import streamlit as st
import pandas as pd
from pathlib import Path


# --- Data loading ---
@st.cache_data(ttl=3600, show_spinner="Loading project data...")
def _load_projects():
    path = Path("data/processed/projects_clean.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=3600, show_spinner="Running outlier detection...")
def _run_outliers(n_projects):
    df = _load_projects()
    if df.empty:
        return pd.DataFrame()
    from utils.outlier_detector import detect_efficiency_outliers
    return detect_efficiency_outliers(df)


df_projects = _load_projects()

if df_projects.empty:
    st.warning("No project data available. Run `python utils/data_loader.py` first.")
    st.stop()

df_outliers = _run_outliers(len(df_projects))

# --- Header ---
st.header("Project Recommender")
st.caption(
    "Select a project to find comparable high-efficiency benchmark projects "
    "from other crisis contexts."
)

# --- Sidebar filters ---
st.sidebar.header("Project Selection")

# Country filter
available_countries = sorted(df_projects["country_iso3"].dropna().unique().tolist())
selected_country = st.sidebar.selectbox("Filter by Country", ["All"] + available_countries)

# Cluster filter
available_clusters = sorted(df_projects["cluster_name"].dropna().unique().tolist())
selected_cluster = st.sidebar.selectbox("Filter by Cluster", ["All"] + available_clusters)

# Filter project list
df_filtered = df_projects.copy()
if selected_country != "All":
    df_filtered = df_filtered[df_filtered["country_iso3"] == selected_country]
if selected_cluster != "All":
    df_filtered = df_filtered[df_filtered["cluster_name"] == selected_cluster]

if df_filtered.empty:
    st.info("No projects match the selected filters.")
    st.stop()

# Number of results
top_n = st.sidebar.slider("Number of results", min_value=3, max_value=10, value=5)

# Project selector
df_filtered = df_filtered.sort_values("budget_usd", ascending=False)
project_options = df_filtered["project_code"].tolist()

# Build display labels
def _project_label(code):
    row = df_filtered[df_filtered["project_code"] == code]
    if row.empty:
        return code
    r = row.iloc[0]
    title = str(r.get("project_title", ""))[:50]
    budget = r.get("budget_usd", 0)
    return f"{code} | ${budget:,.0f} | {title}"


selected_project = st.sidebar.selectbox(
    "Select Project",
    project_options,
    format_func=_project_label,
)

# --- Selected project detail ---
st.markdown("---")
st.subheader("Selected Project")

proj_row = df_projects[df_projects["project_code"] == selected_project]
if not proj_row.empty:
    p = proj_row.iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Country", str(p.get("country_iso3", "N/A")))
    with c2:
        st.metric("Cluster", str(p.get("cluster_name", "N/A")))
    with c3:
        budget = p.get("budget_usd", 0)
        st.metric("Budget", f"${budget:,.0f}" if pd.notna(budget) else "N/A")
    with c4:
        ben = p.get("beneficiaries_total", 0)
        st.metric("Beneficiaries", f"{ben:,.0f}" if pd.notna(ben) else "N/A")

    if pd.notna(p.get("project_title")):
        st.caption(f"**Title:** {p['project_title']}")

    # Outlier flag
    if not df_outliers.empty:
        flag_row = df_outliers[df_outliers["project_code"] == selected_project]
        if not flag_row.empty:
            flag = flag_row.iloc[0].get("efficiency_flag", "unknown")
            z = flag_row.iloc[0].get("zscore_efficiency", float("nan"))
            flag_colors = {
                "high_efficiency": "green",
                "low_efficiency": "red",
                "normal": "gray",
                "insufficient_data": "orange",
            }
            color = flag_colors.get(flag, "gray")
            z_str = f" (z={z:.2f})" if pd.notna(z) else ""
            st.markdown(f"Efficiency flag: :{color}[**{flag}**]{z_str}")

# --- Run recommender ---
st.markdown("---")
st.subheader("Similar Benchmark Projects")

if st.button("Find Similar Projects", type="primary") or "last_recommendations" in st.session_state:
    with st.spinner("Computing similarity..."):
        from utils.similarity_engine import find_similar_projects

        results = find_similar_projects(
            selected_project, df_projects, df_outliers, top_n=top_n
        )

        # Detect backend
        backend = "sklearn cosine similarity"
        try:
            from utils.actian_connector import _check_actian_available
            if _check_actian_available():
                backend = "Actian VectorAI"
        except Exception:
            pass

    st.caption(f"Powered by: **{backend}**")

    if results.empty:
        st.info(
            "No similar benchmark projects found. This may happen if there are "
            "too few high-efficiency projects in the dataset."
        )
    else:
        # Display results
        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True,
            column_config={
                "budget_usd": st.column_config.NumberColumn("Budget (USD)", format="$%,.0f"),
                "beneficiaries_total": st.column_config.NumberColumn("Beneficiaries", format="%,.0f"),
                "efficiency_ratio": st.column_config.NumberColumn("Efficiency", format="%.6f"),
                "similarity_score": st.column_config.ProgressColumn(
                    "Similarity", min_value=0, max_value=1, format="%.3f"
                ),
            },
        )

        # Summary insight
        if len(results) > 0:
            avg_budget = results["budget_usd"].mean()
            avg_ben = results["beneficiaries_total"].mean()
            st.success(
                f"**Benchmarks average:** ${avg_budget:,.0f} budget, "
                f"{avg_ben:,.0f} beneficiaries — "
                f"compare to selected project's ${p.get('budget_usd', 0):,.0f} budget "
                f"and {p.get('beneficiaries_total', 0):,.0f} beneficiaries."
            )
else:
    st.info("Click **Find Similar Projects** to search for comparable benchmarks.")

# --- Methodology ---
with st.expander("How does the recommender work?"):
    st.markdown("""
    Projects are compared using **cosine similarity** on a feature vector that includes:

    - **Cluster type** (one-hot encoded: WASH, Health, Food Security, etc.)
    - **Organization type** (one-hot encoded: INGO, NNGO, UN, etc.)
    - **Budget** (log-scaled, min-max normalized)
    - **Beneficiaries** (log-scaled, min-max normalized)

    Results are filtered to **high-efficiency benchmark projects only** (z-score > 2.0
    within their cluster), so recommendations represent projects that achieved
    strong beneficiary coverage relative to their budget.

    If Actian VectorAI DB is available, the recommender uses vector search for
    faster nearest-neighbor queries. Otherwise, it falls back to scikit-learn
    cosine similarity.
    """)
