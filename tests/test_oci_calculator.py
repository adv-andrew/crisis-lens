"""
tests for the OCI calculator
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.oci_calculator import compute_oci_scores


def test_oci_basic_output_shape(sample_hno, sample_fts, sample_pop):
    """oci output has expected rows and columns"""
    result = compute_oci_scores(sample_hno, sample_fts, sample_pop)
    assert len(result) == 5
    assert "oci_score" in result.columns
    assert "oci_rank" in result.columns
    assert "country_iso3" in result.columns


def test_oci_scores_between_zero_and_one(sample_hno, sample_fts, sample_pop):
    """all oci scores should be in [0, 1]"""
    result = compute_oci_scores(sample_hno, sample_fts, sample_pop)
    assert result["oci_score"].min() >= 0
    assert result["oci_score"].max() <= 1


def test_oci_rank_ordering(sample_hno, sample_fts, sample_pop):
    """rank 1 should have the highest oci score"""
    result = compute_oci_scores(sample_hno, sample_fts, sample_pop)
    top = result[result["oci_rank"] == 1]
    assert len(top) >= 1
    assert top["oci_score"].iloc[0] == result["oci_score"].max()


def test_oci_higher_funding_gap_increases_score(sample_hno, sample_pop):
    """a crisis with 90% funding gap should score higher than 10% gap, all else equal"""
    fts_high_gap = pd.DataFrame({
        "country_iso3": ["AFG"],
        "year": [2025],
        "plan_name": ["Afghanistan HRP 2025"],
        "requirements_usd_m": [3200.0],
        "funding_usd_m": [320.0],
        "funding_gap": [0.9],
        "percent_funded": [10.0],
    })
    fts_low_gap = pd.DataFrame({
        "country_iso3": ["AFG"],
        "year": [2025],
        "plan_name": ["Afghanistan HRP 2025"],
        "requirements_usd_m": [3200.0],
        "funding_usd_m": [2880.0],
        "funding_gap": [0.1],
        "percent_funded": [90.0],
    })

    hno_single = sample_hno[sample_hno["country_iso3"] == "AFG"].copy()

    result_high = compute_oci_scores(hno_single, fts_high_gap, sample_pop)
    result_low = compute_oci_scores(hno_single, fts_low_gap, sample_pop)

    assert result_high["oci_raw"].iloc[0] > result_low["oci_raw"].iloc[0]


def test_oci_missing_fts_uses_default_gap(sample_hno, sample_pop):
    """countries without FTS data should get funding_gap = 0.5"""
    fts_empty = pd.DataFrame(columns=[
        "country_iso3", "year", "plan_name",
        "requirements_usd_m", "funding_usd_m", "funding_gap", "percent_funded",
    ])
    result = compute_oci_scores(sample_hno, fts_empty, sample_pop)
    assert (result["funding_gap"] == 0.5).all()
    assert (result["has_funding_data"] == False).all()  # noqa: E712


def test_oci_missing_population_gives_zero(sample_fts):
    """countries without population data should get oci_raw = 0"""
    hno = pd.DataFrame({
        "country_iso3": ["XXX"],
        "year": [2025],
        "people_in_need_k": [1000.0],
        "people_targeted_k": [500.0],
        "ocha_severity": [np.nan],
    })
    pop_empty = pd.DataFrame(columns=["country_iso3", "total_population"])
    result = compute_oci_scores(hno, sample_fts, pop_empty)
    assert result["oci_raw"].iloc[0] == 0


def test_oci_country_name_extraction(sample_hno, sample_fts, sample_pop):
    """country_name should be extracted from plan_name"""
    result = compute_oci_scores(sample_hno, sample_fts, sample_pop)
    afg = result[result["country_iso3"] == "AFG"]
    assert afg["country_name"].iloc[0] == "Afghanistan"


def test_oci_severity_defaults_to_max(sample_hno, sample_fts, sample_pop):
    """nan severity should default to 5.0, giving severity_weight = 1.0"""
    result = compute_oci_scores(sample_hno, sample_fts, sample_pop)
    assert (result["severity_weight"] == 1.0).all()
