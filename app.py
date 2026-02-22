"""
CrisisLens — Overlooked Crisis Index
=====================================
Streamlit entry point. Sets page config (the ONLY place this is called),
initializes session state, and renders the interactive HTML dashboard as
the home/landing view. Deeper analysis pages are accessible via the sidebar.
Chart NFT minting (same logic as mint_nfts.py) is integrated below.
"""

import json
import os
import subprocess
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# Chart NFT metadata URIs (Pinata IPFS) — same as mint_nfts.py
CHART_TOKEN_URIS = {
    "cluster_gaps": "https://gateway.pinata.cloud/ipfs/bafkreiaozmzhohbubvwsn3qkx6h7kxchszwawamjkehxhzq5ofa5y2ouei",
    "double_neglect_scatter": "https://gateway.pinata.cloud/ipfs/bafkreial62mpyuq2m43p7duzyjcymp5r26wfppiu2vcxk3yebccmrrxq6e",
    "efficiency_scatter": "https://gateway.pinata.cloud/ipfs/bafkreigsfgw7szapxmnnrt6xcrvfkdlh2lh2xi65drkn3es4cnp4jshnnq",
    "funding_forecast": "https://gateway.pinata.cloud/ipfs/bafkreigp3xhdgwgmumdhfysemvk36n3rpwqsace6p32d7tsbtdwmlwnhle",
    "top_10_crises": "https://gateway.pinata.cloud/ipfs/bafkreie3ptak7fzwofg77wfpqiow5feg565sm34ouxqzyzkk43hlll4tj4",
    "world_map": "https://gateway.pinata.cloud/ipfs/bafkreigdwsdh5yx2pbgo55xrxglryc3d5p77bf4rxcodp5cgiktrjsyfve",
}

CHART_DISPLAY_NAMES = {
    "world_map": "CrisisLens — World Map",
    "top_10_crises": "CrisisLens — Top 10 Crises",
    "double_neglect_scatter": "CrisisLens — Double Neglect Scatter",
    "cluster_gaps": "CrisisLens — Cluster Gaps",
    "funding_forecast": "CrisisLens — Funding Forecast",
    "efficiency_scatter": "CrisisLens — Efficiency Scatter",
}

# Paste the output of `python mint_nfts.py` here after running it (remotely or locally).
# Then the app will show "View on Solana" links instead of needing to mint from the app.
CHART_TOKEN_IDS = {}


def _mint_chart_token(name: str, uri: str) -> tuple[str | None, str]:
    """Run spl-token mint for one chart (same logic as mint_nfts.py). Returns (token_address, error_message)."""
    out = subprocess.getoutput("spl-token create-token --program-2022 --decimals 0 --enable-metadata")
    try:
        token_address = out.split("Creating token ")[1].split()[0]
    except IndexError:
        return None, out or "spl-token not found or failed"
    display = CHART_DISPLAY_NAMES.get(name, name)
    # Use list args to avoid shell escaping
    subprocess.run(["spl-token", "initialize-metadata", token_address, display, "CRISIS", uri], check=False)
    subprocess.run(["spl-token", "create-account", token_address], check=False)
    subprocess.run(["spl-token", "mint", token_address, "1"], check=False)
    subprocess.run(["spl-token", "authorize", token_address, "mint", "--disable"], check=False)
    return token_address, ""

st.set_page_config(
    page_title="CrisisLens — Overlooked Crisis Index",
    page_icon=":earth_americas:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "selected_iso3" not in st.session_state:
    st.session_state["selected_iso3"] = None


# --- Load and embed the HTML dashboard ---
@st.cache_data(ttl=3600)
def _build_dashboard_html():
    """Read index.html and inject OCI data inline so it works inside st.components."""
    html_path = Path("index.html")
    json_path = Path("data/processed/oci_frontend.json")

    if not html_path.exists():
        return None, "index.html not found"
    if not json_path.exists():
        return None, "data/processed/oci_frontend.json not found. Run: python utils/data_loader.py"

    html = html_path.read_text(encoding="utf-8")
    json_data = json_path.read_text(encoding="utf-8")

    # Replace the empty array with actual data
    html = html.replace("let OCI_DATA = [];", f"const OCI_DATA = {json_data};")

    # Replace the async fetch block with a simple loading-hide since data is already inline
    # The fetch block starts with "try {" and ends with the loading hide
    html = html.replace(
        """  try {
    const resp = await fetch('data/processed/oci_frontend.json');
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    OCI_DATA = await resp.json();
  } catch (e) {
    console.error('Failed to load OCI data:', e);
    document.getElementById('loading').querySelector('div:last-child').textContent = 'Failed to load crisis data. Run: python utils/data_loader.py';
    return;
  }""",
        "  // Data injected inline by Streamlit"
    )

    return html, None


html_content, error = _build_dashboard_html()

if error:
    st.warning("Dashboard unavailable.")
    st.info(error)
    st.stop()

# Render the full HTML dashboard
components.html(html_content, height=900, scrolling=False)

# --- Navigation hint ---
st.markdown(
    "<div style='text-align:center; color:#888; font-size:13px; margin-top:-10px'>"
    "Use the <b>sidebar</b> to access Crisis Drilldown, Efficiency Outliers, "
    "Project Recommender, and Funding Forecast."
    "</div>",
    unsafe_allow_html=True,
)

# --- Mint chart NFTs (integrated from mint_nfts.py) ---
with st.expander("Mint chart NFTs on Solana"):
    st.caption(
        "Mint the six CrisisLens chart images as Solana tokens (Token-2022). "
        "Run **`python mint_nfts.py`** (remotely or locally), then paste the printed "
        "**CHART_TOKEN_IDS** block into app.py above so the app shows links here."
    )
    if CHART_TOKEN_IDS:
        st.success("Minted tokens (paste from mint_nfts.py output):")
        for name, mint in CHART_TOKEN_IDS.items():
            display = CHART_DISPLAY_NAMES.get(name, name)
            st.markdown(
                f"**{display}** — [View on Solana](https://explorer.solana.com/address/{mint}) · `{mint}`"
            )
    else:
        st.info("No token IDs in app.py yet. Run `python mint_nfts.py`, then paste the printed CHART_TOKEN_IDS into app.py.")
    st.markdown("---")
    st.caption("Or mint from this app (requires spl-token and default keypair where Streamlit runs):")
    if st.button("Mint all chart NFTs", type="primary"):
        progress = st.progress(0, text="Minting...")
        n = len(CHART_TOKEN_URIS)
        results = []
        for i, (name, uri) in enumerate(CHART_TOKEN_URIS.items()):
            progress.progress((i + 1) / n, text=f"Minting {CHART_DISPLAY_NAMES.get(name, name)}...")
            token_addr, err = _mint_chart_token(name, uri)
            results.append((name, token_addr, err))
        progress.empty()
        for name, token_addr, err in results:
            display = CHART_DISPLAY_NAMES.get(name, name)
            if token_addr:
                st.success(f"**{display}** → [View](https://explorer.solana.com/address/{token_addr}) `{token_addr}`")
            else:
                st.error(f"**{display}**: {err}")
        st.caption("Paste the token addresses above into app.py as CHART_TOKEN_IDS so they persist.")
