"""
CrisisLens — Overlooked Crisis Index
=====================================
Streamlit entry point. Sets page config (the ONLY place this is called),
initializes session state, and renders the home/landing view.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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

# --- Headline insight stat ---
latest_year = df_oci["year"].max()
df_latest = df_oci[df_oci["year"] == latest_year].copy()
if df_latest.empty:
    df_latest = df_oci.copy()

# Compute the funding mismatch headline
df_with_funding = df_latest[
    df_latest["funding_usd_m"].notna() & df_latest["requirements_usd_m"].notna()
].copy()

if not df_with_funding.empty:
    median_gap = df_with_funding["funding_gap"].median()
    well_funded = df_with_funding[df_with_funding["funding_gap"] < median_gap]
    underfunded = df_with_funding[df_with_funding["funding_gap"] >= median_gap]

    well_funded_total = well_funded["funding_usd_m"].sum()
    underfunded_total = underfunded["funding_usd_m"].sum()
    underfunded_pin = underfunded["people_in_need_k"].sum() / 1000
    underfunded_gap_avg = underfunded["funding_gap"].mean()

    st.markdown(
        f"> **The Funding Mismatch:** In {int(latest_year)}, "
        f"**${well_funded_total:,.0f}M** went to crises below the median funding gap, "
        f"while **{underfunded_pin:.0f}M people** in the most underfunded crises "
        f"received only **${underfunded_total:,.0f}M** "
        f"(average {underfunded_gap_avg * 100:.0f}% unfunded)."
    )
    st.markdown("")

# --- Top 5 Most Overlooked Crises ---
st.subheader("Top 5 Most Overlooked Crises")

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
        media = row.get("media_score", float("nan"))

        st.metric(
            label=str(country),
            value=f"OCI: {oci:.3f}",
            delta=f"{gap * 100:.0f}% gap" if pd.notna(gap) else "No data",
            delta_color="inverse",
        )
        if pd.notna(pin) and pin > 0:
            pin_m = pin / 1000
            st.caption(f"{pin_m:.1f}M people in need")
        if pd.notna(media) and media > 0:
            attention = (1 - media) * 100
            st.caption(f"Media attention: {attention:.0f}%")

st.markdown("---")

# --- Quick stats ---
col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.metric("Total Crises Tracked", len(df_latest))
with col_b:
    total_pin = df_latest["people_in_need_k"].sum() / 1000
    st.metric("Total People in Need", f"{total_pin:.0f}M")
with col_c:
    avg_gap = df_latest["funding_gap"].mean()
    st.metric("Average Funding Gap", f"{avg_gap * 100:.0f}%" if pd.notna(avg_gap) else "N/A")
with col_d:
    if "media_score" in df_latest.columns:
        high_neglect = (df_latest["media_score"] > 0.7).sum()
        st.metric("Low-Attention Crises", high_neglect)

st.markdown("---")

# --- Funding Reallocation Simulator ---
st.subheader("Funding Reallocation Simulator")
st.caption(
    "What if new funding were distributed proportionally to OCI scores? "
    "Drag the slider to see how additional funding could reduce neglect."
)

new_funding = st.slider(
    "Additional funding to redistribute ($M USD)",
    min_value=0, max_value=2000, value=500, step=50,
)

if new_funding > 0 and not df_latest.empty:
    df_sim = df_latest[
        df_latest["oci_score"].notna()
        & (df_latest["oci_score"] > 0)
        & df_latest["requirements_usd_m"].notna()
    ].copy()

    if not df_sim.empty:
        # Allocate proportionally to OCI score
        total_oci = df_sim["oci_score"].sum()
        df_sim["allocation_usd_m"] = (df_sim["oci_score"] / total_oci) * new_funding

        # Compute new funding gap
        df_sim["new_funding_usd_m"] = df_sim["funding_usd_m"].fillna(0) + df_sim["allocation_usd_m"]
        df_sim["new_gap"] = np.where(
            df_sim["requirements_usd_m"] > 0,
            1 - (df_sim["new_funding_usd_m"] / df_sim["requirements_usd_m"]),
            df_sim["funding_gap"],
        )
        df_sim["new_gap"] = df_sim["new_gap"].clip(0, 1)
        df_sim["gap_reduction"] = df_sim["funding_gap"] - df_sim["new_gap"]

        # Show top beneficiaries
        top_alloc = df_sim.nlargest(8, "allocation_usd_m")

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Bar(
            x=top_alloc["country_name"].fillna(top_alloc["country_iso3"]),
            y=top_alloc["funding_gap"] * 100,
            name="Current Gap",
            marker_color="#e74c3c",
            opacity=0.6,
        ))
        fig_sim.add_trace(go.Bar(
            x=top_alloc["country_name"].fillna(top_alloc["country_iso3"]),
            y=top_alloc["new_gap"] * 100,
            name="After Reallocation",
            marker_color="#2ecc71",
            opacity=0.8,
        ))
        fig_sim.update_layout(
            barmode="group",
            yaxis=dict(title="Funding Gap %", range=[0, 105]),
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_sim, use_container_width=True)

        avg_old_gap = df_sim["funding_gap"].mean()
        avg_new_gap = df_sim["new_gap"].mean()
        st.success(
            f"Redistributing **${new_funding:,}M** by OCI score would reduce the "
            f"average funding gap from **{avg_old_gap * 100:.0f}%** to "
            f"**{avg_new_gap * 100:.0f}%** across tracked crises."
        )

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
    The Overlooked Crisis Index combines four components:

    ```
    OCI = (PIN_normalized x Severity_weight x Funding_gap) x (1 + Media_score x 0.2)
    ```

    - **PIN Normalized** = People in Need / Total Population (0-1)
    - **Severity Weight** = Derived OCHA severity / 5.0 (0-1), based on crisis intensity
    - **Funding Gap** = 1 - (Actual Funding / Total Requirements) (0-1)
    - **Media Score** = 1 - Normalized Google Trends interest (0-1, higher = less coverage)

    The media multiplier boosts the OCI for crises that receive little public attention,
    amplifying the "overlooked" signal. A crisis can be severely underfunded *and*
    invisible in global media — those are the ones CrisisLens is designed to surface.

    The raw OCI is then min-max normalized across all crises to produce a final
    score between 0 (well-addressed) and 1 (most overlooked).

    **Data sources:** OCHA HNO, FTS, COD-PS Population, CBPF Pooled Funds, Google Trends
    """)
