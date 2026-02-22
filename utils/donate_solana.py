"""
Solana donation flow: one treasury address, memo = country ISO3 for attribution.
Set TREASURY_SOLANA_ADDRESS in .env or Streamlit secrets.
"""

import os
from pathlib import Path


def get_treasury_address():
    """Treasury Solana address from .env or st.secrets. Empty string if not set."""
    try:
        from dotenv import load_dotenv
        for p in [Path.cwd() / ".env", Path(__file__).resolve().parent.parent / ".env"]:
            if p.exists():
                load_dotenv(p)
                break
    except ImportError:
        pass
    addr = (os.environ.get("TREASURY_SOLANA_ADDRESS") or "").strip()
    try:
        import streamlit as st
        if not addr and hasattr(st, "secrets") and st.secrets:
            addr = (st.secrets.get("TREASURY_SOLANA_ADDRESS") or "").strip()
    except Exception:
        pass
    return addr


# Fake address for demo when no treasury configured
MOCK_TREASURY_ADDRESS = "Demo111111111111111111111111111111111111111111"

def render_donate_solana(iso3: str, country_name: str, *, compact: bool = False):
    """
    Render the "Donate SOL" UI for one country: address, memo, links.
    When treasury is not set, shows same UI and a "Simulate donation" button for demo.
    """
    import streamlit as st

    treasury = get_treasury_address()
    is_mock = not treasury
    if is_mock:
        treasury = MOCK_TREASURY_ADDRESS

    memo = iso3

    if compact:
        st.caption("Donate SOL to this crisis (attributed via memo)")
    else:
        st.subheader("Donate SOL to this crisis")

    st.markdown(
        f"Send **SOL** to the CrisisLens treasury with memo **`{memo}`** so your donation "
        f"is attributed to **{country_name}**."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Treasury address (send SOL here)", treasury, key=f"donate_addr_{iso3}", disabled=True)
    with col2:
        st.text_input("Memo (required for attribution)", memo, key=f"donate_memo_{iso3}", disabled=True)

    if is_mock:
        if st.button("Simulate donation", key=f"donate_sim_{iso3}"):
            st.success(f"Thank you! Donation attributed to **{country_name}** ({memo}). (Demo — no SOL was sent.)")
    else:
        explorer_send = f"https://explorer.solana.com/address/{treasury}"
        st.link_button("Open address in Solana Explorer", explorer_send)

    solana_uri = f"solana:{treasury}?memo={memo}"
    st.caption(f"Wallet link: `solana:{treasury}?memo={memo}` — paste in Phantom/Solflare to pre-fill recipient and memo.")
