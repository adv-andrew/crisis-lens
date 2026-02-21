#!/usr/bin/env python3
"""
Upload nft_images/ to Pinata (IPFS) and optionally create metadata JSONs for minting.

Setup:
  1. Sign up at https://pinata.cloud and create an API key (JWT).
  2. Set PINATA_JWT in .env or environment.

Usage:
  From repo root:  python scripts/upload_nft_images_to_pinata.py
  From crisis-lens: python scripts/upload_nft_images_to_pinata.py

  Uses nft_images/ next to the notebook (notebooks/nft_images) or in cwd.
"""

import json
import os
import sys
from pathlib import Path

import requests

# Try to find nft_images: notebooks/nft_images (when run from crisis-lens) or ./nft_images
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CANDIDATES = [
    REPO_ROOT / "notebooks" / "nft_images",
    REPO_ROOT / "nft_images",
    Path.cwd() / "nft_images",
    Path.cwd() / "notebooks" / "nft_images",
]

UPLOAD_URL = "https://uploads.pinata.cloud/v3/files"

# Chart filename -> (display name, description) for metadata
CHART_META = {
    "world_map.png": (
        "CrisisLens — OCI World Map",
        "Overlooked Crisis Index choropleth by country. Higher = more overlooked.",
    ),
    "top_10_crises.png": (
        "CrisisLens — Top 10 Overlooked Crises",
        "Bar chart of most overlooked crises and OCI component breakdown.",
    ),
    "double_neglect_scatter.png": (
        "CrisisLens — Double Neglect Scatter",
        "Media neglect vs funding gap. Upper-right = most overlooked.",
    ),
    "cluster_gaps.png": (
        "CrisisLens — Cluster Funding Gaps",
        "Cluster-level average funding gaps (WASH, Health, Food Security, etc.).",
    ),
    "funding_forecast.png": (
        "CrisisLens — Funding Gap Forecast",
        "Top 3 at-risk crises: funding gap trend with 90% prediction interval.",
    ),
    "efficiency_scatter.png": (
        "CrisisLens — Project Efficiency",
        "CBPF budget vs beneficiaries; high-efficiency benchmarks highlighted.",
    ),
}


def find_nft_images_dir() -> Path | None:
    for p in CANDIDATES:
        if p.is_dir():
            return p
    return None


def upload_file(path: Path, jwt: str, network: str = "public") -> str:
    """Upload a single file to Pinata; return CID."""
    with open(path, "rb") as f:
        files = {"file": (path.name, f)}
        data = {"network": network}
        resp = requests.post(
            UPLOAD_URL,
            headers={"Authorization": f"Bearer {jwt}"},
            files=files,
            data=data,
            timeout=60,
        )
    resp.raise_for_status()
    out = resp.json()
    cid = out.get("data", {}).get("cid")
    if not cid:
        raise RuntimeError(f"Pinata response missing cid: {out}")
    return cid


def main() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv(REPO_ROOT / ".env")
        load_dotenv(Path.cwd() / ".env")
    except ImportError:
        pass

    jwt = os.environ.get("PINATA_JWT", "").strip()
    if not jwt:
        print("Set PINATA_JWT in .env or environment (get a JWT from https://pinata.cloud).", file=sys.stderr)
        sys.exit(1)

    nft_dir = find_nft_images_dir()
    if not nft_dir:
        print("No nft_images/ folder found. Run the full_pipeline notebook first to export charts.", file=sys.stderr)
        sys.exit(1)

    pngs = sorted(nft_dir.glob("*.png"))
    if not pngs:
        print(f"No PNGs in {nft_dir}. Run the notebook to export charts.", file=sys.stderr)
        sys.exit(1)

    gateway = "https://gateway.pinata.cloud/ipfs"
    results = []

    for path in pngs:
        name = path.name
        if name not in CHART_META:
            print(f"  Skipping unknown chart: {name}")
            continue
        title, description = CHART_META[name]

        print(f"  Uploading {name}...", end=" ", flush=True)
        try:
            image_cid = upload_file(path, jwt)
            image_uri = f"{gateway}/{image_cid}"
        except Exception as e:
            print(f"Failed: {e}")
            continue
        print(f"CID {image_cid}")

        metadata = {
            "name": title,
            "description": description,
            "image": image_uri,
            "attributes": [
                {"trait_type": "Chart Type", "value": name.replace(".png", "").replace("_", " ").title()},
                {"trait_type": "Source", "value": "CrisisLens"},
            ],
        }
        # Upload metadata JSON (as a virtual file)
        print(f"  Uploading metadata for {name}...", end=" ", flush=True)
        try:
            json_bytes = json.dumps(metadata, indent=2).encode("utf-8")
            meta_name = name.replace(".png", ".json")
            files = {"file": (meta_name, json_bytes, "application/json")}
            data = {"network": "public"}
            resp = requests.post(
                UPLOAD_URL,
                headers={"Authorization": f"Bearer {jwt}"},
                files=files,
                data=data,
                timeout=30,
            )
            resp.raise_for_status()
            meta_cid = resp.json().get("data", {}).get("cid")
            if not meta_cid:
                raise RuntimeError("No cid in metadata upload response")
            metadata_uri = f"{gateway}/{meta_cid}"
            print(f"CID {meta_cid}")
            results.append((name, image_uri, metadata_uri))
        except Exception as e:
            print(f"Failed: {e}")

    if not results:
        print("No files uploaded.")
        return

    print("\n" + "=" * 60)
    print("Upload complete. Use these metadata URIs for minting:")
    print("=" * 60)
    for name, img_uri, meta_uri in results:
        print(f"  {name}\n    {meta_uri}")
    print("\nSingle base URL for all metadata (if your minter uses filename.json):")
    print("  Not applicable — each metadata has its own CID above.")
    print("\nFor Solana minting, set each NFT's URI to the metadata URI above,")
    print("or use a script that loops over these URIs.")


if __name__ == "__main__":
    main()
