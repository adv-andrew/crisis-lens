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
