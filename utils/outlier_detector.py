"""
CrisisLens Efficiency Outlier Detector
=======================================
Z-score analysis on beneficiary-to-budget ratios within each cluster.
Flags high-efficiency benchmarks and low-efficiency outliers.
"""

import pandas as pd
import numpy as np
from scipy.stats import zscore

MIN_CLUSTER_SIZE = 3  # minimum projects to compute meaningful z-score
OUTLIER_THRESHOLD = 2.0  # z-score threshold (not 3.0 — small cluster sizes)


def detect_efficiency_outliers(
    df_projects: pd.DataFrame,
    threshold: float = OUTLIER_THRESHOLD,
) -> pd.DataFrame:
    """
    Compute z-score of efficiency_ratio within each (cluster_name, year) group.
    Flag high_efficiency (z > threshold) and low_efficiency (z < -threshold).

    Parameters
    ----------
    df_projects : DataFrame with columns including
        project_code, country_iso3, year, cluster_name,
        budget_usd, beneficiaries_total, efficiency_ratio
    threshold : z-score cutoff for outlier flagging

    Returns
    -------
    DataFrame with added columns: zscore_efficiency, efficiency_flag, is_benchmark
    """
    df = df_projects.copy()

    df["zscore_efficiency"] = np.nan
    df["efficiency_flag"] = "normal"

    group_cols = ["cluster_name", "year"]

    for keys, group_idx in df.groupby(group_cols).groups.items():
        group = df.loc[group_idx]
        valid_mask = group["efficiency_ratio"].notna()
        valid_count = valid_mask.sum()

        if valid_count < MIN_CLUSTER_SIZE:
            df.loc[group_idx, "efficiency_flag"] = "insufficient_data"
            continue

        valid_indices = group_idx[valid_mask.values]
        ratios = group.loc[valid_mask, "efficiency_ratio"].values

        # Log1p transform: efficiency ratios are right-skewed
        log_ratios = np.log1p(ratios)

        # Z-score with sample std (ddof=1)
        std = np.std(log_ratios, ddof=1)
        if std == 0:
            continue
        mean = np.mean(log_ratios)
        z = (log_ratios - mean) / std

        df.loc[valid_indices, "zscore_efficiency"] = z

        # Flag outliers
        high_mask = z > threshold
        low_mask = z < -threshold
        df.loc[valid_indices[high_mask], "efficiency_flag"] = "high_efficiency"
        df.loc[valid_indices[low_mask], "efficiency_flag"] = "low_efficiency"

    # Benchmark tag
    df["is_benchmark"] = df["efficiency_flag"] == "high_efficiency"

    return df


def get_outlier_summary(df_flagged: pd.DataFrame) -> pd.DataFrame:
    """Return only outlier rows, sorted by absolute z-score descending."""
    outliers = df_flagged[df_flagged["efficiency_flag"].isin(["high_efficiency", "low_efficiency"])].copy()
    if outliers.empty:
        return outliers
    outliers["abs_z"] = outliers["zscore_efficiency"].abs()
    return outliers.sort_values("abs_z", ascending=False).drop(columns=["abs_z"])
