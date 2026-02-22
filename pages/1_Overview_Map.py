"""
CrisisLens — Overview Map
=========================
OCI choropleth world map with country click drill-down.
Primary entry point for the visual experience.
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --- Data loading ---
@st.cache_data(ttl=3600, show_spinner="Loading OCI scores...")
def _load_oci():
    path = Path("data/processed/oci_scores.csv")
    if not path.exists():
        st.warning("Dataset unavailable — run `python utils/data_loader.py` first.")
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=3600, show_spinner="Loading cluster data...")
def _load_cluster():
    from utils.data_loader import load_fts_cluster
    try:
        return load_fts_cluster()
    except Exception:
        return pd.DataFrame()


df_oci = _load_oci()

if df_oci.empty:
    st.warning("No data available. Run `python utils/data_loader.py` first.")
    st.stop()

# Initialize session state
if "selected_iso3" not in st.session_state:
    st.session_state["selected_iso3"] = None

# --- Sidebar filters ---
st.sidebar.header("Map Controls")

available_years = sorted(df_oci["year"].dropna().unique().tolist(), reverse=True)
selected_years = st.sidebar.multiselect(
    "Year", available_years, default=[available_years[0]] if available_years else []
)

map_layers = ["OCI Score", "Funding Gap %", "People in Need (M)"]
if "media_score" in df_oci.columns:
    map_layers.append("Media Neglect")
map_mode = st.sidebar.radio("Map Layer", map_layers, index=0)

# --- Filter and deduplicate ---
if selected_years:
    df_filtered = df_oci[df_oci["year"].isin(selected_years)].copy()
else:
    df_filtered = df_oci.copy()

# For multi-year selection, keep latest year per country
df_filtered = (
    df_filtered.sort_values("year", ascending=False)
    .drop_duplicates("country_iso3")
    .copy()
)

# Ensure hover name column exists
df_filtered["display_name"] = df_filtered["country_name"].fillna(df_filtered["country_iso3"])

# --- Build choropleth ---
st.header("Overlooked Crisis Index — World Map")

# Prepare color column based on mode
if map_mode == "OCI Score":
    color_col = "oci_score"
    color_scale = [[0, "#2ecc71"], [0.35, "#f39c12"], [0.65, "#e74c3c"], [1, "#8e0000"]]
    color_label = "OCI Score"
    range_color = (0, 1)
elif map_mode == "Funding Gap %":
    color_col = "funding_gap"
    color_scale = "OrRd"
    color_label = "Funding Gap"
    range_color = (0, 1)
elif map_mode == "People in Need (M)":
    df_filtered["people_in_need_m"] = df_filtered["people_in_need_k"] / 1000
    color_col = "people_in_need_m"
    color_scale = "Blues"
    color_label = "People in Need (M)"
    range_color = None
else:  # Media Neglect
    color_col = "media_score"
    color_scale = [[0, "#2ecc71"], [0.5, "#f39c12"], [1, "#8e0000"]]
    color_label = "Media Neglect Score"
    range_color = (0, 1)

fig = px.choropleth(
    df_filtered,
    locations="country_iso3",
    locationmode="ISO-3",
    color=color_col,
    color_continuous_scale=color_scale,
    range_color=range_color,
    hover_name="display_name",
    hover_data={
        "country_iso3": True,
        "oci_score": ":.3f",
        "funding_gap": ":.1%",
        "people_in_need_k": ":,.0f",
        "media_score": ":.2f" if "media_score" in df_filtered.columns else False,
        "display_name": False,
    },
    labels={
        color_col: color_label,
        "oci_score": "OCI Score",
        "funding_gap": "Funding Gap",
        "people_in_need_k": "People in Need (k)",
        "media_score": "Media Neglect",
        "country_iso3": "ISO3",
    },
)

fig.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    height=550,
    geo=dict(
        showframe=False,
        showcoastlines=True,
        coastlinecolor="rgba(150,150,150,0.5)",
        projection_type="natural earth",
        bgcolor="rgba(0,0,0,0)",
    ),
    coloraxis_colorbar=dict(
        title=color_label,
        thickness=15,
        len=0.6,
    ),
)

# --- Render map with click events ---
event = st.plotly_chart(
    fig,
    use_container_width=True,
    key="oci_map",
    on_select="rerun",
    selection_mode="points",
)

# Handle map click
if event and event.selection and event.selection.points:
    point = event.selection.points[0]
    iso3 = point.get("location")
    if iso3:
        st.session_state["selected_iso3"] = iso3

# --- Clear selection button ---
col_clear, col_spacer = st.columns([1, 5])
with col_clear:
    if st.button("Clear selection"):
        st.session_state["selected_iso3"] = None
        st.rerun()

# --- Selected country detail panel ---
selected = st.session_state.get("selected_iso3")

if selected:
    row = df_filtered[df_filtered["country_iso3"] == selected]
    if row.empty:
        row = df_oci[df_oci["country_iso3"] == selected].sort_values("year", ascending=False)

    if not row.empty:
        r = row.iloc[0]
        country_name = r.get("country_name") or selected

        st.markdown("---")
        st.subheader(f"{country_name} ({selected})")

        # --- Quick Crisis Brief ---
        pin_m = r.get("people_in_need_k", 0) / 1000 if pd.notna(r.get("people_in_need_k")) else 0
        gap_pct = r.get("funding_gap", 0) * 100 if pd.notna(r.get("funding_gap")) else 0
        media = r.get("media_score", 0) if pd.notna(r.get("media_score")) else 0
        req = r.get("requirements_usd_m", 0) if pd.notna(r.get("requirements_usd_m")) else 0
        fund = r.get("funding_usd_m", 0) if pd.notna(r.get("funding_usd_m")) else 0

        if media > 0.8:
            media_desc = "virtually no global media attention"
        elif media > 0.6:
            media_desc = "minimal media coverage"
        elif media > 0.4:
            media_desc = "below-average media visibility"
        else:
            media_desc = "moderate-to-high media coverage"

        brief = (
            f"**{country_name}** has **{pin_m:.1f}M people** in need. "
            f"Only **${fund:,.0f}M** of the **${req:,.0f}M** required has been funded "
            f"({gap_pct:.0f}% gap). The crisis receives {media_desc}."
        )
        st.markdown(
            f'<div style="border-left:3px solid #cd3a1f;padding:8px 14px;'
            f'margin-bottom:12px;font-size:13px;line-height:1.6;'
            f'background:#ffffff;border:1px solid #d4d4d4;border-left:3px solid #cd3a1f;'
            f'border-radius:0 4px 4px 0;box-shadow:0 1px 2px rgba(0,0,0,0.04);color:#4a4a4a">'
            f'{brief}</div>',
            unsafe_allow_html=True,
        )

        # KPI metrics
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("OCI Score", f"{r['oci_score']:.3f}",
                       f"Rank #{int(r.get('oci_rank', 0))}" if pd.notna(r.get('oci_rank')) else None)
        with c2:
            gap = r.get("funding_gap", float("nan"))
            st.metric("Funding Gap", f"{gap * 100:.0f}%" if pd.notna(gap) else "N/A")
        with c3:
            pin_m = r.get("people_in_need_k", 0) / 1000
            st.metric("People in Need", f"{pin_m:.1f}M")
        with c4:
            req = r.get("requirements_usd_m", float("nan"))
            fund = r.get("funding_usd_m", float("nan"))
            if pd.notna(req) and pd.notna(fund):
                st.metric("Funding", f"${fund:.0f}M / ${req:.0f}M")
            else:
                st.metric("Funding", "No data")

        # Cluster breakdown
        df_cluster = _load_cluster()
        if not df_cluster.empty:
            year_filter = selected_years if selected_years else available_years
            df_c = df_cluster[
                (df_cluster["country_iso3"] == selected)
                & (df_cluster["year"].isin(year_filter))
            ].copy()

            if not df_c.empty:
                # Deduplicate clusters (take latest year)
                df_c = df_c.sort_values("year", ascending=False).drop_duplicates("cluster_name")
                df_c = df_c.sort_values("funding_gap", ascending=False)

                st.markdown("#### Cluster-Level Funding Gaps")

                fig_cluster = px.bar(
                    df_c,
                    x="funding_gap",
                    y="cluster_name",
                    orientation="h",
                    color="funding_gap",
                    color_continuous_scale=[[0, "#2ecc71"], [0.5, "#f39c12"], [1, "#e74c3c"]],
                    range_color=[0, 1],
                    labels={"funding_gap": "Funding Gap", "cluster_name": "Cluster"},
                    hover_data={
                        "requirements_usd_m": ":.1f",
                        "funding_usd_m": ":.1f",
                        "funding_gap": ":.1%",
                    },
                )
                fig_cluster.update_layout(
                    height=max(250, len(df_c) * 35),
                    showlegend=False,
                    coloraxis_showscale=False,
                    margin=dict(l=0, r=0, t=10, b=0),
                    yaxis=dict(title=""),
                )
                st.plotly_chart(fig_cluster, use_container_width=True)

                # Most underfunded cluster headline
                worst = df_c.iloc[0]
                st.info(
                    f"Most underfunded cluster: **{worst['cluster_name']}** "
                    f"({worst['funding_gap'] * 100:.0f}% funding gap)"
                )

        # Navigate to drilldown
        st.page_link("pages/2_Crisis_Drilldown.py", label=f"Full drill-down for {country_name} →")

else:
    st.info("Click a country on the map to see its details.")

# --- Top 10 ranking table ---
st.markdown("---")
st.subheader("OCI Rankings")

df_table = (
    df_filtered.sort_values("oci_score", ascending=False)
    .head(20)
    .copy()
)
df_table["Rank"] = range(1, len(df_table) + 1)

display_cols = {
    "Rank": "Rank",
    "display_name": "Country",
    "oci_score": "OCI Score",
    "funding_gap": "Funding Gap",
    "people_in_need_k": "People in Need (k)",
    "requirements_usd_m": "Requirements ($M)",
    "funding_usd_m": "Funded ($M)",
}
df_display = df_table[[c for c in display_cols if c in df_table.columns]].rename(
    columns=display_cols
)

st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "OCI Score": st.column_config.ProgressColumn(
            "OCI Score", min_value=0, max_value=1, format="%.3f"
        ),
        "Funding Gap": st.column_config.ProgressColumn(
            "Funding Gap", min_value=0, max_value=1, format="%.0%%"
        ),
    },
)
