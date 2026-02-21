"""
CrisisLens OCI Calculator
=========================
Computes the Overlooked Crisis Index (OCI) per country-year.

Formula:
    severity_weight = ocha_severity / 5.0
    pin_normalized  = people_in_need / total_population
    funding_gap     = 1 - (actual_funding / total_requirements)
    media_score     = 1 - normalized_search_interest  (0=high coverage, 1=ignored)

    OCI = (pin_normalized * severity_weight * funding_gap) * (1 + media_score * 0.2)

OCI is normalized 0-1 across all crises. Higher = more overlooked.
"""

import numpy as np
import pandas as pd


def compute_oci_scores(
    df_hno: pd.DataFrame,
    df_fts: pd.DataFrame,
    df_pop: pd.DataFrame,
    df_media: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Join HNO + FTS + Population + Media and compute OCI per country-year.

    Parameters
    ----------
    df_hno : DataFrame with columns [country_iso3, year, people_in_need_k, ocha_severity]
    df_fts : DataFrame with columns [country_iso3, year, plan_name, requirements_usd_m,
             funding_usd_m, funding_gap]
    df_pop : DataFrame with columns [country_iso3, total_population]
    df_media : DataFrame with columns [country_iso3, media_score] (optional)

    Returns
    -------
    DataFrame with OCI scores and all intermediate components.
    """
    # Start from HNO as base
    df = df_hno.copy()

    # LEFT JOIN FTS global funding
    fts_cols = ["country_iso3", "year", "plan_name", "requirements_usd_m",
                "funding_usd_m", "funding_gap", "percent_funded"]
    fts_available = [c for c in fts_cols if c in df_fts.columns]
    df = df.merge(df_fts[fts_available], on=["country_iso3", "year"], how="left")

    # LEFT JOIN population (static — no year dimension)
    df = df.merge(df_pop[["country_iso3", "total_population"]], on="country_iso3", how="left")

    # LEFT JOIN media scores (static — no year dimension)
    if df_media is not None and not df_media.empty and "media_score" in df_media.columns:
        media_cols = ["country_iso3", "media_score"]
        if "media_raw" in df_media.columns:
            media_cols.append("media_raw")
        df = df.merge(df_media[media_cols], on="country_iso3", how="left")
        df["media_score"] = df["media_score"].fillna(0.5)  # unknown = neutral
    else:
        df["media_score"] = 0.0  # no media data = don't penalize

    # ----- OCI component: severity_weight -----
    # HNO CSVs lack numeric severity. Derive a proxy from PIN/population
    # ratio using quantile binning into OCHA's 1-5 scale.
    df["_pin_pop_ratio"] = np.where(
        df["total_population"].notna() & (df["total_population"] > 0),
        (df["people_in_need_k"] * 1000) / df["total_population"],
        np.nan,
    )
    # Quantile-based severity: higher ratio → higher severity
    valid_ratio = df["_pin_pop_ratio"].dropna()
    if len(valid_ratio) >= 5:
        bins = [0] + valid_ratio.quantile([0.2, 0.4, 0.6, 0.8]).tolist() + [float("inf")]
        labels = [1, 2, 3, 4, 5]
        df["derived_severity"] = pd.cut(
            df["_pin_pop_ratio"], bins=bins, labels=labels, include_lowest=True,
        ).astype(float)
    else:
        df["derived_severity"] = 3.0

    # Use real OCHA severity if available, otherwise derived
    df["ocha_severity"] = df["ocha_severity"].fillna(df["derived_severity"]).fillna(3.0)
    df["severity_weight"] = (df["ocha_severity"] / 5.0).clip(0, 1)
    df = df.drop(columns=["_pin_pop_ratio", "derived_severity"])

    # ----- OCI component: pin_normalized -----
    df["people_in_need"] = df["people_in_need_k"] * 1000
    df["pin_normalized"] = np.where(
        df["total_population"].notna() & (df["total_population"] > 0),
        df["people_in_need"] / df["total_population"],
        np.nan,
    )
    df["pin_normalized"] = df["pin_normalized"].clip(0, 1)

    # ----- OCI component: funding_gap -----
    df["has_funding_data"] = df["funding_gap"].notna()
    df["funding_gap"] = pd.to_numeric(df["funding_gap"], errors="coerce").fillna(0.5).clip(0, 1)

    # ----- OCI raw score with media multiplier -----
    base_oci = df["pin_normalized"] * df["severity_weight"] * df["funding_gap"]
    df["oci_raw"] = base_oci * (1 + df["media_score"] * 0.2)

    # Countries with no population data get NaN pin_normalized -> oci_raw = 0
    df["oci_raw"] = pd.to_numeric(df["oci_raw"], errors="coerce").fillna(0)

    # ----- Normalize OCI to [0, 1] -----
    oci_min = df["oci_raw"].min()
    oci_max = df["oci_raw"].max()
    if oci_max > oci_min:
        df["oci_score"] = (df["oci_raw"] - oci_min) / (oci_max - oci_min)
    else:
        df["oci_score"] = 0.0

    df["oci_score"] = df["oci_score"].round(4)

    # ----- Rank (1 = most overlooked) -----
    df["oci_rank"] = df["oci_score"].rank(ascending=False, method="min").astype("Int64")

    # ----- Country name lookup (ISO3 → display name) -----
    _ISO3_NAMES = {
        "AFG": "Afghanistan", "BFA": "Burkina Faso", "CAF": "Central African Republic",
        "CMR": "Cameroon", "COD": "DR Congo", "COL": "Colombia",
        "ETH": "Ethiopia", "GTM": "Guatemala", "HTI": "Haiti",
        "HND": "Honduras", "IRQ": "Iraq", "LBN": "Lebanon",
        "LBY": "Libya", "MLI": "Mali", "MMR": "Myanmar",
        "MOZ": "Mozambique", "NER": "Niger", "NGA": "Nigeria",
        "PSE": "Palestine", "SDN": "Sudan", "SLV": "El Salvador",
        "SOM": "Somalia", "SSD": "South Sudan", "SYR": "Syria",
        "TCD": "Chad", "UKR": "Ukraine", "VEN": "Venezuela",
        "YEM": "Yemen", "ZWE": "Zimbabwe",
    }

    def _extract_country_name(row):
        iso3 = row.get("country_iso3")
        if iso3 in _ISO3_NAMES:
            return _ISO3_NAMES[iso3]
        plan_name = row.get("plan_name")
        if pd.isna(plan_name):
            return iso3
        s = str(plan_name)
        for marker in ["Humanitarian", "humanitarian", "HRP", "Flash Appeal",
                        "Besoins", "besoins", "Necesidades", "necesidades",
                        "Plan de Respuesta", "Plan de Réponse"]:
            idx = s.find(marker)
            if idx > 0:
                return s[:idx].strip().rstrip("-").strip()
        return s.split(" ")[0] if " " in s else iso3

    df["country_name"] = df.apply(_extract_country_name, axis=1)

    # ----- Select output columns -----
    output_cols = [
        "country_iso3", "year", "country_name", "plan_name",
        "people_in_need_k", "people_targeted_k",
        "total_population",
        "requirements_usd_m", "funding_usd_m",
        "pin_normalized", "severity_weight", "funding_gap",
        "media_score",
        "oci_raw", "oci_score", "oci_rank",
        "has_funding_data", "ocha_severity",
    ]

    return df[[c for c in output_cols if c in df.columns]].reset_index(drop=True)
