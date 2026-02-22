"""
generate_figures.py — publication-quality figures for the Crisis Lens paper.

reads processed CSVs from data/processed/ and raw cluster data,
produces vector PDF figures in figures/ and paper/figures/.

usage:
    python generate_figures.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from scipy import stats

# ---------------------------------------------------------------------------
# style setup (matches RESEARCH.md Figure Production Spec)
# ---------------------------------------------------------------------------
matplotlib.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman No9 L", "DejaVu Serif"],
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.5,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.linewidth": 0.8,
    "lines.linewidth": 2.0,
    "lines.markersize": 6,
    "errorbar.capsize": 3,
    "legend.framealpha": 0.9,
    "legend.edgecolor": "0.8",
})

# colorblind-safe palette
COLORS = {
    "blue": "#0072B2",
    "orange": "#D55E00",
    "green": "#009E73",
    "pink": "#CC79A7",
    "yellow": "#F0E442",
    "sky": "#56B4E9",
    "gray": "#999999",
    "red": "#CC3311",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
FIG_DIR = os.path.join(BASE_DIR, "figures")
PAPER_FIG_DIR = os.path.join(BASE_DIR, "..", "paper", "figures")
TEMP_DIR = os.path.join(BASE_DIR, "..", "temp")

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(PAPER_FIG_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


def save_fig(fig, name):
    """save to figures/, paper/figures/, and temp/ as PDF and PNG."""
    for d in [FIG_DIR, PAPER_FIG_DIR]:
        fig.savefig(os.path.join(d, f"{name}.pdf"), format="pdf")
    for d in [FIG_DIR, TEMP_DIR]:
        fig.savefig(os.path.join(d, f"{name}.png"), format="png", dpi=300)
    print(f"  saved {name}.pdf + .png")


# ---------------------------------------------------------------------------
# load data
# ---------------------------------------------------------------------------
df_oci = pd.read_csv(os.path.join(DATA_DIR, "oci_scores.csv"))
df_projects = pd.read_csv(os.path.join(DATA_DIR, "projects_clean.csv"))
df_cluster_raw = pd.read_csv(
    os.path.join(RAW_DIR, "fts_cluster.csv"), skiprows=[1], low_memory=False
)

print(f"loaded: {len(df_oci)} OCI rows, {len(df_projects)} projects, "
      f"{len(df_cluster_raw)} cluster rows")


# ===========================================================================
# figure 2: OCI choropleth world map
# ===========================================================================
def fig_oci_map():
    print("\ngenerating: oci_map")
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        import cartopy.io.shapereader as shpreader
        from matplotlib.colors import LinearSegmentedColormap

        df = df_oci.sort_values("year", ascending=False).drop_duplicates("country_iso3")
        oci_by_iso3 = dict(zip(df["country_iso3"], df["oci_score"]))

        # single-hue blue colormap
        oci_cmap = LinearSegmentedColormap.from_list(
            "oci_blue", ["#DEEBF7", "#6BAED6", "#08519C"], N=256
        )

        fig, ax = plt.subplots(
            figsize=(7, 3.8),
            subplot_kw={"projection": ccrs.Robinson()},
        )
        ax.set_global()

        # white ocean
        ax.add_feature(cfeature.OCEAN, facecolor="white", zorder=0)

        # light gray base land
        ax.add_feature(cfeature.LAND, facecolor="#ECECEC", edgecolor="none", zorder=1)

        # faint country borders
        ax.add_feature(cfeature.BORDERS, linewidth=0.2, edgecolor="#CCCCCC", zorder=2)

        # remove globe outline
        try:
            ax.outline_patch.set_visible(False)
        except AttributeError:
            ax.spines["geo"].set_visible(False)

        # fill scored countries with OCI color
        shapefile = shpreader.natural_earth(
            resolution="110m", category="cultural", name="admin_0_countries"
        )
        reader = shpreader.Reader(shapefile)

        for record in reader.records():
            iso3 = record.attributes["ADM0_A3"]
            if iso3 in oci_by_iso3:
                score = oci_by_iso3[iso3]
                color = oci_cmap(score)
                ax.add_geometries(
                    [record.geometry], ccrs.PlateCarree(),
                    facecolor=color, edgecolor="#444444",
                    linewidth=0.4, zorder=3,
                )

        # colorbar
        sm = plt.cm.ScalarMappable(cmap=oci_cmap, norm=plt.Normalize(0, 1))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.55, pad=0.02, aspect=22)
        cbar.set_label("OCI Score", fontsize=9)
        cbar.ax.tick_params(labelsize=8)
        cbar.outline.set_linewidth(0.4)

        fig.subplots_adjust(left=0.02, right=0.92, top=0.98, bottom=0.02)

        save_fig(fig, "oci_map")
        plt.close(fig)
    except ImportError:
        # fallback: bar chart if cartopy not available
        print("  cartopy not available, generating bar chart fallback")
        df = df_oci.sort_values("year", ascending=False).drop_duplicates("country_iso3")
        df_sorted = df.nlargest(15, "oci_score").sort_values("oci_score")

        from matplotlib.colors import LinearSegmentedColormap
        oci_cmap = LinearSegmentedColormap.from_list(
            "oci_blue", ["#DEEBF7", "#6BAED6", "#08519C"], N=256
        )
        colors = [oci_cmap(s) for s in df_sorted["oci_score"]]

        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.barh(
            df_sorted["country_name"], df_sorted["oci_score"],
            color=colors, edgecolor="white", linewidth=0.3,
        )
        ax.set_xlabel("OCI Score")
        ax.set_xlim(0, 1.05)
        for i, (_, row) in enumerate(df_sorted.iterrows()):
            ax.text(
                row["oci_score"] + 0.02, i, f"{row['oci_score']:.3f}",
                va="center", fontsize=8,
            )
        sns.despine(ax=ax, top=True, right=True)

        save_fig(fig, "oci_map")
        plt.close(fig)
    except Exception as e:
        print(f"  warning: oci_map generation failed: {e}")
        import traceback
        traceback.print_exc()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, f"OCI Map failed: {e}", ha="center", va="center",
                transform=ax.transAxes, fontsize=10)
        ax.set_axis_off()
        save_fig(fig, "oci_map")
        plt.close(fig)


# ===========================================================================
# figure 3: cluster-level funding gaps (South Sudan 2026)
# ===========================================================================
def fig_cluster_gap():
    print("\ngenerating: cluster_gap_ssd_2026")

    ssd = df_cluster_raw[
        (df_cluster_raw["countryCode"] == "SSD")
        & (df_cluster_raw["year"] == 2026)
    ].copy()

    # filter junk clusters
    exclude = {"Not specified", "Multiple clusters/sectors (shared)"}
    ssd = ssd[~ssd["cluster"].isin(exclude) & ssd["requirements"].notna()].copy()

    ssd["requirements"] = pd.to_numeric(ssd["requirements"], errors="coerce")
    ssd["funding"] = pd.to_numeric(ssd["funding"], errors="coerce").fillna(0)
    ssd["gap"] = ((ssd["requirements"] - ssd["funding"]) / ssd["requirements"]).clip(0, 1)

    # shorten long cluster names
    name_map = {
        "Camp Coordination  and Camp  Management": "Camp Coord.",
        "Camp Coordination and Camp Management": "Camp Coord.",
        "Coordination,  Thematic and  System Support": "Coord. Support",
        "Coordination, Thematic and System Support": "Coord. Support",
        "Shelter and Non-food Items": "Shelter/NFI",
        "Water, Sanitation  and Hygiene": "WASH",
        "Water, Sanitation and Hygiene": "WASH",
        "Multi-Purpose Cash": "Multi-Cash",
        "Refugee Response": "Refugee Resp.",
    }
    ssd["label"] = ssd["cluster"].str.strip().map(
        lambda x: name_map.get(x, x)
    )

    ssd = ssd.sort_values("gap", ascending=False)

    # blue gradient matching OCI map and forecast trend
    from matplotlib.colors import LinearSegmentedColormap
    gap_cmap = LinearSegmentedColormap.from_list(
        "gap", ["#DEEBF7", "#9ECAE1", "#4292C6", "#08519C"], N=256
    )
    colors = [gap_cmap(g) for g in ssd["gap"]]

    fig, ax = plt.subplots(figsize=(6, 2.6))
    x_pos = np.arange(len(ssd))
    bars = ax.bar(
        x_pos, ssd["gap"].values,
        color=colors, edgecolor="white", linewidth=0.5, width=0.7,
    )

    # data labels above bars
    for i, (bar, gap_val) in enumerate(zip(bars, ssd["gap"])):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{gap_val:.0%}", ha="center", va="bottom", fontsize=7.5,
        )

    # diagonal x-axis labels
    ax.set_xticks(x_pos)
    ax.set_xticklabels(ssd["label"].values, rotation=40, ha="right", fontsize=8)

    ax.set_ylim(0, 1.12)
    ax.set_yticks([])
    ax.grid(visible=False)
    ax.spines["left"].set_visible(False)

    fig.tight_layout()
    save_fig(fig, "cluster_gap_ssd_2026")
    plt.close(fig)


# ===========================================================================
# figure 4: project budget vs. beneficiaries scatter
# ===========================================================================
def fig_outlier_scatter():
    print("\ngenerating: outlier_scatter")

    df = df_projects.copy()
    df["budget_usd"] = pd.to_numeric(df["budget_usd"], errors="coerce")
    df["beneficiaries_total"] = pd.to_numeric(df["beneficiaries_total"], errors="coerce")
    df["efficiency_ratio"] = pd.to_numeric(df.get("efficiency_ratio", pd.Series(dtype=float)), errors="coerce")

    # filter to positive values for log scale
    mask = (df["budget_usd"] > 0) & (df["beneficiaries_total"] > 0)
    df = df[mask].copy()

    # compute flags via z-score within (cluster_name, year) groups
    flag_col = "flag"
    df[flag_col] = "normal"
    group_cols = [c for c in ["cluster_name", "year"] if c in df.columns]
    if not group_cols:
        group_cols = ["cluster_name"] if "cluster_name" in df.columns else []

    if group_cols and "efficiency_ratio" in df.columns:
        for _, grp in df.groupby(group_cols):
            valid = grp["efficiency_ratio"].notna()
            if valid.sum() < 3:
                df.loc[grp.index, flag_col] = "insufficient_data"
                continue
            log_r = np.log1p(grp.loc[valid, "efficiency_ratio"].values)
            std = log_r.std(ddof=1)
            if std == 0:
                continue
            z = (log_r - log_r.mean()) / std
            vi = grp.index[valid.values]
            df.loc[vi[z > 2.0], flag_col] = "high_efficiency"
            df.loc[vi[z < -2.0], flag_col] = "low_efficiency"

    # merge insufficient_data into normal for cleaner plot
    df.loc[df[flag_col] == "insufficient_data", flag_col] = "normal"

    fig, ax = plt.subplots(figsize=(6, 4.5))

    # normal projects: light blue
    normal = df[df[flag_col] == "normal"]
    ax.scatter(
        normal["budget_usd"], normal["beneficiaries_total"],
        c="#B0CEE3", s=12, alpha=0.6, edgecolors="none",
        label="Projects", zorder=1,
    )

    # high-efficiency benchmarks: dark navy
    benchmarks = df[df[flag_col] == "high_efficiency"]
    ax.scatter(
        benchmarks["budget_usd"], benchmarks["beneficiaries_total"],
        c="#08519C", s=28, alpha=0.85, edgecolors="white",
        linewidths=0.4, label="High Efficiency", zorder=4,
    )

    # reference line: median efficiency
    valid_eff = df[df["efficiency_ratio"].notna() & (df["efficiency_ratio"] > 0)]
    if not valid_eff.empty:
        median_eff = valid_eff["efficiency_ratio"].median()
        x_range = np.logspace(
            np.log10(df["budget_usd"].min()),
            np.log10(df["budget_usd"].max()),
            100,
        )
        ax.plot(
            x_range, median_eff * x_range, "--",
            color="#444444", linewidth=1.0, alpha=0.5,
            label=f"Median ({median_eff:.3f} ben/USD)",
            zorder=2,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Budget (USD, log scale)")
    ax.set_ylabel("Beneficiaries (log scale)")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9, edgecolor="#cccccc")
    ax.grid(True, alpha=0.15, which="major", linewidth=0.5, color="#888888")
    ax.grid(True, alpha=0.08, which="minor", linewidth=0.3, color="#aaaaaa")
    sns.despine(ax=ax, top=True, right=True)
    ax.spines["left"].set_linewidth(0.6)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.spines["left"].set_color("#444444")
    ax.spines["bottom"].set_color("#444444")

    fig.tight_layout()
    save_fig(fig, "outlier_scatter")
    plt.close(fig)


# ===========================================================================
# figure 5: funding-gap history (South Sudan)
# uses full funding history from funding_clean.csv (not just OCI years)
# ===========================================================================
df_funding = pd.read_csv(os.path.join(DATA_DIR, "funding_clean.csv"))

def fig_forecast_trend():
    print("\ngenerating: forecast_trend_ssd")

    ssd = df_funding[df_funding["country_iso3"] == "SSD"].sort_values("year")
    ssd = ssd.dropna(subset=["funding_gap", "year"])

    x = ssd["year"].values.astype(int)
    y = ssd["funding_gap"].values.astype(float)

    if len(x) < 3:
        print("  skipping: not enough data points for SSD")
        return

    with sns.axes_style("white"):
        fig, ax = plt.subplots(figsize=(5.5, 2.8))

        # soft fill under the curve
        ax.fill_between(
            x, y, alpha=0.08, color=COLORS["blue"], linewidth=0,
        )

        # main line
        ax.plot(
            x, y, "-", color=COLORS["blue"], linewidth=2.0, zorder=4,
        )

        # dot markers
        ax.scatter(
            x, y, s=28, color=COLORS["blue"], edgecolors="white",
            linewidths=1.0, zorder=5,
        )

        ax.set_xlabel("Year", fontsize=10)
        ax.set_ylabel("Funding Gap", fontsize=10)
        ax.set_ylim(0, 1.05)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
        ax.yaxis.set_major_locator(mticker.MultipleLocator(0.2))

        # clean grid: horizontal only, very light
        ax.grid(axis="y", alpha=0.15, linewidth=0.6, color="#888888")
        ax.grid(axis="x", visible=False)

        # spines: only bottom and left, thin
        sns.despine(ax=ax, top=True, right=True)
        ax.spines["left"].set_linewidth(0.6)
        ax.spines["bottom"].set_linewidth(0.6)
        ax.spines["left"].set_color("#444444")
        ax.spines["bottom"].set_color("#444444")

        ax.tick_params(colors="#444444", labelsize=9)

        # integer year ticks, every 3 years
        ax.xaxis.set_major_locator(mticker.MultipleLocator(3))
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v)}"))

    fig.tight_layout()
    save_fig(fig, "forecast_trend_ssd")
    plt.close(fig)


# ===========================================================================
# figure 6: reallocation sensitivity sweep
# ===========================================================================
def fig_realloc_sensitivity():
    print("\ngenerating: realloc_sensitivity")

    # use latest year OCI data
    latest_year = df_oci["year"].max()
    df = df_oci[df_oci["year"] == latest_year].copy()
    df = df.dropna(subset=["oci_score", "funding_gap", "requirements_usd_m", "funding_usd_m"])
    df = df[df["oci_score"] > 0].copy()

    # donor pool: crises with below-median funding gap (relatively better funded)
    # recipient pool: crises with OCI > 0.5 (most overlooked)
    median_gap = df["funding_gap"].median()
    recipient_threshold = 0.5

    donors = df[df["funding_gap"] <= median_gap]
    recipients = df[df["oci_score"] > recipient_threshold]

    donor_total_funding = donors["funding_usd_m"].sum()

    # sweep reallocation from 0% to 30%
    pct_range = np.arange(0, 31, 1)
    avg_recipient_gaps = []
    total_people_reached = []

    for pct in pct_range:
        pool = donor_total_funding * (pct / 100.0)
        rec = recipients.copy()

        # allocate proportional to OCI
        total_oci = rec["oci_score"].sum()
        rec["alloc"] = (rec["oci_score"] / total_oci) * pool

        # cap at each recipient's shortfall
        rec["shortfall"] = (rec["requirements_usd_m"] - rec["funding_usd_m"]).clip(lower=0)
        rec["alloc"] = rec[["alloc", "shortfall"]].min(axis=1)

        rec["new_funding"] = rec["funding_usd_m"] + rec["alloc"]
        rec["new_gap"] = np.where(
            rec["requirements_usd_m"] > 0,
            1 - (rec["new_funding"] / rec["requirements_usd_m"]),
            rec["funding_gap"],
        )
        rec["new_gap"] = rec["new_gap"].clip(0, 1)

        avg_recipient_gaps.append(rec["new_gap"].mean())

        # estimate additional people reached (linear: alloc * median efficiency)
        # use beneficiaries/budget from project data as proxy
        median_eff = 0.031  # from outlier scatter median
        additional = rec["alloc"].sum() * 1e6 * median_eff  # alloc is in $M
        total_people_reached.append(additional)

    avg_recipient_gaps = np.array(avg_recipient_gaps)

    with sns.axes_style("white"):
        fig, ax = plt.subplots(figsize=(5.5, 2.8))

        # area fill
        ax.fill_between(
            pct_range, avg_recipient_gaps, alpha=0.08, color=COLORS["blue"], linewidth=0,
        )

        # main line
        ax.plot(
            pct_range, avg_recipient_gaps, "-", color=COLORS["blue"], linewidth=2.0, zorder=4,
        )

        # dot markers at 5% intervals
        marker_idx = pct_range % 5 == 0
        ax.scatter(
            pct_range[marker_idx], avg_recipient_gaps[marker_idx],
            s=28, color=COLORS["blue"], edgecolors="white",
            linewidths=1.0, zorder=5,
        )

        ax.set_xlabel("Reallocation (%)", fontsize=10)
        ax.set_ylabel("Avg. Recipient Funding Gap", fontsize=10)
        y_min = avg_recipient_gaps.min()
        y_max = avg_recipient_gaps.max()
        pad = (y_max - y_min) * 0.3
        ax.set_ylim(max(0, y_min - pad), min(1, y_max + pad))
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v)}%"))
        ax.xaxis.set_major_locator(mticker.MultipleLocator(5))

        # clean grid
        ax.grid(axis="y", alpha=0.15, linewidth=0.6, color="#888888")
        ax.grid(axis="x", visible=False)

        sns.despine(ax=ax, top=True, right=True)
        ax.spines["left"].set_linewidth(0.6)
        ax.spines["bottom"].set_linewidth(0.6)
        ax.spines["left"].set_color("#444444")
        ax.spines["bottom"].set_color("#444444")
        ax.tick_params(colors="#444444", labelsize=9)

    fig.tight_layout()
    save_fig(fig, "realloc_sensitivity")
    plt.close(fig)


# ===========================================================================
# main
# ===========================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Crisis Lens — Paper Figure Generation")
    print("=" * 60)

    fig_oci_map()
    fig_cluster_gap()
    fig_outlier_scatter()
    fig_forecast_trend()
    fig_realloc_sensitivity()

    print("\n" + "=" * 60)
    print("done. figures written to:")
    print(f"  {FIG_DIR}/")
    print(f"  {PAPER_FIG_DIR}/")
    print("=" * 60)
