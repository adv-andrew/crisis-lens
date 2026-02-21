"""
CrisisLens — Funding Forecast
===============================
Identifies crises trending toward deeper underfunding using
linear regression on historical funding coverage.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path


# --- Data loading ---
@st.cache_data(ttl=3600, show_spinner="Loading OCI scores...")
def _load_oci():
    path = Path("data/processed/oci_scores.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=3600, show_spinner="Computing forecasts...")
def _compute_forecasts(df_oci_hash):
    """Compute linear regression forecasts for all countries with multi-year data."""
    df_oci = _load_oci()
    if df_oci.empty:
        return pd.DataFrame()

    results = []
    for iso3, group in df_oci.groupby("country_iso3"):
        g = group.dropna(subset=["funding_gap", "year"]).sort_values("year")
        if len(g) < 2:
            continue

        x = g["year"].values.astype(float)
        y = g["funding_gap"].values.astype(float)

        # Linear regression: funding_gap = slope * year + intercept
        slope, intercept = np.polyfit(x, y, deg=1)

        # Project to 2027
        proj_2027 = float(np.clip(slope * 2027 + intercept, 0, 1))

        # R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        results.append({
            "country_iso3": iso3,
            "country_name": g["country_name"].dropna().iloc[-1] if "country_name" in g.columns and g["country_name"].notna().any() else iso3,
            "slope": round(slope, 6),
            "intercept": round(intercept, 4),
            "r_squared": round(r_squared, 4),
            "current_gap": round(float(y[-1]), 4),
            "proj_gap_2027": round(proj_2027, 4),
            "latest_oci": float(g["oci_score"].iloc[-1]) if "oci_score" in g.columns else 0,
            "n_years": len(g),
            "years_range": f"{int(x[0])}-{int(x[-1])}",
        })

    return pd.DataFrame(results)


df_oci = _load_oci()

if df_oci.empty:
    st.warning("No data available. Run `python utils/data_loader.py` first.")
    st.stop()

df_forecast = _compute_forecasts(len(df_oci))

# --- Header ---
st.header("Funding Forecast")
st.caption(
    "Linear regression on historical funding gap data to identify crises "
    "trending toward deeper underfunding."
)

if df_forecast.empty:
    st.warning(
        "Insufficient multi-year data for forecasting. "
        "Need at least 2 years of data per country."
    )
    st.stop()

# --- Sidebar ---
st.sidebar.header("Forecast Controls")

min_years = st.sidebar.slider("Minimum years of data", 2, 5, 2)
df_forecast_filtered = df_forecast[df_forecast["n_years"] >= min_years]

show_all = st.sidebar.checkbox("Show all crises (not just at-risk)", value=False)

# --- At-risk crises ---
# Positive slope = funding gap growing = crisis getting worse
median_oci = df_oci["oci_score"].median() if "oci_score" in df_oci.columns else 0.5

df_at_risk = df_forecast_filtered[
    (df_forecast_filtered["slope"] > 0)
    & (df_forecast_filtered["latest_oci"] > median_oci)
].sort_values("slope", ascending=False)

# --- Summary metrics ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Crises at Risk", len(df_at_risk))
with c2:
    st.metric("Crises Analyzed", len(df_forecast_filtered))
with c3:
    if not df_at_risk.empty:
        worst = df_at_risk.iloc[0]
        st.metric(
            "Most At-Risk",
            str(worst["country_name"]),
            f"+{worst['slope'] * 100:.1f}% gap/year",
        )
    else:
        st.metric("Most At-Risk", "None detected")

st.markdown("---")

# --- At-risk table ---
st.subheader("Crises at Risk of Being Forgotten")
st.caption(
    "Crises with increasing funding gaps AND above-median OCI scores. "
    "Positive slope means the gap is growing year over year."
)

display_df = df_at_risk if not show_all else df_forecast_filtered.sort_values("slope", ascending=False)

if not display_df.empty:
    st.dataframe(
        display_df[
            ["country_name", "country_iso3", "current_gap", "proj_gap_2027",
             "slope", "r_squared", "latest_oci", "n_years", "years_range"]
        ].rename(columns={
            "country_name": "Country",
            "country_iso3": "ISO3",
            "current_gap": "Current Gap",
            "proj_gap_2027": "2027 Projected Gap",
            "slope": "Gap Trend (slope)",
            "r_squared": "R²",
            "latest_oci": "Latest OCI",
            "n_years": "Data Points",
            "years_range": "Years",
        }),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current Gap": st.column_config.ProgressColumn(
                "Current Gap", min_value=0, max_value=1, format="%.0%%"
            ),
            "2027 Projected Gap": st.column_config.ProgressColumn(
                "2027 Projected", min_value=0, max_value=1, format="%.0%%"
            ),
            "Latest OCI": st.column_config.ProgressColumn(
                "Latest OCI", min_value=0, max_value=1, format="%.3f"
            ),
        },
    )
else:
    st.success("No crises currently trending toward increased underfunding.")

# --- Individual trend chart ---
st.markdown("---")
st.subheader("Country Funding Trend")

if not df_forecast_filtered.empty:
    country_options = df_forecast_filtered.sort_values("slope", ascending=False)
    selected_country = st.selectbox(
        "Select country",
        country_options["country_iso3"].tolist(),
        format_func=lambda iso3: f"{df_forecast_filtered[df_forecast_filtered['country_iso3'] == iso3]['country_name'].iloc[0]} ({iso3})",
    )

    # Get historical data
    df_hist = df_oci[df_oci["country_iso3"] == selected_country].sort_values("year")
    df_hist = df_hist.dropna(subset=["funding_gap", "year"])

    forecast_row = df_forecast_filtered[df_forecast_filtered["country_iso3"] == selected_country]

    if not df_hist.empty and not forecast_row.empty:
        fr = forecast_row.iloc[0]
        country_name = fr["country_name"]

        # Build forecast points
        last_year = int(df_hist["year"].max())
        forecast_years = list(range(last_year + 1, 2028))
        forecast_gaps = [float(np.clip(fr["slope"] * y + fr["intercept"], 0, 1)) for y in forecast_years]

        fig = go.Figure()

        # Historical line
        fig.add_trace(go.Scatter(
            x=df_hist["year"],
            y=df_hist["funding_gap"],
            mode="lines+markers",
            name="Historical",
            line=dict(color="#1f77b4", width=2.5),
            marker=dict(size=8),
        ))

        # Trend line (full range including historical)
        all_years = list(df_hist["year"].values) + forecast_years
        trend_y = [float(np.clip(fr["slope"] * y + fr["intercept"], 0, 1)) for y in all_years]
        fig.add_trace(go.Scatter(
            x=all_years,
            y=trend_y,
            mode="lines",
            name="Linear Trend",
            line=dict(color="#95a5a6", width=1.5, dash="dot"),
        ))

        # Forecast points
        if forecast_years:
            fig.add_trace(go.Scatter(
                x=forecast_years,
                y=forecast_gaps,
                mode="markers",
                name="Projected",
                marker=dict(color="#e74c3c", size=12, symbol="star"),
            ))

        # Shade forecast zone
        if forecast_years:
            fig.add_vrect(
                x0=forecast_years[0] - 0.5,
                x1=forecast_years[-1] + 0.5,
                fillcolor="orange",
                opacity=0.07,
                layer="below",
                line_width=0,
            )

        fig.update_layout(
            height=400,
            yaxis=dict(range=[0, 1.05], title="Funding Gap (0=Funded, 1=Unfunded)"),
            xaxis=dict(title="Year"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=30, b=0),
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

        # Interpretation
        direction = "increasing" if fr["slope"] > 0 else "decreasing"
        st.markdown(
            f"**{country_name}:** Funding gap is **{direction}** at "
            f"**{abs(fr['slope']) * 100:.2f} percentage points per year** "
            f"(R² = {fr['r_squared']:.3f}). "
            f"Projected 2027 funding gap: **{fr['proj_gap_2027'] * 100:.0f}%**."
        )
    else:
        st.info("Insufficient data for this country.")

# --- Methodology ---
with st.expander("How does forecasting work?"):
    st.markdown("""
    **Method:** Simple linear regression on historical funding gap vs. year.

    - `funding_gap = slope × year + intercept`
    - A **positive slope** means the gap is growing (coverage declining)
    - Projections are clipped to [0, 1] (valid range for a percentage)
    - R² measures how well the linear trend fits the historical data

    **"At risk" criteria:**
    - Positive slope (gap increasing) **AND**
    - Latest OCI score above the median across all crises

    This identifies crises that are both currently overlooked and getting worse
    over time — the strongest signal for proactive funding reallocation.

    **Limitation:** Linear extrapolation assumes the trend continues. Sudden
    changes (new conflict, peace agreement, donor pledges) are not captured.
    """)
