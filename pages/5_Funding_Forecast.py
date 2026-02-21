"""
CrisisLens — Funding Forecast
===============================
Identifies crises trending toward deeper underfunding using
linear regression with confidence intervals on historical funding coverage.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats


# --- Data loading ---
@st.cache_data(ttl=3600, show_spinner="Loading OCI scores...")
def _load_oci():
    path = Path("data/processed/oci_scores.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(ttl=3600, show_spinner="Computing forecasts...")
def _compute_forecasts(df_oci_hash):
    """Compute linear regression forecasts with confidence intervals."""
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

        # scipy linregress gives us slope, intercept, r_value, p_value, stderr
        result = stats.linregress(x, y)
        slope = result.slope
        intercept = result.intercept
        r_squared = result.rvalue ** 2
        stderr = result.stderr
        intercept_stderr = result.intercept_stderr if hasattr(result, "intercept_stderr") else 0

        # Project to 2027
        proj_2027 = float(np.clip(slope * 2027 + intercept, 0, 1))

        # 90% prediction interval width at 2027
        n = len(x)
        x_mean = x.mean()
        se_pred = stderr * np.sqrt(1 + 1/n + (2027 - x_mean)**2 / np.sum((x - x_mean)**2)) if n > 2 else stderr * 2
        t_crit = stats.t.ppf(0.95, df=max(n - 2, 1))  # 90% two-sided
        margin = t_crit * se_pred

        results.append({
            "country_iso3": iso3,
            "country_name": g["country_name"].dropna().iloc[-1] if "country_name" in g.columns and g["country_name"].notna().any() else iso3,
            "slope": round(slope, 6),
            "intercept": round(intercept, 4),
            "r_squared": round(r_squared, 4),
            "p_value": round(result.pvalue, 4),
            "stderr": round(stderr, 6),
            "current_gap": round(float(y[-1]), 4),
            "proj_gap_2027": round(proj_2027, 4),
            "proj_upper": round(float(np.clip(proj_2027 + margin, 0, 1)), 4),
            "proj_lower": round(float(np.clip(proj_2027 - margin, 0, 1)), 4),
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
    "Linear regression with confidence intervals on historical funding gap data "
    "to identify crises trending toward deeper underfunding."
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
confidence_level = st.sidebar.radio("Confidence Band", ["90%", "None"], index=0)

# --- At-risk crises ---
median_oci = df_oci["oci_score"].median() if "oci_score" in df_oci.columns else 0.5

df_at_risk = df_forecast_filtered[
    (df_forecast_filtered["slope"] > 0)
    & (df_forecast_filtered["latest_oci"] > median_oci)
].sort_values("slope", ascending=False)

# --- Summary metrics ---
c1, c2, c3, c4 = st.columns(4)
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
with c4:
    sig_count = (df_forecast_filtered["p_value"] < 0.1).sum()
    st.metric("Statistically Significant", f"{sig_count}/{len(df_forecast_filtered)}")

# --- Key Finding ---
if not df_at_risk.empty:
    n_worsening = len(df_at_risk)
    worst_name = df_at_risk.iloc[0]["country_name"]
    worst_proj = df_at_risk.iloc[0]["proj_gap_2027"]
    st.error(
        f"**Key Finding:** {n_worsening} crises are trending toward deeper neglect. "
        f"**{worst_name}** is projected to reach a **{worst_proj * 100:.0f}% funding gap** "
        f"by 2027 if current trends continue."
    )

st.markdown("---")

# --- At-risk table ---
st.subheader("Crises at Risk of Being Forgotten")
st.caption(
    "Crises with increasing funding gaps AND above-median OCI scores. "
    "Positive slope means the gap is growing year over year."
)

display_df = df_at_risk if not show_all else df_forecast_filtered.sort_values("slope", ascending=False)

if not display_df.empty:
    table_cols = ["country_name", "country_iso3", "current_gap", "proj_gap_2027",
                  "proj_lower", "proj_upper", "slope", "r_squared", "p_value",
                  "latest_oci", "n_years", "years_range"]
    available_cols = [c for c in table_cols if c in display_df.columns]
    st.dataframe(
        display_df[available_cols].rename(columns={
            "country_name": "Country",
            "country_iso3": "ISO3",
            "current_gap": "Current Gap",
            "proj_gap_2027": "2027 Projected",
            "proj_lower": "90% Lower",
            "proj_upper": "90% Upper",
            "slope": "Gap Trend (slope)",
            "r_squared": "R²",
            "p_value": "p-value",
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
            "2027 Projected": st.column_config.ProgressColumn(
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

        # Confidence band (if enabled and enough data)
        if confidence_level == "90%" and fr["n_years"] >= 2:
            x_hist = df_hist["year"].values.astype(float)
            n = len(x_hist)
            x_mean = x_hist.mean()
            ss_x = np.sum((x_hist - x_mean) ** 2)

            all_years_arr = np.array(list(df_hist["year"].values) + forecast_years, dtype=float)

            if n > 2 and ss_x > 0:
                # Residual standard error
                y_hist = df_hist["funding_gap"].values.astype(float)
                y_pred_hist = fr["slope"] * x_hist + fr["intercept"]
                s_e = np.sqrt(np.sum((y_hist - y_pred_hist) ** 2) / (n - 2))
                t_crit = stats.t.ppf(0.95, df=n - 2)

                se_pred = s_e * np.sqrt(
                    1 + 1/n + (all_years_arr - x_mean)**2 / ss_x
                )
                trend_y = np.array([fr["slope"] * y + fr["intercept"] for y in all_years_arr])
                upper = np.clip(trend_y + t_crit * se_pred, 0, 1)
                lower = np.clip(trend_y - t_crit * se_pred, 0, 1)

                fig.add_trace(go.Scatter(
                    x=np.concatenate([all_years_arr, all_years_arr[::-1]]),
                    y=np.concatenate([upper, lower[::-1]]),
                    fill="toself",
                    fillcolor="rgba(231,76,60,0.1)",
                    line=dict(color="rgba(231,76,60,0)"),
                    name="90% Prediction Interval",
                    hoverinfo="skip",
                ))

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
        sig_text = " (statistically significant)" if fr["p_value"] < 0.1 else " (not statistically significant)"
        st.markdown(
            f"**{country_name}:** Funding gap is **{direction}** at "
            f"**{abs(fr['slope']) * 100:.2f} percentage points per year** "
            f"(R² = {fr['r_squared']:.3f}, p = {fr['p_value']:.3f}){sig_text}. "
            f"Projected 2027 funding gap: **{fr['proj_gap_2027'] * 100:.0f}%** "
            f"(90% CI: {fr['proj_lower'] * 100:.0f}%–{fr['proj_upper'] * 100:.0f}%)."
        )
    else:
        st.info("Insufficient data for this country.")

# --- Methodology ---
with st.expander("How does forecasting work?"):
    st.markdown("""
    **Method:** Linear regression (`scipy.stats.linregress`) on historical funding gap vs. year,
    with prediction intervals.

    - `funding_gap = slope × year + intercept`
    - A **positive slope** means the gap is growing (coverage declining)
    - Projections are clipped to [0, 1] (valid range for a percentage)
    - **R²** measures goodness of fit; **p-value** tests statistical significance of the trend
    - **90% prediction interval** shows the range within which the true 2027 value is
      expected to fall, accounting for both parameter uncertainty and residual variance

    **"At risk" criteria:**
    - Positive slope (gap increasing) **AND**
    - Latest OCI score above the median across all crises

    This identifies crises that are both currently overlooked and getting worse
    over time — the strongest signal for proactive funding reallocation.

    **Limitation:** Linear extrapolation assumes the trend continues. Sudden
    changes (new conflict, peace agreement, donor pledges) are not captured.
    With only 2-3 data points, confidence intervals are necessarily wide.
    """)
