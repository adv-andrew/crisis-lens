"""
CrisisLens Data Loader
======================
ALL data loading and cleaning lives here. Pages import loader functions,
never read CSVs directly. Raw downloads cached in data/raw/, processed
outputs in data/processed/.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")

# ---------------------------------------------------------------------------
# Data source URLs
# ---------------------------------------------------------------------------
HNO_URLS = {
    2026: "https://data.humdata.org/dataset/8326ed53-8f3a-47f9-a2aa-83ab4ecee476/resource/edb91329-0e6b-4ebc-b6cb-051b2a11e536/download/hpc_hno_2026.csv",
    2025: "https://data.humdata.org/dataset/8326ed53-8f3a-47f9-a2aa-83ab4ecee476/resource/22093993-e23b-45c8-b84f-61e4a414ebbb/download/hpc_hno_2025.csv",
    2024: "https://data.humdata.org/dataset/8326ed53-8f3a-47f9-a2aa-83ab4ecee476/resource/8e3931a5-452b-4583-9d02-2247a34e397b/download/hpc_hno_2024.csv",
}

FTS_GLOBAL_URL = "https://data.humdata.org/dataset/b2bbb33c-2cfb-4809-8dd3-6bbdc080cbb9/resource/b3232da8-f1e4-41ab-9642-b22dae10a1d7/download/fts_requirements_funding_global.csv"

FTS_CLUSTER_URL = "https://data.humdata.org/dataset/b2bbb33c-2cfb-4809-8dd3-6bbdc080cbb9/resource/80975d5b-508b-47b2-a10c-b967104d3179/download/fts_requirements_funding_cluster_global.csv"

POP_URL = "https://data.humdata.org/dataset/27e3d1c6-c57a-4159-85a4-adb6b7aca6b9/resource/d4ea8fba-3d98-4d6e-85c8-84a5b0b4ebd9/download/cod_population_admin0.csv"

CBPF_URL = "https://cbpfapi.unocha.org/vo1/odata/ProjectSummary?ShowAllPooledFunds=1&$format=json"

# ---------------------------------------------------------------------------
# Column rename maps
# ---------------------------------------------------------------------------
HNO_COL_MAP = {
    "Country ISO3": "country_iso3",
    "Cluster": "cluster_code",
    "Category": "category",
    "Population": "population",
    "In Need": "people_in_need_raw",
    "Targeted": "people_targeted_raw",
    "Affected": "affected_raw",
    "Reached": "reached_raw",
    "Description": "description",
}

FTS_GLOBAL_COL_MAP = {
    "countryCode": "country_iso3",
    "year": "year",
    "name": "plan_name",
    "typeName": "plan_type",
    "requirements": "requirements_usd",
    "funding": "funding_usd",
    "percentFunded": "percent_funded",
}

FTS_CLUSTER_COL_MAP = {
    "countryCode": "country_iso3",
    "year": "year",
    "name": "plan_name",
    "cluster": "cluster_name",
    "clusterCode": "cluster_code_id",
    "requirements": "requirements_usd",
    "funding": "funding_usd",
    "percentFunded": "percent_funded",
}

CBPF_CLUSTER_KEYWORDS = {
    "Education": "Education",
    "Health": "Health",
    "Nutrition": "Nutrition",
    "Protection": "Protection",
    "Shelter": "Emergency Shelter and NFI",
    "WASH": "WASH",
    "Water": "WASH",
    "Sanitation": "WASH",
    "Food": "Food Security",
    "Agriculture": "Food Security",
    "Livelihoods": "Food Security",
    "Cash": "Multipurpose Cash",
    "Logistics": "Coordination and Common Services",
    "Coordination": "Coordination and Common Services",
    "Camp": "Camp Coordination and Camp Management",
    "Early Recovery": "Early Recovery",
    "Telecom": "Emergency Telecommunications",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _download(url: str, raw_path: Path, timeout: int = 120) -> bytes:
    """Download URL to raw_path if not cached. Return raw bytes."""
    if raw_path.exists():
        return raw_path.read_bytes()
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {raw_path.name} ...")
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    raw_path.write_bytes(resp.content)
    return resp.content


def _download_csv(
    url: str,
    raw_path: Path,
    skiprows=None,
    encoding: str = "utf-8",
) -> pd.DataFrame:
    """Download CSV and return DataFrame. Caches to raw_path."""
    _download(url, raw_path)
    return pd.read_csv(
        raw_path,
        skiprows=skiprows,
        encoding=encoding,
        low_memory=False,
        on_bad_lines="skip",
    )


def _to_numeric(series: pd.Series) -> pd.Series:
    """Convert series to numeric, handling commas and whitespace."""
    return pd.to_numeric(
        series.astype(str).str.replace(",", "").str.strip(),
        errors="coerce",
    )


def _infer_cluster(title: str) -> str:
    """Infer humanitarian cluster from project title keywords."""
    if pd.isna(title):
        return "Other"
    title_lower = str(title).lower()
    for keyword, cluster in CBPF_CLUSTER_KEYWORDS.items():
        if keyword.lower() in title_lower:
            return cluster
    return "Other"


# ---------------------------------------------------------------------------
# Public loaders — raw data
# ---------------------------------------------------------------------------
def load_hno() -> pd.DataFrame:
    """
    Load Humanitarian Needs Overview data for 2024-2026.
    Returns country-level aggregates: one row per (country_iso3, year).
    """
    frames = []
    for year, url in HNO_URLS.items():
        raw_path = RAW_DIR / f"hno_{year}.csv"
        try:
            df = _download_csv(url, raw_path, skiprows=[1])
            df = df.rename(columns=HNO_COL_MAP)
            df["year"] = year
            frames.append(df)
        except Exception as e:
            print(f"  Warning: HNO {year} failed: {e}")

    if not frames:
        raise RuntimeError("All HNO downloads failed")

    combined = pd.concat(frames, ignore_index=True)

    # Filter to country-level totals:
    #  - cluster_code == "ALL" (aggregate across all clusters)
    #  - category is empty/NaN (total, not demographic breakdown)
    mask_all = combined["cluster_code"].astype(str).str.strip().str.upper() == "ALL"
    mask_no_cat = combined["category"].isna() | (
        combined["category"].astype(str).str.strip() == ""
    )

    # For 2024/2025 files with admin columns, also filter to country-level
    if "Admin 1 PCode" in combined.columns:
        mask_country = combined["Admin 1 PCode"].isna() | (
            combined["Admin 1 PCode"].astype(str).str.strip() == ""
        )
    else:
        mask_country = pd.Series(True, index=combined.index)

    df_country = combined[mask_all & mask_no_cat & mask_country].copy()

    # Convert numeric columns
    for col in ["people_in_need_raw", "people_targeted_raw", "population"]:
        if col in df_country.columns:
            df_country[col] = _to_numeric(df_country[col])

    # To thousands (_k convention)
    df_country["people_in_need_k"] = df_country["people_in_need_raw"] / 1000
    df_country["people_targeted_k"] = df_country.get(
        "people_targeted_raw", pd.Series(dtype=float)
    ) / 1000

    # Deduplicate: one row per (country_iso3, year)
    df_country = df_country.sort_values("people_in_need_raw", ascending=False)
    df_country = df_country.drop_duplicates(subset=["country_iso3", "year"])

    # HNO does not include numeric severity — placeholder for OCI calc
    df_country["ocha_severity"] = np.nan

    return df_country[
        ["country_iso3", "year", "people_in_need_k", "people_targeted_k", "ocha_severity"]
    ].reset_index(drop=True)


def load_fts_global() -> pd.DataFrame:
    """
    Load FTS global requirements and funding data.
    Returns one row per (country_iso3, year) for HRP-type plans.
    """
    raw_path = RAW_DIR / "fts_global.csv"
    df = _download_csv(FTS_GLOBAL_URL, raw_path, skiprows=[1])
    df = df.rename(columns=FTS_GLOBAL_COL_MAP)

    # Filter to named plans (exclude bilateral/unattributed)
    df = df[df["plan_name"].notna() & (df["plan_name"].str.strip() != "")].copy()
    df = df[df["plan_name"] != "Not specified"].copy()

    # Convert numeric
    for col in ["requirements_usd", "funding_usd", "percent_funded"]:
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    df["year"] = _to_numeric(df["year"]).astype("Int64")

    # USD millions
    df["requirements_usd_m"] = df["requirements_usd"] / 1e6
    df["funding_usd_m"] = df["funding_usd"] / 1e6

    # Funding gap: 0 = fully funded, 1 = zero funded
    df["funding_gap"] = np.where(
        df["requirements_usd"].notna() & (df["requirements_usd"] > 0),
        1 - (df["funding_usd"].fillna(0) / df["requirements_usd"]),
        np.nan,
    )
    df["funding_gap"] = df["funding_gap"].clip(0, 1)

    # Deduplicate: keep largest-requirement plan per (country, year)
    df = df.sort_values("requirements_usd", ascending=False)
    df = df.drop_duplicates(subset=["country_iso3", "year"])

    return df[
        [
            "country_iso3", "year", "plan_name",
            "requirements_usd_m", "funding_usd_m", "funding_gap", "percent_funded",
        ]
    ].reset_index(drop=True)


def load_fts_cluster() -> pd.DataFrame:
    """
    Load FTS cluster-level funding data.
    Returns one row per (country_iso3, year, cluster_name).
    """
    raw_path = RAW_DIR / "fts_cluster.csv"
    df = _download_csv(FTS_CLUSTER_URL, raw_path, skiprows=[1])
    df = df.rename(columns=FTS_CLUSTER_COL_MAP)

    # Remove unspecified / multi-cluster rows
    df = df[
        df["cluster_name"].notna()
        & ~df["cluster_name"].isin(
            ["Not specified", "Multiple clusters/sectors (shared)"]
        )
    ].copy()

    for col in ["requirements_usd", "funding_usd", "percent_funded"]:
        if col in df.columns:
            df[col] = _to_numeric(df[col])

    df["year"] = _to_numeric(df["year"]).astype("Int64")
    df["requirements_usd_m"] = df["requirements_usd"] / 1e6
    df["funding_usd_m"] = df["funding_usd"] / 1e6

    df["funding_gap"] = np.where(
        df["requirements_usd"].notna() & (df["requirements_usd"] > 0),
        1 - (df["funding_usd"].fillna(0) / df["requirements_usd"]),
        np.nan,
    )
    df["funding_gap"] = df["funding_gap"].clip(0, 1)

    return df[
        [
            "country_iso3", "year", "cluster_name",
            "requirements_usd_m", "funding_usd_m", "funding_gap", "percent_funded",
        ]
    ].reset_index(drop=True)


def load_population() -> pd.DataFrame:
    """
    Load COD-PS country-level population totals.
    Returns one row per country_iso3 with total_population.
    """
    raw_path = RAW_DIR / "population_admin0.csv"
    df = _download_csv(POP_URL, raw_path, encoding="utf-8-sig")

    # Handle BOM in column name
    df.columns = [c.replace("\ufeff", "").strip() for c in df.columns]
    df = df.rename(columns={"ISO3": "country_iso3"})

    # Filter to total population rows
    if "Population_group" in df.columns:
        df_total = df[df["Population_group"] == "T_TL"].copy()
    else:
        # Fallback: sum all rows per country
        df_total = df.copy()

    df_total["Population"] = _to_numeric(df_total["Population"])
    df_total["Reference_year"] = _to_numeric(df_total["Reference_year"])

    # Take most recent year per country
    df_total = df_total.sort_values("Reference_year", ascending=False)
    df_total = df_total.drop_duplicates(subset=["country_iso3"])

    return df_total[["country_iso3", "Population"]].rename(
        columns={"Population": "total_population"}
    ).reset_index(drop=True)


def load_cbpf_projects() -> pd.DataFrame:
    """
    Load CBPF project-level data from OData API.
    Returns project-level budget and beneficiary data (2020+).
    """
    raw_path = RAW_DIR / "cbpf_projects.json"
    _download(CBPF_URL, raw_path, timeout=180)

    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = data.get("value", data) if isinstance(data, dict) else data
    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame()

    # Extract ISO3 from project code (first 3 chars)
    if "ChfProjectCode" in df.columns:
        df["country_iso3"] = df["ChfProjectCode"].str[:3].str.upper()
    else:
        df["country_iso3"] = np.nan

    # Total beneficiaries
    for col in ["Men", "Women", "Boys", "Girls"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0
    df["beneficiaries_total"] = df["Men"] + df["Women"] + df["Boys"] + df["Girls"]

    # Rename columns
    rename_map = {
        "AllocationYear": "year",
        "Budget": "budget_usd",
        "PooledFundName": "pooled_fund_name",
        "OrganizationType": "org_type",
        "OrganizationName": "org_name",
        "ProjectTitle": "project_title",
        "AllocationType": "allocation_type",
        "ProjectStatus": "project_status",
        "ChfProjectCode": "project_code",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    df["budget_usd"] = pd.to_numeric(df.get("budget_usd", pd.Series(dtype=float)), errors="coerce")
    df["year"] = pd.to_numeric(df.get("year", pd.Series(dtype=float)), errors="coerce")

    # Filter to recent years with positive budget
    df = df[(df["year"] >= 2020) & df["budget_usd"].notna() & (df["budget_usd"] > 0)].copy()

    # Efficiency ratio
    df["efficiency_ratio"] = np.where(
        (df["beneficiaries_total"] > 0) & (df["budget_usd"] > 0),
        df["beneficiaries_total"] / df["budget_usd"],
        np.nan,
    )

    # Infer cluster from project title
    df["cluster_name"] = df["project_title"].apply(_infer_cluster)

    output_cols = [
        "project_code", "country_iso3", "year", "pooled_fund_name",
        "cluster_name", "budget_usd", "beneficiaries_total",
        "efficiency_ratio", "org_type", "org_name", "project_title",
        "allocation_type", "project_status",
    ]
    return df[[c for c in output_cols if c in df.columns]].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Public loaders — processed data (for Streamlit pages)
# ---------------------------------------------------------------------------
def load_oci_scores() -> pd.DataFrame:
    """Load pre-computed OCI scores from processed CSV."""
    path = PROC_DIR / "oci_scores.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_projects_clean() -> pd.DataFrame:
    """Load cleaned CBPF project data from processed CSV."""
    path = PROC_DIR / "projects_clean.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def load_funding_clean() -> pd.DataFrame:
    """Load cleaned FTS funding data from processed CSV."""
    path = PROC_DIR / "funding_clean.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Full pipeline orchestrator
# ---------------------------------------------------------------------------
def run_full_pipeline():
    """Download all raw data, compute OCI, save processed files."""
    from utils.oci_calculator import compute_oci_scores

    print("=" * 60)
    print("CrisisLens Data Pipeline")
    print("=" * 60)

    print("\n[1/5] Loading HNO data...")
    df_hno = load_hno()
    print(f"  -> {len(df_hno)} country-year rows")

    print("\n[2/5] Loading FTS global funding...")
    df_fts = load_fts_global()
    print(f"  -> {len(df_fts)} country-year rows")

    print("\n[3/5] Loading population data...")
    df_pop = load_population()
    print(f"  -> {len(df_pop)} countries")

    print("\n[4/5] Loading CBPF project data...")
    df_cbpf = load_cbpf_projects()
    print(f"  -> {len(df_cbpf)} projects")

    print("\n[5/5] Computing OCI scores...")
    df_oci = compute_oci_scores(df_hno, df_fts, df_pop)
    print(f"  -> {len(df_oci)} scored crises")

    # Save processed outputs
    PROC_DIR.mkdir(parents=True, exist_ok=True)

    df_oci.to_csv(PROC_DIR / "oci_scores.csv", index=False)
    print(f"\n  Saved oci_scores.csv ({len(df_oci)} rows)")

    df_fts.to_csv(PROC_DIR / "funding_clean.csv", index=False)
    print(f"  Saved funding_clean.csv ({len(df_fts)} rows)")

    df_cbpf.to_csv(PROC_DIR / "projects_clean.csv", index=False)
    print(f"  Saved projects_clean.csv ({len(df_cbpf)} rows)")

    # Print top 5 most overlooked
    if not df_oci.empty and "oci_score" in df_oci.columns:
        print("\n" + "=" * 60)
        print("Top 5 Most Overlooked Crises:")
        print("=" * 60)
        top5 = df_oci.nlargest(5, "oci_score")
        for _, row in top5.iterrows():
            name = row.get("country_name") or row["country_iso3"]
            print(f"  {name}: OCI={row['oci_score']:.4f} (rank #{row.get('oci_rank', '?')})")

    print("\nPipeline complete.")


if __name__ == "__main__":
    import sys
    from pathlib import Path as _P
    sys.path.insert(0, str(_P(__file__).resolve().parent.parent))
    run_full_pipeline()
