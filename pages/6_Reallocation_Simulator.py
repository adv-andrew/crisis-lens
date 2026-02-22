"""
CrisisLens — Funding Reallocation Simulator
=============================================
Interactive policy tool: model the impact of redistributing funding
from well-funded crises to the most overlooked ones, proportional to OCI score.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


# --- Data loading ---
@st.cache_data(ttl=3600, show_spinner="Loading OCI scores...")
def _load_oci():
    path = Path("data/processed/oci_scores.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


df_oci = _load_oci()

if df_oci.empty:
    st.warning("No data available. Run `python utils/data_loader.py` first.")
    st.stop()

# --- Header ---
st.header("Funding Reallocation Simulator")
st.caption(
    "Model the impact of redistributing a fraction of funding from "
    "better-funded crises to the most overlooked ones, proportional to OCI score."
)

# --- Filter to latest year per country ---
df = (
    df_oci.sort_values("year", ascending=False)
    .drop_duplicates("country_iso3")
    .copy()
)

# Ensure required columns
for col in ["requirements_usd_m", "funding_usd_m", "funding_gap", "oci_score"]:
    if col not in df.columns:
        st.error(f"Missing column: {col}")
        st.stop()

df = df[
    df["requirements_usd_m"].notna()
    & df["funding_usd_m"].notna()
    & (df["requirements_usd_m"] > 0)
].copy()

if df.empty:
    st.warning("No crises with funding data available.")
    st.stop()

df["display_name"] = df["country_name"].fillna(df["country_iso3"])
df["shortfall_usd_m"] = (df["requirements_usd_m"] - df["funding_usd_m"]).clip(lower=0)
df["surplus_usd_m"] = (df["funding_usd_m"] - df["requirements_usd_m"]).clip(lower=0)

# --- Sidebar Controls ---
st.sidebar.header("Simulator Controls")

# Reallocation percentage
realloc_pct = st.sidebar.slider(
    "Reallocation %",
    min_value=0,
    max_value=30,
    value=10,
    step=1,
    help="Percentage of funding to redistribute from donor crises to recipient crises.",
)

# OCI threshold for recipients
oci_threshold = st.sidebar.slider(
    "Recipient OCI threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.05,
    help="Only crises with OCI above this threshold receive reallocated funds.",
)

# Funding gap threshold for donors
gap_threshold = st.sidebar.slider(
    "Donor max funding gap",
    min_value=0.0,
    max_value=1.0,
    value=0.90,
    step=0.05,
    help="Only crises with funding gap below this threshold contribute funds. "
         "Most crises have gaps above 80%, so set this high to include donors.",
)

# --- Compute reallocation ---
# Donors: crises that are relatively well-funded (gap < threshold)
donors = df[df["funding_gap"] <= gap_threshold].copy()
# Recipients: crises that are most overlooked (OCI > threshold)
recipients = df[df["oci_score"] >= oci_threshold].copy()

# Total pool: realloc_pct of donor funding
total_pool = donors["funding_usd_m"].sum() * (realloc_pct / 100)

# Distribute proportional to OCI score (higher OCI = more allocation)
if not recipients.empty and total_pool > 0:
    recipients["oci_weight"] = recipients["oci_score"] / recipients["oci_score"].sum()
    recipients["allocated_usd_m"] = recipients["oci_weight"] * total_pool
    # Cap allocation at the shortfall (don't over-fund)
    recipients["allocated_usd_m"] = recipients[["allocated_usd_m", "shortfall_usd_m"]].min(axis=1)
    recipients["new_funding_usd_m"] = recipients["funding_usd_m"] + recipients["allocated_usd_m"]
    recipients["new_funding_gap"] = (
        1 - recipients["new_funding_usd_m"] / recipients["requirements_usd_m"]
    ).clip(0, 1)
    recipients["gap_reduction"] = recipients["funding_gap"] - recipients["new_funding_gap"]
    recipients["additional_people_reached_k"] = (
        recipients["allocated_usd_m"]
        / recipients["requirements_usd_m"]
        * recipients.get("people_in_need_k", 0)
    )
else:
    recipients["allocated_usd_m"] = 0
    recipients["new_funding_gap"] = recipients["funding_gap"]
    recipients["gap_reduction"] = 0
    recipients["additional_people_reached_k"] = 0

# --- Summary Metrics ---
c1, c2, c3, c4 = st.columns(4)

total_allocated = recipients["allocated_usd_m"].sum() if not recipients.empty else 0
avg_gap_before = recipients["funding_gap"].mean() if not recipients.empty else 0
avg_gap_after = recipients["new_funding_gap"].mean() if not recipients.empty else 0
total_additional_people = recipients["additional_people_reached_k"].sum() if not recipients.empty else 0

with c1:
    st.metric(
        "Funding Pool",
        f"${total_pool:,.0f}M",
        f"{realloc_pct}% of ${donors['funding_usd_m'].sum():,.0f}M" if not donors.empty else None,
    )
with c2:
    st.metric(
        "Total Reallocated",
        f"${total_allocated:,.0f}M",
        f"to {len(recipients)} crises",
    )
with c3:
    gap_delta = avg_gap_after - avg_gap_before
    st.metric(
        "Avg Recipient Gap",
        f"{avg_gap_after * 100:.1f}%",
        f"{gap_delta * 100:+.1f}pp" if gap_delta != 0 else "no change",
        delta_color="inverse",
    )
with c4:
    st.metric(
        "Additional People Reached",
        f"{total_additional_people / 1000:.1f}M",
        "estimated from funding proportions",
    )

# --- Key Finding ---
if not recipients.empty and total_allocated > 0:
    top_recipient = recipients.sort_values("allocated_usd_m", ascending=False).iloc[0]
    st.success(
        f"**Policy Insight:** Redirecting **{realloc_pct}%** of funding from "
        f"{len(donors)} better-funded crises generates **${total_pool:,.0f}M**. "
        f"Distributing by OCI score reduces the average recipient funding gap from "
        f"**{avg_gap_before * 100:.0f}%** to **{avg_gap_after * 100:.0f}%**, "
        f"potentially reaching an additional **{total_additional_people / 1000:.1f}M people**. "
        f"The largest allocation goes to **{top_recipient['display_name']}** "
        f"(+${top_recipient['allocated_usd_m']:,.0f}M)."
    )
elif realloc_pct == 0:
    st.info("Adjust the reallocation slider above to model funding redistribution.")
else:
    st.warning("No eligible donor or recipient crises with current thresholds.")

st.markdown("---")

# --- Before/After Comparison Chart ---
st.subheader("Before vs. After Funding Gaps")

if not recipients.empty and total_allocated > 0:
    df_chart = recipients.sort_values("oci_score", ascending=False).head(15).copy()

    fig = go.Figure()

    # Before (current gap)
    fig.add_trace(go.Bar(
        y=df_chart["display_name"],
        x=df_chart["funding_gap"] * 100,
        name="Current Gap",
        orientation="h",
        marker_color="rgba(205,58,31,0.5)",
        text=[f"{v:.0f}%" for v in df_chart["funding_gap"] * 100],
        textposition="auto",
    ))

    # After (new gap)
    fig.add_trace(go.Bar(
        y=df_chart["display_name"],
        x=df_chart["new_funding_gap"] * 100,
        name=f"After {realloc_pct}% Reallocation",
        orientation="h",
        marker_color="rgba(127,185,47,0.7)",
        text=[f"{v:.0f}%" for v in df_chart["new_funding_gap"] * 100],
        textposition="auto",
    ))

    fig.update_layout(
        barmode="overlay",
        height=max(400, len(df_chart) * 40),
        xaxis=dict(title="Funding Gap (%)", range=[0, 105]),
        yaxis=dict(autorange="reversed"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=10, b=0),
    )

    st.plotly_chart(fig, use_container_width=True)

# --- Allocation Detail Table ---
st.markdown("---")
st.subheader("Allocation Details")

if not recipients.empty and total_allocated > 0:
    df_table = recipients.sort_values("allocated_usd_m", ascending=False).copy()
    display_cols = {
        "display_name": "Country",
        "oci_score": "OCI Score",
        "funding_gap": "Current Gap",
        "allocated_usd_m": "Allocated ($M)",
        "new_funding_gap": "New Gap",
        "gap_reduction": "Gap Reduction",
        "additional_people_reached_k": "Add'l People (k)",
    }
    df_show = df_table[[c for c in display_cols if c in df_table.columns]].rename(
        columns=display_cols
    )
    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "OCI Score": st.column_config.ProgressColumn(
                "OCI Score", min_value=0, max_value=1, format="%.3f"
            ),
            "Current Gap": st.column_config.ProgressColumn(
                "Current Gap", min_value=0, max_value=1, format="%.0%%"
            ),
            "New Gap": st.column_config.ProgressColumn(
                "New Gap", min_value=0, max_value=1, format="%.0%%"
            ),
            "Allocated ($M)": st.column_config.NumberColumn(
                "Allocated ($M)", format="$%,.1f"
            ),
            "Gap Reduction": st.column_config.NumberColumn(
                "Gap Reduction", format="%.1%%"
            ),
            "Add'l People (k)": st.column_config.NumberColumn(
                "Add'l People (k)", format="%,.0f"
            ),
        },
    )
else:
    st.info("Adjust the sliders in the sidebar to see allocation details.")

# --- Donor breakdown ---
st.markdown("---")
st.subheader("Donor Crises")
st.caption(
    f"Crises with funding gap below {gap_threshold * 100:.0f}% contributing "
    f"{realloc_pct}% of their received funding."
)

if not donors.empty:
    donors_show = donors.sort_values("funding_gap").copy()
    donors_show["contribution_usd_m"] = donors_show["funding_usd_m"] * (realloc_pct / 100)
    donors_show["remaining_usd_m"] = donors_show["funding_usd_m"] - donors_show["contribution_usd_m"]
    donors_show["remaining_gap"] = (
        1 - donors_show["remaining_usd_m"] / donors_show["requirements_usd_m"]
    ).clip(0, 1)

    donor_cols = {
        "display_name": "Country",
        "funding_gap": "Current Gap",
        "funding_usd_m": "Current Funding ($M)",
        "contribution_usd_m": "Contribution ($M)",
        "remaining_gap": "Gap After Contribution",
    }
    df_donor_show = donors_show[
        [c for c in donor_cols if c in donors_show.columns]
    ].rename(columns=donor_cols)

    st.dataframe(
        df_donor_show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Current Gap": st.column_config.ProgressColumn(
                "Current Gap", min_value=0, max_value=1, format="%.0%%"
            ),
            "Current Funding ($M)": st.column_config.NumberColumn(
                "Current Funding ($M)", format="$%,.1f"
            ),
            "Contribution ($M)": st.column_config.NumberColumn(
                "Contribution ($M)", format="$%,.1f"
            ),
            "Gap After Contribution": st.column_config.ProgressColumn(
                "Gap After", min_value=0, max_value=1, format="%.0%%"
            ),
        },
    )
else:
    st.info(f"No crises have a funding gap below {gap_threshold * 100:.0f}%.")

# --- Sensitivity: sweep reallocation percentages ---
st.markdown("---")
st.subheader("Sensitivity Analysis")
st.caption("How average recipient funding gap changes across reallocation levels.")

if not donors.empty and not recipients.empty:
    sweep_pcts = list(range(0, 31, 2))
    sweep_gaps = []
    sweep_people = []
    donor_funding_total = donors["funding_usd_m"].sum()
    recipient_oci_sum = recipients["oci_score"].sum()

    for pct in sweep_pcts:
        pool = donor_funding_total * (pct / 100)
        if recipient_oci_sum > 0:
            alloc = (recipients["oci_score"] / recipient_oci_sum) * pool
            alloc = pd.DataFrame({
                "alloc": alloc.values,
                "shortfall": recipients["shortfall_usd_m"].values,
                "funding": recipients["funding_usd_m"].values,
                "req": recipients["requirements_usd_m"].values,
                "pin_k": recipients["people_in_need_k"].values if "people_in_need_k" in recipients.columns else 0,
            })
            alloc["alloc"] = alloc[["alloc", "shortfall"]].min(axis=1)
            alloc["new_gap"] = (1 - (alloc["funding"] + alloc["alloc"]) / alloc["req"]).clip(0, 1)
            alloc["add_people_k"] = alloc["alloc"] / alloc["req"] * alloc["pin_k"]
            sweep_gaps.append(alloc["new_gap"].mean())
            sweep_people.append(alloc["add_people_k"].sum() / 1000)
        else:
            sweep_gaps.append(avg_gap_before)
            sweep_people.append(0)

    fig_sens = go.Figure()
    fig_sens.add_trace(go.Scatter(
        x=sweep_pcts,
        y=[g * 100 for g in sweep_gaps],
        mode="lines+markers",
        name="Avg Recipient Gap (%)",
        line=dict(color="#cd3a1f", width=2.5),
        marker=dict(size=6),
    ))

    # Mark current selection
    fig_sens.add_vline(
        x=realloc_pct,
        line_dash="dash",
        line_color="#f39c12",
        annotation_text=f"Current: {realloc_pct}%",
        annotation_position="top",
    )

    # Reference line: current gap
    fig_sens.add_hline(
        y=avg_gap_before * 100,
        line_dash="dot",
        line_color="#95a5a6",
        annotation_text="No reallocation",
        annotation_position="bottom right",
    )

    fig_sens.update_layout(
        height=350,
        xaxis=dict(title="Reallocation %", dtick=5),
        yaxis=dict(title="Avg Recipient Funding Gap (%)"),
        margin=dict(l=0, r=0, t=10, b=0),
    )

    st.plotly_chart(fig_sens, use_container_width=True)

    # People reached on secondary axis
    fig_people = go.Figure()
    fig_people.add_trace(go.Bar(
        x=sweep_pcts,
        y=sweep_people,
        marker_color="rgba(127,185,47,0.6)",
        name="Additional People Reached (M)",
    ))
    fig_people.add_vline(
        x=realloc_pct, line_dash="dash", line_color="#f39c12",
    )
    fig_people.update_layout(
        height=250,
        xaxis=dict(title="Reallocation %", dtick=5),
        yaxis=dict(title="Additional People Reached (M)"),
        margin=dict(l=0, r=0, t=10, b=0),
    )
    st.plotly_chart(fig_people, use_container_width=True)

# --- Methodology ---
with st.expander("How does the simulator work?"):
    st.markdown("""
    **Funding Pool:** A percentage of funding currently received by "donor" crises
    (those with funding gap below the donor threshold) is pooled for redistribution.

    **Allocation:** The pool is distributed to "recipient" crises (those with OCI
    above the recipient threshold) in proportion to their OCI scores — higher OCI
    gets a larger share. Allocations are capped at each crisis's shortfall to avoid
    over-funding.

    **People Reached Estimate:** Assumes a linear relationship between funding and
    coverage. If a crisis has $X requirement for Y people, each dollar of additional
    funding is estimated to reach Y/X additional people. This is a simplification —
    real marginal returns vary by context.

    **Limitations:**
    - This is a **modeling tool**, not a policy recommendation. Real reallocation
      involves political, logistical, and mandate constraints not captured here.
    - The linear people-reached estimate overestimates impact in hard-to-reach areas
      and underestimates it in efficient contexts.
    - Donor crises may be under-funded relative to needs even if their gap is below
      the threshold.
    """)
