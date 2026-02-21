"""
shared fixtures for crisislens tests
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_hno():
    """minimal HNO dataframe for testing"""
    return pd.DataFrame({
        "country_iso3": ["AFG", "SSD", "YEM", "HTI", "COD"],
        "year": [2025, 2025, 2025, 2025, 2025],
        "people_in_need_k": [23700.0, 9400.0, 18200.0, 5500.0, 25400.0],
        "people_targeted_k": [15000.0, 6200.0, 12000.0, 3200.0, 8700.0],
        "ocha_severity": [np.nan, np.nan, np.nan, np.nan, np.nan],
    })


@pytest.fixture
def sample_fts():
    """minimal FTS global funding dataframe"""
    return pd.DataFrame({
        "country_iso3": ["AFG", "SSD", "YEM", "HTI", "COD"],
        "year": [2025, 2025, 2025, 2025, 2025],
        "plan_name": [
            "Afghanistan HRP 2025",
            "South Sudan HRP 2025",
            "Yemen HRP 2025",
            "Haiti Flash Appeal 2025",
            "DRC HRP 2025",
        ],
        "requirements_usd_m": [3200.0, 1800.0, 4300.0, 680.0, 2600.0],
        "funding_usd_m": [1400.0, 350.0, 2100.0, 120.0, 1300.0],
        "funding_gap": [0.5625, 0.8056, 0.5116, 0.8235, 0.5000],
        "percent_funded": [43.75, 19.44, 48.84, 17.65, 50.00],
    })


@pytest.fixture
def sample_pop():
    """minimal population dataframe"""
    return pd.DataFrame({
        "country_iso3": ["AFG", "SSD", "YEM", "HTI", "COD"],
        "total_population": [42000000, 11000000, 34000000, 11800000, 103200000],
    })


@pytest.fixture
def sample_projects():
    """minimal CBPF project dataframe for outlier and similarity tests"""
    np.random.seed(42)
    n = 50
    clusters = ["WASH", "Health", "Food Security", "Education", "Protection"]
    countries = ["AFG", "SSD", "YEM", "HTI", "COD"]
    org_types = ["INGO", "NNGO", "UN Agency"]

    budgets = np.random.lognormal(mean=12, sigma=1.5, size=n)
    beneficiaries = budgets * np.random.lognormal(mean=-2, sigma=1, size=n)

    return pd.DataFrame({
        "project_code": [f"PRJ-{i:04d}" for i in range(n)],
        "country_iso3": np.random.choice(countries, n),
        "year": np.random.choice([2023, 2024, 2025], n),
        "cluster_name": np.random.choice(clusters, n),
        "budget_usd": budgets,
        "beneficiaries_total": beneficiaries,
        "efficiency_ratio": beneficiaries / budgets,
        "org_type": np.random.choice(org_types, n),
        "org_name": [f"Org-{i}" for i in range(n)],
        "project_title": [f"Project {c} {i}" for i, c in zip(range(n), np.random.choice(clusters, n))],
        "pooled_fund_name": [f"Fund-{c}" for c in np.random.choice(countries, n)],
        "allocation_type": "Standard",
        "project_status": "Completed",
    })
