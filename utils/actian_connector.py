"""
CrisisLens Actian VectorAI DB Connector
========================================
Sponsor challenge integration for the Actian VectorAI DB.
Docker: docker pull williamimoh/actian-vectorai-db:1.0b

All Actian DB interactions go through this module.
If Actian is unavailable, callers fall back to similarity_engine.py (sklearn).
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

ACTIAN_HOST = os.getenv("ACTIAN_HOST", "localhost")
ACTIAN_PORT = os.getenv("ACTIAN_PORT", "5432")
ACTIAN_BASE_URL = f"http://{ACTIAN_HOST}:{ACTIAN_PORT}"


def _check_actian_available() -> bool:
    """Ping Actian endpoint. Returns True if reachable."""
    try:
        resp = requests.get(f"{ACTIAN_BASE_URL}/health", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def upsert_project_vectors(df_projects: pd.DataFrame) -> bool:
    """
    Store project feature vectors in Actian VectorAI DB.
    Returns True on success, False on failure.
    """
    if not _check_actian_available():
        return False

    try:
        from utils.similarity_engine import build_feature_matrix

        X, enc, scaler, df_feat = build_feature_matrix(df_projects)
        X_dense = X.toarray().tolist()

        records = []
        for i, (_, row) in enumerate(df_feat.iterrows()):
            records.append({
                "id": row.get("project_code", str(i)),
                "vector": X_dense[i],
                "metadata": {
                    "country_iso3": str(row.get("country_iso3", "")),
                    "cluster_name": str(row.get("cluster_name", "")),
                    "budget_usd": float(row.get("budget_usd", 0) or 0),
                    "beneficiaries_total": float(row.get("beneficiaries_total", 0) or 0),
                    "project_title": str(row.get("project_title", "")),
                    "efficiency_ratio": float(row.get("efficiency_ratio", 0) or 0),
                },
            })

        resp = requests.post(
            f"{ACTIAN_BASE_URL}/vectors/upsert",
            json={"collection": "hrp_projects", "records": records},
            timeout=30,
        )
        return resp.status_code == 200
    except Exception:
        return False


def search_similar_projects(
    project_code: str,
    top_n: int = 5,
) -> pd.DataFrame | None:
    """
    Query Actian for nearest neighbors to project_code.
    Returns DataFrame or None if Actian unavailable.
    """
    if not _check_actian_available():
        return None

    try:
        resp = requests.post(
            f"{ACTIAN_BASE_URL}/vectors/search",
            json={
                "collection": "hrp_projects",
                "query_id": project_code,
                "top_k": top_n,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return None

        results = resp.json().get("results", [])
        if not results:
            return None

        return pd.DataFrame([
            {
                "project_code": r["id"],
                "similarity_score": r.get("score", 0),
                **r.get("metadata", {}),
            }
            for r in results
        ])
    except Exception:
        return None
