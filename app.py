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

# --- OCHA-style custom CSS to match index.html theme ---
st.markdown("""
<style>
/* Import Roboto fonts to match index.html */
@import url('https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@400;700&family=Roboto:wght@300;400;500;700&display=swap');

/* Root variables matching index.html */
:root {
    --ocha-blue: #002856;
    --ocha-blue-mid: #1f69b3;
    --ocha-blue-bright: #82b5e9;
    --red: #cd3a1f;
    --highlight-red: #e56a54;
    --orange: #ff7a00;
    --green: #7fb92f;
    --grey-dark: #4a4a4a;
    --grey-light: #f2f2f2;
    --border: #d4d4d4;
    --white: #ffffff;
}

/* Global font override */
html, body, [class*="css"] {
    font-family: 'Roboto', helvetica, arial, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

/* Main content area */
.stMain {
    background: var(--grey-light);
}

/* Sidebar styling — white background with navy accents */
section[data-testid="stSidebar"] {
    background: var(--white) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Roboto Condensed', helvetica, arial, sans-serif !important;
    color: var(--grey-dark) !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-size: 13px !important;
}

/* Headers — Roboto Condensed like OCHA */
h1, h2, h3 {
    font-family: 'Roboto Condensed', helvetica, arial, sans-serif !important;
    color: var(--grey-dark) !important;
}

/* Metric cards — white cards with subtle shadow */
div[data-testid="stMetric"] {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
div[data-testid="stMetric"] label {
    font-family: 'Roboto Condensed', helvetica, arial, sans-serif !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--grey-dark) !important;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    font-family: 'Roboto Condensed', helvetica, arial, sans-serif !important;
    font-weight: 700 !important;
    color: var(--ocha-blue) !important;
}

/* Data tables */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
}

/* Buttons — OCHA navy style */
.stButton > button {
    background: var(--ocha-blue) !important;
    color: white !important;
    border: none !important;
    border-radius: 3px !important;
    font-family: 'Roboto', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
.stButton > button:hover {
    background: var(--ocha-blue-mid) !important;
}

/* Selectbox and slider styling */
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stMultiSelect"] label {
    font-family: 'Roboto', sans-serif !important;
    font-size: 12px !important;
    color: var(--grey-dark) !important;
    font-weight: 500;
}

/* Alert boxes — match OCHA palette */
div[data-testid="stAlert"] {
    border-radius: 3px !important;
}

/* Expander styling */
details {
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    background: var(--white) !important;
}
details summary {
    font-family: 'Roboto Condensed', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

/* Page links */
a {
    color: var(--ocha-blue-mid) !important;
}

/* Tabs styling */
button[data-baseweb="tab"] {
    font-family: 'Roboto Condensed', sans-serif !important;
    text-transform: uppercase;
    font-size: 12px !important;
    letter-spacing: 0.5px;
}

/* Plotly chart containers */
div[data-testid="stPlotlyChart"] {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 8px;
}

/* Caption text */
.stCaption, div[data-testid="stCaptionContainer"] {
    font-size: 12px !important;
    color: #646464 !important;
}

/* Radio buttons */
div[data-testid="stRadio"] label {
    font-size: 13px !important;
}

/* Separator lines */
hr {
    border-color: var(--border) !important;
}
</style>
""", unsafe_allow_html=True)


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
    "<div style='text-align:center; color:#646464; font-size:12px; margin-top:-10px;"
    "font-family:Roboto,sans-serif'>"
    "Use the <b>sidebar</b> to access Crisis Drilldown, Efficiency Outliers, "
    "Project Recommender, Funding Forecast, and Reallocation Simulator."
    "</div>",
    unsafe_allow_html=True,
)
