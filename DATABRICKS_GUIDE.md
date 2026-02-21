# Databricks Guide for CrisisLens

> Step-by-step walkthrough for someone who has never used Databricks.
> Covers: account setup, running our notebook, exporting for judges, and raffle video.

---

## Table of Contents

1. [Create Your Account](#1-create-your-account)
2. [Your First Time in the Workspace](#2-your-first-time-in-the-workspace)
3. [Import Our Notebook](#3-import-our-notebook)
4. [Connect to Compute](#4-connect-to-compute)
5. [Run the Notebook](#5-run-the-notebook)
6. [Troubleshooting Common Issues](#6-troubleshooting-common-issues)
7. [Export for Judge Submission](#7-export-for-judge-submission)
8. [Record the Databricks Raffle Video](#8-record-the-databricks-raffle-video)
9. [Quick Reference](#9-quick-reference)

---

## 1. Create Your Account

> **Important:** Databricks Community Edition was retired on Jan 1, 2026.
> The replacement is **Databricks Free Edition** — it's better and still free.

### Steps

1. Go to: **https://www.databricks.com/try-databricks**
2. Click **"Get started for free"** (NOT the cloud trial with credit card)
3. Sign up with your **Google account** or **email**
   - Use your GT email if you want — either works
4. When asked, choose **"Free Edition"**
   - Do NOT pick AWS/Azure/GCP trial — those need a credit card
5. Your workspace is automatically created. You'll land at a URL like:
   ```
   https://your-workspace-id.cloud.databricks.com
   ```
6. Bookmark this URL — this is your Databricks home

### What You Get (Free, No Credit Card)

- Serverless compute (auto-managed, no cluster setup needed)
- Notebooks with Python, SQL, R, Scala support
- Built-in Plotly chart rendering
- File storage
- Daily fair-use compute quota (more than enough for our project)

---

## 2. Your First Time in the Workspace

When you log in, you'll see the Databricks home screen. Here's what matters:

```
┌─────────────────────────────────────────────────────────┐
│  [Home icon]  Home          ← Your personal dashboard   │
│  [Folder]     Workspace     ← Where notebooks live      │
│  [Play]       Compute       ← Managed for you           │
│  [DB icon]    SQL            ← Not needed for us        │
│  [Gear]       Settings       ← Not needed for us        │
└─────────────────────────────────────────────────────────┘
```

**Click "Workspace"** in the left sidebar — that's where we'll work.

---

## 3. Import Our Notebook

Our notebook is at `notebooks/full_pipeline.ipynb` in the project repo.

### Steps

1. Click **Workspace** in the left sidebar
2. You'll see your home folder (usually `/Users/your-email@example.com/`)
3. Click on your home folder to open it
4. Click the **kebab menu** (three dots ⋮) at the top right, OR right-click in the folder
5. Select **"Import"**
6. In the dialog:
   - Click **"browse"** or drag-and-drop
   - Select `notebooks/full_pipeline.ipynb` from your local computer
   - (It's in the `crisis-lens/notebooks/` folder)
7. Click **"Import"**
8. The notebook appears in your folder — click it to open

### What Just Happened

Databricks converted our `.ipynb` Jupyter notebook into its native format.
All the cells (code + markdown) are preserved exactly as-is.

---

## 4. Connect to Compute

Before you can run any code, you need to connect to a compute engine.

### Steps

1. With the notebook open, look at the **top-right toolbar**
2. You'll see a **"Connect"** dropdown button
3. Click it → select **"Serverless"**
4. Wait 10-15 seconds for the green indicator (it says "Connected")

```
┌──────────────────────────────────────────────────────┐
│  [full_pipeline]                    [Connect ▼]      │
│                                     → Serverless  ✓  │
└──────────────────────────────────────────────────────┘
```

That's it. No cluster configuration, no waiting for VMs to spin up.
Serverless means Databricks handles all the infrastructure.

> **If "Serverless" doesn't appear:** Check that the Hacklytics organizers
> haven't given you a separate workspace with credits. Ask on Discord.

---

## 5. Run the Notebook

### Step 5a: Install Dependencies

The **first cell** (cell 2 in our notebook) has pip installs commented out.
You need to **uncomment** the `%pip` line:

1. Find the cell that says:
   ```python
   # Uncomment the line below when running in Databricks
   # %pip install pandas numpy scipy scikit-learn plotly requests
   ```

2. **Remove the `#`** from the pip line so it reads:
   ```python
   %pip install pandas numpy scipy scikit-learn plotly requests
   ```

3. Run this cell first (Shift+Enter)

4. **The kernel will restart** after the install — this is normal!
   You'll see a message like "Python kernel restarted"

> **Important Databricks rule:** `%pip` must be the ONLY command in its cell.
> Don't put any other code in the same cell as `%pip install`.

### Step 5b: Run All Cells

After the pip install + restart:

1. Click **"Run all"** in the top toolbar
   - OR go to **Run menu → Run All**
   - OR manually Shift+Enter through each cell

2. The notebook will execute top-to-bottom:
   - Steps 1-4: Downloads data live from UN APIs (~30-60 seconds)
   - Step 5: Computes OCI scores
   - Step 6: Renders the choropleth map (you'll see it inline!)
   - Steps 7-9: Cluster analysis + outlier detection
   - Step 10: Runs the recommender demo

3. **Total runtime: about 2-3 minutes**

### What You'll See

Each cell shows its output directly below it:

- **DataFrames** render as nice formatted tables
- **Print statements** show as text output
- **Plotly charts** render as interactive visualizations (you can hover, zoom!)
- **Progress messages** like "HNO 2026: 14532 rows, 9 columns"

### Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| Run cell + move to next | **Shift + Enter** |
| Run cell + stay | **Ctrl + Enter** |
| Run all cells | **Run menu → Run All** |
| Add cell below | Press **B** (when not in edit mode) |
| Add cell above | Press **A** (when not in edit mode) |
| Delete cell | Press **D, D** (double-tap D) |
| Toggle markdown/code | Press **M** or **Y** |

---

## 6. Troubleshooting Common Issues

### "ModuleNotFoundError: No module named 'sklearn'"
→ You forgot to uncomment and run the `%pip install` cell. Go back to Step 5a.

### "Kernel restarted" after pip install
→ This is **normal and expected**. Just continue running the remaining cells.

### Cell takes forever (> 2 minutes)
→ The CBPF API download (Step 8) can be slow. Give it up to 3 minutes.
   If it truly hangs, click the stop button and re-run just that cell.

### "Quota exceeded" error
→ Free Edition has a daily compute quota. If you hit it:
   - Wait until tomorrow (quota resets daily)
   - OR ask the Hacklytics Databricks sponsors for credits

### Plotly chart doesn't render
→ Make sure you ran the `%pip install plotly` cell. Databricks serverless
   may not have Plotly pre-installed. After installing, restart and re-run.

### "Connection lost" or compute disconnects
→ Click "Connect" → "Serverless" again. Your notebook state is preserved
   but you'll need to re-run cells from the top (variables are lost on disconnect).

---

## 7. Export for Judge Submission

After all cells have run successfully and you can see outputs:

### Export as HTML (recommended for judges)

1. With the notebook open and all outputs visible
2. Click **File** in the notebook toolbar (top-left area)
3. Click **"Export"**
4. Select **"HTML"**
5. Make sure **"Include outputs"** is checked
6. Click **Export** — file downloads to your computer

The HTML file is a single self-contained file that anyone can open in a browser.
It includes all your code, markdown, tables, AND the interactive Plotly charts.

### Export as .ipynb (for technical review)

Same steps, but select **"IPython Notebook (.ipynb)"** instead of HTML.
This preserves outputs and lets judges re-run it if they want.

### What to Submit

Submit **both** files:
- `full_pipeline.html` — for easy reading (no software needed)
- `full_pipeline.ipynb` — for technical judges who want to inspect/re-run

Upload these to your Devpost submission under "Additional files" or link from your GitHub repo.

---

## 8. Record the Databricks Raffle Video

The Databricks raffle just needs a short video showing you used Databricks.

### What to Record (30-60 seconds)

1. Show the Databricks workspace with your notebook open
2. Run a few cells — show data loading and OCI computation
3. Show the Plotly choropleth rendering inside Databricks
4. Show the final OCI results table

### How to Record on Windows

**Option A: Xbox Game Bar (built-in)**
1. Press **Win + G** to open Game Bar
2. Click the record button (circle icon) or press **Win + Alt + R**
3. Do your demo
4. Press **Win + Alt + R** again to stop recording
5. Video saves to `C:\Users\YourName\Videos\Captures\`

**Option B: OBS Studio (better quality)**
1. Download OBS from https://obsproject.com
2. Add a "Window Capture" source → select your browser with Databricks
3. Click "Start Recording"
4. Demo the notebook
5. Click "Stop Recording"

### Script for the Raffle Video

> "This is CrisisLens running on Databricks. We used Databricks to process
> UN humanitarian data from five sources — HNO needs data, FTS funding data,
> population data, cluster-level funding, and CBPF project data. Our pipeline
> downloads the data live, cleans it, computes the Overlooked Crisis Index,
> and runs efficiency outlier detection on over 8,000 CBPF projects.
> Here you can see the OCI choropleth map rendered directly in Databricks."

(While saying this, scroll through the notebook showing cells running and outputs.)

### Where to Submit

Check the Hacklytics Discord for the raffle submission form link.
It's typically a Google Form where you paste a video link (upload to YouTube unlisted or Google Drive).

---

## 9. Quick Reference

### Account
- **Sign up:** https://www.databricks.com/try-databricks → Free Edition
- **Login:** https://accounts.cloud.databricks.com

### In Databricks
```
1. Workspace → Import → upload full_pipeline.ipynb
2. Open notebook → Connect → Serverless
3. Uncomment %pip install cell → Run it → Kernel restarts (normal)
4. Run All cells (takes ~2-3 min)
5. File → Export → HTML (include outputs) → Download
```

### Files to Submit
| File | Purpose | Where |
|---|---|---|
| `full_pipeline.html` | Judges can read methodology | Devpost + GitHub |
| `full_pipeline.ipynb` | Judges can re-run | GitHub repo |
| Raffle video (30-60s) | Shows Databricks usage | Raffle submission form |

### Key Data Points for the Video
- 65 OCI-scored crises across 24 countries (2024-2026)
- 8,400+ CBPF projects analyzed for efficiency
- South Sudan: OCI 1.000 (most overlooked — 9.9M people in need, 89.5% gap)
- Sudan: OCI 0.862 (33.7M people in need, 87.0% gap)
- Haiti: OCI 0.725 (6.4M people in need, 96.3% gap — worst funding gap)

---

## Still Stuck?

- **Databricks docs:** https://docs.databricks.com
- **Ask on Hacklytics Discord** — other teams + Databricks mentors can help
- **Databricks sponsor booth** at the event — they're there to help you use their platform
