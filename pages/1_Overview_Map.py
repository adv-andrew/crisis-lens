"""
CrisisLens — Overview Map
=========================
OCI choropleth world map with country click drill-down.
Primary entry point for the visual experience.
Includes tokenize-on-Solana for each country in the OCI rankings (same method as mint_nfts.py).
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.pinata_upload import get_pinata_jwt, upload_json_to_pinata
from utils.donate_solana import get_treasury_address, render_donate_solana


def _make_country_mint_script(uris):
    """Generate a runnable Python script that mints each country as a Solana token (same logic as mint_nfts.py)."""
    lines = [
        '"""Mint CrisisLens country tokens on Solana. Generated from Overview Map. Same logic as mint_nfts.py."""',
        "import subprocess",
        "",
        "uris = {",
    ]
    for iso, data in uris.items():
        name_safe = data["name"].replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{iso}": {{"name": "{name_safe}", "uri": "{data["uri"]}"}},')
    lines.append("}")
    lines.append("")
    lines.append('print("Minting country tokens...\\n" + "="*40)')
    lines.append("")
    lines.append("for iso, info in uris.items():")
    lines.append('    name, uri = info["name"], info["uri"]')
    lines.append('    print(f"Minting: {name}")')
    lines.append("    out = subprocess.getoutput('spl-token create-token --program-2022 --decimals 0 --enable-metadata')")
    lines.append("    try:")
    lines.append('        token_address = out.split("Creating token ")[1].split()[0]')
    lines.append("    except IndexError:")
    lines.append('        print(f"  Error: {out}")')
    lines.append("        continue")
    lines.append("    subprocess.run(['spl-token', 'initialize-metadata', token_address, name, 'CRISIS', uri], check=True)")
    lines.append("    subprocess.run(['spl-token', 'create-account', token_address], check=True)")
    lines.append("    subprocess.run(['spl-token', 'mint', token_address, '1'], check=True)")
    lines.append("    subprocess.run(['spl-token', 'authorize', token_address, 'mint', '--disable'], check=True)")
    lines.append('    print(f"  Token: {token_address}\\n" + "-"*40)')
    return "\n".join(lines)


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

st.sidebar.markdown("---")
animate_timeline = st.sidebar.checkbox(
    "Animate Timeline (2024-2026)",
    value=False,
    help="Play an animated choropleth showing how OCI scores evolve year over year.",
)

# --- Prepare color settings ---
def _get_color_settings(map_mode, df):
    if map_mode == "OCI Score":
        return "oci_score", [[0, "#7fb92f"], [0.35, "#ff7a00"], [0.65, "#cd3a1f"], [1, "#8e0000"]], "OCI Score", (0, 1)
    elif map_mode == "Funding Gap %":
        return "funding_gap", [[0, "#7fb92f"], [0.5, "#ff7a00"], [1, "#cd3a1f"]], "Funding Gap", (0, 1)
    elif map_mode == "People in Need (M)":
        df["people_in_need_m"] = df["people_in_need_k"] / 1000
        return "people_in_need_m", [[0, "#82b5e9"], [1, "#002856"]], "People in Need (M)", None
    else:  # Media Neglect
        return "media_score", [[0, "#7fb92f"], [0.5, "#ff7a00"], [1, "#8e0000"]], "Media Neglect Score", (0, 1)


# --- Build choropleth ---
st.header("Overlooked Crisis Index — World Map")

if animate_timeline:
    # --- ANIMATED TIMELINE MODE ---
    # Generate interpolated frames between years for smooth transitions.
    # Instead of 3 choppy frames, we create ~15 frames that blend values.
    import numpy as np

    df_base = df_oci.copy()
    df_base["display_name"] = df_base["country_name"].fillna(df_base["country_iso3"])
    df_base["year"] = df_base["year"].astype(int)

    years_sorted = sorted(df_base["year"].unique())
    all_countries = df_base["country_iso3"].unique()
    n_interp = 5  # intermediate frames between each real year

    interpolated_frames = []
    for i in range(len(years_sorted)):
        y = years_sorted[i]
        df_y = df_base[df_base["year"] == y].set_index("country_iso3")

        # Add the real year frame
        frame = df_y.copy()
        frame["frame_label"] = str(y)
        interpolated_frames.append(frame.reset_index())

        # Interpolate toward the next year
        if i < len(years_sorted) - 1:
            y_next = years_sorted[i + 1]
            df_next = df_base[df_base["year"] == y_next].set_index("country_iso3")

            # Only interpolate countries present in both years
            shared = df_y.index.intersection(df_next.index)

            for step in range(1, n_interp + 1):
                t = step / (n_interp + 1)  # 0 < t < 1
                interp = df_y.loc[shared].copy()
                for col in ["oci_score", "funding_gap", "people_in_need_k", "media_score",
                            "pin_normalized", "requirements_usd_m", "funding_usd_m"]:
                    if col in interp.columns and col in df_next.columns:
                        interp[col] = (
                            df_y.loc[shared, col].values * (1 - t)
                            + df_next.loc[shared, col].values * t
                        )
                interp["frame_label"] = f"{y}+{step}"
                interpolated_frames.append(interp.reset_index())

    df_anim = pd.concat(interpolated_frames, ignore_index=True)
    df_anim["display_name"] = df_anim["country_name"].fillna(df_anim["country_iso3"])

    color_col, color_scale, color_label, range_color = _get_color_settings(map_mode, df_anim)

    fig = px.choropleth(
        df_anim,
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
            "display_name": False,
        },
        labels={
            color_col: color_label,
            "oci_score": "OCI Score",
            "funding_gap": "Funding Gap",
            "people_in_need_k": "People in Need (k)",
            "country_iso3": "ISO3",
        },
        animation_frame="frame_label",
    )

    # Only show real years on the slider, not intermediate steps
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        height=600,
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
        sliders=[dict(
            currentvalue=dict(
                prefix="",
                font=dict(size=14, family="Roboto Condensed, sans-serif", color="#4a4a4a"),
            ),
            pad=dict(t=30),
        )],
        updatemenus=[dict(
            type="buttons",
            showactive=False,
            y=0,
            x=0.05,
            xanchor="right",
            buttons=[
                dict(label="Play", method="animate",
                     args=[None, {"frame": {"duration": 400, "redraw": True},
                                  "fromcurrent": True,
                                  "transition": {"duration": 350, "easing": "cubic-in-out"}}]),
                dict(label="Pause", method="animate",
                     args=[[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate",
                                    "transition": {"duration": 0}}]),
            ],
        )],
    )

    st.plotly_chart(fig, use_container_width=True, key="oci_map_animated")

    st.caption(
        "Press **Play** to animate OCI scores across 2024-2026. "
        "Watch how crises evolve — countries appearing in deeper red are becoming more overlooked over time."
    )

    # In animated mode, use latest year for the detail panel and rankings
    df_filtered = (
        df_oci.sort_values("year", ascending=False)
        .drop_duplicates("country_iso3")
        .copy()
    )
    df_filtered["display_name"] = df_filtered["country_name"].fillna(df_filtered["country_iso3"])

    # Skip click-selection in animated mode
    event = None

else:
    # --- STATIC MODE (original behavior) ---
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

    df_filtered["display_name"] = df_filtered["country_name"].fillna(df_filtered["country_iso3"])

    color_col, color_scale, color_label, range_color = _get_color_settings(map_mode, df_filtered)

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

# Handle map click (static mode only)
if event is not None and event and event.selection and event.selection.points:
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

# --- Donate SOL to a country on the OCI list ---
with st.expander("Donate SOL to a country"):
    options = df_table.apply(
        lambda r: (r["country_iso3"], r.get("country_name") or r.get("display_name") or r["country_iso3"]),
        axis=1,
    ).tolist()
    iso_list = [x[0] for x in options]
    name_list = [x[1] for x in options]
    labels = [f"{name} ({iso})" for iso, name in options]
    idx = st.selectbox("Country to donate to", range(len(labels)), format_func=lambda i: labels[i], key="donate_country_select")
    if idx is not None:
        render_donate_solana(iso_list[idx], name_list[idx], compact=True)

# --- Tokenize countries on Solana (same logic as mint_nfts.py) ---
if "country_token_uris" not in st.session_state:
    st.session_state["country_token_uris"] = {}

with st.expander("Tokenize countries on Solana"):
    st.caption(
        "Upload each country in the rankings table as metadata to IPFS (Pinata), "
        "then mint as a Solana token (Token-2022) using the same method as mint_nfts.py."
    )
    jwt = get_pinata_jwt()
    if not jwt:
        st.warning("Set **PINATA_JWT** in `.env` to enable tokenization (get a JWT at [pinata.cloud](https://pinata.cloud)).")
    else:
        if st.button("Upload metadata for all countries in table", type="primary"):
            progress = st.progress(0, text="Uploading to Pinata...")
            uris = {}
            n = len(df_table)
            for i, (_, row) in enumerate(df_table.iterrows()):
                name = str(row.get("country_name") or row.get("display_name") or row["country_iso3"])
                iso = row["country_iso3"]
                oci = float(row.get("oci_score", 0))
                gap = float(row.get("funding_gap", 0))
                pin_k = float(row.get("people_in_need_k", 0))
                req = row.get("requirements_usd_m")
                fund = row.get("funding_usd_m")
                metadata = {
                    "name": f"CrisisLens — {name}",
                    "description": (
                        f"Overlooked Crisis Index: {name}. "
                        f"OCI {oci:.3f}, funding gap {gap*100:.0f}%, "
                        f"{pin_k:,.0f}k people in need."
                    ),
                    "attributes": [
                        {"trait_type": "Country", "value": name},
                        {"trait_type": "ISO3", "value": iso},
                        {"trait_type": "OCI Score", "value": round(oci, 3)},
                        {"trait_type": "Funding Gap %", "value": round(gap * 100, 1)},
                        {"trait_type": "People in Need (k)", "value": round(pin_k, 0)},
                        {"trait_type": "Source", "value": "CrisisLens"},
                    ],
                }
                try:
                    uri = upload_json_to_pinata(
                        metadata,
                        filename=f"crisislens_country_{iso}.json",
                        jwt=jwt,
                    )
                    uris[iso] = {"name": name, "uri": uri}
                except Exception as e:
                    st.session_state["country_token_error"] = str(e)
                progress.progress((i + 1) / n, text=f"Uploaded {i+1}/{n}...")
            progress.empty()
            st.session_state["country_token_uris"] = uris
            if "country_token_error" in st.session_state:
                st.error(st.session_state["country_token_error"])
                del st.session_state["country_token_error"]

        uris = st.session_state.get("country_token_uris", {})
        if uris:
            st.success(f"**{len(uris)}** country metadata URIs ready. Use them to mint Solana tokens (same as mint_nfts.py).")
            for iso, data in list(uris.items())[:10]:
                st.text(f"{data['name']}: {data['uri']}")
            if len(uris) > 10:
                st.caption(f"... and {len(uris) - 10} more.")
            # Generate mint script like mint_nfts.py (spl-token create-token, initialize-metadata, mint 1, lock)
            st.subheader("Mint with spl-token (same as mint_nfts.py)")
            st.caption("Requires Solana CLI and spl-token. Run the downloaded script from the crisis-lens directory.")
            script_body = _make_country_mint_script(uris)
            st.code(script_body, language="python")
            st.download_button(
                "Download mint script (mint_country_tokens.py)",
                data=script_body,
                file_name="mint_country_tokens.py",
                mime="text/x-python",
            )
