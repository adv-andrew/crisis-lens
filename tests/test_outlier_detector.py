"""
tests for the efficiency outlier detector
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.outlier_detector import detect_efficiency_outliers, get_outlier_summary


def test_detect_adds_expected_columns(sample_projects):
    """output should have zscore_efficiency, efficiency_flag, is_benchmark"""
    result = detect_efficiency_outliers(sample_projects)
    assert "zscore_efficiency" in result.columns
    assert "efficiency_flag" in result.columns
    assert "is_benchmark" in result.columns


def test_detect_preserves_row_count(sample_projects):
    """should not add or remove rows"""
    result = detect_efficiency_outliers(sample_projects)
    assert len(result) == len(sample_projects)


def test_detect_flag_values(sample_projects):
    """efficiency_flag should only contain expected values"""
    result = detect_efficiency_outliers(sample_projects)
    valid_flags = {"normal", "high_efficiency", "low_efficiency", "insufficient_data"}
    assert set(result["efficiency_flag"].unique()).issubset(valid_flags)


def test_detect_benchmark_matches_high_efficiency(sample_projects):
    """is_benchmark should be True iff efficiency_flag == high_efficiency"""
    result = detect_efficiency_outliers(sample_projects)
    assert (result["is_benchmark"] == (result["efficiency_flag"] == "high_efficiency")).all()


def test_detect_insufficient_data_for_small_groups():
    """groups with fewer than 3 projects should be flagged insufficient_data"""
    df = pd.DataFrame({
        "project_code": ["A", "B"],
        "country_iso3": ["AFG", "AFG"],
        "year": [2025, 2025],
        "cluster_name": ["WASH", "WASH"],
        "budget_usd": [100000, 200000],
        "beneficiaries_total": [500, 1000],
        "efficiency_ratio": [0.005, 0.005],
    })
    result = detect_efficiency_outliers(df)
    assert (result["efficiency_flag"] == "insufficient_data").all()


def test_detect_custom_threshold(sample_projects):
    """lower threshold should produce more outliers"""
    strict = detect_efficiency_outliers(sample_projects, threshold=3.0)
    loose = detect_efficiency_outliers(sample_projects, threshold=1.0)
    strict_outliers = strict["efficiency_flag"].isin(["high_efficiency", "low_efficiency"]).sum()
    loose_outliers = loose["efficiency_flag"].isin(["high_efficiency", "low_efficiency"]).sum()
    assert loose_outliers >= strict_outliers


def test_get_outlier_summary_filters(sample_projects):
    """summary should only return outlier rows"""
    flagged = detect_efficiency_outliers(sample_projects)
    summary = get_outlier_summary(flagged)
    if not summary.empty:
        assert summary["efficiency_flag"].isin(["high_efficiency", "low_efficiency"]).all()


def test_get_outlier_summary_sorted_by_abs_z(sample_projects):
    """summary should be sorted by absolute z-score descending"""
    flagged = detect_efficiency_outliers(sample_projects)
    summary = get_outlier_summary(flagged)
    if len(summary) > 1:
        abs_z = summary["zscore_efficiency"].abs().values
        assert all(abs_z[i] >= abs_z[i + 1] for i in range(len(abs_z) - 1))
