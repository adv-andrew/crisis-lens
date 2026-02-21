"""
CrisisLens — Overlooked Crisis Index
=====================================
Streamlit entry point. Sets page config (the ONLY place this is called),
initializes session state, and renders the home/landing view.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="CrisisLens — Overlooked Crisis Index",
    page_icon=":earth_americas:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "selected_iso3" not in st.session_state:
    st.session_state["selected_iso3"] = None


# --- Data loading ---
@st.cache_data(ttl=3600, show_spinner="Loading OCI scores...")
def _load_oci():
    path = Path("data/processed/oci_scores.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


df_oci = _load_oci()

# --- Header ---
st.title("CrisisLens")
st.markdown(
    "**The Overlooked Crisis Index (OCI)** — surfacing the humanitarian crises "
    "the world is missing. Built for the Databricks x United Nations Geo-Insight Challenge."
)
st.markdown("---")

# --- Empty state ---
if df_oci.empty:
    st.warning("No processed data found.")
    st.info(
        "Run the data pipeline first:\n\n"
        "```bash\npython utils/data_loader.py\n```\n\n"
        "This downloads all UN datasets, computes OCI scores, and saves results to `data/processed/`."
    )
    st.stop()

# --- Top 5 Most Overlooked Crises ---
st.subheader("Top 5 Most Overlooked Crises")

# Get most recent year per country, then rank
latest_year = df_oci["year"].max()
df_latest = df_oci[df_oci["year"] == latest_year].copy()
if df_latest.empty:
    df_latest = df_oci.copy()

top5 = (
    df_latest.sort_values("oci_score", ascending=False)
    .drop_duplicates("country_iso3")
    .head(5)
)

cols = st.columns(5)
for i, (_, row) in enumerate(top5.iterrows()):
    with cols[i]:
        country = row.get("country_name") or row["country_iso3"]
        oci = row["oci_score"]
        gap = row.get("funding_gap", float("nan"))
        pin = row.get("people_in_need_k", float("nan"))

        st.metric(
            label=str(country),
            value=f"OCI: {oci:.3f}",
            delta=f"{gap * 100:.0f}% gap" if pd.notna(gap) else "No data",
            delta_color="inverse",
        )
        if pd.notna(pin) and pin > 0:
            pin_m = pin / 1000
            st.caption(f"{pin_m:.1f}M people in need")

st.markdown("---")

# --- Quick stats ---
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Total Crises Tracked", len(df_latest))
with col_b:
    total_pin = df_latest["people_in_need_k"].sum() / 1000
    st.metric("Total People in Need", f"{total_pin:.0f}M")
with col_c:
    avg_gap = df_latest["funding_gap"].mean()
    st.metric("Average Funding Gap", f"{avg_gap * 100:.0f}%" if pd.notna(avg_gap) else "N/A")

st.markdown("---")

# --- How to use ---
st.markdown("""
### How to Use CrisisLens

1. **Overview Map** — See the OCI choropleth for all crises. Click a country to select it.
2. **Crisis Drilldown** — Deep-dive into a selected country's cluster-level funding gaps.
3. **Efficiency Outliers** — Find projects doing more with less (and vice versa).
4. **Project Recommender** — Surface comparable benchmark projects for any selected project.
5. **Funding Forecast** — Identify crises trending toward being forgotten.

Use the **sidebar** to navigate between pages.
""")

# --- Methodology ---
with st.expander("How is the OCI calculated?"):
    st.markdown("""
    The Overlooked Crisis Index combines three components:

    ```
    OCI = PIN_normalized x Severity_weight x Funding_gap
    ```

    - **PIN Normalized** = People in Need / Total Population (0-1)
    - **Severity Weight** = OCHA severity classification / 5.0 (0-1)
    - **Funding Gap** = 1 - (Actual Funding / Total Requirements) (0-1)

    The raw OCI is then min-max normalized across all crises to produce a final
    score between 0 (well-addressed) and 1 (most overlooked).

    **Data sources:** OCHA HNO, FTS, COD-PS Population, CBPF Pooled Funds
    """)
