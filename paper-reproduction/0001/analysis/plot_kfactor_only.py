"""
Standalone K-factor plots, read directly from the {obs}_kfactor.csv files
produced by make_kfactor_plot.py (no recomputation here -- pure plotting
from the already-derived K(x) = NLO+PS / LO+PS numbers).

Outputs:
  - output/figures/lops_vs_nlops/{obs}_kfactor_only.png / .pdf  (one per obs)
  - output/figures/lops_vs_nlops/kfactor_overview.png / .pdf    (all 5, grid)
"""

import csv
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from binning import BIN_EDGES

DATA_DIR = "output/data/lops_vs_nlops"
FIG_DIR = "output/figures/lops_vs_nlops"

OBS_META = {
    "pt_ttbar": r"$p_T^{t\bar{t}}$ [GeV]",
    "dphi_ttbar": r"$\Delta\phi_{t\bar{t}}$ [rad]",
    "pt_top_lead": r"$p_T^{t,\mathrm{lead}}$ [GeV]",
    "m_ttbar": r"$m_{t\bar{t}}$ [GeV]",
    "y_t": r"$y_t$",
}

K_INCL = 1.3249
DK_INCL = 0.0278


def load_kfactor_csv(obs_name):
    path = os.path.join(DATA_DIR, f"{obs_name}_kfactor.csv")
    centers, K, dK = [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["valid"] == "1" and row["K"] != "":
                centers.append(float(row["bin_center"]))
                K.append(float(row["K"]))
                dK.append(float(row["K_err"]))
    return np.array(centers), np.array(K), np.array(dK)


def plot_single(obs_name):
    centers, K, dK = load_kfactor_csv(obs_name)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(centers, K, yerr=dK, fmt="o", color="tab:red",
                ecolor="tab:red", markersize=5, elinewidth=1.2, capsize=3,
                label="K(x) = NLO+PS / LO+PS")
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=1.0, label="K = 1")
    ax.axhline(K_INCL, color="black", linestyle="--", linewidth=1.0,
               label=f"inclusive K = {K_INCL:.3f} $\\pm$ {DK_INCL:.3f}")
    ax.axhspan(K_INCL - DK_INCL, K_INCL + DK_INCL, color="black", alpha=0.08)
    ax.set_xlabel(OBS_META[obs_name])
    ax.set_ylabel("K(x)")
    ax.set_title(f"Differential K-factor: {OBS_META[obs_name]}")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()

    out_pdf = os.path.join(FIG_DIR, f"{obs_name}_kfactor_only.pdf")
    out_png = os.path.join(FIG_DIR, f"{obs_name}_kfactor_only.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[plot] wrote {out_pdf} and {out_png}")


def plot_overview():
    obs_names = list(BIN_EDGES)
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()
    for i, obs_name in enumerate(obs_names):
        ax = axes[i]
        centers, K, dK = load_kfactor_csv(obs_name)
        ax.errorbar(centers, K, yerr=dK, fmt="o", color="tab:red",
                    ecolor="tab:red", markersize=4, elinewidth=1.0, capsize=2)
        ax.axhline(1.0, color="gray", linestyle=":", linewidth=1.0)
        ax.axhline(K_INCL, color="black", linestyle="--", linewidth=1.0)
        ax.axhspan(K_INCL - DK_INCL, K_INCL + DK_INCL, color="black", alpha=0.08)
        ax.set_xlabel(OBS_META[obs_name])
        ax.set_ylabel("K(x)")
        ax.set_title(obs_name)
    axes[-1].axis("off")
    fig.suptitle(r"Differential K-factor, NLO+PS / LO+PS:  $pp \to t\bar{t}$ @ 13 TeV"
                 f"\ndashed = inclusive K = {K_INCL:.3f} $\\pm$ {DK_INCL:.3f}, dotted = K=1")
    fig.tight_layout(rect=[0, 0, 1, 0.94])

    out_pdf = os.path.join(FIG_DIR, "kfactor_overview.pdf")
    out_png = os.path.join(FIG_DIR, "kfactor_overview.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[plot] wrote {out_pdf} and {out_png}")


def main():
    for obs_name in BIN_EDGES:
        plot_single(obs_name)
    plot_overview()


if __name__ == "__main__":
    main()
