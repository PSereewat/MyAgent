"""
Plain per-bin K-factor: K = NLO+PS_yield / LO+PS_yield, computed directly
in each of the original fixed-width Tier-2 bins. No neff masking, no
adaptive rebinning -- every bin is plotted as-is, with propagated
statistical errors, so the error bars themselves show which points are
noisy rather than dropping or merging them.

K = N / L
sigma_K = K * sqrt( (sigma_N/N)^2 + (sigma_L/L)^2 )

Bins are skipped only when the ratio is undefined (L == 0), never for
being "too noisy".

Inputs:
  - output/data/lops_vs_nlops/{obs}_lops_vs_nlops.csv

Outputs:
  - output/figures/lops_vs_nlops/{obs}_kfactor_simple.png / .pdf
  - output/data/lops_vs_nlops/{obs}_kfactor_simple.csv
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


def load_rows(obs_name):
    path = os.path.join(DATA_DIR, f"{obs_name}_lops_vs_nlops.csv")
    with open(path) as f:
        return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]


def compute(rows):
    centers, K, dK = [], [], []
    for r in rows:
        L, dL = r["LOPS_yield_pb"], r["LOPS_error_pb"]
        N, dN = r["NLOPS_yield_pb"], r["NLOPS_error_pb"]
        if L <= 0:
            continue
        k = N / L
        dk = k * np.sqrt((dN / N) ** 2 + (dL / L) ** 2) if N > 0 else np.nan
        centers.append(r["bin_center"])
        K.append(k)
        dK.append(dk)
    return np.array(centers), np.array(K), np.array(dK)


def plot_observable(obs_name, rows):
    centers, K, dK = compute(rows)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.errorbar(centers, K, yerr=dK, fmt="o", color="tab:red",
                ecolor="tab:red", markersize=4, elinewidth=1.0, capsize=2,
                label="K(x) = NLO+PS / LO+PS (per fixed bin)")
    ax.axhline(1.0, color="gray", linestyle=":", linewidth=1.0, label="K = 1")
    ax.axhline(K_INCL, color="black", linestyle="--", linewidth=1.0,
               label=f"inclusive K = {K_INCL:.3f} $\\pm$ {DK_INCL:.3f}")
    ax.axhspan(K_INCL - DK_INCL, K_INCL + DK_INCL, color="black", alpha=0.08)
    ax.set_xlabel(OBS_META[obs_name])
    ax.set_ylabel("K(x)")
    ax.set_title(f"Differential K-factor (plain per-bin ratio): {OBS_META[obs_name]}")
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()

    out_pdf = os.path.join(FIG_DIR, f"{obs_name}_kfactor_simple.pdf")
    out_png = os.path.join(FIG_DIR, f"{obs_name}_kfactor_simple.png")
    fig.savefig(out_pdf)
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"[plot] wrote {out_pdf} and {out_png}  ({len(centers)} bins)")
    return centers, K, dK


def write_csv(obs_name, centers, K, dK):
    path = os.path.join(DATA_DIR, f"{obs_name}_kfactor_simple.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bin_center", "K", "K_err"])
        for c, k, dk in zip(centers, K, dK):
            w.writerow([c, k, dk])
    print(f"[csv] wrote {path}")


def main():
    for obs_name in BIN_EDGES:
        rows = load_rows(obs_name)
        centers, K, dK = plot_observable(obs_name, rows)
        write_csv(obs_name, centers, K, dK)


if __name__ == "__main__":
    main()
