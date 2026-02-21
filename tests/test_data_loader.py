"""
tests for data_loader utility functions (unit tests only, no network calls)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.data_loader import _infer_cluster, _to_numeric


def test_to_numeric_plain():
    """plain numeric strings should convert"""
    s = pd.Series(["100", "200", "300"])
    result = _to_numeric(s)
    assert result.tolist() == [100.0, 200.0, 300.0]


def test_to_numeric_with_commas():
    """numbers with commas should convert"""
    s = pd.Series(["1,000", "2,500,000", "100"])
    result = _to_numeric(s)
    assert result.tolist() == [1000.0, 2500000.0, 100.0]


def test_to_numeric_with_whitespace():
    """whitespace should be stripped"""
    s = pd.Series(["  100  ", " 200", "300 "])
    result = _to_numeric(s)
    assert result.tolist() == [100.0, 200.0, 300.0]


def test_to_numeric_invalid():
    """non-numeric strings should return NaN"""
    s = pd.Series(["abc", "N/A", ""])
    result = _to_numeric(s)
    assert result.isna().all()


def test_infer_cluster_wash():
    """WASH-related keywords should map to WASH"""
    assert _infer_cluster("Water supply project") == "WASH"
    assert _infer_cluster("Sanitation improvement") == "WASH"


def test_infer_cluster_health():
    assert _infer_cluster("Health clinic support") == "Health"


def test_infer_cluster_food():
    assert _infer_cluster("Food distribution") == "Food Security"
    assert _infer_cluster("Agriculture support") == "Food Security"


def test_infer_cluster_education():
    assert _infer_cluster("Education for children") == "Education"


def test_infer_cluster_protection():
    assert _infer_cluster("Protection of civilians") == "Protection"


def test_infer_cluster_unknown():
    """unrecognized titles should return Other"""
    assert _infer_cluster("General support project") == "Other"


def test_infer_cluster_nan():
    """NaN input should return Other"""
    assert _infer_cluster(np.nan) == "Other"


def test_infer_cluster_case_insensitive():
    """matching should be case insensitive"""
    assert _infer_cluster("WATER AND SANITATION") == "WASH"
    assert _infer_cluster("health care") == "Health"
