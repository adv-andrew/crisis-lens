"""Rebuild the visualization section of full_pipeline.ipynb with academic theme."""
import json

NB_PATH = "C:/Users/andyv/hacklytics/crisis/crisis-lens/notebooks/full_pipeline.ipynb"

with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)


def fix_src(text):
    lines = text.strip().split("\n")
    return [line + "\n" for line in lines[:-1]] + [lines[-1]]


def code_cell(source):
    return {
        "cell_type": "code", "execution_count": None, "metadata": {},
        "outputs": [], "source": fix_src(source),
    }


def md_cell(source):
    return {"cell_type": "markdown", "metadata": {}, "source": fix_src(source)}


# ── New cells ──────────────────────────────────────────────────────

viz_heading = md_cell(
    "## Step 8: Visualizations\n\n"
    "All charts use a consistent publication-quality theme: white background, "
    "colorblind-safe Tol Bright palette, sans-serif typography, and minimal gridlines. "
    "Style reference: Davidson et al. (2025)."
)

theme = code_cell(r'''# ── CrisisLens Publication-Quality Chart Theme ─────────────────────
import plotly.io as pio

# Tol Bright colorblind-safe palette
C_BLUE   = "#0072B2"
C_ORANGE = "#D55E00"
C_GREEN  = "#009E73"
C_PINK   = "#CC79A7"
C_YELLOW = "#F0E442"
C_SKY    = "#56B4E9"
C_GRAY   = "#999999"
C_RED    = "#CC3311"

# OCI severity color scale (green -> yellow -> orange -> red)
OCI_COLORSCALE = [[0, C_GREEN], [0.35, C_YELLOW], [0.65, C_ORANGE], [1.0, C_RED]]

# Build Plotly template
_layout = go.Layout(
    font=dict(family="Helvetica, Arial, sans-serif", size=12, color="#333"),
    paper_bgcolor="white", plot_bgcolor="white",
    title=dict(font=dict(size=16, color="#222"), x=0.0, xanchor="left"),
    xaxis=dict(gridcolor="rgba(0,0,0,0.06)", gridwidth=0.5, linecolor="#CCC", linewidth=0.8,
               title_font=dict(size=11, color="#555"), tickfont=dict(size=10, color="#555"),
               showgrid=True, ticks="outside", ticklen=4, tickcolor="#CCC"),
    yaxis=dict(gridcolor="rgba(0,0,0,0.06)", gridwidth=0.5, linecolor="#CCC", linewidth=0.8,
               title_font=dict(size=11, color="#555"), tickfont=dict(size=10, color="#555"),
               showgrid=True, ticks="outside", ticklen=4, tickcolor="#CCC"),
    colorway=[C_BLUE, C_ORANGE, C_GREEN, C_PINK, C_SKY, C_YELLOW, C_GRAY],
    margin=dict(l=60, r=20, t=50, b=40),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#DDD", borderwidth=0.5,
                font=dict(size=10)),
    hoverlabel=dict(bgcolor="white", font_size=11, font_color="#333", bordercolor="#CCC"),
)
pio.templates["crisislens"] = go.layout.Template(layout=_layout)
pio.templates.default = "crisislens"

print("Publication-quality chart theme loaded")''')

md_8a = md_cell("### 8a: OCI Choropleth World Map")

choropleth = code_cell(r'''df_map = df_oci.sort_values("year", ascending=False).drop_duplicates("country_iso3")

fig = px.choropleth(
    df_map, locations="country_iso3", locationmode="ISO-3",
    color="oci_score",
    color_continuous_scale=OCI_COLORSCALE,
    range_color=(0, 1),
    hover_name="country_name",
    hover_data={"oci_score": ":.3f", "funding_gap": ":.1%", "media_score": ":.2f",
                "people_in_need_k": ":,.0f", "country_name": False, "country_iso3": False},
    labels={"oci_score": "OCI Score", "funding_gap": "Funding Gap",
            "media_score": "Media Neglect", "people_in_need_k": "People in Need (k)"},
)
fig.update_layout(
    title="Overlooked Crisis Index — Global Map",
    height=520,
    geo=dict(
        showframe=False, projection_type="natural earth",
        bgcolor="white", landcolor="#F0F0F0", oceancolor="white",
        lakecolor="white", coastlinecolor="#BBB", countrycolor="#DDD",
        showocean=True, showlakes=True,
    ),
    coloraxis_colorbar=dict(
        title="OCI", titleside="right", thickness=12, len=0.55,
        tickvals=[0, 0.25, 0.5, 0.75, 1.0],
        tickfont=dict(size=9), outlinewidth=0.5, outlinecolor="#CCC",
    ),
    margin=dict(l=0, r=0, t=40, b=0),
)
fig.show()''')

md_8b = md_cell("### 8b: Top 10 Most Overlooked — OCI Decomposition")

bar_chart = code_cell(r'''df_top10 = df_map.nlargest(10, "oci_score").sort_values("oci_score")

fig = make_subplots(
    rows=1, cols=2, column_widths=[0.52, 0.48],
    subplot_titles=["OCI Score", "Component Breakdown"],
    horizontal_spacing=0.14,
)

# Left: OCI bars
bar_colors = [C_RED if s > 0.7 else C_ORANGE if s > 0.4 else C_GREEN for s in df_top10["oci_score"]]
fig.add_trace(go.Bar(
    y=df_top10["country_name"], x=df_top10["oci_score"], orientation="h",
    marker=dict(color=bar_colors, line=dict(width=0.5, color="white")),
    text=df_top10["oci_score"].apply(lambda s: f"{s:.3f}"),
    textposition="outside", textfont=dict(size=10), showlegend=False,
), row=1, col=1)

# Right: grouped component bars
for col_name, color, label in [
    ("pin_normalized", C_RED, "PIN / Population"),
    ("severity_weight", C_ORANGE, "Severity"),
    ("funding_gap", "#882255", "Funding Gap"),
    ("media_score", C_BLUE, "Media Neglect"),
]:
    fig.add_trace(go.Bar(
        y=df_top10["country_name"], x=df_top10[col_name], orientation="h",
        name=label, marker=dict(color=color, line=dict(width=0.3, color="white")),
    ), row=1, col=2)

fig.update_layout(
    height=480, barmode="group",
    title="Top 10 Most Overlooked Crises — OCI Decomposition",
    legend=dict(orientation="h", yanchor="bottom", y=1.06, xanchor="center", x=0.76),
    margin=dict(l=10, r=10, t=70, b=10),
)
fig.update_xaxes(range=[0, 1.12], showgrid=False, row=1, col=1)
fig.update_xaxes(range=[0, 1.12], showgrid=False, row=1, col=2)
fig.update_yaxes(tickfont=dict(size=11), row=1, col=1)
fig.update_yaxes(showticklabels=False, row=1, col=2)
for ann in fig.layout.annotations:
    ann.font = dict(size=12, color="#555")
fig.show()''')

md_8c = md_cell("### 8c: Media Attention vs. Funding Gap — The Double Neglect Scatter")

scatter = code_cell(r'''df_map["_bubble_size"] = df_map["people_in_need_k"].clip(lower=200)

fig = px.scatter(
    df_map, x="media_score", y="funding_gap",
    size="_bubble_size", size_max=50,
    color="oci_score",
    color_continuous_scale=OCI_COLORSCALE,
    range_color=(0, 1),
    hover_name="country_name",
    hover_data={"oci_score": ":.3f", "people_in_need_k": ":,.0f",
                "requirements_usd_m": ":,.0f", "country_name": False,
                "_bubble_size": False, "country_iso3": False},
    labels={"media_score": "Media Neglect (1 = invisible)",
            "funding_gap": "Funding Gap (1 = unfunded)",
            "oci_score": "OCI", "people_in_need_k": "People in Need (k)"},
)

# Quadrant shading
fig.add_shape(type="rect", x0=0.5, x1=1.05, y0=0.5, y1=1.05,
              fillcolor="rgba(204,51,17,0.04)", line=dict(width=0))
fig.add_shape(type="rect", x0=-0.05, x1=0.5, y0=-0.05, y1=0.5,
              fillcolor="rgba(0,158,115,0.03)", line=dict(width=0))

# Divider lines
fig.add_hline(y=0.5, line_dash="dot", line_color="rgba(0,0,0,0.15)", line_width=0.8)
fig.add_vline(x=0.5, line_dash="dot", line_color="rgba(0,0,0,0.15)", line_width=0.8)

# Quadrant labels
fig.add_annotation(x=0.92, y=0.98, text="MOST OVERLOOKED", showarrow=False,
                   font=dict(size=11, color=C_RED), opacity=0.8)
fig.add_annotation(x=0.08, y=0.97, text="Underfunded<br>but visible", showarrow=False,
                   font=dict(size=9, color="#999"))
fig.add_annotation(x=0.92, y=0.03, text="Invisible<br>but funded", showarrow=False,
                   font=dict(size=9, color="#999"))
fig.add_annotation(x=0.08, y=0.03, text="Covered &<br>funded", showarrow=False,
                   font=dict(size=9, color=C_GREEN), opacity=0.6)

# Label top 6 crises
for _, row in df_map.nlargest(6, "oci_score").iterrows():
    fig.add_annotation(
        x=row["media_score"], y=row["funding_gap"],
        text=row["country_name"], showarrow=True,
        arrowhead=0, arrowwidth=0.8, arrowcolor="#BBB",
        ax=28, ay=-22,
        font=dict(size=9, color="#333"),
        bgcolor="rgba(255,255,255,0.85)", borderpad=2,
    )

fig.update_layout(
    title="Double Neglect: Crises that are Underfunded AND Invisible",
    height=550,
    xaxis=dict(range=[-0.05, 1.05], dtick=0.25),
    yaxis=dict(range=[-0.05, 1.05], dtick=0.25),
    coloraxis_colorbar=dict(title="OCI", thickness=12, len=0.5,
                            outlinewidth=0.5, outlinecolor="#CCC"),
    margin=dict(l=50, r=20, t=50, b=40),
)
df_map.drop(columns=["_bubble_size"], inplace=True, errors="ignore")
fig.show()''')

interp = md_cell(
    "> **Interpretation:** The upper-right quadrant contains crises that are "
    "**both underfunded and invisible** — the strongest signal for proactive "
    "intervention. Bubble size represents the absolute number of people in need."
)

md_8d = md_cell("### 8d: Funding Gap by Cluster (Cleaned)")

cluster = code_cell(r'''# Clean cluster data
df_cluster = df_cluster_raw.rename(columns={
    "countryCode": "country_iso3", "cluster": "cluster_name",
    "requirements": "requirements_usd", "funding": "funding_usd", "year": "year",
})

exclude_clusters = {"Not specified", "Multiple clusters/sectors (shared)",
                    "CLUSTER NOT YET SPECIFIED", "Multi-Cluster", "Cluster not yet specified"}
df_cluster = df_cluster[
    df_cluster["cluster_name"].notna()
    & ~df_cluster["cluster_name"].isin(exclude_clusters)
    & ~df_cluster["cluster_name"].str.contains("not yet specified|NOT YET", case=False, na=False)
].copy()

cluster_normalize = {
    "Nutirition": "Nutrition", "Water Sanitation Hygiene": "WASH",
    "Water, Sanitation and Hygiene": "WASH",
    "Emergency Shelter and NFI": "Shelter/NFI", "Emergency Shelter/NFI": "Shelter/NFI",
    "Camp Coordination / Management": "Camp Coordination",
    "Camp Coordination and Camp Management": "Camp Coordination",
}
df_cluster["cluster_name"] = df_cluster["cluster_name"].replace(cluster_normalize)

for col in ["requirements_usd", "funding_usd"]:
    df_cluster[col] = pd.to_numeric(df_cluster[col], errors="coerce")
df_cluster["year"] = pd.to_numeric(df_cluster["year"], errors="coerce")

df_cluster["funding_gap"] = np.where(
    df_cluster["requirements_usd"] > 0,
    1 - df_cluster["funding_usd"].fillna(0) / df_cluster["requirements_usd"], np.nan,
)
df_cluster["funding_gap"] = pd.to_numeric(pd.Series(df_cluster["funding_gap"]), errors="coerce").clip(0, 1)

latest_year = int(df_cluster["year"].max())
latest_cluster = df_cluster[df_cluster["year"] == latest_year]
cluster_avg = (
    latest_cluster.groupby("cluster_name")
    .agg(avg_gap=("funding_gap", "mean"), total_req=("requirements_usd", "sum"),
         n_plans=("funding_gap", "count"))
    .query("n_plans >= 3")
    .sort_values("avg_gap", ascending=True)
    .reset_index()
)

bar_colors = [C_RED if g > 0.7 else C_ORANGE if g > 0.4 else C_GREEN for g in cluster_avg["avg_gap"]]

fig = go.Figure(go.Bar(
    y=cluster_avg["cluster_name"], x=cluster_avg["avg_gap"], orientation="h",
    marker=dict(color=bar_colors, line=dict(width=0.5, color="white")),
    text=cluster_avg["avg_gap"].apply(lambda g: f"{g:.0%}"),
    textposition="outside", textfont=dict(size=10, color="#555"),
    hovertemplate="<b>%{y}</b><br>Avg Gap: %{x:.1%}<br>Plans: %{customdata[0]}<extra></extra>",
    customdata=cluster_avg[["n_plans"]].values,
))

fig.add_vline(x=0.5, line_dash="dash", line_color="rgba(0,0,0,0.1)", line_width=0.8)

fig.update_layout(
    title=f"Cluster-Level Funding Gaps — Global, {latest_year}",
    height=max(350, len(cluster_avg) * 32),
    xaxis=dict(range=[0, 1.12], tickformat=".0%", title="Average Funding Gap", showgrid=False),
    yaxis=dict(title="", tickfont=dict(size=11)),
    margin=dict(l=10, r=10, t=50, b=10), showlegend=False,
)
fig.show()''')

# ── Now rebuild the forecast and efficiency charts too ──────────

# Find the forecast and efficiency cells
forecast_md_idx = None
forecast_code_idx = None
forecast_viz_idx = None
efficiency_md_idx = None
efficiency_code_idx = None
efficiency_viz_idx = None

for i, cell in enumerate(nb["cells"]):
    src = "".join(cell["source"])
    if "Step 9: Funding Forecast" in src:
        forecast_md_idx = i
    if "forecast_results = []" in src:
        forecast_code_idx = i
    if "Visualize forecast for top" in src and cell["cell_type"] == "code":
        forecast_viz_idx = i
    if "Step 10: CBPF Project Efficiency" in src:
        efficiency_md_idx = i
    if "# Clean CBPF data" in src or "df_cbpf = df_cbpf_raw" in src:
        efficiency_code_idx = i
    if "Scatter: Budget vs. Beneficiaries" in src and cell["cell_type"] == "code":
        efficiency_viz_idx = i

# New forecast viz cell
forecast_viz = code_cell(r'''# Visualize forecast for top 3 at-risk crises
n_panels = min(3, len(df_at_risk))
panel_titles = [r["country_name"] for _, r in df_at_risk.head(n_panels).iterrows()]
fig = make_subplots(rows=1, cols=n_panels, subplot_titles=panel_titles, horizontal_spacing=0.08)

for i, (_, fr) in enumerate(df_at_risk.head(n_panels).iterrows()):
    col = i + 1
    hist = df_oci[df_oci["country_iso3"] == fr["country_iso3"]].sort_values("year")
    hist = hist.dropna(subset=["funding_gap", "year"])
    intercept = fr["proj_gap_2027"] - fr["slope"] * 2027

    # Confidence band
    last_year = int(hist["year"].max())
    band_years = list(range(last_year, 2028))
    margin_up = fr["proj_upper"] - fr["proj_gap_2027"]
    margin_dn = fr["proj_gap_2027"] - fr["proj_lower"]
    band_upper = [float(np.clip(fr["slope"] * y + intercept + margin_up, 0, 1)) for y in band_years]
    band_lower = [float(np.clip(fr["slope"] * y + intercept - margin_dn, 0, 1)) for y in band_years]

    fig.add_trace(go.Scatter(
        x=band_years, y=band_upper, mode="lines",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ), row=1, col=col)
    fig.add_trace(go.Scatter(
        x=band_years, y=band_lower, mode="lines",
        line=dict(width=0), fill="tonexty",
        fillcolor="rgba(204,51,17,0.12)",
        showlegend=(i == 0), name="90% Prediction Interval",
    ), row=1, col=col)

    # Trend line
    all_years = list(range(int(hist["year"].min()), 2028))
    trend_y = [float(np.clip(fr["slope"] * y + intercept, 0, 1)) for y in all_years]
    fig.add_trace(go.Scatter(
        x=all_years, y=trend_y, mode="lines", name="Trend",
        line=dict(color=C_GRAY, width=1.5, dash="dot"), showlegend=(i == 0),
    ), row=1, col=col)

    # Historical
    fig.add_trace(go.Scatter(
        x=hist["year"], y=hist["funding_gap"], mode="lines+markers",
        name="Historical", line=dict(color=C_BLUE, width=2.5),
        marker=dict(size=8, color=C_BLUE, line=dict(width=1.5, color="white")),
        showlegend=(i == 0),
    ), row=1, col=col)

    # 2027 projection
    fig.add_trace(go.Scatter(
        x=[2027], y=[fr["proj_gap_2027"]], mode="markers", name="2027 Projected",
        marker=dict(color=C_RED, size=14, symbol="star",
                    line=dict(width=1.5, color="white")),
        showlegend=(i == 0),
    ), row=1, col=col)

    # p-value annotation
    sig_text = f"p = {fr['p_value']:.3f}" if fr["p_value"] >= 0.001 else "p < 0.001"
    sig_color = C_RED if fr["p_value"] < 0.1 else C_GRAY
    fig.add_annotation(
        x=2025.5, y=0.1, text=sig_text,
        showarrow=False, font=dict(size=10, color=sig_color), row=1, col=col,
    )

    fig.update_yaxes(range=[0, 1.05], tickformat=".0%", row=1, col=col)
    fig.update_xaxes(dtick=1, row=1, col=col)

fig.update_layout(
    height=400,
    title="Funding Gap Forecasts — Top 3 At-Risk Crises",
    legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
    margin=dict(l=10, r=10, t=80, b=10),
)
for ann in fig.layout.annotations:
    if ann.text in panel_titles:
        ann.font = dict(size=12, color="#555")
fig.show()''')

# New efficiency scatter cell
efficiency_viz = code_cell(r'''# Scatter: Budget vs. Beneficiaries colored by efficiency flag
df_scatter = df_cbpf[
    (df_cbpf["Budget"] > 0) & (df_cbpf["beneficiaries_total"] > 0)
].copy()

fig = go.Figure()

# Normal projects — muted background dots
normal = df_scatter[df_scatter["flag"].isin(["normal", "insufficient_data"])]
fig.add_trace(go.Scatter(
    x=normal["Budget"], y=normal["beneficiaries_total"],
    mode="markers", name=f"Normal ({len(normal):,})",
    marker=dict(size=3.5, color=C_GRAY, opacity=0.15, line=dict(width=0)),
    hovertemplate="<b>%{customdata[0]}</b><br>$%{x:,.0f}<br>%{y:,.0f} ben<extra></extra>",
    customdata=normal[["ChfProjectCode"]].values,
))

# Benchmarks — prominent green
high_eff = df_scatter[df_scatter["flag"] == "high_efficiency"]
fig.add_trace(go.Scatter(
    x=high_eff["Budget"], y=high_eff["beneficiaries_total"],
    mode="markers", name=f"Benchmark ({len(high_eff):,})",
    marker=dict(size=7, color=C_GREEN, opacity=0.75,
                line=dict(width=0.8, color="white")),
    hovertemplate="<b>%{customdata[0]}</b><br>$%{x:,.0f}<br>%{y:,.0f} ben<br>z=%{customdata[1]:.2f}<extra></extra>",
    customdata=high_eff[["ChfProjectCode", "zscore"]].values,
))

# Low efficiency — red
low_eff = df_scatter[df_scatter["flag"] == "low_efficiency"]
if not low_eff.empty:
    fig.add_trace(go.Scatter(
        x=low_eff["Budget"], y=low_eff["beneficiaries_total"],
        mode="markers", name=f"Low Efficiency ({len(low_eff):,})",
        marker=dict(size=7, color=C_RED, opacity=0.75,
                    line=dict(width=0.8, color="white")),
        hovertemplate="<b>%{customdata[0]}</b><br>$%{x:,.0f}<br>%{y:,.0f} ben<br>z=%{customdata[1]:.2f}<extra></extra>",
        customdata=low_eff[["ChfProjectCode", "zscore"]].values,
    ))

# Iso-efficiency reference lines
for ratio, label in [(0.01, "0.01 ben/$"), (0.1, "0.1 ben/$"), (1.0, "1.0 ben/$")]:
    x_range = np.array([1e3, 1e8])
    fig.add_trace(go.Scatter(
        x=x_range, y=x_range * ratio, mode="lines",
        line=dict(color="rgba(0,0,0,0.06)", width=1, dash="dot"),
        showlegend=False, hoverinfo="skip",
    ))

fig.update_layout(
    title="Project Efficiency: Budget vs. Beneficiaries",
    height=520,
    xaxis=dict(type="log", title="Budget (USD)", tickprefix="$",
               gridcolor="rgba(0,0,0,0.04)"),
    yaxis=dict(type="log", title="Beneficiaries",
               gridcolor="rgba(0,0,0,0.04)"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    margin=dict(l=10, r=10, t=50, b=10),
)

# Summary callout
fig.add_annotation(
    x=0.98, y=0.02, xref="paper", yref="paper",
    text=f"{len(high_eff):,} benchmarks at 15.6x median efficiency",
    showarrow=False, font=dict(size=11, color=C_GREEN),
    bgcolor="rgba(0,158,115,0.08)", borderpad=5, xanchor="right",
)
fig.show()''')

# ── Assemble final notebook ────────────────────────────────────────

# Find section boundaries
kept_before = nb["cells"][:18]  # cells 0-17 (up to Delta write cell)

# Find the Delta write cell (cell with "if DATABRICKS" that's the Step 7 one)
delta_cell = None
for i, cell in enumerate(nb["cells"][:20]):
    src = "".join(cell["source"])
    if "DATABRICKS" in src and "Delta Lake write" in src:
        delta_cell = nb["cells"][i]
        break
if delta_cell is None:
    delta_cell = nb["cells"][18]

# Find forecast computation cell
forecast_compute = None
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if "forecast_results = []" in src:
        forecast_compute = cell
        break

# Find forecast markdown
forecast_md = None
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if "Step 9: Funding Forecast" in src and cell["cell_type"] == "markdown":
        forecast_md = cell
        break

# Find at-risk table display (the part after forecast_results computation)
# It's in the same cell as forecast_compute, so we already have it

# Find efficiency markdown
efficiency_md = None
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if "Step 10: CBPF Project Efficiency" in src and cell["cell_type"] == "markdown":
        efficiency_md = cell
        break

# Find CBPF data cleaning cell
cbpf_clean = None
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if "df_cbpf = df_cbpf_raw" in src or "# Clean CBPF data" in src:
        cbpf_clean = cell
        break

# Find recommender and everything after
recommender_and_after = []
found_recommender = False
for cell in nb["cells"]:
    src = "".join(cell["source"])
    if "Step 11: Project Recommender" in src:
        found_recommender = True
    if found_recommender:
        recommender_and_after.append(cell)

# Build final notebook
nb["cells"] = (
    kept_before
    + [delta_cell]
    # Step 8: Visualizations
    + [viz_heading, theme, md_8a, choropleth, md_8b, bar_chart, md_8c, scatter, interp, md_8d, cluster]
    # Step 9: Forecast
    + [forecast_md, forecast_compute, forecast_viz]
    # Step 10: Efficiency
    + [efficiency_md, cbpf_clean, efficiency_viz]
    # Steps 11+: Recommender, Delta write, Conclusions
    + recommender_and_after
)

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"Notebook rebuilt: {len(nb['cells'])} cells")
for i, cell in enumerate(nb["cells"]):
    src = "".join(cell["source"])[:70]
    print(f"  {i:2d} | {cell['cell_type']:8s} | {src}")
