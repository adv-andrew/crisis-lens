"""
tests for the project similarity engine
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.similarity_engine import build_feature_matrix, get_similar_projects


def test_feature_matrix_shape(sample_projects):
    """feature matrix should have same number of rows as input (minus NaN clusters)"""
    X, enc, scaler, df_feat = build_feature_matrix(sample_projects)
    valid_count = sample_projects["cluster_name"].notna().sum()
    assert X.shape[0] == valid_count
    assert X.shape[1] > 0


def test_feature_matrix_no_nan(sample_projects):
    """feature matrix should not contain NaN"""
    X, _, _, _ = build_feature_matrix(sample_projects)
    assert not np.isnan(X.toarray()).any()


def test_get_similar_returns_correct_count(sample_projects):
    """should return top_n results"""
    code = sample_projects["project_code"].iloc[0]
    result = get_similar_projects(code, sample_projects, top_n=3, benchmark_only=False)
    assert len(result) == 3


def test_get_similar_excludes_query(sample_projects):
    """query project should not appear in results"""
    code = sample_projects["project_code"].iloc[0]
    result = get_similar_projects(code, sample_projects, top_n=5, benchmark_only=False)
    assert code not in result["project_code"].values


def test_get_similar_has_similarity_score(sample_projects):
    """results should include similarity_score column"""
    code = sample_projects["project_code"].iloc[0]
    result = get_similar_projects(code, sample_projects, top_n=3, benchmark_only=False)
    assert "similarity_score" in result.columns
    assert (result["similarity_score"] >= 0).all()
    assert (result["similarity_score"] <= 1).all()


def test_get_similar_sorted_descending(sample_projects):
    """results should be sorted by similarity_score descending"""
    code = sample_projects["project_code"].iloc[0]
    result = get_similar_projects(code, sample_projects, top_n=5, benchmark_only=False)
    scores = result["similarity_score"].values
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))


def test_get_similar_unknown_code(sample_projects):
    """unknown project code should return empty dataframe"""
    result = get_similar_projects("NONEXISTENT", sample_projects, top_n=3, benchmark_only=False)
    assert result.empty


def test_get_similar_benchmark_only(sample_projects):
    """with benchmark_only=True and outlier data, should prefer benchmarks"""
    from utils.outlier_detector import detect_efficiency_outliers
    flagged = detect_efficiency_outliers(sample_projects, threshold=1.0)

    code = sample_projects["project_code"].iloc[0]
    result = get_similar_projects(
        code, sample_projects, df_outliers=flagged, top_n=3, benchmark_only=True,
    )
    # result should not be empty (falls back to all projects if no benchmarks)
    assert not result.empty
