# CrisisLens

**The Overlooked Crisis Index** -- surfacing the humanitarian crises the world is missing.

Built for the Databricks x United Nations Geo-Insight Challenge at Hacklytics 2026.

---

## What It Does

CrisisLens computes an Overlooked Crisis Index (OCI) that quantifies how "overlooked" each humanitarian crisis is relative to its severity. It merges UN humanitarian needs data, funding data, and population data to produce a single score per crisis, then surfaces the results through an interactive Streamlit dashboard.

The OCI combines three components:
- People in Need (normalized by population)
- OCHA severity classification
- Funding gap (requirements vs. actual funding)

Higher OCI = more overlooked.

---

## Features

**Interactive Geo Map** -- Choropleth world map color-coded by OCI score. Click any country to drill down.

**Cluster-Level Drilldown** -- Within each crisis, see which humanitarian clusters (WASH, Health, Food Security, etc.) are most underfunded. Fund managers operate at cluster level; this is the granularity they need.

**Efficiency Outlier Detection** -- Z-score analysis on beneficiary-to-budget ratios across 8,000+ CBPF projects. Flags high-efficiency benchmarks and low-efficiency outliers.

**Project Recommender** -- Given any underfunded project, surfaces comparable high-efficiency benchmark projects from other contexts using cosine similarity on project feature vectors.

**Funding Trajectory Forecasting** -- Identifies crises trending toward deeper underfunding using year-over-year funding data.

---

## Setup

```bash
pip install -r requirements.txt
python utils/data_loader.py
streamlit run app.py
```

The data pipeline downloads all datasets from UN HumData and CBPF APIs, computes OCI scores, and caches processed outputs in `data/processed/`.

---

## Data Sources

- Humanitarian Needs Overview (HNO) -- people in need, severity classifications
- Humanitarian Response Plans (HRP) -- project-level budgets and beneficiary targets
- Global Requirements and Funding (FTS) -- total requirements vs. actual funding
- Population Data (COD-PS) -- country population for normalization
- CBPF Pooled Funds -- project-level allocations from Country-Based Pooled Funds

---

## Tech Stack

- Python, pandas, numpy, scipy, scikit-learn
- Streamlit for the web app
- Plotly for interactive visualizations
- Databricks for scalable data processing
- Actian VectorAI DB for vector search (sponsor challenge)

---

## Testing

```bash
python -m pytest tests/ -v
ruff check .
```

---

## Team

Built by @matheusmaldaner and team at Hacklytics 2026, Georgia Tech.
