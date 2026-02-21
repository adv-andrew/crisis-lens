"""
CrisisLens Project Similarity Engine
=====================================
Cosine similarity recommender using scikit-learn.
Given an underfunded or low-efficiency project, surfaces comparable
high-efficiency benchmark projects from other contexts.
"""

import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder


def build_feature_matrix(df_projects: pd.DataFrame):
    """
    Build combined sparse feature matrix from project attributes.

    Returns
    -------
    X : sparse matrix (n_projects x n_features)
    encoder : fitted OneHotEncoder
    scaler : fitted MinMaxScaler
    df_feat : aligned DataFrame (same row order as X)
    """
    df = df_projects.dropna(subset=["cluster_name"]).copy()
    df = df.reset_index(drop=True)

    # Categorical features
    cat_cols = ["cluster_name", "org_type"]
    for col in cat_cols:
        if col not in df.columns:
            df[col] = "Unknown"
        df[col] = df[col].fillna("Unknown")

    enc = OneHotEncoder(sparse_output=True, handle_unknown="ignore")
    X_cat = enc.fit_transform(df[cat_cols])

    # Numeric features (log-scaled + normalized)
    df["log_budget"] = np.log1p(df["budget_usd"].fillna(0))
    df["log_beneficiaries"] = np.log1p(df["beneficiaries_total"].fillna(0))

    num_cols = ["log_budget", "log_beneficiaries"]
    scaler = MinMaxScaler()
    X_num = sp.csr_matrix(scaler.fit_transform(df[num_cols]))

    # Combine
    X = sp.hstack([X_cat, X_num])

    return X, enc, scaler, df


def get_similar_projects(
    project_code: str,
    df_projects: pd.DataFrame,
    df_outliers: pd.DataFrame | None = None,
    top_n: int = 5,
    benchmark_only: bool = True,
) -> pd.DataFrame:
    """
    Return top_n most similar projects to the given project_code.

    Parameters
    ----------
    project_code : the project to find matches for
    df_projects : full project dataset
    df_outliers : projects with efficiency flags (from outlier_detector)
    top_n : number of results to return
    benchmark_only : if True, only return high-efficiency benchmarks

    Returns
    -------
    DataFrame with similar projects and similarity_score column.
    """
    X, enc, scaler, df_feat = build_feature_matrix(df_projects)

    # Find query project index
    query_mask = df_feat["project_code"] == project_code
    if not query_mask.any():
        return pd.DataFrame()

    query_idx = query_mask.values.argmax()
    query_vec = X[query_idx]

    # Build candidate pool
    if benchmark_only and df_outliers is not None:
        bench_codes = set(
            df_outliers.loc[
                df_outliers["efficiency_flag"] == "high_efficiency", "project_code"
            ]
        )
        bench_codes.discard(project_code)
        candidate_mask = df_feat["project_code"].isin(bench_codes)
    else:
        candidate_mask = df_feat["project_code"] != project_code

    if not candidate_mask.any():
        # Fall back to all projects if no benchmarks found
        candidate_mask = df_feat["project_code"] != project_code
        if not candidate_mask.any():
            return pd.DataFrame()

    X_candidates = X[candidate_mask.values]

    # Cosine similarity
    sims = cosine_similarity(query_vec.reshape(1, -1), X_candidates)[0]

    # Top N
    n = min(top_n, len(sims))
    top_idx = sims.argsort()[-n:][::-1]

    result_df = df_feat[candidate_mask].iloc[top_idx].copy()
    result_df["similarity_score"] = sims[top_idx]

    output_cols = [
        "project_code", "country_iso3", "cluster_name",
        "project_title", "budget_usd", "beneficiaries_total",
        "efficiency_ratio", "similarity_score",
    ]
    return result_df[[c for c in output_cols if c in result_df.columns]].reset_index(drop=True)


def find_similar_projects(
    project_code: str,
    df_projects: pd.DataFrame,
    df_outliers: pd.DataFrame | None = None,
    top_n: int = 5,
) -> pd.DataFrame:
    """
    Try Actian VectorAI first, fall back to sklearn cosine similarity.
    """
    try:
        from utils.actian_connector import search_similar_projects
        results = search_similar_projects(project_code, df_projects=df_projects, top_n=top_n)
        if results is not None and not results.empty:
            return results
    except Exception:
        pass

    return get_similar_projects(project_code, df_projects, df_outliers, top_n)
