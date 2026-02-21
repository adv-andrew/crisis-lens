"""
edge case tests for core utils
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.oci_calculator import compute_oci_scores
from utils.outlier_detector import detect_efficiency_outliers
from utils.similarity_engine import build_feature_matrix, get_similar_projects


def test_oci_single_crisis():
    """should handle a single crisis without division by zero"""
    hno = pd.DataFrame({
        "country_iso3": ["SSD"],
        "year": [2025],
        "people_in_need_k": [9000.0],
        "people_targeted_k": [5000.0],
        "ocha_severity": [np.nan],
    })
    fts = pd.DataFrame({
        "country_iso3": ["SSD"],
        "year": [2025],
        "plan_name": ["South Sudan HRP"],
        "requirements_usd_m": [1800.0],
        "funding_usd_m": [300.0],
        "funding_gap": [0.83],
        "percent_funded": [17.0],
    })
    pop = pd.DataFrame({
        "country_iso3": ["SSD"],
        "total_population": [11000000],
    })
    result = compute_oci_scores(hno, fts, pop)
    assert len(result) == 1
    # with only one crisis, normalized score should be 0 (min == max -> 0)
    # or the formula handles it gracefully
    assert pd.notna(result["oci_score"].iloc[0])


def test_oci_zero_population():
    """zero population should not cause division by zero"""
    hno = pd.DataFrame({
        "country_iso3": ["XXX"],
        "year": [2025],
        "people_in_need_k": [1000.0],
        "people_targeted_k": [500.0],
        "ocha_severity": [np.nan],
    })
    fts = pd.DataFrame(columns=[
        "country_iso3", "year", "plan_name",
        "requirements_usd_m", "funding_usd_m", "funding_gap", "percent_funded",
    ])
    pop = pd.DataFrame({
        "country_iso3": ["XXX"],
        "total_population": [0],
    })
    result = compute_oci_scores(hno, fts, pop)
    assert len(result) == 1
    # zero pop -> pin_normalized is nan -> oci_raw = 0
    assert result["oci_raw"].iloc[0] == 0


def test_oci_negative_funding_gap_clipped():
    """negative funding gap (overfunded) should be clipped to 0"""
    hno = pd.DataFrame({
        "country_iso3": ["AFG"],
        "year": [2025],
        "people_in_need_k": [10000.0],
        "people_targeted_k": [5000.0],
        "ocha_severity": [np.nan],
    })
    fts = pd.DataFrame({
        "country_iso3": ["AFG"],
        "year": [2025],
        "plan_name": ["Afghanistan HRP"],
        "requirements_usd_m": [1000.0],
        "funding_usd_m": [2000.0],  # overfunded
        "funding_gap": [-1.0],
        "percent_funded": [200.0],
    })
    pop = pd.DataFrame({
        "country_iso3": ["AFG"],
        "total_population": [40000000],
    })
    result = compute_oci_scores(hno, fts, pop)
    # funding gap is already -1.0 from input, but oci_calculator should handle it
    assert result["oci_raw"].iloc[0] >= 0


def test_outlier_all_same_efficiency():
    """all projects with identical ratios should all be normal"""
    df = pd.DataFrame({
        "project_code": [f"P{i}" for i in range(10)],
        "country_iso3": ["AFG"] * 10,
        "year": [2025] * 10,
        "cluster_name": ["WASH"] * 10,
        "budget_usd": [100000] * 10,
        "beneficiaries_total": [5000] * 10,
        "efficiency_ratio": [0.05] * 10,
    })
    result = detect_efficiency_outliers(df)
    # all same -> std = 0 -> no z-scores computed -> all should remain normal or have nan z
    outlier_count = result["efficiency_flag"].isin(["high_efficiency", "low_efficiency"]).sum()
    assert outlier_count == 0


def test_outlier_empty_dataframe():
    """empty input should return empty output"""
    df = pd.DataFrame(columns=[
        "project_code", "country_iso3", "year", "cluster_name",
        "budget_usd", "beneficiaries_total", "efficiency_ratio",
    ])
    result = detect_efficiency_outliers(df)
    assert len(result) == 0
    assert "zscore_efficiency" in result.columns


def test_similarity_single_project():
    """single project should return empty results"""
    df = pd.DataFrame({
        "project_code": ["P1"],
        "country_iso3": ["AFG"],
        "cluster_name": ["WASH"],
        "budget_usd": [100000],
        "beneficiaries_total": [5000],
        "org_type": ["INGO"],
    })
    result = get_similar_projects("P1", df, top_n=5, benchmark_only=False)
    assert result.empty


def test_feature_matrix_all_same_cluster():
    """should work with homogeneous data"""
    df = pd.DataFrame({
        "project_code": [f"P{i}" for i in range(20)],
        "country_iso3": ["AFG"] * 20,
        "cluster_name": ["WASH"] * 20,
        "budget_usd": np.random.lognormal(12, 1, 20),
        "beneficiaries_total": np.random.lognormal(8, 1, 20),
        "org_type": ["INGO"] * 20,
    })
    X, enc, scaler, df_feat = build_feature_matrix(df)
    assert X.shape[0] == 20
    assert X.shape[1] > 0


def test_similarity_with_nan_efficiency():
    """should handle NaN efficiency ratios gracefully"""
    df = pd.DataFrame({
        "project_code": [f"P{i}" for i in range(10)],
        "country_iso3": ["AFG"] * 5 + ["SSD"] * 5,
        "cluster_name": ["WASH"] * 5 + ["Health"] * 5,
        "budget_usd": [100000] * 10,
        "beneficiaries_total": [0] * 5 + [5000] * 5,
        "efficiency_ratio": [np.nan] * 5 + [0.05] * 5,
        "org_type": ["INGO"] * 10,
    })
    result = get_similar_projects("P0", df, top_n=3, benchmark_only=False)
    assert len(result) == 3
