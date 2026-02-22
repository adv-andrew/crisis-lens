"""
CrisisLens — Overlooked Crisis Index
=====================================
Streamlit entry point. Sets page config (the ONLY place this is called),
initializes session state, and renders the interactive HTML dashboard as
the home/landing view. Deeper analysis pages are accessible via the sidebar.
"""

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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
