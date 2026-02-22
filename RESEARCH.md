# RESEARCH.md -- CrisisLens Paper

> Project-specific research paper pipeline. Adapted from the master RESEARCH.md for the CrisisLens paper on humanitarian crisis prioritization.

---

## Golden Standard Reference

**Reference paper**: Davidson et al., "The Collaboration Gap" (arXiv:2511.02687, Nov 2025)

Match this paper's organization, figure quality, table formatting, and writing voice. See master RESEARCH.md at `/home/matheus/projects/RESEARCH.md` for the full golden standard specification and all banned patterns, review passes, figure recipes, etc.

Key conventions to follow:
- Related work embedded in Discussion, not standalone section
- Results structured as narrative arc: baseline, main finding, variations, intervention
- Figures: sans-serif labels, subtle gridlines, horizontal bar charts, heatmap matrices, line plots with CI bands
- Tables: booktabs, bold best values, right-aligned numbers with +/- notation
- Writing: variable sentence length, topic-sentence paragraphs, cautious but assertive, no em dashes
- Named phenomenon for key finding (the "overlooked crisis gap" or similar)

---

## Phase 0: Project Information

```
Title (working):       CrisisLens: Quantifying Overlooked Humanitarian Crises Through
                       Composite Need-Funding Mismatch Scoring
Authors:               Matheus Maldaner (University of Florida), [coauthors TBD]
Venue:                 TBD (candidates: arXiv preprint, AAAI AI for Social Impact workshop,
                       ACM COMPASS, CHI Late-Breaking Work, NeurIPS Socially Responsible ML)
Paper type:            conference / workshop paper
Page limit:            TBD (depends on venue, assume 8+refs)
Submission deadline:   TBD
Overleaf git URL:      TBD (create and link here)
Abstract (rough):      Billions of dollars in humanitarian aid are allocated annually, but
                       distribution does not track where need is greatest. We propose the
                       Overlooked Crisis Index (OCI), a composite metric that scores each
                       crisis by the mismatch between its severity and its funding coverage.
                       Applied to 24 countries across 3 years of UN data, the OCI identifies
                       crises like South Sudan (OCI=1.0, 89.5% funding gap) and Haiti
                       (OCI=0.73, 96.3% gap) as structurally overlooked. We complement the
                       index with cluster-level mismatch analysis, project-level efficiency
                       outlier detection across 8,091 CBPF projects, and a cosine-similarity
                       recommender that surfaces benchmark projects for underfunded contexts.
```

```
Related prior work by author:  Maldaner undergrad thesis on DiffLogic (UF 2025),
                               Plato's Cave (AAAI 2026 submission on knowledge graphs)
Target contribution type:      system + analysis (new metric + tool + empirical findings)
Existing code/data:            this repo (crisis-lens/)
Devpost/hackathon writeup:     yes, dual-purpose (Hacklytics 2026 Devpost submission)
```

### Phase Gate

- [x] All required fields filled (venue TBD, will finalize before writing)
- [ ] Venue template identified and downloaded
- [ ] Overleaf repo cloned locally
- [ ] matheus-style.tex copied into paper directory

---

## Phase 1: Literature Review

### Keyword Clusters

1. **humanitarian crisis prioritization**: crisis severity scoring, humanitarian needs assessment, OCHA severity classification, crisis ranking frameworks
2. **aid allocation and funding gaps**: humanitarian funding distribution, donor attention bias, needs-based allocation, funding mismatch detection
3. **composite indices for development/crisis**: Human Development Index methodology, vulnerability indices, multi-criteria humanitarian scoring, index construction
4. **data-driven humanitarian response**: humanitarian data analytics, UN data platforms, OCHA data ecosystems, evidence-based aid allocation
5. **project-level efficiency in aid**: cost-effectiveness of humanitarian projects, beneficiary-to-budget analysis, aid efficiency measurement, value for money in humanitarian action

### Key Papers to Find

- OCHA's own severity classification methodology (the JIAF framework)
- Existing humanitarian index work (INFORM Risk Index, DARA Crisis Severity Index, ACAPS severity framework)
- FTS/CBPF documentation papers or reports
- Academic work on donor attention bias and "forgotten crises" (MSF annual lists, ECHO forgotten crisis assessments)
- Statistical methods for composite index construction (OECD Handbook on Composite Indicators)
- Cost-effectiveness in humanitarian aid (Humanitarian Policy Group, ODI publications)
- Any prior work combining needs data with funding data computationally

### Gaps to Establish

The paper's motivation rests on these gaps:
1. **No open, reproducible composite index** exists that quantifies "overlooked-ness" by combining PIN, severity, and funding gap into a single score. Existing frameworks (INFORM, JIAF) measure risk or severity but not the mismatch between severity and response.
2. **Cluster-level mismatch is not surfaced** in existing tools. Country-level aggregates mask that specific sectors (WASH, Health) within a crisis can be critically underfunded while the country-level average looks adequate.
3. **Project-level efficiency benchmarking** is not connected to funding gap analysis. Knowing a crisis is underfunded is one thing. Knowing which project models work efficiently in similar contexts is actionable.
4. **No tool combines all three layers** (macro crisis scoring, meso cluster analysis, micro project recommendations) in a single interactive platform.

### Phase Gate

- [ ] Literature matrix has 15+ entries (store in `paper/lit-matrix.md`)
- [ ] Gaps 1-4 confirmed against existing literature
- [ ] User has reviewed and approved literature matrix

---

## Phase 2: Paper Skeleton

### Modular Main TeX Pattern (Required)

Use a thin `paper/main.tex` that only contains:
- preamble and metadata (`\title`, `\author`, `\date`)
- `\begin{document}` / `\end{document}`
- ordered `\input{sections/...}` statements

Required include order:
1. `sections/00_abstract.tex`
2. `sections/01_introduction.tex`
3. `sections/02_*` for problem/method sections
4. `sections/03_*` and onward for setup/results/discussion/conclusion
5. `sections/08_reproducibility_statement.tex` (or equivalent)
6. `sections/09_references.tex` (if inline bibliography is used)

Rules:
- Do not keep section prose directly in `main.tex`.
- Add one file per major section; use stable numeric prefixes for ordering.
- Keep figures/tables in the section file where they are first discussed.
- Keep labels local to section files and reference them globally as usual.

### Proposed Structure

```
1. Introduction
   - P1: humanitarian funding does not track need (motivate with South Sudan / Haiti data)
   - P2: existing tools measure severity or risk, not the mismatch between severity and funding
   - P3: we propose the OCI, a composite metric, plus cluster-level analysis and project recommender
   - P4: key findings (OCI identifies X crises as structurally overlooked, Y% funding gap)
   - P5: paper organization (optional)

2. The Overlooked Crisis Index
   2.1 Problem Formulation
       - define "overlooked" formally
       - distinguish from severity (a crisis can be severe and well-funded, or moderate and ignored)
   2.2 Data Sources
       - HNO (people in need, severity)
       - FTS (requirements vs. funding)
       - COD-PS (population)
       - CBPF (project-level budgets and beneficiaries)
       - table summarizing each source, rows, years, fields
   2.3 OCI Formula
       - PIN normalization (P/N)
       - funding gap computation (G)
       - media neglect multiplier (1 + 0.2M)
       - min-max normalization across crises
       - equation block with clear variable definitions
   2.4 Cluster-Level Mismatch Analysis
       - per-cluster funding gap within each crisis
       - flagging clusters >1.5 std above country average
   2.5 Efficiency Outlier Detection
       - beneficiary-to-budget ratio
       - log-transform + z-score within (cluster, year) groups
       - benchmark flagging (z > 2.0)
   2.6 Project Recommender
       - feature vector construction (cluster one-hot, org type, log-budget, log-beneficiaries)
       - cosine similarity
       - Actian VectorAI DB integration for scalable search

3. Experimental Setup
   - dataset statistics (24 countries, 65 crisis-year observations, 8,091 projects)
   - time period (2020-2026 for projects, 2024-2026 for OCI)
   - implementation details (Python, Streamlit, Actian VectorAI Docker)
   - table: dataset summary with rows, columns, source, years

4. Results
   4.1 OCI Rankings
       - table: top 5 most overlooked crises with OCI components
       - choropleth figure showing OCI scores globally
       - key finding: South Sudan (1.000), Yemen (0.858), Syria (0.844), Sudan (0.837), Haiti (0.695)
   4.2 Cluster-Level Findings
       - figure: horizontal bar chart of cluster funding gaps for top 3 OCI countries
       - finding: within-country variance is large (some clusters 90%+ gap, others <30%)
       - fund managers operate at cluster level; this is the operationally useful granularity
   4.3 Efficiency Outlier Analysis
       - figure: scatter plot of budget vs. beneficiaries, colored by efficiency flag
       - 265 high-efficiency benchmarks identified across 13 clusters
       - finding: z-score distribution is right-skewed (min z = -1.41, max z = 16.65)
       - no low-efficiency outliers at z < -2.0 threshold (data is well-normalized within clusters)
   4.4 Recommender Evaluation
       - qualitative example: given an underfunded WASH project in Sudan, top-5 similar
         high-efficiency WASH projects from other countries
       - comparison: sklearn cosine similarity vs. Actian VectorAI DB nearest-neighbor search
       - finding: both return identical top-5 for most queries; Actian is faster at scale
   4.5 Funding Trajectory Forecasting
       - figure: line plot with CI bands using full FTS history
       - 7 crises with statistically significant positive slope + above-median OCI
       - top slopes: Myanmar (0.031/yr), Cameroon (0.030/yr), Mali (0.026/yr)

5. Discussion
   5.1 Related Work
       - existing crisis indices (INFORM, JIAF, ACAPS) and how OCI differs
       - humanitarian data analytics platforms (HDX, ReliefWeb, FTS)
       - aid efficiency literature
       - funding attention bias research ("forgotten crises" reports from MSF, ECHO)
   5.2 Limitations
       - media attention from search interest is noisy and language-biased
       - CBPF cluster inference uses keyword matching on project titles (~85% accuracy)
       - linear trend extrapolation is descriptive, not predictive; slopes sensitive to time window
       - only HRP-covered countries scored (non-HRP crises excluded)
   5.3 Broader Impact
       - tool designed for UN fund managers to identify reallocation opportunities
       - all data publicly available, pipeline reproducible
       - OCI can be updated annually as new HNO/FTS data is released

6. Conclusion
   - one paragraph: what we built and what it reveals about humanitarian funding
   - one paragraph: future work (severity data integration, media attention layer,
     real-time updates, deployment with OCHA)

References

Appendices
   A. OCI Formula Derivation and Sensitivity Analysis
   B. Full OCI Rankings Table (all 65 crisis-year observations)
   C. Cluster-Level Funding Gaps for All Countries
   D. Recommender Feature Vector Details
   E. Actian VectorAI DB Integration Details
   F. Streamlit Dashboard Screenshots
```

### Writing Order

1. Section 2 (OCI method, data, formula)
2. Section 4 (results, findings)
3. Section 3 (experimental setup)
4. Section 1 (introduction, motivated by results)
5. Section 5 (discussion, related work, limitations)
6. Section 6 (conclusion)
7. Abstract
8. Title (finalize)

### Phase Gate

- [ ] Skeleton .tex file compiles with venue template
- [ ] All section headers in place
- [ ] User has approved structure

---

## Phase 3: Drafting Rules

Follow the master RESEARCH.md (`/home/matheus/projects/RESEARCH.md`) Phase 3 rules exactly, including all banned patterns, required patterns, tone, paragraph structure, and section closers.

Additional project-specific notes below.

### Key Numbers (source of truth, do not fabricate)

```
OCI scores (current formula: OCI = (P/N) * G * (1 + 0.2M), no severity term):
  - 65 crisis-year observations across 24 countries (2024-2026)
  - Top 5 (2026): South Sudan (1.000), Yemen (0.858), Syria (0.844), Sudan (0.837), Haiti (0.695)
  - severity was removed: P/N quintile proxy correlated 0.96 with P/N, added no signal
  - population fallbacks in data_loader.py cover YEM, MMR, SYR, UKR, CAF (no longer OCI=0)
  - pin_normalized range: 0.027 to 0.800
  - funding_gap range: 0.229 to 0.963
  - 2026 figures are year-to-date (funding accrues throughout year)

Projects:
  - 8,091 CBPF projects across 22 countries, 13 clusters, 7 years (2020-2026)
  - 4 org types: International NGO, National NGO, UN Agency, Others
  - 265 high-efficiency benchmarks (z > 2.0), 7 insufficient data
  - benchmark median efficiency 0.469 ben/USD vs 0.030 non-benchmark (15.6x)

Funding:
  - 1,069 funding rows across all years (back to 2000+ for many countries)
  - full history used for trend analysis (not just OCI years)

Forecasting (full-history slopes):
  - steepest significant: Myanmar (0.031/yr, n=15), Cameroon (0.030/yr, n=13), Mali (0.026/yr, n=20)
  - South Sudan: 0.021/yr over 16 years (not the 0.306 from 3-point window)
  - Ukraine: 0.006/yr, not significant (reversion from post-invasion funding surge)
  - 7 crises with statistically significant positive slope + above-median OCI
```

### Terminology (use consistently, do not alternate)

```
OCI                  (not "the index", "our metric", "the score" interchangeably)
funding gap          (not "coverage gap", "financing gap", "underfunding ratio")
people in need       (not "affected population", "crisis-affected individuals")
cluster              (not "sector", "thematic area" -- match UN terminology)
benchmark project    (not "exemplary project", "high-performing project")
efficiency ratio     (not "cost-effectiveness ratio", "beneficiary ratio")
overlooked           (not "forgotten", "neglected" -- our index name uses "overlooked")
```

---

## Phase 4: Figures Plan

### Figure 1: OCI World Map (choropleth)

- Type: plotly choropleth, exported as static PDF for paper
- Colors: sequential red scale (green=0, yellow=0.35, red=0.65, dark red=1.0)
- Shows: OCI scores for 24 countries (latest year, 2026)
- Gray fill for non-HRP countries (not white, avoids looking empty)
- Caption: "Overlooked Crisis Index scores for 24 HRP-covered countries (2026). Darker red indicates greater mismatch between humanitarian need and funding coverage."

### Figure 2 (removed): OCI Component Breakdown
- removed from paper: with severity gone, OCI has only P/N, G, and media multiplier.
  Full component table is in Appendix A instead.

### Figure 3: Cluster-Level Funding Gaps (vertical bars)

- Type: horizontal bar chart, small multiples (one panel per country) or single panel
- Shows: funding gap per cluster for South Sudan, Sudan, Haiti
- Colors: sequential red scale matching Figure 1
- Caption: "Cluster-level funding gaps within the three most overlooked crises. Within-country variance is substantial, with some clusters exceeding 90% gap while others fall below 30%."

### Figure 4: Efficiency Scatter (budget vs. beneficiaries)

- Type: scatter plot with log-log axes
- Colors: green (high-efficiency z > 2.0), gray (normal), light orange (insufficient data)
- Caption: "Project budget vs. beneficiaries across 8,091 CBPF projects (log-log scale). Green markers indicate high-efficiency benchmarks (z > 2.0 within cluster)."

### Figure 5: Funding Trajectory Forecast (line plot with CI bands)

- Type: line plot with full FTS history (not just OCI years)
- Shows: historical funding gap (2011-2026) + projected 2027 gap for South Sudan
- Solid lines with circular markers for historical, star markers for projected
- CI bands: shaded (alpha=0.12, soft red, no hard edges)
- Red dashed trend line with slope annotation
- Caption: "Funding-gap trend for South Sudan (2011-2026) with linear projection to 2027."

### Figure 6: Recommender Example (table-figure hybrid)

- Type: formatted table showing a query project and top-5 similar benchmark results
- Columns: project code, country, cluster, budget, beneficiaries, similarity score
- Caption: "Top-5 benchmark projects recommended for an underfunded WASH project in Sudan, ranked by cosine similarity on project feature vectors."

### Table 1: Data Source Summary

| Dataset | Source | Records | Years | Key Fields |
|---|---|---|---|---|
| HNO | HumData | ~200 | 2024-2026 | people in need, severity, country |
| FTS Global | HumData | 1,069 | 2000-2026 | requirements, funding, gap |
| FTS Cluster | HumData | ~5,000 | 2000-2026 | cluster, requirements, funding |
| COD-PS | HumData | ~250 | various | country, total population |
| CBPF Projects | OCHA API | 8,091 | 2020-2026 | budget, beneficiaries, cluster, org type |

### Table 2: Top 5 OCI Rankings (2026)

See paper Table 2 and Appendix A for full scores. Current top 5:
South Sudan (1.000), Yemen (0.858), Syria (0.844), Sudan (0.837), Haiti (0.695)

### Table 3: Efficiency Outlier Summary by Cluster

Generate from data. Columns: cluster name, total projects, benchmarks (z > 2.0), median efficiency ratio, median budget.

---

## Phase 5: Experiments

### Research Questions

1. **RQ1**: Which humanitarian crises are most overlooked according to the OCI, and does this align with expert assessments (e.g., MSF's annual "forgotten crises" list)?
2. **RQ2**: How much does cluster-level analysis reveal that country-level aggregates obscure? (within-country variance of funding gaps)
3. **RQ3**: What characterizes high-efficiency humanitarian projects, and can they be surfaced through automated similarity search?
4. **RQ4**: Which crises are trending toward deeper underfunding, and how reliable is linear extrapolation on 3 years of data?

### Baselines for RQ1

- **Naive ranking**: rank crises by funding gap alone (ignore PIN and severity)
- **PIN-only ranking**: rank by people in need per capita (ignore funding)
- **INFORM Risk Index**: compare OCI rankings against INFORM's publicly available risk scores
- **MSF Forgotten Crises List**: compare OCI top-10 against MSF's 2024 list

### Evaluation

- Rank correlation (Spearman's rho) between OCI and each baseline
- Overlap analysis (Jaccard similarity of top-10 sets between OCI and external lists)
- Sensitivity analysis: vary OCI component weights and measure ranking stability (Kendall's tau)

### Phase Gate

- [ ] All 4 RQs have corresponding results
- [ ] At least one external baseline compared (MSF or INFORM)
- [ ] Sensitivity analysis complete

---

## Phase 6: Review

Follow the master RESEARCH.md Phase 6 exactly (6 review passes, quality scoring 0-100, phase gate requiring all passes 80+).

### Project-Specific Review Items

In addition to the standard 6 passes, verify:
- All OCI numbers match `data/processed/oci_scores.csv`
- Project counts match (8,091 projects, 265 benchmarks, 7,826 non-benchmark)
- OCI formula in paper matches `utils/oci_calculator.py` exactly (no severity term)
- Trend slopes computed from funding_clean.csv full history (not 3-point OCI window)
- 2026 funding gap caveat present (year-to-date, not full-year)
- Limitations section covers 3 issues (media noise, cluster inference, linear trends)
- No em dashes anywhere
- Terminology consistency (check the list in Phase 3)

Track scores in `paper/review-log.md`.

---

## Phase 7: Overleaf

```
Overleaf git URL: TBD
```

Once created:
```bash
git clone <url> paper/
cp matheus-style.tex paper/
cd paper/
# add \usepackage{matheus-style} to main.tex preamble
```

---

## Phase 8: Submission Targets

### Venue Candidates (in order of preference)

1. **AAAI AI for Social Impact Workshop** -- directly aligned, UN/humanitarian focus, 4-6 pages
2. **ACM COMPASS** (Computing and Sustainable Societies) -- interdisciplinary, development focus
3. **NeurIPS Socially Responsible ML Workshop** -- if ML contribution is strengthened
4. **CHI Late-Breaking Work** -- if framed as decision-support tool for humanitarian workers
5. **arXiv preprint** -- fallback, immediate visibility, no review

### Dual Output: Devpost

| Paper Section | Devpost Section | Notes |
|---|---|---|
| Intro P1 (problem) | Inspiration | South Sudan / Haiti hook |
| Section 2 (method) | How we built it | simplify formula, focus on pipeline |
| Section 4 (results) | Accomplishments | top 3 crises, 8K projects analyzed |
| Section 5.2 (limitations) | Challenges | missing severity, population gaps |
| Section 6 (future work) | What's next | media layer, real-time updates |

---

## Memory

### Key Decisions

- OCI formula: `(P/N) * funding_gap * (1 + 0.2 * media_score)`, min-max normalized. Severity removed (correlated 0.96 with P/N).
- Efficiency threshold: z > 2.0 on log-transformed beneficiary-to-budget ratio within (cluster, year) groups.
- Trend slopes use full FTS funding history (funding_clean.csv), not the 3-year OCI window.
- Actian VectorAI DB is the sponsor challenge integration. Falls back to sklearn cosine similarity.
- Media scores use static January 2025 baseline (pytrends not installed in production).

### Known Data Issues

- Population fallbacks added for YEM, MMR, SYR, UKR, CAF (previously OCI=0, now resolved).
- 2026 funding gaps are year-to-date and will decrease as funding flows in. Not comparable to full-year figures.
- CBPF cluster assignment uses keyword matching (~85% accuracy). Affects outlier detection counts.
- Country names truncated in HNO: "Republique" (DRC or CAR), "El" (El Salvador), "Burkina" (Burkina Faso), "Tchad" (Chad).

### Style Choices

- "overlooked" not "forgotten" or "neglected"
- "funding gap" not "coverage gap"
- "people in need" not "affected population"
- "cluster" not "sector" (UN terminology)
- "benchmark project" not "exemplary project"
- All monetary values: $X.XM format
- All population: X.XM or X.XK format

---

## Quick Reference

### File Structure

```
crisis-lens/
  RESEARCH.md             # this file
  matheus-style.tex       # personal style file (copy into paper/)
  paper/                  # created when Overleaf repo is cloned
    main.tex
    sections/             # REQUIRED: one .tex per section, loaded by main.tex
    matheus-style.tex
    references.bib
    lit-matrix.md
    review-log.md
    MEMORY.md
    figures/
    tables/
    experiments/
  utils/                  # existing pipeline code (data source)
  data/processed/         # existing computed results (data source)
  tests/                  # existing test suite
```

### Commands

```bash
# generate figures (saves to figures/ and paper/figures/)
python generate_figures.py

# compile paper (run twice for cross-references)
cd ../paper/ && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex

# refresh data
python utils/data_loader.py

# verify data integrity
python -m pytest tests/ -v
```
