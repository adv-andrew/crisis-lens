"""
CrisisLens — Crisis Drilldown
==============================
Per-country cluster-level funding mismatch analysis.
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
df_cluster = _load_cluster()

if df_oci.empty:
    st.warning("No data available. Run `python utils/data_loader.py` first.")
    st.stop()

# Initialize session state
if "selected_iso3" not in st.session_state:
    st.session_state["selected_iso3"] = None

# --- Sidebar filters ---
st.sidebar.header("Crisis Drilldown")

# Country selector
all_iso3 = sorted(df_oci["country_iso3"].dropna().unique().tolist())
if not all_iso3:
    st.warning("No countries in dataset.")
    st.stop()

# Build name map for display
name_map = {}
if "country_name" in df_oci.columns:
    name_map = (
        df_oci.dropna(subset=["country_name"])
        .drop_duplicates("country_iso3")
        .set_index("country_iso3")["country_name"]
        .to_dict()
    )

preselected = st.session_state.get("selected_iso3")
idx = all_iso3.index(preselected) if preselected and preselected in all_iso3 else 0

selected_iso3 = st.sidebar.selectbox(
    "Country",
    all_iso3,
    index=idx,
    format_func=lambda iso3: f"{name_map.get(iso3, iso3)} ({iso3})",
)
st.session_state["selected_iso3"] = selected_iso3

# Year filter
available_years = sorted(df_oci["year"].dropna().unique().tolist(), reverse=True)
selected_year = st.sidebar.selectbox("Year", available_years, index=0)

# --- Get country data ---
country_name = name_map.get(selected_iso3, selected_iso3)

row = df_oci[
    (df_oci["country_iso3"] == selected_iso3) & (df_oci["year"] == selected_year)
]
if row.empty:
    row = df_oci[df_oci["country_iso3"] == selected_iso3].sort_values("year", ascending=False)

if row.empty:
    st.warning(f"No data for {country_name} ({selected_iso3}).")
    st.stop()

r = row.iloc[0]

# --- Header ---
st.header(f"{country_name} ({selected_iso3})")
st.caption(f"Year: {int(r['year'])}" if pd.notna(r.get("year")) else "")

# --- AI Crisis Brief ---
def _generate_crisis_brief(r, country_name, df_cluster, selected_iso3, selected_year):
    """Generate a template-based intelligence brief for this crisis."""
    pin_m = r.get("people_in_need_k", 0) / 1000 if pd.notna(r.get("people_in_need_k")) else 0
    pop_m = r.get("total_population", 0) / 1e6 if pd.notna(r.get("total_population")) else 0
    gap_pct = r.get("funding_gap", 0) * 100 if pd.notna(r.get("funding_gap")) else 0
    oci = r.get("oci_score", 0)
    req = r.get("requirements_usd_m", 0) if pd.notna(r.get("requirements_usd_m")) else 0
    fund = r.get("funding_usd_m", 0) if pd.notna(r.get("funding_usd_m")) else 0
    media = r.get("media_score", 0) if pd.notna(r.get("media_score")) else 0

    # Severity tier from PIN/population ratio
    pin_ratio = r.get("pin_normalized", 0) if pd.notna(r.get("pin_normalized")) else 0
    if pin_ratio > 0.30:
        severity_label = "Extreme (Phase 5)"
    elif pin_ratio > 0.20:
        severity_label = "Severe (Phase 4)"
    elif pin_ratio > 0.10:
        severity_label = "Serious (Phase 3)"
    elif pin_ratio > 0.05:
        severity_label = "Stressed (Phase 2)"
    else:
        severity_label = "Minimal (Phase 1)"

    # Media description
    if media > 0.8:
        media_desc = "virtually no global media attention"
    elif media > 0.6:
        media_desc = "minimal global media coverage"
    elif media > 0.4:
        media_desc = "below-average media visibility"
    elif media > 0.2:
        media_desc = "moderate media coverage"
    else:
        media_desc = "relatively high media attention"

    # Worst cluster
    worst_cluster = None
    if not df_cluster.empty:
        df_c = df_cluster[
            (df_cluster["country_iso3"] == selected_iso3)
            & (df_cluster["year"] == selected_year)
        ]
        if not df_c.empty:
            worst_row = df_c.sort_values("funding_gap", ascending=False).iloc[0]
            worst_cluster = worst_row["cluster_name"]
            worst_gap = worst_row["funding_gap"] * 100

    # Build the brief
    lines = []
    lines.append(
        f"**{country_name}** has **{pin_m:.1f} million people** in need of humanitarian assistance "
        f"out of a population of {pop_m:.1f}M — a severity classification of **{severity_label}**."
    )
    lines.append(
        f"The crisis requires **${req:,.0f}M** in funding but has received only "
        f"**${fund:,.0f}M** ({100 - gap_pct:.0f}%), leaving a **{gap_pct:.0f}% funding gap**. "
        f"It receives {media_desc} (media neglect score: {media:.2f})."
    )
    if worst_cluster:
        lines.append(
            f"The most critically underfunded sector is **{worst_cluster}** "
            f"at **{worst_gap:.0f}% unfunded**. "
            f"With an OCI score of **{oci:.3f}**, this crisis ranks among the "
            f"{'most' if oci > 0.7 else 'moderately' if oci > 0.4 else 'less'} overlooked globally."
        )
    else:
        lines.append(
            f"With an OCI score of **{oci:.3f}**, this crisis ranks among the "
            f"{'most' if oci > 0.7 else 'moderately' if oci > 0.4 else 'less'} overlooked globally."
        )

    return "\n\n".join(lines)


brief = _generate_crisis_brief(r, country_name, df_cluster, selected_iso3, selected_year)
st.markdown(
    f'<div style="background:linear-gradient(135deg,#1a1a2e,#16213e);border-left:4px solid #e74c3c;'
    f'padding:16px 20px;border-radius:0 8px 8px 0;margin-bottom:20px;font-size:15px;line-height:1.7">'
    f'<div style="color:#e74c3c;font-weight:700;font-size:13px;letter-spacing:1px;margin-bottom:8px">'
    f'CRISIS INTELLIGENCE BRIEF</div>'
    f'{brief}</div>',
    unsafe_allow_html=True,
)

# --- KPI Metrics ---
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(
        "OCI Score",
        f"{r['oci_score']:.3f}",
        f"Rank #{int(r['oci_rank'])}" if pd.notna(r.get("oci_rank")) else None,
    )
with c2:
    pin_m = r.get("people_in_need_k", 0)
    pin_m = pin_m / 1000 if pd.notna(pin_m) else 0
    st.metric("People in Need", f"{pin_m:.1f}M")
with c3:
    req = r.get("requirements_usd_m", float("nan"))
    st.metric("Requirements", f"${req:.0f}M" if pd.notna(req) else "N/A")
with c4:
    gap = r.get("funding_gap", float("nan"))
    funded_pct = (1 - gap) * 100 if pd.notna(gap) else float("nan")
    st.metric(
        "Funded",
        f"{funded_pct:.0f}%" if pd.notna(funded_pct) else "N/A",
        f"${r.get('funding_usd_m', 0):.0f}M received" if pd.notna(r.get("funding_usd_m")) else None,
    )

st.markdown("---")

# --- OCI Component Breakdown ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("OCI Component Breakdown")

    comp_names = ["PIN Normalized", "Funding Gap"]
    comp_values = [
        r.get("pin_normalized", 0),
        r.get("funding_gap", 0),
    ]
    if pd.notna(r.get("media_score")) and r.get("media_score", 0) > 0:
        comp_names.append("Media Neglect")
        comp_values.append(r.get("media_score", 0))
    components = pd.DataFrame({
        "Component": comp_names,
        "Value": comp_values,
    })
    components["Value"] = components["Value"].fillna(0).astype(float)

    fig_comp = px.bar(
        components,
        x="Component",
        y="Value",
        color="Component",
        color_discrete_sequence=["#e74c3c", "#e67e22", "#c0392b"],
        range_y=[0, 1],
        labels={"Value": "Score (0-1)"},
    )
    fig_comp.update_layout(
        height=350,
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_comp, use_container_width=True)

# --- Cluster Funding Gaps ---
with col_right:
    st.subheader("Cluster Funding Gaps")

    if not df_cluster.empty:
        df_c = df_cluster[
            (df_cluster["country_iso3"] == selected_iso3)
            & (df_cluster["year"] == selected_year)
        ].copy()

        if df_c.empty:
            # Try any year for this country
            df_c = df_cluster[df_cluster["country_iso3"] == selected_iso3].copy()
            df_c = df_c.sort_values("year", ascending=False).drop_duplicates("cluster_name")

        if not df_c.empty:
            df_c = df_c.sort_values("funding_gap", ascending=True)

            fig_cluster = px.bar(
                df_c,
                x="funding_gap",
                y="cluster_name",
                orientation="h",
                color="funding_gap",
                color_continuous_scale=[[0, "#2ecc71"], [0.5, "#f39c12"], [1, "#e74c3c"]],
                range_color=[0, 1],
                labels={"funding_gap": "Funding Gap", "cluster_name": ""},
                hover_data={
                    "requirements_usd_m": ":.1f",
                    "funding_usd_m": ":.1f",
                    "funding_gap": ":.1%",
                },
            )
            fig_cluster.update_layout(
                height=max(300, len(df_c) * 30),
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig_cluster, use_container_width=True)
        else:
            st.info("No cluster-level data available for this country/year.")
    else:
        st.info("Cluster data not loaded.")

# --- Cluster Detail Table ---
st.markdown("---")
st.subheader("Cluster Detail Table")

if not df_cluster.empty:
    df_c_table = df_cluster[
        (df_cluster["country_iso3"] == selected_iso3)
    ].copy()

    if selected_year:
        df_c_year = df_c_table[df_c_table["year"] == selected_year]
        if not df_c_year.empty:
            df_c_table = df_c_year

    if not df_c_table.empty:
        df_c_table = df_c_table.sort_values("funding_gap", ascending=False)

        # Flag clusters > 1.5 std below crisis average
        avg_gap = df_c_table["funding_gap"].mean()
        std_gap = df_c_table["funding_gap"].std()
        if pd.notna(std_gap) and std_gap > 0:
            df_c_table["critically_underfunded"] = (
                df_c_table["funding_gap"] > avg_gap + 1.5 * std_gap
            )
        else:
            df_c_table["critically_underfunded"] = False

        display_cols = [
            "cluster_name", "requirements_usd_m", "funding_usd_m",
            "funding_gap", "percent_funded", "critically_underfunded",
        ]
        df_show = df_c_table[[c for c in display_cols if c in df_c_table.columns]].copy()
        df_show = df_show.rename(columns={
            "cluster_name": "Cluster",
            "requirements_usd_m": "Requirements ($M)",
            "funding_usd_m": "Funded ($M)",
            "funding_gap": "Funding Gap",
            "percent_funded": "% Funded",
            "critically_underfunded": "Critical",
        })

        st.dataframe(df_show, use_container_width=True, hide_index=True)

        n_critical = df_c_table["critically_underfunded"].sum()
        if n_critical > 0:
            st.warning(
                f"{n_critical} cluster(s) are critically underfunded "
                f"(more than 1.5 std deviations above the country's average funding gap)."
            )
    else:
        st.info("No cluster detail data for this selection.")

# --- Key Finding ---
if pd.notna(r.get("funding_gap")) and pd.notna(r.get("requirements_usd_m")):
    shortfall = r["requirements_usd_m"] * r["funding_gap"]
    media_note = ""
    if pd.notna(r.get("media_score")) and r.get("media_score", 0) > 0.5:
        media_note = (
            f" Meanwhile, it receives only **{(1 - r['media_score']) * 100:.0f}%** "
            f"of the global median media attention."
        )
    st.error(
        f"**Key Finding:** {country_name} has a funding shortfall of "
        f"**${shortfall:,.0f}M** ({r['funding_gap'] * 100:.0f}% unfunded) "
        f"while **{r.get('people_in_need_k', 0) / 1000:.1f}M people** need assistance."
        f"{media_note}"
    )

# --- Historical Trend ---
st.markdown("---")
st.subheader("Funding Gap Trend Over Time")

df_hist = df_oci[df_oci["country_iso3"] == selected_iso3].sort_values("year")

if len(df_hist) > 1:
    fig_trend = px.line(
        df_hist,
        x="year",
        y="funding_gap",
        markers=True,
        labels={"funding_gap": "Funding Gap (0=Funded, 1=Unfunded)", "year": "Year"},
    )
    fig_trend.update_layout(
        height=350,
        yaxis=dict(range=[0, 1.05]),
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Only one year of data available — trend requires multiple years.")
