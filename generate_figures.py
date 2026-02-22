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

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(PAPER_FIG_DIR, exist_ok=True)


def save_fig(fig, name):
    """save to both figures/ and paper/figures/ as PDF and PNG."""
    for d in [FIG_DIR, PAPER_FIG_DIR]:
        fig.savefig(os.path.join(d, f"{name}.pdf"), format="pdf")
    fig.savefig(os.path.join(FIG_DIR, f"{name}.png"), format="png", dpi=300)
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
        import matplotlib.patches as mpatches
        # we need a world shapefile — try cartopy first, fallback to simple scatter
        try:
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
            HAS_CARTOPY = True
        except ImportError:
            HAS_CARTOPY = False

        df = df_oci.sort_values("year", ascending=False).drop_duplicates("country_iso3")

        if HAS_CARTOPY:
            fig, ax = plt.subplots(
                figsize=(7, 3.8),
                subplot_kw={"projection": ccrs.Robinson()},
            )
            ax.set_global()
            ax.add_feature(cfeature.LAND, facecolor="#f0f0f0", edgecolor="none")
            ax.add_feature(cfeature.BORDERS, linewidth=0.3, edgecolor="#cccccc")
            ax.add_feature(cfeature.OCEAN, facecolor="white")
            try:
                ax.outline_patch.set_visible(False)
            except AttributeError:
                ax.spines["geo"].set_visible(False)

            # country centroids (approximate)
            centroids = {
                "SSD": (30.2, 6.8), "SYR": (38.9, 35.0), "YEM": (48.0, 15.5),
                "SDN": (30.2, 15.5), "HTI": (-72.3, 19.0), "AFG": (67.7, 33.9),
                "ETH": (40.5, 9.0), "COD": (21.8, -4.0), "NGA": (8.7, 9.1),
                "SOM": (46.2, 5.2), "MMR": (96.0, 21.9), "UKR": (31.2, 48.4),
                "TCD": (18.7, 15.5), "MLI": (-1.9, 17.6), "BFA": (-1.6, 12.3),
                "CMR": (12.4, 7.4), "CAF": (20.9, 6.6), "NER": (8.1, 17.6),
                "MOZ": (35.5, -18.7), "COL": (-74.3, 4.6), "VEN": (-66.6, 6.4),
                "HND": (-86.2, 15.2), "GTM": (-90.2, 15.8), "SLV": (-88.9, 13.8),
                "PSE": (35.2, 31.9), "LBN": (35.9, 33.9), "IRQ": (44.0, 33.2),
                "LBY": (17.2, 26.3),
            }

            from matplotlib.colors import LinearSegmentedColormap
            oci_cmap = LinearSegmentedColormap.from_list(
                "oci", ["#2ecc71", "#f39c12", "#e74c3c", "#8e0000"], N=256
            )

            for _, row in df.iterrows():
                iso3 = row["country_iso3"]
                if iso3 in centroids:
                    lon, lat = centroids[iso3]
                    color = oci_cmap(row["oci_score"])
                    size = max(40, row["oci_score"] * 200)
                    ax.scatter(
                        lon, lat, c=[color], s=size, edgecolors="black",
                        linewidths=0.3, transform=ccrs.PlateCarree(), zorder=5,
                    )

            sm = plt.cm.ScalarMappable(
                cmap=oci_cmap, norm=plt.Normalize(0, 1)
            )
            sm.set_array([])
            cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02, aspect=20)
            cbar.set_label("OCI Score", fontsize=9)
            cbar.ax.tick_params(labelsize=8)

            fig.subplots_adjust(left=0.02, right=0.92, top=0.98, bottom=0.02)
        else:
            # fallback: simple bar chart of OCI scores (no map library)
            df_sorted = df.nlargest(15, "oci_score").sort_values("oci_score")
            from matplotlib.colors import LinearSegmentedColormap
            oci_cmap = LinearSegmentedColormap.from_list(
                "oci", ["#2ecc71", "#f39c12", "#e74c3c", "#8e0000"], N=256
            )
            colors = [oci_cmap(s) for s in df_sorted["oci_score"]]

            fig, ax = plt.subplots(figsize=(6, 4.5))
            ax.barh(
                df_sorted["country_name"], df_sorted["oci_score"],
                color=colors, edgecolor="black", linewidth=0.3,
            )
            ax.set_xlabel("OCI Score")
            ax.set_xlim(0, 1.05)
            for i, (_, row) in enumerate(df_sorted.iterrows()):
                ax.text(
                    row["oci_score"] + 0.02, i, f"{row['oci_score']:.3f}",
                    va="center", fontsize=8,
                )

        save_fig(fig, "oci_map")
        plt.close(fig)
    except Exception as e:
        print(f"  warning: oci_map generation failed: {e}")
        # create a minimal placeholder
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "OCI Map (requires cartopy)", ha="center", va="center",
                transform=ax.transAxes, fontsize=12)
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

    # smooth light red gradient: light blush -> warm rose
    from matplotlib.colors import LinearSegmentedColormap
    gap_cmap = LinearSegmentedColormap.from_list(
        "gap", ["#f9d6d2", "#e8998d", "#d66b6b", "#c43e3e"], N=256
    )
    colors = [gap_cmap(g) for g in ssd["gap"]]

    fig, ax = plt.subplots(figsize=(6, 4.0))
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

    ax.set_title("Funding Gap", fontsize=11, pad=10)
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

    color_map = {
        "high_efficiency": COLORS["green"],
        "normal": "#bfbfbf",
        "low_efficiency": COLORS["red"],
        "insufficient_data": "#e0e0e0",
    }
    label_map = {
        "high_efficiency": "High Efficiency",
        "normal": "Normal",
        "low_efficiency": "Low Efficiency",
        "insufficient_data": "Insufficient Data",
    }
    zorder_map = {
        "high_efficiency": 4,
        "low_efficiency": 3,
        "normal": 1,
        "insufficient_data": 0,
    }

    fig, ax = plt.subplots(figsize=(6, 4.5))

    # plot each category separately for legend
    for flag_val in ["insufficient_data", "normal", "low_efficiency", "high_efficiency"]:
        subset = df[df[flag_col] == flag_val]
        if subset.empty:
            continue
        ax.scatter(
            subset["budget_usd"], subset["beneficiaries_total"],
            c=color_map.get(flag_val, "#bfbfbf"),
            s=15 if flag_val in ("normal", "insufficient_data") else 25,
            alpha=0.5 if flag_val in ("normal", "insufficient_data") else 0.8,
            edgecolors="black" if flag_val == "high_efficiency" else "none",
            linewidths=0.3,
            label=label_map.get(flag_val, flag_val),
            zorder=zorder_map.get(flag_val, 1),
        )

    # reference line: median efficiency (beneficiaries = efficiency * budget)
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
            color=COLORS["gray"], linewidth=1.0, alpha=0.6,
            label=f"Median efficiency ({median_eff:.3f} ben/USD)",
            zorder=2,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Budget (USD, log scale)")
    ax.set_ylabel("Beneficiaries (log scale)")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.grid(True, alpha=0.2, which="both")

    fig.tight_layout()
    save_fig(fig, "outlier_scatter")
    plt.close(fig)


# ===========================================================================
# figure 5: funding-gap trend with 2027 projection (South Sudan)
# uses full funding history from funding_clean.csv (not just OCI years)
# ===========================================================================
df_funding = pd.read_csv(os.path.join(DATA_DIR, "funding_clean.csv"))

def fig_forecast_trend():
    print("\ngenerating: forecast_trend_ssd")

    ssd = df_funding[df_funding["country_iso3"] == "SSD"].sort_values("year")
    ssd = ssd.dropna(subset=["funding_gap", "year"])

    x = ssd["year"].values.astype(float)
    y = ssd["funding_gap"].values.astype(float)

    if len(x) < 3:
        print("  skipping: not enough data points for SSD")
        return

    result = stats.linregress(x, y)
    proj_2027 = float(np.clip(result.slope * 2027 + result.intercept, 0, 1))

    # prediction interval
    n = len(x)
    x_mean = x.mean()
    ss_x = np.sum((x - x_mean) ** 2)
    y_pred = result.slope * x + result.intercept
    s_e = np.sqrt(np.sum((y - y_pred) ** 2) / (n - 2))
    t_crit = stats.t.ppf(0.95, df=n - 2)

    # continuous trend and CI band
    x_cont = np.linspace(x.min(), 2027, 200)
    y_trend = result.slope * x_cont + result.intercept

    se_band = s_e * np.sqrt(1 + 1 / n + (x_cont - x_mean) ** 2 / ss_x)
    y_upper = y_trend + t_crit * se_band
    y_lower = y_trend - t_crit * se_band

    fig, ax = plt.subplots(figsize=(5.5, 3.8))

    # confidence band (soft, no hard edges)
    ax.fill_between(
        x_cont, y_lower, y_upper,
        alpha=0.12, color=COLORS["red"], linewidth=0,
        label="90% prediction interval",
    )

    # historical data
    ax.plot(
        x, y, "o-", color=COLORS["blue"], markersize=5,
        linewidth=1.5, label=f"Historical (n={n})", zorder=5,
    )

    # trend line
    ax.plot(
        x_cont, y_trend, "--",
        color=COLORS["red"], linewidth=1.2, alpha=0.7,
        label=f"Linear trend ({result.slope:.3f}/yr)",
    )

    # projected point
    ax.plot(
        2027, proj_2027, "*", color=COLORS["red"], markersize=14,
        markeredgecolor="black", markeredgewidth=0.5,
        label="Projected", zorder=6,
    )

    ax.set_xlabel("Year")
    ax.set_ylabel("Funding Gap")
    ax.set_ylim(-0.02, 1.15)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.2)

    fig.tight_layout()
    save_fig(fig, "forecast_trend_ssd")
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

    print("\n" + "=" * 60)
    print("done. figures written to:")
    print(f"  {FIG_DIR}/")
    print(f"  {PAPER_FIG_DIR}/")
    print("=" * 60)
