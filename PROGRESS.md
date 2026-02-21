# CrisisLens - Progress

> **Living Memory Document**: Updated at every development step.

---

## Current Status

- **Project**: CrisisLens - Overlooked Crisis Index
- **Phase**: Phase 1 (Core Functionality)
- **Current Task**: Final polish
- **Last Updated**: 2026-02-21
- **Tests Passing**: Yes (48/48)

---

## Service Status

- Streamlit App: Port 8501 - Verified
- Data Pipeline: CLI - Verified
- Actian VectorAI: Port 50051 (Docker) - Running

---

## Phase Checklist

### Phase 0: Setup
- [x] Create GitHub repository
- [x] Set up .gitignore and .env.example
- [x] Create CLAUDE.md with project conventions
- [x] Create PLAN.md with full strategy and rubric analysis
- [x] Define file structure and tech stack
- [x] Install dependencies (requirements.txt)

### Phase 1: Core Functionality
- [x] Implement data_loader.py (all 5 UN dataset loaders + pipeline orchestrator)
- [x] Implement oci_calculator.py (OCI formula, normalization, ranking)
- [x] Implement outlier_detector.py (z-score efficiency analysis)
- [x] Implement similarity_engine.py (cosine similarity recommender)
- [x] Implement actian_connector.py (VectorAI DB integration)
- [x] Implement filters.py (shared sidebar filter widgets)
- [x] Build app.py (Streamlit entry point, top 5 crises, quick stats)
- [x] Build 1_Overview_Map.py (OCI choropleth world map)
- [x] Build 2_Crisis_Drilldown.py (cluster-level funding mismatch)
- [x] Build 3_Efficiency_Outliers.py (beneficiary-to-budget outlier table)
- [x] Build 4_Project_Recommender.py (comparable project search)
- [x] Build 5_Funding_Forecast.py (funding trajectory forecasting)
- [x] Run data pipeline end-to-end (65 OCI scores, 8091 projects, 1069 funding rows)
- [x] Verify all utils work with real data
- [x] Verify Streamlit app starts cleanly
- [x] Add tests for utils (48 tests: data_loader, oci_calculator, outlier_detector, similarity_engine, actian_connector, edge cases)
- [x] Set up linting (ruff, all checks passing)

### Phase 2: Polish
- [x] Create README.md for GitHub/Devpost
- [x] Build Databricks notebook (full_pipeline.ipynb) - code complete, needs Databricks runtime for outputs
- [x] Actian VectorAI DB integration testing (gRPC, 8091 vectors indexed, search working)
- [ ] Deploy Streamlit app (Streamlit Cloud or Databricks serving)
- [ ] Record 2-minute pitch video
- [ ] Devpost submission

### Phase 3: Sponsor Challenges
- [x] Actian VectorAI DB integrated (gRPC connector, auto-populate, 8091 vectors)
- [ ] Figma Make individual submission
- [ ] Databricks Raffle video

---

## Completed Tasks

- Project scaffolding (CLAUDE.md, PLAN.md, .gitignore, .env.example) - Feb 20
- Full codebase implementation (18 files, 2942 lines) - Feb 20 (commit: "part 1")
- Data pipeline verification (65 OCI scores computed from live UN data) - Feb 20
- All utils verified: outlier detection (265 outliers from 8091 projects), similarity engine working - Feb 20
- 36 pytest tests added (data_loader, oci_calculator, outlier_detector, similarity_engine) - Feb 20
- Ruff linting configured and passing (pyproject.toml) - Feb 20
- Fixed pandas FutureWarnings in oci_calculator.py - Feb 20
- Fixed lambda assignments in filters.py - Feb 20
- README.md created for GitHub/Devpost - Feb 20
- PROGRESS.md created - Feb 20
- Actian VectorAI DB integrated via gRPC (8091 vectors, cosine similarity search working) - Feb 21
- Fixed negative funding gap bug in oci_calculator (added clip to input) - Feb 21
- 48 tests passing (added actian connector tests, edge case tests) - Feb 21
- Recommender page simplified (auto-runs similarity on page load) - Feb 21

---

## Decisions Log

- OCI severity_weight defaults to 1.0 (max) for all crises because HNO data lacks numeric severity field - This means OCI differentiates on PIN and funding gap only - Feb 20
- CBPF project cluster inference uses keyword matching on project titles - Acceptable accuracy for hackathon scope - Feb 20
- Actian VectorAI falls back silently to sklearn cosine similarity if unavailable - Feb 20

---

## Risk Register

- HNO severity data missing - Medium - Default to max severity (5.0) so OCI still differentiates on PIN + funding gap - Mitigated
- Actian VectorAI deployed via Docker on port 50051 - Low - gRPC connector working - Resolved
- Data freshness depends on UN API availability - Low - Raw files cached locally after first download - Mitigated

---

## Session Notes

### Session: 2026-02-20
**Completed**: Full codebase, data pipeline, Actian VectorAI gRPC integration, 48 tests, ruff linting, README, PROGRESS
**Current State**: App runs with 65 OCI-scored crises, 8091 projects, Actian VectorAI with 8091 indexed vectors. 48/48 tests, lint clean.
**Next Steps**: Deploy to Streamlit Cloud, record pitch video, Devpost submission, Figma Make, Databricks raffle video

---

## Quick Reference

### Commands
```bash
pip install -r requirements.txt        # install dependencies
python utils/data_loader.py            # run full data pipeline
streamlit run app.py                   # launch web app
pytest tests/                          # run tests
```

### Important Links
- Hacklytics 2026: https://hacklytics.io
- UN HumData: https://data.humdata.org
- CBPF Data: https://cbpf.data.unocha.org
- Actian VectorAI: docker pull williamimoh/actian-vectorai-db:1.0b
