"""
Upload JSON metadata to Pinata (IPFS) for Solana tokenization.
Used by the Overview Map country tokenize flow and by mint_nfts/upload scripts.
"""

import json
import os
from pathlib import Path

UPLOAD_URL = "https://uploads.pinata.cloud/v3/files"
GATEWAY = "https://gateway.pinata.cloud/ipfs"


def upload_json_to_pinata(metadata: dict, filename: str, jwt: str, network: str = "public") -> str:
    """
    Upload a JSON metadata dict to Pinata; return the gateway URI (ipfs://... style not used, we return https).
    """
    import requests

    json_bytes = json.dumps(metadata, indent=2).encode("utf-8")
    files = {"file": (filename, json_bytes, "application/json")}
    data = {"network": network}
    resp = requests.post(
        UPLOAD_URL,
        headers={"Authorization": f"Bearer {jwt}"},
        files=files,
        data=data,
        timeout=30,
    )
    resp.raise_for_status()
    cid = resp.json().get("data", {}).get("cid")
    if not cid:
        raise RuntimeError("Pinata response missing cid")
    return f"{GATEWAY}/{cid}"


def get_pinata_jwt() -> str:
    """Load PINATA_JWT from .env or environment."""
    try:
        from dotenv import load_dotenv
        for p in [Path.cwd() / ".env", Path(__file__).resolve().parent.parent / ".env"]:
            if p.exists():
                load_dotenv(p)
                break
    except ImportError:
        pass
    return (os.environ.get("PINATA_JWT") or "").strip()
