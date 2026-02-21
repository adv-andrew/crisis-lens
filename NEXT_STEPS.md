# CrisisLens — Hackathon Next Steps

> **Status as of Feb 21, 2026 (morning)**
> Code is complete. 48/48 tests passing. Data pipeline runs. App works locally.
> What remains is **deployment, polish, and submissions**.

---

## What's Done (you're in great shape)

- [x] Full codebase: 18 source files, ~3000 lines
- [x] Data pipeline: 65 OCI-scored crises, 8,400 CBPF projects, 1,069 funding rows
- [x] All 5 Streamlit pages working (Map, Drilldown, Outliers, Recommender, Forecast)
- [x] Actian VectorAI DB integration via gRPC (8,091 vectors indexed)
- [x] 48 unit tests passing
- [x] Linting clean (ruff)
- [x] README.md for Devpost/GitHub
- [x] Databricks notebook (code complete, needs runtime for cell outputs)

---

## What's Left (priority order)

### CRITICAL — Must Do Before Submission

#### 1. Deploy Streamlit App (30-60 min)
The app needs to be live for judges to interact with.

**Option A: Streamlit Community Cloud (fastest)**
```bash
# 1. Push to GitHub (already done)
# 2. Go to https://share.streamlit.io
# 3. Connect your GitHub repo
# 4. Set main file: app.py
# 5. Add data/processed/*.csv to the repo (they're not gitignored)
```
- Make sure `data/processed/oci_scores.csv`, `funding_clean.csv`, and `projects_clean.csv` are committed
- The app reads from these CSVs, so they must be in the repo
- Streamlit Cloud is free and gives you a shareable URL

**Option B: Run on a VM / Databricks**
- If Streamlit Cloud has issues, you can serve from any machine with `streamlit run app.py --server.port 8501`

**Blocker check:** Are the processed CSV files committed to git? Run:
```bash
git ls-files data/processed/
```
If they're not tracked, add them:
```bash
git add data/processed/oci_scores.csv data/processed/funding_clean.csv data/processed/projects_clean.csv
git commit -m "add processed data for deployment"
git push
```

#### 2. Record 2-Minute Pitch Video (45-60 min)
This is the **biggest differentiator** on the Clarity & Engagement rubric criteria (worth 10 points).

**Script structure (from PLAN.md):**

| Time | Section | What to Show |
|---|---|---|
| 0:00-0:20 | **Hook** | "Right now, 33.7 million people in Sudan need humanitarian aid. Only 13% of required funding has arrived. And almost nobody is talking about it." |
| 0:20-0:50 | **The Problem** | Show the OCI map. Explain that funding doesn't track need. |
| 0:50-1:30 | **Live Demo** | Click Sudan on the map → show drilldown → show cluster gaps → show recommender |
| 1:30-1:50 | **What's Different** | OCI is a novel metric. Cluster-level is operationally useful. Recommender gives actionable next steps. |
| 1:50-2:00 | **The Ask** | "This tool is ready for UN teams to use. The methodology is documented, the pipeline is reproducible." |

**Tips:**
- Show genuine enthusiasm — the rubric explicitly scores this
- Use real data points from your OCI results (South Sudan OCI=1.0, Sudan=0.86, Haiti=0.73)
- Screen-record the live app, overlay with face cam if possible
- Keep it under 2 minutes — judges watch dozens of these

**Key stats for the video (from your data):**
- South Sudan: OCI 1.000 — most overlooked crisis, 9.9M people in need, 89.5% funding gap
- Sudan: OCI 0.862 — 33.7M people in need, 87.0% funding gap
- Haiti: OCI 0.725 — 6.4M people in need, 96.3% funding gap (worst gap!)
- 24 countries tracked across 3 years (2024-2026)
- 8,400+ CBPF projects analyzed for efficiency

#### 3. Devpost Submission (30-45 min)
Write the Devpost description following this structure:

1. **Inspiration** — The UN allocates billions annually, but distribution doesn't match need
2. **What it does** — The OCI, interactive map, cluster drilldown, efficiency outliers, recommender, forecasting
3. **How we built it** — Python + Streamlit + Plotly + scikit-learn + Databricks + Actian VectorAI
4. **Challenges** — Schema differences across HNO years, missing severity data, cluster inference from project titles
5. **Accomplishments** — Novel OCI metric, 5 interactive dashboard pages, 8,400+ projects analyzed
6. **What we learned** — How humanitarian funding is structured, cluster-level operations, data quality challenges
7. **What's next** — Media attention layer (GDELT), real-time data updates, OCHA severity integration

**Don't forget:**
- Upload the 2-minute video
- Add screenshots of the app (map, drilldown, scatter plot)
- Link to GitHub repo
- Tag: Databricks x UN Geo-Insight Challenge + Pure Imagination track

---

### HIGH PRIORITY — Strong Impact on Score

#### 4. Run Databricks Notebook (30-45 min)
The `notebooks/full_pipeline.ipynb` is code-complete but needs to be run in Databricks to produce cell outputs.

```
1. Create a free Databricks Community Edition workspace (if you haven't)
2. Upload full_pipeline.ipynb
3. Run all cells — they download data live from UN APIs
4. Export the notebook with outputs (File → Export → HTML or DBC)
5. Save the exported version for submission
```

This serves two purposes:
- **Judges can audit** the full methodology
- **Databricks Raffle** — record a short video of the notebook running for raffle entry

#### 5. Databricks Raffle Video (10 min)
- Screen-record the Databricks notebook running (30-60 seconds)
- Show the data loading, OCI computation, and choropleth visualization cells
- Submit via the raffle form
- This is essentially free — just a screen recording

---

### NICE TO HAVE — Extra Prize Pools

#### 6. Figma Make Individual Submission (2-3 hours, one team member)
One team member can submit individually for an extra prize pool.

```
1. Export data/processed/oci_scores.csv (12KB — well under 5MB limit)
2. Build an interactive choropleth in Figma Make using this data
3. Record a 1-minute demo video
4. Submit individually on Devpost (separate submission)
5. Fill out Google Form: https://forms.gle/ktXCtaqgzh25Asak8
```

#### 7. Visual Polish (if time allows, 30-60 min)
These are small improvements that could push the Clarity score higher:

- [ ] Add a CrisisLens logo/header image to app.py
- [ ] Add country flags or emoji indicators next to country names
- [ ] Customize Streamlit theme colors in `.streamlit/config.toml`:
  ```toml
  [theme]
  primaryColor = "#e74c3c"
  backgroundColor = "#0e1117"
  secondaryBackgroundColor = "#1a1a2e"
  textColor = "#fafafa"
  ```
- [ ] Add a "Data last updated" timestamp on the home page
- [ ] Make the OCI ranking table on the map page clickable (select country from table)

---

## Submission Checklist

| Submission | Platform | Status | Deadline |
|---|---|---|---|
| Databricks x UN Geo-Insight | Devpost (team) | **Not submitted** | Feb 23 |
| Pure Imagination Track | Devpost (same submission) | **Not submitted** | Feb 23 |
| Actian VectorAI DB | Devpost (same submission) | **Code done** — mention in write-up | Feb 23 |
| Figma Make | Devpost (individual) + Google Form | **Not started** | Feb 23 |
| Databricks Raffle | Raffle form + video | **Not started** | Feb 23 |

---

## Quick Commands Reference

```bash
# Run the app locally
streamlit run app.py

# Re-run data pipeline (if data needs refresh)
python utils/data_loader.py

# Run tests
python -m pytest tests/ -v

# Check linting
ruff check .

# Check git status
git status
```

---

## Team Task Assignment Suggestion

| Person | Tasks | Time |
|---|---|---|
| Person A | Deploy Streamlit + Devpost write-up | ~1.5 hours |
| Person B | Record & edit pitch video | ~1 hour |
| Person C | Run Databricks notebook + raffle video | ~45 min |
| Person D (individual) | Figma Make submission | ~2 hours |

All tasks can be done **in parallel**. The video is the most important single deliverable after deployment.
