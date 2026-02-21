"""
CrisisLens OCI Calculator
=========================
Computes the Overlooked Crisis Index (OCI) per country-year.

Formula (DO NOT MODIFY without being explicitly asked):
    severity_weight = ocha_severity / 5.0
    pin_normalized  = people_in_need / total_population
    funding_gap     = 1 - (actual_funding / total_requirements)
    OCI = pin_normalized * severity_weight * funding_gap
    (media layer omitted — no GDELT data available)

OCI is normalized 0-1 across all crises. Higher = more overlooked.
"""

import numpy as np
import pandas as pd


def compute_oci_scores(
    df_hno: pd.DataFrame,
    df_fts: pd.DataFrame,
    df_pop: pd.DataFrame,
) -> pd.DataFrame:
    """
    Join HNO + FTS + Population and compute OCI per country-year.

    Parameters
    ----------
    df_hno : DataFrame with columns [country_iso3, year, people_in_need_k, ocha_severity]
    df_fts : DataFrame with columns [country_iso3, year, plan_name, requirements_usd_m,
             funding_usd_m, funding_gap]
    df_pop : DataFrame with columns [country_iso3, total_population]

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

    # ----- OCI component: severity_weight -----
    # HNO lacks numeric severity; default to 5.0 (max) for all HRP crises
    df["ocha_severity"] = df["ocha_severity"].fillna(5.0)
    df["severity_weight"] = (df["ocha_severity"] / 5.0).clip(0, 1)

    # ----- OCI component: pin_normalized -----
    # people_in_need_k is in thousands; total_population is in units
    df["people_in_need"] = df["people_in_need_k"] * 1000
    df["pin_normalized"] = np.where(
        df["total_population"].notna() & (df["total_population"] > 0),
        df["people_in_need"] / df["total_population"],
        np.nan,
    )
    df["pin_normalized"] = df["pin_normalized"].clip(0, 1)

    # ----- OCI component: funding_gap -----
    # Already computed in data_loader; fill missing with 0.5 (unknown)
    df["has_funding_data"] = df["funding_gap"].notna()
    df["funding_gap"] = pd.to_numeric(df["funding_gap"], errors="coerce").fillna(0.5)

    # ----- OCI raw score -----
    df["oci_raw"] = df["pin_normalized"] * df["severity_weight"] * df["funding_gap"]

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

    # ----- Extract country name from plan_name -----
    def _extract_country_name(plan_name):
        if pd.isna(plan_name):
            return None
        s = str(plan_name)
        # Plan names are like "Afghanistan Humanitarian Needs and Response Plan 2026"
        for marker in ["Humanitarian", "humanitarian", "HRP", "Flash Appeal"]:
            idx = s.find(marker)
            if idx > 0:
                return s[:idx].strip().rstrip("-").strip()
        return s.split(" ")[0] if " " in s else None

    df["country_name"] = df["plan_name"].apply(_extract_country_name)

    # ----- Select output columns -----
    output_cols = [
        "country_iso3", "year", "country_name", "plan_name",
        "people_in_need_k", "people_targeted_k",
        "total_population",
        "requirements_usd_m", "funding_usd_m",
        "pin_normalized", "severity_weight", "funding_gap",
        "oci_raw", "oci_score", "oci_rank",
        "has_funding_data", "ocha_severity",
    ]

    return df[[c for c in output_cols if c in df.columns]].reset_index(drop=True)
